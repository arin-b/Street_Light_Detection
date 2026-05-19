from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from rbccps_measurement.attribution.counterfactual import estimate_counterfactual_attribution
from rbccps_measurement.contracts.calibration_policy import CalibrationPolicy
from rbccps_measurement.contracts.input_schema import ClipManifest, DetectorTrackRecord
from rbccps_measurement.contracts.output_schema import MeasurementReport
from rbccps_measurement.decomposition.source_slots import estimate_source_evidence
from rbccps_measurement.features.distributional_coverage import estimate_useful_features
from rbccps_measurement.fusion.conformal import decide_abstention
from rbccps_measurement.fusion.monotonic_heads import monotonic_fuse
from rbccps_measurement.geometry.lamp_footprint_field import estimate_footprint
from rbccps_measurement.ingest.validation import validate_clip_manifest
from rbccps_measurement.normalization.luma import estimate_normalization_quality
from rbccps_measurement.reporting.overlays import write_overlay_manifest
from rbccps_measurement.reporting.writers import write_csv, write_geojson, write_json
from rbccps_measurement.segmentation.masks import estimate_region_mix
from rbccps_measurement.status.latent_emission_state import estimate_lamp_status


def _mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    if not clean:
        return None
    return sum(clean) / len(clean)


def _group_tracks(tracks: tuple[DetectorTrackRecord, ...]) -> dict[str, list[DetectorTrackRecord]]:
    grouped: dict[str, list[DetectorTrackRecord]] = defaultdict(list)
    for track in tracks:
        grouped[track.track_id].append(track)
    for records in grouped.values():
        records.sort(key=lambda item: (item.timestamp_ns, item.frame_id))
    return dict(grouped)


def _bbox_center_x_pixels(track: DetectorTrackRecord, frame_width: int) -> float:
    x1, _, x2, _ = track.bbox_xyxy
    center = (x1 + x2) / 2
    if track.bbox_format == "normalized_xyxy_original_frame":
        return center * frame_width
    return center


class MeasurementPipeline:
    def __init__(self, measurement_run_id: str = "measurement_run") -> None:
        self.measurement_run_id = measurement_run_id

    def run(self, manifest: ClipManifest) -> list[MeasurementReport]:
        validate_clip_manifest(manifest)
        frames = manifest.frame_by_id()
        grouped = _group_tracks(manifest.tracks)
        reports: list[MeasurementReport] = []

        for track_id, track_records in sorted(grouped.items()):
            frame_records = [frames[track.frame_id] for track in track_records]
            qualities = [estimate_normalization_quality(frame.camera) for frame in frame_records]
            normalization_reliability = sum(q.reliability for q in qualities) / len(qualities)
            flags = sorted({flag for quality in qualities for flag in quality.flags})

            if any((track.track_confidence or track.detector_score) < 0.65 for track in track_records):
                flags.append("moderate_detector_confidence")

            status = estimate_lamp_status(track_records, normalization_reliability)
            footprint = estimate_footprint(track_id, track_records, frames)
            source = estimate_source_evidence(track_records, frames)
            features = estimate_useful_features(status, footprint, source, normalization_reliability)
            attribution = estimate_counterfactual_attribution(features, source)

            observation_completeness = min(1.0, len(track_records) / max(1, max(track.track_age or len(track_records) for track in track_records)))
            fusion = monotonic_fuse(features, attribution, observation_completeness)
            decision = decide_abstention(fusion.overall_category, fusion.confidence, flags)

            camera_qualities = [frame.camera.metadata_quality for frame in frame_records]
            metadata_quality = "good" if all(q in {"good", "complete", "controlled"} for q in camera_qualities) else "partial"
            auto_exposure = any(frame.camera.auto_exposure_active for frame in frame_records)
            policy = CalibrationPolicy.decide(
                manifest.calibration_level,
                manifest.optional_calibration.has_field_lux_calibration,
                auto_exposure,
                metadata_quality,
            )

            first_frame = frame_records[0]
            last_frame = frame_records[-1]
            first_track = track_records[0]
            center_x = _bbox_center_x_pixels(first_track, first_frame.width)
            region_mix = estimate_region_mix(first_frame.width, center_x)
            metrics = features.to_dict()
            metrics.update({
                "attribution_confidence": round(attribution.score, 4),
                "overall_useful_illumination_score": round(fusion.overall_score, 4),
                "overall_category": fusion.overall_category,
            })

            physical_valid = policy.physical_allowed
            physical = {
                "valid": physical_valid,
                "reason": policy.physical_reason,
                "horizontal_illuminance_lux_mean": None,
                "horizontal_illuminance_lux_interval": None,
                "vertical_illuminance_lux_mean": None,
                "served_area_m2_est": None,
            }

            report = MeasurementReport(
                measurement_run_id=self.measurement_run_id,
                lamp_observation_id=f"obs_{track_id}_{manifest.clip_id}",
                lamp_track_id=track_id,
                mapped_lamp_id=None,
                clip_id=manifest.clip_id,
                time_window={
                    "start_ns": first_frame.timestamp_ns,
                    "end_ns": last_frame.timestamp_ns,
                    "num_frames_used": len(track_records),
                    "evidence_frames": [track.frame_id for track in track_records[:4]],
                },
                geo_summary={
                    "lat": _mean([frame.pose.latitude for frame in frame_records]),
                    "lon": _mean([frame.pose.longitude for frame in frame_records]),
                    "gps_accuracy_m": _mean([frame.pose.gps_accuracy_m for frame in frame_records]),
                    "heading_deg": _mean([frame.pose.heading_deg for frame in frame_records]),
                },
                status=status.to_dict(),
                affected_region=footprint.to_dict(region_mix.to_dict()),
                metrics=metrics,
                confidence={
                    "overall": round(fusion.confidence, 4),
                    "calibration_level": policy.calibration_level,
                    "claim_tier": policy.claim_tier,
                    "observation_completeness": round(observation_completeness, 4),
                    "attribution_class": attribution.attribution_class,
                    "action": decision.action,
                    "prediction_set": decision.prediction_set,
                },
                uncertainty_flags=decision.uncertainty_flags,
                optional_physical_estimates=physical,
                traceability={
                    "model_versions": {
                        "pipeline": "deterministic_research_skeleton_v1",
                        "trained_weights": None,
                    },
                    "feature_snapshot_ref": f"features/{track_id}_{manifest.clip_id}.json",
                    "policy_id": manifest.policy_id,
                },
            )
            reports.append(report)

        return reports


def run_clip_to_directory(manifest_path: str | Path, output_dir: str | Path, measurement_run_id: str | None = None) -> list[MeasurementReport]:
    manifest = ClipManifest.load(manifest_path)
    run_id = measurement_run_id or f"run_{manifest.clip_id}"
    reports = MeasurementPipeline(run_id).run(manifest)
    out = Path(output_dir)
    (out / "masks").mkdir(parents=True, exist_ok=True)
    (out / "features").mkdir(parents=True, exist_ok=True)
    write_json(out / "reports.json", reports)
    write_csv(out / "reports.csv", reports)
    write_geojson(out / "reports.geojson", reports)
    write_overlay_manifest(out / "overlays.json", reports)
    for report in reports:
        (out / report.affected_region["image_mask_uri"]).write_text(
            json.dumps({
                "lamp_track_id": report.lamp_track_id,
                "note": "placeholder footprint mask; replace with learned dense mask output",
                "region_mix": report.affected_region["region_mix"],
            }, indent=2),
            encoding="utf-8",
        )
        feature_path = out / report.traceability["feature_snapshot_ref"]
        feature_path.write_text(json.dumps(report.metrics, indent=2), encoding="utf-8")
    return reports
