# Set 01 Implementation Plan

> For agentic workers: use scoped parallel artifact production; user explicitly selected main + three max workers.

Goal: deliver four reference-driven editable game-art models.
Architecture: isolated per-asset Blender scripts and outputs; main owns reference generation and integration.
Tech stack: built-in image generation, Blender headless Python, PNG, BLEND, GLB, FBX.
Spec: BRIEF.md.

## Global constraints
- Four images are generated sequentially by the main agent before modeling begins.
- Main models cargo_rover; max workers model service_mech, arched_workshop, water_station.
- Writes stay inside REF/Set01 and Blender/Set01; no Git operations or existing creative assets.
- No shared live Blender mutation; separate headless processes.

## Review focus
- All four final references really exist and are individually inspected.
- Each editable model and both exports load, contain non-empty finite geometry and correct named materials.
- Objects visibly resemble their own reference and required functional pieces are present.
- No missing external images; UV maps are present; no studio geometry exported.
- Renders are actual Blender renders and not substituted image-generation evidence.

## Tasks
- [x] Generate and inspect cargo_rover, service_mech, arched_workshop, water_station reference sheets in order; persist prompts and timestamps.
- [x] Main: build cargo_rover; export and render; inspect and correct.
- [x] Worker 1: build service_mech; export and render; inspect and correct.
- [x] Worker 2: build arched_workshop; export and render; inspect and correct.
- [x] Worker 3: build water_station; export and render; inspect and correct.
- [x] Reopen final files, validate outputs, review actual renders and create an actual-render review index and delivery report.

