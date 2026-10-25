$ErrorActionPreference='Stop'
& 'D:/github/AstraEffort/ForestDemo/Work/Tools/Run-UnrealIsolated.ps1' -Project 'D:/github/AstraEffort/ForestDemo/Saved/Workers/NightMarket/max/NightMarketPrivate.uproject' -LogPath 'D:/github/AstraEffort/ForestDemo/Work/NightMarket/max/Logs/fix_01.log' -TimingPath 'D:/github/AstraEffort/ForestDemo/Work/NightMarket/max/Logs/fix_01_timing.json' -EditorArguments @('-ExecutePythonScript=D:/github/AstraEffort/ForestDemo/Work/NightMarket/max/Source/fix_unreal.py','-RenderOffscreen','-NoSound','-windowed','-ResX=1920','-ResY=1080')
exit $LASTEXITCODE
