from __future__ import annotations

import base64
import json
from pathlib import Path

from PIL import Image

from rbccps_annotator.auto_polygon import prompt_segmenter_status, propose_auto_polygon
from rbccps_annotator.exports import export_measurement, export_yolo
from rbccps_annotator.workspace import create_workspace_from_frames


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def test_frame_workspace_and_exports(tmp_path: Path) -> None:
    frames = tmp_path / "frames"
    frames.mkdir()
    (frames / "frame_0001.png").write_bytes(PNG_1X1)
    workspace = tmp_path / "workspace"

    create_workspace_from_frames(frames, workspace, "smoke", "route_a", "clip_a", "train", "raw_frames")
    manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
    key = manifest["items"][0]["key"]

    review_dir = workspace / "reviews" / "items"
    review_dir.mkdir(parents=True)
    (review_dir / f"{key}.json").write_text(
        json.dumps(
            {
                "schema_version": "measurement_annotator_v1",
                "item_key": key,
                "review_status": "accepted",
                "boxes": [
                    {
                        "box_id": "box_001",
                        "class_name": "streetlight",
                        "bbox_xyxy": [0, 0, 1, 1],
                        "track_id": "track_1",
                        "status": "accepted",
                        "source": "manual",
                    }
                ],
                "polygons": [
                    {
                        "polygon_id": "poly_001",
                        "surface_type": "building_facade",
                        "points": [[0, 0], [1, 0], [1, 1]],
                        "augmentation_allowed": True,
                        "can_confound_streetlight": True,
                    }
                ],
                "measurement": {
                    "lamp_status": [{"track_id": "track_1", "status": "on"}],
                    "public_space_regions": [],
                    "affected_regions": [],
                    "visibility_labels": [{"track_id": "track_1", "visibility_class": "adequate"}],
                    "attribution_labels": [{"track_id": "track_1", "attribution_class": "certain"}],
                    "lux_points": [{"track_id": "track_1", "point_type": "P1", "lux_value": "1.0", "x": 0, "y": 0}],
                    "qa_flags": [{"track_id": "track_1", "flag": "smoke"}],
                },
            }
        ),
        encoding="utf-8",
    )

    export_yolo(workspace, workspace / "exports" / "yolo")
    export_measurement(workspace, workspace / "exports" / "measurement")

    assert (workspace / "exports" / "yolo" / "classes.txt").read_text(encoding="utf-8") == "streetlight\n"
    assert (workspace / "exports" / "yolo" / "labels" / f"{key}.txt").read_text(encoding="utf-8").startswith("0 ")
    assert (workspace / "exports" / "measurement" / "lamp_status.csv").read_text(encoding="utf-8").count("track_1") == 1


def test_auto_polygon_returns_polygon_and_overlap_warning(tmp_path: Path) -> None:
    image_path = tmp_path / "surface.png"
    image = Image.new("RGB", (80, 60), (20, 20, 24))
    for x in range(10, 55):
        for y in range(8, 45):
            image.putpixel((x, y), (90, 95, 100))
    image.save(image_path)

    result = propose_auto_polygon(
        image_path=image_path,
        bbox_xyxy=[8, 6, 58, 48],
        protected_boxes=[[45, 20, 70, 50]],
        margin_px=4,
        repo_root=tmp_path,
    )

    assert len(result.points) >= 3
    assert result.engine in {"opencv_grabcut_fallback", "pil_edge_fallback", "rectangle_fallback"}
    assert result.model_status in {"ready", "missing"}
    assert any("lamp box" in warning for warning in result.warnings)


def test_prompt_segmenter_status_reports_missing_assets(tmp_path: Path) -> None:
    status = prompt_segmenter_status(tmp_path)
    assert status["ready"] is False
    assert status["weights_present"] is False
    assert status["engine"] == "FastSAM-s"
