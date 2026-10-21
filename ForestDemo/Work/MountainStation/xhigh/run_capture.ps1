$ErrorActionPreference='Stop'
$work='D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh'
$scratch='D:/github/AstraEffort/ForestDemo/Saved/Workers/MountainStation/xhigh'
& 'D:/github/AstraEffort/ForestDemo/Work/Tools/Run-UnrealIsolated.ps1' -Project "$scratch/Project/ForestDemo.uproject" -LogPath "$scratch/Logs/capture.log" -TimingPath "$scratch/Timings/capture.json" -EditorArguments @("-ExecutePythonScript=$work/capture_bootstrap.py",'-RenderOffscreen','-nosound','-windowed','-ResX=1920','-ResY=1080')
