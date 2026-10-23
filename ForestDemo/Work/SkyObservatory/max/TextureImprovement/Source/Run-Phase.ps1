param([Parameter(Mandatory)][int]$Attempt,[string]$Script='build_texture_pass.py')
$ErrorActionPreference='Stop'
$repo='D:/github/AstraEffort'
$scope="$repo/ForestDemo/Work/SkyObservatory/max/TextureImprovement"
$tag=$Attempt.ToString('00')
$scriptPath="$scope/Source/$Script"
& 'C:/Program Files/Epic Games/UE_5.7/Engine/Binaries/ThirdParty/Python3/Win64/python.exe' -m py_compile $scriptPath
if($LASTEXITCODE -ne 0){throw 'Python compile failure; no UE registration'}
& "$repo/ForestDemo/Work/Tools/Run-UnrealIsolated.ps1" -Project "$repo/ForestDemo/Saved/Workers/SkyObservatory/max/Project/SkyObservatoryMax.uproject" -LogPath "$scope/Evidence/ue_phase$tag.log" -TimingPath "$scope/Evidence/ue_timing_$tag.json" -EditorArguments @("-ExecutePythonScript=$scriptPath",'-RenderOffscreen','-NoSound','-NoSplash','-NoSourceControl')
exit $LASTEXITCODE
