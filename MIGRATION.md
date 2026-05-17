# Migration Guide

This repo now exposes a src-style package rooted at `src/rbccps_od`.

## Command mapping

| Legacy command | New command |
| --- | --- |
| deleted script path | `python -m rbccps_od review-app` |
| deleted script path | `python -m rbccps_od sync-v3-reviews` |
| deleted script path | `python -m rbccps_od build-v3-corpus` |
| deleted script path | `python -m rbccps_od train` |
| deleted script path | `python -m rbccps_od build-tiled` |
| deleted script path | `python -m rbccps_od build-mixed` |
| deleted script path | `python -m rbccps_od propagate-reviews` |
| deleted script path | `python -m rbccps_od build-review-subset` |
| deleted script path | `python -m rbccps_od export-candidates` |
| deleted script path | `python -m rbccps_od score-reliability` |
| deleted script path | `python -m rbccps_od evaluate-gate` |
| deleted script path | `python -m rbccps_od integrate-reviewed-data` |
| deleted script path | `python -m rbccps_od materialize-review-batches` |
| model asset fetching by ad hoc local copies | `python -m rbccps_od download-models` |
| ad hoc detector inference scripts | `python -m rbccps_od run-baseline` or `python -m rbccps_od run-advanced-pipeline` |

## Module mapping

- deleted `review_app.py` -> `rbccps_od.review.repository` + `rbccps_od.review.app`
- deleted `prepare_annotation_corpus_v3_reviews.py` -> `rbccps_od.datasets.review_sync`
- deleted `build_annotation_corpus_v3.py` -> `rbccps_od.datasets.corpus_v3`
- deleted `build_tiled_training_dataset.py` -> `rbccps_od.datasets.tiled`
- deleted `build_mixed_local_openimages_dataset.py` -> `rbccps_od.datasets.mixed_external`
- deleted `build_review_subset.py` -> `rbccps_od.review.subset`
- deleted `propagate_positive_reviews_v3.py` -> `rbccps_od.review.propagation`
- deleted `train_yolov26.py` -> `rbccps_od.training.train`
- deleted `export_annotation_candidates.py` -> `rbccps_od.pipeline.export_candidates`
- deleted `score_reliability.py` -> `rbccps_od.evaluation.reliability`
- deleted `evaluate_annotation_gate.py` -> `rbccps_od.evaluation.gate`
- deleted `integrate_reviewed_data.py` -> `rbccps_od.datasets.negative_integration`
- deleted `materialize_review_batches.py` -> `rbccps_od.review.materialize_batches`
- Windows-to-Linux dataset YAML rewriting -> `rbccps_od.training.dataset_yaml.resolve_dataset_yaml_for_runtime`

## Migration posture

The new package is now the active architecture. The superseded OD script entrypoints have been removed.
