# Mountain railway delivery

Five original models are ready for review: Mountain diesel locomotive, Mountain passenger coach, Sheltered mountain station, Open-arch masonry railway bridge, and Alpine capsule cable car. Each is delivered in two real native voxel resolutions, with VOX authoritative and BLEND/GLB/FBX surface exports.

## Actual timing

- Start UTC: 2026-10-23T14:48:16Z
- Start KST: 2026-10-23T23:48:16+09:00
- Finish UTC: 2026-10-23T15:03:51.705Z
- Finish KST: 2026-10-24T00:03:51.705+09:00
- Elapsed worker wall seconds: 935.705
- Initial build/export/ten primary renders: 95.022 seconds, 2026-10-23T14:57:20.507271+00:00 to 2026-10-23T14:58:55.529206+00:00.
- Station entrance correction build/export/two primary renders: 19.944 seconds, 2026-10-23T15:00:52.733666+00:00 to 2026-10-23T15:01:12.677415+00:00.
- Final independent verification: 7.700 seconds, 2026-10-23T15:02:52.630938+00:00 to 2026-10-23T15:03:00.330874+00:00.
- Worker image-generation time: 0 seconds. No image-generation tool was invoked by this worker.

The build, revision and verification processes ran sequentially with four Blender CPU threads. Total wall time includes authoring, render review and reporting; those intervals are not invented as separate measurements.

## Model counts

| Asset | Variant | Grid XYZ | Occupied voxels | Triangles | Physical grid XYZ (m) |
|---|---|---|---:|---:|---|
| locomotive | large | 56 x 128 x 76 | 251,709 | 6,948 | 3.36 x 7.68 x 4.56 |
| locomotive | half | 28 x 64 x 38 | 34,567 | 3,006 | 3.36 x 7.68 x 4.56 |
| passenger_car | large | 56 x 128 x 72 | 297,453 | 5,982 | 3.64 x 8.32 x 4.68 |
| passenger_car | half | 28 x 64 x 36 | 39,748 | 2,390 | 3.64 x 8.32 x 4.68 |
| station | large | 128 x 96 x 96 | 339,610 | 11,018 | 9.6 x 7.200 x 7.200 |
| station | half | 64 x 48 x 48 | 48,294 | 6,012 | 9.6 x 7.200 x 7.200 |
| railway_bridge | large | 128 x 56 x 64 | 171,117 | 2,428 | 12.8 x 5.600 x 6.4 |
| railway_bridge | half | 64 x 28 x 32 | 23,398 | 1,770 | 12.8 x 5.600 x 6.4 |
| cable_car | large | 80 x 72 x 128 | 256,715 | 5,092 | 4.4 x 3.96 x 7.04 |
| cable_car | half | 40 x 36 x 64 | 34,187 | 2,060 | 4.4 x 3.96 x 7.04 |

Every large grid has even dimensions and longest axis 128. Every half grid is exactly half on all three axes with twice the meters per voxel. Physical grid extents match within each pair. Conservative reduction can move the visible boundary outward by at most one original large cell. These are distinct native voxel grids, not merely scaled meshes. No manual half-grid changes were needed.

## Delivery and verification

The output contains five assets, ten variants, 40 model-format files and ten actual preview PNGs. assets/ASSET/{large,half} contains ASSET.vox, ASSET.blend, ASSET.glb, ASSET.fbx, metadata.json and preview.png. Source is build.py. palette.json names each shared theme color; provenance.json records the only visual reference and source hash. capture_manifest.json records real render times, camera settings and image/source hashes. DELIVERY.json inventories final file hashes.

| Asset | Large preview | Half preview |
|---|---|---|
| locomotive | [large](assets/locomotive/large/preview.png) | [half](assets/locomotive/half/preview.png) |
| passenger_car | [large](assets/passenger_car/large/preview.png) | [half](assets/passenger_car/half/preview.png) |
| station | [large](assets/station/large/preview.png) | [half](assets/station/half/preview.png) |
| railway_bridge | [large](assets/railway_bridge/large/preview.png) | [half](assets/railway_bridge/half/preview.png) |
| cable_car | [large](assets/cable_car/large/preview.png) | [half](assets/cable_car/half/preview.png) |

Fresh independent verification passed all five assets and ten variants with zero errors. The native VOX parser checked occupied cells, grid sizes, palette indices, duplicate/out-of-range coordinates and hashes. Fresh imports of all ten BLEND, ten GLB and ten FBX files checked bounds, triangle parity, finite grid-aligned coordinates, outward voxel-boundary surfaces and palette assignment. Every import reports zero degenerate triangles, invalid boundary triangles, invalid material triangles and off-grid coordinates. Full evidence is in validation_export.json and validation_export.log. The original full build and station revision records are preserved beside the combined build_validation.json.

All ten final primary images were opened and inspected. The single visual correction makes the station's side entrance visible beside the porch columns; both revised station previews were inspected before final validation. VISUAL_REVIEW.md records each asset's large/half findings. No optional rear captures or further polish loop was performed.

## Limitations and ownership

These are static models with no rig, animation, LOD chain, collision or engine integration. Window and lamp appearances use opaque palette colors; transparent passenger interiors, optical lighting simulation and vehicle/cable dynamics are not supplied. Small joints, spring grooves, roof vents and frame edges become coarser at half resolution. The bridge is game-art geometry, not an engineered structure or a verified common track gauge. Each model has its own physical scale; no assembled running railway scene is claimed.

Meshes contain merged coplanar exterior faces from native occupancy and use per-face flat palette materials, so no texture UVs are needed. GLB and FBX contain asset geometry only. BLEND includes a separate STUDIO collection for reproducible previews. The station platform and bridge foundations are intentional architectural parts; no common diorama floor is authored.

Only voxel/mountain_railway was written. Accepted farm and harbor creative files remained frozen and were not inspected or copied. No other theme creative resources, ForestDemo, previous Blender assets, Git or live shared Blender scene were accessed. The sole visual reference was REF/voxel/mountain_railway/reference.png; only generic parent-owned voxel tools were shared. No external references were consulted.

Files are frozen on submission. This completes this worker's three assigned themes; no further theme is queued.