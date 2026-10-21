$ErrorActionPreference='Stop'
$scratch='D:/github/AstraEffort/ForestDemo/Saved/Workers/medium/ForestDemo'
$work='D:/github/AstraEffort/ForestDemo/Work/medium'
$dest='D:/github/AstraEffort/ForestDemo/Content/Forest/medium'
$validation=Get-Content "$work/validation.json" -Raw | ConvertFrom-Json -DateKind String
if(Test-Path "$work/capture_error.txt"){throw 'Capture script error remains'}
if (!$validation.reloaded -or $validation.bad_dependencies.Count -ne 0) {throw 'Validation failed'}
if (!$validation.solid_prop_simple_collision_counts -or ($validation.solid_prop_simple_collision_counts.PSObject.Properties.Value | Where-Object {$_ -le 0}).Count -gt 0) {throw 'Missing solid collision'}
$capture=Get-Content "$work/Screenshots/capture_manifest.json" -Raw | ConvertFrom-Json -DateKind String
if($capture.captures.Count -ne 4){throw 'Incomplete captures'}
foreach($item in $capture.captures){if([DateTimeOffset]::Parse($item.captured_at_utc) -lt [DateTimeOffset]::Parse($validation.validated_at_utc)){throw 'Stale capture'}}
$runtime=Get-Content "$work/runtime_validation.json" -Raw | ConvertFrom-Json -DateKind String
if($runtime.status -ne 'passed'){throw 'Runtime validation not passed'}
$timing=Get-Content 'D:/github/AstraEffort/ForestDemo/Saved/Workers/medium/delivery6-capture-timing.json' -Raw | ConvertFrom-Json -DateKind String
if ($timing.exit_code -ne 0) {throw 'Private capture editor did not finish cleanly'}
if ((Get-ChildItem "$scratch/Content/Forest/medium" -Recurse -File | Where-Object {$_.Name -match 'BuiltData|ExternalActors|ExternalObjects'}).Count -gt 0) {throw 'Forbidden package'}
Add-Type -AssemblyName System.Drawing
$shots=@()
foreach($name in @('overview','top_down','lake','beach')) {
 $path="$work/Screenshots/$name.png"; $im=[Drawing.Image]::FromFile($path)
 if($im.Width -ne 1920 -or $im.Height -ne 1080){$im.Dispose();throw 'Wrong capture size'}
 $im.Dispose();$shots+=@{file=$path;sha256=(Get-FileHash $path -Algorithm SHA256).Hash}
}
if (($shots.sha256 | Select-Object -Unique).Count -ne 4) {throw 'Duplicate captures'}
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item -LiteralPath "$scratch/Content/Forest/medium/Materials" -Destination $dest -Recurse -Force
Copy-Item -LiteralPath "$scratch/Content/Forest/medium/Meshes" -Destination $dest -Recurse -Force
Copy-Item -LiteralPath "$scratch/Content/Maps/medium.umap" -Destination 'D:/github/AstraEffort/ForestDemo/Content/Maps/medium.umap' -Force
$hashes=@()
foreach($file in Get-ChildItem $dest -Recurse -File){
 $rel=[IO.Path]::GetRelativePath($dest,$file.FullName);$a=(Get-FileHash $file.FullName -Algorithm SHA256).Hash;$b=(Get-FileHash (Join-Path "$scratch/Content/Forest/medium" $rel) -Algorithm SHA256).Hash
 if($a -ne $b){throw "Copy mismatch: $rel"};$hashes+=@{file=$file.FullName;sha256=$a}
}
$map='D:/github/AstraEffort/ForestDemo/Content/Maps/medium.umap';$mapHash=(Get-FileHash $map -Algorithm SHA256).Hash
if($mapHash -ne (Get-FileHash "$scratch/Content/Maps/medium.umap" -Algorithm SHA256).Hash){throw 'Map copy mismatch'}
$hashes+=@{file=$map;sha256=$mapHash}
@{published_at_utc=[DateTimeOffset]::UtcNow.ToString('o');files=$hashes;screenshots=$shots;private_editor_exit_code=$timing.exit_code} | ConvertTo-Json -Depth 6 | Set-Content "$work/delivery_manifest.json"
Write-Output "Published $($hashes.Count) verified packages and checked four unique 1920x1080 captures."




