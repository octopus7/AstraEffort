param(
    [Parameter(Mandatory)][string]$Project,
    [Parameter(Mandatory)][string]$LogPath,
    [Parameter(Mandatory)][string]$TimingPath,
    [string[]]$EditorArguments = @()
)
$ErrorActionPreference='Stop'
if(!(Test-Path -LiteralPath $Project)){throw "Project not found: $Project"}
. (Join-Path $PSScriptRoot 'AuthoringQueue.ps1')
$projectRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$arguments=@([IO.Path]::GetFullPath($Project),'-unattended','-nop4','-nosplash',('-abslog='+[IO.Path]::GetFullPath($LogPath)))+$EditorArguments
$result=Invoke-AuthoringQueue -Project $Project -LogPath $LogPath -TimingPath $TimingPath -EngineExe 'C:/Program Files/Epic Games/UE_5.7/Engine/Binaries/Win64/UnrealEditor-Cmd.exe' -EngineArguments $arguments -QueueRoot (Join-Path $projectRoot 'Saved/Coordination/UEQueue') -MutexName 'Local\AstraEffort_UE_Authoring' -GuardToken (Join-Path $projectRoot 'Saved/Workers/') -WorkersRoot (Join-Path $projectRoot 'Saved/Workers')
exit $result
