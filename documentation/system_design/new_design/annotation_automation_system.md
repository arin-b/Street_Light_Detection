# Annotation Automation System

## Purpose

This document specifies the automated annotation subsystem for the streetlight object-detection pipeline.

Its role is to scale dataset creation for night-time streetlight detection in mobile urban video while enforcing a strict quality gate. The subsystem shall generate candidate streetlight annotations, estimate annotation reliability, route uncertain cases for review, and admit only sufficiently reliable labels into the training corpus.

This system is not responsible for final streetlight condition assessment or illumination scoring. Its job is only to create and maintain high-quality detection annotations for the `streetlight` class.

## Objective

The annotation system must support training a `YOLOv26` one-class detector that identifies:

- `streetlight`

The annotation system must reject or avoid incorrectly labeling:

- headlights
- taillights
- traffic lights
- illuminated signboards
- shop lights
- lit windows
- reflections
- glare blobs
- ambiguous streaks
- other non-streetlight night light sources

## Operating Principle

The system shall operate as a `human-in-the-loop automated annotation pipeline`.

It shall not behave as unrestricted pseudo-labeling. Automatic labels are allowed into the training set only after they pass a reliability gate that is validated across all available datasets.

The hard acceptance rule is:

- `AUC >= 0.95`

No automatic annotation configuration shall be accepted below that threshold.

## Inputs

The annotation system shall consume:

- raw night-driving videos
- extracted video frames
- manually annotated seed data
- existing labeled datasets from internal and external sources
- detector outputs from the current `YOLOv26` checkpoint
- optional clip metadata such as dataset source, video ID, frame ID, and time-of-day tags

Recommended source groups:

- internally collected Bengaluru or India night-driving video
- Indian night or low-light driving datasets
- curated proxy datasets with compatible labeling assumptions

## Outputs

The annotation system shall produce:

- reviewed bounding-box annotations for `streetlight`
- per-box reliability scores
- per-frame review status
- per-batch acceptance status
- audit metadata for provenance and review history

Each output annotation record should carry at least:

- dataset ID
- clip ID
- frame ID
- image path
- class label
- bounding box
- detector confidence
- reliability score
- acceptance band
- review status
- source model version

## Annotation Ontology

The labeling ontology for the detection stage shall remain intentionally narrow.

### Positive class

- `streetlight`

### Background / non-target classes

These are not labeled as positives and must be treated as negatives or ignored depending on the frame context:

- headlights
- taillights
- traffic lights
- shopfront lighting
- signboards
- windows
- reflections on wet roads
- lens flare
- glare bloom
- decorative lights

## Annotation Standard

The target annotation is the visible lamp or lamp-head region corresponding to a true streetlight instance.

Rules:

- annotate only credible streetlight sources
- annotate partially occluded streetlights if identity is still clear
- do not annotate isolated glow without a visible or strongly inferable streetlight source
- do not annotate generic bright regions that cannot be attributed to a streetlight
- maintain consistent box tightness across datasets and reviewers

## System Architecture

The annotation subsystem should be structured into the following stages.

### 1. Seed Set Construction

Build a small, manually verified gold-standard dataset first.

This seed set must:

- cover multiple road types
- include dense traffic and glare
- include distant and partially occluded streetlights
- include hard negatives
- be clip-balanced rather than frame-random

This seed set is the only source allowed to bootstrap the first model.

### 2. Initial Detector Training

Train an initial `YOLOv26` one-class detector on the gold-standard seed set.

This detector is not yet trusted for direct dataset expansion. Its only role is to generate candidate boxes for the automated annotation loop.

### 3. Candidate Generation

Run the detector over all unlabeled or weakly labeled night-driving data.

For each frame:

- infer candidate `streetlight` boxes
- keep raw detector confidence
- store the full prediction set before threshold-based pruning for later calibration

### 4. Candidate Cleaning

Apply deterministic post-processing before reliability scoring.

Required operations:

- duplicate suppression
- removal of clearly invalid boxes
- geometry sanity checks
- optional frame-border checks
- optional minimum-area filtering for obvious sensor noise artifacts

This stage must be conservative. It should remove clearly broken predictions, not aggressively suppress uncertain but plausible streetlights.

### 5. Reliability Scoring

Each candidate annotation must receive a secondary reliability score. This score is distinct from detector confidence.

Recommended reliability features:

- detector confidence
- consistency across test-time augmentations
- agreement across multiple checkpoints or folds
- temporal persistence across adjacent frames
- box stability under small image perturbations
- geometric plausibility in road context
- consistency with expected pole-height or upper-scene placement
- sensitivity to low-light enhancement or exposure variation

The reliability score should be calibrated as a classifier of annotation correctness.

### 6. Decision Bands

Each prediction must be placed into one of three bands:

- `auto-accept`
- `manual-review`
- `auto-reject`

Interpretation:

- `auto-accept`: reliable enough to enter the training corpus automatically
- `manual-review`: plausible but not sufficiently reliable for automatic admission
- `auto-reject`: likely false positive, ignored unless later mined for failure analysis

### 7. Manual Review Loop

The review loop should prioritize:

- predictions near the `auto-accept` threshold
- clips with many conflicting predictions
- novel domains or new dataset sources
- scenes with glare, reflections, traffic density, or occlusion

Human reviewers shall:

- confirm true positives
- delete false positives
- add missed streetlights if the frame is being reviewed anyway
- flag ambiguous cases for policy discussion

### 8. Corpus Admission

Only `auto-accept` predictions or manually approved predictions may enter the training corpus.

All accepted labels must preserve provenance:

- automatic vs manual origin
- model version
- review timestamp
- reviewer identifier if manually reviewed

### 9. Iterative Re-Training

After each accepted batch:

- merge reviewed labels into the training dataset
- re-split by clip if new source clips are added
- re-train or continue fine-tuning the detector
- re-run the annotation pipeline on remaining unlabeled data

This loop continues until error rates or coverage gains plateau.

## Reliability Gate

The key system requirement is a strict annotation-quality gate.

### Acceptance metric

- `AUC`, defined as area under the ROC curve for annotation correctness

### Hard threshold

- `AUC >= 0.95`

### Meaning

The annotation system must be evaluated as a classifier that distinguishes:

- correct annotations
- incorrect annotations

The detector confidence threshold alone is not sufficient. The final admission rule must be based on the calibrated reliability system.

## Cross-Dataset Validation

The annotation system must be validated under cross training from all available datasets.

Validation shall include:

- pooled validation across all datasets
- held-out internal night-video validation
- held-out Indian driving dataset validation
- held-out proxy validation where labels are compatible

The system is acceptable only if the `auto-accept` policy satisfies `AUC >= 0.95`:

- on the pooled validation set
- on each source-specific validation subset

If any source-specific validation subset falls below the threshold, the current annotation policy must be rejected or recalibrated.

## Dataset Split Policy

All annotation evaluation and detector re-training must obey clip-level separation.

Mandatory rule:

- frames from the same video clip shall never be distributed across training, validation, and test splits

This prevents temporal leakage and artificially inflated performance.

## Hard-Negative Strategy

The annotation system must explicitly preserve difficult negatives, because these scenes define the detector boundary.

Hard-negative categories to retain:

- oncoming headlights
- stationary headlights
- taillights
- traffic signals
- store fronts
- signboards
- lit windows
- glare pools
- wet-road reflections
- lens flare

These examples should be used both:

- during detector re-training
- during annotation-system failure analysis

## Failure Analysis

The annotation subsystem must maintain an explicit failure log.

Recommended failure buckets:

- headlight mistaken as streetlight
- traffic light mistaken as streetlight
- signboard mistaken as streetlight
- reflected light mistaken as streetlight
- distant streetlight missed
- partially occluded streetlight missed
- glare-dominated frame failure
- motion-blur failure
- overexposed frame failure

Each retraining cycle should review the dominant failure buckets before the next promotion of auto-labeled data.

## Review and Audit Metadata

Every annotation decision should be traceable.

Minimum metadata fields:

- source dataset
- source clip
- frame index
- annotation origin
- detector version
- reliability version
- acceptance band
- review decision
- review timestamp

This is necessary because the dataset will be accumulated iteratively rather than labeled in one pass.

## Recommended Operating Order

1. Build a gold-standard seed set manually.
2. Train a baseline `YOLOv26` detector.
3. Run automated candidate generation.
4. Score annotation reliability.
5. Enforce the `AUC >= 0.95` gate.
6. Admit only `auto-accept` or manually reviewed labels.
7. Retrain the detector.
8. Repeat until coverage and error rates stabilize.

## Non-Negotiable Rules

- no frame-level split leakage
- no unrestricted pseudo-label admission
- no use of detector confidence alone as the acceptance signal
- no deployment use of auto-annotation policy below `0.95 AUC`
- no collapse of negative-light-source categories into unlabeled noise during review

## Practical Interpretation

This annotation automation system is best understood as a controlled dataset-engineering pipeline, not just an inference script. Its core function is to expand the training corpus without corrupting it.

Because the target problem is night-time streetlight detection under heavy visual ambiguity, the annotation system must behave conservatively. Coverage may grow slowly, but label trust must remain high enough that each retraining cycle improves the detector rather than destabilizing it.
