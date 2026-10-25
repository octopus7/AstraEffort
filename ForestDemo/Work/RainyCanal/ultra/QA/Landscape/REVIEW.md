# Landscape FBX independent import audit

Result: **pass_source_fbx_checks**. Imported 13 FBXs in clean Blender 5.2.0 LTS scenes. Actual UTC 2026-10-22T15:45:40.402873+00:00 to 2026-10-22T15:45:41.737550+00:00 (1.335 seconds).

| Mesh | Triangles | UV layers | World Z min / max (m) | UV1 px/m min / max | UV0 cell margin px |
|---|---:|---:|---:|---:|---:|
| SM_BankWest | 2 | 2 | 0.0000 / 0.0000 | 128.0000 / 128.0000 | 2.1000 |
| SM_BankEast | 2 | 2 | 0.0000 / 0.0000 | 128.0000 / 128.0000 | 2.1000 |
| SM_CanalWater | 2 | 2 | 0.0000 / 0.0000 | 128.0000 / 128.0000 | 2.1000 |
| SM_CanalBed | 12 | 2 | -1.9500 / -1.6500 | 128.0000 / 128.0000 | 2.1000 |
| SM_QuayWall | 44 | 2 | -2.0000 / 0.1000 | 128.0000 / 128.0000 | 2.1000 |
| SM_QuayCap | 108 | 2 | -0.0000 / 0.2000 | 128.0000 / 128.0000 | 2.1000 |
| SM_Dock | 108 | 2 | -0.2800 / 0.0000 | 127.9999 / 128.0000 | 2.1000 |
| SM_DockStep | 28 | 2 | -0.4200 / 0.1600 | 128.0000 / 128.0000 | 2.1000 |
| SM_Puddle | 48 | 2 | 0.0000 / 0.0000 | 128.0000 / 128.0000 | 2.1000 |
| SM_RainVolume | 7736 | 2 | -0.7000 / 0.6298 | 127.9996 / 128.0026 | 1.3963 |
| SM_CanalTree | 508 | 2 | 0.0000 / 5.2330 | 128.0000 / 128.0000 | 2.1000 |
| SM_Shrub | 60 | 2 | -0.0300 / 0.9300 | 128.0000 / 128.0000 | 2.1000 |
| SM_GrassFringe | 11 | 2 | 0.0000 / 0.4894 | 128.0000 / 128.0000 | 2.1000 |

## Findings

No failed source-FBX checks. Every mesh retained two UV layers, nondegenerate geometry and UV triangles, a unique UV0 atlas with disjoint triangle bounding boxes, and UV1 density within 1% of 128 px/m. World-space transformed bounds match local geometry plus authored object position to 0.1 mm.


Rain colors: 3868 connected strips pair into 1934 crossed drops. Each strip retains constant red phase (maximum spread 0.0); green preserves [4] values per strip. B=0 and A=1 ranges are in the JSON record.

## Observations and limits

- Final current-hash audit reimports all 13 FBXs, then opens current source.blend read-only to compare all 13 geometry counts and transformed bounds. No creative source is executed or saved.
- SM_QuayWall is now the 44-triangle closed notched wall described by wall_notch.json, superseding its original manifest entry. Actual ray intersections confirm top Z=-0.12 m across design Y=26..30 m, linear transitions across 25.8..26 and 30..30.2, top +0.1 m elsewhere and bottom -2 m throughout. Nominal clearance to a Z=0 deck is 0.12 m; final deck placement/collision is a UE check.
- SM_DockStep remains the 28-triangle closed continuous Timber ramp described by dock_ramp.json, superseding its original manifest entry. Local Z is -0.42..+0.16 m. Intended actor placement (6.4,1,0) yields top endpoints (x=5,z=-0.3) and (x=8.2,z=0), with +0.16 m crest. The prior 0.06 m clearance remains relative to the normal +0.1 m quay top; the new wall notch is at a separate design-Y range.
- UV0 is a unique per-triangle atlas. Its density varies with physical triangle size by design; texture density is on UV1.
- UV1 is physically isometric at 128 px/m per triangle and intentionally overlaps/repeats. Each triangle has a separate local origin and orientation, so directional textures can show discontinuities across triangle boundaries. Use the intended world-coherent material sampling for broad architectural courses.
- UV0 inter-island cell margin is 2.1 px for ordinary meshes and approximately 1.396 px for RainVolume at 1024. Rain uses dynamic vertex-driven translucency; there is no baked-lightmap validation in this audit.
- CanalWater FBX is a zero-height source plane at Z=0. The parent scene must place its waterline at the desired canal elevation.
- Shrub source extends about 0.03 m below its origin, suitable for slight ground embedding; final placement is not verified here.
- No UE import, mesh bounds in UE, materials, collision, WPO or runtime rendering were checked.

Full bounds, density percentiles, padding, rain color data, hashes and timing are in `landscape_qa.json`. The audit modifies no source asset and launches no UE session.
