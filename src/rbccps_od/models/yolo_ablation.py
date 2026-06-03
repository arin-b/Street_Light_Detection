from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


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
        if module._rbccps_use_negative_attention:
            features = module.rbccps_negative_attention(features, getattr(module, "_rbccps_negative_mask", None))
        if module._rbccps_use_geometry_attention:
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
        _register_negative_mask_hooks(pytorch_model, detect_heads)
        negative_mask_hooks = 1

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
    )
    yolo.rbccps_ablation_modules = summary
    return yolo


def negative_mask_trainer(mask_root: str | Path):
    """Build an Ultralytics trainer that adds negative segmentation masks to each batch."""

    try:
        from ultralytics.models.yolo.detect import DetectionTrainer
    except ImportError:
        try:
            from ultralytics.models.yolo.detect.train import DetectionTrainer
        except ImportError as exc:
            raise SystemExit("ultralytics is not installed. Install the training extras before running ablations.") from exc

    resolved_mask_root = Path(mask_root).expanduser().resolve()

    class RBCCPSNegativeMaskTrainer(DetectionTrainer):
        def preprocess_batch(self, batch: dict[str, Any]) -> dict[str, Any]:
            batch = super().preprocess_batch(batch)
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
    if getattr(detect_head, "_rbccps_attention_patched", False):
        detect_head._rbccps_use_geometry_attention = (
            detect_head._rbccps_use_geometry_attention or use_geometry_attention
        )
        detect_head._rbccps_use_negative_attention = (
            detect_head._rbccps_use_negative_attention or use_negative_attention
        )
        return

    from rbccps_od.models.attention import GeometryAttention, NegativeMaskBlock

    detect_head.rbccps_geometry_attention = GeometryAttention()
    detect_head.rbccps_negative_attention = NegativeMaskBlock()
    detect_head._rbccps_use_geometry_attention = use_geometry_attention
    detect_head._rbccps_use_negative_attention = use_negative_attention
    detect_head._rbccps_negative_mask = None
    detect_head.register_forward_pre_hook(DetectAttentionInputHook())
    detect_head._rbccps_attention_patched = True


def _register_negative_mask_hooks(pytorch_model: Any, detect_heads: list[Any]) -> None:
    if getattr(pytorch_model, "_rbccps_negative_mask_hooks", None):
        return
    pytorch_model.register_forward_pre_hook(NegativeMaskRootPreHook(detect_heads))
    pytorch_model.register_forward_hook(NegativeMaskRootPostHook(detect_heads))
    pytorch_model._rbccps_negative_mask_hooks = True


def _extract_negative_mask(payload: Any) -> Any:
    if isinstance(payload, dict):
        for key in ("negative_mask", "negative_masks", "seg_mask", "seg_masks"):
            if key in payload:
                return payload[key]
    return None


def _load_batch_negative_masks(batch: dict[str, Any], mask_root: Path) -> Any:
    import torch

    image_tensor = batch["img"]
    image_paths = batch.get("im_file") or batch.get("img_path") or []
    if isinstance(image_paths, (str, Path)):
        image_paths = [image_paths]
    height, width = image_tensor.shape[-2:]
    masks = [
        _load_negative_mask_for_image(Path(image_path), mask_root, size=(height, width))
        for image_path in image_paths
    ]
    if not masks:
        masks = [torch.zeros((1, height, width), dtype=image_tensor.dtype)]
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
