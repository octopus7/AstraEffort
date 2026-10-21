# medium — Willow Cove

Status: ready_for_review. Published after private editor exit, fresh validation, direct image review, and SHA-256 copy verification.

## Time record

- Actual start: 2026-10-21 12:11:50 UTC / 2026-10-21 21:11:50 KST.
- First map assembly saved: 12:16:14 UTC. Subsequent visual review found and corrected coordinate, camera and exposure issues.
- Capture script work began at filesystem creation time 12:17:03 UTC. Capture work and scene corrections overlap; these intervals must not be added as independent effort totals.
- User requested `/Game/Forest/medium/` during production. Assets were regenerated using UE import APIs at the new package paths, and the map was recreated. Successful corrected-path map save/reload was performed; the original `/Game/medium` packages remain only in ignored private scratch and are not delivery assets. Path-change handling was not timed independently, so no separate duration is invented.
- Coordinated execution timing files will be summarized on completion. The first final-capture slot waited 62.2019448 seconds and ran 46.8952202 seconds.

## Environment and authorship

100×100m authored mesh terrain, centred on (0,0) cm with Z0=0. An inland elliptical pond sits at approximately (-1500,1300) cm, separated from a southern coastal strip by grassland and forest. A curved path connects the meadow and beach; the pond is reachable across the open meadow. Raised rear terrain frames the clearing.

All meshes were independently authored by deterministic Blender Python generation: terrain, lake and sea meshes, three tree variants, three rounded irregular rocks, two clustered shrubs, two grass/seed tufts, reeds, and a fallen branched log. Tree and vegetation scale, rotation and placement vary. Materials use muted green, blue-green, sand and weathered wood colours. There are no faces, hearts, decorative clouds or imported character motifs.

The source is `make_assets.py`, with individual mesh interchange masters in `Source/*.fbx` and the placement/palette record in `layout.json`. `build_scene.py` imports these into the private project, creates materials, builds the map and saves it. `validate_capture.py` independently reloads the saved map, checks dependencies and renders the four views. `fix_lighting.py` records the small post-review material/lighting correction.

## Gameplay and scope

Ground uses complex-as-simple triangle collision. Solid props receive generated simple collision. Small grass/reeds and water surfaces do not block movement. PlayerStart is on the meadow path. The baseline `/Script/ForestDemo.ScreenDebugLogger` actor is retained for its unmodified BeginPlay Hello behaviour. Dynamic lighting is used throughout; there is no baked lighting data.

This is an environment scene, not a complete game: no custom character controller, swimming, water physics, navigation AI or interaction system was added. The water is a calm opaque stylized surface. Site edges are the explicit finite 100m boundary. Runtime PIE validation was requested as a supervisor follow-up and its actual evidence is recorded separately below.

## Validation and capture protocol

Fresh private-project reload and recursive Asset Registry checks are in `validation.json`. Project dependencies must resolve only to `/Game/Forest/medium/**` or `/Game/Maps/medium`; `/Engine` and baseline `/Script` dependencies are allowed. No assets from another effort were inspected or used. The map is created by non-partitioned `new_level`, and no external actor/object or BuiltData packages are delivered.

Screenshots use the actual UE renderer, SceneCapture2D FinalColorLDR, 1920×1080, High scalability values (2), screen percentage 100. UI, selection outlines, gizmos and debug text are absent. Explicit capture updates and warm-up frames avoid stale render targets. No image generation or retouching is used.

`Screenshots/capture_manifest.json` records final capture times and cameras. Overview uses (12000,-12000,16000), target (0,0,0), orthographic width 20000. Top-down uses (0,0,20000), pitch -90/yaw 0/roll 0, width 20000. Pond and beach views use terrain height +170cm and horizontal FOV 70°. Their site-specific positions limit direct framing comparison.

External references: no external artwork or scene reference. Shared read-only resources are the UE 5.7 engine, its DaylightAmbientCubemap for lighting, and baseline ForestDemo native logger/config/binaries from commit 7558c8f. No shared binaries were built and no Git index/branch/commit operations were performed.

## Supervisor runtime follow-up

Actual follow-up start recorded: 2026-10-21 12:46:14 UTC / 21:46:14 KST. First submission and completed runtime evidence are recorded in the final delivery record and `runtime_validation.json`, with actual start/end timestamps. The runtime script uses the baseline default pawn/controller; no new character implementation or shared configuration changes are made. Capture and runtime share the delivery6 mutex execution, whose exact wait/run times are recorded by the coordination utility.


## Final delivery record

- Finish / first submission: 2026-10-21 13:08:52.136 UTC / 2026-10-21 22:08:52.136 KST.
- Total elapsed wall seconds: 3422.1361498. Original start is preserved.
- Coordinated runner cumulative wait: 1490.973883 seconds; execution: 361.083476 seconds across 9 recorded runs. Includes failed attempts; see execution_timings.json. Pre-coordination runs were not separately timed.
- Final ground uses 25cm mesh spacing and direct Grass/Moss/Sand/Path material regions in GroundSmooth. Earlier Ground/GroundPainted meshes and the unused vertex-colour material were deleted through UE asset APIs after references were updated. Final capture timestamps: overview: 2026-10-21T13:07:33.3562560+00:00; top_down: 2026-10-21T13:07:35.6047290+00:00; lake: 2026-10-21T13:07:37.8208390+00:00; beach: 2026-10-21T13:07:40.0475050+00:00. Capture development began 12:17:03Z and overlapped scene work; no additive time claim is made.
- Supervisor runtime follow-up completed: 2026-10-21T13:07:42.3028250+00:00. Actual PIE test ran from 2026-10-21T13:07:40.0525820+00:00 for 2.25024366378784 seconds. Shared mutex time covers combined capture/runtime work, not exclusively the follow-up.
- Delivered 31 packages: Content/Forest/medium/Materials/**, Content/Forest/medium/Meshes/**, Content/Maps/medium.umap. No redirectors, external actors/objects or BuiltData files were published. Exact file hashes are in delivery_manifest.json.
- Fresh validation: 672 actors, 31 recursively checked owned packages, zero forbidden project references, 10000x10000cm ground. Nine solid mesh types have nonzero simple/convex collision totals. PlayerStart and native logger each appear once. Start-region placement data is clear of solid props within 400cm.
- Actual PIE result: passed; possession, short swept movement, terrain blocking sweep and normal PIE shutdown are documented in runtime_validation.json. Native Hello screenshot is Screenshots/runtime_hello.png and was reviewed separately from the four clean scene views.
- Evidence: Screenshots/overview.png, top_down.png, lake.png, beach.png; all four are unique 1920x1080 actual UE renders. Camera details and UTC timestamps are in Screenshots/capture_manifest.json.
- Commands: Blender background --python make_assets.py; coordinated UE -run=pythonscript -script=build_scene.py -nullrhi; coordinated UE -ExecCmds=py restore_ground.py -RenderOffscreen (calls finish_scene.py, validate_capture.py and runtime_validation.py); publish.ps1 verifies and copies only owned packages.
- Validation correction: UE GetSimpleCollisionCount excludes convex hulls. The final check adds GetConvexCollisionCount; earlier zero simple counts alone did not prove missing collision. Engine source API names were checked locally.



## Approval evidence supplement (no art changes)

- Supplement start: 2026-10-21T13:18:00.0000000+00:00 / 2026-10-21T22:18:00.0000000+09:00 KST.
- Supplement completion: 2026-10-21T13:32:36.4016158+00:00 / 2026-10-21T22:32:36.4016158+09:00 KST; elapsed 876.4016158 seconds.
- Original start, first ready timestamp (2026-10-21T13:08:52.1361498Z), first elapsed 3422.1361498 seconds, original captures and delivery_manifest.json are preserved. No maps/assets were generated, imported, edited or saved in this supplement.
- A fresh private UE process loaded the final map and assets and ran scan_paths_synchronous with force_rescan=True. All 31 owned packages were recursively checked for hard+soft package, searchable and management references. GroundSmooth resolves M_Grass, M_Moss, M_Path and M_Sand in both registry dependencies and actual material slots. No forbidden project references or owned redirectors were found.
- No /Game/medium reference exists in the delivered dependency graph, and shared Content/medium does not exist. There are 30 unused legacy packages in ignored private scratch; these are not delivered or referenced. They were not deleted because this supplement is validation-only.
- Actual PIE downward pawn sweep: blocking_hit=true, initial_overlap=false; actor /Game/Maps/UEDPIE_0_medium.medium:PersistentLevel.StaticMeshActor_0; component StaticMeshComponent0; hit mesh /Game/Forest/medium/Meshes/GroundSmooth.GroundSmooth. Impact point approximately (1198.943,-1399.328,30.963) cm; pawn stopped at Z=67.650589cm instead of requested Z=-500cm. PIE ended normally and the final editor process exited 0.
- The first attempt used an unavailable Python static BreakHitResult name; the second confirmed the ground hit through HitResult.to_tuple() but suffered a WebBrowser/CEF shutdown crash (exit 3). The final fresh process used the engine-supported -nocef flag and exited normally. Project/config/assets were not changed to address CEF.
- Supplement mutex wait total: 365.5745525 seconds; execution total: 52.7185559 seconds across three attempts. See supplement_execution_timings.json.
- All 31 delivered package SHA-256 values match the original manifest before and after validation, and match their private scratch copies. The four original scene PNG hashes also match.
- Evidence: supplement_validation.json, supplement_validation.log, updated validation.json and runtime_validation.json. The original registry evidence is retained as validation_first_delivery.json.
