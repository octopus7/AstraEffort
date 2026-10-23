param([Parameter(Mandatory)][int]$Attempt,[string]$Script='build_unreal.py')
$ErrorActionPreference='Stop'
$repo='D:/github/AstraEffort'
$tag=$Attempt.ToString('00')
$scriptPath="$repo/ForestDemo/Work/SkyObservatory/max/Source/$Script"
& 'C:/Program Files/Epic Games/UE_5.7/Engine/Binaries/ThirdParty/Python3/Win64/python.exe' -m py_compile $scriptPath
if($LASTEXITCODE -ne 0){throw 'Python source compilation failed; not registering Unreal'}
& "$repo/ForestDemo/Work/Tools/Run-UnrealIsolated.ps1" -Project "$repo/ForestDemo/Saved/Workers/SkyObservatory/max/Project/SkyObservatoryMax.uproject" -LogPath "$repo/ForestDemo/Saved/Workers/SkyObservatory/max/Logs/phase$tag.log" -TimingPath "$repo/ForestDemo/Work/SkyObservatory/max/Evidence/ue_timing_$tag.json" -EditorArguments @("-ExecutePythonScript=$scriptPath",'-RenderOffscreen','-NoSound','-NoSplash','-NoSourceControl')
exit $LASTEXITCODE
