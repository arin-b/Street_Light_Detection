# Deletion Plan

Executed deletion set:

- `scripts/annotation_automation/review_app.py`
- `scripts/annotation_automation/prepare_annotation_corpus_v3_reviews.py`
- `scripts/annotation_automation/build_annotation_corpus_v3.py`
- `scripts/annotation_automation/train_yolov26.py`
- `scripts/annotation_automation/build_tiled_training_dataset.py`
- `scripts/annotation_automation/build_mixed_local_openimages_dataset.py`
- `scripts/annotation_automation/propagate_positive_reviews_v3.py`
- `scripts/annotation_automation/build_review_subset.py`
- `scripts/annotation_automation/export_annotation_candidates.py`
- `scripts/annotation_automation/score_reliability.py`
- `scripts/annotation_automation/evaluate_annotation_gate.py`
- `scripts/annotation_automation/integrate_reviewed_data.py`
- `scripts/annotation_automation/materialize_review_batches.py`

Deletion criteria that were satisfied before removal:

1. `python -m rbccps_od review-app` reproduces the existing local reviewer behavior.
2. `python -m rbccps_od sync-v3-reviews` reproduces the current v3 review workspace.
3. `python -m rbccps_od build-v3-corpus` reproduces the current local-night corpus outputs.
4. `python -m rbccps_od train` reproduces the current YOLOv26 baseline training invocation.
5. Optional experiment builders (`build-tiled`, `build-mixed`) match prior manifests and outputs.

## Remaining old code

These remain only because they are either extraction helpers or unreplaced reviewer utilities:

- extraction helpers
- reviewer contact-sheet / overlay helpers
