# Fire rescue voxel implementation plan

**Goal:** Deliver four original fire/rescue models, each in native 128-axis and 64-axis grids and four requested formats.
**Architecture:** Pure `make_assets()` uses the parent voxel grid primitives; parent export and independent import verification remain unchanged. Native occupancy is authoritative.
**Tech stack:** Python, NumPy, isolated Blender 4.5, parent voxelkit/blender_pipeline/verify_theme.
**Spec:** `../PHASE_B_WORKER_BRIEF.md`, `../EXPANSION_PLAN.md`, `../BRIEF.md`, `../_tools/API.md`, assigned reference.

- [x] Author `build.py` and `palette.json`: red/ivory machinery with purposeful rounded voxel silhouettes; fire engine shutters, hose reel and ladder; robot tracks, articulated gripper and single camera pod; station with two genuinely open bays; helicopter cockpit, rotor, skids and outboard winch.
- [x] Run one isolated four-thread background build with `--python-exit-code 1`; save process timing and logs.
- [x] Inspect the eight primary rendered previews. One necessary engine-pair rerun restores half-grid shutter/hose detail; no optional views.
- [x] Reparse saved native grids for functional openings and mechanisms; run the generic fresh BLEND/GLB/FBX verifier in a separate process.
- [x] Write concise evidence, exact UTC/KST/wall/process timings, limitations and `ready_for_review` status; freeze submission.

All writes remain under `voxel/fire_rescue`. No generated scene imagery, other-theme reads/reuse, shared Blender, Git, installations or extra agents. Half grids double cell size and preserve physical grid extent. Source colors are opaque. Flat voxel faces remain unsmoothed. The station slab is part of its building; movable assets have no permanent floor.
