from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from rbccps_od.models.enhancer import LowLightEnhancer  # noqa: E402

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

SPLIT_TOKENS = {
    "_images_train_": "train",
    "_images_valid_": "valid",
    "_images_test_": "test",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build dataset using only Zero-DCE enhancement."
    )

    parser.add_argument(
        "--image-dir",
        default="datasets/processed/original/images"
    )

    parser.add_argument(
        "--label-dir",
        default="datasets/processed/original/labels"
    )

    parser.add_argument(
        "--output-root",
        default="datasets/processed/zerodce-enhanced"
    )

    parser.add_argument("--device", default=None)

    parser.add_argument(
        "--zero-dce-checkpoint",
        default=None
    )

    parser.add_argument(
        "--overwrite",
        action="store_true"
    )

    return parser.parse_args()


def infer_split(path: Path) -> str:
    for token, split in SPLIT_TOKENS.items():
        if token in path.stem:
            return split

    raise ValueError(f"Could not infer split from filename: {path.name}")


def matching_label(image_path: Path, label_dir: Path) -> Path:
    label_name = image_path.stem.replace("_images_", "_labels_") + ".txt"

    label_path = label_dir / label_name

    if label_path.exists():
        return label_path

    fallback = label_dir / f"{image_path.stem}.txt"

    if fallback.exists():
        return fallback

    raise FileNotFoundError(
        f"No matching label found for {image_path.name}"
    )


def collect_images(image_dir: Path):
    return sorted(
        p for p in image_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
    )


def write_dataset_yaml(output_root: Path) -> None:
    dataset_yaml = output_root / "dataset.yaml"
    dataset_yaml.write_text(
        "\n".join(
            [
                f"path: {output_root.resolve()}",
                "train: images/train",
                "val: images/valid",
                "test: images/test",
                "names:",
                "  0: streetlight",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:

    args = parse_args()

    image_dir = Path(args.image_dir).resolve()
    label_dir = Path(args.label_dir).resolve()
    output_root = Path(args.output_root).resolve()

    enhancer = LowLightEnhancer(
        checkpoint=args.zero_dce_checkpoint,
        enabled=True
    )

    images = collect_images(image_dir)

    if not images:
        raise SystemExit(f"No images found in {image_dir}")

    rows: list[dict[str, str]] = []

    for index, image_path in enumerate(images, start=1):

        split = infer_split(image_path)

        label_path = matching_label(image_path, label_dir)

        output_image_dir = (
            output_root / "images" / split
        )

        output_label_dir = (
            output_root / "labels" / split
        )

        output_image_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        output_label_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        output_image = output_image_dir / image_path.name

        output_label = (
            output_label_dir / f"{image_path.stem}.txt"
        )

        if output_image.exists() and output_label.exists() and not args.overwrite:
            print(f"Skipping existing: {output_image.name}")
        else:
            enhanced_path = Path(
                enhancer.enhance(
                    image_path,
                    output_path=output_image,
                    device=args.device
                )
            )

            if Image.open(image_path).size != Image.open(enhanced_path).size:
                raise RuntimeError(
                    f"Enhanced image size changed for {image_path.name}; labels are no longer valid."
                )

            shutil.copy2(label_path, output_label)

        rows.append(
            {
                "split": split,
                "source_image": str(image_path),
                "source_label": str(label_path),
                "enhanced_image": str(output_image),
                "enhanced_label": str(output_label),
            }
        )

        if index % 25 == 0 or index == len(images):
            print(f"processed {index}/{len(images)}")

    write_dataset_yaml(output_root)
    manifest_path = output_root / "manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone.")
    print(f"Output dataset: {output_root}")
    print(f"yaml: {output_root / 'dataset.yaml'}")
    print(f"manifest: {manifest_path}")


if __name__ == "__main__":
    main()
