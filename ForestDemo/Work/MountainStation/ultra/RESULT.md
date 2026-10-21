# MountainStation / ultra — Alder Pass

Ready for supervisor review. The independent 100 × 100 m scene, owned assets, saved map, four actual UE renders and validation records are delivered. No Git index or commit operations were performed.

## Time record

| Event | UTC | KST |
|---|---|---|
| Original work start | 2026-10-21T12:27:25+00:00 | 2026-10-21T21:27:25+09:00 |
| First submitted ready (retained) | 2026-10-21T13:44:03.774679+00:00 | 2026-10-21T22:44:03.774679+09:00 |

First-delivery elapsed wall time: **4598.775 seconds**. Recorded UE mutex/priority wait: **1304.602434 seconds**. Recorded UE process execution: **572.378509 seconds**. Wall time includes CPU authoring, reviews, tool debugging, queue waiting, the supervisor's temporary registration hold while updating the queue runner, and reporting. The registration hold occurred before queue entry and is not counted as mutex wait. Queue wait is not active scene-production time. No migration was required for this MountainStation asset root.

| Timing record | Wait seconds | Execution seconds | Process exit |
|---|---:|---:|---:|
| timing_build.json | 0.023901 | 0.935465 | 0 |
| timing_build_authorized.json | 302.568018 | 18.626278 | -1 |
| timing_review_01.json | 358.962289 | 72.698543 | 0 |
| timing_review_02.json | 261.821998 | 24.711447 | 0 |
| timing_review_03.json | 251.745601 | 16.306753 | 0 |
| timing_review_04.json | 109.127247 | 32.318328 | 0 |
| timing_review_05.json | 0.017568 | 121.371605 | 0 |
| timing_review_06.json | 20.053175 | 127.448010 | 0 |
| timing_review_07.json | 0.015123 | 125.285334 | 0 |
| timing_runtime_final_01.json | 0.267514 | 32.676746 | 0 |

`timing_build.json` is an unsuccessful sandbox launch with no engine log; its small launcher time remains in the totals. Earlier zero process exits do not imply successful scene checks: Python failures are preserved under Diagnostics. The first authorized build failed on a Python API field. Subsequent iterations resolved level replacement, capture lifetime/projection, collision initialization/profiles, ramp/path/fence obstruction, lighting and lettering. All time remains counted.

The supervisor runtime supplement began at 2026-10-21T12:47:13Z and ended at 2026-10-21T13:43:19.376028+00:00, spanning 3366.376 seconds. This interval overlaps production and retries; it cannot be treated as exclusive supervision overhead. The final actual PIE test lasted 8.033 seconds; final four-view capture sequence lasted 48.247 seconds. Detailed timestamps are in `supplement_timing.json` and the original timing files.

## Delivered paths and scene

- `Content/Maps/MountainStation_ultra.umap` — `/Game/Maps/MountainStation_ultra`.
- `Content/MountainStation/ultra/` — 75 assets under the sole permitted project asset root.
- `Work/MountainStation/ultra/` — source, scripts, evidence, this report and Screenshots.
- `SourceArt/AlderPass.blend` plus 47 FBX exports are the authoritative final geometry. Historical refinement scripts are not idempotent; follow `REPRODUCTION.md`.

The scene combines a teal timber station, terracotta roof/canopy, glazed window frames, clock/name/number signs, benches, luggage and planting; a curved masonry platform and accessible graded ramp; curved rails with sleepers/fasteners/ballast; a masonry tunnel portal and short lined dark interior; freight shed, crates, sacks and handcart; contour-following loop trail, fences, conifers, shrubs and rounded rock formations. Terrain and props are original background-Blender geometry with a restrained palette. No generated scene imagery or external artistic assets were used.

Final source: 47 semantic mesh groups, 163305 vertices and 154689 source polygons. These are source geometry counts, not runtime performance measurements. Unreal has 47 owned mesh assets and 28 owned materials, with dynamic key/fill/skylight illumination. Terrain is mesh-based; there is no Landscape sculpt asset.

## Validation evidence

- Saved private map reloaded: 56 actors; terrain XY extent is exactly 5,000 cm each side (100 × 100 m).
- Recursive dependency audit visited 76 packages and found zero foreign `/Game` dependencies. Only `/Game/MountainStation/ultra`, its own map, baseline script classes and engine resources are referenced. See `validation.json`.
- No World Partition external actor/object packages or map BuiltData. The scene was authored with a non-partitioned new level and force-no-precomputed-lighting; `publication_manifest.json` records the package check.
- Ten downward collision samples have no initial overlap. Ramp/platform join differs by approximately 0.862 cm. The ramp has a 1334.166 cm plan run, 112 cm rise and approximately 4.799° slope.
- Actual PIE game world created a PlayerController and DefaultPawn, possessed correctly at the arrival PlayerStart. Eight successive swept moves along the ground/ramp/platform reached their targets; the original side-sweep criterion was insufficient because it accepted an unchanged position with no movement HitResult. That original platform-blocking claim is withdrawn and superseded by the verified post-review supplement below. This is a short DefaultPawn sweep test, not full character locomotion QA.
- One original baseline ScreenDebugLogger was present. A transient Python subclass overriding only ReceiveBeginPlay proved dispatch through the unchanged native BeginPlay lifecycle. Native implementation still calls its existing green `Hello` message. Comparison renders intentionally omit debug overlays; no screenshot claim is made for visible Hello pixels. No probe actor/class is saved in the delivered map.
- PIE ended normally. Map SHA-256 was identical before/after the runtime-only supplement. The private editor exited before publication. Every copied final asset and map was SHA-256 matched to the validated private files.

Evidence: `validation.json`, `runtime_validation.json` (original evidence retained; platform-blocking criterion superseded), `native_baseline_evidence.json`, `collision_readiness.json`, `visual_inspection.json`, `publication_manifest.json`, `source_summary.json`, `timing_summary.json`, and `Logs/`.

## Actual renders

All four images were rendered by UE 5.7 SceneCapture2D with a real RHI at 1920 × 1080, High scalability and 100% screen percentage. The author opened and inspected every final image; `visual_inspection.json` binds observations to SHA-256 values. `Screenshots/capture_manifest.json` contains camera, exposure, render settings and actual capture timestamps.

Overview: camera (12000, -12000, 16000) cm aimed at origin, orthographic width 20000 cm. Top-down: (0, 0, 20000) cm, pitch -90°, yaw/roll 0°, same width. Detail cameras have 70° horizontal FOV at 170 cm above sampled local ground. Detail positions differ from other authors' views and should be compared accordingly.

![Overview](D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/Screenshots/overview.png)
![Top down](D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/Screenshots/top_down.png)
![Platform](D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/Screenshots/platform.png)
![Tracks and tunnel](D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/Screenshots/tracks.png)

## Limitations and references

Station and freight structures are exterior shells; the tunnel is a short visual interior with a dark backing. No train movement, railway simulation, custom character movement, NavMesh, full traversal playthrough, packaged-game test or frame-rate benchmark is claimed. Some path seams are angular and distant areas are sparse. The fixed overview sees the tunnel obliquely; the tracks view supplies its frontal evidence. Deep canopy/tunnel shadows remain. Palette materials use no image textures; a future texture/UV pass is separate work.

Original art was authored independently in a background Blender process. Shared Blender MCP, other themes/efforts' resources, shared project saving, shared Source/Config changes and Git mutations were not used. Only read-only baseline ForestDemo native classes and Engine built-ins are shared. Installed UE headers and the official technical API pages linked in `REPRODUCTION.md` informed tooling. No external artistic references.


## Post-review collision evidence correction

This supplement completed at **2026-10-21T14:37:37.823151+00:00 UTC / 2026-10-21T23:37:37.823151+09:00 KST**. First-ready remains **2026-10-21T13:44:03.774679+00:00**; its STATUS, RESULT, runtime evidence and package manifest are preserved in `BlockingSupplement/Before/`. The previous eight ramp moves, native BeginPlay probe and normal PIE shutdown are retained. The original platform claim accepted `actual == start` and a `None` move result; it did not exclude initial overlap and is not sufficient evidence of platform blocking.

The new test used a fresh private UE process and the actually possessed DefaultPawn, with its real SphereComponent radius **35 cm**, object channel **ECC_PAWN**, and **Pawn** collision profile. At every test start, an identical sphere/profile query reported no blocking overlap. The Pawn then moved a positive distance and stopped short of the requested target. Its own returned HitResult has **blocking_hit=true**, **initial_overlap=false**, and **0 < time < 1** for every test. Actor, component, static mesh, contact point/normal, requested position and actual end position are recorded in `BlockingSupplement/validation.json`. A second identical sphere/profile trace corroborates the exact same actor/component; the movement result remains the primary evidence.

| Actual Pawn sweep | Start cm | Requested target cm | Actual end cm | Moved cm | Hit static mesh |
|---|---|---|---|---:|---|
| platform_downward | [300.0, -300.0, 800.0] | [300.0, -300.0, 40.0] | [300.0, -300.0, 188.7601] | 611.2399 | SM_Platform |
| terrain_section_0 | [333.3333333333333, -3033.3333333333335, 421.82663853963214] | [333.3333333333333, -3033.3333333333335, -78.17336146036784] | [333.3333, -3033.3333, 58.3372] | 363.4894 | SM_Terrain |
| platform_front_side | [500.0, -800.0, 170.0] | [500.0, -400.0, 170.0] | [500.0, -636.5772, 170.0] | 163.4228 | SM_PlatformCoping |

HitResult tuple indices were checked against the installed UE 5.7 `GameplayStatics.h` `BreakHitResult` declaration (line 1079), and `Actor.cpp` `K2_SetActorLocation` (line 6654). The live Python documentation states that set_actor_location returns a HitResult only when movement occurred. `KismetSystemLibrary.cpp` `SphereTraceSingleByProfile` constructs a sphere and calls the world's profile-based sweep. Exact mapping and live API documentation are saved with the test.

### Terrain section audit

The actual final imported Terrain LOD0 has **1 section**, containing **20000 triangles**, with collision enabled and material slot **0**. There are **0 slot-1 triangles**. The final presentation refinement changed all terrain faces to Meadow slot 0; `build_art.py` is historical initial-generation source, not the final material assignment. The previous `[true,false]` readiness record came from blindly querying indices 0 and 1; UE returns false for the invalid section-1 index. It was not evidence of a disabled existing terrain section. `run_review.py` now enumerates the actual section count.

The downward Pawn test uses the centroid of actual imported LOD0 section 0, triangle 10386, material slot 0, with barycentric weights (1/3,1/3,1/3): [333.3333333333333, -3033.3333333333335, 21.82663853963216] cm. Its three world-space vertices and section-local vertex indices are recorded. These were read from UE's actual LOD0 position/index buffers through ProceduralMeshLibrary and transformed by the placed Terrain actor. There is no slot-1 interior point to test because that final section has no faces. No collision package change was required.

### Preservation and separate timing

All **76 published map/asset files**, all corresponding private map/asset files, and the **four final PNGs** match their original first-delivery SHA-256 values. `BlockingSupplement/hashes_after.json` contains the per-file proof. No art, lighting, camera, collision settings or package saves were made, and no assets were republished. `BlockingSupplement/editor_closed.json` confirms the private process was closed.

Supplement start: 2026-10-21T13:52:25.1127606+00:00 UTC / 2026-10-21T22:52:25.112760+09:00 KST. Finish: 2026-10-21T14:37:37.823151+00:00 UTC / 2026-10-21T23:37:37.823151+09:00 KST. Separate elapsed wall: **2712.710 s**; UE queue wait: **1889.312337 s**; UE execution: **162.297712 s**. Original first-delivery timing above is unchanged.

Four unsuccessful supplement attempts are retained: the first exposed an unavailable Python conversion API; the second rejected a candidate overlapping the rail; the third rejected ballast initial overlap during the intended trace direction; the fourth produced a valid actual Pawn blocking hit but hit a lamp instead of the intended platform. A short probe moving upward out of an overlap had missed the third case, so the final probe uses the intended movement direction. Final candidate paths were queried against actual scene collision, with every query recorded, to select clear routes to the intended meshes before testing actual Pawn movement. The final side start is above the rail/ballast and its concrete hit is `SM_PlatformCoping`, identified separately from the platform slab. All attempts remain included in the separate timing. See `BlockingSupplement/timing.json`, `attempt01_validation.json` through `attempt04_validation.json`, `validation.json` and `Logs/blocking_supplement_*.log`. The ordinary runtime validator uses the same strict non-overlap, positive-motion and actual-hit checks for future runs.
