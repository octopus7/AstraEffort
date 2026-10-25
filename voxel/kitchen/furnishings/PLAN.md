# Kitchen furnishings implementation plan

**Goal:** Six readable household furnishings, each as native large/half VOX and actual same-camera PNG.

**Architecture:** A pure `build.make_assets()` authors colored occupancy. A local preview runner writes and reparses native files before calling the read-only generic surface/studio helpers. A separate validator checks saved native geometry, features, renders and hashes.

**Tech stack:** NumPy, native VOX 150, Blender 4.5 headless CPU Cycles, standard Python PNG tooling.

**Spec:** `../BRIEF.md` (binding). User expressly authorized direct execution without another design gate; no Git and no further agents. Only this batch directory is writable.

## Global constraints

- Exact models: sink_cabinet, kitchen_island, dish_cabinet, kitchen_cart, dish_drying_rack, knife_block.
- Large longest grid axis 128, even axes; half dimensions exactly divided by two, cell size doubled.
- Palette fixed to brief; genuine empty functional cavities and openings.
- 768 x 768 PNG, Cycles CPU, 24 samples, AgX, denoising, four threads.
- Only VOX/PNG product outputs. No scene or exchange-mesh files, image generation, permanent model floor, cross-batch geometry or reuse.

## Review focus

- Sink basin must remain genuinely empty above its floor at both sizes.
- Cabinet handles and island/cart storage must retain open air gaps.
- Dish display shelf clearances, drying-rack slots and utensil cup must survive reduction.
- Knife block unused slots and spaces between handles must survive reduction.
- Previews must be derived from reparsed files, camera-identical across sizes and visually inspected individually.

## Tasks

- [x] Author `build.py`, `palette.json`, local `preview_pipeline.py`, `validate.py` and meaningful saved-file feature probes.
- [x] Run native build/roundtrip and feature validation; remedy demonstrated failures before rendering.
- [x] Render all twelve variants from reopened VOX without scene or mesh export; capture real timing/settings/hashes.
- [x] Inspect all twelve actual images and create labeled `overview_half.png` from those images.
- [x] Run full saved-file verification, freeze file hashes, write real `RESULT.md`, `STATUS.json` and capture evidence; provide completion paths.

## Decisions and ledger

- Physical scales are per-object: sink 1.28 m grid width, island 1.408 m, hutch 1.792 m height, cart 0.9984 m height, rack 0.5888 m width, knife block 0.4096 m height.
- No half postprocessing is planned. Thin parts and empty gaps are deliberately wide enough for native 2x reduction.
- Standard Blender Python contains NumPy but no Pillow. Contact-sheet assembly will use available local image support without package installation.
- Start record is the first actual UTC clock reading after brief/tool preflight. No fabricated earlier timestamp is used.
- Native validation (2026-10-25 05:31:17 UTC): twelve files, 48 feature probes passed. A probe initially straddled half-cell boundaries; aligned it to a complete cell. The initial raised facade entered handle clearance; recessed the facade to preserve at least four large cells of grip clearance. Both failures were observed before the correction.
- A separate six-neighbor component check found actual support gaps in four models: the island towel-rail mounts, hutch bowl, rack plates and inserted knives. Corrected only these observed support defects: mounts now meet side posts, bowl rests on its shelf, a rack crossbar supports plates, and hidden knife blades reach slot floors. `logs/support_check_initial.json` records the failing native evidence. Those four pairs will be rerendered; unchanged pairs are retained.
