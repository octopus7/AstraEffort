param(
    [Parameter(Mandatory)][string]$SessionRoot,
    [string]$SupervisorThreadId='01a15e52-9373-7cb3-884e-eda6747350f2',
    [string]$WorkRoot=(Split-Path -Parent $PSScriptRoot),
    [string]$AsOfUtc,
    [switch]$NoWrite,
    [switch]$IgnoreComparisonCutoffs
)
$ErrorActionPreference='Stop'
if($IgnoreComparisonCutoffs -and !$NoWrite){throw '-IgnoreComparisonCutoffs is permitted only with -NoWrite.'}
$coord=Get-Content (Join-Path $WorkRoot 'coordination.json') -Raw|ConvertFrom-Json -DateKind String
if(!$NoWrite -and $coord.ultra_self_improvement.comparison_freeze.status -eq 'frozen'){throw 'Comparison accounting is frozen; writing comparison outputs is prohibited.'}
$jobs=@($coord.efforts)+@($coord.mountain_station_efforts)
$jobs+=[pscustomobject]@{theme='Supervisor';effort='separate';threadId=$SupervisorThreadId}
$captured=[DateTimeOffset]::UtcNow
$cutoff=if($AsOfUtc){[DateTimeOffset]::Parse($AsOfUtc)}else{$captured}
$comparisonCutoffs=@{}
if(!$IgnoreComparisonCutoffs){
    foreach($entry in $coord.comparison_token_cutoffs){
        $job=@($jobs|Where-Object threadId -eq $entry.threadId)
        if(!$entry.threadId -or !$entry.as_of_utc -or $job.Count -ne 1 -or $job[0].theme -ne $entry.theme -or $job[0].effort -ne $entry.effort){throw 'Invalid comparison_token_cutoffs identity or missing cutoff.'}
        if($comparisonCutoffs.ContainsKey([string]$entry.threadId)){throw 'Duplicate comparison_token_cutoffs threadId.'}
        $comparisonCutoffs[[string]$entry.threadId]=[DateTimeOffset]::Parse($entry.as_of_utc)
    }
}
$fields=@('input_tokens','cached_input_tokens','uncached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens')
$index=@{};$discoveryIssues=[Collections.Generic.List[string]]::new();$headerProblems=@()
function Open-Reader($path){return [IO.StreamReader]::new([IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete)))}
# Discovery reads only the first session_meta record. Never export its instructions or conversation content.
foreach($file in Get-ChildItem -LiteralPath $SessionRoot -Recurse -Filter '*.jsonl' -File){
    $reader=$null
    try {
        $reader=Open-Reader $file.FullName;$line=$reader.ReadLine()
        if([string]::IsNullOrWhiteSpace($line)){$headerProblems+=@{file=$file.Name;reason='empty_header';timestamp=$null};continue}
        $meta=$line|ConvertFrom-Json -DateKind String
        if($meta.type -ne 'session_meta' -or !$meta.payload.id){$headerProblems+=@{file=$file.Name;reason='unsupported_header';timestamp=$meta.timestamp};continue}
        $p=$meta.payload;$id=[string]$p.id
        $parents=@(@($p.parent_thread_id,$p.source.subagent.thread_spawn.parent_thread_id)|Where-Object {$_}|Select-Object -Unique)
        if(!$index.ContainsKey($id)){$index[$id]=@{id=$id;parents=@();files=@();created=$p.timestamp;kind=$p.thread_source;agent_path=$p.source.subagent.thread_spawn.agent_path;forked_from_id=$p.forked_from_id;metadata_conflict=$false}}
        $entry=$index[$id];$entry.files+=,$file.FullName;$entry.parents=@(@($entry.parents)+@($parents)|Select-Object -Unique)
        if($entry.created -ne $p.timestamp -or $entry.kind -ne $p.thread_source){$entry.metadata_conflict=$true}
    }catch{$headerProblems+=@{file=$file.Name;reason='unreadable_header';timestamp=$null}}
    finally{if($reader){$reader.Dispose()}}
}
$owners=@{};$rootIds=@($jobs.threadId|Select-Object -Unique)
foreach($id in $rootIds){$owners[$id]=$id}
$rootDates=@(foreach($id in $rootIds){if($index.ContainsKey($id) -and $index[$id].created){[DateTimeOffset]::Parse($index[$id].created)}})
$earliestRoot=$rootDates|Sort-Object|Select-Object -First 1
$historicalHeaders=0;$unresolvedHeaders=0
foreach($problem in $headerProblems){
    $knownRoot=@($rootIds|Where-Object {$problem.file.EndsWith([string]$_+'.jsonl')}).Count -gt 0
    $historical=$false
    if(!$knownRoot -and $earliestRoot){
        if($problem.timestamp){try{$historical=[DateTimeOffset]::Parse($problem.timestamp) -lt $earliestRoot}catch{}}
        elseif($problem.file -match '^rollout-(\d{4}-\d{2}-\d{2})T'){
            # Filename dates are local: keep a two-day margin rather than assuming their timezone.
            $historical=[DateTime]::ParseExact($Matches[1],'yyyy-MM-dd',[Globalization.CultureInfo]::InvariantCulture) -lt $earliestRoot.UtcDateTime.Date.AddDays(-1)
        }
    }
    if($historical){$historicalHeaders++}else{$unresolvedHeaders++}
}
if($unresolvedHeaders){$discoveryIssues.Add("$unresolvedHeaders unresolved headers may affect selected-family discovery; unknown coverage, not zero descendants.")}
# Each session belongs to exactly one nearest configured root. forked_from_id is not an ancestry edge.
do{
    $changed=$false
    foreach($id in @($index.Keys)){
        if($owners.ContainsKey($id)){continue};$entry=$index[$id]
        if($entry.parents.Count -eq 1 -and !$entry.metadata_conflict -and $owners.ContainsKey([string]$entry.parents[0])){
            $owners[$id]=$owners[[string]$entry.parents[0]];$changed=$true
        }
    }
}while($changed)
foreach($entry in $index.Values){
    if(($entry.parents.Count -gt 1 -or $entry.metadata_conflict) -and @($entry.parents|Where-Object {$owners.ContainsKey([string]$_)}).Count){$discoveryIssues.Add('Conflicting ancestry/session metadata references a selected family; excluded rather than counted twice.')}
}
$cache=@{}
function Read-MetadataEvents($id){
    if($cache.ContainsKey($id)){return $cache[$id]}
    $data=@{events=@();contexts=@();issues=[Collections.Generic.List[string]]::new();unparsed=0}
    if(!$index.ContainsKey($id)){$data.issues.Add('No identified rollout metadata found.');$cache[$id]=$data;return $data}
    foreach($file in $index[$id].files){
        $reader=$null
        try {
            $reader=Open-Reader $file
            while(($line=$reader.ReadLine()) -ne $null){
                if($line -notmatch '"type"\s*:\s*"(turn_context|token_count)"'){continue}
                try{$e=$line|ConvertFrom-Json -DateKind String}catch{$data.unparsed++;continue}
                if($e.type -eq 'turn_context'){
                    $data.contexts+=@{timestamp=$e.timestamp;model=$e.payload.model;effort=$e.payload.effort}
                }elseif($e.type -eq 'event_msg' -and $e.payload.type -eq 'token_count' -and $e.payload.info.total_token_usage){
                    $data.events+=@{timestamp=$e.timestamp;usage=$e.payload.info.total_token_usage;last=$e.payload.info.last_token_usage}
                }
            }
        }catch{$data.issues.Add('Selected rollout could not be completely read.')}
        finally{if($reader){$reader.Dispose()}}
    }
    $cache[$id]=$data;return $data
}
function Usage-At($id,[DateTimeOffset]$at,$job,$isRoot){
    $data=Read-MetadataEvents $id;$meta=$index[$id]
    $issues=[Collections.Generic.List[string]]::new();foreach($issue in $data.issues){$issues.Add($issue)}
    if($meta.metadata_conflict){$issues.Add('Conflicting session metadata across duplicate rollout files.')}
    $models=[Collections.Generic.HashSet[string]]::new();$efforts=[Collections.Generic.HashSet[string]]::new()
    foreach($context in $data.contexts){if([DateTimeOffset]::Parse($context.timestamp) -le $at){if($context.model){[void]$models.Add($context.model)};if($context.effort){[void]$efforts.Add($context.effort)}}}
    $events=@($data.events|Where-Object {[DateTimeOffset]::Parse($_.timestamp) -le $at}|Sort-Object {[DateTimeOffset]::Parse($_.timestamp)})
    $seen=[Collections.Generic.HashSet[string]]::new();$unique=@()
    foreach($e in $events){$key=$e.timestamp+'|'+($e.usage|ConvertTo-Json -Compress);if($seen.Add($key)){$unique+=,$e}}
    $first=$unique|Select-Object -First 1;$latest=$unique|Select-Object -Last 1;$u=$latest.usage
    $decreases=0;$deltaMismatch=0;$changed=0;$predates=0;$previous=$null
    foreach($e in $unique){
        if($meta.created -and [DateTimeOffset]::Parse($e.timestamp) -lt [DateTimeOffset]::Parse($meta.created)){$predates++}
        if($previous -and $null -ne $e.usage.total_tokens -and $null -ne $previous.total_tokens){
            $delta=$e.usage.total_tokens-$previous.total_tokens
            if($delta -lt 0){$decreases++}
            elseif($delta -gt 0){$changed++;if($null -eq $e.last.total_tokens -or $delta -ne $e.last.total_tokens){$deltaMismatch++}}
        };$previous=$e.usage
    }
    $firstLocal=$first -and $null -ne $first.last.total_tokens -and $first.usage.total_tokens -eq $first.last.total_tokens
    $localVerified=[bool]($firstLocal -and !$predates -and !$decreases -and !$deltaMismatch)
    $eligible=[bool]($u -and !$decreases -and ($isRoot -or $localVerified))
    if(!$u){$issues.Add('No usage recorded at or before cutoff; unknown, not zero.')}
    if($decreases){$issues.Add('Cumulative counter decreased; excluded from additive accounting.')}
    if(!$isRoot -and !$localVerified){$issues.Add('Child-local cumulative scope is unverified; reported counters are excluded from additive accounting.')}
    if($data.unparsed){$issues.Add('Incomplete metadata lines encountered; last complete record may lag.')}
    if(!$models.Count){$issues.Add('No model metadata observed.')};if(!$efforts.Count){$issues.Add('No reasoning-effort metadata observed.')}
    if($isRoot -and $job.theme -ne 'Supervisor'){
        if($models.Count -ne 1 -or !$models.Contains('gpt-6-astra')){$issues.Add('Observed model differs from gpt-6-astra or is mixed/missing.')}
        if($efforts.Count -ne 1 -or !$efforts.Contains($job.effort)){$issues.Add('Observed effort differs from assigned effort or is mixed/missing.')}
    }
    foreach($field in @('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens','total_tokens')){if($null -eq $u.$field){$issues.Add('Missing token field: '+$field)}}
    if($null -ne $u.total_tokens -and $null -ne $u.input_tokens -and $null -ne $u.output_tokens -and $u.total_tokens -ne ($u.input_tokens+$u.output_tokens)){$issues.Add('Total differs from input + output.');$eligible=$false}
    if(($null -ne $u.cached_input_tokens -and $null -ne $u.input_tokens -and $u.cached_input_tokens -gt $u.input_tokens) -or ($null -ne $u.reasoning_output_tokens -and $null -ne $u.output_tokens -and $u.reasoning_output_tokens -gt $u.output_tokens)){$issues.Add('Token subset invariant failed.');$eligible=$false}
    $category=if($isRoot){'configured_parent'}elseif($meta.kind -eq 'guardian_review'){'automatic_approval_review'}else{'delegated_subagent'}
    $row=[ordered]@{thread_id=$id;parent_thread_id=$(if($meta.parents.Count -eq 1){$meta.parents[0]}else{$null});thread_source=$meta.kind;accounting_category=$category;agent_path=$meta.agent_path;forked_from_id=$meta.forked_from_id;session_created_at_utc=$meta.created;observed_models=@($models);observed_efforts=@($efforts);usage_recorded_at_utc=$latest.timestamp;as_of_utc=$at.ToString('o')}
    foreach($field in $fields){$row[$field]=$u.$field}
    $row.uncached_input_tokens=if($null -ne $u.input_tokens -and $null -ne $u.cached_input_tokens){$u.input_tokens-$u.cached_input_tokens}else{$null}
    $row.accounting_eligible=$eligible;$row.child_local_evidence=@{verified=$localVerified;first_total_equals_first_last_usage=[bool]$firstLocal;predating_events=$predates;changed_events=$changed;delta_mismatches=$deltaMismatch;counter_decreases=$decreases}
    $row.token_events_observed=$unique.Count;$row.duplicate_snapshots_removed=$events.Count-$unique.Count;$row.incomplete_metadata_lines=$data.unparsed;$row.issues=@($issues)
    $row.source_files=@($meta.files|ForEach-Object {[IO.Path]::GetFileName($_)})
    return [pscustomobject]$row
}
function Sum-Usage($members){
    $sum=[ordered]@{member_count=@($members).Count;known_subtotal=[ordered]@{};unknown_thread_ids=@($members|Where-Object {!$_.accounting_eligible -or $null -eq $_.total_tokens}|ForEach-Object {$_.thread_id})}
    foreach($field in $fields){
        $known=0L;$complete=$true
        foreach($member in $members){if($member.accounting_eligible -and $null -ne $member.$field){$known+=[long]$member.$field}else{$complete=$false}}
        $sum[$field]=if($complete){$known}else{$null};$sum.known_subtotal[$field]=$known
    }
    $sum.total_tokens_complete=($null -ne $sum.total_tokens)
    return [pscustomobject]$sum
}
$rows=@();$allMembers=@();$creationMembers=@()
foreach($job in $jobs){
    $id=[string]$job.threadId;$effectiveCutoff=$cutoff;$comparisonCutoff=$comparisonCutoffs[$id]
    if($null -ne $comparisonCutoff -and $comparisonCutoff -lt $effectiveCutoff){$effectiveCutoff=$comparisonCutoff}
    $parent=Usage-At $id $effectiveCutoff $job $true
    $parent|Add-Member -NotePropertyName effective_cutoff_utc -NotePropertyValue $effectiveCutoff.ToString('o')
    $parent|Add-Member -NotePropertyName comparison_accounting_cutoff_utc -NotePropertyValue $(if($null -ne $comparisonCutoff){$comparisonCutoff.ToString('o')}else{$null})
    $childIds=@($owners.Keys|Where-Object {$owners[$_] -eq $id -and $_ -ne $id}|Sort-Object)
    $children=@(foreach($childId in $childIds){if(!$index[$childId].created -or [DateTimeOffset]::Parse($index[$childId].created) -le $effectiveCutoff){Usage-At $childId $effectiveCutoff $job $false}})
    $parent|Add-Member -NotePropertyName theme -NotePropertyValue $job.theme
    $parent|Add-Member -NotePropertyName effort -NotePropertyValue $job.effort
    $parent|Add-Member -NotePropertyName descendants -NotePropertyValue $children
    $parent|Add-Member -NotePropertyName descendant_category_counts -NotePropertyValue @{
        automatic_approval_review=@($children|Where-Object accounting_category -eq automatic_approval_review).Count
        delegated_subagent=@($children|Where-Object accounting_category -eq delegated_subagent).Count
    }
    $parent|Add-Member -NotePropertyName descendant_usage -NotePropertyValue (Sum-Usage $children)
    $members=@($parent)+@($children)
    $parent|Add-Member -NotePropertyName combined_usage -NotePropertyValue (Sum-Usage $members)
    # Preserve the previously frozen parent object verbatim; do not replace it with a later or reconstructed value.
    $parent|Add-Member -NotePropertyName frozen_parent_usage -NotePropertyValue $job.token_usage_at_first_delivery
    $parent|Add-Member -NotePropertyName frozen_parent_captured_at_utc -NotePropertyValue $job.token_usage_frozen_at_utc
    $firstCommit=$null
    if($job.first_commit_at_utc -and [DateTimeOffset]::Parse($job.first_commit_at_utc) -le $effectiveCutoff){
        $firstAt=[DateTimeOffset]::Parse($job.first_commit_at_utc)
        $firstParent=Usage-At $id $firstAt $job $true
        $firstChildren=@(foreach($childId in $childIds){if(!$index[$childId].created -or [DateTimeOffset]::Parse($index[$childId].created) -le $firstAt){Usage-At $childId $firstAt $job $false}})
        $firstCommit=@{cutoff_utc=$firstAt.ToString('o');method='Latest recorded snapshot at or before first commit; not an exact transaction-time measurement.';parent_usage=$firstParent;descendants=$firstChildren;descendant_usage=(Sum-Usage $firstChildren);combined_usage=(Sum-Usage (@($firstParent)+@($firstChildren)))}
    }
    $parent|Add-Member -NotePropertyName as_of_first_commit -NotePropertyValue $firstCommit
    $rows+=,$parent;$allMembers+=$members;if($job.theme -ne 'Supervisor'){$creationMembers+=$members}
}
$snapshot=[ordered]@{
    schema_version=2;captured_at_utc=$captured.ToString('o');as_of_utc=$cutoff.ToString('o');provisional=$true
    comparison_cutoffs_ignored=[bool]$IgnoreComparisonCutoffs
    method='Latest cumulative token_count per unique thread, with identified descendants assigned to one nearest configured root. No cumulative snapshot summing. Parent fields retain their original parent-only meaning.'
    scope='Configured creation chats and supervisor, plus locally identified delegated subagents and automatic guardian approval-review descendants. Metadata discovery cannot prove absence of unavailable rollouts. External CLI/model calls and image-generation usage are not included in these local counters. No conversation or reasoning text is exported.'
    discovery_issues=@($discoveryIssues|Select-Object -Unique)
    discovery_header_summary=@{historical_outside_family_window=$historicalHeaders;unresolved_in_scope_or_unknown=$unresolvedHeaders;earliest_configured_root_utc=$(if($earliestRoot){$earliestRoot.ToString('o')}else{$null});historical_rule='Legacy header timestamps before all configured roots, or unknown filename dates at least two calendar days earlier; known root filenames are never skipped as historical.'}
    rows=$rows;creation_jobs_usage=(Sum-Usage $creationMembers);all_roots_usage=(Sum-Usage $allMembers)
}
function Format-Count($value){if($null -eq $value){return 'unknown'};return ([long]$value).ToString('N0',[Globalization.CultureInfo]::InvariantCulture)}
$report=[Collections.Generic.List[string]]::new()
$report.Add('<!-- TOKEN_USAGE_START -->');$report.Add('## 대화별 토큰 사용량');$report.Add('')
$report.Add('집계 시각: '+$captured.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-dd HH:mm:ss')+' KST. 로컬 마지막 누적 기록 기준 잠정치입니다.')
$report.Add('부모와 식별된 하위 대화를 별도로 표시하고 thread ID마다 한 번만 합산합니다. 자동 guardian 승인 검토(automatic_approval_review)는 위임 제작 에이전트(delegated_subagent)와 구분합니다. 캐시 입력은 입력에, 추론은 출력에 이미 포함됩니다. 누적 스냅샷끼리는 더하지 않습니다.')
$report.Add('반복 문맥도 포함되는 로컬 계수이며 구독 한도나 청구 금액으로 환산하지 않습니다. 누락·범위 미확인 토큰은 unknown이며 알려진 부분합만 별도 제공합니다.')
$report.Add('외부 CLI의 별도 모델 호출 및 이미지 생성 사용량은 이 로컬 토큰 계수에 포함되지 않습니다.')
$report.Add('')
if($comparisonCutoffs.Count){
    $report.Add('comparison accounting cutoff: 아래 대화와 식별된 후손은 지정 시각과 전체 조회 시각 중 이른 시각까지 집계합니다. 나머지 대화는 전체 조회 시각을 따릅니다.')
    $report.Add('')
    $report.Add('| 테마 | 강도 | 지정 cutoff (UTC) | 유효 cutoff (UTC) |')
    $report.Add('|---|---|---|---|')
    foreach($row in $rows|Where-Object comparison_accounting_cutoff_utc){$report.Add('| '+$row.theme+' | '+$row.effort+' | '+$row.comparison_accounting_cutoff_utc+' | '+$row.effective_cutoff_utc+' |')}
    $report.Add('')
}
$report.Add('| 테마 | 강도 | 부모 총합 | 후손 수 | 후손 총합 | 부모+후손 총합 | 알려진 부분합 |')
$report.Add('|---|---|---:|---:|---:|---:|---:|')
foreach($row in $rows){$report.Add('| '+$row.theme+' | '+$row.effort+' | '+(Format-Count $row.total_tokens)+' | '+$row.descendants.Count+' | '+(Format-Count $row.descendant_usage.total_tokens)+' | '+(Format-Count $row.combined_usage.total_tokens)+' | '+(Format-Count $row.combined_usage.known_subtotal.total_tokens)+' |')}
$report.Add('')
$report.Add('부모+후손 토큰 구성입니다. 캐시 입력과 추론은 각각 입력·출력의 부분집합입니다.')
$report.Add('')
$report.Add('| 테마 | 강도 | 입력 | 캐시 입력(입력 내) | 비캐시 입력 | 출력 | 추론(출력 내) | 총합 |')
$report.Add('|---|---|---:|---:|---:|---:|---:|---:|')
foreach($row in $rows){$u=$row.combined_usage;$report.Add('| '+$row.theme+' | '+$row.effort+' | '+(Format-Count $u.input_tokens)+' | '+(Format-Count $u.cached_input_tokens)+' | '+(Format-Count $u.uncached_input_tokens)+' | '+(Format-Count $u.output_tokens)+' | '+(Format-Count $u.reasoning_output_tokens)+' | '+(Format-Count $u.total_tokens)+' |')}
$report.Add('')
$report.Add('후손 종류별 개수이며, 손자 이하도 해당 제작 대화에 한 번만 귀속됩니다.')
$report.Add('')
$report.Add('| 테마 | 강도 | 자동 승인 검토 | 위임 보조 에이전트 | 전체 후손 |')
$report.Add('|---|---|---:|---:|---:|')
foreach($row in $rows){$report.Add('| '+$row.theme+' | '+$row.effort+' | '+$row.descendant_category_counts.automatic_approval_review+' | '+$row.descendant_category_counts.delegated_subagent+' | '+$row.descendants.Count+' |')}
$report.Add('')
$report.Add('제작 작업 합계(감독 제외): '+(Format-Count $snapshot.creation_jobs_usage.total_tokens)+'. 감독 포함 전체: '+(Format-Count $snapshot.all_roots_usage.total_tokens)+'.')
$report.Add('Supervisor에는 초기 프로젝트 생성 및 그 감독 대화의 후손이 포함됩니다. 독립 제작 대화 8개는 감독의 후손으로 다시 더하지 않습니다.')
$report.Add('최초 납품 부모 고정값은 frozen_parent_usage에 보존합니다. 최초 커밋 시각 이전 마지막 부모·후손 스냅샷 재구성은 as_of_first_commit에 따로 저장하며 정확한 커밋 순간의 사용량이라고 주장하지 않습니다.')
$report.Add('보존 부모 값의 기록 시각과 커밋 시각은 다를 수 있습니다. 따라서 보존 부모에 커밋 기준 후손을 섞어 합산하지 않고, 동일 커밋 기준으로 재구성한 합계를 별도로 제시합니다.')
$report.Add('')
$report.Add('| 테마 | 강도 | 최초 커밋 기준(KST) | 보존 부모 총합 | 당시 재구성 부모 | 당시 후손 | 당시 부모+후손 |')
$report.Add('|---|---|---|---:|---:|---:|---:|')
foreach($row in $rows|Where-Object theme -ne Supervisor){
    $f=$row.as_of_first_commit;$when=if($f){[DateTimeOffset]::Parse($f.cutoff_utc).ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-dd HH:mm:ss')}else{'미커밋/기준시각 이후'}
    $report.Add('| '+$row.theme+' | '+$row.effort+' | '+$when+' | '+(Format-Count $row.frozen_parent_usage.total_tokens)+' | '+(Format-Count $f.parent_usage.total_tokens)+' | '+(Format-Count $f.descendant_usage.total_tokens)+' | '+(Format-Count $f.combined_usage.total_tokens)+' |')
}
$report.Add('')
$report.Add('발견 범위: 선택한 대화 시작 이전의 역사적 헤더 '+$historicalHeaders+'개는 대상 계보 밖으로 분리했습니다. 현재 범위 또는 시점 불명 헤더 '+$unresolvedHeaders+'개는 발견 범위 미확인으로 남깁니다.')
$report.Add('모델·effort, ancestry, child-local 카운터 증거, 입력/캐시/출력/추론 및 unknown 부분합은 token_usage.json을 참고하세요. 접근할 수 없는 후손 기록의 부재까지 보장하지 않습니다.')
foreach($issue in $snapshot.discovery_issues){$report.Add('- '+$issue)}
foreach($row in $rows){foreach($member in @($row)+@($row.descendants)){foreach($issue in $member.issues){$report.Add('- '+$row.theme+'/'+$row.effort+' ['+$member.thread_id+']: '+$issue)}}}
$report.Add('<!-- TOKEN_USAGE_END -->')
if(!$NoWrite){
    # Recheck after discovery so a concurrent freeze/cutoff update cannot knowingly publish stale accounting.
    $latestCoord=Get-Content (Join-Path $WorkRoot 'coordination.json') -Raw|ConvertFrom-Json -DateKind String
    if($latestCoord.ultra_self_improvement.comparison_freeze.status -eq 'frozen'){throw 'Comparison accounting is frozen; writing comparison outputs is prohibited.'}
    if(($latestCoord.comparison_token_cutoffs|ConvertTo-Json -Depth 8 -Compress) -ne ($coord.comparison_token_cutoffs|ConvertTo-Json -Depth 8 -Compress)){throw 'Comparison accounting cutoffs changed during collection; rerun before writing.'}
    $encoding=[Text.UTF8Encoding]::new($false)
    [IO.File]::WriteAllText((Join-Path $WorkRoot 'token_usage.json'),($snapshot|ConvertTo-Json -Depth 20)+"`n",$encoding)
    $reportPath=Join-Path $WorkRoot 'SUPERVISION.md';$text=[IO.File]::ReadAllText($reportPath);$block=$report -join "`n"
    $pattern='(?s)<!-- TOKEN_USAGE_START -->.*?<!-- TOKEN_USAGE_END -->'
    if([regex]::IsMatch($text,$pattern)){$text=[regex]::Replace($text,$pattern,[Text.RegularExpressions.MatchEvaluator]{param($m)$block})}else{$text=$text.TrimEnd()+"`n`n"+$block+"`n"}
    [IO.File]::WriteAllText($reportPath,$text,$encoding)
}
$snapshot|ConvertTo-Json -Depth 20
