param([string]$Attempt='01')
$ErrorActionPreference='Stop'
& 'D:/github/AstraEffort/ForestDemo/Work/Tools/Run-UnrealIsolated.ps1' -Project 'D:/github/AstraEffort/ForestDemo/Saved/Workers/NightMarket/max/NightMarketPrivate.uproject' -LogPath ('D:/github/AstraEffort/ForestDemo/Work/NightMarket/max/Logs/capture_'+$Attempt+'.log') -TimingPath ('D:/github/AstraEffort/ForestDemo/Work/NightMarket/max/Logs/capture_'+$Attempt+'_timing.json') -EditorArguments @('-ExecutePythonScript=D:/github/AstraEffort/ForestDemo/Work/NightMarket/max/Source/capture_validate.py','-RenderOffscreen','-NoSound','-NoSplash','-NoLoadingScreen','-windowed','-ResX=1920','-ResY=1080')
exit $LASTEXITCODE
