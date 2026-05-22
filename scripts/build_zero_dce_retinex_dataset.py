from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from rbccps_od.models.enhancer import LowLightEnhancer  # noqa: E402
from rbccps_od.models.retinex import RetinexDecompositionModel  # noqa: E402

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
SPLIT_TOKENS = {
    "_images_train_": "train",
    "_images_valid_": "valid",
    "_images_test_": "test",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a YOLO dataset from Zero-DCE enhanced + Retinex reflectance images."
    )
    parser.add_argument("--image-dir", default="datasets/processed/original/images")
    parser.add_argument("--label-dir", default="datasets/processed/original/labels")
    parser.add_argument("--output-root", default="datasets/processed/zero_dce_retinex_reflectance")
    parser.add_argument("--device", default=None, help="Torch device, for example cpu, cuda, or cuda:0.")
    parser.add_argument("--zero-dce-checkpoint", default=None, help="Optional explicit Epoch99.pth path.")
    parser.add_argument("--retinex-checkpoint", default=None, help="Optional explicit Retinex Decom checkpoint path.")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--overlay-limit", type=int, default=40, help="Number of QA overlay images to draw; use 0 to disable.")
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
    raise FileNotFoundError(f"No matching label found for {image_path.name}")


def collect_images(image_dir: Path) -> list[Path]:
    return sorted(p for p in image_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)


def draw_yolo_overlay(image_path: Path, label_path: Path, output_path: Path) -> None:
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    draw = ImageDraw.Draw(image)
    text = label_path.read_text(encoding="utf-8-sig").strip()
    for line in text.splitlines():
        parts = line.split()
        if len(parts) != 5:
            continue
        cls_id, x_c, y_c, box_w, box_h = parts
        x_c, y_c, box_w, box_h = map(float, (x_c, y_c, box_w, box_h))
        x1 = (x_c - box_w / 2.0) * width
        y1 = (y_c - box_h / 2.0) * height
        x2 = (x_c + box_w / 2.0) * width
        y2 = (y_c + box_h / 2.0) * height
        draw.rectangle((x1, y1, x2, y2), outline=(255, 64, 64), width=3)
        draw.text((x1 + 3, max(0, y1 - 14)), cls_id, fill=(255, 64, 64))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


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

    enhancer = LowLightEnhancer(checkpoint=args.zero_dce_checkpoint, enabled=True)
    retinex = RetinexDecompositionModel(checkpoint=args.retinex_checkpoint, enabled=True)

    rows: list[dict[str, str]] = []
    overlay_count = 0
    images = collect_images(image_dir)
    if not images:
        raise SystemExit(f"No images found in {image_dir}")

    for index, image_path in enumerate(images, start=1):
        split = infer_split(image_path)
        label_path = matching_label(image_path, label_dir)
        final_stem = f"{image_path.stem}_reflectance"

        enhanced_path = output_root / "intermediate" / "enhanced" / split / image_path.name
        retinex_dir = output_root / "intermediate" / "retinex" / split / image_path.stem
        output_image = output_root / "images" / split / f"{final_stem}.png"
        output_label = output_root / "labels" / split / f"{final_stem}.txt"

        if output_image.exists() and output_label.exists() and not args.overwrite:
            reflectance_path = output_image
        else:
            enhanced = Path(enhancer.enhance(image_path, output_path=enhanced_path, device=args.device))
            components = retinex.decompose(enhanced, output_dir=retinex_dir, device=args.device)
            reflectance_path = Path(components["reflectance"])
            if Image.open(image_path).size != Image.open(reflectance_path).size:
                raise RuntimeError(f"Reflectance image size changed for {image_path.name}; labels are no longer valid.")

            output_image.parent.mkdir(parents=True, exist_ok=True)
            output_label.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(reflectance_path, output_image)
            shutil.copy2(label_path, output_label)

        if args.overlay_limit > 0 and overlay_count < args.overlay_limit:
            overlay_path = output_root / "qa_overlays" / split / f"{final_stem}.jpg"
            draw_yolo_overlay(output_image, output_label, overlay_path)
            overlay_count += 1

        rows.append(
            {
                "split": split,
                "source_image": str(image_path),
                "source_label": str(label_path),
                "reflectance_image": str(output_image),
                "reflectance_label": str(output_label),
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

    print(f"dataset: {output_root}")
    print(f"yaml: {output_root / 'dataset.yaml'}")
    print(f"manifest: {manifest_path}")


if __name__ == "__main__":
    main()
