$ErrorActionPreference='Stop'
$root='D:/github/AstraEffort/ForestDemo/Work/medium'
$pass="$root/TexturePass"
$delivery=Get-Content "$pass/delivery_manifest.json" -Raw|ConvertFrom-Json
$runtime=Get-Content "$pass/runtime_validation.json" -Raw|ConvertFrom-Json
$tex=Get-Content "$pass/texture_application_validation.json" -Raw|ConvertFrom-Json
$water=Get-Content "$pass/water_animation_validation.json" -Raw|ConvertFrom-Json
$validation=Get-Content "$pass/validation.json" -Raw|ConvertFrom-Json
$timings=@(Get-ChildItem "$pass/*_timing.json" | ForEach-Object {Get-Content $_.FullName -Raw|ConvertFrom-Json})
if($runtime.status -ne 'passed' -or $tex.status -ne 'passed' -or $water.status -ne 'passed' -or !$delivery.validated_copy_hashes_match){throw 'Incomplete final evidence'}
if(@($timings|Where-Object exit_code -ne 0).Count){throw 'Review nonzero UE process exit before finalizing'}
$archive=Get-Content "$root/FirstDelivery/archive_manifest.json" -Raw|ConvertFrom-Json
foreach($f in $archive.files){if((Get-FileHash (Join-Path "$root/FirstDelivery" $f.path) -Algorithm SHA256).Hash -ne $f.sha256){throw "FirstDelivery modified: $($f.path)"}}
$finish=[DateTimeOffset]::UtcNow;$start=[DateTimeOffset]::Parse('2026-10-21T13:42:41Z')
$wait=($timings|Measure-Object wait_seconds -Sum).Sum;$run=($timings|Measure-Object execution_seconds -Sum).Sum
$status=[ordered]@{effort='medium';theme='Forest';phase='texture_pass';status='ready_for_review';started_at_utc=$start.ToString('o');started_at_kst=$start.ToOffset([TimeSpan]::FromHours(9)).ToString('o');finished_at_utc=$finish.ToString('o');finished_at_kst=$finish.ToOffset([TimeSpan]::FromHours(9)).ToString('o');elapsed_seconds=($finish-$start).TotalSeconds;map='/Game/Maps/medium';asset_root='/Game/Forest/medium';imagegen_wall_seconds=32;supervisor_reported_interruption_seconds=775;coordinated_wait_seconds=$wait;coordinated_execution_seconds=$run;validation=@{fresh_saved_map_reload=$true;bad_dependencies=$validation.bad_dependencies;runtime_status=$runtime.status;ground_hit_mesh=$runtime.ground_sweep.hit_mesh;texture_application=$tex.status;water_animation=$water.status;capture_resolution='1920x1080';comparison_capture_count=4;water_capture_count=2;published_packages=$delivery.files.Count;copy_hashes_verified=$true;private_editor_closed=$true;first_delivery_archive_unchanged=$true};blockers=@()}
$status|ConvertTo-Json -Depth 8|Set-Content "$pass/STATUS.json" -Encoding utf8
@{total_wait_seconds=$wait;total_execution_seconds=$run;runs=$timings}|ConvertTo-Json -Depth 8|Set-Content "$pass/execution_timings.json" -Encoding utf8
$original=Get-Content "$root/STATUS.json" -Raw|ConvertFrom-Json
$original.status='ready_for_review';$original|Add-Member -Force NoteProperty phase 'texture_pass';$original|Add-Member -Force NoteProperty texture_pass $status
$original|ConvertTo-Json -Depth 12|Set-Content "$root/STATUS.json" -Encoding utf8
$result=[IO.File]::ReadAllText("$pass/RESULT.md").Replace('Status: working. Final saved-map validation and publication are pending.','Status: ready_for_review. Saved-map validation and publication completed; no Git staging or commit.').Replace('Pending. Planned evidence:','Completed evidence:').Replace('Actual UE render evidence will be in','Actual UE render evidence is in')
$details=@"

## Completion record

- Start UTC: $($status.started_at_utc); KST: $($status.started_at_kst)
- Finish UTC: $($status.finished_at_utc); KST: $($status.finished_at_kst)
- Total elapsed wall seconds: $($status.elapsed_seconds)
- UE queue wait seconds: $wait; UE execution seconds: $run
- Image generation: 32 seconds. Supervisor-recorded interruption: 775 seconds (included in total wall time).
- Published $($delivery.files.Count) packages after editor exit, with SHA-256 equality between scratch and delivery. See delivery_manifest.json.
- Runtime possession, short swept movement, blocking GroundSmooth hit and normal PIE exit passed. See runtime_validation.json.
- All 85 UV variants and all placed textured prop instances passed saved mesh/texture checks. See texture_application_validation.json.
- Recursive hard/soft/searchable/management dependency scan found no forbidden /Game packages. Saved map and owned assets were freshly reloaded.
- Timed fixed-camera water interval: $($water.world_time_delta_seconds) game-world seconds. See water_animation_validation.json and Screenshots/water_t0.png, water_t1.png.
- FirstDelivery archive hash verification passed again at completion. Original root timing fields remain unchanged; current pass status is nested in texture_pass.

Deliverables: ForestDemo/Content/Forest/medium/**, ForestDemo/Content/Maps/medium.umap, and this TexturePass evidence/source directory. Final integration and commit belong to the supervisor.
"@
[IO.File]::WriteAllText("$pass/RESULT.md",$result+$details)
Add-Content "$root/RESULT.md" "`nTexture pass completed: see TexturePass/RESULT.md and TexturePass/STATUS.json. First-delivery times above are preserved."
$status|ConvertTo-Json -Depth 8
