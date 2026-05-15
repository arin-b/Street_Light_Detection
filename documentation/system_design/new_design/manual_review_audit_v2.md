# Manual Review Audit v2

This note audits the current manual-review artifacts against [validation_and_labeling_protocol_v2.md](F:\RBCCPS_Directory\documentation\system_design\new_design\validation_and_labeling_protocol_v2.md).

## Inputs reviewed

- [calibration_subset_manifest.csv](F:\RBCCPS_Directory\datasets\derived\annotation_automation\reviews\calibration_subset_manifest.csv)
- [hard_negative_review_manifest.csv](F:\RBCCPS_Directory\datasets\derived\annotation_automation\reviews\hard_negative_review_manifest.csv)
- boxed calibration overlays
- hard-negative contact sheets, especially the `ambiguous` pool

## Calibration audit

The calibration set is broadly usable for the next stage.

Current state:

- `locked_clean`: `166`
- `locked_negative`: `1`
- `locked_needs_fix`: `15`

Interpretation:

- the calibration corpus is large enough to remain the gold review subset
- the excluded `locked_needs_fix` rows should stay excluded
- no additional calibration relabeling is required before run 2

## Hard-negative audit

Current state:

- `clean_negative`: `45`
- `ambiguous`: `77`
- `missed_positive`: `125`

### What holds up

- The `clean_negative` pool is small but defensible.
- The `missed_positive` pool is directionally correct and should stay out of any negative-training export.

### What does not fully hold up

The `ambiguous` bucket is too broad under the stricter v2 protocol.

Observed pattern from the contact sheets:

- many `local_extracted_night` ambiguous frames visibly contain streetlights and are therefore not true negatives
- several `arindam_unannotated_seed` ambiguous frames are blur-dominated and already note ambient light from streetlights
- many `hf_night_external` ambiguous frames are genuinely visibility-limited due to glare, bloom, fog, or smear

Practical consequence:

- the `local_extracted_night` ambiguous pool should be re-reviewed first
- the `arindam_unannotated_seed` ambiguous rows should also be re-reviewed
- `hf_night_external` ambiguous rows can remain ambiguous for now unless more negative volume is urgently needed

## Re-review priority

Highest priority:

- ambiguous rows from `local_extracted_night`
- ambiguous rows from `arindam_unannotated_seed`

Lower priority:

- ambiguous rows from `hf_night_external`

Reason:

- the local ambiguous pool most often violates the v2 rule that visible streetlights cannot remain in the negative pool

## Output artifacts

- [hard_negative_rereview_candidates_v2.csv](F:\RBCCPS_Directory\datasets\derived\annotation_automation_v2\reports\hard_negative_rereview_candidates_v2.csv)

## Bottom line

The current manual reviews are sufficient to run experiment 2, but not sufficient to claim the negative-mining problem is solved.

The right order is:

1. run experiment 2 with the rebuilt validation policy
2. inspect detector failures
3. re-review the local ambiguous pool
4. mine an additional batch of candidate negatives
