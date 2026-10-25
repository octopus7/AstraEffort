param([ValidateSet('build','layout','polish','terrain','validate','capture')][string]$Phase='build')
$ErrorActionPreference='Stop'
$taskRoot='D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/max'
$scratch='D:/github/AstraEffort/ForestDemo/Saved/Workers/WindmillFarm/max'
$stamp=[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')
if($Phase -eq 'capture'){
    $editorArgs=@('/Game/Maps/WindmillFarm_max','-RenderOffscreen','-NoSound','-Windowed','-ResX=1920','-ResY=1080','-ForceRes','-NoTextureStreaming',('-ExecCmds=py '+$taskRoot+'/Scripts/capture_scene.py'))
}elseif($Phase -in @('build','layout','polish','terrain')){
    $script=if($Phase -eq 'build'){'build_scene.py'}elseif($Phase -eq 'layout'){'repair_layout.py'}elseif($Phase -eq 'terrain'){'refine_terrain.py'}else{'polish_scene.py'}
    $editorArgs=@(('-ExecutePythonScript='+$taskRoot+'/Scripts/'+$script),'-RenderOffscreen','-NoSound','-NoTextureStreaming')
}else{
    $editorArgs=@(('-ExecutePythonScript='+$taskRoot+'/Scripts/validate_scene.py'),'-RenderOffscreen','-NoSound')
}
& 'D:/github/AstraEffort/ForestDemo/Work/Tools/Run-UnrealIsolated.ps1' -Project ($scratch+'/Project/WindmillFarmMax.uproject') -LogPath ($scratch+'/Logs/'+$Phase+'-'+$stamp+'.log') -TimingPath ($taskRoot+'/Evidence/ue-'+$Phase+'-'+$stamp+'-timing.json') -EditorArguments $editorArgs
exit $LASTEXITCODE
