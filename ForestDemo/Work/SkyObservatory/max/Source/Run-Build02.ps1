$ErrorActionPreference='Stop'
$repo='D:/github/AstraEffort'
& "$repo/ForestDemo/Work/Tools/Run-UnrealIsolated.ps1" -Project "$repo/ForestDemo/Saved/Workers/SkyObservatory/max/Project/SkyObservatoryMax.uproject" -LogPath "$repo/ForestDemo/Saved/Workers/SkyObservatory/max/Logs/build02.log" -TimingPath "$repo/ForestDemo/Work/SkyObservatory/max/Evidence/ue_timing_02.json" -EditorArguments @('-ExecutePythonScript=D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max/Source/build_unreal.py','-RenderOffscreen','-NoSound','-NoSplash','-NoSourceControl')
exit $LASTEXITCODE
