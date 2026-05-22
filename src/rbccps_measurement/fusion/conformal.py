from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AbstentionDecision:
    action: str
    uncertainty_flags: list[str]
    prediction_set: list[str]


def decide_abstention(overall_category: str, confidence: float, flags: list[str]) -> AbstentionDecision:
    prediction_set = [overall_category]
    if confidence < 0.55:
        flags = [*flags, "low_conformal_confidence"]
        prediction_set = sorted(set([overall_category, "manual_review_recommended"]))
    if confidence < 0.35:
        return AbstentionDecision("abstain", flags, prediction_set)
    return AbstentionDecision("report", flags, prediction_set)
