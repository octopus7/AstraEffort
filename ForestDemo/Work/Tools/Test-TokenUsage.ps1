$ErrorActionPreference='Stop'
$root=Join-Path ([IO.Path]::GetTempPath()) ('token-worktest-'+[guid]::NewGuid().ToString('N'))
$sessions=Join-Path $root 'sessions';$work=Join-Path $root 'work'
[IO.Directory]::CreateDirectory($sessions)|Out-Null;[IO.Directory]::CreateDirectory($work)|Out-Null
function Assert($condition,$message){if(!$condition){throw $message}}
function Usage($n){return @{input_tokens=$n;cached_input_tokens=0;cache_write_input_tokens=0;output_tokens=0;reasoning_output_tokens=0;total_tokens=$n}}
function Session($id,$parent,$kind,$events,$created='2026-01-01T00:00:00Z'){
    $meta=@{timestamp=$created;type='session_meta';payload=@{id=$id;timestamp=$created;parent_thread_id=$parent;thread_source=$kind;source=@{subagent=@{thread_spawn=@{parent_thread_id=$parent}}};forked_from_id=$parent}}
    $lines=@(($meta|ConvertTo-Json -Depth 8 -Compress),(@{timestamp=$created;type='turn_context';payload=@{model='gpt-6-astra';effort='high'}}|ConvertTo-Json -Compress))
    foreach($e in $events){$lines+=(@{timestamp=$e.at;type='event_msg';payload=@{type='token_count';info=@{total_token_usage=$e.total;last_token_usage=$e.last}}}|ConvertTo-Json -Depth 8 -Compress)}
    $lines|Set-Content -LiteralPath "$sessions/rollout-$id.jsonl"
}
$a='2026-01-01T00:00:01Z';$b='2026-01-01T00:00:03Z'
Session 'parent' $null 'user' @(@{at=$a;total=(Usage 100);last=(Usage 100)},@{at=$b;total=(Usage 150);last=(Usage 50)})
Session 'child' 'parent' 'subagent' @(@{at=$a;total=(Usage 20);last=(Usage 20)},@{at=$b;total=(Usage 30);last=(Usage 10)})
Copy-Item "$sessions/rollout-child.jsonl" "$sessions/duplicate-child.jsonl"
Session 'grandchild' 'child' 'guardian_review' @(@{at=$a;total=(Usage 5);last=(Usage 5)})
Session 'supervisor' 'parent' 'user' @(@{at=$a;total=(Usage 7);last=(Usage 7)})
Session 'unrelated' $null 'user' @(@{at=$a;total=(Usage 999);last=(Usage 999)})
$coord=@{efforts=@(@{theme='Forest';effort='high';threadId='parent';first_commit_at_utc='2026-01-01T00:00:02Z';token_usage_at_first_delivery=@{total_tokens=123;custom='preserve'}});mountain_station_efforts=@()}
$coord|ConvertTo-Json -Depth 8|Set-Content "$work/coordination.json";[IO.File]::WriteAllText("$work/SUPERVISION.md",'Synthetic report')
@{id='legacy';timestamp='2025-01-01T00:00:00Z';instructions='DO NOT COPY'}|ConvertTo-Json -Compress|Set-Content "$sessions/rollout-2025-01-01T00-00-00-legacy.jsonl"
[IO.File]::WriteAllText("$sessions/rollout-2025-01-02T00-00-00-empty.jsonl",'')
$scriptPath=Join-Path $PSScriptRoot 'Update-TokenUsage.ps1'
& $scriptPath -SessionRoot $sessions -SupervisorThreadId supervisor -WorkRoot $work | Out-Null
$data=Get-Content "$work/token_usage.json" -Raw|ConvertFrom-Json
$row=$data.rows|Where-Object thread_id -eq parent
Assert ($row.total_tokens -eq 150) 'Parent cumulative snapshots were summed or changed'
Assert ($row.descendants.Count -eq 2 -and $row.descendant_usage.total_tokens -eq 35) 'Descendant recursion or duplicate-file deduplication failed'
Assert ($row.combined_usage.total_tokens -eq 185) 'Parent plus descendant total failed'
Assert ($row.as_of_first_commit.combined_usage.total_tokens -eq 125) 'As-of cutoff included later usage'
Assert ($row.frozen_parent_usage.total_tokens -eq 123 -and $row.frozen_parent_usage.custom -eq 'preserve') 'Frozen parent was overwritten'
Assert (($row.descendants|Where-Object thread_id -eq grandchild).accounting_category -eq 'automatic_approval_review') 'Guardian approval review was mislabeled as author delegation'
Assert ($data.creation_jobs_usage.total_tokens -eq 185 -and $data.all_roots_usage.total_tokens -eq 192) 'Supervisor or unrelated-session accounting failed'
Assert ($data.discovery_issues.Count -eq 0 -and $data.discovery_header_summary.historical_outside_family_window -eq 2) 'Unrelated historical headers contaminated family coverage'
$markdown=Get-Content "$work/SUPERVISION.md" -Raw
Assert ($markdown.Contains('캐시 입력(입력 내)') -and $markdown.Contains('당시 부모+후손') -and $markdown.Contains('위임 보조 에이전트')) 'Required standalone Markdown tables are missing'
Assert ($row.descendant_category_counts.automatic_approval_review -eq 1 -and $row.descendant_category_counts.delegated_subagent -eq 1) 'Descendant category counts are wrong'
# Missing child usage is unknown, and inherited cumulative counters cannot be added twice.
Session 'missing' 'parent' 'guardian_review' @()
Session 'inherited' 'parent' 'subagent' @(@{at=$a;total=(Usage 200);last=(Usage 10)})
[IO.File]::WriteAllText("$sessions/rollout-2026-01-01T00-00-00-empty-live.jsonl",'')
& $scriptPath -SessionRoot $sessions -SupervisorThreadId supervisor -WorkRoot $work | Out-Null
$data=Get-Content "$work/token_usage.json" -Raw|ConvertFrom-Json;$row=$data.rows|Where-Object thread_id -eq parent
Assert ($null -eq $row.combined_usage.total_tokens -and $row.combined_usage.known_subtotal.total_tokens -eq 185) 'Unknown or non-local child usage was silently treated as zero/additive'
Assert (!(($row.descendants|Where-Object thread_id -eq inherited).accounting_eligible)) 'Inherited usage was accepted as child-local'
Assert ($data.discovery_header_summary.unresolved_in_scope_or_unknown -eq 1 -and $data.discovery_issues.Count -eq 1) 'Current empty rollout was silently classified as unrelated'
Assert ((Get-Content "$work/coordination.json" -Raw|ConvertFrom-Json).efforts[0].token_usage_at_first_delivery.total_tokens -eq 123) 'Source coordination mutated'
$before=(Get-FileHash "$work/token_usage.json").Hash
$historical=& $scriptPath -SessionRoot $sessions -SupervisorThreadId supervisor -WorkRoot $work -AsOfUtc '2026-01-01T00:00:01Z' -NoWrite | ConvertFrom-Json
Assert ((Get-FileHash "$work/token_usage.json").Hash -eq $before) 'NoWrite changed outputs'
Assert ($null -eq ($historical.rows|Where-Object thread_id -eq parent).as_of_first_commit) 'Historical cutoff leaked future first-commit reconstruction'
Write-Output "PASS: latest cumulative, ancestry, deduplication, as-of, frozen parent, unknown/non-local child, root separation. Evidence: $root"
