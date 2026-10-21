# MountainStation / medium — Alder Pass

Status: ready_for_review after the actual Pawn movement correction below. Independently authored by this chat; no subagents, borrowed scene resources, Git index changes or commits.

## Actual timing

- Start UTC: 2026-10-21T12:27:10.0000000+00:00; KST: 2026-10-21T21:27:10.0000000+09:00.
- Finish / first ready UTC: 2026-10-21T13:05:26.4557133+00:00; KST: 2026-10-21T22:05:26.4557133+09:00.
- Total wall time: 2296.456 seconds. Start was never reset.
- Named mutex wait total: 1006.402 seconds. UE process execution total: 506.29 seconds, including failed/repeated attempts.
- Final reload/dependency/editor collision audit: 0.113 seconds.
- Final four-image capture interval: 112.838 seconds. Final PIE runtime check: 9.025 seconds.
- Supplement requested during work: 2026-10-21 12:46:02 UTC / 21:46:02 KST. See supplement_timing.json for completion and separate wait/execution records. Combined sessions also include necessary visual refinement and capture work.
- Clock correction: an intermediate STATUS update incorrectly added about 9 hours because ConvertFrom-Json converted UTC to DateTime before string parsing. Re-read with -DateKind String and calculate DateTimeOffset.UtcNow minus the original UTC timestamp. Only KST display uses ToOffset(+09:00). The corrected elapsed value is authoritative.

| Session | Mutex wait seconds | UE execution seconds | Exit |
|---|---:|---:|---:|
| build_timing | 0.008 | 1.093 | 0 |
| build2_timing | 151.459 | 17.556 | 3 |
| build3_timing | 182.552 | 71.113 | 0 |
| capture1_timing | 218.894 | 126.658 | 0 |
| final1_timing | 174.021 | 135.922 | 0 |
| refine1_timing | 279.468 | 153.948 | 0 |

The first sandbox launch exited without creating a UE log and is not counted as validation success. The commandlet FBX import failed a Slate assertion. Normal offscreen editor execution resolved this. Initial captures exposed FBX handedness, overlapping terrain/base geometry, and positional Rotator argument errors; those were corrected before delivery. Initial actor-movement validation was retried with a re-entry guard and independent runtime sphere sweeps. These attempts remain included in total wall time.

## Delivered files

- Level: ForestDemo/Content/Maps/MountainStation_medium.umap.
- Assets: ForestDemo/Content/MountainStation/medium/ (one authored combined scene mesh, twenty materials).
- 22 published packages including the map; source and destination SHA-256 match for every package in delivery_manifest.json.
- Source: AlderPass.blend retains individual authored objects; AlderPass.fbx is the handedness-corrected export. Reproduce art with build_art.py then refine_art.py. UE scripts and the exact palette/route specification are in this Work folder.
- Screenshots/overview.png, top_down.png, platform.png, tracks.png; capture_manifest.json and image_validation.json.
- validation.json, collision_validation.json, validation_log.txt; runtime_validation.json, runtime_log.txt, runtime_hello.png.
- No shared Source/Config/Plugins/uproject or other maps were modified. The private editor exited before publishing. Scratch Content contained no external actor/object packages or BuiltData assets.

## Scene and validation

100 × 100 m sculpted terrain, a cream-and-teal small station, 40 m curving platform with ramp access, continuous curved rails/sleepers/ballast, a short horseshoe tunnel, covered freight deck, a hillside walking route, benches, station signs, analog clock, lanterns, luggage, strapped crates, fencing, conifers and rock outcrops. Meshes and colors were independently authored; no external art was downloaded.

The final map was saved and reloaded. The recursive Asset Registry audit visited 22 packages with zero foreign /Game dependencies. Only /Game/MountainStation/medium and the owned map occur; /Engine and baseline /Script/ForestDemo are permitted references. Geometry is non-World-Partition, lighting is dynamic, and the backdrop uses an Engine basic sphere with an owned material. Lighting-only polish was saved/reloaded after runtime checks and did not alter geometry or package references.

Ground collision is complex-as-simple, double-sided, with mesh-section collision enabled. Reloaded editor traces hit the entry at 7.82 cm, ramp midpoint at 36.5 cm, platform at 72 cm, and a sleeper at 32 cm. Real PIE created and possessed an Engine DefaultPawn at (-1900, -1150, 120) cm. Runtime traces hit the same authored surfaces; 35 cm sphere sweeps verified the clear approach corridor and blocking ramp/platform. PIE ended normally. The original native ScreenDebugLogger was present in the running game world, and green Hello was visually confirmed in runtime_hello.png.

All four final 1920 × 1080 UE SceneCapture images were directly inspected. High scalability (sg.* 2), screen percentage 100, final-color LDR and manual exposure bias 2 were used. The common overview and top-down transforms/orthographic width are exact; close views use 70° horizontal FOV and approximately 170 cm above their walking surface. The four comparison images contain no UI or debug text. The additional runtime_hello.png intentionally includes the editor/PIE UI solely as runtime evidence.

## Known limitations

- Resolved in the movement correction below: the backdrop had reloaded as BlockAll, preventing actual Pawn movement. Fresh-process verification now proves actual possessed Pawn movement and blocking sweeps. No full keyboard-controlled walking playthrough or new character/controller system was added.
- The environment is one combined static mesh for reliable isolated delivery. Blender retains separate parts, but UE per-prop editing, LOD/culling optimization and performance profiling are not provided.
- The station is an exterior set, with no furnished interior or operational railway simulation. The tunnel is short and its far opening is visible. Some large rock forms remain intentionally faceted, and canopy undersides are shaded strongly.
- The terrain surface is exactly 100 × 100 m; rail end geometry extends about 52 cm beyond each X edge. Geometry bounds are recorded in validation.json.
- Captures use SceneCapture and fixed exposure; default interactive viewport auto-exposure can look brighter. No generated-image replacement, image retouching, or Blender render was used as scene evidence.

## External technical references

- Epic UE Python SceneCaptureComponent2D documentation: https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/SceneCaptureComponent2D?application_version=5.7
- Epic LevelEditorSubsystem documentation and local Engine source for PIE, StaticMeshEditorSubsystem collision rebuild, and GameViewportClient screenshot command behavior.
- Baseline native project source was read from commit 7558c8f; existing native binaries were copied into the private project without rebuilding shared binaries.

## Actual Pawn movement correction — supersedes the initial runtime verdict

The initial runtime pass was insufficient: Visibility complex traces did not exercise the Pawn movement collision path, and the failed direct Pawn move should have remained blocking. The previous completion statement is corrected here.

Root cause was proven in a fresh private UE process. The saved Quiet blue horizon backdrop reloaded with actor collision enabled, component QueryAndPhysics, and BlockAll profile. A Pawn-profile simple sweep reported an initial penetrating hit on that backdrop actor. Actual possessed Pawn motion was 0 cm. Disabling only the backdrop collision in the same PIE changed the same motion to 200 cm, proving causality.

The permanent map fix assigns NoCollision profile and disables both component and actor collision. build_ue.py now authors these persistent settings. The map was saved, reloaded, and then loaded again by another fresh private UE process. Both editor and PIE reported NoCollision, component collision off and actor collision off. The Pawn began at (-1900,-1150,120) cm without a Pawn-channel blocking start overlap and moved 200 cm by a real swept SetActorLocation on the possessed Pawn. The same Pawn's downward sweeps were blocked by terrain, ramp and platform at the expected surface plus its collision radius. Every required check, including actual movement and normal PIE shutdown, participates in the final passed verdict.

Evidence: movement_diagnosis.json, movement_diagnosis_log.txt, movement_runtime_validation.json, runtime_validation.json and runtime_log.txt. Canonical runtime_validation.json replaces the earlier inadequate verdict. The final recursive dependency audit still visits 22 packages with zero foreign /Game references. Delivery manifest and published map hashes were regenerated after the private editor exited.

The first fresh-process verification also exposed an invalid terrain test assumption: the Pawn sphere contacted nearby sloping geometry above the center line-trace surface, so a flat surface-plus-radius assertion failed. That failure is retained in ignored scratch as movement_verify_rock_sample.json. Ground sample selection was checked against the original Blender source; the complete required checks were rerun at the unobstructed terrain point (2000,-3000) cm. No required check was removed from the final verdict.

This collision-only change does not alter scene geometry, materials, lights or cameras. The four existing rendered captures remain unchanged, with matching SHA-256 hashes; reuse is documented in capture_manifest.json and the required Screenshots/capture_manifest.json. The runtime evidence capture is separate.

- Original first ready: 2026-10-21T13:05:26.4557133+00:00 (preserved); original first-delivery wall time: 2296.456 seconds.
- This correction started UTC: 2026-10-21T13:15:03.0000000+00:00; KST: 2026-10-21T22:15:03.0000000+09:00.
- This correction finished UTC: 2026-10-21T13:27:54.3894996+00:00; KST: 2026-10-21T22:27:54.3894996+09:00.
- Correction wall seconds: 771.389; mutex wait seconds: 484.604; UE execution seconds: 63.874.
- Overall elapsed from original start includes the idle interval between the first submission and this requested correction. See movement_supplement_timing.json for the separate correction interval.
