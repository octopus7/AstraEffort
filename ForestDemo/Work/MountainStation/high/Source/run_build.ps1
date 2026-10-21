$ErrorActionPreference='Stop'
$root='D:/github/AstraEffort/ForestDemo'
$mine="$root/Saved/Workers/MountainStation/high"
& "$root/Work/Tools/Run-UnrealIsolated.ps1" -Project "$mine/Project/ForestDemo.uproject" -LogPath "$mine/build.log" -TimingPath "$mine/build_timing.json" -EditorArguments @('-run=pythonscript',"-script=$root/Work/MountainStation/high/Source/build_unreal.py",'-NullRHI')
exit $LASTEXITCODE
