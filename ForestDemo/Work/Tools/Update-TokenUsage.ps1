param(
    [Parameter(Mandatory)][string]$SessionRoot,
    [string]$SupervisorThreadId = '01a15e52-9373-7cb3-884e-eda6747350f2'
)

$ErrorActionPreference = 'Stop'
$workRoot = Split-Path -Parent $PSScriptRoot
$coord = Get-Content (Join-Path $workRoot 'coordination.json') -Raw | ConvertFrom-Json -DateKind String
$jobs = @($coord.efforts) + @($coord.mountain_station_efforts)
$jobs += [pscustomobject]@{theme='Supervisor'; effort='separate'; threadId=$SupervisorThreadId; status='ongoing'}
$files = @(Get-ChildItem -LiteralPath $SessionRoot -Recurse -Filter '*.jsonl' -File)
$rows = @()
foreach ($job in $jobs) {
    $matches = @($files | Where-Object { $_.Name.EndsWith($job.threadId + '.jsonl') })
    $latest = $null
    $models = [Collections.Generic.HashSet[string]]::new()
    $efforts = [Collections.Generic.HashSet[string]]::new()
    $issues = [Collections.Generic.List[string]]::new()
    $previousTotal = $null
    $count = 0
    $unparsed = 0
    foreach ($file in ($matches | Sort-Object Name)) {
        $stream = [IO.File]::Open($file.FullName, [IO.FileMode]::Open, [IO.FileAccess]::Read, ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
        $reader = [IO.StreamReader]::new($stream)
        try {
            while (($line = $reader.ReadLine()) -ne $null) {
                if (!$line.Contains('"token_count"') -and !$line.Contains('"turn_context"')) { continue }
                try { $event = $line | ConvertFrom-Json -DateKind String }
                catch { $unparsed++; continue }
                if ($event.type -eq 'turn_context') {
                    if ($event.payload.model) { $models.Add($event.payload.model) | Out-Null }
                    if ($event.payload.effort) { $efforts.Add($event.payload.effort) | Out-Null }
                }
                if ($event.type -ne 'event_msg' -or $event.payload.type -ne 'token_count' -or !$event.payload.info.total_token_usage) { continue }
                $count++
                $usage = $event.payload.info.total_token_usage
                if ($null -ne $previousTotal -and $usage.total_tokens -lt $previousTotal) {
                    $issues.Add('Cumulative counter decreased; latest value requires review.')
                }
                $previousTotal = $usage.total_tokens
                if (!$latest -or [DateTimeOffset]::Parse($event.timestamp) -ge [DateTimeOffset]::Parse($latest.timestamp)) { $latest = $event }
            }
        }
        finally { $reader.Dispose() }
    }
    $u = $latest.payload.info.total_token_usage
    if (!$latest) { $issues.Add('No recorded usage available; missing values are unknown, not zero.') }
    if ($matches.Count -ne 1) { $issues.Add('Expected exactly one rollout file; verify source coverage.') }
    if ($u) {
        if ($u.total_tokens -ne ($u.input_tokens + $u.output_tokens)) { $issues.Add('Total differs from input + output.') }
        if ($u.cached_input_tokens -gt $u.input_tokens -or $u.reasoning_output_tokens -gt $u.output_tokens) { $issues.Add('Token subset invariant failed.') }
    }
    $rows += [pscustomobject][ordered]@{
        theme = $job.theme
        effort = $job.effort
        thread_id = $job.threadId
        observed_models = @($models)
        observed_efforts = @($efforts)
        usage_recorded_at_utc = $latest.timestamp
        input_tokens = $(if ($u) { $u.input_tokens } else { $null })
        cached_input_tokens = $(if ($u) { $u.cached_input_tokens } else { $null })
        uncached_input_tokens = $(if ($u) { $u.input_tokens - $u.cached_input_tokens } else { $null })
        cache_write_input_tokens = $(if ($u) { $u.cache_write_input_tokens } else { $null })
        output_tokens = $(if ($u) { $u.output_tokens } else { $null })
        reasoning_output_tokens = $(if ($u) { $u.reasoning_output_tokens } else { $null })
        total_tokens = $(if ($u) { $u.total_tokens } else { $null })
        token_events_observed = $count
        incomplete_metadata_lines = $unparsed
        issues = @($issues)
        source_files = @($matches.Name)
    }
}
$snapshot = [ordered]@{
    captured_at_utc = [DateTimeOffset]::UtcNow.ToString('o')
    method = 'Latest event_msg/token_count/info/total_token_usage per thread; cumulative snapshots are never summed.'
    provisional = $true
    rows = $rows
}
$encoding = [Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText((Join-Path $workRoot 'token_usage.json'), ($snapshot | ConvertTo-Json -Depth 8) + "`n", $encoding)
function Format-Count($value) { if ($null -eq $value) { return 'unknown' }; return ([long]$value).ToString('N0', [Globalization.CultureInfo]::InvariantCulture) }
$kst = [DateTimeOffset]::Parse($snapshot.captured_at_utc).ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-dd HH:mm:ss')
$report = [Collections.Generic.List[string]]::new()
$report.Add('<!-- TOKEN_USAGE_START -->')
$report.Add('## 대화별 토큰 사용량')
$report.Add('')
$report.Add('집계 시각: ' + $kst + ' KST. 진행 중인 대화의 잠정 누적치이며 각 행은 마지막 기록 시점 기준입니다.')
$report.Add('로컬 rollout의 마지막 total_token_usage만 사용하며 누적 스냅샷들을 더하지 않습니다.')
$report.Add('입력에는 캐시 입력이, 출력에는 추론 토큰이 포함됩니다. 총합은 입력+출력입니다.')
$report.Add('비캐시 입력=입력−캐시 입력입니다. 총합에는 반복해서 전달된 문맥이 누적되므로 새로 작성한 글의 분량과 다릅니다.')
$report.Add('이는 로컬 기록의 토큰 계수이며 구독 사용 한도나 실제 청구 금액으로 환산하지 않습니다.')
$report.Add('완료 후 감독자는 최초 완료 집계도 보존하고 이후 수정 비용과 구분합니다.')
$report.Add('')
$report.Add('| 테마 | 강도 | 입력 | 캐시 입력(입력 내) | 비캐시 입력 | 출력 | 추론(출력 내) | 총합 | 기록 시각(KST) |')
$report.Add('|---|---|---:|---:|---:|---:|---:|---:|---|')
foreach ($row in $rows) {
    $recorded = if ($row.usage_recorded_at_utc) { [DateTimeOffset]::Parse($row.usage_recorded_at_utc).ToOffset([TimeSpan]::FromHours(9)).ToString('HH:mm:ss') } else { 'unknown' }
    $report.Add('| ' + $row.theme + ' | ' + $row.effort + ' | ' + (Format-Count $row.input_tokens) + ' | ' + (Format-Count $row.cached_input_tokens) + ' | ' + (Format-Count $row.uncached_input_tokens) + ' | ' + (Format-Count $row.output_tokens) + ' | ' + (Format-Count $row.reasoning_output_tokens) + ' | ' + (Format-Count $row.total_tokens) + ' | ' + $recorded + ' |')
}
$report.Add('')
$report.Add('Supervisor 행은 이 감독 대화 전체(초기 프로젝트 생성 포함)이며 8개 제작 작업의 합계에서 제외합니다. 별도 리뷰 보조 에이전트 사용량은 이 행에 포함하지 않습니다.')
$report.Add('관측된 모델/추론 강도와 카운터 검증 결과는 token_usage.json에 보관합니다. 메타데이터만 추출하며 대화 내용이나 추론 본문은 복사하지 않습니다.')
foreach ($row in $rows) { foreach ($issue in $row.issues) { $report.Add('- ' + $row.theme + '/' + $row.effort + ': ' + $issue) } }
$report.Add('')
$report.Add('공식 프로토콜 참고: [Codex App Server의 thread/tokenUsage/updated](https://learn.chatgpt.com/docs/app-server#turn-events). 실제 수치는 해당 로컬 대화 기록에서 읽었습니다.')
$report.Add('<!-- TOKEN_USAGE_END -->')
$reportPath = Join-Path $workRoot 'SUPERVISION.md'
$text = [IO.File]::ReadAllText($reportPath)
$block = $report -join "`n"
$pattern = '(?s)<!-- TOKEN_USAGE_START -->.*?<!-- TOKEN_USAGE_END -->'
if ([regex]::IsMatch($text, $pattern)) { $text = [regex]::Replace($text, $pattern, [Text.RegularExpressions.MatchEvaluator]{param($m) $block}) }
else { $text = $text.TrimEnd() + "`n`n" + $block + "`n" }
[IO.File]::WriteAllText($reportPath, $text, $encoding)
$rows | Select-Object theme,effort,total_tokens,input_tokens,cached_input_tokens,output_tokens,reasoning_output_tokens,issues | ConvertTo-Json -Depth 4
