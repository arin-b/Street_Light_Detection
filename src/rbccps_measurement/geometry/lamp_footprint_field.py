from __future__ import annotations

from dataclasses import dataclass

from rbccps_measurement.contracts.input_schema import FrameRecord, DetectorTrackRecord


@dataclass(frozen=True)
class FootprintEstimate:
    quality: str
    mask_ref: str
    geometry_quality: float

    def to_dict(self, region_mix: dict[str, float]) -> dict[str, object]:
        return {
            "quality": self.quality,
            "image_mask_uri": self.mask_ref,
            "ground_polygon_geojson": None,
            "region_mix": region_mix,
            "geometry_quality": round(self.geometry_quality, 4),
        }


def estimate_footprint(track_id: str, tracks: list[DetectorTrackRecord], frames: dict[int, FrameRecord]) -> FootprintEstimate:
    pose_good = 0
    for track in tracks:
        pose = frames[track.frame_id].pose
        if pose.latitude is not None and pose.longitude is not None and (pose.gps_accuracy_m or 999) <= 10:
            pose_good += 1
    geometry_quality = pose_good / max(1, len(tracks))
    if geometry_quality >= 0.75:
        quality = "good"
    elif geometry_quality >= 0.35:
        quality = "moderate"
    else:
        quality = "weak"
    return FootprintEstimate(quality=quality, mask_ref=f"masks/{track_id}.json", geometry_quality=geometry_quality)
