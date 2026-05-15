from __future__ import annotations

import csv
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import build_annotation_corpus as v1


ROOT = Path(__file__).resolve().parents[2]
CURRENT_ROOT = ROOT / "datasets" / "derived" / "annotation_automation"
OUTPUT_ROOT = ROOT / "datasets" / "derived" / "annotation_automation_v2"

POSITIVE_CLIP_SPLITS: dict[tuple[str, str], str] = {
    ("jobin", "train_set_1"): "test",
    ("jobin", "train_set_2"): "train",
    ("jobin", "val_set_1"): "valid",
    ("jobin", "val_set_2"): "train",
    ("jobin", "test_set_1"): "valid",
    ("jobin", "test_set_2"): "train",
    ("arindam", "set_1"): "train",
    ("arindam", "set_3"): "valid",
    ("arindam", "set_4"): "train",
    ("arindam", "set_5"): "test",
    ("arindam", "set_7"): "valid",
    ("arindam", "set_8"): "train",
    ("arindam", "set_13"): "train",
    ("arindam", "set_15"): "valid",
    ("arindam", "train_set_1"): "test",
    ("arindam", "train_set_2"): "train",
}

NEGATIVE_SOURCE_TARGETS = {
    "hf_night_external": {"train": 15, "valid": 11, "test": 8},
    "local_extracted_night": {"train": 3, "valid": 2, "test": 1},
}


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_csv(path: Path) -> list[dict]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, data: dict) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def copy_image(src: Path, dst: Path) -> None:
    ensure_dir(dst.parent)
    if not dst.exists():
        shutil.copy2(src, dst)


def build_positive_export(
    merged_manifest_rows: list[dict],
    annotation_rows: list[dict],
    dims_by_uid: dict[str, tuple[int, int]],
) -> tuple[list[dict], list[dict]]:
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)

    dataset_root = ensure_dir(OUTPUT_ROOT / "yolo_dataset")
    manifests_root = ensure_dir(OUTPUT_ROOT / "manifests")
    reports_root = ensure_dir(OUTPUT_ROOT / "reports")

    anns_by_uid: dict[str, list[dict]] = defaultdict(list)
    for row in annotation_rows:
        anns_by_uid[row["image_uid"]].append(row)

    coco_by_split = {
        split: {
            "info": {"description": "Annotation automation v2 streetlight corpus", "version": "2.0"},
            "licenses": [],
            "images": [],
            "annotations": [],
            "categories": [{"id": 1, "name": "streetlight", "supercategory": "light_source"}],
        }
        for split in ("train", "valid", "test")
    }

    next_image_id = 1
    next_ann_id = 1
    export_rows: list[dict] = []
    validation_rows: list[dict] = []

    for row in merged_manifest_rows:
        if row["corpus_role"] != "seed_positive":
            continue
        dataset_id = row["dataset_id"]
        clip_id = row["clip_id"]
        split = POSITIVE_CLIP_SPLITS[(dataset_id, clip_id)]
        image_uid = row["image_uid"]
        image_path = Path(row["image_path"])
        output_file_name = row["output_file_name"]
        anns = anns_by_uid[image_uid]
        if not anns:
            continue

        image_dst = dataset_root / "images" / split / output_file_name
        label_dst = dataset_root / "labels" / split / f"{Path(output_file_name).stem}.txt"
        copy_image(image_path, image_dst)
        ensure_dir(label_dst.parent)

        width, height = dims_by_uid[image_uid]
        yolo_lines: list[str] = []
        for ann in anns:
            bbox_x = float(ann["bbox_x"])
            bbox_y = float(ann["bbox_y"])
            bbox_w = float(ann["bbox_w"])
            bbox_h = float(ann["bbox_h"])
            x_c = (bbox_x + (bbox_w / 2.0)) / width
            y_c = (bbox_y + (bbox_h / 2.0)) / height
            yolo_lines.append(f"0 {x_c:.6f} {y_c:.6f} {bbox_w / width:.6f} {bbox_h / height:.6f}")

            coco_by_split[split]["annotations"].append(
                {
                    "id": next_ann_id,
                    "image_id": next_image_id,
                    "category_id": 1,
                    "bbox": [bbox_x, bbox_y, bbox_w, bbox_h],
                    "iscrowd": 0,
                    "area": bbox_w * bbox_h,
                    "segmentation": [],
                }
            )
            next_ann_id += 1

        label_dst.write_text("\n".join(yolo_lines) + "\n", encoding="utf-8")
        coco_by_split[split]["images"].append(
            {
                "id": next_image_id,
                "license": 1,
                "file_name": output_file_name,
                "height": int(height),
                "width": int(width),
            }
        )
        export_rows.append(
            {
                "image_uid": image_uid,
                "dataset_id": dataset_id,
                "clip_id": clip_id,
                "frame_id": row["frame_id"],
                "assigned_split": split,
                "corpus_role": "seed_positive",
                "image_path": str(image_path),
                "output_file_name": output_file_name,
                "annotation_count": row["annotation_count"],
            }
        )
        if split == "valid":
            validation_rows.append(
                {
                    "image_uid": image_uid,
                    "dataset_id": dataset_id,
                    "clip_id": clip_id,
                    "frame_id": row["frame_id"],
                    "validation_role": "positive",
                    "condition_group": "clip_held_out_positive",
                    "image_path": str(image_path),
                }
            )
        next_image_id += 1

    for split, coco in coco_by_split.items():
        write_json(OUTPUT_ROOT / "cleaned_coco" / "merged" / split / "_annotations.coco.json", coco)

    dataset_yaml = "\n".join(
        [
            f"path: {dataset_root.as_posix()}",
            "train: images/train",
            "val: images/valid",
            "test: images/test",
            "",
            "names:",
            "  0: streetlight",
            "",
        ]
    )
    (dataset_root / "dataset.yaml").write_text(dataset_yaml, encoding="utf-8")

    write_csv(
        manifests_root / "merged_manifest_v2.csv",
        export_rows,
        [
            "image_uid",
            "dataset_id",
            "clip_id",
            "frame_id",
            "assigned_split",
            "corpus_role",
            "image_path",
            "output_file_name",
            "annotation_count",
        ],
    )
    return export_rows, validation_rows


def assign_clean_negative_splits(clean_negative_rows: list[dict]) -> list[dict]:
    remaining = {pool: dict(targets) for pool, targets in NEGATIVE_SOURCE_TARGETS.items()}
    assigned_rows: list[dict] = []

    for row in clean_negative_rows:
        pool = row["source_pool"]
        if pool == "arindam_unannotated_seed":
            split = POSITIVE_CLIP_SPLITS[(row["dataset_id"], row["clip_id"])]
        else:
            pool_targets = remaining[pool]
            if pool_targets["valid"] > 0:
                split = "valid"
                pool_targets["valid"] -= 1
            elif pool_targets["test"] > 0:
                split = "test"
                pool_targets["test"] -= 1
            else:
                split = "train"
                pool_targets["train"] -= 1
        assigned = dict(row)
        assigned["assigned_split_v2"] = split
        assigned_rows.append(assigned)
    return assigned_rows


def integrate_clean_negatives(assigned_negative_rows: list[dict], validation_rows: list[dict]) -> list[dict]:
    dataset_root = OUTPUT_ROOT / "yolo_dataset"
    admissions: list[dict] = []
    for row in assigned_negative_rows:
        split = row["assigned_split_v2"]
        source_path = Path(row["image_path"])
        output_stem = f"neg__{row['review_candidate_id']}__{source_path.stem}"
        image_dst = dataset_root / "images" / split / f"{output_stem}{source_path.suffix.lower()}"
        label_dst = dataset_root / "labels" / split / f"{output_stem}.txt"
        copy_image(source_path, image_dst)
        ensure_dir(label_dst.parent)
        label_dst.write_text("", encoding="utf-8")

        admissions.append(
            {
                "review_candidate_id": row["review_candidate_id"],
                "dataset_id": row["dataset_id"],
                "clip_id": row["clip_id"],
                "frame_id": row["frame_id"],
                "source_pool": row["source_pool"],
                "assigned_split_v2": split,
                "image_path": str(source_path),
                "copied_image_path": str(image_dst),
                "label_path": str(label_dst),
                "review_label": row["review_label"],
                "notes": row["notes"],
            }
        )
        if split == "valid":
            validation_rows.append(
                {
                    "image_uid": row["review_candidate_id"],
                    "dataset_id": row["dataset_id"],
                    "clip_id": row["clip_id"],
                    "frame_id": row["frame_id"],
                    "validation_role": "background",
                    "condition_group": row["source_pool"],
                    "image_path": str(source_path),
                }
            )
    write_csv(
        OUTPUT_ROOT / "integrated_reviews" / "reviewed_negative_admissions_v2.csv",
        admissions,
        [
            "review_candidate_id",
            "dataset_id",
            "clip_id",
            "frame_id",
            "source_pool",
            "assigned_split_v2",
            "image_path",
            "copied_image_path",
            "label_path",
            "review_label",
            "notes",
        ],
    )
    return admissions


def write_report(export_rows: list[dict], validation_rows: list[dict], clean_negative_rows: list[dict]) -> None:
    reports_root = ensure_dir(OUTPUT_ROOT / "reports")
    split_counts = Counter((row["assigned_split"], row["corpus_role"]) for row in export_rows)
    neg_counts = Counter(row["assigned_split_v2"] for row in clean_negative_rows)
    lines = [
        "# Validation Policy v2",
        "",
        "## Positive clip assignments",
        "",
        "| Dataset | Clip | Split | Images |",
        "| --- | --- | --- | ---: |",
    ]
    clip_counts = Counter((row["dataset_id"], row["clip_id"], row["assigned_split"]) for row in export_rows)
    for (dataset_id, clip_id, split), count in sorted(clip_counts.items()):
        lines.append(f"| {dataset_id} | {clip_id} | {split} | {count} |")

    lines.extend(
        [
            "",
            "## Validation summary",
            "",
            f"- Positive validation images: `{split_counts[('valid', 'seed_positive')]}`",
            f"- Reviewed clean-negative validation images: `{neg_counts['valid']}`",
            f"- Total validation images after integrating clean negatives: `{split_counts[('valid', 'seed_positive')] + neg_counts['valid']}`",
            "",
            "## Rationale",
            "",
            "- `jobin/test_set_1` stays in validation because it already acted as the only substantial held-out Jobin family in v1.",
            "- `jobin/val_set_1` is promoted into validation to expand urban glare-heavy coverage without collapsing the independent Jobin test family.",
            "- `arindam/set_15`, `set_3`, and `set_7` are used in validation to cover smaller residential-style clips and avoid a validation set drawn from only one source style.",
            "- `arindam/set_13` remains in training because it carries most of the usable Arindam positive volume.",
            "- The current `45` reviewed clean negatives are redistributed to improve validation pressure, but this is still not enough to solve the negative-mining problem fully.",
            "",
            "## Protocol links",
            "",
            "- [validation_and_labeling_protocol_v2.md](F:\\RBCCPS_Directory\\documentation\\system_design\\new_design\\validation_and_labeling_protocol_v2.md)",
        ]
    )
    (reports_root / "validation_policy_v2.md").write_text("\n".join(lines), encoding="utf-8")

    write_csv(
        OUTPUT_ROOT / "reports" / "validation_manifest_v2.csv",
        validation_rows,
        [
            "image_uid",
            "dataset_id",
            "clip_id",
            "frame_id",
            "validation_role",
            "condition_group",
            "image_path",
        ],
    )


def main() -> None:
    merged_manifest_rows = load_csv(CURRENT_ROOT / "manifests" / "merged_manifest.csv")
    annotation_rows = load_csv(CURRENT_ROOT / "manifests" / "annotation_metadata_seed.csv")
    hard_negative_rows = load_csv(CURRENT_ROOT / "reviews" / "hard_negative_review_manifest.csv")
    dims_by_uid: dict[str, tuple[int, int]] = {}
    jobin_records, _ = v1.load_jobin_source()
    arindam_records, _ = v1.load_arindam_source()
    for record in jobin_records + arindam_records:
        dims_by_uid[record.image_uid] = (record.width, record.height)

    export_rows, validation_rows = build_positive_export(merged_manifest_rows, annotation_rows, dims_by_uid)

    clean_negative_rows = [row for row in hard_negative_rows if row["review_label"] == "clean_negative"]
    assigned_negative_rows = assign_clean_negative_splits(clean_negative_rows)
    integrate_clean_negatives(assigned_negative_rows, validation_rows)
    write_report(export_rows, validation_rows, assigned_negative_rows)

    print(f"annotation_automation_v2 written to: {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
