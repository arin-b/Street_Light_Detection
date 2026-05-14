# RBCCPS Streetlight Auditing Project

## Overview

This repository is a working project directory for the development of an automated streetlight auditing system based on computer vision. The target application is night-time assessment of streetlight condition and performance from road imagery and mobile video captured in urban environments.

The intended system is being developed for deployment in Bangalore under the municipal corporation of Bangalore. The broader objective is to support scalable infrastructure auditing by identifying streetlights, assessing whether they are functioning, and estimating the adequacy of the illumination they provide to roads and nearby public areas.

## Institutional Context

This work is being carried out under RBCCPS, Indian Institute of Science (IISc).

## Team

- Angad Singh Ahuja, Research Intern, RBCCPS, IISc
- Arindam Bhaduri, Research Intern, RBCCPS, IISc

## Academic Supervision

The work is being conducted under the guidance of:

- Prof. Prasant Misra
- Prof. Pandrasamy Arjunan

## Project Scope

The current repository contents indicate work across the following areas:

- literature review on object detection, low-light enhancement, domain adaptation, tracking, illumination measurement, and streetlight-related auditing
- dataset collection and organization for night-time road scenes and related imported image corpora
- annotation automation scripts for rebuilding training corpora, review manifests, and detector handoff packages
- system-design material for a streetlight auditing pipeline
- measurement-block planning for estimating useful illumination from detected and tracked streetlights on edge devices such as mobile phones

## Repository Structure

```text
RBCCPS_Directory/
  datasets/
  documentation/
  scripts/
  .gitignore
  README.md
```

### `datasets/`

Contains local dataset storage used for research and experimentation, including raw videos, extracted frames, imported datasets, and derived artifacts. The annotation automation pipeline writes generated datasets, manifests, reviews, reports, and remote-training handoff files under `datasets/derived/annotation_automation/`. The current organization of this directory is documented in [datasets/README.md](datasets/README.md).

### `documentation/`

Contains literature-review material, downloaded references, bibliography files, and system-design notes related to the streetlight auditing problem.

### `scripts/`

Contains tracked implementation code for local workflows. The annotation automation pipeline scripts live under [scripts/annotation_automation/README.md](scripts/annotation_automation/README.md).

## Version Control Notes

This directory is initialized as a Git repository. `.gitignore` has been prepared to keep large datasets, regenerated artifacts, and local-only research assets out of version control by default.

## Ignored Folders

The following folders are intentionally listed in `.gitignore` because they contain large binary assets, regenerated data, or imported reference material that should usually remain outside version control.

| Path | Category | Primary Contents | Source / Provenance | Reason for Exclusion |
| --- | --- | --- | --- | --- |
| `datasets/raw/` | Raw capture storage | Original night-drive video clips (`.mp4`) | Phone or vehicle-mounted capture sessions | Large binary source inputs; retained locally rather than versioned |
| `datasets/extracted_frames/` | Derived dataset storage | Frame batches extracted from raw videos (`.jpg`) | Generated during preprocessing | Regenerable from source videos and large in volume |
| `datasets/imported/` | External dataset storage | Imported datasets and platform exports | Roboflow exports and other third-party collections | Mixed provenance, large size, and potentially separate redistribution constraints |
| `datasets/derived/` | Generated artifacts | Preview videos, outputs, intermediate artifacts, and annotation automation products | Produced by scripts, experiments, and review workflows | Rebuildable outputs that should not clutter version history |
| `documentation/literature_review/papers/` | Literature asset storage | Downloaded research papers and PDF references | Manually collected literature sources | Large binary reference assets, not primary project source files |

## Working Notes

- The dataset layout has been normalized to separate raw captures, extracted frames, imported data, and derived outputs.
- The annotation automation implementation is tracked in `scripts/annotation_automation/`, while its generated manifests and dataset packages are written under `datasets/derived/annotation_automation/`.
- The literature-review material currently reflects parallel workstreams associated with Angad and Arindam.
- The repository is presently stronger on documentation, datasets, and system planning than on implementation code.

## Status

At its current stage, this repository should be treated as a structured research and development workspace for the streetlight auditing system rather than as a finalized software codebase.
