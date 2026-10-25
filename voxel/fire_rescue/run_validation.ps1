$ErrorActionPreference = 'Stop'
$taskRoot = 'D:/github/AstraEffort/voxel/fire_rescue'
$taskStarted = [DateTimeOffset]::UtcNow
$taskTimer = [Diagnostics.Stopwatch]::StartNew()
$taskProcess = Start-Process -FilePath 'C:/Program Files/Blender Foundation/Blender 4.5/blender.exe' -ArgumentList @('--background', '--factory-startup', '--threads', '4', '--python-exit-code', '1', '--python', 'D:/github/AstraEffort/voxel/_tools/verify_theme.py', '--', $taskRoot, "$taskRoot/validation_export.json") -RedirectStandardOutput "$taskRoot/validation.log" -RedirectStandardError "$taskRoot/validation_stderr.log" -WindowStyle Hidden -PassThru
$taskProcess.Id | Set-Content -LiteralPath "$taskRoot/validation_pid.txt" -Encoding ASCII
$taskProcess.WaitForExit()
$taskExit = $taskProcess.ExitCode
$taskTimer.Stop()
[ordered]@{
    started_at_utc = $taskStarted.ToString('o')
    finished_at_utc = [DateTimeOffset]::UtcNow.ToString('o')
    elapsed_seconds = $taskTimer.Elapsed.TotalSeconds
    exit_code = $taskExit
    threads = 4
    purpose = 'Fresh independent saved VOX parse and BLEND/GLB/FBX imports for all eight variants'
} | ConvertTo-Json | Set-Content -LiteralPath "$taskRoot/validation_process.json" -Encoding UTF8
exit $taskExit
