param(
    [Parameter(Mandatory)][string]$Project,
    [Parameter(Mandatory)][string]$LogPath,
    [Parameter(Mandatory)][string]$TimingPath,
    [string[]]$EditorArguments = @()
)

$ErrorActionPreference = 'Stop'
$engineExe = 'C:/Program Files/Epic Games/UE_5.7/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
if (!(Test-Path -LiteralPath $Project)) { throw "Project not found: $Project" }
foreach ($outputPath in @($LogPath, $TimingPath)) {
    $outputDir = Split-Path -Parent ([IO.Path]::GetFullPath($outputPath))
    [IO.Directory]::CreateDirectory($outputDir) | Out-Null
}
$waitStarted = [DateTimeOffset]::UtcNow
$acquired = $false
$mutex = [Threading.Mutex]::new($false, 'Local\AstraEffort_UE_Authoring')
$process = $null
$runStarted = $null
$exitCode = 1
try {
    Write-Output 'Waiting for the shared Unreal execution slot; creative files remain isolated.'
    try { $acquired = $mutex.WaitOne() }
    catch [Threading.AbandonedMutexException] { $acquired = $true }
    $runStarted = [DateTimeOffset]::UtcNow
    $startInfo = [Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $engineExe
    $startInfo.WorkingDirectory = Split-Path -Parent ([IO.Path]::GetFullPath($Project))
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.WindowStyle = [Diagnostics.ProcessWindowStyle]::Hidden
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    foreach ($argument in @($Project, '-unattended', '-nop4', '-nosplash', ('-abslog=' + [IO.Path]::GetFullPath($LogPath))) + $EditorArguments) {
        $startInfo.ArgumentList.Add($argument)
    }
    $process = [Diagnostics.Process]::Start($startInfo)
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    $stdoutText = $stdoutTask.GetAwaiter().GetResult()
    $stderrText = $stderrTask.GetAwaiter().GetResult()
    $exitCode = $process.ExitCode
    if ($exitCode -ne 0) {
        Write-Output ($stdoutText | Select-Object -Last 1)
        Write-Output $stderrText
    }
}
finally {
    $finished = [DateTimeOffset]::UtcNow
    $timing = [ordered]@{
        wait_started_at_utc = $waitStarted.ToString('o')
        run_started_at_utc = $(if ($runStarted) { $runStarted.ToString('o') } else { $null })
        finished_at_utc = $finished.ToString('o')
        wait_seconds = $(if ($runStarted) { ($runStarted - $waitStarted).TotalSeconds } else { ($finished - $waitStarted).TotalSeconds })
        execution_seconds = $(if ($runStarted) { ($finished - $runStarted).TotalSeconds } else { 0 })
        exit_code = $exitCode
        project = $Project
        log = $LogPath
    }
    if ($process) { $process.Dispose() }
    if ($acquired) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
    [IO.File]::WriteAllText([IO.Path]::GetFullPath($TimingPath), ($timing | ConvertTo-Json) + "`n", [Text.UTF8Encoding]::new($false))
    Write-Output ($timing | ConvertTo-Json -Compress)
}
exit $exitCode
