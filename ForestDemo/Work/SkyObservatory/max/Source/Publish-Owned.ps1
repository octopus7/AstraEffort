$ErrorActionPreference='Stop'
$repo='D:/github/AstraEffort'
$taskWork="$repo/ForestDemo/Work/SkyObservatory/max"
$private="$repo/ForestDemo/Saved/Workers/SkyObservatory/max/Project/Content"
$dest="$repo/ForestDemo/Content"
$privateAssets="$private/SkyObservatory/max"
$destAssets="$dest/SkyObservatory/max"
$mapRelative='Maps/SkyObservatory_max.umap'
$live=@(Get-CimInstance Win32_Process -Filter "Name = 'UnrealEditor-Cmd.exe' AND CommandLine LIKE '%SkyObservatoryMax.uproject%'")
if($live.Count){throw 'Own private Unreal editor is still running; publication blocked'}
$validation=Get-Content -LiteralPath "$taskWork/Evidence/ue_validation.json" -Raw|ConvertFrom-Json
if($validation.graph_packages -ne 60 -or $validation.required_missing_from_graph.Count -ne 0 -or !$validation.saved_map_reloaded){throw 'Saved map validation incomplete'}
$privateFiles=@(Get-ChildItem -LiteralPath $private -File -Recurse)
foreach($file in $privateFiles){
 $rel=[IO.Path]::GetRelativePath($private,$file.FullName).Replace('\','/')
 if($rel -ne $mapRelative -and !$rel.StartsWith('SkyObservatory/max/')){throw "Unexpected private content package: $rel"}
 if($rel -match '__ExternalActors__|__ExternalObjects__|BuiltData'){throw "Forbidden external/baked package: $rel"}
}
if($privateFiles.Count -ne 60){throw "Expected 60 final files, got $($privateFiles.Count)"}
foreach($package in $validation.placed_required_packages){
 $rel=$package.Substring('/Game/'.Length)+'.uasset'
 if(!(Test-Path -LiteralPath (Join-Path $private $rel))){throw "Missing required package: $package"}
}
$manifest=[Collections.Generic.List[object]]::new()
foreach($file in $privateFiles){
 $rel=[IO.Path]::GetRelativePath($private,$file.FullName)
 $target=[IO.Path]::GetFullPath((Join-Path $dest $rel))
 $allowedAssetRoot=[IO.Path]::GetFullPath($destAssets).TrimEnd('\')+'\'
 $allowedMap=[IO.Path]::GetFullPath((Join-Path $dest $mapRelative))
 if(!$target.StartsWith($allowedAssetRoot,[StringComparison]::OrdinalIgnoreCase) -and $target -ne $allowedMap){throw "Publication scope escape: $target"}
 [IO.Directory]::CreateDirectory((Split-Path -Parent $target))|Out-Null
 Copy-Item -LiteralPath $file.FullName -Destination $target
 $sourceHash=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
 $publishedHash=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
 if($sourceHash -ne $publishedHash){throw "Published hash mismatch: $rel"}
 $manifest.Add([ordered]@{relative_path=$rel.Replace('\','/');private_file=$file.FullName;published_file=$target;bytes=$file.Length;private_sha256=$sourceHash;published_sha256=$publishedHash;match=$true})
}
$proof=[ordered]@{published_at_utc=[DateTimeOffset]::UtcNow.ToString('o');own_private_editor_closed=$true;checked_process_filter="UnrealEditor-Cmd.exe / own SkyObservatoryMax.uproject only";validated_private_graph_packages=$validation.graph_packages;file_count=$manifest.Count;all_sha256_match=$true;no_external_actor_object_or_builtdata_packages=$true;files=$manifest}
$proof|ConvertTo-Json -Depth 8|Set-Content -LiteralPath "$taskWork/Evidence/publication_manifest.json" -Encoding utf8
Write-Output "PUBLICATION_PASS $($manifest.Count) owned files; all private/published SHA256 match"
