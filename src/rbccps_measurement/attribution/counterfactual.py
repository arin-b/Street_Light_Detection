from __future__ import annotations

from dataclasses import dataclass

from rbccps_measurement.decomposition.source_slots import SourceEvidence
from rbccps_measurement.features.distributional_coverage import UsefulIlluminationFeatures


@dataclass(frozen=True)
class AttributionEstimate:
    score: float
    attribution_class: str
    uncertainty: float


def estimate_counterfactual_attribution(features: UsefulIlluminationFeatures, source: SourceEvidence) -> AttributionEstimate:
    all_utility = features.adequacy_proxy
    without_target = max(0.0, all_utility * (1.0 - source.target_lamp))
    score = max(0.0, min(1.0, all_utility - without_target + 0.25 * source.target_lamp))
    if score >= 0.65 and source.confounder_penalty < 0.25:
        klass = "certain"
    elif score >= 0.45:
        klass = "likely_target"
    elif source.confounder_penalty >= 0.35:
        klass = "mixed"
    else:
        klass = "uncertain"
    uncertainty = max(0.0, min(1.0, 1.0 - score + 0.5 * source.confounder_penalty))
    return AttributionEstimate(score=score, attribution_class=klass, uncertainty=uncertainty)
