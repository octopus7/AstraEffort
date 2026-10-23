$ErrorActionPreference='Stop'
$repo='D:/github/AstraEffort'
& "$repo/ForestDemo/Work/Tools/Run-UnrealIsolated.ps1" -Project "$repo/ForestDemo/Saved/Workers/SkyObservatory/max/Project/SkyObservatoryMax.uproject" -LogPath "$repo/ForestDemo/Saved/Workers/SkyObservatory/max/Logs/build01.log" -TimingPath "$repo/ForestDemo/Work/SkyObservatory/max/Evidence/ue_timing_01.json" -EditorArguments @('-ExecutePythonScript=D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max/Source/build_unreal.py','-RenderOffscreen','-NoSound','-NoSplash','-NoSourceControl','-NoShaderWorker')
exit $LASTEXITCODE
