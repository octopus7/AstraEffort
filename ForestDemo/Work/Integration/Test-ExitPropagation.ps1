param([Parameter(Mandatory)][string]$EvidenceDirectory)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$prefix = [IO.Path]::GetFullPath((Join-Path $projectRoot 'Saved/Workers/Supervisor')) + [IO.Path]::DirectorySeparatorChar
$evidence = [IO.Path]::GetFullPath($EvidenceDirectory)
if (!$evidence.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'Test evidence must stay in supervisor scratch' }
$fixture = Join-Path $evidence ('ExitPropagation-' + [guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($fixture) | Out-Null
$helper = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'Invoke-QueueCall.ps1') -Raw
# Substitute only the external runner location; execute the actual helper logic.
$helper = $helper.Replace('../Tools/Run-UnrealIsolated.ps1','./Fake-Runner.ps1')
Set-Content -LiteralPath (Join-Path $fixture 'Helper.ps1') -Value $helper -Encoding utf8
$fake = @'
param([string]$Project,[string]$LogPath,[string]$TimingPath,[string[]]$EditorArguments)
$requested = [int]$EditorArguments[0]
@{exit_code=$requested}|ConvertTo-Json|Set-Content -LiteralPath $TimingPath
exit $requested
'@
Set-Content -LiteralPath (Join-Path $fixture 'Fake-Runner.ps1') -Value $fake -Encoding utf8
$pwsh = (Get-Process -Id $PID).Path
$rows = @(foreach ($expected in @(0,37,-1073741819)) {
    $inputPath = Join-Path $fixture ('input-'+$expected+'.json')
    @{project='unused-no-UE';log=(Join-Path $fixture 'unused.log');timing=(Join-Path $fixture ('timing-'+$expected+'.json'));arguments=@([string]$expected)}|ConvertTo-Json|Set-Content -LiteralPath $inputPath
    & $pwsh -NoProfile -File (Join-Path $fixture 'Helper.ps1') -InvocationJson $inputPath
    $observed = $LASTEXITCODE
    [ordered]@{expected=$expected;observed=$observed;passed=($expected -eq $observed)}
})
$report = [ordered]@{tested_at_utc=[DateTimeOffset]::UtcNow.ToString('o');helper_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'Invoke-QueueCall.ps1')).Hash;no_ue_execution=$true;cases=$rows;passed=(@($rows|Where-Object {-not $_.passed}).Count -eq 0)}
$report|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $fixture 'result.json')
$report|ConvertTo-Json -Depth 5
if (!$report.passed) { throw "Exit propagation failed; preserved evidence: $fixture" }
