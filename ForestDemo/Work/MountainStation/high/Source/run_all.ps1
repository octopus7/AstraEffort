$root='D:/github/AstraEffort/ForestDemo'
$mine="$root/Saved/Workers/MountainStation/high"
& "$root/Work/Tools/Run-UnrealIsolated.ps1" -Project "$mine/Project/ForestDemo.uproject" -LogPath "$mine/pipeline.log" -TimingPath "$mine/pipeline_timing.json" -EditorArguments @("-ExecutePythonScript=$root/Work/MountainStation/high/Source/run_all.py",'-RenderOffscreen','-NoSound','-windowed','-ResX=1920','-ResY=1080','-ExecCmds=Interchange.FeatureFlags.Import.FBX 0')
exit $LASTEXITCODE
