param([Parameter(Mandatory)][string]$Phase)
$ErrorActionPreference='Stop'
$workRoot=$PSScriptRoot
$repoRoot=[IO.Path]::GetFullPath((Join-Path $workRoot '../../../..'))
$projectPath=Join-Path $repoRoot 'ForestDemo/Saved/Workers/RainyCanal/ultra/Project/RainyCanal.uproject'
$scriptPath=Join-Path $workRoot ('ue_'+$Phase+'.py')
if(!(Test-Path -LiteralPath $scriptPath)){throw "Missing phase script: $scriptPath"}
$editorArgs=@(('-ExecutePythonScript='+$scriptPath),'-RenderOffscreen','-d3d12','-sm5','-windowed','-ResX=1920','-ResY=1080','-NoSound','-NoSplash')
& (Join-Path $repoRoot 'ForestDemo/Work/Tools/Run-UnrealIsolated.ps1') -Project $projectPath -LogPath (Join-Path $workRoot ('Execution/'+$Phase+'.log')) -TimingPath (Join-Path $workRoot ('Execution/'+$Phase+'_timing.json')) -EditorArguments $editorArgs
exit $LASTEXITCODE
