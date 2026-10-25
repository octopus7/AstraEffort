$ErrorActionPreference = 'Stop'
$directory = 'D:/github/AstraEffort/voxel/mountain_railway'
$utf = [Text.UTF8Encoding]::new($false)
function LoadJson($name) { Get-Content -Raw -LiteralPath (Join-Path $directory $name) | ConvertFrom-Json }
function PutJson($name, $data) { [IO.File]::WriteAllText((Join-Path $directory $name), ($data | ConvertTo-Json -Depth 45), $utf) }
$check = LoadJson 'validation_export.json'
if (-not $check.passed -or $check.asset_count -ne 5 -or $check.variant_count -ne 10 -or @($check.errors).Count -ne 0) { throw 'Independent validation must pass all five pairs.' }
$capture = LoadJson 'capture_manifest.json'
if ($capture.captures.Count -ne 10) { throw 'Ten primary render captures are required.' }
$names = @('locomotive', 'passenger_car', 'station', 'railway_bridge', 'cable_car')
$metadata = foreach ($name in $names) { foreach ($size in @('large', 'half')) { LoadJson "assets/$name/$size/metadata.json" } }
$initial = LoadJson 'build_validation_initial.json'
$revision = LoadJson 'build_validation_station_revision.json'
$latestPairs = foreach ($name in $names) { @{ asset = $name; large = ($metadata | Where-Object { $_.asset -eq $name -and $_.variant -eq 'large' }); half = ($metadata | Where-Object { $_.asset -eq $name -and $_.variant -eq 'half' }) } }
PutJson 'build_validation.json' @{
    passed = ($initial.passed -and $revision.passed); assets = @($latestPairs)
    started_at_utc = $initial.started_at_utc; finished_at_utc = $revision.finished_at_utc
    elapsed_seconds = ($initial.elapsed_seconds + $revision.elapsed_seconds)
    elapsed_measurement = 'Sum of the measured initial build and station visibility correction; intervening review excluded.'
    invocations = @('build_validation_initial.json', 'build_validation_station_revision.json')
    final_independent_verification = 'validation_export.json'
}
$colorNames = @('empty', 'dark_steel', 'steel', 'metal', 'light_metal', 'forest_green', 'light_green', 'deep_green', 'ivory', 'light_ivory', 'brick_red', 'light_red', 'dark_red', 'timber', 'light_timber', 'dark_timber', 'stone', 'light_stone', 'mortar', 'opaque_glass', 'light_glass', 'amber', 'lamp', 'bolt', 'rubber')
$swatches = for ($i = 0; $i -lt $colorNames.Count; $i++) { @{ index = $i; name = $colorNames[$i]; rgba_srgb_0_255 = $metadata[0].palette[$i] } }
PutJson 'palette.json' @{ theme = 'mountain_railway'; empty_index = 0; colors = @($swatches); material_model = 'Opaque flat palette PBR; roughness 0.74; no image textures or UVs required' }
PutJson 'provenance.json' @{
    theme = 'mountain_railway'; source = 'build.py'; source_sha256 = (Get-FileHash -LiteralPath (Join-Path $directory 'build.py') -Algorithm SHA256).Hash.ToLower()
    design_reference = @{ path = 'REF/voxel/mountain_railway/reference.png'; sha256 = (Get-FileHash -LiteralPath 'D:/github/AstraEffort/REF/voxel/mountain_railway/reference.png' -Algorithm SHA256).Hash.ToLower(); usage = 'Viewed as design guidance only; not scene evidence or a texture' }
    external_references = @(); worker_image_generation_seconds = 0
    geometry = 'Five new uint8 occupied XYZ voxel grids; palette index 0 empty, actual colors start at 1'
    half_method = 'Exact 2x axis reduction via nonempty 2x2x2 majority with doubled meters per voxel; no manual half-grid corrections'
    generic_tools = @('voxel/_tools/voxelkit.py', 'voxel/_tools/blender_pipeline.py', 'voxel/_tools/verify_theme.py')
}
$visualReview = @'
# Mountain railway visual review

All ten final primary previews were individually opened and inspected at 768 x 768. Each asset's two resolutions use matching camera and studio settings. These are actual Blender renders of geometry extracted from the native voxel data. No optional rear captures or polish passes were performed.

| Asset | Observed in large and half |
|---|---|
| Locomotive | Rounded low nose, sloped cab panes, three lamps, two bogies, side louver banks, roof equipment and coupler socket remain legible. The half wheels/springs and louver spaces are coarser. |
| Passenger car | Five large side windows, rounded roof, end door/gangway surround, two bogies, handrails and coupler remain distinct. The half roof vent markings simplify. |
| Station | Broad eaves, sheltered platform, bench, masonry base and stairs are visible. First rendering showed the front entrance hidden by its porch column. The final source adds a clearly visible glazed side entrance; both corrected station images were reopened. |
| Railway bridge | Two masonry supports flank a fully open stepped arch. Two uninterrupted rails, cross sleepers, clips and the deck remain distinct. Half mortar lines become wider, while the arch remains open. |
| Cable car | Capsule corners, large framed windows, split side doors, lamps, separate braced hanger, four pulleys and short overhead cable segments remain readable. Coarse wheel hubs and brace steps are expected at half resolution. |

Only the station entrance visibility required a source correction. It was rebuilt at both native resolutions, recaptured with the same primary camera, and included in the fresh final independent verification. No manual half-voxel edits were required. Other camera angles were not rendered; full export geometry was checked computationally.
'@
[IO.File]::WriteAllText((Join-Path $directory 'VISUAL_REVIEW.md'), $visualReview, $utf)

$begin = [DateTimeOffset]::Parse('2026-10-23T14:48:16Z')
$end = [DateTimeOffset]::UtcNow
$seconds = [Math]::Round(($end - $begin).TotalSeconds, 3)
$rows = $metadata | ForEach-Object {
    $extent = ($_.grid_extents_m | ForEach-Object { [Math]::Round($_, 3) }) -join ' x '
    '| {0} | {1} | {2} | {3:N0} | {4:N0} | {5} |' -f $_.asset, $_.variant, ($_.grid_size -join ' x '), $_.occupied_voxels, $_.surface.triangles, $extent
}
$links = $names | ForEach-Object { '| {0} | [large](assets/{0}/large/preview.png) | [half](assets/{0}/half/preview.png) |' -f $_ }
$report = @"
# Mountain railway delivery

Five original models are ready for review: Mountain diesel locomotive, Mountain passenger coach, Sheltered mountain station, Open-arch masonry railway bridge, and Alpine capsule cable car. Each is delivered in two real native voxel resolutions, with VOX authoritative and BLEND/GLB/FBX surface exports.

## Actual timing

- Start UTC: $($begin.ToString('yyyy-MM-ddTHH:mm:ssZ'))
- Start KST: $($begin.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:sszzz'))
- Finish UTC: $($end.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'))
- Finish KST: $($end.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:ss.fffzzz'))
- Elapsed worker wall seconds: $seconds
- Initial build/export/ten primary renders: $([Math]::Round($initial.elapsed_seconds, 3)) seconds, $($initial.started_at_utc) to $($initial.finished_at_utc).
- Station entrance correction build/export/two primary renders: $([Math]::Round($revision.elapsed_seconds, 3)) seconds, $($revision.started_at_utc) to $($revision.finished_at_utc).
- Final independent verification: $([Math]::Round($check.elapsed_seconds, 3)) seconds, $($check.started_at_utc) to $($check.finished_at_utc).
- Worker image-generation time: 0 seconds. No image-generation tool was invoked by this worker.

The build, revision and verification processes ran sequentially with four Blender CPU threads. Total wall time includes authoring, render review and reporting; those intervals are not invented as separate measurements.

## Model counts

| Asset | Variant | Grid XYZ | Occupied voxels | Triangles | Physical grid XYZ (m) |
|---|---|---|---:|---:|---|
$($rows -join "`n")

Every large grid has even dimensions and longest axis 128. Every half grid is exactly half on all three axes with twice the meters per voxel. Physical grid extents match within each pair. Conservative reduction can move the visible boundary outward by at most one original large cell. These are distinct native voxel grids, not merely scaled meshes. No manual half-grid changes were needed.

## Delivery and verification

The output contains five assets, ten variants, 40 model-format files and ten actual preview PNGs. assets/ASSET/{large,half} contains ASSET.vox, ASSET.blend, ASSET.glb, ASSET.fbx, metadata.json and preview.png. Source is build.py. palette.json names each shared theme color; provenance.json records the only visual reference and source hash. capture_manifest.json records real render times, camera settings and image/source hashes. DELIVERY.json inventories final file hashes.

| Asset | Large preview | Half preview |
|---|---|---|
$($links -join "`n")

Fresh independent verification passed all five assets and ten variants with zero errors. The native VOX parser checked occupied cells, grid sizes, palette indices, duplicate/out-of-range coordinates and hashes. Fresh imports of all ten BLEND, ten GLB and ten FBX files checked bounds, triangle parity, finite grid-aligned coordinates, outward voxel-boundary surfaces and palette assignment. Every import reports zero degenerate triangles, invalid boundary triangles, invalid material triangles and off-grid coordinates. Full evidence is in validation_export.json and validation_export.log. The original full build and station revision records are preserved beside the combined build_validation.json.

All ten final primary images were opened and inspected. The single visual correction makes the station's side entrance visible beside the porch columns; both revised station previews were inspected before final validation. VISUAL_REVIEW.md records each asset's large/half findings. No optional rear captures or further polish loop was performed.

## Limitations and ownership

These are static models with no rig, animation, LOD chain, collision or engine integration. Window and lamp appearances use opaque palette colors; transparent passenger interiors, optical lighting simulation and vehicle/cable dynamics are not supplied. Small joints, spring grooves, roof vents and frame edges become coarser at half resolution. The bridge is game-art geometry, not an engineered structure or a verified common track gauge. Each model has its own physical scale; no assembled running railway scene is claimed.

Meshes contain merged coplanar exterior faces from native occupancy and use per-face flat palette materials, so no texture UVs are needed. GLB and FBX contain asset geometry only. BLEND includes a separate STUDIO collection for reproducible previews. The station platform and bridge foundations are intentional architectural parts; no common diorama floor is authored.

Only voxel/mountain_railway was written. Accepted farm and harbor creative files remained frozen and were not inspected or copied. No other theme creative resources, ForestDemo, previous Blender assets, Git or live shared Blender scene were accessed. The sole visual reference was REF/voxel/mountain_railway/reference.png; only generic parent-owned voxel tools were shared. No external references were consulted.

Files are frozen on submission. This completes this worker's three assigned themes; no further theme is queued.
"@
[IO.File]::WriteAllText((Join-Path $directory 'RESULT.md'), $report, $utf)
PutJson 'STATUS.json' @{
    theme = 'mountain_railway'; worker = 1; status = 'ready_for_review'; assets = $names; asset_count = 5; variant_count = 10
    started_at_utc = $begin.ToString('yyyy-MM-ddTHH:mm:ssZ'); started_at_kst = $begin.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:sszzz')
    finished_at_utc = $end.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'); finished_at_kst = $end.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:ss.fffzzz')
    elapsed_seconds = $seconds; model_format_files = 40; actual_previews = 10; frozen_on_submission = $true
    validation_summary = 'Native VOX plus fresh BLEND/GLB/FBX imports pass for all ten variants with zero errors; all ten final primary renders inspected.'
    validation = 'validation_export.json'; blockers = @()
}
$inventory = Get-ChildItem -LiteralPath $directory -Recurse -File | Where-Object { $_.Name -ne 'DELIVERY.json' -and $_.Extension -ne '.blend1' } | ForEach-Object {
    @{ path = $_.FullName.Substring($directory.Length + 1).Replace('\', '/'); bytes = $_.Length; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower() }
}
PutJson 'DELIVERY.json' @{ theme = 'mountain_railway'; created_at_utc = $end.ToString('o'); files = @($inventory) }
Get-Content -LiteralPath (Join-Path $directory 'STATUS.json')
