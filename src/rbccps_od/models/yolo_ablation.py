from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import weakref

import torch


@dataclass(frozen=True)
class AppliedAblationModules:
    cse_replacements: int = 0
    attention_heads: int = 0
    negative_mask_hooks: int = 0


class CSEOutputHook:
    def __call__(self, module: Any, _inputs: tuple[Any, ...], output: Any) -> Any:
        if hasattr(output, "ndim") and output.ndim == 4:
            return module.rbccps_cse(output)
        return output


class DetectAttentionInputHook:
    def __call__(self, module: Any, args: tuple[Any, ...]) -> tuple[Any, ...] | None:
        if not args:
            return None
        features = args[0]
        if module._rbccps_use_negative_attention and hasattr(module, "rbccps_negative_attention"):
            features = module.rbccps_negative_attention(features)
        if module._rbccps_use_geometry_attention and hasattr(module, "rbccps_geometry_attention"):
            features = module.rbccps_geometry_attention(features)
        return (features, *args[1:])


class NegativeMaskRootPreHook:
    def __init__(self, detect_heads: list[Any]) -> None:
        self.detect_heads = detect_heads

    def __call__(self, _module: Any, args: tuple[Any, ...]) -> None:
        payload = args[0] if args else None
        negative_mask = _extract_negative_mask(payload)
        for head in self.detect_heads:
            head._rbccps_negative_mask = negative_mask


class NegativeMaskRootPostHook:
    def __init__(self, detect_heads: list[Any]) -> None:
        self.detect_heads = detect_heads

    def __call__(self, _module: Any, _args: tuple[Any, ...], _output: Any) -> None:
        for head in self.detect_heads:
            head._rbccps_negative_mask = None


class NegativeAttentionLossWrapper:
    """Add supervised negative-attention BCE to the native YOLO detection loss."""

    def __init__(self, base_criterion: Any, model: Any, loss_weight: float) -> None:
        self.base_criterion = base_criterion
        self._model_ref = weakref.ref(model)
        self.loss_weight = float(loss_weight)

    def __call__(self, preds: Any, batch: dict[str, Any]) -> tuple[torch.Tensor, torch.Tensor]:
        loss, loss_items = self.base_criterion(preds, batch)
        model = self._model_ref() if self._model_ref is not None else None
        mask_loss = collect_negative_attention_loss(model, batch.get("negative_mask")) if model is not None else loss.sum() * 0.0
        weighted_mask_loss = mask_loss * self.loss_weight
        batch_size = int(batch["img"].shape[0]) if isinstance(batch, dict) and "img" in batch else 1
        mask_component = (weighted_mask_loss * batch_size).reshape(1)
        loss = torch.cat([loss.reshape(-1), mask_component])
        loss_items = torch.cat([loss_items.reshape(-1), weighted_mask_loss.detach().reshape(1)])
        return loss, loss_items

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        state["_model_ref"] = None
        return state

    def update(self) -> None:
        update = getattr(self.base_criterion, "update", None)
        if update is not None:
            update()


def replace_c2f_with_cse(module: Any) -> int:
    """Recursively replace Ultralytics C2f blocks with CSE-augmented C2f blocks."""

    from rbccps_od.models.yolo_cse import CSEC2f

    replacements = 0
    for name, child in list(module.named_children()):
        if child.__class__.__name__ == "C2f":
            new_module = CSEC2f(
                child.cv1.conv.in_channels,
                child.cv2.conv.out_channels,
                n=len(child.m),
                shortcut=_c2f_shortcut(child),
                g=_c2f_groups(child),
                e=_c2f_expansion(child),
            )
            setattr(module, name, new_module)
            replacements += 1
        else:
            replacements += replace_c2f_with_cse(child)
    return replacements


def apply_ablation_modules(
    pytorch_model: Any,
    *,
    use_geometry_attention: bool = False,
    use_cse: bool = False,
    use_negative_attention: bool = False,
    negative_mask_loss_weight: float = 1.0,
) -> AppliedAblationModules:
    cse_replacements = 0
    if use_cse:
        cse_replacements = replace_c2f_with_cse(pytorch_model)
        cse_replacements += attach_cse_to_csp_modules(pytorch_model)
    attention_heads = 0
    detect_heads = _detect_heads(pytorch_model)
    if use_geometry_attention or use_negative_attention:
        for head in detect_heads:
            _patch_detect_head(
                head,
                use_geometry_attention=use_geometry_attention,
                use_negative_attention=use_negative_attention,
            )
        attention_heads = len(detect_heads)

    negative_mask_hooks = 0
    if use_negative_attention and detect_heads:
        pytorch_model._rbccps_negative_mask_loss_weight = float(negative_mask_loss_weight)
        negative_mask_hooks = len(detect_heads)

    return AppliedAblationModules(
        cse_replacements=cse_replacements,
        attention_heads=attention_heads,
        negative_mask_hooks=negative_mask_hooks,
    )


def attach_cse_to_csp_modules(module: Any) -> int:
    """Attach CSE blocks to YOLO26 CSP-style modules that are not C2f."""

    from rbccps_od.domain.cse import CSEBlock

    attached = 0
    for child in module.modules():
        if child.__class__.__name__ not in {"C3k2", "C3k"}:
            continue
        if getattr(child, "_rbccps_cse_attached", False):
            continue
        channels = _module_output_channels(child)
        if channels is None:
            continue
        child.rbccps_cse = CSEBlock(channels)
        child.register_forward_hook(CSEOutputHook())
        child._rbccps_cse_attached = True
        attached += 1
    return attached


def build_yolo26_ablation_model(
    weights_path: str | Path,
    *,
    use_geometry_attention: bool = False,
    use_cse: bool = False,
    use_negative_attention: bool = False,
    negative_mask_loss_weight: float = 1.0,
) -> Any:
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("ultralytics is not installed. Install the training extras before running ablations.") from exc

    yolo = YOLO(str(weights_path))
    summary = apply_ablation_modules(
        yolo.model,
        use_geometry_attention=use_geometry_attention,
        use_cse=use_cse,
        use_negative_attention=use_negative_attention,
        negative_mask_loss_weight=negative_mask_loss_weight,
    )
    yolo.rbccps_ablation_modules = summary
    return yolo


def negative_mask_trainer(mask_root: str | Path | None, *, loss_weight: float = 1.0):
    """Build an Ultralytics trainer that adds negative segmentation masks to each batch."""

    try:
        from ultralytics.models.yolo.detect import DetectionTrainer
    except ImportError:
        try:
            from ultralytics.models.yolo.detect.train import DetectionTrainer
        except ImportError as exc:
            raise SystemExit("ultralytics is not installed. Install the training extras before running ablations.") from exc

    resolved_mask_root = Path(mask_root).expanduser().resolve() if mask_root is not None else None

    class RBCCPSNegativeMaskTrainer(DetectionTrainer):
        def set_model_attributes(self) -> None:
            super().set_model_attributes()
            install_negative_attention_loss(self.model, loss_weight=loss_weight)

        def get_validator(self):
            validator = super().get_validator()
            self.loss_names = "box_loss", "cls_loss", "dfl_loss", "mask_loss"
            return validator

        def preprocess_batch(self, batch: dict[str, Any]) -> dict[str, Any]:
            batch = super().preprocess_batch(batch)
            if resolved_mask_root is not None and "negative_mask" not in batch:
                batch["negative_mask"] = _load_batch_negative_masks(batch, resolved_mask_root)
            return batch

    return RBCCPSNegativeMaskTrainer


def _c2f_shortcut(module: Any) -> bool:
    first = next(iter(module.m), None)
    return bool(getattr(first, "add", False))


def _c2f_groups(module: Any) -> int:
    first = next(iter(module.m), None)
    conv = getattr(getattr(first, "cv2", None), "conv", None)
    return int(getattr(conv, "groups", 1))


def _c2f_expansion(module: Any) -> float:
    hidden = int(getattr(module, "c", 0))
    output = int(module.cv2.conv.out_channels)
    if not hidden or not output:
        return 0.5
    return hidden / output


def _module_output_channels(module: Any) -> int | None:
    for attr in ("cv3", "cv2"):
        conv = getattr(getattr(module, attr, None), "conv", None)
        channels = getattr(conv, "out_channels", None)
        if channels:
            return int(channels)
    return None


def _detect_heads(pytorch_model: Any) -> list[Any]:
    return [
        module
        for module in pytorch_model.modules()
        if module.__class__.__name__.endswith("Detect") and hasattr(module, "forward")
    ]


def _patch_detect_head(
    detect_head: Any,
    *,
    use_geometry_attention: bool,
    use_negative_attention: bool,
) -> None:
    channels = _detect_head_input_channels(detect_head)
    _ensure_attention_modules(
        detect_head,
        channels,
        use_geometry_attention=use_geometry_attention,
        use_negative_attention=use_negative_attention,
    )
    has_hook = _has_attention_input_hook(detect_head)
    if getattr(detect_head, "_rbccps_attention_patched", False) and has_hook:
        detect_head._rbccps_use_geometry_attention = (
            detect_head._rbccps_use_geometry_attention or use_geometry_attention
        )
        detect_head._rbccps_use_negative_attention = (
            detect_head._rbccps_use_negative_attention or use_negative_attention
        )
        return

    detect_head._rbccps_use_geometry_attention = use_geometry_attention
    detect_head._rbccps_use_negative_attention = use_negative_attention
    detect_head._rbccps_negative_mask = None
    if not has_hook:
        detect_head.register_forward_pre_hook(DetectAttentionInputHook())
    detect_head._rbccps_attention_patched = True


def _ensure_attention_modules(
    detect_head: Any,
    channels: tuple[int, ...],
    *,
    use_geometry_attention: bool,
    use_negative_attention: bool,
) -> None:
    if use_geometry_attention and not hasattr(detect_head, "rbccps_geometry_attention"):
        from rbccps_od.models.attention import GeometryAttention

        detect_head.rbccps_geometry_attention = GeometryAttention(channels)
    if use_negative_attention and not hasattr(detect_head, "rbccps_negative_attention"):
        from rbccps_od.models.attention import NegativeAttention

        detect_head.rbccps_negative_attention = NegativeAttention(channels)


def _has_attention_input_hook(detect_head: Any) -> bool:
    return any(isinstance(hook, DetectAttentionInputHook) for hook in detect_head._forward_pre_hooks.values())


def _register_negative_mask_hooks(pytorch_model: Any, detect_heads: list[Any]) -> None:
    if getattr(pytorch_model, "_rbccps_negative_mask_hooks", None):
        return
    pytorch_model.register_forward_pre_hook(NegativeMaskRootPreHook(detect_heads))
    pytorch_model.register_forward_hook(NegativeMaskRootPostHook(detect_heads))
    pytorch_model._rbccps_negative_mask_hooks = True


def install_negative_attention_loss(pytorch_model: Any, *, loss_weight: float = 1.0) -> None:
    """Wrap the model criterion with the negative-mask BCE auxiliary loss."""

    if not _detect_heads(pytorch_model):
        return
    if getattr(pytorch_model, "criterion", None) is None:
        pytorch_model.criterion = pytorch_model.init_criterion()
    if isinstance(pytorch_model.criterion, NegativeAttentionLossWrapper):
        pytorch_model.criterion.loss_weight = float(loss_weight)
        return
    pytorch_model.criterion = NegativeAttentionLossWrapper(pytorch_model.criterion, pytorch_model, loss_weight)


def collect_negative_attention_loss(pytorch_model: Any, target_mask: torch.Tensor | None) -> torch.Tensor:
    losses: list[torch.Tensor] = []
    for head in _detect_heads(pytorch_model):
        attention = getattr(head, "rbccps_negative_attention", None)
        if attention is not None and getattr(head, "_rbccps_use_negative_attention", False):
            losses.append(attention.mask_loss(target_mask))
    if losses:
        return torch.stack(losses).mean()
    parameter = next(pytorch_model.parameters(), None)
    if parameter is None:
        return torch.tensor(0.0)
    return parameter.sum() * 0.0


def _extract_negative_mask(payload: Any) -> Any:
    if isinstance(payload, dict):
        for key in ("negative_mask", "negative_masks", "seg_mask", "seg_masks"):
            if key in payload:
                return payload[key]
    return None


def _detect_head_input_channels(detect_head: Any) -> tuple[int, ...]:
    channels: list[int] = []
    for scale_head in getattr(detect_head, "cv2", []):
        channel = _first_conv_in_channels(scale_head)
        if channel is None:
            raise ValueError("Could not infer YOLO detect-head input channels for attention modules.")
        channels.append(channel)
    if not channels:
        raise ValueError("YOLO detect head exposes no feature scales for attention modules.")
    return tuple(channels)


def _first_conv_in_channels(module: Any) -> int | None:
    for child in module.modules():
        conv = getattr(child, "conv", None)
        if conv is not None and hasattr(conv, "in_channels"):
            return int(conv.in_channels)
        if hasattr(child, "in_channels"):
            return int(child.in_channels)
    return None


def _load_batch_negative_masks(batch: dict[str, Any], mask_root: Path) -> Any:
    import torch

    image_tensor = batch["img"]
    image_paths = batch.get("im_file") or batch.get("img_path") or []
    if isinstance(image_paths, (str, Path)):
        image_paths = [image_paths]
    height, width = image_tensor.shape[-2:]
    batch_size = int(image_tensor.shape[0])
    masks = [
        _load_negative_mask_for_image(Path(image_path), mask_root, size=(height, width))
        for image_path in list(image_paths)[:batch_size]
    ]
    while len(masks) < batch_size:
        masks.append(torch.zeros((1, height, width), dtype=torch.float32))
    return torch.stack(masks, dim=0).to(device=image_tensor.device, dtype=image_tensor.dtype)


def _load_negative_mask_for_image(image_path: Path, mask_root: Path, *, size: tuple[int, int]) -> Any:
    import torch
    import torch.nn.functional as F
    from PIL import Image

    from rbccps_od.models.attention import candidate_negative_mask_paths

    mask_path = next(
        (candidate for candidate in candidate_negative_mask_paths(image_path, mask_root) if candidate.exists()),
        None,
    )
    height, width = size
    if mask_path is None:
        return torch.zeros((1, height, width), dtype=torch.float32)

    suffix = mask_path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg"}:
        with Image.open(mask_path) as image:
            mask = image.convert("L").resize((width, height), Image.Resampling.NEAREST)
            data = torch.as_tensor(list(mask.getdata()), dtype=torch.float32).view(1, height, width)
            return data / 255.0
    if suffix == ".npy":
        import numpy as np

        data = torch.as_tensor(np.load(mask_path), dtype=torch.float32)
    elif suffix == ".pt":
        data = torch.as_tensor(torch.load(mask_path, map_location="cpu"), dtype=torch.float32)
    else:
        raise ValueError(f"Unsupported negative mask format: {mask_path}")

    if data.ndim == 2:
        data = data.unsqueeze(0)
    if data.ndim == 3 and data.shape[0] != 1:
        data = data[:1]
    if data.shape[-2:] != (height, width):
        data = F.interpolate(data.unsqueeze(0), size=(height, width), mode="nearest").squeeze(0)
    return data.clamp(0.0, 1.0)
