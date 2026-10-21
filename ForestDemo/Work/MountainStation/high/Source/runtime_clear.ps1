$root='D:/github/AstraEffort/ForestDemo'
$mine="$root/Saved/Workers/MountainStation/high"
& "$root/Work/Tools/Run-UnrealIsolated.ps1" -Project "$mine/Project/ForestDemo.uproject" -LogPath "$mine/runtime_clear.log" -TimingPath "$mine/runtime_clear_timing.json" -EditorArguments @("-ExecutePythonScript=$root/Work/MountainStation/high/Source/runtime_only.py",'-RenderOffscreen','-NoSound','-windowed','-ResX=1920','-ResY=1080')
exit $LASTEXITCODE
