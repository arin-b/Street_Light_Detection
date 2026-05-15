# Validation and Labeling Protocol v2

This protocol replaces the ad hoc validation and manual-review policy used in the first YOLOv26 baseline run.

It is based on direct review of:

- [calibration_subset_manifest.csv](F:\RBCCPS_Directory\datasets\derived\annotation_automation\reviews\calibration_subset_manifest.csv)
- [hard_negative_review_manifest.csv](F:\RBCCPS_Directory\datasets\derived\annotation_automation\reviews\hard_negative_review_manifest.csv)
- the boxed calibration overlays
- the hard-negative contact sheets
- the first detector run artifacts from `streetlight_detector_v1-2`

## Why v1 was not enough

The first detector run exposed three immediate dataset-policy problems:

1. The validation slice was too small.
   - Only `48` validation images were seen during training.
   - Only `58` validation instances were present.
   - Metrics oscillated too much to support reliable model selection.

2. The training set had too little reviewed negative pressure.
   - Only `30` background images reached the training split.
   - This is weak relative to the real problem, where non-streetlight light sources are abundant.

3. The review labels were usable, but too permissive in the `ambiguous` bucket.
   - Several ambiguous examples from local night-road frames still showed visible streetlights and should not be considered recoverable negatives without re-review.

## Labeling protocol

### A. Positive streetlight box protocol

Annotate a box as `streetlight` only if all of the following are true:

- the light source is physically consistent with a roadside or public-area streetlight
- the emitting lamp head or clearly associated luminous unit is visible
- the box is centered on the emitting streetlight unit, not the illuminated road patch
- the box excludes large areas of empty sky, nearby buildings, or unrelated glare when possible

Do not annotate:

- vehicle headlights
- taillights
- shop lights
- signboards
- lit windows
- reflections
- flare blobs without a defendable lamp source

### B. Hard-negative review protocol

Use `clean_negative` only when:

- no visible streetlight should have been annotated
- no partially occluded but still identifiable lamp head is present
- the frame is not so blurred, saturated, or fogged that the absence of a streetlight is uncertain

Use `missed_positive` when:

- at least one visible streetlight is present
- or the scene is clearly lit by a visible lamp head that should have been boxed

Use `ambiguous` only when:

- visibility is too poor to defend either decision
- severe glare, bloom, fog, smear, or obstruction prevents a reliable judgment

Practical interpretation:

- `ambiguous` is a last resort, not a convenience label.
- If a visible streetlight exists, the frame is not a negative, even if the rest of the scene is noisy.

### C. Calibration lock protocol

Use `locked_clean` only when:

- the visible streetlight annotations are defensible as gold truth
- boxes are tight enough to support quantitative evaluation
- the scene is not so blurred or clipped that the annotation is debatable

Use `locked_negative` only when:

- the frame is a true clean negative under the hard-negative rule

Use `locked_needs_fix` when:

- boxes are visibly cropped, off-center, too loose, or too uncertain
- the image is dominated by glare or truncation
- there is a visible missed streetlight

## Validation policy v2

### Principles

1. Validation must be clip-held-out, not frame-held-out.
2. Validation must cover more than one clip family per source.
3. Validation must contain hard conditions, not only easy positives.
4. Validation backgrounds must include reviewed clean negatives.
5. Calibration gold images are not substitutes for a held-out validation split.

### Clip selection rule

Keep the large independent test families for final testing.

Use validation to cover:

- busy urban glare-heavy Jobin scenes
- a second Jobin family with different street geometry
- small but distinct Arindam clip families
- one Arindam residential-style family

### Validation target

For the next serious run, validation should be roughly:

- `140+` positive images
- `15+` reviewed clean-negative images
- multiple clip families from both Jobin and Arindam

This is still small, but substantially better than the original `48`-image validation set.

## Review audit findings under this protocol

### Calibration

- The calibration review is mostly usable.
- `166` rows are locked clean.
- `1` row is locked negative.
- `15` rows remain intentionally excluded as `locked_needs_fix`.

### Hard negatives

- The current reviewed pool yields only `45` defendable clean negatives.
- `77` rows remain ambiguous.
- `125` rows were correctly identified as `missed_positive`.

Observed pattern from contact-sheet review:

- many `local_extracted_night` ambiguous scenes still show visible streetlights and should stay out of the negative pool
- many `hf_night_external` ambiguous scenes are dominated by glare, bloom, or low visibility and are not suitable as clean negatives without re-review

Conclusion:

- the current reviewed pool is enough to improve the next run modestly
- it is not enough to solve the negative-coverage problem completely
- more negative mining is still required after run 2

## What changes for run 2

1. Rebuild the split with a larger clip-held-out validation set.
2. Integrate all reviewed `clean_negative` images into the dataset export.
3. Preserve independent test families instead of stealing them for validation.
4. Keep ambiguous and missed-positive frames out of the negative pool.
5. Re-run the same detector family before making architecture changes.

## External annotated dataset policy

An external open-source annotated source may be added to the corpus, but it must not be dumped wholesale into training.

Current intended use:

- extract only the relevant `streetlight` subset from an appropriate road-scene dataset
- normalize it into the same one-class `streetlight` ontology
- keep source provenance so every external image remains distinguishable from `Jobin` and `Arindam`

Approved role of external annotations:

1. training augmentation
2. later held-out testing for cross-dataset generalization

Required rule:

- do not consume all external annotations as training data
- reserve a source-held-out external slice for later testing
- keep that held-out slice untouched during detector tuning and reliability-gate calibration

Recommended workflow:

1. extract the external `streetlight` subset into its own manifest and YOLO export
2. review a sample for ontology match with the `full visible luminaire` rule
3. split the external source into:
   - eligible training augmentation
   - held-out external validation or test
4. use the held-out external slice only after the detector is stabilized on the cleaned local corpus

Implementation note:

- the extraction path for this is already scaffolded by [extract_mapillary_vistas_streetlights.py](F:\RBCCPS_Directory\scripts\annotation_automation\extract_mapillary_vistas_streetlights.py)
