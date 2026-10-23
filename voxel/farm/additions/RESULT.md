# Farm addition: combine harvester

One original combine harvester is ready for review in large and half voxel resolutions. Native VOX is authoritative; the BLEND, GLB and FBX files are surface-only voxel-derived outputs.

## Actual timing

- Start UTC: 2026-10-23T15:31:18Z
- Start KST: 2026-10-24T00:31:18+09:00
- Finish UTC: 2026-10-23T15:41:52.675Z
- Finish KST: 2026-10-24T00:41:52.675+09:00
- Elapsed worker wall: 634.676 seconds.
- Measured build/export/primary render pipeline: 22.416 seconds, 2026-10-23T15:38:06.708557+00:00 to 2026-10-23T15:38:29.124476+00:00.
- Measured independent validation: 6.521 seconds, 2026-10-23T15:39:32.696509+00:00 to 2026-10-23T15:39:39.217002+00:00. Tool-observed full verifier command wall time: 7.0288096 seconds.
- One build, one validation, no visual revision builds, no optional views and no worker image generation.

TIMING.json records the measurement boundaries. Build pipeline timing excludes Blender startup and make_assets; full build-process wall was not separately instrumented and is not invented. All authoring, startup, review and reporting remain within the actual worker wall interval.

## Native model and delivery

| Variant | Grid XYZ | Occupied cells | Surface triangles | Physical grid XYZ (m) |
|---|---|---:|---:|---|
| large | 128 x 128 x 112 | 402,879 | 29,928 | 8.32 x 8.32 x 7.28 |
| half | 64 x 64 x 56 | 57,598 | 10,368 | 8.32 x 8.32 x 7.28 |

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