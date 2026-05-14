# Annotation Automation Scripts

This directory contains the local implementation scaffolding for the annotation automation plan.

## Scripts

- `build_annotation_corpus.py`
  - rebuilds clip-level splits
  - normalizes classes into one `streetlight` label
  - exports cleaned COCO and YOLO datasets
  - writes review and calibration manifests
  - writes seed annotation metadata
  - writes a remote training package
- `train_yolov26.py`
  - thin wrapper around Ultralytics training for the cleaned dataset
- `export_annotation_candidates.py`
  - runs a fine-tuned detector and writes candidate detections to CSV
- `score_reliability.py`
  - fits or scores the hybrid reliability gate

## Typical order

1. Run `build_annotation_corpus.py`.
2. Review the generated hard-negative and calibration manifests.
3. Train `detector_v1` on a remote GPU using the generated dataset package.
4. Export candidate detections on unlabeled night frames.
5. Score reliability and route predictions into `auto-accept`, `manual-review`, and `auto-reject`.
