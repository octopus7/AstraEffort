$ErrorActionPreference='Stop'
$work='D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh'
$scratch='D:/github/AstraEffort/ForestDemo/Saved/Workers/MountainStation/xhigh'
while (!(Test-Path -LiteralPath "$work/SourceArt/geometry_manifest.json")) { Start-Sleep -Seconds 5 }
& 'D:/github/AstraEffort/ForestDemo/Work/Tools/Run-UnrealIsolated.ps1' -Project "$scratch/Project/ForestDemo.uproject" -LogPath "$scratch/Logs/build.log" -TimingPath "$scratch/Timings/build.json" -EditorArguments @('-run=pythonscript',"-script=$work/build_scene.py",'-NullRHI','-nosound')
