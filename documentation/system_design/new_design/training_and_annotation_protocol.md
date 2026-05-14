# Training Protocol

## Scope

This document defines the proposed training protocol for the `Object Detection Block` under a constrained `YOLOv26-only` fine-tuning strategy.

The protocol is designed for the night-time streetlight auditing problem in mobile urban video, where the detector must identify true streetlights while rejecting other night light sources such as headlights, shop lighting, signboards, building lights, glare, and reflections.

This document is intentionally limited to detector training. Annotation automation is specified separately in:

- [annotation_automation_system.md](F:\RBCCPS_Directory\documentation\system_design\new_design\annotation_automation_system.md)

## 1. Detection Objective

The first-stage detector shall be trained as a `one-class detector`:

- `streetlight`

All non-streetlight light sources shall be treated as background or hard negatives.

The objective of this stage is not yet to determine `working`, `non-working`, or `illumination adequacy`. It is only to localize candidate streetlights with high recall while keeping false positives under control.

## 2. Base Model Strategy

The baseline system shall use `YOLOv26` only.

The following components from the larger conceptual system diagram shall be excluded from baseline training:

- paired dark/enhanced dual-input training
- Retinex branches
- domain adaptation side networks such as `DAI-Net`
- tracking-based supervision
- multi-cue post-filter aggregation in the training loop

These may be introduced later as controlled ablations, but they shall not be part of the first production-quality detector baseline.

## 3. Dataset Assembly

Training shall use all currently available relevant datasets and curated subsets, including:

- internally collected Bengaluru or India night-driving video frames
- Indian road-driving datasets with night or low-light coverage
- other curated night-driving or low-light proxy datasets where useful

Only relevant frames shall be retained for detector training. The dataset must prioritize:

- night-time road scenes
- visible streetlights in varied poses, distances, and occlusion conditions
- confusing negative examples such as headlights, taillights, signboards, traffic lights, lit windows, illuminated shops, and wet-road reflections

## 4. Split Policy

Data shall be split by `video clip`, not by frame.

This rule is mandatory. Frames from the same source clip shall never appear in more than one of:

- training
- validation
- testing

Recommended default split:

- `70%` training
- `15%` validation
- `15%` testing

If multiple datasets are used, the split must preserve source-level separation and must also support cross-dataset evaluation.

## 5. Training Data Standard

The training target is the visible lamp or lamp-head region corresponding to a streetlight instance.

Training labels should follow these rules:

- include true streetlights only
- exclude headlights, vehicle lamps, traffic lights, shop lights, windows, signboards, reflections, glare blobs, and ambiguous light streaks
- include partially occluded streetlights if object identity is still clear
- exclude isolated glow without a credible streetlight source
- maintain consistent box tightness across datasets

The quality of hard negatives is as important as the quality of positives.

## 6. YOLOv26 Fine-Tuning Protocol

### 6.1 Initialization

- start from pretrained `YOLOv26` weights
- do not train from scratch
- use the variant that matches deployment constraints, then scale upward only if recall is unacceptable

### 6.2 Training Target

- one-class detection: `streetlight`

### 6.3 Resolution

- prefer higher resolution than generic road-object detection because streetlights are often small and distant
- recommended first pass: `960` or `1280`, depending on memory and throughput

### 6.4 Augmentation

Use conservative augmentations that preserve nighttime light structure:

- horizontal flip
- mild scale and crop
- small rotation
- limited brightness and contrast jitter
- JPEG compression
- mild blur
- sensor-noise simulation
- motion blur

Avoid overly aggressive augmentations in the baseline:

- heavy mosaic
- strong mixup
- extreme color warping
- unrealistic illumination transforms

### 6.5 Hard-Negative Mining

Hard-negative mining is mandatory.

The training set must deliberately include frequent confusing cases:

- oncoming headlights
- taillights
- signboards
- shopfront lighting
- traffic lights
- building windows
- reflections on wet roads
- lens flare
- glare blooms

### 6.6 Two-Phase Training

Phase 1:

- train the baseline detector on the manually verified dataset
- optimize for stable recall and localization quality

Phase 2:

- collect detector failures from validation and cross-dataset inference
- add reviewed hard negatives and missed streetlight cases
- continue fine-tuning at lower learning rate

## 7. Evaluation Protocol

The detector shall be evaluated using:

- `mAP@0.5`
- `mAP@0.5:0.95`
- precision
- recall
- `F1`
- false positives by subtype

Evaluation must be reported separately for:

- dense urban roads
- heavy traffic scenes
- glare-heavy scenes
- low-light but non-empty roads
- occluded streetlights
- distant streetlights
- moving-camera scenes

## 8. Deployment Rule

The production detector used for phone deployment must be selected only after it shows acceptable recall and false-positive behavior on held-out night-driving data.

Any detector configuration that fails this criterion shall be considered non-deployable.

## 9. Recommended Development Order

1. Build a manually verified training set.
2. Fine-tune a plain `YOLOv26` one-class detector.
3. Add hard-negative mining.
4. Re-train with reviewed failures.
5. Introduce enhancement or temporal ablations only after the baseline is stable.
