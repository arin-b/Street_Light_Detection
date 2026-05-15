# Annotation Automation Readiness Assessment

This note evaluates the currently available `Jobin` annotated dataset, the `Arindam` annotated dataset, and the available `YOLOv26` weights against the requirements defined in:

- [annotation_automation_system.md](F:\RBCCPS_Directory\documentation\system_design\new_design\annotation_automation_system.md)

## Bottom line

Not good enough yet for annotation automation as defined in [annotation_automation_system.md](F:\RBCCPS_Directory\documentation\system_design\new_design\annotation_automation_system.md). What you currently have is good enough to bootstrap a seed detector, but not to operate the automated annotation system safely.

## Main findings for the Jobin dataset

- The Jobin export violates the split policy required by the protocol. All three splits contain the same clip families: `train_set_1`, `train_set_2`, `val_set_1`, `val_set_2`, `test_set_1`, and `test_set_2`. That means clip-level separation is broken, even if exact frame filenames differ. For automation, this makes validation optimistic and invalidates the `AUC >= 0.95` gate.
- The Jobin seed dataset has no negative-only frames. I checked all `839` images in [jobin-original-annotated-images](F:\RBCCPS_Directory\datasets\annotated_seed\jobin-original-annotated-images): every image has at least one positive annotation. That is not enough for the protocol's hard-negative requirement, because the automation system must learn what not to label.
- The Jobin class schema is dirty. In the COCO JSONs, the actual annotated category is `id=1, name='0'`, with an extra dataset-level category entry. This is fixable, but it should be normalized before any training or reliability calibration.
- Provenance and review metadata are missing. The export only carries generic frame filenames and a `version1` tag. The protocol requires dataset ID, clip ID, frame ID, acceptance band, reviewer status, model version, and review traceability. None of that exists yet in a usable annotation-automation form.

## Main findings for the Arindam dataset

- The Arindam export has only one split: `train`. There is no `valid` or `test` export present in [nighttime-streetlight-detection.coco](F:\RBCCPS_Directory\datasets\annotated_seed\arindam-annotated-images\nighttime-streetlight-detection.coco). That means it cannot support the annotation protocol's validation gate by itself.
- The Arindam dataset has broader clip-family coverage than Jobin. I found `10` clip families: `set_1`, `set_3`, `set_4`, `set_5`, `set_7`, `set_8`, `set_13`, `set_15`, `train_set_1`, and `train_set_2`. That is better for seed diversity, but it still needs clean clip-level splitting before use in automation.
- The Arindam class schema is mixed and inconsistent. The COCO file has three category entries, and actual annotations are split across two positive category IDs:
  - `id=2, name='Streetlight'` with `1130` annotations
  - `id=1, name='0'` with `19` annotations
  This must be merged into one clean `streetlight` class before training or auto-label calibration.
- The Arindam dataset at least contains a small number of negative-only frames. I found `7` images without annotations out of `444` total images. That is better than Jobin, but still nowhere near enough hard-negative coverage for the automation protocol.
- Some of the empty Arindam frames look like valid hard negatives, but some also look ambiguous enough that they could be annotation misses rather than intentionally curated negative frames. Those frames need manual review before being treated as gold negatives.
- Provenance is still too weak for automation. As with Jobin, the export has frame names and Roboflow-style metadata, but not the full audit trail required by the annotation automation protocol.

## Main findings for the YOLOv26 weights

- The available weight file is [yolo26m.pt](F:\RBCCPS_Directory\datasets\yolov26_weights\yolo26m.pt).
- The checkpoint looks like a serialized Ultralytics PyTorch checkpoint and is suitable as a base model initialization.
- The checkpoint metadata references `yolo26m.yaml` and `coco.yaml`, and I found no evidence inside it that it is already a streetlight-specific or night-specific model.
- That is good as a base pretrained weight for fine-tuning, but not enough by itself for auto-annotation.

## What is good enough right now

- [yolo26m.pt](F:\RBCCPS_Directory\datasets\yolov26_weights\yolo26m.pt) is good enough as the starting pretrained weight for fine-tuning.
- [jobin-original-annotated-images](F:\RBCCPS_Directory\datasets\annotated_seed\jobin-original-annotated-images) is good enough as an initial manually annotated seed set, assuming you manually verify label quality first.
- [nighttime-streetlight-detection.coco](F:\RBCCPS_Directory\datasets\annotated_seed\arindam-annotated-images\nighttime-streetlight-detection.coco) is also good enough as an additional seed source after class cleanup and split reconstruction.

## What is not good enough yet

- Jobin is not valid for annotation automation evaluation in its current split form.
- Arindam is not valid for annotation automation evaluation in its current one-split form.
- Neither dataset currently provides enough reviewed hard negatives.
- Neither dataset currently carries the audit metadata required for automated label admission.
- The `YOLOv26` weights are not an annotation engine on their own; they are only a base checkpoint.

## What you still need before annotation automation is valid

- ~~Re-split both Jobin and Arindam by clip, not by exported Roboflow split.~~
- ~~Normalize the class mapping to a single clean `streetlight` class in both datasets.~~
- Add reviewed negative-only and hard-negative frames: headlights, taillights, signboards, traffic lights, reflections, glare-heavy scenes, lit windows, and shop lights.
- Build and lock a gold review subset for calibration, not just training.
- Fine-tune a first streetlight detector on the cleaned seed set.
- Calibrate and validate the annotation reliability layer on reviewed data so detector confidence is not used alone.
- Run cross-dataset validation on a trained detector and calibrated gate, because the current Jobin and Arindam exports alone are not sufficient to justify the `AUC >= 0.95` admission rule.
- ~~Add annotation metadata and audit fields so accepted auto-labels are traceable.~~
- Add an external open-source annotated streetlight source, but reserve part of it as a held-out source-specific test set instead of consuming all of it for training.

## What is implemented locally now

- ~~Clip-level split reconstruction~~ completed with leakage-free assignments written to:
  - [merged_manifest.csv](F:\RBCCPS_Directory\datasets\derived\annotation_automation\manifests\merged_manifest.csv)
- ~~Class normalization~~ completed with cleaned source-of-truth COCO files written to:
  - [jobin_cleaned.coco.json](F:\RBCCPS_Directory\datasets\derived\annotation_automation\cleaned_coco\jobin_cleaned.coco.json)
  - [arindam_cleaned.coco.json](F:\RBCCPS_Directory\datasets\derived\annotation_automation\cleaned_coco\arindam_cleaned.coco.json)
- ~~Merged training corpus export~~ completed with derived YOLO dataset written to:
  - [dataset.yaml](F:\RBCCPS_Directory\datasets\derived\annotation_automation\yolo_dataset\dataset.yaml)
- ~~Hard-negative review manifest creation~~ completed with a seeded review queue written to:
  - [hard_negative_review_manifest.csv](F:\RBCCPS_Directory\datasets\derived\annotation_automation\reviews\hard_negative_review_manifest.csv)
- ~~Calibration subset manifest creation~~ completed with a pending review subset written to:
  - [calibration_subset_manifest.csv](F:\RBCCPS_Directory\datasets\derived\annotation_automation\reviews\calibration_subset_manifest.csv)
- ~~Traceable seed annotation metadata~~ completed with seed-level provenance written to:
  - [annotation_metadata_seed.csv](F:\RBCCPS_Directory\datasets\derived\annotation_automation\manifests\annotation_metadata_seed.csv)
- ~~Remote detector training package~~ completed with a portable package written to:
  - [remote_package](F:\RBCCPS_Directory\datasets\derived\annotation_automation\training\remote_package)
- ~~Annotation reliability gate scaffolding~~ completed with local scripts written to:
  - [score_reliability.py](F:\RBCCPS_Directory\scripts\annotation_automation\score_reliability.py)
- ~~Cross-dataset validation scaffolding~~ completed with source-specific split manifests and cleaned validation splits prepared locally.
- ~~Reviewer batch materialization tooling~~ completed with a local script written to:
  - [materialize_review_batches.py](F:\RBCCPS_Directory\scripts\annotation_automation\materialize_review_batches.py)
- ~~Reviewed-negative ingestion tooling~~ completed with a local script written to:
  - [integrate_reviewed_data.py](F:\RBCCPS_Directory\scripts\annotation_automation\integrate_reviewed_data.py)
- ~~Gate evaluation tooling~~ completed with a local script written to:
  - [evaluate_annotation_gate.py](F:\RBCCPS_Directory\scripts\annotation_automation\evaluate_annotation_gate.py)

## What remains manual right now

- Review every row in [hard_negative_review_manifest.csv](F:\RBCCPS_Directory\datasets\derived\annotation_automation\reviews\hard_negative_review_manifest.csv) and mark each candidate as `clean_negative`, `ambiguous`, or `missed_positive`.
- Review and lock every row in [calibration_subset_manifest.csv](F:\RBCCPS_Directory\datasets\derived\annotation_automation\reviews\calibration_subset_manifest.csv).
- Decide which reviewed negative frames are trusted enough to be admitted into the cleaned corpus.
- Run the first remote GPU training job for the streetlight detector using the generated remote package.
- Review candidate auto-labels that fall into the `manual-review` band after detector inference is available.
- Approve the final `auto-accept` threshold only after the calibrated gate satisfies `AUC >= 0.95` on pooled and source-specific validation.

## External dataset decision

The current dataset-formation plan now explicitly allows an external open-source annotated road-scene source to be added for `streetlight` extraction.

That external source is not train-only.

Use it in two roles:

1. as additional training augmentation after ontology cleanup
2. as a later held-out external test slice for generalization checking

The important rule is that external annotations must retain source identity and must not all be merged blindly into the training pool.

Implementation note:

- the extraction scaffold for this is already present in [extract_mapillary_vistas_streetlights.py](F:\RBCCPS_Directory\scripts\annotation_automation\extract_mapillary_vistas_streetlights.py)

## How to close each gap

### 1. Cleaned clip-level splits

How to do it:

- Ignore the current Roboflow split folders as ground truth for evaluation.
- Reconstruct clip identity from the original frame names before the `.rf.` suffix.
- Treat clip families such as `set_13`, `set_15`, `train_set_1`, and `train_set_2` as indivisible units.
- Build a new manifest table with one row per image and at least:
  - `dataset_id`
  - `clip_id`
  - `frame_id`
  - `image_path`
  - `has_annotation`
- Re-split at the `clip_id` level into `train`, `valid`, and `test`.
- Keep all frames from any one clip in exactly one split.

Recommended rule:

- Use `70/15/15` by clip.
- Reserve at least `2` clip families from Arindam for validation and testing.
- Reserve at least `1` full clip family from Jobin for validation or testing.

Expected outcome:

- A leakage-free split that can support real detector evaluation and later annotation-gate calibration.

### 2. Class normalization

How to do it:

- Load both COCO exports.
- Merge all positive categories into one canonical category:
  - `id: 1`
  - `name: streetlight`
- Rewrite all annotations with positive IDs `0`, `1`, or `2` into the canonical `streetlight` class where they are semantically the same.
- Remove unused category records.
- Re-export clean COCO JSONs and, if needed, YOLO-format labels derived from the cleaned COCO source.

Recommended rule:

- Keep the cleaned COCO files as the source of truth.
- Generate any YOLO labels from those files, not by editing TXT labels manually.

Expected outcome:

- One consistent ontology across Jobin and Arindam, which is required for mixed-source training.

### 3. Reviewed hard negatives

How to do it:

- Create a dedicated negative-mining folder from:
  - empty Arindam frames
  - unlabeled night frames from your own Bengaluru videos
  - hard frames from the downloaded night-driving datasets
- Curate frames containing:
  - oncoming headlights
  - parked vehicles with lights
  - traffic lights
  - illuminated signboards
  - shop lighting
  - window lighting
  - glare pools
  - wet-road reflections
  - lens flare
- Review these manually and mark each frame as:
  - `clean_negative`
  - `ambiguous`
  - `missed_positive`

Recommended minimum:

- Build at least `200 to 500` reviewed negative-only frames before trusting any automation loop.
- Make sure these negatives come from multiple clip families and not one road type only.

Expected outcome:

- A negative set that teaches the detector and the reliability gate what should not be auto-labeled.

### 4. Reviewed calibration subset

How to do it:

- Build a gold subset that is never used for pseudo-label promotion.
- Sample it deliberately from:
  - clean streetlight scenes
  - glare-heavy scenes
  - traffic-heavy scenes
  - distant streetlight scenes
  - occluded streetlight scenes
  - negative-only scenes
- Review every image and every annotation manually.
- Lock this subset and do not mutate it casually between runs.

Recommended minimum:

- `150 to 300` images, balanced across easy, hard, and negative conditions.

Expected outcome:

- A stable set for calibrating the reliability model and computing the annotation-system `AUC`.

### 5. Fine-tuned streetlight detector

How to do it:

- Start from [yolo26m.pt](F:\RBCCPS_Directory\datasets\yolov26_weights\yolo26m.pt).
- Fine-tune on the cleaned and merged Jobin + Arindam seed data.
- Train only a one-class detector:
  - `streetlight`
- Include the reviewed hard negatives in the training loop.
- Use clip-level validation only.

Recommended training order:

- Phase 1: train on cleaned positives plus a small negative set.
- Phase 2: add mined hard negatives and detector failure cases.
- Phase 3: freeze the best checkpoint as `detector_v1` for annotation generation.

Expected outcome:

- A first detector strong enough to propose candidate boxes for the annotation pipeline.

### 6. Reliability gate

How to do it:

- Do not use detector confidence alone.
- For every predicted box, compute a reliability score using features such as:
  - detector confidence
  - agreement across test-time augmentations
  - temporal persistence across nearby frames
  - agreement across checkpoints or folds
  - geometric plausibility, such as upper-scene placement and roadside structure
  - stability under mild exposure or enhancement perturbation
- Train or calibrate a lightweight reliability classifier on the reviewed calibration subset.
- Convert reliability scores into three operating bands:
  - `auto-accept`
  - `manual-review`
  - `auto-reject`

Recommended first implementation:

- Start with a weighted scoring rule before moving to a learned reliability model.
- Only move to learned calibration if the rule-based gate is too brittle.

Expected outcome:

- A promotion gate that can decide whether a candidate label is trustworthy enough to enter the training corpus.

### 7. Cross-dataset validation

How to do it:

- Evaluate the detector and the reliability gate on more than one source domain.
- At minimum, define:
  - pooled validation over cleaned Jobin + Arindam
  - source-specific validation on Jobin-only held-out clips
  - source-specific validation on Arindam-only held-out clips
  - additional validation on your own night-driving frames once reviewed labels exist
- Report:
  - detector `mAP@0.5`
  - detector recall
  - false positives by subtype
  - annotation reliability `AUC`

Recommended rule:

- Reject any `auto-accept` threshold that falls below `0.95 AUC` on any source-specific validation slice.

Expected outcome:

- A gate that generalizes across datasets instead of overfitting one export.

### 8. Traceable annotation metadata

How to do it:

- Maintain a manifest file, preferably CSV or JSONL, with one row per image and one row per accepted box if needed.
- Minimum image-level fields:
  - `dataset_id`
  - `clip_id`
  - `frame_id`
  - `image_path`
  - `split`
  - `review_status`
- Minimum annotation-level fields:
  - `annotation_id`
  - `class_name`
  - `bbox`
  - `annotation_origin`
  - `detector_version`
  - `reliability_version`
  - `detector_confidence`
  - `reliability_score`
  - `acceptance_band`
  - `reviewer_id`
  - `review_timestamp`

Recommended rule:

- Treat the manifest as the source of truth for the automation pipeline.
- Never admit auto-labels into training without writing their provenance.

Expected outcome:

- Full traceability of how each label entered the corpus and under which model and rule set.

## Recommended implementation order

1. Rebuild clip-level manifests for Jobin and Arindam.
2. Normalize classes into one canonical `streetlight` label.
3. Manually review the `7` Arindam empty frames and collect a much larger negative-only set.
4. Merge cleaned Jobin and Arindam into a new seed dataset.
5. Create a locked calibration subset from the merged data.
6. Fine-tune `YOLOv26` on the cleaned seed dataset.
7. Build the first reliability gate using reviewed calibration data.
8. Run candidate annotation on unlabeled night frames.
9. Promote labels only through the `auto-accept` band.
10. Re-train and repeat once the gate satisfies `AUC >= 0.95`.

## Bottom-line judgment by asset

- `Jobin annotated dataset`: sufficient as a seed dataset, not sufficient as the full basis for annotation automation.
- `Arindam annotated dataset`: useful as an additional seed dataset, not sufficient as the full basis for annotation automation.
- `YOLOv26 weights`: sufficient as base pretrained weights, not sufficient as the annotation engine.

## Practical interpretation

You do not need a brand new dataset before starting. You do need to convert the current assets into a proper seed corpus with clean splits, clean classes, reviewed negatives, and review metadata.

The best immediate use of the current assets is:

- Jobin for initial positive seed coverage
- Arindam for broader seed diversity and a few candidate negative frames
- `yolo26m.pt` as the base checkpoint for the first fine-tuned detector

## Final conclusion

You do require additional work according to the annotation protocol documentation.

The missing requirements are:

- reviewed hard negatives
- a reviewed calibration subset
- a fine-tuned streetlight detector
- a calibrated reliability gate
- executed cross-dataset validation on trained detector outputs

The current assets are strong enough to start building the seed detector. They are not strong enough to claim the annotation automation system is ready.

## Latest Implementation Status

Continued the annotation-automation implementation and pushed it past scaffolding.

What I added:
- [materialize_review_batches.py](F:\RBCCPS_Directory\scripts\annotation_automation\materialize_review_batches.py) to copy review images into reviewer-friendly folders
- [integrate_reviewed_data.py](F:\RBCCPS_Directory\scripts\annotation_automation\integrate_reviewed_data.py) to admit only reviewed `clean_negative` frames into the derived YOLO corpus
- [evaluate_annotation_gate.py](F:\RBCCPS_Directory\scripts\annotation_automation\evaluate_annotation_gate.py) to compute pooled and per-dataset gate AUC and threshold metrics
- [REVIEW_WORKFLOW.md](F:\RBCCPS_Directory\scripts\annotation_automation\REVIEW_WORKFLOW.md) so the manual review is explicit
- updated [scripts/annotation_automation/README.md](F:\RBCCPS_Directory\scripts\annotation_automation\README.md) and [annotation_automation_readiness.md](F:\RBCCPS_Directory\documentation\system_design\new_design\annotation_automation_readiness.md)

What I ran:
- Materialized reviewer batches at [reviews/batches](F:\RBCCPS_Directory\datasets\derived\annotation_automation\reviews\batches)
- Created `247` hard-negative review images and `182` calibration review images
- Verified the reviewed-negative ingestion script on the current manifests
- Current ingestion result is correct: `0` clean negatives admitted, `247` still pending, because no manual labels have been filled yet

What remains manual:
- Fill [hard_negative_review_manifest.csv](F:\RBCCPS_Directory\datasets\derived\annotation_automation\reviews\hard_negative_review_manifest.csv)
- Fill and lock [calibration_subset_manifest.csv](F:\RBCCPS_Directory\datasets\derived\annotation_automation\reviews\calibration_subset_manifest.csv)
- Use [REVIEW_WORKFLOW.md](F:\RBCCPS_Directory\scripts\annotation_automation\REVIEW_WORKFLOW.md) while doing that
- After that, rerun [integrate_reviewed_data.py](F:\RBCCPS_Directory\scripts\annotation_automation\integrate_reviewed_data.py)
- Then run the first GPU training job from [remote_package](F:\RBCCPS_Directory\datasets\derived\annotation_automation\training\remote_package)

The repo changes from this turn are limited to:
- [annotation_automation_readiness.md](F:\RBCCPS_Directory\documentation\system_design\new_design\annotation_automation_readiness.md)
- [README.md](F:\RBCCPS_Directory\scripts\annotation_automation\README.md)
- [REVIEW_WORKFLOW.md](F:\RBCCPS_Directory\scripts\annotation_automation\REVIEW_WORKFLOW.md)
- the three new Python utilities above

If you want, the next useful step is for me to make a very strict reviewer checklist for what counts as `clean_negative` versus `missed_positive` specifically for Bengaluru night street scenes.
