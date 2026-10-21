$ErrorActionPreference='Stop'
$w='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium'
$scratch='D:/github/AstraEffort/ForestDemo/Saved/Workers/MountainStation/medium'
$r=Get-Content "$w/movement_runtime_validation.json" -Raw | ConvertFrom-Json -DateKind String
if (!$r.passed -or !$r.direct_actor_move_succeeded) { throw 'Actual Pawn movement must pass' }
$s=Get-Content "$w/STATUS.json" -Raw | ConvertFrom-Json -DateKind String
$first=$s.first_ready_at_utc
$start=[DateTimeOffset]::Parse($s.movement_supplement_started_at_utc)
$end=[DateTimeOffset]::UtcNow
$runs=@('movement_diagnose_timing.json','movement_verify_timing.json','movement_verify2_timing.json') | ForEach-Object {Get-Content "$w/$_" -Raw | ConvertFrom-Json -DateKind String}
$summary=[ordered]@{started_at_utc=$start.ToString('o');finished_at_utc=$end.ToString('o');elapsed_seconds=($end-$start).TotalSeconds;mutex_wait_seconds=($runs | Measure-Object wait_seconds -Sum).Sum;ue_execution_seconds=($runs | Measure-Object execution_seconds -Sum).Sum;first_ready_at_utc=$first;first_delivery_elapsed_seconds=2296.4557133;fresh_process_runtime_passed=$r.passed;actual_pawn_movement_cm=$r.spawn_move.distance_cm}
$summary | ConvertTo-Json -Depth 6 | Set-Content "$w/movement_supplement_timing.json"
Select-String -Path "$scratch/movement_verify2.log" -Pattern 'LogPlayLevel:|MOVEMENT_RUNTIME_VALIDATION|LogWorld: Bringing|LogExit: Editor|Screenshot' | ForEach-Object {$_.Line} | Set-Content "$w/runtime_log.txt"
Select-String -Path "$scratch/movement_diagnose.log" -Pattern 'MOVEMENT_DIAGNOSIS|LogPlayLevel:|LogExit: Editor' | ForEach-Object {$_.Line} | Set-Content "$w/movement_diagnosis_log.txt"
$c=Get-Content "$w/capture_manifest.json" -Raw | ConvertFrom-Json -DateKind String
$c | Add-Member collision_only_revision ([ordered]@{verified_at_utc=$r.finished_at_utc;description='Persisted NoCollision profile and actor collision off on Quiet blue horizon. No visual geometry/material/light/camera change. All four existing actual UE captures retained unchanged.';runtime_evidence='movement_runtime_validation.json'}) -Force
$c | ConvertTo-Json -Depth 12 | Set-Content "$w/capture_manifest.json"
Copy-Item "$w/capture_manifest.json" "$w/Screenshots/capture_manifest.json" -Force
& "$w/publish.ps1"
$doc=Get-Content "$w/RESULT.md" -Raw
$doc=$doc.Replace('Status: ready_for_review.','Status: ready_for_review after the actual Pawn movement correction below.')
$old='- Direct DefaultPawn K2_SetActorLocation sweep returned no movement in this automated check. It is not reported as successful traversal. Independent runtime sphere sweeps passed; a full keyboard-controlled walking playthrough was not performed. The inherited Engine DefaultPawn is retained; no new character/controller system was added.'
$new='- Resolved in the movement correction below: the backdrop had reloaded as BlockAll, preventing actual Pawn movement. Fresh-process verification now proves actual possessed Pawn movement and blocking sweeps. No full keyboard-controlled walking playthrough or new character/controller system was added.'
$doc=$doc.Replace($old,$new)
$append=@'

## Actual Pawn movement correction — supersedes the initial runtime verdict

The initial runtime pass was insufficient: Visibility complex traces did not exercise the Pawn movement collision path, and the failed direct Pawn move should have remained blocking. The previous completion statement is corrected here.

Root cause was proven in a fresh private UE process. The saved Quiet blue horizon backdrop reloaded with actor collision enabled, component QueryAndPhysics, and BlockAll profile. A Pawn-profile simple sweep reported an initial penetrating hit on that backdrop actor. Actual possessed Pawn motion was 0 cm. Disabling only the backdrop collision in the same PIE changed the same motion to 200 cm, proving causality.

The permanent map fix assigns NoCollision profile and disables both component and actor collision. build_ue.py now authors these persistent settings. The map was saved, reloaded, and then loaded again by another fresh private UE process. Both editor and PIE reported NoCollision, component collision off and actor collision off. The Pawn began at (-1900,-1150,120) cm without a Pawn-channel blocking start overlap and moved 200 cm by a real swept SetActorLocation on the possessed Pawn. The same Pawn's downward sweeps were blocked by terrain, ramp and platform at the expected surface plus its collision radius. Every required check, including actual movement and normal PIE shutdown, participates in the final passed verdict.

Evidence: movement_diagnosis.json, movement_diagnosis_log.txt, movement_runtime_validation.json, runtime_validation.json and runtime_log.txt. Canonical runtime_validation.json replaces the earlier inadequate verdict. The final recursive dependency audit still visits 22 packages with zero foreign /Game references. Delivery manifest and published map hashes were regenerated after the private editor exited.

The first fresh-process verification also exposed an invalid terrain test assumption: the Pawn sphere contacted nearby sloping geometry above the center line-trace surface, so a flat surface-plus-radius assertion failed. That failure is retained in ignored scratch as movement_verify_rock_sample.json. Ground sample selection was checked against the original Blender source; the complete required checks were rerun at the unobstructed terrain point (2000,-3000) cm. No required check was removed from the final verdict.

This collision-only change does not alter scene geometry, materials, lights or cameras. The four existing rendered captures remain unchanged, with matching SHA-256 hashes; reuse is documented in capture_manifest.json and the required Screenshots/capture_manifest.json. The runtime evidence capture is separate.

- Original first ready: FIRST (preserved); original first-delivery wall time: 2296.456 seconds.
- This correction started UTC: START; KST: STARTKST.
- This correction finished UTC: END; KST: ENDKST.
- Correction wall seconds: WALL; mutex wait seconds: WAIT; UE execution seconds: EXEC.
- Overall elapsed from original start includes the idle interval between the first submission and this requested correction. See movement_supplement_timing.json for the separate correction interval.
'@
$append=$append.Replace('FIRST',$first).Replace('STARTKST',$start.ToOffset([TimeSpan]::FromHours(9)).ToString('o')).Replace('ENDKST',$end.ToOffset([TimeSpan]::FromHours(9)).ToString('o')).Replace('START',$start.ToString('o')).Replace('END',$end.ToString('o')).Replace('WALL',([math]::Round($summary.elapsed_seconds,3)).ToString()).Replace('WAIT',([math]::Round($summary.mutex_wait_seconds,3)).ToString()).Replace('EXEC',([math]::Round($summary.ue_execution_seconds,3)).ToString())
Set-Content "$w/RESULT.md" ($doc+$append)
$s.status='ready_for_review'; $s.finished_at_utc=$end.ToString('o'); $s.elapsed_seconds=($end-[DateTimeOffset]::Parse($s.started_at_utc)).TotalSeconds
$s.validation.runtime_passed=$true
$s.validation.PSObject.Properties.Remove('direct_pawn_move_limitation')
$s.validation | Add-Member actual_possessed_pawn_movement_cm 200 -Force
$s.validation | Add-Member fresh_process_backdrop_no_collision $true -Force
$s.validation | Add-Member pawn_terrain_ramp_platform_sweeps_passed $true -Force
$s.blockers=@(); $s | Add-Member movement_supplement_finished_at_utc $end.ToString('o') -Force
$s | ConvertTo-Json -Depth 10 | Set-Content "$w/STATUS.json"
if ($s.first_ready_at_utc -ne $first) { throw 'First ready timestamp changed' }
$summary | ConvertTo-Json -Depth 6
