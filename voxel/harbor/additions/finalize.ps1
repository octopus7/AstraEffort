$ErrorActionPreference = 'Stop'
$root = 'D:/github/AstraEffort/voxel/harbor/additions'
$utf = [Text.UTF8Encoding]::new($false)
function Load($file) { Get-Content -Raw -LiteralPath (Join-Path $root $file) | ConvertFrom-Json }
function Save($file, $value) { [IO.File]::WriteAllText((Join-Path $root $file), ($value | ConvertTo-Json -Depth 45), $utf) }
$export = Load 'validation_export.json'
$opening = Load 'validation_opening.json'
$build = Load 'build_validation.json'
$captures = Load 'capture_manifest.json'
if (-not $export.passed -or $export.asset_count -ne 1 -or $export.variant_count -ne 2 -or @($export.errors).Count) { throw 'Format verification did not pass the complete pair.' }
if (-not $opening.passed -or $opening.records.Count -ne 2 -or -not $build.passed -or $captures.captures.Count -ne 2) { throw 'Opening/build/capture evidence incomplete.' }
$processes = @((Load 'process_build.json'), (Load 'process_validation_export.json'), (Load 'process_validation_opening.json'))
if (@($processes | Where-Object { $_.exit_code -ne 0 }).Count) { throw 'A recorded Blender process failed.' }
$large = Load 'assets/repair_dock/large/metadata.json'
$half = Load 'assets/repair_dock/half/metadata.json'
$paletteNames = @('empty','graphite','steel','metal','light_metal','marine_teal','light_teal','deep_teal','ivory','light_ivory','brick_orange','light_brick','dark_brick','timber','light_timber','dark_timber','stone','light_stone','mortar','opaque_blue_glass','light_glass','amber','rope','bolt','lamp','rubber')
$colors = for ($i=0; $i -lt $paletteNames.Count; $i++) { @{ index=$i; name=$paletteNames[$i]; rgba_srgb_0_255=$large.palette[$i] } }
Save 'palette.json' @{ theme='harbor'; scope='additions'; empty_index=0; continuity_source='Accepted harbor palette, consulted for style only'; material_model='Opaque flat palette PBR, roughness 0.74'; colors=@($colors) }
Save 'provenance.json' @{
    theme='harbor'; scope='additions'; asset='repair_dock'; geometry_source='build.py'
    source_sha256=(Get-FileHash -LiteralPath (Join-Path $root 'build.py') -Algorithm SHA256).Hash.ToLower()
    reference=@{ path='REF/voxel/harbor/additions/reference.png'; sha256=(Get-FileHash -LiteralPath 'D:/github/AstraEffort/REF/voxel/harbor/additions/reference.png' -Algorithm SHA256).Hash.ToLower(); role='Design input only, not a texture or render evidence' }
    approved_style_source='voxel/harbor/palette.json'; geometry='Original native uint8 occupied grid; no accepted original model or source copied'
    generic_tools=@('voxel/_tools/voxelkit.py','voxel/_tools/blender_pipeline.py','voxel/_tools/verify_theme.py')
    external_references=@(); worker_image_generation_seconds=0
    half_method='Exact axis halving via conservative nonempty 2x2x2 majority; doubled meters per voxel; no manual half-grid edits'
}
$start = [DateTimeOffset]::Parse('2026-10-23T15:44:38Z')
$finish = [DateTimeOffset]::UtcNow
$wall = [Math]::Round(($finish-$start).TotalSeconds,3)
Save 'TIMING.json' @{
    started_at_utc=$start.ToString('yyyy-MM-ddTHH:mm:ssZ'); finished_at_utc=$finish.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'); worker_wall_seconds=$wall
    full_blender_processes=$processes; build_pipeline_seconds=$build.elapsed_seconds; export_verifier_seconds=$export.elapsed_seconds; opening_check_seconds=$opening.elapsed_seconds
    measurement='Each full process is measured from immediately before Blender invocation through process exit with a .NET Stopwatch; process startup and script geometry execution included.'
    build_invocations=1; export_validation_invocations=1; native_opening_validation_invocations=1; visual_revision_invocations=0; image_generation_seconds=0
}
$modelRows = @($large,$half) | ForEach-Object {
    $physical = ($_.grid_extents_m | ForEach-Object { [Math]::Round($_,3) }) -join ' x '
    '| {0} | {1} | {2:N0} | {3:N0} | {4} |' -f $_.variant,($_.grid_size -join ' x '),$_.occupied_voxels,$_.surface.triangles,$physical
}
$processRows = $processes | ForEach-Object { '| {0} | {1} | {2} | {3:0.000} | {4} |' -f $_.process,$_.started_at_utc,$_.finished_at_utc,$_.elapsed_seconds,$_.exit_code }
$report = @"
# Harbor addition: empty repair dock

One original empty U-shaped boat repair dock is ready for review in large and half native voxel resolutions. Two sidewalls and the rear deck surround a lowered paved bay with an open front, three keel blocks and four hull stands in two pairs. A small cabinet, winch, ladder and mooring fittings complete the working structure. There is no boat, water or landscape.

## Actual timing

- Start UTC: $($start.ToString('yyyy-MM-ddTHH:mm:ssZ'))
- Start KST: $($start.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:sszzz'))
- Finish UTC: $($finish.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'))
- Finish KST: $($finish.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:ss.fffzzz'))
- Total worker wall: $wall seconds.

| Full Blender process | UTC start | UTC finish | Wall seconds | Exit |
|---|---|---|---:|---:|
$($processRows -join "`n")

These process measurements include Blender startup and script execution. The parent utility separately measured $([Math]::Round($build.elapsed_seconds,3)) seconds inside build/export/render execution, $([Math]::Round($export.elapsed_seconds,3)) seconds inside export verification, and the native semantic check measured $([Math]::Round($opening.elapsed_seconds,3)) seconds. Full scopes and times are in TIMING.json and process_*.json. One build, two required verification processes, no visual rebuild, no optional render angles and zero worker image-generation time.

## Models and files

| Variant | Grid XYZ | Occupied cells | Surface triangles | Physical grid XYZ (m) |
|---|---|---:|---:|---|
$($modelRows -join "`n")

The large grid is 128 x 128 x 72. Half is exactly 64 x 64 x 36 with twice the cell size and the same physical grid extents. Conservative reduction may expand occupied boundaries by one original large cell. Native VOX is authoritative; half is a true lower-resolution occupied grid, not a scaled mesh. No manual half-grid edits were required.

assets/repair_dock/{large,half} each contains repair_dock.vox, repair_dock.blend, repair_dock.glb, repair_dock.fbx, metadata.json and preview.png: one asset, two variants, eight model-format files and two actual PNGs. Geometry source is build.py. validate_opening.py independently checks saved native files. palette.json and provenance.json preserve style and source/reference information; capture_manifest.json records real matching-camera render settings/times and hashes; DELIVERY.json inventories final hashes.

[Large preview](assets/repair_dock/large/preview.png) | [Half preview](assets/repair_dock/half/preview.png)

## Verification and actual image review

Both final previews were individually opened and inspected. The front entrance and lowered bay remain clear. All three keel blocks and the four support pads remain distinct, with purposeful A-frame timbers below. Cabinet, rear hauling winch, ladder, coping, mooring posts and external fenders remain readable at both resolutions. Fine plank/paving divisions, winch winding ridges and stand bracing become coarser in half. No demonstrated visual defect required a rebuild, and no optional views or polish passes were made.

validation_export.json reports passed=true, one asset, two variants and zero errors. The fresh native parser checked occupancy, palette indices, coordinates, counts and hashes. Both BLEND, GLB and FBX variants were freshly imported and compared with the authoritative voxel boundary. All six format imports report zero degenerate triangles, invalid boundary triangles, invalid material triangles and off-grid coordinates, with matching bounds and triangle counts.

validation_opening.json separately reparses the saved VOX without importing the authoring module. In both sizes it verifies an empty front-entry volume, an empty central upper working volume, a continuous low bay floor, exactly three disconnected centerline keel blocks above that floor, two disconnected stands in the left support strip and two in the right. The tested boxes, voxel counts and component sizes are recorded explicitly. This proves the opening and support counts in native occupancy, not only in a render.

## Limits and ownership

Static game-art structure only: no rig, winch animation, dry-dock water system, collision, LOD chain or engine integration. No engineering load rating is claimed. Materials use opaque flat palette colors on merged coplanar exterior voxel faces, so no texture UVs are needed. GLB/FBX contain asset geometry only; BLEND retains a separate STUDIO collection for reproducible previews. The bay paving and structural foundations are parts of the dock itself.

Only voxel/harbor/additions was authored. Accepted harbor originals and all other deliveries remained frozen. The accepted harbor palette was read only for authorized style continuity; no accepted creative source or geometry was inspected/copied. The sole visual reference is REF/voxel/harbor/additions/reference.png. No other theme, ForestDemo, Git, installation, shared live Blender scene, image generation or worker delegation was used.

The addition is frozen on submission. Forestry has not begun and waits for phase-A acceptance, reference readiness and explicit parent dispatch.
"@
[IO.File]::WriteAllText((Join-Path $root 'RESULT.md'),$report,$utf)
Save 'STATUS.json' @{
    theme='harbor'; delivery_scope='additions'; worker=1; status='ready_for_review'; assets=@('repair_dock'); asset_count=1; variant_count=2
    started_at_utc=$start.ToString('yyyy-MM-ddTHH:mm:ssZ'); started_at_kst=$start.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:sszzz')
    finished_at_utc=$finish.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'); finished_at_kst=$finish.ToOffset([TimeSpan]::FromHours(9)).ToString('yyyy-MM-ddTHH:mm:ss.fffzzz')
    elapsed_seconds=$wall; model_format_files=8; actual_previews=2; frozen_on_submission=$true
    validation_summary='Native VOX and all six fresh mesh imports passed; saved-native opening, three keel blocks and two stand pairs verified at both resolutions; both previews inspected.'
    validation=@('validation_export.json','validation_opening.json'); blockers=@()
}
$files = Get-ChildItem -LiteralPath $root -Recurse -File | Where-Object { $_.Name -ne 'DELIVERY.json' } | ForEach-Object {
    @{ path=$_.FullName.Substring($root.Length+1).Replace('\','/'); bytes=$_.Length; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower() }
}
Save 'DELIVERY.json' @{ theme='harbor'; scope='additions'; created_at_utc=$finish.ToString('o'); files=@($files) }
Get-Content -LiteralPath (Join-Path $root 'STATUS.json')
