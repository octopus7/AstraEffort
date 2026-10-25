$ErrorActionPreference = 'Stop'
$root = 'D:/github/AstraEffort/voxel/farm/additions'
$utf8 = [Text.UTF8Encoding]::new($false)
function ReadRecord($file) { Get-Content -Raw -LiteralPath (Join-Path $root $file) | ConvertFrom-Json }
function SaveRecord($file, $record) { [IO.File]::WriteAllText((Join-Path $root $file), ($record | ConvertTo-Json -Depth 40), $utf8) }
$validation = ReadRecord 'validation_export.json'
$build = ReadRecord 'build_validation.json'
$capture = ReadRecord 'capture_manifest.json'
if (-not $validation.passed -or $validation.asset_count -ne 1 -or $validation.variant_count -ne 2 -or @($validation.errors).Count -ne 0) { throw 'Independent verification must pass the one asset pair.' }
if (-not $build.passed -or $capture.captures.Count -ne 2) { throw 'Build or actual capture pair is incomplete.' }
$large = ReadRecord 'assets/combine_harvester/large/metadata.json'
$half = ReadRecord 'assets/combine_harvester/half/metadata.json'
$colorNames = @('empty', 'tire_recess', 'dark_iron', 'iron', 'worn_metal', 'olive', 'olive_highlight', 'deep_olive', 'warm_ivory', 'terracotta', 'terracotta_highlight', 'dark_terracotta', 'timber', 'light_timber', 'dark_timber', 'warm_plaster', 'stone', 'mortar', 'opaque_glass', 'opaque_glass_shadow', 'amber_lamp', 'headlight', 'grain_binding', 'straw', 'bolt', 'canvas')
$colors = for ($i = 0; $i -lt $colorNames.Count; $i++) { @{ index = $i; name = $colorNames[$i]; rgba_srgb_0_255 = $large.palette[$i] } }
SaveRecord 'palette.json' @{ theme = 'farm'; scope = 'additions'; continuity_source = 'Accepted farm palette, consulted for style only'; empty_index = 0; colors = @($colors); material_model = 'Opaque flat palette PBR surfaces, roughness 0.74' }
SaveRecord 'provenance.json' @{
    theme = 'farm'; scope = 'additions'; asset = 'combine_harvester'; geometry_source = 'build.py'
    source_sha256 = (Get-FileHash -LiteralPath (Join-Path $root 'build.py') -Algorithm SHA256).Hash.ToLower()
    reference = @{ path = 'REF/voxel/farm/additions/reference.png'; sha256 = (Get-FileHash -LiteralPath 'D:/github/AstraEffort/REF/voxel/farm/additions/reference.png' -Algorithm SHA256).Hash.ToLower(); role = 'Design input only; not a model texture or render evidence' }
    style_palette = 'voxel/farm/palette.json, read only for approved style continuity'
    creative_geometry = 'Original occupied-cell geometry; no accepted original model asset or source copied'
    shared_generic_tools = @('voxel/_tools/voxelkit.py', 'voxel/_tools/blender_pipeline.py', 'voxel/_tools/verify_theme.py')
    external_references = @(); worker_image_generation_seconds = 0
    half_method = 'Exact 2x axis reduction via nonempty 2x2x2 majority and doubled meters per voxel; no manual half-grid edits'
}
$started = [DateTimeOffset]::Parse('2026-10-23T15:31:18Z')
$finished = [DateTimeOffset]::UtcNow
$wall = [Math]::Round(($finished - $started).TotalSeconds, 3)
SaveRecord 'TIMING.json' @{
    started_at_utc = $started.ToString('yyyy-MM-ddTHH:mm:ssZ'); finished_at_utc = $finished.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'); worker_wall_seconds = $wall
    build_pipeline = @{ started_at_utc = $build.started_at_utc; finished_at_utc = $build.finished_at_utc; elapsed_seconds = $build.elapsed_seconds; scope = 'Measured inside run_theme; export, native roundtrip and render execution; Blender startup and make_assets are outside this interval' }
    independent_validation = @{ started_at_utc = $validation.started_at_utc; finished_at_utc = $validation.finished_at_utc; elapsed_seconds = $validation.elapsed_seconds; process_tool_wall_seconds = 7.0288096 }
    complete_build_process_wall_seconds = $null; complete_build_process_note = 'Not separately instrumented; no duration invented. The measured build pipeline interval and total worker wall time are retained.'
    image_generation_seconds = 0; build_invocations = 1; validation_invocations = 1; visual_revision_invocations = 0
}
$rows = @($large, $half) | ForEach-Object {
    $extent = ($_.grid_extents_m | ForEach-Object { [Math]::Round($_, 3) }) -join ' x '
    '| {0} | {1} | {2:N0} | {3:N0} | {4} |' -f $_.variant, ($_.grid_size -join ' x '), $_.occupied_voxels, $_.surface.triangles, $extent
}
$result = @"
# Farm addition: combine harvester

One original combine harvester is ready for review in large and half voxel resolutions. Native VOX is authoritative; the BLEND, GLB and FBX files are surface-only voxel-derived outputs.

## Actual timing

- Start UTC: $($started.ToString('yyyy-MM-ddTHH:mm:ssZ'))
- Start KST: $($started.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:sszzz'))
- Finish UTC: $($finished.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'))
- Finish KST: $($finished.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:ss.fffzzz'))
- Elapsed worker wall: $wall seconds.
- Measured build/export/primary render pipeline: $([Math]::Round($build.elapsed_seconds, 3)) seconds, $($build.started_at_utc) to $($build.finished_at_utc).
- Measured independent validation: $([Math]::Round($validation.elapsed_seconds, 3)) seconds, $($validation.started_at_utc) to $($validation.finished_at_utc). Tool-observed full verifier command wall time: 7.0288096 seconds.
- One build, one validation, no visual revision builds, no optional views and no worker image generation.

TIMING.json records the measurement boundaries. Build pipeline timing excludes Blender startup and make_assets; full build-process wall was not separately instrumented and is not invented. All authoring, startup, review and reporting remain within the actual worker wall interval.

## Native model and delivery

| Variant | Grid XYZ | Occupied cells | Surface triangles | Physical grid XYZ (m) |
|---|---|---:|---:|---|
$($rows -join "`n")

The large grid is 128 x 128 x 112. The half grid is 64 x 64 x 56, with exactly half the cells on each axis and twice the meters per voxel. Both have identical physical grid extents. Conservative resampling may expand occupied boundaries by one original large cell. No mesh scaling or manual half-grid edits were used.

assets/combine_harvester/{large,half} each contains combine_harvester.vox, combine_harvester.blend, combine_harvester.glb, combine_harvester.fbx, metadata.json and preview.png. Total: one model, two variants, eight model-format files and two actual previews. Source geometry is build.py; palette.json records the approved farm style colors; provenance.json records source/reference hashes. capture_manifest.json stores matching camera settings and real render times/hashes. DELIVERY.json inventories final file hashes.

[Large preview](assets/combine_harvester/large/preview.png) | [Half preview](assets/combine_harvester/half/preview.png)

## Verification and visual review

The isolated Blender build exited 0. Independent verification also exited 0 and reports passed=true, asset_count=1, variant_count=2 and zero errors. It reparsed both native VOX files and freshly imported both BLEND, GLB and FBX variants. Native occupancy, palette indices, coordinates, counts and hashes passed; all imported triangles matched the true outward occupied-cell boundary and correct materials. Both sizes report zero degenerate triangles, invalid boundary triangles, invalid material triangles and off-grid coordinates. Full evidence is in build_validation.json, validation_export.json and their logs.

Both final PNGs were individually opened and inspected. The broad reel remains visibly open, with four circular supports, transverse bars, tine rows and cutter teeth. Raised glazing, front lamps, rounded wheels, access ladder, genuinely open grain hopper and the collared unloading auger remain legible in both sizes. Small wheel bolt, tread and reel details become coarser at half resolution. Four wheels are present in the native geometry; the body occludes the far rear wheel from this single primary camera. No demonstrated defect required a rebuild. No optional render or polish pass was performed.

## Limitations and ownership

Static model only: no rig, animation, harvesting or grain simulation, collision, LOD chain or engine integration. Glazing uses opaque palette colors. GLB/FBX contain only asset geometry; BLEND additionally retains a separate STUDIO collection for reproducible rendering. Merged coplanar native boundary faces use flat palette materials and need no texture UVs.

Only voxel/farm/additions was authored. Accepted farm original geometry, source, captures and records remain untouched. The existing farm palette was consulted solely for the explicitly authorized visual continuity. The provided addition reference is the only image source. No other theme, ForestDemo, Git, installation, live shared Blender scene, image generation or worker delegation was used.

The addition is frozen on submission. Harbor repair_dock remains unstarted pending explicit parent dispatch and reference readiness. No new theme has been started.
"@
[IO.File]::WriteAllText((Join-Path $root 'RESULT.md'), $result, $utf8)
SaveRecord 'STATUS.json' @{
    theme = 'farm'; delivery_scope = 'additions'; worker = 1; status = 'ready_for_review'; assets = @('combine_harvester'); asset_count = 1; variant_count = 2
    started_at_utc = $started.ToString('yyyy-MM-ddTHH:mm:ssZ'); started_at_kst = $started.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:sszzz')
    finished_at_utc = $finished.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'); finished_at_kst = $finished.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:ss.fffzzz')
    elapsed_seconds = $wall; model_format_files = 8; actual_previews = 2; frozen_on_submission = $true
    validation_summary = 'Native VOX and fresh BLEND/GLB/FBX verification pass both variants with zero errors; both final actual previews inspected.'
    validation = 'validation_export.json'; blockers = @()
}
$files = Get-ChildItem -LiteralPath $root -Recurse -File | Where-Object { $_.Name -ne 'DELIVERY.json' } | ForEach-Object {
    @{ path = $_.FullName.Substring($root.Length + 1).Replace('\', '/'); bytes = $_.Length; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower() }
}
SaveRecord 'DELIVERY.json' @{ theme = 'farm'; scope = 'additions'; created_at_utc = $finished.ToString('o'); files = @($files) }
Get-Content -LiteralPath (Join-Path $root 'STATUS.json')
