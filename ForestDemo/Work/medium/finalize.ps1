$ErrorActionPreference='Stop'
$work='D:/github/AstraEffort/ForestDemo/Work/medium'
$scratch='D:/github/AstraEffort/ForestDemo/Saved/Workers/medium'
$delivery=Get-Content "$work/delivery_manifest.json" -Raw | ConvertFrom-Json -DateKind String
$validation=Get-Content "$work/validation.json" -Raw | ConvertFrom-Json -DateKind String
$runtime=Get-Content "$work/runtime_validation.json" -Raw | ConvertFrom-Json -DateKind String
$capture=Get-Content "$work/Screenshots/capture_manifest.json" -Raw | ConvertFrom-Json -DateKind String
$timings=@(Get-ChildItem $scratch -Filter '*-timing.json' | ForEach-Object {Get-Content $_.FullName -Raw | ConvertFrom-Json -DateKind String})
$wait=($timings | Measure-Object wait_seconds -Sum).Sum
$run=($timings | Measure-Object execution_seconds -Sum).Sum
$finished=[DateTimeOffset]::UtcNow
$started=[DateTimeOffset]::Parse('2026-10-21T12:11:50Z')
$elapsed=($finished-$started).TotalSeconds
$status=[ordered]@{effort='medium';status='ready_for_review';started_at_utc=$started.ToString('o');finished_at_utc=$finished.ToString('o');elapsed_seconds=$elapsed;map='/Game/Maps/medium';asset_root='/Game/Forest/medium';validation=@{reloaded=$validation.reloaded;package_count=$validation.dependency_packages;bad_dependencies=$validation.bad_dependencies;actor_count=$validation.actor_count;runtime_status=$runtime.status;capture_count=4;capture_resolution='1920x1080';published_packages=$delivery.files.Count;copy_hashes_verified=$true};blockers=@();coordinated_wait_seconds=$wait;coordinated_execution_seconds=$run;supervisor_followup_started_at_utc='2026-10-21T12:46:14Z';supervisor_followup_finished_at_utc=$runtime.finished_at_utc;path_change='Regenerated under /Game/Forest/medium using UE import APIs; map recreated and dependencies rechecked; separate duration not measured'}
$status | ConvertTo-Json -Depth 8 | Set-Content "$work/STATUS.json"
$timings | ConvertTo-Json -Depth 5 | Set-Content "$work/execution_timings.json"
$report=Get-Content "$work/RESULT.md" -Raw
$report=$report.Replace('Status: working; final visual verification and publication pending.','Status: ready_for_review. Published after private editor exit, fresh validation, direct image review, and SHA-256 copy verification.')
$report=$report.Replace('No first submission has yet been made. Runtime evidence is pending the queued private UE session; it will be recorded in `runtime_validation.json`, with its own start/end timestamps.','First submission and completed runtime evidence are recorded in the final delivery record and `runtime_validation.json`, with actual start/end timestamps.')
$report=$report.Replace('Capture and runtime share the delivery3 mutex execution','Capture and runtime share the delivery6 mutex execution')
$report+="`n`n## Final delivery record`n`n"
$report+="- Finish / first submission: $($finished.ToString('yyyy-MM-dd HH:mm:ss.fff')) UTC / $($finished.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-dd HH:mm:ss.fff')) KST.`n"
$report+="- Total elapsed wall seconds: $elapsed. Original start is preserved.`n"
$report+="- Coordinated runner cumulative wait: $wait seconds; execution: $run seconds across $($timings.Count) recorded runs. Includes failed attempts; see execution_timings.json. Pre-coordination runs were not separately timed.`n"
$report+="- Final ground uses 25cm mesh spacing and direct Grass/Moss/Sand/Path material regions in GroundSmooth. Earlier Ground/GroundPainted meshes and the unused vertex-colour material were deleted through UE asset APIs after references were updated. Final capture timestamps: $(( $capture.captures | ForEach-Object {$_.name+': '+$_.captured_at_utc}) -join '; '). Capture development began 12:17:03Z and overlapped scene work; no additive time claim is made.`n"
$report+="- Supervisor runtime follow-up completed: $($runtime.finished_at_utc). Actual PIE test ran from $($runtime.started_at_utc) for $($runtime.elapsed_seconds) seconds. Shared mutex time covers combined capture/runtime work, not exclusively the follow-up.`n"
$report+="- Delivered $($delivery.files.Count) packages: Content/Forest/medium/Materials/**, Content/Forest/medium/Meshes/**, Content/Maps/medium.umap. No redirectors, external actors/objects or BuiltData files were published. Exact file hashes are in delivery_manifest.json.`n"
$report+="- Fresh validation: $($validation.actor_count) actors, $($validation.dependency_packages) recursively checked owned packages, zero forbidden project references, 10000x10000cm ground. Nine solid mesh types have nonzero simple/convex collision totals. PlayerStart and native logger each appear once. Start-region placement data is clear of solid props within 400cm.`n"
$report+="- Actual PIE result: $($runtime.status); possession, short swept movement, terrain blocking sweep and normal PIE shutdown are documented in runtime_validation.json. Native Hello screenshot is Screenshots/runtime_hello.png and was reviewed separately from the four clean scene views.`n"
$report+="- Evidence: Screenshots/overview.png, top_down.png, lake.png, beach.png; all four are unique 1920x1080 actual UE renders. Camera details and UTC timestamps are in Screenshots/capture_manifest.json.`n"
$report+="- Commands: Blender background --python make_assets.py; coordinated UE -run=pythonscript -script=build_scene.py -nullrhi; coordinated UE -ExecCmds=py restore_ground.py -RenderOffscreen (calls finish_scene.py, validate_capture.py and runtime_validation.py); publish.ps1 verifies and copies only owned packages.`n"
$report+="- Validation correction: UE GetSimpleCollisionCount excludes convex hulls. The final check adds GetConvexCollisionCount; earlier zero simple counts alone did not prove missing collision. Engine source API names were checked locally.`n"
$report | Set-Content "$work/RESULT.md"
Write-Output ($status | ConvertTo-Json -Depth 8)


