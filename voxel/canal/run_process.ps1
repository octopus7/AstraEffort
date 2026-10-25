param([ValidateSet('build', 'verify')][string]$Stage = 'build', [string]$Asset = '')
$ErrorActionPreference = 'Stop'
$env:PYTHONDONTWRITEBYTECODE = '1'
$themeRoot = $PSScriptRoot
$blenderExe = 'C:/Program Files/Blender Foundation/Blender 4.5/blender.exe'
$stageArguments = @('--background', '--threads', '4', '--factory-startup', '--python-exit-code', '1')
if ($Stage -eq 'build') {
    $stageArguments += @('--python', (Join-Path $themeRoot 'build.py'))
    if ($Asset) { $stageArguments += @('--', '--asset', $Asset) }
} else {
    $stageArguments += @('--python', 'D:/github/AstraEffort/voxel/_tools/verify_theme.py', '--', $themeRoot, (Join-Path $themeRoot 'validation_export.json'))
}
$startUtc = [DateTimeOffset]::UtcNow
$timer = [System.Diagnostics.Stopwatch]::StartNew()
$logTag = $Stage
if ($Asset) { $logTag += '_' + $Asset + '_fix' }
$child = Start-Process -FilePath $blenderExe -ArgumentList $stageArguments -WorkingDirectory 'D:/github/AstraEffort' -WindowStyle Hidden -RedirectStandardOutput (Join-Path $themeRoot ($logTag + '.log')) -RedirectStandardError (Join-Path $themeRoot ($logTag + '.stderr.log')) -Wait -PassThru
$childId = $child.Id
Write-Output ($Stage + ' Blender PID ' + $childId)
$timer.Stop()
$endUtc = [DateTimeOffset]::UtcNow
$result = [ordered]@{
    stage = $Stage
    asset_filter = $Asset
    started_at_utc = $startUtc.ToString('o')
    finished_at_utc = $endUtc.ToString('o')
    started_at_kst = $startUtc.ToOffset([TimeSpan]::FromHours(9)).ToString('o')
    finished_at_kst = $endUtc.ToOffset([TimeSpan]::FromHours(9)).ToString('o')
    elapsed_seconds = $timer.Elapsed.TotalSeconds
    exit_code = $child.ExitCode
    pid = $childId
    threads = 4
    command = @($blenderExe) + $stageArguments
}
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $themeRoot ($logTag + '_timing.json')) -Encoding UTF8
$result | ConvertTo-Json -Depth 5
if ($child.ExitCode -ne 0) { throw "$Stage failed with exit code $($child.ExitCode)" }
