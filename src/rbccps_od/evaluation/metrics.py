from __future__ import annotations


def precision(tp: int, fp: int) -> float:
    denom = tp + fp
    return 0.0 if denom == 0 else tp / denom


def recall(tp: int, fn: int) -> float:
    denom = tp + fn
    return 0.0 if denom == 0 else tp / denom
