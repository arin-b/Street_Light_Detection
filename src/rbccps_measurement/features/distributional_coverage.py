from __future__ import annotations

from dataclasses import dataclass

from rbccps_measurement.decomposition.source_slots import SourceEvidence
from rbccps_measurement.geometry.lamp_footprint_field import FootprintEstimate
from rbccps_measurement.status.latent_emission_state import LampStatusEstimate


@dataclass(frozen=True)
class UsefulIlluminationFeatures:
    coverage_proxy: float
    adequacy_proxy: float
    adequacy_class: str
    uniformity_proxy: float
    dark_hole_fraction: float
    glare_penalty: float
    confounder_penalty: float
    occlusion_penalty: float
    temporal_stability: float

    def to_dict(self) -> dict[str, float | str]:
        return {
            "coverage_proxy": round(self.coverage_proxy, 4),
            "adequacy_proxy": round(self.adequacy_proxy, 4),
            "adequacy_class": self.adequacy_class,
            "uniformity_proxy": round(self.uniformity_proxy, 4),
            "dark_hole_fraction": round(self.dark_hole_fraction, 4),
            "glare_penalty": round(self.glare_penalty, 4),
            "confounder_penalty": round(self.confounder_penalty, 4),
            "occlusion_penalty": round(self.occlusion_penalty, 4),
            "temporal_stability": round(self.temporal_stability, 4),
        }


def estimate_useful_features(
    status: LampStatusEstimate,
    footprint: FootprintEstimate,
    source: SourceEvidence,
    normalization_reliability: float,
) -> UsefulIlluminationFeatures:
    geometry_factor = {"good": 1.0, "moderate": 0.82, "weak": 0.55}[footprint.quality]
    coverage = max(0.0, min(1.0, status.confidence * geometry_factor * (1.0 - 0.4 * source.confounder_penalty)))
    uniformity = max(0.0, min(1.0, 0.75 * coverage + 0.25 * footprint.geometry_quality))
    glare = 0.28 if status.saturated_flag else 0.08
    occlusion = status.occluded_probability
    stability = max(0.0, min(1.0, 1.0 - status.flicker_index - 0.25 * (1.0 - normalization_reliability)))
    dark_hole = max(0.0, min(1.0, 1.0 - uniformity))
    adequacy = max(0.0, min(1.0, 0.45 * coverage + 0.30 * uniformity + 0.25 * stability - 0.2 * glare))
    if adequacy >= 0.72:
        adequacy_class = "adequate"
    elif adequacy >= 0.45:
        adequacy_class = "marginal"
    elif adequacy >= 0.2:
        adequacy_class = "poor"
    else:
        adequacy_class = "unknown"
    return UsefulIlluminationFeatures(
        coverage_proxy=coverage,
        adequacy_proxy=adequacy,
        adequacy_class=adequacy_class,
        uniformity_proxy=uniformity,
        dark_hole_fraction=dark_hole,
        glare_penalty=glare,
        confounder_penalty=source.confounder_penalty,
        occlusion_penalty=occlusion,
        temporal_stability=stability,
    )
