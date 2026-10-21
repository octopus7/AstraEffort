$root='D:/github/AstraEffort/ForestDemo'
$mine="$root/Saved/Workers/MountainStation/high"
& "$root/Work/Tools/Run-UnrealIsolated.ps1" -Project "$mine/Project/ForestDemo.uproject" -LogPath "$mine/validate.log" -TimingPath "$mine/validate_timing.json" -EditorArguments @('-run=pythonscript',"-script=$root/Work/MountainStation/high/Source/validate_unreal.py",'-NullRHI')
exit $LASTEXITCODE
