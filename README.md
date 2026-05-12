# RBCCPS Directory

This workspace currently contains documentation assets and local dataset storage for streetlight-auditing research.

## Git Status

This folder does not appear to be initialized as a Git repository yet, but the ignore rules below are prepared for when Git is enabled.

## Ignored Folders

The following folders are listed in `.gitignore` because they contain large binary assets, regenerated data, or imported material that should usually stay out of version control.

| Path | Category | Primary Contents | Source / Provenance | Why Ignored |
| --- | --- | --- | --- | --- |
| `datasets/raw/` | Raw capture storage | Original night-drive video clips (`.mp4`) | Phone or vehicle-mounted capture sessions | Large binary inputs; should be preserved locally, not versioned |
| `datasets/extracted_frames/` | Derived dataset storage | Frame batches extracted from raw videos (`.jpg`) | Generated from raw video during preprocessing | Regenerable from source videos; very large image volume |
| `datasets/imported/` | External dataset storage | Imported third-party or platform-exported datasets | Roboflow exports and other external collections | Mixed provenance, large size, and often redistributable only under separate terms |
| `datasets/derived/` | Generated artifacts | Preview videos, quick outputs, intermediate renderings | Produced by scripts, experiments, or manual review flows | Rebuildable outputs that should not clutter version history |
| `documentation/literature_review/papers/` | Literature asset storage | Downloaded research papers and PDF references | Manually downloaded from bibliography sources | Large binary reference library; not core source material |

## Notes

- Dataset layout details are documented in [datasets/README.md](datasets/README.md).
- The ignored folders are intentionally broad. If you later want to version manifests, metadata, or small sample assets from those trees, add explicit negation rules to `.gitignore`.
