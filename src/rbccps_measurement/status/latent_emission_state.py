from __future__ import annotations

from dataclasses import dataclass

from rbccps_measurement.contracts.input_schema import DetectorTrackRecord


@dataclass(frozen=True)
class LampStatusEstimate:
    label: str
    confidence: float
    dim_probability: float
    occluded_probability: float
    flicker_index: float
    saturated_flag: bool

    def to_dict(self) -> dict[str, float | str | bool]:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 4),
            "dim_probability": round(self.dim_probability, 4),
            "occluded_probability": round(self.occluded_probability, 4),
            "flicker_index": round(self.flicker_index, 4),
            "saturated_flag": self.saturated_flag,
        }


def estimate_lamp_status(tracks: list[DetectorTrackRecord], normalization_reliability: float) -> LampStatusEstimate:
    scores = [track.detector_score for track in tracks]
    mean_score = sum(scores) / len(scores)
    track_conf = [track.track_confidence for track in tracks if track.track_confidence is not None]
    mean_track_conf = sum(track_conf) / len(track_conf) if track_conf else mean_score
    lost = sum((track.lost_count or 0) for track in tracks)
    flicker_index = min(1.0, lost / max(1, len(tracks) * 2))
    occluded_probability = max(0.0, min(1.0, 1.0 - mean_track_conf))
    dim_probability = max(0.0, min(1.0, 1.0 - mean_score))
    saturated_flag = mean_score > 0.92 and normalization_reliability < 0.8

    if mean_score >= 0.65:
        label = "on"
    elif mean_score >= 0.4:
        label = "dim"
    else:
        label = "unknown"
    if flicker_index > 0.35:
        label = "flicker"
    if occluded_probability > 0.65:
        label = "occluded"

    confidence = max(0.05, min(1.0, 0.55 * mean_score + 0.25 * mean_track_conf + 0.20 * normalization_reliability))
    return LampStatusEstimate(label, confidence, dim_probability, occluded_probability, flicker_index, saturated_flag)
