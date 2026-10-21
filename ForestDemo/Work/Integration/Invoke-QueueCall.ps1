param([Parameter(Mandatory)][string]$InvocationJson)
$ErrorActionPreference = 'Stop'
$call = Get-Content -LiteralPath $InvocationJson -Raw | ConvertFrom-Json
$parameters = @{
    Project = [string]$call.project
    LogPath = [string]$call.log
    TimingPath = [string]$call.timing
    EditorArguments = [string[]]$call.arguments
}
# This helper runs in its own PowerShell process because the existing runner exits.
# JSON preserves each UE argument, including spaces, as a single array item.
& (Join-Path $PSScriptRoot '../Tools/Run-UnrealIsolated.ps1') @parameters
# A nested script's exit sets LASTEXITCODE; explicitly return it to our parent process.
exit $LASTEXITCODE
