import json
import shutil
import tempfile
from pathlib import Path

from ultralytics import YOLO

# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "/media/arindamb/NewVolume/Street_Light_Detection/runs/detect/outputs/cse_ablation/original-8/weights/best.pt"

IMAGE_DIR = Path(
    "/media/arindamb/NewVolume/RBCCPS-Internship-Docs/annotations_LLM/images/val"
)

JSON_FILES = [
    "/media/arindamb/NewVolume/RBCCPS-Internship-Docs/annotations_LLM/annotations_LLM\\batch_001\\annotation_llm.json",
    "/media/arindamb/NewVolume/RBCCPS-Internship-Docs/annotations_LLM/annotations_LLM\\batch_002\\annotation_llm.json",
    "/media/arindamb/NewVolume/RBCCPS-Internship-Docs/annotations_LLM/annotations_LLM\\batch_003\\annotation_llm.json",
    "/media/arindamb/NewVolume/RBCCPS-Internship-Docs/annotations_LLM/annotations_LLM\\batch_004\\annotation_llm.json",
]

CLASS_MAP = {
    "streetlight_lamp_head": 0,
    "streetlight_pole": 1,
}

CLASS_NAMES = [
    "streetlight_lamp_head",
    "streetlight_pole",
]

IMG_SIZE = 1280


# ============================================================
# HELPERS
# ============================================================

def xyxy_to_yolo(box, img_w, img_h):
    x1, y1, x2, y2 = box

    xc = ((x1 + x2) / 2) / img_w
    yc = ((y1 + y2) / 2) / img_h

    w = (x2 - x1) / img_w
    h = (y2 - y1) / img_h

    return xc, yc, w, h

def merge_streetlights(boxes):
    """
    Convert 
num_images = 0
num_boxes = 0
missing_images = []

try:

    # ========lamp-head + pole annotations into
    single streetlight bounding boxes.

    Returns:
        list of merged xyxy boxes
    """

    poles = {}
    merged_boxes = []

    # Index pole boxes by box_id
    for box in boxes:

        if box["class_name"] == "streetlight_pole":

            poles[box["box_id"]] = box

    used_poles = set()

    # Merge lamp heads with their parent pole
    for box in boxes:

        if box["class_name"] != "streetlight_lamp_head":
            continue

        parent_id = box.get("parent_pole_box_id", "")

        if parent_id and parent_id in poles:

            pole_box = poles[parent_id]

            px1, py1, px2, py2 = pole_box["bbox_xyxy"]
            lx1, ly1, lx2, ly2 = box["bbox_xyxy"]

            merged_boxes.append([
                min(px1, lx1),
                min(py1, ly1),
                max(px2, lx2),
                max(py2, ly2),
            ])

            used_poles.add(parent_id)

        else:
            # orphan lamp head
            merged_boxes.append(box["bbox_xyxy"])

    # add poles that never got matched
    for pole_id, pole_box in poles.items():

        if pole_id not in used_poles:
            merged_boxes.append(
                pole_box["bbox_xyxy"]
            )

    return merged_boxes

# ============================================================
# BUILD IMAGE LOOKUP
# ============================================================

print("Building image index...")

IMAGE_LOOKUP = {}

for f in IMAGE_DIR.iterdir():

    if not f.is_file():
        continue

    # Extract filename from embedded Windows path
    actual_name = f.name.split("\\")[-1]

    IMAGE_LOOKUP[actual_name] = f

print(f"Indexed {len(IMAGE_LOOKUP)} images")

# Quick sanity check
sample_key = next(iter(IMAGE_LOOKUP.keys()))
print("Example image:", sample_key)


# ============================================================
# CREATE TEMP DATASET
# ============================================================

temp_root = tempfile.mkdtemp(prefix="streetlight_eval_")

images_dir = Path(temp_root) / "images" / "val"
labels_dir = Path(temp_root) / "labels" / "val"

images_dir.mkdir(parents=True, exist_ok=True)
labels_dir.mkdir(parents=True, exist_ok=True)

print(f"\nTemporary dataset: {temp_root}")

num_images = 0
num_boxes = 0
missing_images = []

try:

    # ========================================================
    # CREATE LABELS
    # ========================================================

    for json_file in JSON_FILES:

        print(f"\nProcessing: {json_file}")

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for ann in data["annotations"]:

            image_name = ann["image_name"]

            src_image = IMAGE_LOOKUP.get(image_name)

            if src_image is None:
                missing_images.append(image_name)
                continue

            dst_image = images_dir / image_name

            if not dst_image.exists():
                shutil.copy2(src_image, dst_image)

            width = ann["width"]
            height = ann["height"]

            label_path = labels_dir / (
                Path(image_name).stem + ".txt"
            )

            merged_boxes = merge_streetlights(
    ann["boxes"]
)

            with open(label_path, "w") as lf:

                for merged_box in merged_boxes:

                    xc, yc, bw, bh = xyxy_to_yolo(
                        merged_box,
                        width,
                        height
                    )

                    lf.write(
                        f"0 "
                        f"{xc:.6f} "
                        f"{yc:.6f} "
                        f"{bw:.6f} "
                        f"{bh:.6f}\n"
                    )

                    num_boxes += 1

            num_images += 1

    # ========================================================
    # DATASET SUMMARY
    # ========================================================

    print("\n" + "=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)

    print(f"Images used : {num_images}")
    print(f"Boxes used  : {num_boxes}")
    print(f"Missing     : {len(missing_images)}")

    if missing_images:
        print("\nFirst 20 missing images:")
        for img in missing_images[:20]:
            print(img)

    if num_images == 0:
        raise RuntimeError(
            "No images found. Check IMAGE_DIR and filenames."
        )

    # ========================================================
    # CREATE DATA.YAML
    # ========================================================

    yaml_path = Path(temp_root) / "data.yaml"

    with open(yaml_path, "w") as f:

        f.write(f"path: {temp_root}\n")
        f.write("train: images/val\n")
        f.write("val: images/val\n")
        f.write("test: images/val\n\n")

        f.write("names: ['streetlight']\n")
    from pathlib import Path

    sample_img = next(images_dir.glob("*.jpg"))

    print("Image:", sample_img.name)

    expected_label = (
        labels_dir /
        (sample_img.stem + ".txt")
    )

    print("Label exists:", expected_label.exists())
    # ========================================================
    # LOAD MODEL
    # ========================================================

    print("\nLoading model...")

    model = YOLO(MODEL_PATH)

    # ========================================================
    # EVALUATE
    # ========================================================

    print("\nRunning evaluation...\n")

    metrics = model.val(
        data=str(yaml_path),
        split="val",
        imgsz=IMG_SIZE,
        conf=0.001,
        batch=8,
        plots=False,
        verbose=True,
        save_json=False,
    )

    # ========================================================
    # OVERALL METRICS
    # ========================================================

    print("\n")
    print("=" * 60)
    print("OVERALL RESULTS")
    print("=" * 60)

    print(f"mAP50      : {metrics.box.map50:.4f}")
    print(f"mAP50-95   : {metrics.box.map:.4f}")
    print(f"Precision  : {metrics.box.mp:.4f}")
    print(f"Recall     : {metrics.box.mr:.4f}")

    # ========================================================
    # PER CLASS METRICS
    # ========================================================

    print("\n")
    print("=" * 60)
    print("\n")
    print("=" * 60)
    print("SINGLE CLASS RESULTS")
    print("=" * 60)

    print(
        f"streetlight "
        f"AP50={metrics.box.map50:.4f} "
        f"AP50-95={metrics.box.map:.4f}"
    )

finally:

    print("\nRemoving temporary dataset...")
    shutil.rmtree(temp_root, ignore_errors=True)
    print("Cleanup complete.")
