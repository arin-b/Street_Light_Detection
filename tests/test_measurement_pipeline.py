import json
from pathlib import Path

from rbccps_measurement.cli.train_module import main as train_module_main
from rbccps_measurement.ingest.pseudo_manifest import PseudoManifestOptions, build_pseudo_manifest
from rbccps_measurement.pipeline import run_clip_to_directory
from rbccps_measurement.training.readiness import check_dataset_readiness

from test_measurement_contracts import make_manifest_payload


def write_manifest(tmp_path: Path, payload=None) -> Path:
    path = tmp_path / "clip_manifest.json"
    path.write_text(json.dumps(payload or make_manifest_payload(), indent=2), encoding="utf-8")
    return path


def test_measure_clip_outputs_reports_and_policy_gates(tmp_path: Path):
    manifest_path = write_manifest(tmp_path)
    out = tmp_path / "run"
    reports = run_clip_to_directory(manifest_path, out)

    assert len(reports) == 1
    report = reports[0].to_dict()
    assert report["lamp_track_id"] == "track_1"
    assert report["optional_physical_estimates"]["valid"] is False
    assert "auto_exposure_active" in report["uncertainty_flags"]
    assert (out / "reports.json").exists()
    assert (out / "reports.csv").exists()
    assert (out / "reports.geojson").exists()
    assert (out / "overlays.json").exists()
    assert (out / "masks" / "track_1.json").exists()
    assert (out / "features" / "track_1_clip_001.json").exists()


def test_measure_clip_can_emit_physical_valid_only_at_controlled_tier(tmp_path: Path):
    payload = make_manifest_payload(calibration_level=3)
    payload["frames"][0]["camera"]["ae_mode"] = "off"
    payload["frames"][0]["camera"]["metadata_quality"] = "good"
    payload["optional_calibration"]["photometric"]["field_lux_calibration_id"] = "field_ref_001"
    manifest_path = write_manifest(tmp_path, payload)

    reports = run_clip_to_directory(manifest_path, tmp_path / "run")
    report = reports[0].to_dict()
    assert report["optional_physical_estimates"]["valid"] is True


def test_measure_clip_handles_normalized_bboxes_in_original_frame(tmp_path: Path):
    payload = make_manifest_payload()
    payload["tracks"][0]["bbox_xyxy"] = [0.4, 0.1, 0.45, 0.2]
    payload["tracks"][0]["bbox_format"] = "normalized_xyxy_original_frame"
    manifest_path = write_manifest(tmp_path, payload)

    reports = run_clip_to_directory(manifest_path, tmp_path / "run")
    report = reports[0].to_dict()
    mix = report["affected_region"]["region_mix"]
    assert abs(sum(mix.values()) - 1.0) < 0.001
    assert report["lamp_track_id"] == "track_1"


def test_prepare_dataset_like_manifest_round_trip(tmp_path: Path):
    clip_manifest = write_manifest(tmp_path)
    dataset_manifest = tmp_path / "dataset_input.json"
    dataset_manifest.write_text(json.dumps({"clips": [str(clip_manifest)]}), encoding="utf-8")

    from rbccps_measurement.cli.prepare_dataset import _load_clip_entries

    assert _load_clip_entries(dataset_manifest) == [str(clip_manifest)]


def test_prepare_dataset_loader_accepts_utf8_bom(tmp_path: Path):
    clip_manifest = write_manifest(tmp_path)
    dataset_manifest = tmp_path / "dataset_input_bom.json"
    dataset_manifest.write_text("\ufeff" + json.dumps({"clips": [str(clip_manifest)]}), encoding="utf-8")

    from rbccps_measurement.cli.prepare_dataset import _load_clip_entries

    assert _load_clip_entries(dataset_manifest) == [str(clip_manifest)]


def test_train_module_dry_run_writes_plan(tmp_path: Path, monkeypatch):
    out = tmp_path / "train"
    monkeypatch.setattr(
        "sys.argv",
        [
            "train-module",
            "--module",
            "segmentation",
            "--dataset",
            str(tmp_path),
            "--out",
            str(out),
            "--dry-run",
            "--skip-readiness",
        ],
    )
    train_module_main()
    payload = json.loads((out / "training_plan.json").read_text(encoding="utf-8"))
    assert payload["module"] == "segmentation"
    assert payload["status"] == "ready"


def test_readiness_accepts_prepared_manifest_without_annotation_requirement(tmp_path: Path):
    clip_manifest = write_manifest(tmp_path)
    dataset_root = tmp_path / "dataset"
    clips = dataset_root / "clips"
    clips.mkdir(parents=True)
    copied = clips / "clip_001.json"
    copied.write_text(clip_manifest.read_text(encoding="utf-8"), encoding="utf-8")
    (dataset_root / "dataset_manifest.json").write_text(
        json.dumps({
            "dataset_type": "rbccps_measurement",
            "clips": [{"clip_id": "clip_001", "manifest": "clips/clip_001.json"}],
        }),
        encoding="utf-8",
    )

    report = check_dataset_readiness(dataset_root, require_annotations=False, ensure_models=False)
    assert report.ready is True
    assert report.clips == 1
    assert report.frames == 1
    assert report.tracks == 1


def test_pseudo_manifest_from_images_runs_measurement_pipeline(tmp_path: Path):
    from PIL import Image, ImageDraw

    image_paths = []
    for index in range(2):
        image = Image.new("RGB", (320, 180), (8, 9, 12))
        draw = ImageDraw.Draw(image)
        draw.ellipse((154 + index, 26, 170 + index, 42), fill=(255, 244, 190))
        path = tmp_path / f"source_{index + 1}.jpg"
        image.save(path)
        image_paths.append(path)

    manifest_path = tmp_path / "pseudo_clip" / "clip_manifest.json"
    manifest = build_pseudo_manifest(
        image_paths,
        manifest_path,
        PseudoManifestOptions(clip_id="pseudo_clip_test", copy_images=True, max_lamps_per_frame=1),
    )

    assert manifest_path.exists()
    assert len(manifest.frames) == 2
    assert len(manifest.tracks) == 2
    assert manifest.tracks[0].source_model == "pseudo_bright_region_estimator_v1"
    assert (manifest_path.parent / manifest.frames[0].image_uri).exists()

    reports = run_clip_to_directory(manifest_path, tmp_path / "pseudo_run")
    assert len(reports) == 1
    assert reports[0].lamp_track_id == "pseudo_lamp_1"
