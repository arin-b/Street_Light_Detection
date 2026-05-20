from __future__ import annotations


def saturation_flag(value: float, threshold: float = 0.98) -> bool:
    return float(value) >= threshold
