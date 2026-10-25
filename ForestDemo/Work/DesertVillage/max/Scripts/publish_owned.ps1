$ErrorActionPreference='Stop'
$repo='D:/github/AstraEffort'
$work=Join-Path $repo 'ForestDemo/Work/DesertVillage/max'
$scratch=Join-Path $repo 'ForestDemo/Saved/Workers/DesertVillage/max'
$project=(Join-Path $scratch 'DesertVillage.uproject').Replace('\','/')
$live=@(Get-CimInstance Win32_Process -Filter "Name = 'UnrealEditor-Cmd.exe' OR Name = 'UnrealEditor.exe'" | Where-Object {$_.CommandLine -and ($_.CommandLine -replace '\\','/').Contains($project,[StringComparison]::OrdinalIgnoreCase)})
if($live.Count){throw 'Own private Unreal editor is still running; no publication allowed.'}
$validation=Get-Content -LiteralPath "$work/Validation/saved_map_validation.json" -Raw | ConvertFrom-Json
if(!$validation.passed -or !$validation.fresh_read_only_final_session){throw 'Final saved-map validation is not a fresh pass.'}
$timing=Get-Content -LiteralPath "$work/Logs/ue_final_verify_timing.json" -Raw | ConvertFrom-Json -DateKind String
if($timing.exit_code -ne 0){throw 'Final private editor did not close successfully.'}
$sourceRoot=Join-Path $scratch 'Content/DesertVillage/max'
$targetRoot=Join-Path $repo 'ForestDemo/Content/DesertVillage/max'
$sourceMap=Join-Path $scratch 'Content/Maps/DesertVillage_max.umap'
$targetMap=Join-Path $repo 'ForestDemo/Content/Maps/DesertVillage_max.umap'
foreach($path in @($sourceRoot,$targetRoot,$sourceMap,$targetMap)){
    $resolved=[IO.Path]::GetFullPath($path).Replace('\','/')
    if(!$resolved.StartsWith($repo+'/',[StringComparison]::OrdinalIgnoreCase)){throw "Path escaped workspace: $resolved"}
}
$privateContent=Join-Path $scratch 'Content'
$disallowed=@(Get-ChildItem -LiteralPath $privateContent -Recurse -File | Where-Object {$_.FullName -match '__ExternalActors|__ExternalObjects|_BuiltData' -or ($_.Extension -eq '.umap' -and $_.FullName -ne ([IO.Path]::GetFullPath($sourceMap)))})
if($disallowed.Count){throw 'Unexpected private external package, BuiltData, or other map.'}
if(Test-Path -LiteralPath $targetRoot){throw 'Destination asset root unexpectedly exists before first publication.'}
if(Test-Path -LiteralPath $targetMap){throw 'Destination map unexpectedly exists before first publication.'}
$files=@(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File)
if($files.Count -ne 76 -or @($files | Where-Object {$_.Extension -ne '.uasset'}).Count){throw 'Unexpected owned asset inventory.'}
$records=@()
foreach($file in $files){
    $relative=[IO.Path]::GetRelativePath($sourceRoot,$file.FullName)
    $dest=Join-Path $targetRoot $relative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
    Copy-Item -LiteralPath $file.FullName -Destination $dest
    $sourceHash=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $targetHash=(Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash.ToLowerInvariant()
    if($sourceHash -ne $targetHash){throw "Copied file hash mismatch: $relative"}
    $records += [ordered]@{path=[IO.Path]::GetRelativePath($repo,$dest).Replace('\','/');source=$file.FullName;sha256=$sourceHash;destination_sha256=$targetHash;size_bytes=$file.Length;hash_match=$true}
}
Copy-Item -LiteralPath $sourceMap -Destination $targetMap
$sourceHash=(Get-FileHash -LiteralPath $sourceMap -Algorithm SHA256).Hash.ToLowerInvariant()
$targetHash=(Get-FileHash -LiteralPath $targetMap -Algorithm SHA256).Hash.ToLowerInvariant()
if($sourceHash -ne $targetHash){throw 'Copied map hash mismatch.'}
$records += [ordered]@{path='ForestDemo/Content/Maps/DesertVillage_max.umap';source=$sourceMap;sha256=$sourceHash;destination_sha256=$targetHash;size_bytes=(Get-Item -LiteralPath $sourceMap).Length;hash_match=$true}
$canonicalLines=@($records | ForEach-Object {$_.path+"`t"+$_.sha256});[Array]::Sort($canonicalLines,[StringComparer]::Ordinal);$canonical=$canonicalLines -join "`n"
$sha=[Security.Cryptography.SHA256]::Create();$aggregate=[Convert]::ToHexString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($canonical))).ToLowerInvariant();$sha.Dispose()
$result=[ordered]@{published_at_utc=[DateTimeOffset]::UtcNow.ToString('o');theme='DesertVillage';effort='max';private_editor_process_count_before_copy=$live.Count;private_editor_finished_at_utc=$timing.finished_at_utc;external_actor_object_or_builtdata_count=$disallowed.Count;file_count=$records.Count;uasset_count=76;map_count=1;all_hashes_match=$true;aggregate_sha256=$aggregate;aggregate_method='SHA256 of ordinal path-sorted path<TAB>sha256 entries joined by LF, no trailing LF';files=$records}
[IO.File]::WriteAllText("$work/Validation/delivery_manifest.json",($result|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
[pscustomobject]$result | Select-Object published_at_utc,file_count,all_hashes_match,aggregate_sha256 | ConvertTo-Json
