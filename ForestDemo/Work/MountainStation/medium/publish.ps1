$ErrorActionPreference='Stop'
$work='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium'
$scratch='D:/github/AstraEffort/ForestDemo/Saved/Workers/MountainStation/medium/Project/ForestDemo/Content'
$dest='D:/github/AstraEffort/ForestDemo/Content'
$validation=Get-Content "$work/validation.json" -Raw | ConvertFrom-Json -DateKind String
if (!$validation.map_reload -or $validation.foreign_game_dependencies.Count -ne 0) { throw 'Validation incomplete' }
$runtime=Get-Content "$work/runtime_validation.json" -Raw | ConvertFrom-Json -DateKind String
if (!$runtime.passed) { throw 'Runtime validation incomplete' }
$capture=Get-Content "$work/capture_manifest.json" -Raw | ConvertFrom-Json -DateKind String
if ([DateTimeOffset]::Parse($capture.shots[0].captured_at_utc) -lt [DateTimeOffset]::Parse($validation.lighting_polish_saved_and_reloaded_utc)) { throw 'Captures precede final lighting' }
foreach ($name in @('overview','top_down','platform','tracks')) {
 if (!(Test-Path "$work/Screenshots/$name.png")) { throw "Missing screenshot $name" }
}
$unexpected=Get-ChildItem $scratch -Recurse -File | Where-Object { $_.FullName -notlike "$($scratch.Replace('/','\'))\MountainStation\medium\*" -and $_.FullName -ne "$($scratch.Replace('/','\'))\Maps\MountainStation_medium.umap" }
if ($unexpected) { throw ('Unexpected scratch Content packages: '+($unexpected.FullName -join ', ')) }
New-Item -ItemType Directory -Force "$dest/MountainStation/medium", "$dest/Maps" | Out-Null
Copy-Item "$scratch/MountainStation/medium/*" "$dest/MountainStation/medium/" -Recurse -Force
Copy-Item "$scratch/Maps/MountainStation_medium.umap" "$dest/Maps/MountainStation_medium.umap" -Force
$files=@(Get-ChildItem "$scratch/MountainStation/medium" -Recurse -File)+@(Get-Item "$scratch/Maps/MountainStation_medium.umap")
$evidence=foreach ($f in $files) {
 $rel=[IO.Path]::GetRelativePath($scratch,$f.FullName)
 $sourceHash=(Get-FileHash $f.FullName -Algorithm SHA256).Hash
 $destHash=(Get-FileHash (Join-Path $dest $rel) -Algorithm SHA256).Hash
 if ($sourceHash -ne $destHash) { throw "Hash mismatch: $rel" }
 [ordered]@{path=$rel; bytes=$f.Length; sha256=$sourceHash; copied_hash_matches=$true}
}
[ordered]@{published_at_utc=[DateTimeOffset]::UtcNow.ToString('o'); files=$evidence; count=$files.Count; external_packages=0; built_data_packages=0} | ConvertTo-Json -Depth 6 | Set-Content "$work/delivery_manifest.json"
