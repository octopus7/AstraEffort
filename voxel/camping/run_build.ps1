$ErrorActionPreference = 'Stop'
$campRoot = $PSScriptRoot
$campBlender = 'C:/Program Files/Blender Foundation/Blender 4.5/blender.exe'
$campStarted = [DateTimeOffset]::UtcNow
$campWatch = [Diagnostics.Stopwatch]::StartNew()
$campProcess = Start-Process -FilePath $campBlender -ArgumentList @('--background', '--factory-startup', '-t', '4', '--python-exit-code', '1', '--python', (Join-Path $campRoot 'build.py')) -WorkingDirectory $campRoot -RedirectStandardOutput (Join-Path $campRoot 'build_stdout.log') -RedirectStandardError (Join-Path $campRoot 'build_stderr.log') -WindowStyle Hidden -Wait -PassThru
$campWatch.Stop()
$campTiming = [ordered]@{started_at_utc=$campStarted.ToString('o'); finished_at_utc=[DateTimeOffset]::UtcNow.ToString('o'); elapsed_seconds=$campWatch.Elapsed.TotalSeconds; exit_code=$campProcess.ExitCode; threads=4; factory_startup=$true}
$campTiming | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $campRoot 'build_timing.json') -Encoding UTF8
$campTiming | ConvertTo-Json
exit $campProcess.ExitCode
