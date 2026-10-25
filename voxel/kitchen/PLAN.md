# Kitchen native voxel and preview implementation plan

> For agentic workers: apply the subagent-driven workflow within the user's explicit constraints: exactly three simultaneous Astra/max workers, no additional reviewers, main coordination only. Do not create Git worktrees or commits; isolated output directories provide asset ownership.

**Goal:** Produce 20 kitchen models as 40 native VOX variants and 40 real previews.

**Architecture:** Three independently owned batch directories share a read-only native voxel/render API and the common written palette. All geometry, rendering and verification occur in workers. Main only maintains dispatch, status and delivery pointers.

**Tech Stack:** NumPy native occupancy, MagicaVoxel VOX150, installed Blender 4.5 headless CPU.

**Spec:** voxel/kitchen/BRIEF.md. User's current narrowed VOX+PNG scope takes precedence over the original theme export pipeline.

## Global constraints

- Exact 20 slugs, output scope, palette and sizes in BRIEF.md; large longest 128 and half axes /2, equal physical grid extents.
- Exactly three gpt-6-astra/max workers. Fast not exposed; do not claim it.
- Four CPU threads per headless Blender job. No Git/index operations, installations, shared tool writes or cross-theme creative reads.
- Main coordination only; workers create and inspect every screenshot/preview.
- No GLB/FBX/BLEND or engine integration outputs.

## Review focus

- Half-size structural gaps and handles remain readable: saved-native feature probes plus visual inspection by each batch.
- Serialized source and preview match: reparse saved VOX before rendering and record hashes.
- Physical sizes and same-camera resolution comparison are correct: grid/cell-size metadata and camera comparisons.
- No unwanted mesh outputs: file inventory and worker scope validation.
- All 20 items have both sizes: independent cross-review inventory and metadata after each batch freezes.

## Tasks

- [x] Worker appliances: author seven assigned assets, generate/reparse both native sizes, render all fourteen previews, verify and inspect them, assemble own half overview, write evidence and freeze hashes.
- [x] Worker furnishings: same lifecycle for six assets and twelve previews.
- [x] Worker countertop: same lifecycle for seven assets and fourteen previews.
- [x] Reuse the three existing agents for read-only circular review (appliances reviews furnishings; furnishings reviews countertop; countertop reviews appliances). Each reviewer reports spec and visual quality verdicts in its own root; corrections return to original owner.
- [x] Delegate final whole-theme contact sheet and file inventory to one existing worker, using only finished preview/data metadata. Main writes final coordination status and delivery links.

No new model generation is needed in main. No commits or archive work requested in this turn.
