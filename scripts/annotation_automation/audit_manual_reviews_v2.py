from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "datasets" / "derived" / "annotation_automation" / "reviews" / "hard_negative_review_manifest.csv"
OUTPUT = ROOT / "datasets" / "derived" / "annotation_automation_v2" / "reports" / "hard_negative_rereview_candidates_v2.csv"


def main() -> None:
    with SOURCE.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    filtered = [
        {
            "review_candidate_id": row["review_candidate_id"],
            "source_pool": row["source_pool"],
            "dataset_id": row["dataset_id"],
            "clip_id": row["clip_id"],
            "frame_id": row["frame_id"],
            "image_path": row["image_path"],
            "review_label": row["review_label"],
            "notes": row["notes"],
            "rereview_reason": (
                "Visible-streetlight local scene likely belongs in missed_positive, not ambiguous."
                if row["source_pool"] == "local_extracted_night"
                else "Seed negative remains uncertain under v2 protocol and should be re-checked."
            ),
        }
        for row in rows
        if row["review_label"] == "ambiguous"
        and row["source_pool"] in {"local_extracted_night", "arindam_unannotated_seed"}
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "review_candidate_id",
                "source_pool",
                "dataset_id",
                "clip_id",
                "frame_id",
                "image_path",
                "review_label",
                "notes",
                "rereview_reason",
            ],
        )
        writer.writeheader()
        writer.writerows(filtered)

    print(f"wrote {len(filtered)} re-review candidates to {OUTPUT}")


if __name__ == "__main__":
    main()
