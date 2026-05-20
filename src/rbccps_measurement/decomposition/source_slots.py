from __future__ import annotations

from dataclasses import dataclass

from rbccps_measurement.contracts.input_schema import DetectorTrackRecord, FrameRecord


@dataclass(frozen=True)
class SourceEvidence:
    target_lamp: float
    other_lamps: float
    headlights: float
    shopfronts: float
    reflections: float
    unknown: float

    @property
    def confounder_penalty(self) -> float:
        return max(0.0, min(1.0, self.headlights + self.shopfronts + self.reflections + 0.5 * self.unknown))


def estimate_source_evidence(tracks: list[DetectorTrackRecord], frames: dict[int, FrameRecord]) -> SourceEvidence:
    mean_score = sum(track.detector_score for track in tracks) / len(tracks)
    speeds = [frames[track.frame_id].pose.speed_mps for track in tracks if frames[track.frame_id].pose.speed_mps is not None]
    mean_speed = sum(speeds) / len(speeds) if speeds else 0.0
    low_metadata = sum(1 for track in tracks if frames[track.frame_id].camera.metadata_quality in {"missing", "poor"})
    metadata_penalty = low_metadata / max(1, len(tracks))
    headlights = min(0.35, max(0.0, mean_speed / 25.0))
    shopfronts = 0.12 if mean_speed < 2.0 else 0.05
    reflections = 0.08 if any(frames[track.frame_id].camera.hdr_mode == "auto" for track in tracks) else 0.03
    unknown = min(0.35, metadata_penalty * 0.25)
    target = max(0.0, min(1.0, mean_score - headlights * 0.25 - shopfronts * 0.2))
    other = max(0.0, 1.0 - target - headlights - shopfronts - reflections - unknown)
    return SourceEvidence(target, other, headlights, shopfronts, reflections, unknown)
