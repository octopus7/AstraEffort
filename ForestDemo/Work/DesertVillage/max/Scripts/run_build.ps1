$ErrorActionPreference='Stop'
$taskRoot='D:/github/AstraEffort/ForestDemo/Work/DesertVillage/max'
& 'D:/github/AstraEffort/ForestDemo/Work/Tools/Run-UnrealIsolated.ps1' -Project 'D:/github/AstraEffort/ForestDemo/Saved/Workers/DesertVillage/max/DesertVillage.uproject' -LogPath "$taskRoot/Logs/ue_build.log" -TimingPath "$taskRoot/Logs/ue_build_timing.json" -EditorArguments @('-ExecutePythonScript=D:/github/AstraEffort/ForestDemo/Work/DesertVillage/max/Scripts/build_unreal.py','-RenderOffscreen','-NoAudio','-ResX=1920','-ResY=1080','-windowed')
exit $LASTEXITCODE
