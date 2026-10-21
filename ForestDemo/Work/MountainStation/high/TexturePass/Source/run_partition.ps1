$r='D:/github/AstraEffort/ForestDemo';$s="$r/Saved/Workers/MountainStation/high";$w="$r/Work/MountainStation/high/TexturePass"
& "$r/Work/Tools/Run-UnrealIsolated.ps1" -Project "$s/Project/ForestDemo.uproject" -LogPath "$s/texture_partition.log" -TimingPath "$w/partition_timing.json" -EditorArguments @("-ExecutePythonScript=$w/Source/check_partition.py",'-RenderOffscreen','-NoSound','-windowed','-ResX=1920','-ResY=1080')
exit $LASTEXITCODE



