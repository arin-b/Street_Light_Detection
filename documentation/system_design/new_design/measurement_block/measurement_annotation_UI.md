# Measurement Annotation UI

I read the measurement-block LaTeX and the module diagrams. The annotator should be a **measurement annotation console**, not just an object-detection box tool. Its job is to turn raw Android night-video frames plus model predictions into the exact supervision needed by the measurement block: lamp tracks, public-space masks, affected regions, confounders, task visibility, attribution, QA, and optional lux-reference links.

## Core Idea

The human interface should be **track/keyframe based**.

Humans should not label every frame. The pipeline should first ingest videos, extract frames, run detector/tracker/segmentation/source models, then sample keyframes per lamp track and route. The annotator then lets a human correct and enrich those predictions.

The unit of work should be:

```text
route -> pass/clip -> frame/keyframe -> target lamp track -> measurement labels
```

Not:

```text
random image -> bounding boxes only
```

## Main UI Layout

A complete annotator should have five main areas:

1. **Left Queue / Dataset Browser**
   - Route list
   - Clip/pass list
   - Lamp-track list
   - Keyframe review queue
   - Filters for:
     - unreviewed
     - low confidence
     - saturated
     - occluded
     - confounded
     - missing affected region
     - missing lux point
     - QA failed

2. **Central Canvas**
   - Full original frame
   - Zoom/pan
   - Layer toggles:
     - raw image
     - lamp boxes/tracks
     - public-space masks
     - affected-region masks
     - confounder/source masks
     - dark patches
     - glare/saturation
     - lux points
     - model uncertainty
   - Drawing tools:
     - box
     - polygon
     - brush/eraser
     - soft-mask brush if possible
     - point marker
     - track-linking tool

3. **Right Inspector Panel**
   For the selected target lamp:
   - Track ID
   - frame ID/timestamp
   - detector confidence
   - tracking confidence
   - lamp status
   - affected regions
   - source/confounder labels
   - attribution confidence
   - task-visibility labels
   - QA status
   - optional lux-reference links

4. **Bottom Timeline**
   - Nearby frames around the selected keyframe
   - Track duration
   - detection confidence over time
   - exposure/luma trace
   - flicker cue
   - lost-count/track gaps
   - buttons for previous/next keyframe, previous/next lamp, play clip

5. **Top Toolbar**
   - Save
   - Save and next
   - Undo/redo
   - Accept model prediction
   - Clear selected layer
   - Mark uncertain
   - Mark unusable
   - Sign off / needs second review

## Annotation Modes

The annotator needs separate modes because the measurement block has several different label types.

### 1. Track Review Mode

- Correct lamp bounding boxes.
- Merge duplicate tracks.
- Split broken tracks.
- Mark false positives.
- Mark missed lamps.
- Preserve stable `track_id`.
- Track labels:
  - valid lamp
  - duplicate
  - false positive
  - missed continuation
  - partially visible
  - unusable

### 2. Lamp Status Mode

Required labels from the architecture:

- `on`
- `dim`
- `off`
- `flicker`
- `occluded`
- `saturated`
- `unknown`

Additional QA flags:

- motion blur
- camera exposure jump
- bloom
- HDR/night-mode artifact
- overexposed lamp core
- tree/building occlusion

### 3. Public-Space Mask Mode

Humans must correct model masks for:

- road
- footpath/sidewalk
- crossing
- curb
- median
- verge
- vegetation
- vehicle
- building/frontage
- shopfront/window
- sign/billboard
- traffic signal
- sky
- wet/reflection-like road
- occluder
- unknown

This is essential because the block measures useful illumination over public space, not brightness anywhere in the image.

### 4. Affected-Region Mode

For each selected target lamp, the annotator should draw the region plausibly served by that lamp.

Separate masks should exist for:

- affected road region
- affected footpath region
- affected crossing region
- affected verge/public-edge region

The label should include:

- affected-region mask
- region confidence: high / medium / low
- geometry quality
- whether the region is partially blocked
- whether another lamp also contributes

### 5. Source / Confounder Mode

The diagrams make this mandatory. The annotator should label competing light sources:

- target lamp
- other streetlights
- vehicle headlights
- shopfront/window light
- traffic signals
- signage/lightbox
- reflections
- wet-road glare
- construction/work lights
- unknown bright source

Each source should support:

- box or mask
- source type
- intensity class: weak / medium / strong
- overlaps target affected region: yes/no
- confounds attribution: yes/no

### 6. Task Visibility Mode

The measurement block is not only asking "is the image bright?" It asks whether the public-space task is adequately visible.

Per affected region, label:

- pedestrian visible
- road edge visible
- obstacle visible
- crossing visible
- dark patch present
- glare present
- visibility class:
  - good
  - adequate
  - marginal
  - poor
  - dark
  - unknown

### 7. Counterfactual Attribution Mode

The annotator should ask:

```text
Is this useful illumination actually attributable to the selected lamp?
```

Labels:

- `certain`
- `mixed`
- `uncertain`
- `impossible_due_to_confounding`

Plus evidence:

- dominated by target lamp
- shared with neighboring lamp
- dominated by headlights
- dominated by shop/sign light
- dominated by reflection
- target lamp visible but not serving public region

### 8. Lux / Reference Point Mode

Optional but required for physical calibration claims.

The UI should let humans attach field lux readings to frames/tracks using point labels:

- `P1`: under target lamp
- `P2`: midpoint between target and next lamp
- `P3`: road center / lane edge / safe roadside
- `P4`: sidewalk / pedestrian edge
- `P5`: darkest visible public-space patch
- `P6`: near confounder
- `P7`: opposite side
- `P8`: occluded or tree-shadowed side

Each lux point needs:

- lux value
- timestamp
- GPS if available
- frame ID
- route ID
- target lamp track ID
- measurement device/source
- calibration notes

### 9. QA / Uncertainty Mode

Every annotation item should support QA flags:

- accepted
- needs review
- unusable frame
- uncertain due to blur
- uncertain due to exposure
- uncertain due to occlusion
- uncertain due to confounders
- outside calibration validity
- physical lux invalid, proxy label only

## Important Data Outputs

The annotator should export these artifacts:

```text
annotations/
  manifest.json
  clips.csv
  frames.csv
  tracks.csv
  keyframes.csv
  lamp_status.csv
  public_space_masks/
  affected_region_masks/
  confounder_masks/
  visibility_labels.csv
  attribution_labels.csv
  lux_points.csv
  qa_flags.csv
```

Each row must preserve:

```text
route_id
clip_id
frame_id
timestamp_ms
original_width
original_height
track_id
bbox_original_xyxy
camera_metadata
gps/imu metadata if available
reviewer_id
review_status
```

## Minimum Viable Annotator

For the first usable version, build these modes first:

1. Track correction
2. Lamp status
3. Public-space mask correction
4. Confounder labels
5. Affected-region drawing
6. Visibility class
7. Attribution confidence
8. QA/signoff
9. Export manifest

That would support the actual training data needed for the research model.

## Full Research Annotator

The complete version should additionally include:

1. Soft affected-region masks
2. Temporal track correction across video
3. Flicker/stability clip labeling
4. Lux point linking
5. Calibration validity labeling
6. Source contribution review
7. Scene-graph relationship review:
   - lamp serves road
   - lamp serves footpath
   - lamp overlaps crossing
   - source confounds target lamp
   - object occludes region
8. Route-split enforcement to prevent train/test leakage

## Bottom Line

The measurement-block annotator should be a **multi-layer video/keyframe annotation system for per-lamp useful illumination**, not a generic bounding-box annotator.

Its core human task is:

```text
For this target lamp track, in this keyframe, what public space does it serve,
how well is that space visibly illuminated, what confounds that judgment,
and how confident are we that the illumination is attributable to this lamp?
```

That is the human interface implied by the LaTeX architecture and the module diagrams.
