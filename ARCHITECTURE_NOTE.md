# Nighttime Streetlight OD Architecture Note

## Baseline path

The baseline path preserves the current reviewed-data local-night workflow:

1. `rbccps_od.review.app` serves the click-review UI.
2. `rbccps_od.datasets.review_sync` syncs the click-review state into the v3 review workspace.
3. `rbccps_od.datasets.corpus_v3` builds the guarded local-night corpus with one-class `streetlight` semantics, clip-safe splits, and hard-negative-aware construction.
4. `rbccps_od.training.train` launches the current YOLOv26 baseline with reusable dataset YAML path resolution.

This path remains the default and reproducible route when all advanced stages are disabled.

## Advanced path

The advanced path is modular and optional. It is orchestrated by `rbccps_od.pipeline.advanced_runner` and consists of:

1. `EnhancementStage`: optional low-light enhancement of the dark frame.
2. `PairedInputFrame`: original dark frame plus optional enhanced/light frame.
3. `DecompositionStage`: optional Retinex or decomposition branch producing reflectance and illumination views.
4. `DetectionStage`: YOLO detector invocation with an optional domain adaptation adapter that can sit alongside detector inference.
5. `TrackingStage`: track association with a camera-motion-compensation hook.
6. `MultiCueFilterStage`: cue scoring over trajectory, size progression, light characteristics, and position prior.
7. `aggregator.weighted_aggregate`: explicit weighted fusion.
8. `thresholding.threshold_score`: explicit final accept/reject decision.

## Where the proposed PDF elements plug in

- Low-light enhancement -> `rbccps_od.models.enhancer` and `pipeline/enhancement_stage.py`
- Paired light/dark input handling -> `pipeline/paired_input.py`
- YOLO detector with domain adaptation -> `models/yolo26.py` + `models/domain_adaptation.py` + `pipeline/detection_stage.py`
- Retinex/decomposition branch -> `models/retinex.py` + `pipeline/decomposition_stage.py`
- Tracking -> `models/tracker.py` + `pipeline/tracking_stage.py`
- Multi-cue filtering and thresholding -> `pipeline/multicue_stage.py`, `pipeline/aggregator.py`, and `pipeline/thresholding.py`

## Model management

External assets are managed through:

- `config/model_registry.py`
- `models/registry.py`
- `models/downloader.py`
- `models/checkpoint_resolver.py`

The registry is manifest-driven and supports named assets, versions, cache layout, and checksums when available. Placeholder entries are included where the exact source URL was not derivable from the uploaded repository contents.

## Important limitation

The uploaded artifact contained the legacy `scripts/annotation_automation` tree but did not contain the referenced design markdown files or the PDF. The advanced pipeline structure in this refactor therefore mirrors the documented components described in the task prompt and is wired as configurable scaffolding so exact checkpoint URLs and stage internals can be filled in without changing the architecture.
