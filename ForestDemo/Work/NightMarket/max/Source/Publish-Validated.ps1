$ErrorActionPreference='Stop'
$nmWork='D:/github/AstraEffort/ForestDemo/Work/NightMarket/max'
$nmPrivate='D:/github/AstraEffort/ForestDemo/Saved/Workers/NightMarket/max'
$nmShared='D:/github/AstraEffort/ForestDemo'
$nmValidation=Get-Content -LiteralPath (Join-Path $nmWork 'Evidence/saved_reload_validation.json') -Raw | ConvertFrom-Json
if(!$nmValidation.world_partition_is_null -or $nmValidation.forbidden_game_dependencies.Count -or $nmValidation.null_or_foreign_materials.Count -or $nmValidation.missing_assemblies.Count -or $nmValidation.external_actor_object_or_builtdata_files.Count){throw 'Saved-map validation is not clean.'}
$nmProcesses=@(Get-CimInstance Win32_Process -Filter "Name LIKE 'UnrealEditor%'" | Where-Object { $_.CommandLine -and $_.CommandLine.Replace('\','/').Contains('/Workers/NightMarket/max/') })
if($nmProcesses.Count){throw 'Private NightMarket UE process is still running.'}
$nmShots=Get-Content -LiteralPath (Join-Path $nmWork 'Screenshots/capture_manifest.json') -Raw | ConvertFrom-Json
if($nmShots.screenshots.Count -ne 4){throw 'Four captured views required.'}
foreach($nmShot in $nmShots.screenshots){
 $nmHash=(Get-FileHash -LiteralPath (Join-Path $nmWork ('Screenshots/'+$nmShot.file)) -Algorithm SHA256).Hash.ToLowerInvariant()
 if($nmHash -ne $nmShot.sha256){throw 'Screenshot hash mismatch.'}
}
$nmSource=Join-Path $nmPrivate 'Content/NightMarket/max'
$nmTarget=Join-Path $nmShared 'Content/NightMarket/max'
$nmDeliveries=[Collections.Generic.List[object]]::new()
foreach($nmFile in Get-ChildItem -LiteralPath $nmSource -Recurse -File){
 if($nmFile.Extension -ne '.uasset'){throw ('Unexpected final asset: '+$nmFile.FullName)}
 $nmRelative=$nmFile.FullName.Substring(([IO.Path]::GetFullPath($nmSource)).Length).TrimStart('\','/')
 $nmDestination=Join-Path $nmTarget $nmRelative
 New-Item -ItemType Directory -Force -Path (Split-Path -Parent $nmDestination) | Out-Null
 Copy-Item -LiteralPath $nmFile.FullName -Destination $nmDestination
 $nmA=(Get-FileHash -LiteralPath $nmFile.FullName -Algorithm SHA256).Hash
 $nmB=(Get-FileHash -LiteralPath $nmDestination -Algorithm SHA256).Hash
 if($nmA -ne $nmB){throw ('Published asset differs: '+$nmRelative)}
 $nmDeliveries.Add([ordered]@{path=('Content/NightMarket/max/'+$nmRelative.Replace('\','/'));sha256=$nmB.ToLowerInvariant();bytes=$nmFile.Length;private_published_equal=$true})
}
$nmMapSource=Join-Path $nmPrivate 'Content/Maps/NightMarket_max.umap'
$nmMapTarget=Join-Path $nmShared 'Content/Maps/NightMarket_max.umap'
Copy-Item -LiteralPath $nmMapSource -Destination $nmMapTarget
$nmMapA=(Get-FileHash -LiteralPath $nmMapSource -Algorithm SHA256).Hash
$nmMapB=(Get-FileHash -LiteralPath $nmMapTarget -Algorithm SHA256).Hash
if($nmMapA -ne $nmMapB){throw 'Map hash mismatch.'}
$nmDeliveries.Add([ordered]@{path='Content/Maps/NightMarket_max.umap';sha256=$nmMapB.ToLowerInvariant();bytes=(Get-Item -LiteralPath $nmMapTarget).Length;private_published_equal=$true})
[ordered]@{published_at_utc=[DateTimeOffset]::UtcNow.ToString('o');private_editor_process_count=0;validation_source='Evidence/saved_reload_validation.json';file_count=$nmDeliveries.Count;all_private_published_equal=$true;files=$nmDeliveries} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $nmWork 'Evidence/publication_hashes.json') -Encoding UTF8
Write-Output ('Published and SHA-256 verified '+$nmDeliveries.Count+' owned files. Map SHA-256 '+$nmMapB)
