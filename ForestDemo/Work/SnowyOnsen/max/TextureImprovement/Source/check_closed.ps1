$ErrorActionPreference='Stop'
$project='D:/github/AstraEffort/ForestDemo/Saved/Workers/SnowyOnsen/max/PrivateOnsen/PrivateOnsen.uproject'
$matching=@(Get-CimInstance Win32_Process -Filter "Name LIKE 'UnrealEditor%'" | Where-Object { $_.CommandLine -and $_.CommandLine.Replace('\','/').Contains($project) } | Select-Object ProcessId,Name,CommandLine)
$record=[ordered]@{at_utc=[DateTime]::UtcNow.ToString('o');project=$project;no_matching_processes=($matching.Count -eq 0);matching_processes=$matching;scope='Only processes referencing this worker private project; no process termination'}
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath 'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max/TextureImprovement/Validation/private_editor_closed.json' -Encoding utf8
if($matching.Count -ne 0){throw 'Own private Unreal editor is still active'}
$record | ConvertTo-Json -Depth 8
