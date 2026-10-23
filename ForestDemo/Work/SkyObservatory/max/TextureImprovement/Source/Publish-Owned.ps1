$ErrorActionPreference='Stop'
$repo='D:/github/AstraEffort'
$taskWork="$repo/ForestDemo/Work/SkyObservatory/max/TextureImprovement"
$private="$repo/ForestDemo/Saved/Workers/SkyObservatory/max/Project/Content"
$dest="$repo/ForestDemo/Content"
$destAssets="$dest/SkyObservatory/max"
$mapRelative='Maps/SkyObservatory_max.umap'
$live=@(Get-CimInstance Win32_Process -Filter "Name = 'UnrealEditor.exe' OR Name = 'UnrealEditor-Cmd.exe'" | Where-Object {$_.CommandLine -like '*SkyObservatoryMax.uproject*'})
if($live.Count){throw 'Own private Unreal editor is still running; publication blocked'}
$validation=Get-Content -LiteralPath "$taskWork/Evidence/ue_validation.json" -Raw|ConvertFrom-Json
$materials=Get-Content -LiteralPath "$taskWork/Evidence/saved_material_validation.json" -Raw|ConvertFrom-Json
if($validation.graph_packages -ne 60 -or $validation.required_missing_from_graph.Count -ne 0 -or !$validation.saved_map_reloaded){throw 'Saved map validation incomplete'}
if(!$materials.all_21_materials_have_compiled_shader_statistics -or !$materials.private_package_hashes_before_after_equal){throw 'Final material validation incomplete'}
$expected=@{}
foreach($row in $materials.packages){$expected[$row.relative_path]=$row.sha256}
$privateFiles=@(Get-ChildItem -LiteralPath $private -File -Recurse)
foreach($file in $privateFiles){
 $rel=[IO.Path]::GetRelativePath($private,$file.FullName).Replace('\','/')
 if($rel -ne $mapRelative -and !$rel.StartsWith('SkyObservatory/max/')){throw "Unexpected private package: $rel"}
 if($rel -match '__ExternalActors__|__ExternalObjects__|BuiltData'){throw "Forbidden external/baked package: $rel"}
 if((Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected[$rel]){throw "Changed since captured and validated: $rel"}
}
if($privateFiles.Count -ne 60){throw "Expected 60 files, got $($privateFiles.Count)"}
foreach($package in $validation.placed_required_packages){
 $rel=$package.Substring('/Game/'.Length)+'.uasset'
 if(!(Test-Path -LiteralPath (Join-Path $private $rel))){throw "Missing required package: $package"}
}
$archive=Get-Content -LiteralPath "$repo/ForestDemo/Work/SkyObservatory/max/FirstDelivery/archive_manifest.json" -Raw|ConvertFrom-Json
$baseline=@{};foreach($row in $archive.asset_files){$baseline[$row.relative_path]=$row.sha256.ToLowerInvariant()}
$manifest=[Collections.Generic.List[object]]::new()
foreach($file in $privateFiles){
 $rel=[IO.Path]::GetRelativePath($private,$file.FullName).Replace('\','/')
 $target=[IO.Path]::GetFullPath((Join-Path $dest $rel))
 $allowedAssetRoot=[IO.Path]::GetFullPath($destAssets).TrimEnd('\')+'\'
 $allowedMap=[IO.Path]::GetFullPath((Join-Path $dest $mapRelative))
 if(!$target.StartsWith($allowedAssetRoot,[StringComparison]::OrdinalIgnoreCase) -and $target -ne $allowedMap){throw "Publication scope escape: $target"}
 $previousHash=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
 if($previousHash -ne $baseline[$rel]){throw "Shared owned baseline changed before publication: $rel"}
 [IO.Directory]::CreateDirectory((Split-Path -Parent $target))|Out-Null
 Copy-Item -LiteralPath $file.FullName -Destination $target
 $sourceHash=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
 $publishedHash=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
 if($sourceHash -ne $publishedHash){throw "Published hash mismatch: $rel"}
 $manifest.Add([ordered]@{relative_path=$rel;private_file=$file.FullName;published_file=$target;bytes=$file.Length;baseline_sha256=$previousHash;private_sha256=$sourceHash;published_sha256=$publishedHash;match=$true;changed_from_first_delivery=($sourceHash -ne $previousHash)})
}
$publishedCount=@(Get-ChildItem -LiteralPath $destAssets -Recurse -File).Count+1
if($publishedCount -ne 60){throw "Published package count mismatch: $publishedCount"}
$proof=[ordered]@{published_at_utc=[DateTimeOffset]::UtcNow.ToString('o');own_private_editor_closed=$true;checked_process_filter='UnrealEditor.exe and UnrealEditor-Cmd.exe / own SkyObservatoryMax.uproject only';validated_private_graph_packages=60;file_count=$manifest.Count;all_sha256_match=$true;all_published_hashes_equal_fresh_final_validation=$true;all_previous_shared_hashes_equal_committed_first_delivery=$true;no_external_actor_object_or_builtdata_packages=$true;capture_manifest_sha256=(Get-FileHash -LiteralPath "$taskWork/Screenshots/capture_manifest.json" -Algorithm SHA256).Hash.ToLowerInvariant();saved_material_validation_sha256=(Get-FileHash -LiteralPath "$taskWork/Evidence/saved_material_validation.json" -Algorithm SHA256).Hash.ToLowerInvariant();files=$manifest}
$proof|ConvertTo-Json -Depth 8|Set-Content -LiteralPath "$taskWork/Evidence/publication_manifest.json" -Encoding utf8
Write-Output "PUBLICATION_PASS $($manifest.Count) owned files; all private/published/captured asset SHA256 match"
