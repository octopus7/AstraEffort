# Camping result

Four original models are **ready for coordinating review**: `camper_van`, `log_cabin`, `generator_trailer`, and `shower_block`. Each has native VOX, BLEND, GLB, FBX, metadata and an actual 768×768 Cycles preview under `assets/<asset>/{large,half}/`.

Recorded authoring start: 2026-10-25T05:03:03+00:00 / 2026-10-25T14:03:03+09:00 KST. Finish: 2026-10-25T05:14:38.406595+00:00 / 2026-10-25T14:14:38.406595+09:00 KST. Elapsed wall: **695.407 s**. One isolated four-thread build: **88.303 s** (pipeline 87.522 s); independent verifier: **7.091 s** (internal 6.467 s); saved-native probes: **0.702 s**. No correction rebuilds or optional renders.

The cream/olive camper has a sloped windshield, entry and stowed awning. The warm log cabin has rounded log ends, a stepped clay roof and clear porch access. The trailer has an open ring coupling, A-frame, support foot, wheel pair, real ventilation slots and controls. The three-stall shower building has an open central door, shower fixture and side-mounted heater/plumbing. Building foundations are structural; there is no campsite base.

**Validation:** All eight native roundtrips passed. Independent `validation_export.json` reports 4 models, 8 variants, 24 fresh BLEND/GLB/FBX imports, and no errors; verifier exit code is 0. Bounds, palette assignment, exposed outward surfaces, grid alignment, triangle counts, finite geometry and geometry-only exchange exports passed. `validation_functional.json` records 34 saved-native probes for access gaps, hitch opening, ventilation and fixtures. All eight primary previews were inspected and four matching-camera pairs checked (`visual_review.json`, `capture_manifest.json`).

Every large grid has even axes and longest axis 128; half grids divide all axes by two, with 0.10 m cells versus 0.05 m large cells and unchanged physical grid extents. Reduction is conservative native occupancy with no manual half corrections. `build.py`, `palette.json`, `source_manifest.json`, logs, validation records and `frozen_files.json` preserve reproducibility and evidence.

**Limits:** Opaque palette windows, static parts/doors, no furnished interiors, animation, rig, collision, simulation or engine integration. Half reduction simplifies small dividers/details and may expand boundaries by one large cell. The shower head is partly occluded in the primary view and is checked in native occupancy. The original build wrapper lost the child exit code (null preserved in `build_timing.json`); pipeline completion and independent verification establish the finished output. The verifier captured exit 0.

**Reference:** Only `REF/voxel/camping/reference.png`, supplied by the parent, informed this original theme. No external reference downloads, image generation, cross-theme assets, shared scene changes or Git actions. Main performs final independent review and commit.
