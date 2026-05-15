from __future__ import annotations

import csv
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP_DATA_PATH = ROOT / "datasets" / "derived" / "annotation_click_review" / "app_data" / "jobin_positive.json"
REVIEWS_PATH = ROOT / "datasets" / "derived" / "annotation_click_review" / "reviews" / "jobin_positive.csv"

JOBIN_BASELINE_COMPLETED = 87

# Rows accidentally written by the assistant into the user's manual range.
ASSISTANT_RANGE_KEYS = {
    "jobin:train_set_1_frame_39_jpg",
    "jobin:train_set_1_frame_40_jpg",
    "jobin:train_set_1_frame_46_jpg",
    "jobin:train_set_1_frame_48_jpg",
    "jobin:train_set_1_frame_49_jpg",
    "jobin:train_set_1_frame_50_jpg",
    "jobin:train_set_1_frame_51_jpg",
    "jobin:train_set_1_frame_52_jpg",
    "jobin:train_set_1_frame_53_jpg",
    "jobin:train_set_1_frame_54_jpg",
    "jobin:train_set_1_frame_55_jpg",
}

# High-confidence "clean luminaire" templates used only for conservative keep propagation.
KEEP_TEMPLATE_KEYS = [
    "jobin:train_set_1_frame_46_jpg",
    "jobin:train_set_1_frame_48_jpg",
    "jobin:train_set_1_frame_49_jpg",
    "jobin:train_set_1_frame_50_jpg",
    "jobin:train_set_1_frame_52_jpg",
    "jobin:train_set_1_frame_53_jpg",
    "jobin:train_set_1_frame_55_jpg",
]

KEEP_TEMPLATE_MAX_DIST = 0.13
EXCLUDE_NEIGHBOR_MAX_DIST = 0.04

FIELDNAMES = [
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


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def feature_vector(item: dict) -> list[float]:
    boxes = [list(map(float, box)) for box in item["boxes"]]
    boxes.sort()
    vector: list[float] = [float(len(boxes))]
    for x, y, w, h in boxes[:3]:
        vector.extend([x / 1280.0, y / 720.0, w / 1280.0, h / 720.0])
    while len(vector) < 13:
        vector.append(0.0)
    return vector


def euclidean(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((left - right) ** 2 for left, right in zip(a, b)))


def main() -> None:
    items = json.loads(APP_DATA_PATH.read_text(encoding="utf-8"))
    item_by_key = {item["key"]: item for item in items}
    item_index = {item["key"]: index for index, item in enumerate(items, start=1)}
    features = {item["key"]: feature_vector(item) for item in items}

    existing_rows = load_csv(REVIEWS_PATH)
    preserved_rows = [row for row in existing_rows if row["key"] not in ASSISTANT_RANGE_KEYS]
    preserved_by_key = {row["key"]: row for row in preserved_rows}

    reviewed_for_neighbors = [
        row
        for row in preserved_rows
        if row["primary_decision"] in {"keep", "exclude"}
    ]

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    assistant_rows: list[dict[str, str]] = []

    for position, item in enumerate(items, start=1):
        if position < JOBIN_BASELINE_COMPLETED + 1:
            continue
        if item["key"] in preserved_by_key:
            continue

        keep_distances = sorted(
            (euclidean(features[item["key"]], features[key]), key)
            for key in KEEP_TEMPLATE_KEYS
            if key in features
        )
        if keep_distances and keep_distances[0][0] < KEEP_TEMPLATE_MAX_DIST:
            assistant_rows.append(
                {
                    "key": item["key"],
                    "image_uid": item["key"],
                    "dataset_id": item["dataset_id"],
                    "clip_id": item["clip_id"],
                    "frame_id": item["frame_id"],
                    "image_path": item["image_path"],
                    "annotation_count": str(item["annotation_count"]),
                    "current_split_v2": item["current_split_v2"],
                    "primary_decision": "keep",
                    "secondary_reason": "",
                    "scene_bucket": "quiet_residential_lane",
                    "updated_boxes_json": json.dumps(item["boxes"]),
                    "review_timestamp": timestamp,
                }
            )
            continue

        neighbor_distances = sorted(
            (
                euclidean(features[item["key"]], features[row["key"]]),
                row,
            )
            for row in reviewed_for_neighbors
        )
        top_neighbors = neighbor_distances[:4]
        if (
            len(top_neighbors) == 4
            and all(row["primary_decision"] == "exclude" for _, row in top_neighbors)
            and max(distance for distance, _ in top_neighbors) < EXCLUDE_NEIGHBOR_MAX_DIST
        ):
            reasons = [row["secondary_reason"] for _, row in top_neighbors if row["secondary_reason"]]
            reason = Counter(reasons).most_common(1)[0][0] if reasons else "exclude_ambiguous_source"
            assistant_rows.append(
                {
                    "key": item["key"],
                    "image_uid": item["key"],
                    "dataset_id": item["dataset_id"],
                    "clip_id": item["clip_id"],
                    "frame_id": item["frame_id"],
                    "image_path": item["image_path"],
                    "annotation_count": str(item["annotation_count"]),
                    "current_split_v2": item["current_split_v2"],
                    "primary_decision": "exclude",
                    "secondary_reason": reason,
                    "scene_bucket": "quiet_residential_lane",
                    "updated_boxes_json": json.dumps(item["boxes"]),
                    "review_timestamp": timestamp,
                }
            )

    combined_rows = preserved_rows + assistant_rows
    combined_rows.sort(key=lambda row: item_index.get(row["key"], 10**9))
    write_csv(REVIEWS_PATH, combined_rows)

    print(f"Preserved rows: {len(preserved_rows)}")
    print(f"Assistant prefill rows: {len(assistant_rows)}")
    print(f"Keep rows added: {sum(1 for row in assistant_rows if row['primary_decision'] == 'keep')}")
    print(f"Exclude rows added: {sum(1 for row in assistant_rows if row['primary_decision'] == 'exclude')}")


if __name__ == "__main__":
    main()
