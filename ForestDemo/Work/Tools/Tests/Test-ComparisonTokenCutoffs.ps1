$ErrorActionPreference='Stop'
$root=Join-Path ([IO.Path]::GetTempPath()) ('comparison-cutoff-test-'+[guid]::NewGuid().ToString('N'))
$sessions=Join-Path $root 'sessions';$work=Join-Path $root 'work'
[IO.Directory]::CreateDirectory($sessions)|Out-Null;[IO.Directory]::CreateDirectory($work)|Out-Null
$scriptPath=Join-Path (Split-Path -Parent $PSScriptRoot) 'Update-TokenUsage.ps1'
function Assert($ok,$message){if(!$ok){throw $message}}
function Usage($n){@{input_tokens=$n;cached_input_tokens=0;cache_write_input_tokens=0;output_tokens=0;reasoning_output_tokens=0;total_tokens=$n}}
function Session($id,$parent,$first,$last,$created='2026-01-01T00:00:00Z'){
    $lines=@((@{type='session_meta';timestamp=$created;payload=@{id=$id;timestamp=$created;parent_thread_id=$parent;thread_source=$(if($parent){'subagent'}else{'user'})}}|ConvertTo-Json -Depth 8 -Compress),(@{type='turn_context';timestamp=$created;payload=@{model='gpt-6-astra';effort='ultra'}}|ConvertTo-Json -Compress))
    if($first){$lines+=(@{type='event_msg';timestamp='2026-01-01T00:00:01Z';payload=@{type='token_count';info=@{total_token_usage=(Usage $first);last_token_usage=(Usage $first)}}}|ConvertTo-Json -Depth 8 -Compress)}
    $lines+=(@{type='event_msg';timestamp='2026-01-01T00:00:03Z';payload=@{type='token_count';info=@{total_token_usage=(Usage $last);last_token_usage=(Usage ($last-$first))}}}|ConvertTo-Json -Depth 8 -Compress)
    $lines|Set-Content "$sessions/$id.jsonl"
}
Session forest $null 100 200
Session child forest 10 20
Session newchild forest 0 30 '2026-01-01T00:00:03Z'
Session station $null 1000 2000
Session supervisor $null 5 15
Session review supervisor 2 4
$coord=@{efforts=@(@{threadId='forest';theme='Forest';effort='ultra';first_commit_at_utc='2026-01-01T00:00:01Z';token_usage_at_first_delivery=@{total_tokens=99;custom='unchanged'}});mountain_station_efforts=@(@{threadId='station';theme='MountainStation';effort='ultra'});comparison_token_cutoffs=@(@{threadId='forest';theme='Forest';effort='ultra';as_of_utc='2026-01-01T00:00:02Z'},@{threadId='supervisor';theme='Supervisor';effort='separate';as_of_utc='2026-01-01T00:00:02Z'})}
function Save-Coord{$coord|ConvertTo-Json -Depth 12|Set-Content "$work/coordination.json"}
function Run([hashtable]$extra=@{}){& $scriptPath -SessionRoot $sessions -SupervisorThreadId supervisor -WorkRoot $work -AsOfUtc '2026-01-01T00:00:04Z' @extra|ConvertFrom-Json}
Save-Coord;[IO.File]::WriteAllText("$work/SUPERVISION.md",'Fixture')
$before=(Get-FileHash "$work/coordination.json").Hash
$data=Run @{NoWrite=$true};$forest=$data.rows|Where-Object thread_id -eq forest;$sup=$data.rows|Where-Object thread_id -eq supervisor
Assert ($forest.total_tokens -eq 100 -and $forest.descendants.Count -eq 1 -and $forest.combined_usage.total_tokens -eq 110) 'Per-job cutoff failed to cap parent/child or exclude new descendants'
Assert ($sup.combined_usage.total_tokens -eq 7) 'Supervisor family cutoff failed'
Assert (($data.rows|Where-Object thread_id -eq station).total_tokens -eq 2000 -and $data.creation_jobs_usage.total_tokens -eq 2110 -and $data.all_roots_usage.total_tokens -eq 2117) 'Uncapped Station or effective totals are wrong'
Assert ([DateTimeOffset]::Parse($forest.effective_cutoff_utc) -eq [DateTimeOffset]::Parse('2026-01-01T00:00:02Z')) 'Row effective cutoff is not visible'
Assert ($forest.frozen_parent_usage.custom -eq 'unchanged' -and $forest.as_of_first_commit.combined_usage.total_tokens -eq 110) 'First-delivery fields changed'
Assert (!(Test-Path "$work/token_usage.json")) 'NoWrite unexpectedly wrote snapshot'
$written=Run
Assert ($written.all_roots_usage.total_tokens -eq 2117) 'Write path ignored comparison cutoffs'
$md=Get-Content "$work/SUPERVISION.md" -Raw
Assert ($md.Contains('comparison accounting cutoff') -and $md.Contains('2026-01-01T00:00:02') -and !$md.Contains('self-improvement')) 'Neutral cutoff report is missing or contains unrelated plans'
$hashes=@((Get-FileHash "$work/SUPERVISION.md").Hash,(Get-FileHash "$work/token_usage.json").Hash)
$full=Run @{NoWrite=$true;IgnoreComparisonCutoffs=$true}
Assert (($full.rows|Where-Object thread_id -eq forest).combined_usage.total_tokens -eq 250 -and $full.all_roots_usage.total_tokens -eq 2269) 'Read-only override did not include later usage'
$early=& $scriptPath -SessionRoot $sessions -SupervisorThreadId supervisor -WorkRoot $work -AsOfUtc '2026-01-01T00:00:01Z' -NoWrite|ConvertFrom-Json
Assert ([DateTimeOffset]::Parse(($early.rows|Where-Object thread_id -eq forest).effective_cutoff_utc) -eq [DateTimeOffset]::Parse('2026-01-01T00:00:01Z')) 'Global earlier cutoff was not respected'
$threw=$false;try{Run @{IgnoreComparisonCutoffs=$true}|Out-Null}catch{$threw=$true}
Assert $threw 'Override allowed a write'
Assert ((Get-FileHash "$work/coordination.json").Hash -eq $before) 'Accounting mutated source coordination'
$originalCutoffs=$coord.comparison_token_cutoffs
$coord.comparison_token_cutoffs=@($originalCutoffs)+@($originalCutoffs[0]);Save-Coord
$threw=$false;try{Run @{NoWrite=$true}|Out-Null}catch{$threw=$true}
Assert $threw 'Duplicate cutoff identity was silently accepted'
$coord.comparison_token_cutoffs=@(@{threadId='forest';theme='MountainStation';effort='ultra';as_of_utc='2026-01-01T00:00:02Z'});Save-Coord
$threw=$false;try{Run @{NoWrite=$true}|Out-Null}catch{$threw=$true}
Assert $threw 'Mismatched cutoff assignment was silently accepted'
$coord.comparison_token_cutoffs=$originalCutoffs
$coord.ultra_self_improvement=@{comparison_freeze=@{status='frozen'}};Save-Coord
$threw=$false;try{Run|Out-Null}catch{$threw=$true}
Assert $threw 'Frozen comparison allowed a write'
Run @{NoWrite=$true}|Out-Null;Run @{NoWrite=$true;IgnoreComparisonCutoffs=$true}|Out-Null
Assert ((Get-FileHash "$work/SUPERVISION.md").Hash -eq $hashes[0] -and (Get-FileHash "$work/token_usage.json").Hash -eq $hashes[1]) 'Rejected writes or NoWrite mutated comparison files'
Write-Output "PASS: per-job family cutoff, late descendants, uncapped Station, totals, first-delivery preservation, global minimum, readonly override, frozen write guard. Evidence: $root"
