from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DecompositionSpec:
    pretrained_asset: str = "retinex_decom_9200"
    interpretation: str = "learned_measurement_representation_not_physical_truth"
