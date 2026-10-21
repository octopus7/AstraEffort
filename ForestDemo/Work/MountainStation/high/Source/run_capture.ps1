$root='D:/github/AstraEffort/ForestDemo'
$mine="$root/Saved/Workers/MountainStation/high"
& "$root/Work/Tools/Run-UnrealIsolated.ps1" -Project "$mine/Project/ForestDemo.uproject" -LogPath "$mine/capture.log" -TimingPath "$mine/capture_timing.json" -EditorArguments @("-ExecutePythonScript=$root/Work/MountainStation/high/Source/run_capture.py",'-RenderOffscreen','-NoSound','-windowed','-ResX=1920','-ResY=1080')
exit $LASTEXITCODE
