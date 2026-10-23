# Farm delivery

Four original farm assets are ready for parent review: Orchard tractor, Timber harvest barn, Raised grain silo, and Four-sail grain windmill. Each has two actual voxel resolutions and native VOX, BLEND, GLB and FBX files. Native VOX is authoritative.

## Actual timing

- Worker start UTC: 2026-10-23T14:05:33Z
- Worker start KST: 2026-10-23T23:05:33+09:00
- Worker finish UTC: 2026-10-23T14:24:39.303Z
- Worker finish KST: 2026-10-23T23:24:39.303+09:00
- Elapsed worker wall seconds: 1146.303
- Initial build/export/primary renders: 92.507 seconds.
- Silo ladder revision build/export/primary renders: 20.406 seconds.
- Silo canvas revision build/export/primary renders: 28.360 seconds.
- Initial independent verification: 22.046 seconds.
- Intermediate independent verification after the ladder revision: 23.380 seconds.
- Final independent verification: 26.855 seconds.
- Sum of eight rear render intervals: 80.529 seconds. This excludes process startup and file loading; build and verification timings overlap neither each other nor rear rendering.
- Worker image generation: 0 seconds. The supplied reference was viewed, and no image-generation tool was invoked by this worker.

## Models and counts

| Asset | Version | Grid XYZ | Occupied cells | Surface triangles | Physical grid XYZ (m) |
|---|---|---|---:|---:|---|
| tractor | large | 96 x 128 x 96 | 336,979 | 27,244 | 3.84 x 5.12 x 3.84 |
| tractor | half | 48 x 64 x 48 | 46,602 | 9,078 | 3.84 x 5.12 x 3.84 |
| barn | large | 120 x 128 x 120 | 414,988 | 24,102 | 7.800 x 8.32 x 7.800 |
| barn | half | 60 x 64 x 60 | 61,364 | 10,762 | 7.800 x 8.32 x 7.800 |
| silo | large | 80 x 92 x 128 | 248,171 | 29,428 | 4.4 x 5.06 x 7.04 |
| silo | half | 40 x 46 x 64 | 34,791 | 10,116 | 4.4 x 5.06 x 7.04 |
| windmill | large | 128 x 96 x 128 | 215,172 | 23,784 | 7.04 x 5.28 x 7.04 |
| windmill | half | 64 x 48 x 64 | 30,832 | 8,796 | 7.04 x 5.28 x 7.04 |

The large grids have longest axis 128 and even dimensions. Each half grid is exactly half on all three axes; its meters per voxel doubles. The physical grid extents are identical within every pair. Conservative occupancy reduction may move a visible surface outward by one original large cell. This is a native coarse voxel model, not a scaled high-resolution mesh.

## Delivered paths

- Source geometry: build.py. Rear capture script: capture_rear.py. Named palette: palette.json. Reference provenance: provenance.json.
- assets/ASSET/large and assets/ASSET/half each contain ASSET.vox, ASSET.blend, ASSET.glb, ASSET.fbx, metadata.json, preview.png and preview_rear.png. Total: 4 assets, 8 variants, 32 model-format files, 16 actual render previews.
- Primary and rear capture provenance: capture_manifest.json and capture_rear_manifest.json.
- Validation evidence: build_validation.json, preserved initial and selective build records, validation_export.json, the initial verifier record, and build/verification logs.
- Individual image review: VISUAL_REVIEW.md. Delivery file hashes: DELIVERY.json.

| Asset | Main previews | Rear previews |
|---|---|---|
| tractor | [large](assets/tractor/large/preview.png) / [half](assets/tractor/half/preview.png) | [large rear](assets/tractor/large/preview_rear.png) / [half rear](assets/tractor/half/preview_rear.png) |
| barn | [large](assets/barn/large/preview.png) / [half](assets/barn/half/preview.png) | [large rear](assets/barn/large/preview_rear.png) / [half rear](assets/barn/half/preview_rear.png) |
| silo | [large](assets/silo/large/preview.png) / [half](assets/silo/half/preview.png) | [large rear](assets/silo/large/preview_rear.png) / [half rear](assets/silo/half/preview_rear.png) |
| windmill | [large](assets/windmill/large/preview.png) / [half](assets/windmill/half/preview.png) | [large rear](assets/windmill/large/preview_rear.png) / [half rear](assets/windmill/half/preview_rear.png) |

## Verification

The final independent verifier exited successfully and reports passed=true, asset_count=4, variant_count=8 and zero errors. It reparsed all native VOX files and checked occupancy/hash/palette/grid parity. Fresh BLEND, GLB and FBX imports were checked against native occupancy for every triangle: true exterior voxel boundary, outward orientation, correct palette, finite on-grid coordinates, nonzero area, matching triangles and bounds. All three import formats report zero degenerate triangles, invalid boundary triangles, invalid material triangles and off-grid coordinates for all eight variants. GLB/FBX contain asset geometry only. The BLEND files additionally retain a separately named STUDIO collection for reproducible previews.

All sixteen final PNGs were opened and inspected. The visual source revision after first review was the silo ladder placement: it moved to the front-left side so that the discharge outlet remains visible. The silo canvas Y axis was subsequently increased from 90 to 92 cells while leaving its authored occupied shape intact. Both final silo primary and rear pairs were refreshed and inspected, then all eight final variants passed a fresh independent verification. No per-half manual geometry edits were required.

## Limitations and scope

The deliverables are static models: no rig, animation, LOD chain, collision, or game-engine integration is supplied. Glazing is an opaque flat palette color. Small decorative material divisions become broader at half resolution. The silo is a visual grain-storage model without fluid or grain simulation. The asset meshes use merged coplanar exterior voxel faces and per-face palette materials; they require no texture UVs. Preview ground planes and lights belong only to the BLEND studio setup and are absent from GLB/FBX asset exports.

Only this farm directory was authored. No other theme's creative files, ForestDemo resources, earlier Blender assets, shared live Blender scene or Git state were inspected or modified. The farm reference at REF/voxel/farm/reference.png is the sole visual reference; no external web sources were used. All creative geometry is original source code in build.py.

Files are frozen on submission pending parent acceptance. Harbor and mountain_railway have not been started.