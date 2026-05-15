from __future__ import annotations

import argparse
import csv
import json
import re
import threading
import time
import urllib.parse
import webbrowser
from collections import defaultdict
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import build_annotation_corpus as seed_utils


ROOT = Path(__file__).resolve().parents[2]
DATASETS_ROOT = ROOT / "datasets"
CURRENT_REVIEWS_ROOT = DATASETS_ROOT / "derived" / "annotation_automation" / "reviews"
CURRENT_V2_ROOT = DATASETS_ROOT / "derived" / "annotation_automation_v2"
OUTPUT_ROOT = DATASETS_ROOT / "derived" / "annotation_click_review"
APP_DATA_ROOT = OUTPUT_ROOT / "app_data"
REVIEWS_ROOT = OUTPUT_ROOT / "reviews"

MODE_ORDER = ["jobin_positive", "arindam_positive", "negative_review"]

MODE_BASELINE_COMPLETED = {
    "jobin_positive": 87,
}

MODE_LABELS = {
    "jobin_positive": "Jobin Positive Review",
    "arindam_positive": "Arindam Positive Review",
    "negative_review": "Hard-Negative Review",
}

POSITIVE_DECISIONS = [
    {"id": "keep", "label": "Keep"},
    {"id": "fix", "label": "Fix"},
    {"id": "exclude", "label": "Exclude"},
]

FIX_REASONS = [
    {"id": "fix_full_visible_luminaire_extent", "label": "Fix Full Luminaire Extent"},
    {"id": "fix_loose_dark_region", "label": "Fix Loose Dark Region"},
    {"id": "fix_pole_tree_merge", "label": "Fix Pole/Tree Merge"},
    {"id": "fix_off_center", "label": "Fix Off Center"},
    {"id": "fix_box_too_small", "label": "Fix Box Too Small"},
    {"id": "fix_box_too_large", "label": "Fix Box Too Large"},
]

EXCLUDE_REASONS = [
    {"id": "exclude_occluded", "label": "Exclude Occluded"},
    {"id": "exclude_truncated", "label": "Exclude Truncated"},
    {"id": "exclude_glare_blob", "label": "Exclude Glare Blob"},
    {"id": "exclude_ambiguous_source", "label": "Exclude Ambiguous Source"},
    {"id": "exclude_pole_tree_dominated", "label": "Exclude Pole/Tree Dominated"},
    {"id": "exclude_not_full_visible_luminaire", "label": "Exclude Not Full Visible Luminaire"},
]

SCENE_BUCKETS = [
    {"id": "quiet_residential_lane", "label": "Quiet Residential Lane"},
    {"id": "busy_arterial_road", "label": "Busy Arterial Road"},
    {"id": "heavy_glare_traffic", "label": "Heavy Glare/Traffic"},
]

NEGATIVE_DECISIONS = [
    {"id": "clean_negative", "label": "Clean Negative"},
    {"id": "promote_to_positive_review", "label": "Promote to Positive Review"},
    {"id": "exclude_ambiguous_visibility", "label": "Exclude Ambiguous Visibility"},
]

FRAME_NUM_RE = re.compile(r"(\d+)")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def frame_sort_key(value: str) -> tuple[int, str]:
    match = FRAME_NUM_RE.search(value)
    if not match:
        return (0, value)
    return (int(match.group(1)), value)


def output_fieldnames_for_mode(mode: str) -> list[str]:
    if mode == "negative_review":
        return [
            "key",
            "review_candidate_id",
            "source_pool",
            "dataset_id",
            "clip_id",
            "frame_id",
            "image_path",
            "primary_decision",
            "secondary_reason",
            "scene_bucket",
            "updated_boxes_json",
            "review_timestamp",
        ]
    return [
        "key",
        "image_uid",
        "dataset_id",
        "clip_id",
        "frame_id",
        "image_path",
        "annotation_count",
        "current_split_v2",
        "primary_decision",
        "secondary_reason",
        "scene_bucket",
        "updated_boxes_json",
        "review_timestamp",
    ]


def mode_csv_path(mode: str) -> Path:
    return REVIEWS_ROOT / f"{mode}.csv"


def mode_json_path(mode: str) -> Path:
    return APP_DATA_ROOT / f"{mode}.json"


def mode_subset_keys_path(mode: str) -> Path:
    return REVIEWS_ROOT / f"{mode}_subset_keys.txt"


def signoff_path() -> Path:
    return REVIEWS_ROOT / "mode_signoff.json"


@dataclass
class ReviewItem:
    key: str
    review_id: str
    dataset_id: str
    clip_id: str
    frame_id: str
    image_path: str
    width: int
    height: int
    boxes: list[list[float]]
    annotation_count: int
    current_split_v2: str
    source_pool: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "review_id": self.review_id,
            "dataset_id": self.dataset_id,
            "clip_id": self.clip_id,
            "frame_id": self.frame_id,
            "image_path": self.image_path,
            "width": self.width,
            "height": self.height,
            "boxes": self.boxes,
            "annotation_count": self.annotation_count,
            "current_split_v2": self.current_split_v2,
            "source_pool": self.source_pool,
        }


class ReviewRepository:
    def __init__(self) -> None:
        ensure_dir(APP_DATA_ROOT)
        ensure_dir(REVIEWS_ROOT)
        self.lock = threading.Lock()
        self.mode_items = self._build_items()
        self.reviews_by_mode = self._load_reviews()
        self.signoffs = self._load_signoffs()
        self._write_app_data()
        for mode in MODE_ORDER:
            self._rewrite_mode_csv(mode)
        self._rewrite_secondary_exports()

    def _build_items(self) -> dict[str, list[ReviewItem]]:
        split_lookup: dict[str, str] = {}
        for row in load_csv(CURRENT_V2_ROOT / "manifests" / "merged_manifest_v2.csv"):
            split_lookup[row["image_uid"]] = row["assigned_split"]

        jobin_records, jobin_annotations = seed_utils.load_jobin_source()
        arindam_records, arindam_annotations = seed_utils.load_arindam_source()

        items_by_mode: dict[str, list[ReviewItem]] = {
            "jobin_positive": [],
            "arindam_positive": [],
            "negative_review": [],
        }

        for dataset_name, records, annotations, mode in (
            ("jobin", jobin_records, jobin_annotations, "jobin_positive"),
            ("arindam", arindam_records, arindam_annotations, "arindam_positive"),
        ):
            boxes_by_uid: dict[str, list[list[float]]] = defaultdict(list)
            for ann in annotations:
                boxes_by_uid[ann["image_uid"]].append(seed_utils.coerce_bbox(ann["bbox"]))

            positive_records = [
                record
                for record in records
                if record.dataset_id == dataset_name and record.has_annotation and boxes_by_uid.get(record.image_uid)
            ]
            positive_records.sort(key=lambda item: (item.clip_id, frame_sort_key(item.frame_id), item.image_uid))
            for index, record in enumerate(positive_records, start=1):
                items_by_mode[mode].append(
                    ReviewItem(
                        key=record.image_uid,
                        review_id=f"{dataset_name}_pos_{index:05d}",
                        dataset_id=record.dataset_id,
                        clip_id=record.clip_id,
                        frame_id=record.frame_id,
                        image_path=str(record.source_image_path),
                        width=record.width,
                        height=record.height,
                        boxes=boxes_by_uid[record.image_uid],
                        annotation_count=record.annotation_count,
                        current_split_v2=split_lookup.get(record.image_uid, ""),
                    )
                )

        negative_rows = load_csv(CURRENT_REVIEWS_ROOT / "hard_negative_review_manifest.csv")
        negative_rows.sort(key=lambda row: (row["source_pool"], row["clip_id"], frame_sort_key(row["frame_id"]), row["review_candidate_id"]))
        for row in negative_rows:
            items_by_mode["negative_review"].append(
                ReviewItem(
                    key=row["review_candidate_id"],
                    review_id=row["review_candidate_id"],
                    dataset_id=row["dataset_id"],
                    clip_id=row["clip_id"],
                    frame_id=row["frame_id"],
                    image_path=row["image_path"],
                    width=0,
                    height=0,
                    boxes=[],
                    annotation_count=0,
                    current_split_v2="",
                    source_pool=row["source_pool"],
                )
            )

        return items_by_mode

    def _load_reviews(self) -> dict[str, dict[str, dict[str, str]]]:
        reviews: dict[str, dict[str, dict[str, str]]] = {mode: {} for mode in MODE_ORDER}
        for mode in MODE_ORDER:
            for row in load_csv(mode_csv_path(mode)):
                reviews[mode][row["key"]] = row
        return reviews

    def _load_signoffs(self) -> dict[str, bool]:
        payload = read_json(signoff_path(), {})
        return {mode: bool(payload.get(mode, False)) for mode in MODE_ORDER}

    def _load_subset_keys(self, mode: str) -> set[str]:
        path = mode_subset_keys_path(mode)
        if not path.exists():
            return set()
        return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}

    def _write_signoffs(self) -> None:
        write_json(signoff_path(), self.signoffs)

    def _write_app_data(self) -> None:
        for mode in MODE_ORDER:
            write_json(mode_json_path(mode), [item.to_dict() for item in self.mode_items[mode]])

    def _rewrite_mode_csv(self, mode: str) -> None:
        fieldnames = output_fieldnames_for_mode(mode)
        order_lookup = {item.key: index for index, item in enumerate(self.mode_items[mode])}
        rows = sorted(self.reviews_by_mode[mode].values(), key=lambda row: order_lookup.get(row["key"], 10**9))
        write_csv(mode_csv_path(mode), rows, fieldnames)

    def _rewrite_secondary_exports(self) -> None:
        promoted_rows: list[dict[str, str]] = []
        excluded_rows: list[dict[str, str]] = []
        scene_rows: list[dict[str, str]] = []

        for mode in MODE_ORDER:
            for row in self.reviews_by_mode[mode].values():
                if row.get("scene_bucket"):
                    scene_rows.append(
                        {
                            "mode": mode,
                            "key": row["key"],
                            "dataset_id": row["dataset_id"],
                            "clip_id": row["clip_id"],
                            "frame_id": row["frame_id"],
                            "scene_bucket": row["scene_bucket"],
                            "primary_decision": row["primary_decision"],
                            "secondary_reason": row.get("secondary_reason", ""),
                            "review_timestamp": row["review_timestamp"],
                        }
                    )
                if mode == "negative_review" and row["primary_decision"] == "promote_to_positive_review":
                    promoted_rows.append(
                        {
                            "source_review_key": row["key"],
                            "review_candidate_id": row["review_candidate_id"],
                            "source_pool": row["source_pool"],
                            "dataset_id": row["dataset_id"],
                            "clip_id": row["clip_id"],
                            "frame_id": row["frame_id"],
                            "image_path": row["image_path"],
                            "scene_bucket": row["scene_bucket"],
                            "review_timestamp": row["review_timestamp"],
                        }
                    )
                if row["primary_decision"] == "exclude" or row["primary_decision"] == "exclude_ambiguous_visibility":
                    excluded_rows.append(
                        {
                            "mode": mode,
                            "key": row["key"],
                            "dataset_id": row["dataset_id"],
                            "clip_id": row["clip_id"],
                            "frame_id": row["frame_id"],
                            "image_path": row["image_path"],
                            "primary_decision": row["primary_decision"],
                            "secondary_reason": row.get("secondary_reason", ""),
                            "scene_bucket": row.get("scene_bucket", ""),
                            "review_timestamp": row["review_timestamp"],
                        }
                    )

        write_csv(
            REVIEWS_ROOT / "promoted_positive_queue.csv",
            promoted_rows,
            [
                "source_review_key",
                "review_candidate_id",
                "source_pool",
                "dataset_id",
                "clip_id",
                "frame_id",
                "image_path",
                "scene_bucket",
                "review_timestamp",
            ],
        )
        write_csv(
            REVIEWS_ROOT / "excluded_items.csv",
            excluded_rows,
            [
                "mode",
                "key",
                "dataset_id",
                "clip_id",
                "frame_id",
                "image_path",
                "primary_decision",
                "secondary_reason",
                "scene_bucket",
                "review_timestamp",
            ],
        )
        write_csv(
            REVIEWS_ROOT / "scene_bucket_audit.csv",
            scene_rows,
            [
                "mode",
                "key",
                "dataset_id",
                "clip_id",
                "frame_id",
                "scene_bucket",
                "primary_decision",
                "secondary_reason",
                "review_timestamp",
            ],
        )

    def mode_status(self, mode: str) -> dict[str, Any]:
        total = len(self.mode_items[mode])
        baseline_completed = min(MODE_BASELINE_COMPLETED.get(mode, 0), total)
        active_keys = self._active_ordered_keys(mode)
        active_items = [item for item in self.mode_items[mode] if item.key in set(active_keys)]
        reviewed = sum(
            1
            for index, item in enumerate(self.mode_items[mode], start=1)
            if index <= baseline_completed or item.key in self.reviews_by_mode[mode]
        )
        active_reviewed = sum(1 for item in active_items if item.key in self.reviews_by_mode[mode])
        active_pending = sum(1 for item in active_items if item.key not in self.reviews_by_mode[mode])
        subset_enabled = bool(self._load_subset_keys(mode))
        stage_complete = (reviewed >= total) or (subset_enabled and active_pending == 0)
        previous_modes = MODE_ORDER[: MODE_ORDER.index(mode)]
        unlocked = all(self.signoffs.get(previous_mode, False) for previous_mode in previous_modes)
        return {
            "mode": mode,
            "label": MODE_LABELS[mode],
            "total": total,
            "reviewed": reviewed,
            "remaining": total - reviewed,
            "complete": reviewed >= total,
            "stage_complete": stage_complete,
            "signed_off": self.signoffs.get(mode, False),
            "unlocked": unlocked,
            "baseline_completed": baseline_completed,
            "active_total": len(active_keys),
            "active_reviewed": active_reviewed,
            "active_pending": active_pending,
            "subset_enabled": subset_enabled,
        }

    def _ordered_keys(self, mode: str) -> list[str]:
        return [item.key for item in self.mode_items[mode]]

    def _active_ordered_keys(self, mode: str) -> list[str]:
        ordered_keys = self._ordered_keys(mode)
        baseline_completed = MODE_BASELINE_COMPLETED.get(mode, 0)
        active_keys = ordered_keys[baseline_completed:]
        subset_keys = self._load_subset_keys(mode)
        if not subset_keys:
            return active_keys
        reviewed_keys = set(self.reviews_by_mode[mode])
        filtered: list[str] = []
        for key in active_keys:
            if key in reviewed_keys or key in subset_keys:
                filtered.append(key)
        return filtered

    def bootstrap(self) -> dict[str, Any]:
        statuses = [self.mode_status(mode) for mode in MODE_ORDER]
        current_mode = next((status["mode"] for status in statuses if status["unlocked"] and not status["signed_off"]), MODE_ORDER[-1])
        return {
            "modes": statuses,
            "current_mode": current_mode,
            "positive_decisions": POSITIVE_DECISIONS,
            "fix_reasons": FIX_REASONS,
            "exclude_reasons": EXCLUDE_REASONS,
            "scene_buckets": SCENE_BUCKETS,
            "negative_decisions": NEGATIVE_DECISIONS,
        }

    def get_item(self, mode: str, key: str | None = None) -> dict[str, Any] | None:
        if mode not in self.mode_items:
            return None
        item_lookup = {item.key: item for item in self.mode_items[mode]}
        ordered_keys = self._ordered_keys(mode)
        active_keys = self._active_ordered_keys(mode)
        if key:
            if key not in active_keys:
                return None
            item = item_lookup.get(key)
            if not item:
                return None
        else:
            item = next((item_lookup[item_key] for item_key in active_keys if item_key not in self.reviews_by_mode[mode]), None)
            if not item:
                return None
        current_index = ordered_keys.index(item.key)
        current_active_index = active_keys.index(item.key)
        prev_key = active_keys[current_active_index - 1] if current_active_index > 0 else None
        next_key = active_keys[current_active_index + 1] if current_active_index + 1 < len(active_keys) else None
        payload = item.to_dict()
        payload["existing_review"] = self.reviews_by_mode[mode].get(item.key)
        payload["mode_status"] = self.mode_status(mode)
        payload["position"] = current_index + 1
        payload["active_total"] = len(active_keys)
        payload["active_position"] = current_active_index + 1
        payload["prev_key"] = prev_key
        payload["next_key"] = next_key
        return payload

    def save_review(self, payload: dict[str, Any]) -> dict[str, Any]:
        mode = payload["mode"]
        if mode not in MODE_ORDER:
            raise ValueError("Unknown mode.")
        item_lookup = {item.key: item for item in self.mode_items[mode]}
        key = payload["key"]
        item = item_lookup.get(key)
        if not item:
            raise ValueError("Unknown review item.")

        primary_decision = payload.get("primary_decision", "").strip()
        secondary_reason = payload.get("secondary_reason", "").strip()
        scene_bucket = payload.get("scene_bucket", "").strip()
        updated_boxes = payload.get("updated_boxes", [])

        if mode == "negative_review":
            allowed_primary = {item["id"] for item in NEGATIVE_DECISIONS}
            if primary_decision not in allowed_primary:
                raise ValueError("Invalid negative review decision.")
            if not scene_bucket:
                raise ValueError("Scene bucket is required.")
        else:
            allowed_primary = {item["id"] for item in POSITIVE_DECISIONS}
            if primary_decision not in allowed_primary:
                raise ValueError("Invalid positive review decision.")
            if primary_decision == "fix":
                allowed_secondary = {item["id"] for item in FIX_REASONS}
                if secondary_reason not in allowed_secondary:
                    raise ValueError("Fix reason is required.")
                if not isinstance(updated_boxes, list) or not updated_boxes:
                    raise ValueError("At least one replacement box is required for fixes.")
            elif primary_decision == "exclude":
                allowed_secondary = {item["id"] for item in EXCLUDE_REASONS}
                if secondary_reason not in allowed_secondary:
                    raise ValueError("Exclude reason is required.")
            if not scene_bucket:
                raise ValueError("Scene bucket is required.")

        row: dict[str, str] = {
            "key": item.key,
            "dataset_id": item.dataset_id,
            "clip_id": item.clip_id,
            "frame_id": item.frame_id,
            "image_path": item.image_path,
            "primary_decision": primary_decision,
            "secondary_reason": secondary_reason,
            "scene_bucket": scene_bucket,
            "updated_boxes_json": json.dumps(updated_boxes if primary_decision == "fix" else item.boxes),
            "review_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        if mode == "negative_review":
            row.update(
                {
                    "review_candidate_id": item.key,
                    "source_pool": item.source_pool,
                }
            )
        else:
            row.update(
                {
                    "image_uid": item.key,
                    "annotation_count": str(item.annotation_count),
                    "current_split_v2": item.current_split_v2,
                }
            )

        with self.lock:
            self.reviews_by_mode[mode][item.key] = row
            self._rewrite_mode_csv(mode)
            self._rewrite_secondary_exports()
        return self.mode_status(mode)

    def signoff_mode(self, mode: str) -> dict[str, Any]:
        status = self.mode_status(mode)
        if not status["unlocked"]:
            raise ValueError("Mode is locked until prior signoff is complete.")
        if not status["stage_complete"]:
            raise ValueError("Mode cannot be signed off until the active review queue is complete.")
        with self.lock:
            self.signoffs[mode] = True
            self._write_signoffs()
        return self.bootstrap()


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Streetlight Review App</title>
  <style>
    :root {
      --bg: #f5efe5;
      --panel: rgba(255, 251, 245, 0.88);
      --ink: #171410;
      --muted: #6d6458;
      --accent: #0f5a4a;
      --accent2: #b14f2d;
      --line: rgba(114, 96, 79, 0.22);
      --ok: #2d6a4f;
      --warn: #a15c00;
      --bad: #9c2f2f;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", "Helvetica Neue", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(17, 90, 74, 0.10), transparent 26%),
        radial-gradient(circle at top right, rgba(177, 79, 45, 0.10), transparent 24%),
        linear-gradient(180deg, #f7f1e8 0%, #ece3d5 100%);
      color: var(--ink);
    }
    .shell {
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 18px;
      padding: 18px;
      min-height: 100vh;
    }
    .panel {
      background: var(--panel);
      backdrop-filter: blur(18px);
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: 0 18px 50px rgba(20, 20, 20, 0.08);
      padding: 16px;
    }
    h1, h2, h3, p { margin-top: 0; }
    h1 {
      font-size: 32px;
      letter-spacing: -0.04em;
      margin-bottom: 10px;
    }
    .hero {
      padding: 12px 2px 14px;
      border-bottom: 1px solid var(--line);
      margin-bottom: 14px;
    }
    .hero p {
      color: var(--muted);
      line-height: 1.45;
      margin-bottom: 0;
    }
    .mode-list button, .action-grid button, .secondary-grid button, .scene-grid button, .toolbar button, .signoff button {
      width: 100%;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      padding: 12px 14px;
      border-radius: 12px;
      text-align: left;
      cursor: pointer;
      margin-bottom: 8px;
      font-size: 14px;
    }
    .mode-list button.active, .action-grid button.active, .secondary-grid button.active, .scene-grid button.active, .toolbar button.active {
      background: #e5f1ed;
      border-color: var(--accent);
    }
    .mode-list button {
      padding: 14px;
      border-radius: 16px;
      background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(250,246,241,0.95));
    }
    .mode-list button:disabled {
      opacity: 0.45;
      cursor: not-allowed;
    }
    .counts {
      font-size: 12px;
      color: var(--muted);
      margin-top: 4px;
    }
    .canvas-wrap {
      background: #161616;
      border-radius: 20px;
      overflow: hidden;
      border: 1px solid #000;
      min-height: 420px;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
    }
    canvas {
      max-width: 100%;
      display: block;
      cursor: crosshair;
    }
    .meta-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      margin-bottom: 16px;
    }
    .meta-card {
      background: linear-gradient(180deg, rgba(255,255,255,0.78), rgba(248,241,232,0.94));
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 10px;
      font-size: 13px;
    }
    .meta-card strong {
      display: block;
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      margin-bottom: 6px;
    }
    .workspace {
      display: grid;
      grid-template-columns: 1fr 360px;
      gap: 18px;
    }
    .review-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
      margin-bottom: 14px;
      padding: 12px 14px;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(255,255,255,0.78), rgba(247,240,232,0.95));
    }
    .review-title {
      margin: 0;
      font-size: 22px;
      letter-spacing: -0.03em;
    }
    .review-subtitle {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 13px;
    }
    .nav-strip {
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
    }
    .nav-strip button {
      border: 1px solid var(--line);
      background: white;
      border-radius: 12px;
      padding: 10px 12px;
      cursor: pointer;
      font-weight: 600;
    }
    .nav-strip button:disabled {
      opacity: 0.45;
      cursor: not-allowed;
    }
    .position-chip {
      font-size: 12px;
      color: var(--muted);
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 8px 12px;
      background: rgba(255,255,255,0.85);
    }
    .hidden { display: none; }
    .section-label {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 8px;
    }
    .toolbar {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      margin-top: 12px;
    }
    .toolbar button { text-align: center; }
    .status-pill {
      display: inline-block;
      font-size: 12px;
      border-radius: 999px;
      padding: 6px 10px;
      border: 1px solid var(--line);
      margin-right: 6px;
      margin-bottom: 8px;
      background: #fff;
    }
    .footer {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 16px;
    }
    .footer button {
      flex: 1;
      border-radius: 12px;
      border: none;
      padding: 14px;
      font-weight: 600;
      cursor: pointer;
    }
    .save-btn { background: var(--accent); color: white; }
    .refresh-btn { background: #eee2d2; color: var(--ink); }
    .signoff button { background: #efe7da; font-weight: 600; }
    .message {
      min-height: 22px;
      color: var(--accent2);
      font-size: 13px;
      margin: 8px 0 0;
    }
    .hint-card {
      margin-top: 14px;
      padding: 12px;
      border-radius: 16px;
      background: linear-gradient(180deg, rgba(15,90,74,0.08), rgba(15,90,74,0.02));
      border: 1px solid rgba(15,90,74,0.14);
      font-size: 13px;
      color: #284238;
      line-height: 1.45;
    }
    .hint-card strong {
      display: block;
      margin-bottom: 6px;
      color: var(--accent);
    }
  </style>
</head>
<body>
  <div class="shell">
    <div class="panel">
      <div class="hero">
        <h1>Streetlight Review</h1>
        <p>Click-only audit for full-visible-luminaire positives, hard negatives, and scene buckets.</p>
      </div>
      <div id="modeList" class="mode-list"></div>
      <div class="signoff hidden" id="signoffWrap">
        <button id="signoffBtn">Sign Off Current Mode</button>
      </div>
      <div class="message" id="modeMessage"></div>
    </div>
    <div class="panel">
      <div id="workspace" class="workspace hidden">
        <div>
          <div class="review-header">
            <div>
              <h2 class="review-title" id="reviewTitle">Loading</h2>
              <p class="review-subtitle" id="reviewSubtitle"></p>
            </div>
            <div class="nav-strip">
              <button id="prevBtn">Previous</button>
              <button id="nextBtn">Next</button>
              <span class="position-chip" id="positionChip">0 / 0</span>
            </div>
          </div>
          <div class="meta-grid" id="metaGrid"></div>
          <div class="canvas-wrap">
            <canvas id="reviewCanvas"></canvas>
          </div>
          <div id="boxTools" class="hidden">
            <div class="section-label">Fix Box Tools</div>
            <div class="toolbar">
              <button id="toggleDrawBtn">Enable Box Draw</button>
              <button id="undoBoxBtn">Undo Last</button>
              <button id="clearBoxesBtn">Clear Boxes</button>
              <button id="resetBoxesBtn">Reset Boxes</button>
            </div>
            <div class="hint-card">
              <strong>Fix workflow</strong>
              Choose `Fix`, pick the reason, select the scene bucket, then click `Enable Box Draw`. Drag new boxes on the image. Use `Clear Boxes` if you want to replace everything.
            </div>
          </div>
        </div>
        <div>
          <div class="section-label">Decision</div>
          <div class="action-grid" id="actionGrid"></div>
          <div id="secondarySection" class="hidden">
            <div class="section-label">Reason</div>
            <div class="secondary-grid" id="secondaryGrid"></div>
          </div>
          <div id="sceneSection" class="hidden">
            <div class="section-label">Scene Bucket</div>
            <div class="scene-grid" id="sceneGrid"></div>
          </div>
          <div class="footer">
            <button class="refresh-btn" id="reloadBtn">Reload Item</button>
            <button class="save-btn" id="saveBtn">Save Review</button>
          </div>
          <div class="message" id="itemMessage"></div>
        </div>
      </div>
      <div id="emptyState">
        <h2>Loading</h2>
      </div>
    </div>
  </div>
  <script>
    const state = {
      bootstrap: null,
      activeMode: null,
      currentItem: null,
      image: null,
      imageScale: 1,
      currentDecision: '',
      currentReason: '',
      currentScene: '',
      editBoxes: [],
      drawingEnabled: false,
      dragStart: null,
      dragCurrent: null,
    };

    const canvas = document.getElementById('reviewCanvas');
    const ctx = canvas.getContext('2d');

    async function fetchJson(url, options={}) {
      const response = await fetch(url, options);
      if (!response.ok) {
        const payload = await response.json().catch(() => ({error: response.statusText}));
        throw new Error(payload.error || response.statusText);
      }
      return response.json();
    }

    function setMessage(id, text) {
      document.getElementById(id).textContent = text || '';
    }

    function syncCanvasCursor() {
      canvas.style.cursor = state.drawingEnabled ? 'crosshair' : 'default';
    }

    function getCanvasPoint(event) {
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      return [
        (event.clientX - rect.left) * scaleX,
        (event.clientY - rect.top) * scaleY,
      ];
    }

    function buildModeList() {
      const wrap = document.getElementById('modeList');
      wrap.innerHTML = '';
      for (const mode of state.bootstrap.modes) {
        const btn = document.createElement('button');
        btn.disabled = !mode.unlocked;
        if (mode.mode === state.activeMode) {
          btn.classList.add('active');
        }
        const baselineNote = mode.baseline_completed ? ` - ${mode.baseline_completed} baseline` : '';
        const subsetNote = mode.subset_enabled ? ` - active ${mode.active_reviewed}/${mode.active_total}` : '';
        btn.innerHTML = `<strong>${mode.label}</strong><div class="counts">${mode.reviewed}/${mode.total} reviewed${subsetNote}${baselineNote}${mode.signed_off ? ' - signed off' : ''}</div>`;
        btn.onclick = () => {
          if (!mode.unlocked) return;
          state.activeMode = mode.mode;
          loadCurrentItem();
        };
        wrap.appendChild(btn);
      }
    }

    function buildButtons(containerId, options, currentValue, onClick) {
      const wrap = document.getElementById(containerId);
      wrap.innerHTML = '';
      for (const option of options) {
        const btn = document.createElement('button');
        btn.textContent = option.label;
        if (option.id === currentValue) {
          btn.classList.add('active');
        }
        btn.onclick = () => onClick(option.id);
        wrap.appendChild(btn);
      }
    }

    function renderMeta(item) {
      document.getElementById('reviewTitle').textContent = `${item.dataset_id} / ${item.clip_id}`;
      document.getElementById('reviewSubtitle').textContent = `${item.frame_id} - ${state.bootstrap.modes.find(m => m.mode === state.activeMode).label}`;
      document.getElementById('positionChip').textContent = `${item.position} / ${item.mode_status.total}`;
      document.getElementById('prevBtn').disabled = !item.prev_key;
      document.getElementById('nextBtn').disabled = !item.next_key;
      const meta = document.getElementById('metaGrid');
      const cards = [
        ['Mode', state.bootstrap.modes.find(m => m.mode === state.activeMode).label],
        ['Dataset', item.dataset_id],
        ['Clip', item.clip_id],
        ['Frame', item.frame_id],
        ['Queue Position', `${item.active_position} / ${item.active_total}`],
        ['Boxes', String(item.boxes.length || item.annotation_count || 0)],
        ['Baseline Completed', String(item.mode_status.baseline_completed || 0)],
        ['Current Split', item.current_split_v2 || item.source_pool || 'n/a'],
      ];
      meta.innerHTML = cards.map(([label, value]) => `<div class="meta-card"><strong>${label}</strong>${value}</div>`).join('');
    }

    function drawCanvas() {
      if (!state.image) return;
      const maxWidth = Math.min(1200, state.image.naturalWidth);
      const scale = maxWidth / state.image.naturalWidth;
      const width = Math.round(state.image.naturalWidth * scale);
      const height = Math.round(state.image.naturalHeight * scale);
      state.imageScale = scale;
      canvas.width = width;
      canvas.height = height;
      ctx.clearRect(0, 0, width, height);
      ctx.drawImage(state.image, 0, 0, width, height);
      ctx.lineWidth = 2;
      ctx.font = '16px Segoe UI';
      for (const box of state.editBoxes) {
        ctx.strokeStyle = '#00c2ff';
        ctx.fillStyle = '#00c2ff';
        const [x, y, w, h] = box;
        ctx.strokeRect(x * scale, y * scale, w * scale, h * scale);
      }
      if (state.dragStart && state.dragCurrent) {
        const [sx, sy] = state.dragStart;
        const [cx, cy] = state.dragCurrent;
        ctx.strokeStyle = '#ffce45';
        ctx.strokeRect(sx, sy, cx - sx, cy - sy);
      }
    }

    async function loadImage() {
      return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
          state.image = img;
          drawCanvas();
          resolve();
        };
        img.onerror = reject;
        img.src = `/image?mode=${encodeURIComponent(state.activeMode)}&key=${encodeURIComponent(state.currentItem.key)}&t=${Date.now()}`;
      });
    }

    function updateDecisionUI() {
      const isNegative = state.activeMode === 'negative_review';
      const keepDrawingState = state.currentDecision === 'fix' && state.drawingEnabled;
      buildButtons('actionGrid', isNegative ? state.bootstrap.negative_decisions : state.bootstrap.positive_decisions, state.currentDecision, (value) => {
        const changed = state.currentDecision !== value;
        state.currentDecision = value;
        state.currentReason = '';
        if (changed) {
          state.currentScene = '';
          state.drawingEnabled = false;
        }
        updateDecisionUI();
      });
      const secondarySection = document.getElementById('secondarySection');
      const sceneSection = document.getElementById('sceneSection');
      const boxTools = document.getElementById('boxTools');
      secondarySection.classList.add('hidden');
      sceneSection.classList.add('hidden');
      boxTools.classList.add('hidden');

      if (!state.currentDecision) return;

      if (isNegative) {
        state.drawingEnabled = false;
        document.getElementById('toggleDrawBtn').classList.remove('active');
        document.getElementById('toggleDrawBtn').textContent = 'Enable Box Draw';
        syncCanvasCursor();
        sceneSection.classList.remove('hidden');
        buildButtons('sceneGrid', state.bootstrap.scene_buckets, state.currentScene, (value) => {
          state.currentScene = value;
          updateDecisionUI();
        });
        return;
      }

      if (state.currentDecision === 'keep') {
        sceneSection.classList.remove('hidden');
        buildButtons('sceneGrid', state.bootstrap.scene_buckets, state.currentScene, (value) => {
          state.currentScene = value;
          updateDecisionUI();
        });
        return;
      }

      secondarySection.classList.remove('hidden');
      if (state.currentDecision === 'fix') {
        buildButtons('secondaryGrid', state.bootstrap.fix_reasons, state.currentReason, (value) => {
          state.currentReason = value;
          updateDecisionUI();
        });
      } else {
        buildButtons('secondaryGrid', state.bootstrap.exclude_reasons, state.currentReason, (value) => {
          state.currentReason = value;
          updateDecisionUI();
        });
      }
      if (state.currentReason) {
        sceneSection.classList.remove('hidden');
        buildButtons('sceneGrid', state.bootstrap.scene_buckets, state.currentScene, (value) => {
          state.currentScene = value;
          updateDecisionUI();
        });
      }
      if (state.currentDecision === 'fix') {
        boxTools.classList.remove('hidden');
        state.drawingEnabled = keepDrawingState;
        document.getElementById('toggleDrawBtn').classList.toggle('active', state.drawingEnabled);
        document.getElementById('toggleDrawBtn').textContent = state.drawingEnabled ? 'Disable Box Draw' : 'Enable Box Draw';
      } else {
        state.drawingEnabled = false;
        document.getElementById('toggleDrawBtn').classList.remove('active');
        document.getElementById('toggleDrawBtn').textContent = 'Enable Box Draw';
      }
      syncCanvasCursor();
    }

    function clearSelectionsFromItem(item) {
      const existing = item.existing_review || null;
      state.currentDecision = existing ? existing.primary_decision || '' : '';
      state.currentReason = existing ? existing.secondary_reason || '' : '';
      state.currentScene = existing ? existing.scene_bucket || '' : '';
      if (existing && existing.updated_boxes_json) {
        try {
          state.editBoxes = JSON.parse(existing.updated_boxes_json);
        } catch (error) {
          state.editBoxes = JSON.parse(JSON.stringify(item.boxes || []));
        }
      } else {
        state.editBoxes = JSON.parse(JSON.stringify(item.boxes || []));
      }
      state.drawingEnabled = false;
      state.dragStart = null;
      state.dragCurrent = null;
      syncCanvasCursor();
    }

    async function loadCurrentItem(key = null) {
      setMessage('modeMessage', '');
      setMessage('itemMessage', '');
      document.getElementById('workspace').classList.add('hidden');
      document.getElementById('emptyState').innerHTML = '<h2>Loading</h2>';
      buildModeList();

      try {
        const params = new URLSearchParams({mode: state.activeMode});
        if (key) {
          params.set('key', key);
        }
        const payload = await fetchJson(`/api/item?${params.toString()}`);
        state.currentItem = payload.item;
        const status = payload.status;
        if (!state.currentItem) {
          const title = status.stage_complete ? `${status.label} stage complete` : `${status.label} complete`;
          const detail = status.subset_enabled
            ? `${status.reviewed}/${status.total} reviewed. Active queue: ${status.active_reviewed}/${status.active_total}.`
            : `${status.reviewed}/${status.total} reviewed.`;
          document.getElementById('emptyState').innerHTML = `<h2>${title}</h2><p>${detail}</p>`;
          const signoffWrap = document.getElementById('signoffWrap');
          if (status.stage_complete && status.unlocked && !status.signed_off) {
            signoffWrap.classList.remove('hidden');
          } else {
            signoffWrap.classList.add('hidden');
          }
          buildModeList();
          return;
        }
        document.getElementById('signoffWrap').classList.add('hidden');
        clearSelectionsFromItem(state.currentItem);
        renderMeta(state.currentItem);
        updateDecisionUI();
        await loadImage();
        document.getElementById('emptyState').innerHTML = '';
        document.getElementById('workspace').classList.remove('hidden');
        buildModeList();
      } catch (error) {
        document.getElementById('emptyState').innerHTML = `<h2>Failed to load</h2><p>${error.message}</p>`;
      }
    }

    async function saveCurrentReview() {
      if (!state.currentItem) return;
      const payload = {
        mode: state.activeMode,
        key: state.currentItem.key,
        primary_decision: state.currentDecision,
        secondary_reason: state.currentReason,
        scene_bucket: state.currentScene,
        updated_boxes: state.editBoxes,
      };
      try {
        await fetchJson('/api/review', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload),
        });
        await loadCurrentItem(state.currentItem.next_key);
      } catch (error) {
        setMessage('itemMessage', error.message);
      }
    }

    async function signoffCurrentMode() {
      try {
        const payload = await fetchJson('/api/signoff', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({mode: state.activeMode}),
        });
        state.bootstrap = payload;
        state.activeMode = payload.current_mode;
        await loadCurrentItem();
      } catch (error) {
        setMessage('modeMessage', error.message);
      }
    }

    canvas.addEventListener('mousedown', (event) => {
      if (!state.drawingEnabled || state.activeMode === 'negative_review' || state.currentDecision !== 'fix') return;
      state.dragStart = getCanvasPoint(event);
      state.dragCurrent = state.dragStart.slice();
      drawCanvas();
    });

    canvas.addEventListener('mousemove', (event) => {
      if (!state.dragStart) return;
      state.dragCurrent = getCanvasPoint(event);
      drawCanvas();
    });

    canvas.addEventListener('mouseup', () => {
      if (!state.dragStart || !state.dragCurrent) return;
      const [sx, sy] = state.dragStart;
      const [cx, cy] = state.dragCurrent;
      const x1 = Math.min(sx, cx);
      const y1 = Math.min(sy, cy);
      const x2 = Math.max(sx, cx);
      const y2 = Math.max(sy, cy);
      const width = x2 - x1;
      const height = y2 - y1;
      state.dragStart = null;
      state.dragCurrent = null;
      if (width > 8 && height > 8) {
        state.editBoxes.push([
          x1 / state.imageScale,
          y1 / state.imageScale,
          width / state.imageScale,
          height / state.imageScale,
        ]);
      }
      drawCanvas();
    });

    document.getElementById('toggleDrawBtn').onclick = () => {
      state.drawingEnabled = !state.drawingEnabled;
      document.getElementById('toggleDrawBtn').classList.toggle('active', state.drawingEnabled);
      document.getElementById('toggleDrawBtn').textContent = state.drawingEnabled ? 'Disable Box Draw' : 'Enable Box Draw';
      syncCanvasCursor();
    };
    document.getElementById('undoBoxBtn').onclick = () => {
      state.editBoxes.pop();
      drawCanvas();
    };
    document.getElementById('clearBoxesBtn').onclick = () => {
      state.editBoxes = [];
      drawCanvas();
    };
    document.getElementById('resetBoxesBtn').onclick = () => {
      state.editBoxes = JSON.parse(JSON.stringify(state.currentItem.boxes || []));
      drawCanvas();
    };
    document.getElementById('reloadBtn').onclick = () => loadCurrentItem();
    document.getElementById('saveBtn').onclick = () => saveCurrentReview();
    document.getElementById('signoffBtn').onclick = () => signoffCurrentMode();
    document.getElementById('prevBtn').onclick = () => {
      if (state.currentItem && state.currentItem.prev_key) {
        loadCurrentItem(state.currentItem.prev_key);
      }
    };
    document.getElementById('nextBtn').onclick = () => {
      if (state.currentItem && state.currentItem.next_key) {
        loadCurrentItem(state.currentItem.next_key);
      }
    };

    async function init() {
      state.bootstrap = await fetchJson('/api/bootstrap');
      state.activeMode = state.bootstrap.current_mode;
      await loadCurrentItem();
    }

    init();
  </script>
</body>
</html>
"""


class ReviewRequestHandler(BaseHTTPRequestHandler):
    repository: ReviewRepository | None = None

    def _send_json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_text(self, content: str, content_type: str = "text/html; charset=utf-8", status: int = HTTPStatus.OK) -> None:
        encoded = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_file(self, path: Path) -> None:
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Image not found.")
            return
        content = path.read_bytes()
        suffix = path.suffix.lower()
        content_type = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        repository = self.repository
        if repository is None:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Repository not initialized.")
            return

        if parsed.path == "/":
            self._send_text(HTML_PAGE)
            return
        if parsed.path == "/api/bootstrap":
            self._send_json(repository.bootstrap())
            return
        if parsed.path == "/api/item":
            mode = params.get("mode", [""])[0]
            item = repository.get_item(mode, params.get("key", [None])[0])
            self._send_json({"item": item, "status": repository.mode_status(mode)})
            return
        if parsed.path == "/image":
            mode = params.get("mode", [""])[0]
            key = params.get("key", [""])[0]
            item = repository.get_item(mode, key)
            if not item:
                self.send_error(HTTPStatus.NOT_FOUND, "Review item not found.")
                return
            self._send_file(Path(item["image_path"]))
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found.")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        repository = self.repository
        if repository is None:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Repository not initialized.")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        try:
            if parsed.path == "/api/review":
                status = repository.save_review(payload)
                self._send_json({"ok": True, "status": status})
                return
            if parsed.path == "/api/signoff":
                bootstrap = repository.signoff_mode(payload["mode"])
                self._send_json(bootstrap)
                return
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the click-only streetlight review app.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the local reviewer.")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind the local reviewer.")
    parser.add_argument("--build-only", action="store_true", help="Build app data and exit without starting the server.")
    parser.add_argument("--no-browser", action="store_true", help="Do not auto-open the local review app in a browser.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository = ReviewRepository()
    if args.build_only:
        for mode in MODE_ORDER:
            status = repository.mode_status(mode)
            print(f"{mode}: {status['total']} items, {status['reviewed']} reviewed")
        print(f"Review outputs rooted at: {OUTPUT_ROOT}")
        return

    handler = ReviewRequestHandler
    handler.repository = repository
    server = ThreadingHTTPServer((args.host, args.port), handler)
    url = f"http://{args.host}:{args.port}"
    print(f"Streetlight review app running at: {url}")
    print(f"Review outputs rooted at: {OUTPUT_ROOT}")
    if not args.no_browser:
        webbrowser.open(url)
    server.serve_forever()


if __name__ == "__main__":
    main()
