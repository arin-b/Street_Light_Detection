# Dataset Layout

This directory is organized into four top-level buckets:

- `raw/`: source videos
- `extracted_frames/`: frame batches derived from source videos
- `imported/`: externally sourced datasets
- `derived/`: generated previews, annotation automation outputs, or other rebuildable artifacts

Preservation priority for cleanup:

1. `raw/` is the canonical local source and should be preserved first.
2. `annotated_seed/` and `yolov26_weights/` are core inputs to the current codebase and should be preserved.
3. `derived/annotation_click_review/` and `derived/annotation_automation_v3/` are the current active working outputs.
4. `extracted_frames/` is secondary to `raw/` and should be treated as rebuildable unless tied to active review state.
5. `imported/` should be split into current-use subsets, retained provenance, and deletion candidates.

## Current Structure

```text
datasets/
  annotated_seed/
  raw/
    mobile_night_videos/
      2025-07-22/
      unknown_source/
  extracted_frames/
    mobile_night_videos/
      2025-05-29/
      unknown_source/
  imported/
    huggingface/
      thirdeyelabs_indian_road_dataset/
        night_jpg/
    openimages_cache/
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
    annotation_automation_v2/
    annotation_automation_v3/
    annotation_click_review/
    openimages_streetlight_external/
    previews/
  yolov26_weights/
```

## Active vs Retained Areas

### Active now

- `derived/annotation_click_review/`
  - current click-review app outputs
- `derived/annotation_automation_v3/`
  - current guarded local-night corpus lineage
- `derived/openimages_streetlight_external/`
  - external streetlight subset used for the controlled mixed-data experiment path
- `yolov26_weights/`
  - preserved base training checkpoint(s)

### Retained because the current workflow still depends on them

- `annotated_seed/`
  - original labeled seed sources
- `derived/annotation_automation_v2/`
  - retained because v3 review and build logic still consume v2 outputs
- `imported/huggingface/thirdeyelabs_indian_road_dataset/night_jpg/`
  - sampled by the tracked v1 corpus builder for negative-review sourcing
- `imported/openimages_cache/`
  - retained if `derived/openimages_streetlight_external/` ever needs to be rebuilt

### Retained but not current-first

- `derived/annotation_automation/`
  - original seed corpus lineage
- `previews/`
  - generated media, useful for inspection but not a primary workflow input

### Review for possible demotion or deletion

- `extracted_frames/`
  - rebuildable from `raw/` unless a subset is still tied to active review provenance
- `imported/roboflow/street_lightv_images_only_2026-05-12/`
  - present locally, but not directly referenced by the current tracked v3 workflow

## Annotation Automation Pipeline

The tracked annotation automation scripts live in [../scripts/annotation_automation/README.md](../scripts/annotation_automation/README.md).

Current first-class outputs are written under:

- `derived/annotation_click_review/`
- `derived/annotation_automation_v3/`

Retained earlier outputs remain under:

- `derived/annotation_automation/`
- `derived/annotation_automation_v2/`

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

## Cleanup Notes

- Treat `raw/` as the highest-priority local asset.
- Treat `extracted_frames/` as lower-priority than `raw/`.
- Treat imported subsets by evidence of use, not by age alone.
- Treat `derived/annotation_automation_v3/` and `derived/annotation_click_review/` as the only default working outputs.
- Use [../documentation/repository_maintenance/cleanup_inventory.md](../documentation/repository_maintenance/cleanup_inventory.md) as the authoritative triage list before deleting anything.
