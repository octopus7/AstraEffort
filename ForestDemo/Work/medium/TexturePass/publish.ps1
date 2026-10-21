$ErrorActionPreference='Stop'
$root='D:/github/AstraEffort/ForestDemo/Work/medium/TexturePass'
$private='D:/github/AstraEffort/ForestDemo/Saved/Workers/medium/ForestDemo'
$final='D:/github/AstraEffort/ForestDemo'
$running=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'UnrealEditor*' -and $_.CommandLine -like '*Saved*Workers*medium*ForestDemo.uproject*' })
if($running.Count){throw 'Private editor must be closed before publishing'}
$build=Get-Content "$root/build_report.json" -Raw | ConvertFrom-Json
$uv=Get-Content "$root/fbx_roundtrip_validation.json" -Raw | ConvertFrom-Json
$tex=Get-Content "$root/texture_application_validation.json" -Raw | ConvertFrom-Json
$runtime=Get-Content "$root/runtime_validation.json" -Raw | ConvertFrom-Json
$validation=Get-Content "$root/validation.json" -Raw | ConvertFrom-Json
if($build.status -ne 'passed' -or $uv.status -ne 'passed' -or $tex.status -ne 'passed' -or $runtime.status -ne 'passed' -or $validation.bad_dependencies.Count){throw 'Validation not passed'}
if(!$runtime.checks.normal_pie_shutdown -or !$runtime.ground_sweep.blocking_hit){throw 'PIE or terrain evidence missing'}
foreach($name in @('__ExternalActors__','__ExternalObjects__')){if(Test-Path "$private/Content/$name/Maps/medium"){throw "Unexpected $name"}}
if(Test-Path "$private/Content/Maps/medium_BuiltData.uasset"){throw 'Unexpected baked lighting data'}
Add-Type -AssemblyName System.Drawing
$captures=@()
foreach($name in @('overview','top_down','lake','beach','water_t0','water_t1')){
 $path="$root/Screenshots/$name.png";$im=[Drawing.Image]::FromFile($path)
 if($im.Width -ne 1920 -or $im.Height -ne 1080){$im.Dispose();throw "Wrong size $name"};$im.Dispose()
 $captures+=@{name=$name;sha256=(Get-FileHash $path -Algorithm SHA256).Hash}
}
if(($captures | Where-Object name -eq water_t0).sha256 -eq ($captures | Where-Object name -eq water_t1).sha256){throw 'Water time frames identical'}
Copy-Item -LiteralPath "$private/Content/Forest/medium" -Destination "$final/Content/Forest" -Recurse -Force
Copy-Item -LiteralPath "$private/Content/Maps/medium.umap" -Destination "$final/Content/Maps/medium.umap" -Force
$files=@(Get-ChildItem "$private/Content/Forest/medium" -Recurse -File)+@(Get-Item "$private/Content/Maps/medium.umap")
$manifest=@()
foreach($f in $files){$relative=$f.FullName.Substring($private.Length).Replace('\','/');$dest=$final+$relative;$h=(Get-FileHash $f.FullName -Algorithm SHA256).Hash;if((Get-FileHash $dest -Algorithm SHA256).Hash -ne $h){throw "Hash mismatch $dest"};$manifest+=@{file=$dest;sha256=$h;bytes=$f.Length}}
@{published_at_utc=[DateTimeOffset]::UtcNow.ToString('o');private_editor_closed=$true;files=$manifest;screenshots=$captures;non_world_partition_evidence='Original new_level map retained; fresh dependency scan excludes external actor/object packages; no named external package directories or BuiltData';validated_copy_hashes_match=$true} | ConvertTo-Json -Depth 8 | Set-Content "$root/delivery_manifest.json" -Encoding utf8
Write-Output "Published and SHA256 verified $($manifest.Count) files."
