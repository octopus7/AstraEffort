# Fire rescue — ready for review

Four original models and eight native resolution variants are frozen under `voxel/fire_rescue`. Each `assets/ASSET/{large,half}/` contains VOX 150, BLEND, GLB, FBX, `metadata.json` and the actual 768×768 `preview.png`. Source: `build.py`; opaque palette: `palette.json`; camera/render evidence: `capture_manifest.json` and `visual_review.json`.

| Asset | Large → half grid | Occupied voxels large / half |
|---|---|---|
| fire_engine | 64×128×76 → 32×64×38 | 248806 / 34348 |
| rescue_robot | 96×128×108 → 48×64×54 | 202182 / 29032 |
| fire_station | 128×96×120 → 64×48×60 | 378151 / 55295 |
| rescue_helicopter | 128×128×84 → 64×64×42 | 75951 / 11545 |

All half axes are exactly halved; cell size doubles and physical grid extents remain equal. Shapes are native stepped voxel boundaries with flat palette materials. The station has two open bays and its own structural floor. The other three assets have no permanent base.

Validation: `validation_export.json` passes all eight independent VOX reparses and 24 fresh BLEND/GLB/FBX inspections (occupancy, palette, file hashes, bounds, triangle count, exposed surface area, outward boundary orientation, material indices and grid alignment). `validation_native_features.json` passes all 46 checks, including both station entry passages, ladder opening, gripper gap, cabin loading opening, skid clearance, hook throat and cable continuity. Final validation process exit code: **0**. All eight final primary previews were visually inspected; six unchanged preview hashes match the initially verified files.

One demonstrated correction: reduction erased the half truck's shutter lines and hose-turn separation. A documented native half-grid postprocess restores those details; only the engine pair was rebuilt and re-inspected. `fix_evidence/` preserves the observed first half render and initial native-check report. The initial cable probe included the amber hook connection while requiring black cable color; its corrected span now tests the actual black cable only.

Start: **2026-10-23T16:33:57+00:00 UTC / 2026-10-24T01:33:57+09:00 KST**. Finish: **2026-10-23T16:54:21.409042+00:00 UTC / 2026-10-24T01:54:21.409042+09:00 KST**. Wall: **1224.409 s**. Full build **86.409 s**; necessary engine fix **23.134 s**; first/final fresh validation **9.923 / 13.053 s**; final native probes **0.412 s**. See `timing_summary.json` and process logs. One prior startup aborted on an installed Blender load handler; successful isolated runs use `--factory-startup`, four threads and `--python-exit-code 1`. Initial PowerShell exit-code capture was null; final subprocess records capture exit 0. No worker image generation.

Limitations: static models, opaque stylized glazing, no rig, animation, simulation, collision, LOD chain or engine integration. Smaller bolt/roof detail simplifies at half resolution. No interactive GUI checks were claimed. Design reference: parent-supplied `REF/voxel/fire_rescue/reference.png`, viewed as input only; all scene evidence is actual Blender rendering. No other-theme creative resources were inspected or reused.
