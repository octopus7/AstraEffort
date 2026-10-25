# Set 02 Implementation Plan

> Follow the user-selected main + three max workers workflow.

Goal: four newly designed reference-driven rounded game assets.
Spec: BRIEF.md.
Architecture: four separate per-asset Blender authoring scripts and outputs; main owns image generation and integration.
Tech stack: built-in image_gen; private Blender 4.5.12 LTS Python; BLEND, GLB, FBX, PNG.

## Global constraints
- Main alone generates four references sequentially before modeling begins.
- Main models tracked_excavator; max workers each own one other asset.
- Keep every write inside Set02; no Git operations, live shared Blender or unrelated creative resources.
- Editable final asset geometry, component UVs and actual Blender renders; no generated scene-evidence substitutions.

## Review focus
- Required mechanical counts and functional constructions visible.
- Reference silhouettes, restrained colors and soft forms carried into real geometry.
- Exact saved/exported geometry and dimensions match after fresh-process import.
- No thin-detail bevel collapse, missing UV/materials or external file dependencies.
- Final render and file hashes remain consistent through packaging.

## Tasks
- [x] Sequentially generate and inspect four reference sheets; save prompts and timing manifest.
- [x] Main: tracked_excavator build, render, inspect and verify.
- [x] Worker 1: quadruped_surveyor build, render, inspect and verify.
- [x] Worker 2: mountain_observatory build, render, inspect and verify.
- [x] Worker 3: mine_elevator build, render, inspect and verify.
- [x] Main: independently inspect all final renders and reopen/reimport all files; prepare review index and verified ZIP.

