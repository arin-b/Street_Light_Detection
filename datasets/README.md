# Dataset Layout

This directory has been reorganized into four top-level buckets:

- `raw/`: source videos
- `extracted_frames/`: frame batches derived from source videos
- `imported/`: externally sourced datasets
- `derived/`: generated previews, annotation automation outputs, or other rebuildable artifacts

## Current Structure

```text
datasets/
  raw/
    mobile_night_videos/
      2025-07-22/
      unknown_source/
  extracted_frames/
    mobile_night_videos/
      2025-05-29/
      unknown_source/
  imported/
    roboflow/
      street_lightv_images_only_2026-05-12/
        README.roboflow.txt
        images/
          night_streetlight/
          daytime_driving_generic/
          road_scene_generic/
          road_hazard_speedbreaker/
          unknown_mixed/
  derived/
    annotation_automation/
      cleaned_coco/
      manifests/
      reports/
      reviews/
      training/
      yolo_dataset/
    previews/
```

## Annotation Automation Pipeline

The tracked annotation automation scripts live in [../scripts/annotation_automation/README.md](../scripts/annotation_automation/README.md).

Generated outputs from `build_annotation_corpus.py` are written under `derived/annotation_automation/`, with source and merged manifests in `derived/annotation_automation/manifests/`, review CSVs in `derived/annotation_automation/reviews/`, summary reports in `derived/annotation_automation/reports/`, and regenerated dataset exports in `derived/annotation_automation/cleaned_coco/`, `derived/annotation_automation/yolo_dataset/`, and `derived/annotation_automation/training/`.

## Inventory

- Raw night videos:
  - `2025-07-22`: 6 files
  - `unknown_source`: 1 file
- Extracted frame batches:
  - `2025-05-29`: 7 folders
  - `unknown_source`: 5 folders
- Imported Roboflow images:
  - `night_streetlight`: 2316 images
  - `daytime_driving_generic`: 3434 images
  - `road_scene_generic`: 540 images
  - `road_hazard_speedbreaker`: 2857 images
  - `unknown_mixed`: 1098 images

## Split Logic Used

- `class1_train_data*` -> `daytime_driving_generic`
- `class2_data_speedbreakerrefinedone*` -> `road_hazard_speedbreaker`
- `class2_data_*` -> `road_scene_generic`
- timestamped files like `20241026_...`, numeric streetlight files like `1_jpg...`, and `frame_*` streetlight images -> `night_streetlight`
- everything else from the mixed Roboflow export -> `unknown_mixed`

`unknown_mixed` should be reviewed manually before any training use.
