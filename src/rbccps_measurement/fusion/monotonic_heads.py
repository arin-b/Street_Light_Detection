from __future__ import annotations

from dataclasses import dataclass

from rbccps_measurement.attribution.counterfactual import AttributionEstimate
from rbccps_measurement.features.distributional_coverage import UsefulIlluminationFeatures


@dataclass(frozen=True)
class FusionResult:
    overall_score: float
    overall_category: str
    confidence: float


def monotonic_fuse(features: UsefulIlluminationFeatures, attribution: AttributionEstimate, observation_completeness: float) -> FusionResult:
    positive = 0.32 * features.coverage_proxy + 0.24 * features.uniformity_proxy + 0.24 * features.temporal_stability + 0.20 * attribution.score
    negative = 0.18 * features.glare_penalty + 0.22 * features.confounder_penalty + 0.18 * features.occlusion_penalty + 0.12 * attribution.uncertainty
    score = max(0.0, min(1.0, positive - negative))
    if score >= 0.72:
        category = "adequate"
    elif score >= 0.45:
        category = "marginal"
    elif score >= 0.2:
        category = "poor"
    else:
        category = "unknown"
    confidence = max(0.0, min(1.0, observation_completeness * (1.0 - 0.45 * attribution.uncertainty)))
    return FusionResult(score, category, confidence)
