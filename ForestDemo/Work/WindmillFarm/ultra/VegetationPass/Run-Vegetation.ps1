param([Parameter(Mandatory)][string]$Phase)
$ErrorActionPreference='Stop'
$passWork='D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass'
$privateProject='D:/github/AstraEffort/ForestDemo/Saved/Workers/WindmillFarm/ultra/Project/WindmillFarm.uproject'
$scriptFile=(Join-Path $passWork ('ue_'+$Phase+'.py')).Replace('\','/')
if(!(Test-Path -LiteralPath $scriptFile)){throw "Missing owned script $scriptFile"}
$ueArguments=@(('-ExecutePythonScript='+$scriptFile),'-NoSound','-NoLiveCoding','-RenderOffscreen','-windowed','-ResX=1920','-ResY=1080','-d3d12','-sm5')
& 'D:/github/AstraEffort/ForestDemo/Work/Tools/Run-UnrealIsolated.ps1' -Project $privateProject -LogPath (Join-Path $passWork ('Execution/'+$Phase+'.log')) -TimingPath (Join-Path $passWork ('Execution/'+$Phase+'_timing.json')) -EditorArguments $ueArguments
exit $LASTEXITCODE
