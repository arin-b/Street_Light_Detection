# Run 3 Accuracy Recovery Implementation

This note turns the run-3 recovery plan into an executable local pipeline.

It assumes the target is:

- highest local-night streetlight accuracy first
- heavy manual review allowed
- higher compute allowed when it buys recall

## Current interpretation

The current evidence supports this order:

1. clean the local corpus harder
2. retrain a local-only baseline
3. if recall remains weak, switch to tiled small-object training
4. only then test light external augmentation

Do not reverse that order.

## Implemented pipeline pieces

### 1. V3 review workspace

Use:

- `python -m rbccps_od sync-v3-reviews`

This script:

- pulls current `Jobin` click-review decisions into a dedicated v3 review workspace
- initializes `Arindam` positive review rows if none exist yet
- maps existing hard-negative labels into v3 negative-review states
- writes:
  - `jobin_positive_review_v3.csv`
  - `arindam_positive_review_v3.csv`
  - `negative_review_v3.csv`
  - `scene_bucket_manifest_v3.csv`
  - `promoted_positive_queue_v3.csv`

### 2. Guarded local corpus builder

Use:

- `python -m rbccps_od build-v3-corpus`

This script:

- consumes the v3 review CSVs
- preserves the local clip-held-out split policy from v2
- admits:
  - reviewed `keep`
  - reviewed `fix_box` with explicit replacement boxes
  - reviewed `clean_negative`
- excludes:
  - explicit positive exclusions
  - promoted negatives
  - ambiguous negatives
- blocks strict materialization when:
  - positives are still pending
  - required fix rows do not have replacement boxes
  - retained rows are missing required scene buckets

Outputs:

- `annotation_automation_v3/yolo_dataset`
- `annotation_automation_v3/manifests/merged_manifest_v3.csv`
- `annotation_automation_v3/reports/readiness_report_v3.md`
- `annotation_automation_v3/reports/corpus_summary_v3.json`

### 3. Small-object tiled training path

Use:

- `python -m rbccps_od build-tiled`

Locked defaults:

- tile size: `1024`
- stride: `768`
- retained box fraction: `0.6`
- minimum retained side: `6 px`

This tiles only the `train` split and keeps `valid` and `test` full-image.

### 4. Controlled local plus external mixing

Use:

- `python -m rbccps_od build-mixed`

Locked defaults:

- external total ratio: `0.15`
- external positive fraction: `0.8`

This means:

- local train remains the backbone
- only a light sampled fraction of external Open Images train is added
- local validation and test stay unchanged
- external Open Images validation and test remain separate evaluation sources

### 5. Cross-platform training wrapper fix

Use:

- `python -m rbccps_od train`

It now auto-rewrites Windows-authored dataset YAML `path:` entries when training on Linux, so the AnyDesk/HPC Linux runs do not need manual temporary YAML rewriting.

## Exact command order

### A. Sync the v3 review workspace

```bash
python -m rbccps_od sync-v3-reviews
```

### B. Complete the remaining manual review

Required files:

- `jobin_positive_review_v3.csv`
- `arindam_positive_review_v3.csv`
- `negative_review_v3.csv`

### C. Build the strict local v3 corpus

```bash
python -m rbccps_od build-v3-corpus
```

If you want only a preview build before review is complete:

```bash
python -m rbccps_od build-v3-corpus --allow-unreviewed-positives --allow-missing-scene-buckets
```

Do not treat that preview build as the next serious baseline.

### D. Train the local-only baseline

```bash
python -m rbccps_od train --model datasets/yolov26_weights/yolo26m.pt --data datasets/derived/annotation_automation_v3/yolo_dataset/dataset.yaml --imgsz 1280 --epochs 60 --batch 4 --device 0 --project runs --name streetlight_detector_v3_local --patience 20 --workers 8 --close-mosaic 10
```

### E. If recall is still weak, build the tiled train split

```bash
python -m rbccps_od build-tiled --dataset-root datasets/derived/annotation_automation_v3/yolo_dataset --output-root datasets/derived/annotation_automation_v3_tiled/yolo_dataset
```

Then train:

```bash
python -m rbccps_od train --model datasets/yolov26_weights/yolo26m.pt --data datasets/derived/annotation_automation_v3_tiled/yolo_dataset/dataset.yaml --imgsz 1024 --epochs 60 --batch 4 --device 0 --project runs --name streetlight_detector_v3_tiled --patience 20 --workers 8 --close-mosaic 10
```

### F. Only after a strong local baseline exists, test light external augmentation

```bash
python -m rbccps_od build-mixed --local-root datasets/derived/annotation_automation_v3/yolo_dataset --external-root datasets/derived/openimages_streetlight_external --output-root datasets/derived/annotation_automation_v3_mixed
```

Then train:

```bash
python -m rbccps_od train --model datasets/yolov26_weights/yolo26m.pt --data datasets/derived/annotation_automation_v3_mixed/dataset.yaml --imgsz 1280 --epochs 60 --batch 4 --device 0 --project runs --name streetlight_detector_v3_mixed --patience 20 --workers 8 --close-mosaic 10
```

## Manual blockers that still remain

These are not solved automatically:

- the remaining `Arindam` positive review
- the remaining local-negative scene-bucket tagging
- any positive `fix_box` rows without replacement boxes
- final approval that the retained local positives all obey the `full visible luminaire` rule

Until those are done, the strict v3 build should be considered blocked on purpose.
