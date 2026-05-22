from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROMPT_SEGMENTER_ROOT = Path("models") / "annotator" / "prompt_segmenter"
FASTSAM_FILENAME = "FastSAM-s.pt"

_FASTSAM_MODEL: Any | None = None
_FASTSAM_PATH: Path | None = None


@dataclass(frozen=True)
class SegmenterStatus:
    root: Path
    weights_path: Path
    weights_present: bool
    package_available: bool
    ready: bool
    engine: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "weights_path": str(self.weights_path),
            "weights_present": self.weights_present,
            "package_available": self.package_available,
            "ready": self.ready,
            "engine": self.engine,
        }


def segmenter_root(repo_root: Path | None = None) -> Path:
    return (repo_root or Path.cwd()) / PROMPT_SEGMENTER_ROOT


def fastsam_weights_path(repo_root: Path | None = None) -> Path:
    return segmenter_root(repo_root) / FASTSAM_FILENAME


def status(repo_root: Path | None = None) -> SegmenterStatus:
    _prepare_ultralytics_config(repo_root)
    weights = fastsam_weights_path(repo_root)
    available = _module_available("ultralytics")
    return SegmenterStatus(
        root=segmenter_root(repo_root),
        weights_path=weights,
        weights_present=weights.exists(),
        package_available=available,
        ready=weights.exists() and available,
        engine="FastSAM-s",
    )


def download_fastsam(repo_root: Path | None = None, force: bool = False) -> Path:
    target = fastsam_weights_path(repo_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not force:
        return target

    _prepare_ultralytics_config(repo_root)
    try:
        from ultralytics import FastSAM  # type: ignore
    except Exception as error:
        raise RuntimeError("Ultralytics is required to download FastSAM-s. Use the project YOLO venv.") from error

    previous_cwd = Path.cwd()
    try:
        os.chdir(target.parent)
        FastSAM(FASTSAM_FILENAME)
    finally:
        os.chdir(previous_cwd)

    downloaded = target.parent / FASTSAM_FILENAME
    if downloaded.exists():
        return downloaded

    candidates = sorted(target.parent.rglob(FASTSAM_FILENAME))
    if candidates:
        shutil.copy2(candidates[0], target)
        return target
    raise RuntimeError(f"FastSAM download completed but {target} was not found.")


def propose_mask_polygon(image_path: Path, bbox_xyxy: list[float], repo_root: Path | None = None) -> tuple[list[list[float]], str, float]:
    segmenter_status = status(repo_root)
    if not segmenter_status.ready:
        return [], "", 0.0

    _prepare_ultralytics_config(repo_root)
    model = _load_fastsam(segmenter_status.weights_path)
    try:
        result = model(str(image_path), bboxes=[bbox_xyxy], verbose=False, retina_masks=True)[0]
    except TypeError:
        result = model(str(image_path), bboxes=[bbox_xyxy], verbose=False)[0]
    except Exception:
        return [], "", 0.0

    masks = getattr(result, "masks", None)
    if masks is None:
        return [], "", 0.0

    polygon = _polygon_from_ultralytics_masks(masks)
    if len(polygon) < 3:
        return [], "", 0.0
    confidence = _mask_confidence(masks, bbox_xyxy)
    return polygon, "fastsam_s", confidence


def _load_fastsam(weights_path: Path) -> Any:
    global _FASTSAM_MODEL, _FASTSAM_PATH
    if _FASTSAM_MODEL is not None and _FASTSAM_PATH == weights_path:
        return _FASTSAM_MODEL
    from ultralytics import FastSAM  # type: ignore

    _FASTSAM_MODEL = FastSAM(str(weights_path))
    _FASTSAM_PATH = weights_path
    return _FASTSAM_MODEL


def _prepare_ultralytics_config(repo_root: Path | None = None) -> None:
    config_dir = (repo_root or Path.cwd()) / ".cache" / "ultralytics"
    config_dir.mkdir(parents=True, exist_ok=True)
    os.environ["YOLO_CONFIG_DIR"] = str(config_dir)


def _polygon_from_ultralytics_masks(masks: Any) -> list[list[float]]:
    xy = getattr(masks, "xy", None)
    if xy:
        longest = max(xy, key=lambda item: len(item))
        points = [[float(point[0]), float(point[1])] for point in longest]
        return _simplify_points(points, max_points=36)
    data = getattr(masks, "data", None)
    if data is None or len(data) == 0:
        return []
    mask = data[0]
    try:
        mask_np = mask.detach().cpu().numpy()
    except Exception:
        mask_np = mask
    return _mask_to_polygon(mask_np)


def _mask_to_polygon(mask_np: Any) -> list[list[float]]:
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except Exception:
        return []
    binary = (mask_np > 0.5).astype("uint8") * 255
    contours, _hierarchy = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return []
    contour = max(contours, key=cv2.contourArea)
    if float(cv2.contourArea(contour)) < 20:
        return []
    epsilon = max(3.0, 0.026 * cv2.arcLength(contour, True))
    approx = cv2.approxPolyDP(contour, epsilon, True)
    return [[float(point[0][0]), float(point[0][1])] for point in approx][:36]


def _simplify_points(points: list[list[float]], max_points: int) -> list[list[float]]:
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore

        contour = np.array(points, dtype="float32").reshape((-1, 1, 2))
        epsilon = max(3.0, 0.024 * cv2.arcLength(contour, True))
        approx = cv2.approxPolyDP(contour, epsilon, True)
        simplified = [[float(point[0][0]), float(point[0][1])] for point in approx]
        if len(simplified) >= 3:
            points = simplified
    except Exception:
        pass
    if len(points) <= max_points:
        return points
    step = max(1, len(points) // max_points)
    return points[::step][:max_points]


def _mask_confidence(masks: Any, bbox_xyxy: list[float]) -> float:
    data = getattr(masks, "data", None)
    if data is None or len(data) == 0:
        return 0.78
    try:
        mask_np = data[0].detach().cpu().numpy()
        area = float((mask_np > 0.5).sum())
    except Exception:
        return 0.78
    x1, y1, x2, y2 = [float(value) for value in bbox_xyxy]
    box_area = max(1.0, (x2 - x1) * (y2 - y1))
    return round(max(0.35, min(0.94, area / box_area)), 3)


def _module_available(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False
