# RBCCPS Streetlight Detection Current Work Context

## Current Goal

The project is focused on building a reliable nighttime streetlight object-detection system.

The current practical objective is to detect streetlights in nighttime driving imagery, improve accuracy beyond the cleaned `v3` YOLO baseline, inspect failure modes visually and statistically, and integrate the broader conceptual pipeline from the Object Detection Block PDF:

- low-light enhancement
- Retinex decomposition
- detector inference
- optional tracking
- multi-cue filtering

The immediate working checkpoint is:

```text
F:\RBCCPS_Directory\runs\streetlight_detector_v3_hpc_pull\best.pt
```

The main validation split is:

```text
F:\RBCCPS_Directory\datasets\derived\annotation_automation_v3\yolo_dataset\images\valid
```

It contains `121` images.

## Dataset And Review History

A cleaned local `v3` corpus was created after extensive manual review.

Canonical dataset:

```text
F:\RBCCPS_Directory\datasets\derived\annotation_automation_v3
```

Main YOLO dataset path:

```text
F:\RBCCPS_Directory\datasets\derived\annotation_automation_v3\yolo_dataset\dataset.yaml
```

The `v3` corpus was built from:

- reviewed `Jobin` positives
- reviewed `Arindam` positives
- reviewed local hard negatives
- scene-bucketed negative examples

The Open Images streetlight dataset was also extracted earlier, but it performed poorly as a standalone training source and is not the main training corpus.

Important conclusion:

```text
Open Images Street light is useful as external evaluation or light augmentation,
not as the primary training source for this target.
```

The ThirdEye Indian road dataset in the local repo appears to be unannotated for object detection. It contains images, not detection labels.

## Manual Review Completion

Manual review was completed for:

- `Jobin Positive Review`
- `Arindam Positive Review`
- `Negative Review`

The review app workflow eventually locked all three modes.

The review state was synced and the strict `v3` corpus was successfully materialized.

Important annotation rule:

```text
Positive = full visible luminaire.
```

Boxes that were glare-only, truncated, occluded, ambiguous, or pole/tree dominated were excluded or fixed.

## HPC Training Result

The cleaned `v3` local-night corpus was trained on the HPC using YOLOv26m.

Training checkpoint pulled back locally:

```text
F:\RBCCPS_Directory\runs\streetlight_detector_v3_hpc_pull\best.pt
```

HPC run:

```text
streetlight_detector_v3
```

Best model was saved around epoch `39`.

Final validated metrics from the HPC log for `best.pt`:

```text
Precision: 0.631
Recall:    0.575
mAP50:     0.590
mAP50-95:  0.310
```

This was a real improvement over the earlier `v2` model, which was around:

```text
mAP50:     ~0.416
mAP50-95:  ~0.193
```

Main interpretation:

```text
The v3 data cleanup helped substantially, but recall is still not good enough.
```

## Local Validation And Failure Analysis

The latest checkpoint was run on the full 121-image validation split.

Rendered YOLO-only prediction folder:

```text
F:\RBCCPS_Directory\runs\streetlight_detector_v3_val_predictions_all
```

Important files:

```text
F:\RBCCPS_Directory\runs\streetlight_detector_v3_val_predictions_all\failure_analysis.csv
F:\RBCCPS_Directory\runs\streetlight_detector_v3_val_predictions_all\failure_summary.json
```

Bucketed visual outputs were created under:

```text
F:\RBCCPS_Directory\runs\streetlight_detector_v3_val_predictions_all\failure_buckets
```

Failure buckets included:

- `clean_match`
- `missed_only`
- `false_positive_only`
- `mixed_fp_fn`
- `background_clean`
- `background_false_positive`

YOLO-only failure analysis at `conf=0.25` found:

```text
Images total:             121
Images with predictions:   91
True positives:            94
False positives:           41
False negatives:           80
```

Bucket counts:

```text
clean_match:                 38
missed_only:                 36
false_positive_only:         14
mixed_fp_fn:                 18
background_clean:            14
background_false_positive:    1
```

Main failure mode:

```text
Recall is the bigger issue. The model misses too many true streetlights,
especially multi-light frames and small/distant lamps.
```

Highest-signal missed examples included:

```text
jobin__val_set_1_frame_22.jpg
jobin__test_set_1_frame_3.jpg
jobin__val_set_1_frame_43.jpg
jobin__val_set_1_frame_58.jpg
```

Only one clean negative frame produced a false positive:

```text
neg__neg_0110__0044.jpg
```

## Codebase Refactor

The old flat `scripts/annotation_automation` object-detection code was replaced with a `src`-style package.

Current package:

```text
F:\RBCCPS_Directory\src\rbccps_od
```

Canonical command style:

```powershell
python -m rbccps_od <command>
```

Important commands:

```powershell
python -m rbccps_od review-app
python -m rbccps_od sync-v3-reviews
python -m rbccps_od build-v3-corpus
python -m rbccps_od train
python -m rbccps_od validate
python -m rbccps_od build-tiled
python -m rbccps_od build-mixed
python -m rbccps_od download-models
python -m rbccps_od run-baseline
python -m rbccps_od run-advanced-pipeline
```

Old OD script entrypoints were deleted after replacement.

Docs added or updated included:

```text
F:\RBCCPS_Directory\MIGRATION.md
F:\RBCCPS_Directory\DELETION_PLAN.md
F:\RBCCPS_Directory\ARCHITECTURE_NOTE.md
F:\RBCCPS_Directory\pyproject.toml
```

Tests passed after refactor:

```text
10 passed
```

Later focused tests around the advanced runner also passed:

```text
6 passed
```

## Object Detection Block PDF Context

The PDF read from:

```text
F:\RBCCPS_Directory\documentation\system_design\new_design\objectdet_block\Nighttime CV Proposed System Pipeline.pdf
```

Conceptual system blocks from the PDF:

- Data Preparation
- Low-light enhancement
- paired dark/light input
- YOLO detector
- DAI-Net style domain adaptation
- Retinex-Net decomposition
- tracking algorithms
- multi-cue filtering
- trajectory cue
- size progression cue
- light characteristics cue
- position prior cue
- weighted aggregation
- threshold decision

The markdown docs originally treated some of these as future extensions, but the desired direction became:

```text
Implement the broader conceptual pipeline as code, not just the YOLO baseline.
```

## Advanced Pipeline Assets

Downloaded/cached upstream source bundles:

```text
F:\RBCCPS_Directory\.cache\rbccps_od\models\lowlight_enhancer\master\Zero-DCE-master.zip
F:\RBCCPS_Directory\.cache\rbccps_od\models\retinex_decomposition\main\RetinexNet_Pytorch-main.zip
F:\RBCCPS_Directory\.cache\rbccps_od\models\domain_adaptation\main\DAI-Net-main.zip
F:\RBCCPS_Directory\.cache\rbccps_od\models\tracker_bundle\main\ByteTrack-main.zip
```

Important discoveries:

- `Zero-DCE` archive already contains:

```text
Zero-DCE-master/Zero-DCE_code/snapshots/Epoch99.pth
```

- `RetinexNet_Pytorch` archive already contains:

```text
RetinexNet_Pytorch-main/ckpts/ReNet_LOL/Decom/9200.tar
RetinexNet_Pytorch-main/ckpts/ReNet_LOL/Relight/9200.tar
```

- `DAI-Net` official repo references weights like:

```text
decomp.pth
vgg16_reducedfc.pth
DarkFace ZSDA / FS checkpoints
```

However, DAI-Net released weights are not streetlight-specific. The agreed decision was:

```text
Pin DAI-Net as an official source, but keep it disabled by default for the first streetlight run.
```

## Advanced Pipeline Implementation Status

The advanced runner was changed from a synthetic placeholder to a real pipeline.

Important changed files:

```text
F:\RBCCPS_Directory\src\rbccps_od\pipeline\advanced_runner.py
F:\RBCCPS_Directory\src\rbccps_od\models\enhancer.py
F:\RBCCPS_Directory\src\rbccps_od\models\retinex.py
F:\RBCCPS_Directory\src\rbccps_od\config\model_registry.py
F:\RBCCPS_Directory\src\rbccps_od\models\downloader.py
F:\RBCCPS_Directory\src\rbccps_od\models\checkpoint_resolver.py
F:\RBCCPS_Directory\src\rbccps_od\training\ultralytics_adapter.py
```

The synthetic fallback in `advanced_runner.py` was removed.

Old synthetic behavior:

```python
Detection(bbox=[0.0, 0.0, 1.0, 1.0], score=1.0)
```

That was replaced with real parsing of Ultralytics predictions into `Detection` objects.

Current advanced pipeline can run:

```text
input image
-> Zero-DCE enhancement
-> Retinex decomposition
-> detector inference
-> optional ByteTrack tracking
-> optional multi-cue filtering
-> overlays / JSON / summary outputs
```

The advanced runner supports:

- single image
- image directory batch
- sequence manifest
- sequence root

## Advanced Pipeline Smoke Runs

A single-image advanced smoke run succeeded:

```text
F:\RBCCPS_Directory\runs\advanced_pipeline_smoke
```

It produced:

- enhanced image
- Retinex reflectance image
- Retinex illumination image
- overlay with box
- detection JSON
- summary JSON

Example overlay showed a visible blue detection box:

```text
streetlight 0.79
```

A small sequence smoke run also succeeded:

```text
F:\RBCCPS_Directory\runs\advanced_pipeline_sequence_smoke
```

It processed 3 frames and produced:

```text
detections_total: 2
accepted_total:   2
track_total:      2
```

The multi-cue output included:

- trajectory cue
- size progression cue
- light characteristics cue
- position prior cue

## Current Live Advanced Batch Run

A full advanced batch run was started on the 121-image validation split.

Output folder:

```text
F:\RBCCPS_Directory\runs\advanced_pipeline_val_batch
```

It was launched with:

```text
Zero-DCE enabled
Retinex enabled
multi-cue enabled
tracking disabled for image-batch mode
```

As of the latest check:

```text
The process is still running.
summary.json is not present yet.
summary.csv is not present yet.
```

The folder is already producing outputs:

```text
F:\RBCCPS_Directory\runs\advanced_pipeline_val_batch\overlays
F:\RBCCPS_Directory\runs\advanced_pipeline_val_batch\enhanced
F:\RBCCPS_Directory\runs\advanced_pipeline_val_batch\retinex
F:\RBCCPS_Directory\runs\advanced_pipeline_val_batch\detections
```

Important note:

```text
The visible boxed detections are in the overlays folder.
The enhanced and retinex folders are intermediate images, not boxed outputs.
```

## Statistical Comparison Caveat

An interim statistical comparison was attempted between advanced outputs and YOLO-only outputs on the subset already processed.

It reported advanced pipeline as worse:

```text
Advanced: 0 TP, 32 FP, 63 FN
YOLO-only: 30 TP, 22 FP, 33 FN
```

However, that interim comparison should be treated as suspect because the script compared advanced detector boxes in pixel coordinates against YOLO-format ground truth labels that are normalized coordinates. That coordinate mismatch can invalidate the advanced TP/FP/FN calculation.

The correct comparison must normalize coordinate systems before matching:

```text
Either convert GT normalized YOLO labels to pixel boxes,
or convert advanced pixel boxes to normalized boxes.
```

So the only defensible statement right now is:

```text
The advanced pipeline is producing real outputs,
but we do not yet have a valid full statistical comparison against YOLO-only.
```

The earlier YOLO-only failure analysis is valid.

## Runs Folder Cleanup

The `runs` folder was partially cleaned.

Deleted:

```text
F:\RBCCPS_Directory\runs\advanced_pipeline_smoke
F:\RBCCPS_Directory\runs\advanced_pipeline_sequence_smoke
F:\RBCCPS_Directory\runs\detect\val
```

Kept:

```text
F:\RBCCPS_Directory\runs\advanced_pipeline_val_batch
F:\RBCCPS_Directory\runs\streetlight_detector_v3_hpc_pull
F:\RBCCPS_Directory\runs\streetlight_detector_v3_val_local
F:\RBCCPS_Directory\runs\streetlight_detector_v3_val_predictions_all
F:\RBCCPS_Directory\runs\streetlight_detector_v3_val_predictions_all.zip
```

The live advanced batch logs could not be deleted because the running process still held them open:

```text
F:\RBCCPS_Directory\runs\advanced_pipeline_val_batch_stdout.log
F:\RBCCPS_Directory\runs\advanced_pipeline_val_batch_stderr.log
```

## Key Technical Conclusions So Far

The cleaned `v3` dataset improved the detector substantially.

The current YOLO checkpoint detects streetlights, but recall is still weak.

The most important detector failure mode is missed streetlights, not false positives.

The broad advanced pipeline now runs real components for:

- Zero-DCE enhancement
- Retinex decomposition
- YOLO detection
- ByteTrack-style sequence tracking path
- multi-cue scoring

DAI-Net is not active yet because official weights are not streetlight-specific.

The full advanced batch run is still processing.

The advanced-vs-YOLO statistical comparison must be redone carefully after the full run finishes, with correct coordinate conversion.

## Recommended Next Steps

1. Wait for the current `advanced_pipeline_val_batch` run to finish.

2. Generate a valid advanced-vs-YOLO comparison using consistent pixel-coordinate matching.

3. Compare four ablations:

```text
YOLO only
YOLO + Zero-DCE
YOLO + Retinex
YOLO + Zero-DCE + Retinex
```

4. If advanced preprocessing hurts detection, keep it out of the training/eval path for now.

5. If recall remains the main issue, proceed with tiled/crop training.

6. Preserve the current `best.pt` as the strongest confirmed detector checkpoint until a new experiment beats it cleanly.

## Useful Commands

Check whether the advanced run finished:

```powershell
Test-Path F:\RBCCPS_Directory\runs\advanced_pipeline_val_batch\summary.json
```

List current advanced outputs:

```powershell
Get-ChildItem -Recurse F:\RBCCPS_Directory\runs\advanced_pipeline_val_batch | Select-Object FullName,Length,LastWriteTime
```

Open boxed detections:

```text
F:\RBCCPS_Directory\runs\advanced_pipeline_val_batch\overlays
```

Run YOLO validation:

```powershell
python -m rbccps_od validate --model runs\streetlight_detector_v3_hpc_pull\best.pt --data datasets\derived\annotation_automation_v3\yolo_dataset\dataset.yaml
```

Run advanced pipeline on the validation split:

```powershell
python -m rbccps_od run-advanced-pipeline --image-dir datasets\derived\annotation_automation_v3\yolo_dataset\images\valid --model runs\streetlight_detector_v3_hpc_pull\best.pt --enable-enhancement --enable-retinex --enable-multicue --name advanced_pipeline_val_batch
```

Run advanced pipeline on one image:

```powershell
python -m rbccps_od run-advanced-pipeline --image datasets\derived\annotation_automation_v3\yolo_dataset\images\valid\arindam__set_3_frame_11.jpg --model runs\streetlight_detector_v3_hpc_pull\best.pt --enable-enhancement --enable-retinex --name advanced_pipeline_single
```

## Current State In One Sentence

The project has a working cleaned-data YOLOv26 streetlight detector, a refactored object-detection package, and a real advanced enhancement/Retinex/detection pipeline currently running on the validation split; the next decisive step is a correct statistical comparison after that run finishes.
