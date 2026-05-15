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
- `build_annotation_corpus_v2.py`
  - rebuilds the detector corpus with the stricter v2 validation policy
  - enlarges validation with explicit held-out clip families
  - reintegrates reviewed clean negatives with new split targets
- `prepare_annotation_corpus_v3_reviews.py`
  - syncs the current click-review state and hard-negative review state into a dedicated v3 review workspace
  - writes Jobin, Arindam, negative, scene-bucket, and promoted-positive review CSVs
- `build_annotation_corpus_v3.py`
  - builds the guarded local-only v3 corpus from reviewed positives and reviewed negatives
  - blocks strict materialization when positive review or scene-bucket requirements are still incomplete
- `build_tiled_training_dataset.py`
  - creates a tiled train split for small-object experiments while preserving full-image validation and test
- `build_mixed_local_openimages_dataset.py`
  - creates a controlled local-plus-external mixed train split while keeping local validation/test intact
- `train_yolov26.py`
  - thin wrapper around Ultralytics training for the cleaned dataset
  - auto-rewrites Windows-authored dataset YAML `path:` values when training on Linux
- `export_annotation_candidates.py`
  - runs a fine-tuned detector and writes candidate detections to CSV
- `score_reliability.py`
  - fits or scores the hybrid reliability gate
- `materialize_review_batches.py`
  - copies hard-negative and calibration images into reviewer-friendly folders
- `integrate_reviewed_data.py`
  - validates review labels and admits reviewed clean negatives into the derived YOLO corpus
- `evaluate_annotation_gate.py`
  - computes pooled and source-specific reliability-gate AUC and threshold metrics
- `REVIEW_WORKFLOW.md`
  - reviewer-facing instructions for filling the hard-negative and calibration manifests
- `audit_manual_reviews_v2.py`
  - exports high-priority hard-negative rows that should be re-reviewed under the stricter v2 protocol
- `make_hard_negative_contact_sheets.ps1`
  - creates image contact sheets for reviewed hard-negative buckets
- `make_calibration_contact_sheets.ps1`
  - creates image contact sheets for pending calibration rows
- `generate_calibration_overlays.ps1`
  - draws streetlight boxes on the calibration images for visual review
- `review_app.py`
  - runs a click-only local review app for Jobin positives, Arindam positives, and hard negatives
  - captures decision buttons, scene buckets, signoff state, and fix-queue box redraws
  - writes machine-readable CSV outputs for later corpus rebuild

## Typical order

1. Run `build_annotation_corpus.py`.
2. Run `materialize_review_batches.py` to create reviewer-friendly image folders.
3. Review the generated hard-negative and calibration manifests.
4. Run `integrate_reviewed_data.py` after the hard-negative manifest has been reviewed.
5. Train `detector_v1` on a remote GPU using the generated dataset package.
6. Export candidate detections on unlabeled night frames.
7. Score reliability and route predictions into `auto-accept`, `manual-review`, and `auto-reject`.
8. Run `evaluate_annotation_gate.py` on reviewed calibration outputs before accepting any automation threshold.
9. For run-3 curation, run `review_app.py` and complete:
   - `Jobin Positive Review`
   - `Arindam Positive Review`
   - `Hard-Negative Review`
10. Run `prepare_annotation_corpus_v3_reviews.py` to sync the v3 review workspace.
11. Run `build_annotation_corpus_v3.py` for the next strict local-night corpus.
12. If recall is still weak, run `build_tiled_training_dataset.py` on the v3 YOLO export and compare against the full-frame run.
13. Only after a strong local baseline exists, run `build_mixed_local_openimages_dataset.py` to test light external augmentation.

## Review labels

- Hard-negative manifest allowed labels:
  - `clean_negative`
  - `ambiguous`
  - `missed_positive`
- Calibration manifest should only be considered locked when:
  - `review_status` is no longer `pending_manual_lock`
  - `locked` is set to `1`

## Review app

Launch locally with:

```bash
python scripts/annotation_automation/review_app.py
```

Convenience launchers:

```bash
bash scripts/annotation_automation/run_review_app.sh
```

```powershell
powershell -ExecutionPolicy Bypass -File scripts\annotation_automation\run_review_app.ps1
```

Build the review manifests and app data without launching the server:

```bash
python scripts/annotation_automation/review_app.py --build-only
```

The app writes its working outputs under:

- `datasets/derived/annotation_click_review/app_data`
- `datasets/derived/annotation_click_review/reviews`
