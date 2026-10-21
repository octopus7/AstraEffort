$ErrorActionPreference='Stop'
$w='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium'
$scratch='D:/github/AstraEffort/ForestDemo/Saved/Workers/MountainStation/medium'
$s=Get-Content "$w/STATUS.json" -Raw | ConvertFrom-Json -DateKind String
$start=[DateTimeOffset]::Parse($s.started_at_utc)
$finish=[DateTimeOffset]::UtcNow
$elapsed=($finish-$start).TotalSeconds
$v=Get-Content "$w/validation.json" -Raw | ConvertFrom-Json -DateKind String
$r=Get-Content "$w/runtime_validation.json" -Raw | ConvertFrom-Json -DateKind String
$c=Get-Content "$w/capture_manifest.json" -Raw | ConvertFrom-Json -DateKind String
$d=Get-Content "$w/delivery_manifest.json" -Raw | ConvertFrom-Json -DateKind String
$timings=@(Get-ChildItem "$w/*_timing.json" | ForEach-Object { $t=Get-Content $_.FullName -Raw | ConvertFrom-Json -DateKind String; $t | Add-Member name $_.BaseName -PassThru })
$wait=($timings | Measure-Object wait_seconds -Sum).Sum
$execution=($timings | Measure-Object execution_seconds -Sum).Sum
$suppStart=[DateTimeOffset]::Parse($r.supplement_started_at_utc)
$runtimeFinish=[DateTimeOffset]::Parse($r.finished_at_utc)
$suppRuns=@($timings | Where-Object {$_.name -in @('refine1_timing','final1_timing')})
$supp=[ordered]@{started_at_utc=$suppStart.ToString('o'); finished_at_utc=$runtimeFinish.ToString('o'); elapsed_seconds=($runtimeFinish-$suppStart).TotalSeconds; mutex_wait_seconds=($suppRuns | Measure-Object wait_seconds -Sum).Sum; combined_refinement_capture_and_runtime_ue_seconds=($suppRuns | Measure-Object execution_seconds -Sum).Sum; final_runtime_seconds=$r.runtime_execution_seconds; note='Combined sessions also contain visual fixes and captures; runtime-only time is separately measured.'}
$supp | ConvertTo-Json -Depth 6 | Set-Content "$w/supplement_timing.json"
Select-String -Path "$scratch/final1.log" -Pattern 'LogPlayLevel:|MOUNTAIN_MEDIUM_RUNTIME|LogWorld: Bringing|LogExit: Editor|Screenshot' | ForEach-Object {$_.Line} | Set-Content "$w/runtime_log.txt"
Select-String -Path "$scratch/refine1.log" -Pattern 'MOUNTAIN_MEDIUM_BUILD_VALIDATED|AssetCheck:|LogContentValidation:.*Validated asset|LogExit: Editor' | ForEach-Object {$_.Line} | Set-Content "$w/validation_log.txt"
Add-Type -AssemblyName System.Drawing
$images=foreach ($name in @('overview','top_down','platform','tracks')) {
 $path="$w/Screenshots/$name.png"; $im=[Drawing.Image]::FromFile($path)
 try { if ($im.Width -ne 1920 -or $im.Height -ne 1080) { throw 'Unexpected screenshot dimensions' }; [ordered]@{file="$name.png";width=$im.Width;height=$im.Height;sha256=(Get-FileHash $path -Algorithm SHA256).Hash;visually_reviewed=$true} } finally {$im.Dispose()}
}
$images | ConvertTo-Json -Depth 5 | Set-Content "$w/image_validation.json"
$rows=($timings | ForEach-Object { '| '+$_.name+' | '+([math]::Round($_.wait_seconds,3))+' | '+([math]::Round($_.execution_seconds,3))+' | '+$_.exit_code+' |' }) -join "`n"
$template=@'
# MountainStation / medium — Alder Pass

Status: ready_for_review. Independently authored by this chat; no subagents, borrowed scene resources, Git index changes or commits.

## Actual timing

- Start UTC: STARTUTC; KST: STARTKST.
- Finish / first ready UTC: FINISHUTC; KST: FINISHKST.
- Total wall time: ELAPSED seconds. Start was never reset.
- Named mutex wait total: WAIT seconds. UE process execution total: EXECUTION seconds, including failed/repeated attempts.
- Final reload/dependency/editor collision audit: VALIDATION seconds.
- Final four-image capture interval: CAPTURE seconds. Final PIE runtime check: RUNTIME seconds.
- Supplement requested during work: 2026-10-21 12:46:02 UTC / 21:46:02 KST. See supplement_timing.json for completion and separate wait/execution records. Combined sessions also include necessary visual refinement and capture work.
- Clock correction: an intermediate STATUS update incorrectly added about 9 hours because ConvertFrom-Json converted UTC to DateTime before string parsing. Re-read with -DateKind String and calculate DateTimeOffset.UtcNow minus the original UTC timestamp. Only KST display uses ToOffset(+09:00). The corrected elapsed value is authoritative.

| Session | Mutex wait seconds | UE execution seconds | Exit |
|---|---:|---:|---:|
TIMINGROWS

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

- Direct DefaultPawn K2_SetActorLocation sweep returned no movement in this automated check. It is not reported as successful traversal. Independent runtime sphere sweeps passed; a full keyboard-controlled walking playthrough was not performed. The inherited Engine DefaultPawn is retained; no new character/controller system was added.
- The environment is one combined static mesh for reliable isolated delivery. Blender retains separate parts, but UE per-prop editing, LOD/culling optimization and performance profiling are not provided.
- The station is an exterior set, with no furnished interior or operational railway simulation. The tunnel is short and its far opening is visible. Some large rock forms remain intentionally faceted, and canopy undersides are shaded strongly.
- The terrain surface is exactly 100 × 100 m; rail end geometry extends about 52 cm beyond each X edge. Geometry bounds are recorded in validation.json.
- Captures use SceneCapture and fixed exposure; default interactive viewport auto-exposure can look brighter. No generated-image replacement, image retouching, or Blender render was used as scene evidence.

## External technical references

- Epic UE Python SceneCaptureComponent2D documentation: https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/SceneCaptureComponent2D?application_version=5.7
- Epic LevelEditorSubsystem documentation and local Engine source for PIE, StaticMeshEditorSubsystem collision rebuild, and GameViewportClient screenshot command behavior.
- Baseline native project source was read from commit 7558c8f; existing native binaries were copied into the private project without rebuilding shared binaries.
'@
$text=$template.Replace('STARTUTC',$start.ToString('o')).Replace('STARTKST',$start.ToOffset([TimeSpan]::FromHours(9)).ToString('o')).Replace('FINISHUTC',$finish.ToString('o')).Replace('FINISHKST',$finish.ToOffset([TimeSpan]::FromHours(9)).ToString('o')).Replace('ELAPSED',([math]::Round($elapsed,3)).ToString()).Replace('WAIT',([math]::Round($wait,3)).ToString()).Replace('EXECUTION',([math]::Round($execution,3)).ToString()).Replace('VALIDATION',([math]::Round($v.validation_seconds,3)).ToString()).Replace('CAPTURE',([math]::Round($c.capture_wall_seconds,3)).ToString()).Replace('RUNTIME',([math]::Round($r.runtime_execution_seconds,3)).ToString()).Replace('TIMINGROWS',$rows)
Set-Content "$w/RESULT.md" $text
$s.status='ready_for_review'; $s.finished_at_utc=$finish.ToString('o'); $s.elapsed_seconds=$elapsed
$s.validation=[ordered]@{map_reload=$true;recursive_packages=$v.visited_packages;foreign_game_dependencies=0;runtime_passed=$r.passed;hello_visually_confirmed=$r.hello_overlay_visually_confirmed;captures=4;resolution='1920x1080';published_packages=$d.count;hashes_match=$true;direct_pawn_move_limitation='Runtime sphere sweep alternative passed; see RESULT.md'}
$s.blockers=@()
$s | Add-Member first_ready_at_utc $finish.ToString('o') -Force
$s | ConvertTo-Json -Depth 8 | Set-Content "$w/STATUS.json"
Get-Content "$w/STATUS.json"
