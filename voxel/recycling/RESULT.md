# Recycling — ready for review

Four newly authored models and eight native size variants are frozen under `assets/<asset>/<large|half>/`. Each variant contains VOX 150, BLEND, GLB, FBX, actual 768px `preview.png`, and hashed metadata. Pure source is `build.py`; palette and provenance are in `palette.json` and `source_manifest.json`.

| Asset | Large grid | Half grid | Meters/cell large / half |
|---|---|---|---|
| collection_truck | 74 × 128 × 88 | 37 × 64 × 44 | 0.055 / 0.110 |
| sorting_machine | 128 × 102 × 96 | 64 × 51 × 48 | 0.045 / 0.090 |
| compactor | 102 × 84 × 128 | 51 × 42 × 64 | 0.045 / 0.090 |
| recycling_center | 128 × 96 × 90 | 64 × 48 × 45 | 0.075 / 0.150 |

All large axes are even, with longest axis 128; half axes are exactly divided by two, longest 64, with doubled cell size and equal physical grid extent. Native occupancy is authoritative. Same-camera Cycles CPU previews use four threads and 24 samples; `capture_manifest.json` contains camera settings, actual capture times and hashes.

Fresh generic verification passed all eight saved VOX files and **24 BLEND/GLB/FBX imports**, including palette/grid/hash/bounds checks, exact exposed surfaces, outward normals, grid alignment and valid materials. All **20 saved-native functional checks** passed: rear hopper cavity/access; both sorter funnels and lateral throats, belt continuity and sensor clearance; open compactor chamber, ram/platen and strapped bale; hollow receiving hall and three separate open bins. All **eight primary previews were opened and inspected**. One build, zero geometry-fix passes.

Start: **2026-10-23T16:52:06.820630+00:00 UTC / 2026-10-24T01:52:06.820630+09:00 KST**. Finish: **2026-10-23T17:06:53.126617+00:00 UTC / 2026-10-24T02:06:53.126617+09:00 KST**. Wall: **886.306s**. Build/render process: **89.027s**. Fresh format verification process: **6.282s**. Native function checks: **0.508s**. Queue wait and worker image generation: **0s**.

Limitations: static models without rig, animation, collision, LOD chain or engine integration; opaque glazing; no machine simulation or safety certification. The truck's loading end faces -Y and its cab faces +Y to expose the hopper in the primary preview. Receiving hall is hollow; annex interior stops at bay depth. Small ribs/tread/trim simplify at half resolution. Existing ValveSource addon handler emitted a missing scene.vs warning while importing. The generic verifier completed with no validation errors and exit 0; no addon was modified.

Reference: `REF/voxel/recycling/reference.png` supplied by main, used as design input only. No other-theme creative resources, live Blender scene, installations, Git actions or extra agents were used. Evidence: `validation_export.json`, `validation_function.json`, `build_validation.json`, `visual_review.json`, `capture_manifest.json`, process logs/timing, and `frozen_manifest.json`. Waiting for parent review; no further edits planned.
