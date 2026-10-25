# Camping implementation plan

**Goal:** Four original native voxel camping assets, each with large and half occupancy, four model formats, and actual paired renders.
**Architecture:** Pure `make_assets()` authors only this theme's occupancy. The parent-owned voxelkit and Blender pipeline export the models; independent `verify_theme.py` reparses all native files and freshly imports all 24 mesh files.
**Tech stack:** NumPy, VOX 150, isolated Blender 4.5, four CPU threads.
**Spec:** `../PHASE_B_WORKER_BRIEF.md`, `../BRIEF.md`, `../EXPANSION_PLAN.md`, `../_tools/API.md`; own reference `../../REF/voxel/camping/reference.png`.

## Constraints and decisions

Only `voxel/camping/**` is writable. No Git, extra agents, image generation, shared Blender scene, or cross-theme resources. Every large grid has even dimensions and longest axis 128; half dimensions are exactly divided by two, with doubled cell size. Flat opaque palette, stepped rounded forms, no scene base except building foundations. Use the already authorized finite workflow, without an additional design approval loop.

Palette direction: cream, muted olive, warm timber, clay roof, charcoal running gear, blue-gray opaque glass. Camper has a sloped windshield, entry door and stowed side awning. Cabin has round log ends, a sheltered porch and an unobstructed central route. Trailer has an open drawbar ring, A-frame tongue, support leg, one wheel pair, vent slots and controls. Shower building has three stalls, a fixed open central door, shower head and an external hot-water cylinder/plumbing, following the reference's side-mounted heater.

## Tasks

- [x] Author `build.py`, `palette.json`, and functional probes. Probe saved occupancy for porch/door clearance, wheel gap, hitch opening, vent apertures and shower access/fixtures.
- [x] Run one isolated build with the generic pipeline; preserve build log and measured process duration.
- [x] Inspect all eight primary PNGs. Only correct demonstrated defects; preserve PNG/log evidence, no old model copies.
- [x] Run independent `verify_theme.py` for eight native files and 24 fresh BLEND/GLB/FBX imports; run saved-native probes.
- [x] Write concise RESULT/STATUS, actual UTC/KST timings, capture/review evidence and SHA-256 freeze manifest. Parent reviews and commits.

## Review focus

Door and rail gaps must survive conservative reduction; hitch ring must stay open; vents must retain real apertures; tires must remain distinguishable from bodywork; paired cameras must match. Closed windows are opaque palette surfaces, and fixed doors/parts have no rigs or animation.
