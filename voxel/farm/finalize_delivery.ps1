$ErrorActionPreference = 'Stop'
$root = 'D:/github/AstraEffort/voxel/farm'
$utf8 = [Text.UTF8Encoding]::new($false)
function Write-JsonFile($name, $value) {
    [IO.File]::WriteAllText((Join-Path $root $name), ($value | ConvertTo-Json -Depth 50), $utf8)
}

$validation = Get-Content -Raw -LiteralPath (Join-Path $root 'validation_export.json') | ConvertFrom-Json
if (-not $validation.passed -or $validation.asset_count -ne 4 -or $validation.variant_count -ne 8 -or @($validation.errors).Count -ne 0) {
    throw 'Final independent validation has not passed for all four assets / eight variants.'
}
$primary = Get-Content -Raw -LiteralPath (Join-Path $root 'capture_manifest.json') | ConvertFrom-Json
$rear = Get-Content -Raw -LiteralPath (Join-Path $root 'capture_rear_manifest.json') | ConvertFrom-Json
if ($primary.captures.Count -ne 8 -or $rear.captures.Count -ne 8) { throw 'Expected sixteen final actual renders.' }
$initial = Get-Content -Raw -LiteralPath (Join-Path $root 'build_validation_initial.json') | ConvertFrom-Json
$visualRevision = Get-Content -Raw -LiteralPath (Join-Path $root 'build_validation_silo_visual_revision.json') | ConvertFrom-Json
$revision = Get-Content -Raw -LiteralPath (Join-Path $root 'build_validation.json') | ConvertFrom-Json
if ($revision.assets.Count -ne 1 -or $revision.assets[0].asset -ne 'silo') { throw 'Expected selective silo revision record.' }
Write-JsonFile 'build_validation_silo_revision.json' $revision
Write-JsonFile 'build_validation_silo_dimension_revision.json' $revision
$combined = [ordered]@{
    passed = ($initial.passed -and $revision.passed)
    started_at_utc = $initial.started_at_utc
    finished_at_utc = $revision.finished_at_utc
    elapsed_seconds = ($initial.elapsed_seconds + $visualRevision.elapsed_seconds + $revision.elapsed_seconds)
    elapsed_measurement = 'Sum of the measured full build and both selective silo revision execution intervals; intervening review time excluded.'
    build_invocations = @(
        @{ scope = 'All four assets'; source_record = 'build_validation_initial.json'; elapsed_seconds = $initial.elapsed_seconds; started_at_utc = $initial.started_at_utc; finished_at_utc = $initial.finished_at_utc },
        @{ scope = 'Silo only after ladder visual correction'; source_record = 'build_validation_silo_visual_revision.json'; elapsed_seconds = $visualRevision.elapsed_seconds; started_at_utc = $visualRevision.started_at_utc; finished_at_utc = $visualRevision.finished_at_utc },
        @{ scope = 'Silo canvas adjustment from Y=90 to Y=92'; source_record = 'build_validation_silo_dimension_revision.json'; elapsed_seconds = $revision.elapsed_seconds; started_at_utc = $revision.started_at_utc; finished_at_utc = $revision.finished_at_utc }
    )
    assets = @($initial.assets | Where-Object { $_.asset -ne 'silo' }) + @($revision.assets)
    checks = $initial.checks
    final_independent_validation = 'validation_export.json'
}
Write-JsonFile 'build_validation.json' $combined

$slugs = @('tractor', 'barn', 'silo', 'windmill')
$models = foreach ($slug in $slugs) {
    foreach ($variant in @('large', 'half')) {
        Get-Content -Raw -LiteralPath (Join-Path $root "assets/$slug/$variant/metadata.json") | ConvertFrom-Json
    }
}
$paletteNames = @('empty', 'tire_recess', 'dark_iron', 'iron', 'worn_metal', 'olive', 'olive_highlight', 'deep_olive', 'warm_ivory', 'terracotta', 'terracotta_highlight', 'dark_terracotta', 'timber', 'light_timber', 'dark_timber', 'warm_plaster', 'stone', 'mortar', 'opaque_glass', 'opaque_glass_shadow', 'amber_lamp', 'headlight_sail_highlight', 'grain_binding', 'straw', 'bolt', 'canvas')
$palette = for ($index = 0; $index -lt $paletteNames.Count; $index++) {
    @{ index = $index; name = $paletteNames[$index]; rgba_srgb_0_255 = $models[0].palette[$index] }
}
Write-JsonFile 'palette.json' @{
    theme = 'farm'; occupied_indices = '1 through 25, with unused entries permitted per asset'; empty_index = 0
    material_model = 'Flat palette colors; opaque PBR surfaces, roughness 0.74; no bitmap textures, bevels, or smooth shading'
    colors = $palette
}

$reference = 'D:/github/AstraEffort/REF/voxel/farm/reference.png'
Write-JsonFile 'provenance.json' @{
    theme = 'farm'; authored_source = 'build.py'; source_sha256 = (Get-FileHash -LiteralPath (Join-Path $root 'build.py') -Algorithm SHA256).Hash.ToLower()
    design_input = @{ path = $reference; sha256 = (Get-FileHash -LiteralPath $reference -Algorithm SHA256).Hash.ToLower(); role = 'Parent-provided farm reference; viewed as design guidance only, not used as render evidence or a texture' }
    external_references = @(); worker_image_generation_seconds = 0
    shared_generic_utilities = @('voxel/_tools/voxelkit.py', 'voxel/_tools/blender_pipeline.py', 'voxel/_tools/verify_theme.py')
    authored_geometry = 'Four independent uint8 occupied voxel grids with original deterministic structural detailing'
    reduction = 'Exact 2x reduction of every grid axis; nonempty 2x2x2 majority with doubled meters per voxel; no manual half-grid edits'
}

$review = @'
# Farm visual review

All eight final primary previews and all eight matching rear previews were individually opened and inspected as actual Blender-rendered images. The primary pair cameras match within each asset, and the rear pair cameras match within each asset. Source render settings and image hashes are in the two capture manifests.

| Asset | Primary review at large and half | Rear review at large and half |
|---|---|---|
| Tractor | Olive hood, paired lamps, radiator, stepped round tire/mudguard silhouettes and framed cab read in both versions. Tire tread is coarser in half. | Rear lamps, PTO cylinder and three-point drawbar remain distinct. |
| Barn | Open paired door leaves, cross braces, hinges, hay in the hollow interior, gable, tile courses and side windows remain readable. Half has broader tile and plank steps. | Separate service door, hinges, latch, loft window and downpipes remain present. |
| Silo | First preview showed a centered ladder concealing the outlet. The final source moves the ladder to the front-left tangent. Final large and half previews expose the hopper's angled discharge spout and open end. Structural bands and braced legs remain distinct. | Inspection hatch, handle/bolts and pressure riser read in both. |
| Windmill | Four separate sails, pale canvas inset strips, timber slats, central hub, stepped cap and gallery are visible in both. Canvas strips and mortar become coarser in half. | Rear upper/lower doors, access steps and the loading beam with hanging hoist remain present. One sail is partly occluded by the tower from this rear angle. |

The half models preserve the functional silhouettes. Their conservative voxel reduction broadens some narrow color bands, especially canvas strips, plank grooves and mortar lines. No manual half-grid correction was needed. All preview floors are studio-only; no shared diorama floor belongs to an asset export.
'@
[IO.File]::WriteAllText((Join-Path $root 'VISUAL_REVIEW.md'), $review, $utf8)

$start = [DateTimeOffset]::Parse('2026-10-23T14:05:33Z')
$finish = [DateTimeOffset]::UtcNow
$wallSeconds = [Math]::Round(($finish - $start).TotalSeconds, 3)
$rows = $models | ForEach-Object {
    $physicalExtents = ($_.grid_extents_m | ForEach-Object { [Math]::Round($_, 3) }) -join ' x '
    '| {0} | {1} | {2} | {3:N0} | {4:N0} | {5} |' -f $_.asset, $_.variant, ($_.grid_size -join ' x '), $_.occupied_voxels, $_.surface.triangles, $physicalExtents
}
$previewRows = foreach ($slug in $slugs) {
    '| {0} | [large](assets/{0}/large/preview.png) / [half](assets/{0}/half/preview.png) | [large rear](assets/{0}/large/preview_rear.png) / [half rear](assets/{0}/half/preview_rear.png) |' -f $slug
}
$rearSeconds = ($rear.captures | Measure-Object -Property elapsed_seconds -Sum).Sum
$initialValidation = Get-Content -Raw -LiteralPath (Join-Path $root 'validation_export_initial.json') | ConvertFrom-Json
$preGridValidation = Get-Content -Raw -LiteralPath (Join-Path $root 'validation_export_pre_grid_audit.json') | ConvertFrom-Json
$report = @"
# Farm delivery

Four original farm assets are ready for parent review: Orchard tractor, Timber harvest barn, Raised grain silo, and Four-sail grain windmill. Each has two actual voxel resolutions and native VOX, BLEND, GLB and FBX files. Native VOX is authoritative.

## Actual timing

- Worker start UTC: $($start.ToString('yyyy-MM-ddTHH:mm:ssZ'))
- Worker start KST: $($start.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:sszzz'))
- Worker finish UTC: $($finish.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'))
- Worker finish KST: $($finish.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:ss.fffzzz'))
- Elapsed worker wall seconds: $wallSeconds
- Initial build/export/primary renders: $([Math]::Round($initial.elapsed_seconds, 3)) seconds.
- Silo ladder revision build/export/primary renders: $([Math]::Round($visualRevision.elapsed_seconds, 3)) seconds.
- Silo canvas revision build/export/primary renders: $([Math]::Round($revision.elapsed_seconds, 3)) seconds.
- Initial independent verification: $([Math]::Round($initialValidation.elapsed_seconds, 3)) seconds.
- Intermediate independent verification after the ladder revision: $([Math]::Round($preGridValidation.elapsed_seconds, 3)) seconds.
- Final independent verification: $([Math]::Round($validation.elapsed_seconds, 3)) seconds.
- Sum of eight rear render intervals: $([Math]::Round($rearSeconds, 3)) seconds. This excludes process startup and file loading; build and verification timings overlap neither each other nor rear rendering.
- Worker image generation: 0 seconds. The supplied reference was viewed, and no image-generation tool was invoked by this worker.

## Models and counts

| Asset | Version | Grid XYZ | Occupied cells | Surface triangles | Physical grid XYZ (m) |
|---|---|---|---:|---:|---|
$($rows -join "`n")

The large grids have longest axis 128 and even dimensions. Each half grid is exactly half on all three axes; its meters per voxel doubles. The physical grid extents are identical within every pair. Conservative occupancy reduction may move a visible surface outward by one original large cell. This is a native coarse voxel model, not a scaled high-resolution mesh.

## Delivered paths

- Source geometry: build.py. Rear capture script: capture_rear.py. Named palette: palette.json. Reference provenance: provenance.json.
- assets/ASSET/large and assets/ASSET/half each contain ASSET.vox, ASSET.blend, ASSET.glb, ASSET.fbx, metadata.json, preview.png and preview_rear.png. Total: 4 assets, 8 variants, 32 model-format files, 16 actual render previews.
- Primary and rear capture provenance: capture_manifest.json and capture_rear_manifest.json.
- Validation evidence: build_validation.json, preserved initial and selective build records, validation_export.json, the initial verifier record, and build/verification logs.
- Individual image review: VISUAL_REVIEW.md. Delivery file hashes: DELIVERY.json.

| Asset | Main previews | Rear previews |
|---|---|---|
$($previewRows -join "`n")

## Verification

The final independent verifier exited successfully and reports passed=true, asset_count=4, variant_count=8 and zero errors. It reparsed all native VOX files and checked occupancy/hash/palette/grid parity. Fresh BLEND, GLB and FBX imports were checked against native occupancy for every triangle: true exterior voxel boundary, outward orientation, correct palette, finite on-grid coordinates, nonzero area, matching triangles and bounds. All three import formats report zero degenerate triangles, invalid boundary triangles, invalid material triangles and off-grid coordinates for all eight variants. GLB/FBX contain asset geometry only. The BLEND files additionally retain a separately named STUDIO collection for reproducible previews.

All sixteen final PNGs were opened and inspected. The visual source revision after first review was the silo ladder placement: it moved to the front-left side so that the discharge outlet remains visible. The silo canvas Y axis was subsequently increased from 90 to 92 cells while leaving its authored occupied shape intact. Both final silo primary and rear pairs were refreshed and inspected, then all eight final variants passed a fresh independent verification. No per-half manual geometry edits were required.

## Limitations and scope

The deliverables are static models: no rig, animation, LOD chain, collision, or game-engine integration is supplied. Glazing is an opaque flat palette color. Small decorative material divisions become broader at half resolution. The silo is a visual grain-storage model without fluid or grain simulation. The asset meshes use merged coplanar exterior voxel faces and per-face palette materials; they require no texture UVs. Preview ground planes and lights belong only to the BLEND studio setup and are absent from GLB/FBX asset exports.

Only this farm directory was authored. No other theme's creative files, ForestDemo resources, earlier Blender assets, shared live Blender scene or Git state were inspected or modified. The farm reference at REF/voxel/farm/reference.png is the sole visual reference; no external web sources were used. All creative geometry is original source code in build.py.

Files are frozen on submission pending parent acceptance. Harbor and mountain_railway have not been started.
"@
[IO.File]::WriteAllText((Join-Path $root 'RESULT.md'), $report, $utf8)
Write-JsonFile 'STATUS.json' @{
    theme = 'farm'; worker = 1; status = 'ready_for_review'
    started_at_utc = $start.ToString('yyyy-MM-ddTHH:mm:ssZ')
    started_at_kst = $start.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:sszzz')
    finished_at_utc = $finish.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
    finished_at_kst = $finish.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:ss.fffzzz')
    elapsed_seconds = $wallSeconds; asset_count = 4; variant_count = 8
    assets = $slugs; model_format_files = 32; actual_previews = 16
    validation_summary = 'Final independent native VOX and fresh BLEND/GLB/FBX checks pass for all eight variants with zero errors; all sixteen actual previews inspected.'
    validation = 'validation_export.json'; blockers = @(); frozen_on_submission = $true
}
$hashes = Get-ChildItem -LiteralPath $root -Recurse -File | Where-Object { $_.Name -ne 'DELIVERY.json' -and $_.Extension -ne '.blend1' } | ForEach-Object {
    @{ path = $_.FullName.Substring($root.Length + 1).Replace('\', '/'); bytes = $_.Length; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower() }
}
Write-JsonFile 'DELIVERY.json' @{ theme = 'farm'; created_at_utc = $finish.ToString('o'); files = @($hashes) }
Get-Content -LiteralPath (Join-Path $root 'STATUS.json')
