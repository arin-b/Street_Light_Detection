from __future__ import annotations

from dataclasses import dataclass

from rbccps_measurement.contracts.input_schema import CameraMetadata


@dataclass(frozen=True)
class NormalizationQuality:
    exposure_factor: float
    reliability: float
    flags: tuple[str, ...]


def estimate_normalization_quality(camera: CameraMetadata) -> NormalizationQuality:
    flags: list[str] = []
    reliability = 1.0
    exposure = camera.exposure_time_s or 0.0167
    iso = camera.sensor_sensitivity_iso or 800
    exposure_factor = max(0.1, min(10.0, (exposure / 0.0167) * (iso / 800.0)))

    if camera.metadata_quality in {"missing", "poor"}:
        flags.append("missing_or_poor_camera_metadata")
        reliability -= 0.35
    if camera.auto_exposure_active:
        flags.append("auto_exposure_active")
        reliability -= 0.15
    if str(camera.hdr_mode or "").lower() in {"on", "auto"}:
        flags.append("hdr_or_night_processing_possible")
        reliability -= 0.1
    if camera.night_mode:
        flags.append("night_mode_active")
        reliability -= 0.1
    if (camera.digital_zoom or 1.0) > 1.01:
        flags.append("digital_zoom_active")
        reliability -= 0.1

    return NormalizationQuality(
        exposure_factor=exposure_factor,
        reliability=max(0.05, min(1.0, reliability)),
        flags=tuple(flags),
    )
