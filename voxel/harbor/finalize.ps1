$ErrorActionPreference = 'Stop'
$root = 'D:/github/AstraEffort/voxel/harbor'
$encoding = [Text.UTF8Encoding]::new($false)
function Read-Record($relative) { Get-Content -Raw -LiteralPath (Join-Path $root $relative) | ConvertFrom-Json }
function Save-Record($relative, $record) { [IO.File]::WriteAllText((Join-Path $root $relative), ($record | ConvertTo-Json -Depth 50), $encoding) }

$validation = Read-Record 'validation_export.json'
if (-not $validation.passed -or $validation.asset_count -ne 4 -or $validation.variant_count -ne 8 -or @($validation.errors).Count) { throw 'Final verification is incomplete.' }
$front = Read-Record 'capture_manifest.json'
$back = Read-Record 'capture_rear_manifest.json'
if ($front.captures.Count -ne 8 -or $back.captures.Count -ne 8) { throw 'Sixteen actual final captures are required.' }
$slugs = @('fishing_boat', 'lighthouse', 'warehouse', 'cargo_crane')
$entries = foreach ($slug in $slugs) {
    foreach ($variant in @('large', 'half')) { Read-Record "assets/$slug/$variant/metadata.json" }
}
$buildFiles = @('build_validation_initial.json', 'build_validation_boat_revision.json', 'build_validation_lighthouse_revision.json', 'build_validation_crane_revision.json')
$buildRuns = foreach ($file in $buildFiles) {
    $b = Read-Record $file
    if (-not $b.passed) { throw "Failed build record: $file" }
    [PSCustomObject][ordered]@{ record = $file; started_at_utc = $b.started_at_utc; finished_at_utc = $b.finished_at_utc; elapsed_seconds = $b.elapsed_seconds; assets = @($b.assets | ForEach-Object { $_.asset }) }
}
$pairs = foreach ($slug in $slugs) {
    @{ asset = $slug; large = ($entries | Where-Object { $_.asset -eq $slug -and $_.variant -eq 'large' }); half = ($entries | Where-Object { $_.asset -eq $slug -and $_.variant -eq 'half' }) }
}
Save-Record 'build_validation.json' @{
    passed = $true; assets = @($pairs); build_invocations = @($buildRuns)
    elapsed_seconds = ($buildRuns | Measure-Object -Property elapsed_seconds -Sum).Sum
    elapsed_measurement = 'Sum of build/export/render execution intervals; review and report time are excluded.'
    final_independent_validation = 'validation_export.json'
}

$names = @('empty', 'graphite', 'steel', 'metal', 'light_metal', 'marine_teal', 'light_teal', 'deep_teal', 'ivory', 'light_ivory', 'brick_orange', 'light_brick', 'dark_brick', 'timber', 'light_timber', 'dark_timber', 'stone', 'light_stone', 'mortar', 'opaque_blue_glass', 'light_glass', 'amber', 'rope', 'bolt', 'lamp', 'rubber')
$colors = for ($i = 0; $i -lt $names.Count; $i++) { @{ index = $i; name = $names[$i]; rgba_srgb_0_255 = $entries[0].palette[$i] } }
Save-Record 'palette.json' @{ theme = 'harbor'; empty_index = 0; material_model = 'Opaque flat palette PBR, roughness 0.74, no image textures'; colors = @($colors) }
Save-Record 'provenance.json' @{
    theme = 'harbor'; geometry_source = 'build.py'; source_sha256 = (Get-FileHash -LiteralPath (Join-Path $root 'build.py') -Algorithm SHA256).Hash.ToLower()
    reference = @{ path = 'REF/voxel/harbor/reference.png'; sha256 = (Get-FileHash -LiteralPath 'D:/github/AstraEffort/REF/voxel/harbor/reference.png' -Algorithm SHA256).Hash.ToLower(); usage = 'Viewed as design guidance; not used for texture or output evidence' }
    external_references = @(); worker_image_generation_seconds = 0
    authored_geometry = 'Four new uint8 XYZ occupied grids, independent source; colors start at palette index 1'
    shared_generic_tools = @('voxel/_tools/voxelkit.py', 'voxel/_tools/blender_pipeline.py', 'voxel/_tools/verify_theme.py')
    reduction = '2x2x2 nonempty majority, exact halving of each grid axis, doubled meters per voxel; no manual half-grid edits'
}

$visual = @'
# Harbor visual review

All eight final primary PNGs and all eight final rear PNGs were individually opened and inspected. These are actual Blender renders of the native-derived surface meshes. Each resolution pair uses matching camera and render settings.

| Asset | Main view, both resolutions | Rear view, both resolutions |
|---|---|---|
| Fishing boat | Curved hull, wheelhouse, teal/ivory hull paint, fenders, timber deck, working winch and lifting frame remain readable. | Clear stern workspace, winch, wheelhouse service door, boarding ladder, stern machinery and propeller/rudder assembly are present. |
| Lighthouse | Tapered tower, brick band, front steps and access door, separate lantern posts and central lamp read at both sizes. | Maintenance door, ventilation, gallery and lantern remain visible. |
| Warehouse | Curved barrel roof, open front and side cargo doors, interior crates, attached deck piers and loading steps read at both sizes. | Rear shutter, personnel door, downpipes, roof vents and skylights are present. |
| Cargo crane | Four stout legs, elevated deck, visible cab, open lattice boom, suspension cables, orange block and open hook remain distinct. | Rear cab access, counterweight and winch read with the four-leg support geometry. |

Three concrete first-review defects were corrected in the authoritative source grids: the boat's gunwale fill initially covered the wooden deck; the lighthouse gallery railing initially masked the lamp at half resolution; and the crane cab was initially hidden behind its boom from the primary camera. The final previews show the uncovered timber deck, lower lighthouse rail with visible lamp structure, and cab moved to the visible side with the winch relocated clear of it.

Half-resolution limitations are expected coarse voxel steps and broader small color details. Some narrow plank grooves, roof joints and ladder openings simplify. Four-leg support, the crane hook opening, lighthouse lantern posts, and boat working machinery are retained. All transparent-looking glazing is an opaque palette material. The lighthouse lantern uses open bays around its actual frame/lamp, not simulated transmissive glass.
'@
[IO.File]::WriteAllText((Join-Path $root 'VISUAL_REVIEW.md'), $visual, $encoding)

$started = [DateTimeOffset]::Parse('2026-10-23T14:27:39Z')
$finished = [DateTimeOffset]::UtcNow
$wall = [Math]::Round(($finished - $started).TotalSeconds, 3)
$modelRows = $entries | ForEach-Object {
    $physical = ($_.grid_extents_m | ForEach-Object { [Math]::Round($_, 3) }) -join ' x '
    '| {0} | {1} | {2} | {3:N0} | {4:N0} | {5} |' -f $_.asset, $_.variant, ($_.grid_size -join ' x '), $_.occupied_voxels, $_.surface.triangles, $physical
}
$timingRows = $buildRuns | ForEach-Object {
    '| {0} | {1} | {2} | {3:0.000} |' -f $_.record, $_.started_at_utc, $_.finished_at_utc, $_.elapsed_seconds
}
$previewRows = $slugs | ForEach-Object {
    '| {0} | [large](assets/{0}/large/preview.png) / [half](assets/{0}/half/preview.png) | [large rear](assets/{0}/large/preview_rear.png) / [half rear](assets/{0}/half/preview_rear.png) |' -f $_
}
$rearSeconds = ($back.captures | Measure-Object -Property elapsed_seconds -Sum).Sum
$result = @"
# Harbor delivery

Four original voxel models are ready for parent review: Harbor working fishing boat, Lantern harbor lighthouse, Barrel-roof harbor warehouse, and Four-leg harbor cargo crane. Native VOX is the source of truth. Each asset has large and half native grids plus BLEND, GLB and FBX outputs.

## Actual timing

- Start UTC: $($started.ToString('yyyy-MM-ddTHH:mm:ssZ'))
- Start KST: $($started.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:sszzz'))
- Finish UTC: $($finished.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'))
- Finish KST: $($finished.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:ss.fffzzz'))
- Elapsed worker wall seconds: $wall
- Final independent verification: $([Math]::Round($validation.elapsed_seconds, 3)) seconds.
- Sum of eight actual rear render intervals: $([Math]::Round($rearSeconds, 3)) seconds; this excludes Blender startup/file loading.
- Worker image generation: 0 seconds. No worker image-generation request was made.

| Build record | Actual start UTC | Actual finish UTC | Execution seconds |
|---|---|---|---:|
$($timingRows -join "`n")

Build execution includes export and primary rendering. The four build intervals, rear rendering and independent verification ran sequentially. Authoring, review and report time remain included in total wall time without being invented as separate measured durations.

## Models

| Asset | Variant | Grid XYZ | Occupied cells | Triangles | Physical grid XYZ (m) |
|---|---|---|---:|---:|---|
$($modelRows -join "`n")

All large grids have even dimensions and longest axis 128. Each half grid has exactly half the cells along every axis and twice the meters per voxel, so every large/half pair has identical physical grid extents. Conservative resampling may expand an occupied surface by at most one original large voxel. No mesh scaling was used to create the half versions, and no manual half-grid correction was needed.

## Deliverables and evidence

Each assets/ASSET/{large,half} directory contains ASSET.vox, ASSET.blend, ASSET.glb, ASSET.fbx, metadata.json, preview.png and preview_rear.png. The delivery totals are four assets, eight variants, 32 model-format files and 16 actual preview PNGs. Source and provenance are in build.py, capture_rear.py, palette.json and provenance.json. The two capture manifests record actual settings/timestamps and source/image hashes. DELIVERY.json inventories final file hashes.

| Asset | Primary previews | Rear previews |
|---|---|---|
$($previewRows -join "`n")

The final independent verifier reports passed=true, asset_count=4, variant_count=8 and zero errors. It reparses the native VOX occupancy, palette, coordinates and grids, then freshly imports BLEND, GLB and FBX to verify bounds, triangle counts and palette assignment against the native occupied-cell boundary. Every final format import has zero degenerate triangles, invalid boundary triangles, invalid material triangles and off-grid coordinates. GLB/FBX contain asset geometry only. BLEND files additionally retain a separately named STUDIO collection to reproduce the render evidence. Full evidence is in validation_export.json, validation_export.log, the build records and logs.

All sixteen final previews were opened and inspected. VISUAL_REVIEW.md records the checks and the three source corrections made after first rendering: uncovered timber boat deck, visible lighthouse lantern above its lowered gallery rail, and visible crane cab with separate winch placement. No optional visual polish loop followed those corrections.

## Limitations and scope

These are static assets. No rig, animation, collision, LOD chain or game-engine integration is supplied. Glazing is opaque; the lighthouse has actual open lantern framing and a modeled lamp but no optical beam or transmission simulation. The boat has no water/physics simulation. Small grooves and narrow openings simplify at half resolution. Per-face flat palette materials need no texture UVs. Studio floor/light/camera objects are absent from GLB and FBX exports; the warehouse's attached loading deck and other architectural foundations are intentional asset geometry.

Only voxel/harbor was authored. The accepted farm files remained frozen and were not read or copied; other themes, ForestDemo, previous Blender creative assets, Git and shared live Blender state were not accessed. The only visual reference was REF/voxel/harbor/reference.png. Shared parent-owned generic voxel utilities were used for export and verification. No external sources were consulted.

The harbor delivery is frozen on submission. Mountain_railway remains queued until explicit parent dispatch.
"@
[IO.File]::WriteAllText((Join-Path $root 'RESULT.md'), $result, $encoding)
Save-Record 'STATUS.json' @{
    theme = 'harbor'; worker = 1; status = 'ready_for_review'; assets = $slugs; asset_count = 4; variant_count = 8
    started_at_utc = $started.ToString('yyyy-MM-ddTHH:mm:ssZ'); started_at_kst = $started.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:sszzz')
    finished_at_utc = $finished.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'); finished_at_kst = $finished.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:ss.fffzzz')
    elapsed_seconds = $wall; model_format_files = 32; actual_previews = 16; frozen_on_submission = $true
    validation_summary = 'Native VOX and fresh BLEND/GLB/FBX verification passed all eight variants with zero errors; sixteen actual final previews inspected.'
    validation = 'validation_export.json'; blockers = @()
}
$files = Get-ChildItem -LiteralPath $root -Recurse -File | Where-Object { $_.Name -ne 'DELIVERY.json' -and $_.Extension -ne '.blend1' } | ForEach-Object {
    @{ path = $_.FullName.Substring($root.Length + 1).Replace('\', '/'); bytes = $_.Length; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower() }
}
Save-Record 'DELIVERY.json' @{ theme = 'harbor'; created_at_utc = $finished.ToString('o'); files = @($files) }
Get-Content -LiteralPath (Join-Path $root 'STATUS.json')
