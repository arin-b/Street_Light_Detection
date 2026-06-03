from __future__ import annotations

from pathlib import Path
from typing import Iterable

import torch
import torch.nn as nn
import torch.nn.functional as F


FeatureMaps = torch.Tensor | list[torch.Tensor] | tuple[torch.Tensor, ...]


def _diagonal_pattern(height: int, width: int, *, flip: bool = False) -> torch.Tensor:
    pattern = torch.zeros(height, width)
    if height <= 0 or width <= 0:
        raise ValueError("Geometry kernels must have positive height and width.")
    if width == 1:
        pattern[:, 0] = 1.0
        return pattern

    for row in range(height):
        col = round(row * (width - 1) / max(1, height - 1))
        if flip:
            col = width - 1 - col
        pattern[row, col] = 1.0
    return pattern


def _vertical_pattern(height: int) -> torch.Tensor:
    if height <= 0:
        raise ValueError("Vertical geometry kernel must have positive height.")
    return torch.ones(height, 1)


def _init_single_channel_filter(conv: nn.Conv2d, pattern: torch.Tensor) -> None:
    normalized = pattern / max(float(pattern.sum()), 1.0)
    with torch.no_grad():
        conv.weight.copy_(normalized.view(1, 1, *normalized.shape))


class GeometryAttention(nn.Module):
    """Feature attention from diagonal and vertical streetlight-geometry filters."""

    def __init__(
        self,
        channels: int | None = None,
        *,
        diagonal_kernel: tuple[int, int] = (7, 3),
        vertical_kernel: tuple[int, int] = (7, 1),
        combine: str = "sum",
        strength: float = 1.0,
        learnable: bool = True,
    ) -> None:
        super().__init__()
        del channels
        if vertical_kernel[1] != 1:
            raise ValueError("The vertical pole filter must use a single-column kernel.")
        if combine not in {"sum", "max"}:
            raise ValueError("combine must be either 'sum' or 'max'.")

        diag_padding = (diagonal_kernel[0] // 2, diagonal_kernel[1] // 2)
        vertical_padding = (vertical_kernel[0] // 2, 0)
        self.left_diagonal = nn.Conv2d(1, 1, diagonal_kernel, padding=diag_padding, bias=False)
        self.right_diagonal = nn.Conv2d(1, 1, diagonal_kernel, padding=diag_padding, bias=False)
        self.vertical = nn.Conv2d(1, 1, vertical_kernel, padding=vertical_padding, bias=False)
        self.combine = combine
        self.strength = float(strength)

        height, width = diagonal_kernel
        _init_single_channel_filter(self.left_diagonal, _diagonal_pattern(height, width))
        _init_single_channel_filter(self.right_diagonal, _diagonal_pattern(height, width, flip=True))
        _init_single_channel_filter(self.vertical, _vertical_pattern(vertical_kernel[0]))

        for parameter in self.parameters():
            parameter.requires_grad = learnable

    def _forward_tensor(self, x: torch.Tensor) -> torch.Tensor:
        pooled = x.mean(dim=1, keepdim=True)
        responses = torch.cat(
            [
                self.left_diagonal(pooled),
                self.right_diagonal(pooled),
                self.vertical(pooled),
            ],
            dim=1,
        )
        attention = torch.sigmoid(responses)
        if self.combine == "max":
            mask = attention.max(dim=1, keepdim=True).values
        else:
            mask = attention.sum(dim=1, keepdim=True).clamp(0.0, 1.0)
        return x * (1.0 + self.strength * mask)

    def forward(self, features: FeatureMaps) -> FeatureMaps:
        if isinstance(features, list):
            return [self._forward_tensor(feature) for feature in features]
        if isinstance(features, tuple):
            return tuple(self._forward_tensor(feature) for feature in features)
        return self._forward_tensor(features)


class NegativeMaskBlock(nn.Module):
    """Suppress feature activations inside known negative segmentation regions."""

    def forward(self, features: FeatureMaps, negative_mask: torch.Tensor | None = None) -> FeatureMaps:
        if negative_mask is None:
            return features
        if isinstance(features, list):
            return [self._forward_tensor(feature, negative_mask) for feature in features]
        if isinstance(features, tuple):
            return tuple(self._forward_tensor(feature, negative_mask) for feature in features)
        return self._forward_tensor(features, negative_mask)

    def _forward_tensor(self, features: torch.Tensor, negative_mask: torch.Tensor) -> torch.Tensor:
        mask = _as_batched_mask(negative_mask, device=features.device, dtype=features.dtype)
        if mask.shape[0] == 1 and features.shape[0] != 1:
            mask = mask.expand(features.shape[0], -1, -1, -1)
        if mask.shape[0] != features.shape[0]:
            raise ValueError(
                f"Negative mask batch size {mask.shape[0]} does not match feature batch size {features.shape[0]}."
            )
        mask = F.interpolate(mask, size=features.shape[-2:], mode="nearest").clamp(0.0, 1.0)
        return features * (1.0 - mask)


def _as_batched_mask(mask: torch.Tensor, *, device: torch.device, dtype: torch.dtype) -> torch.Tensor:
    if mask.ndim == 2:
        mask = mask.unsqueeze(0).unsqueeze(0)
    elif mask.ndim == 3:
        mask = mask.unsqueeze(1)
    elif mask.ndim != 4:
        raise ValueError("Negative masks must have shape HxW, BxHxW, or Bx1xHxW.")
    return mask.to(device=device, dtype=dtype)


def candidate_negative_mask_paths(
    image_path: Path,
    mask_root: Path,
    *,
    suffixes: Iterable[str] = (".png", ".jpg", ".jpeg", ".npy", ".pt"),
) -> list[Path]:
    """Return likely mask paths for an image, including mirrored split layouts."""

    candidates: list[Path] = []
    for suffix in suffixes:
        candidates.append(mask_root / f"{image_path.stem}{suffix}")
        parts = image_path.parts
        if "images" in parts:
            image_index = parts.index("images")
            relative_parts = parts[image_index + 1 :]
            if relative_parts:
                candidates.append(mask_root / Path(*relative_parts).with_suffix(suffix))
    return list(dict.fromkeys(candidates))
