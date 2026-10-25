param([Parameter(Mandatory)][string]$Phase,[switch]$Render)
$ErrorActionPreference='Stop'
$ownedWork='D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra'
$privateProject='D:/github/AstraEffort/ForestDemo/Saved/Workers/WindmillFarm/ultra/Project/WindmillFarm.uproject'
$scriptFile=(Join-Path $ownedWork ('ue_'+$Phase+'.py')).Replace('\','/')
if(!(Test-Path -LiteralPath $scriptFile)){throw "Missing owned script $scriptFile"}
$ueArguments=@(('-ExecutePythonScript='+$scriptFile),'-NoSound','-NoLiveCoding')
if($Render){$ueArguments+=@('-RenderOffscreen','-windowed','-ResX=1920','-ResY=1080','-d3d12','-sm5')}
else{$ueArguments+='-NullRHI'}
& 'D:/github/AstraEffort/ForestDemo/Work/Tools/Run-UnrealIsolated.ps1' -Project $privateProject -LogPath (Join-Path $ownedWork ('Execution/'+$Phase+'.log')) -TimingPath (Join-Path $ownedWork ('Execution/'+$Phase+'_timing.json')) -EditorArguments $ueArguments
exit $LASTEXITCODE
