# Harbor delivery

Four original voxel models are ready for parent review: Harbor working fishing boat, Lantern harbor lighthouse, Barrel-roof harbor warehouse, and Four-leg harbor cargo crane. Native VOX is the source of truth. Each asset has large and half native grids plus BLEND, GLB and FBX outputs.

## Actual timing

- Start UTC: 2026-10-23T14:27:39Z
- Start KST: 2026-10-23T23:27:39+09:00
- Finish UTC: 2026-10-23T14:45:24.634Z
- Finish KST: 2026-10-23T23:45:24.634+09:00
- Elapsed worker wall seconds: 1065.635
- Final independent verification: 13.178 seconds.
- Sum of eight actual rear render intervals: 70.831 seconds; this excludes Blender startup/file loading.
- Worker image generation: 0 seconds. No worker image-generation request was made.

| Build record | Actual start UTC | Actual finish UTC | Execution seconds |
|---|---|---|---:|
| build_validation_initial.json | 2026-10-23T14:36:29.452912+00:00 | 2026-10-23T14:37:49.266350+00:00 | 79.814 |
| build_validation_boat_revision.json | 2026-10-23T14:38:37.655474+00:00 | 2026-10-23T14:38:58.474778+00:00 | 20.819 |
| build_validation_lighthouse_revision.json | 2026-10-23T14:40:19.264964+00:00 | 2026-10-23T14:40:40.347295+00:00 | 21.082 |
| build_validation_crane_revision.json | 2026-10-23T14:41:16.368422+00:00 | 2026-10-23T14:41:37.222339+00:00 | 20.853 |

Build execution includes export and primary rendering. The four build intervals, rear rendering and independent verification ran sequentially. Authoring, review and report time remain included in total wall time without being invented as separate measured durations.

## Models

| Asset | Variant | Grid XYZ | Occupied cells | Triangles | Physical grid XYZ (m) |
|---|---|---|---:|---:|---|
| fishing_boat | large | 80 x 128 x 108 | 262,559 | 16,488 | 4.8 x 7.68 x 6.480 |
| fishing_boat | half | 40 x 64 x 54 | 36,318 | 5,396 | 4.8 x 7.68 x 6.480 |
| lighthouse | large | 76 x 76 x 128 | 175,470 | 15,166 | 5.7 x 5.7 x 9.6 |
| lighthouse | half | 38 x 38 x 64 | 24,494 | 5,252 | 5.7 x 5.7 x 9.6 |
| warehouse | large | 128 x 112 x 96 | 392,386 | 12,650 | 9.6 x 8.4 x 7.200 |
| warehouse | half | 64 x 56 x 48 | 56,555 | 4,102 | 9.6 x 8.4 x 7.200 |
| cargo_crane | large | 100 x 128 x 128 | 108,860 | 19,438 | 7.000 x 8.96 x 8.96 |
| cargo_crane | half | 50 x 64 x 64 | 16,949 | 6,692 | 7.000 x 8.96 x 8.96 |

All large grids have even dimensions and longest axis 128. Each half grid has exactly half the cells along every axis and twice the meters per voxel, so every large/half pair has identical physical grid extents. Conservative resampling may expand an occupied surface by at most one original large voxel. No mesh scaling was used to create the half versions, and no manual half-grid correction was needed.

## Deliverables and evidence

Each assets/ASSET/{large,half} directory contains ASSET.vox, ASSET.blend, ASSET.glb, ASSET.fbx, metadata.json, preview.png and preview_rear.png. The delivery totals are four assets, eight variants, 32 model-format files and 16 actual preview PNGs. Source and provenance are in build.py, capture_rear.py, palette.json and provenance.json. The two capture manifests record actual settings/timestamps and source/image hashes. DELIVERY.json inventories final file hashes.

| Asset | Primary previews | Rear previews |
|---|---|---|
| fishing_boat | [large](assets/fishing_boat/large/preview.png) / [half](assets/fishing_boat/half/preview.png) | [large rear](assets/fishing_boat/large/preview_rear.png) / [half rear](assets/fishing_boat/half/preview_rear.png) |
| lighthouse | [large](assets/lighthouse/large/preview.png) / [half](assets/lighthouse/half/preview.png) | [large rear](assets/lighthouse/large/preview_rear.png) / [half rear](assets/lighthouse/half/preview_rear.png) |
| warehouse | [large](assets/warehouse/large/preview.png) / [half](assets/warehouse/half/preview.png) | [large rear](assets/warehouse/large/preview_rear.png) / [half rear](assets/warehouse/half/preview_rear.png) |
| cargo_crane | [large](assets/cargo_crane/large/preview.png) / [half](assets/cargo_crane/half/preview.png) | [large rear](assets/cargo_crane/large/preview_rear.png) / [half rear](assets/cargo_crane/half/preview_rear.png) |

The final independent verifier reports passed=true, asset_count=4, variant_count=8 and zero errors. It reparses the native VOX occupancy, palette, coordinates and grids, then freshly imports BLEND, GLB and FBX to verify bounds, triangle counts and palette assignment against the native occupied-cell boundary. Every final format import has zero degenerate triangles, invalid boundary triangles, invalid material triangles and off-grid coordinates. GLB/FBX contain asset geometry only. BLEND files additionally retain a separately named STUDIO collection to reproduce the render evidence. Full evidence is in validation_export.json, validation_export.log, the build records and logs.

All sixteen final previews were opened and inspected. VISUAL_REVIEW.md records the checks and the three source corrections made after first rendering: uncovered timber boat deck, visible lighthouse lantern above its lowered gallery rail, and visible crane cab with separate winch placement. No optional visual polish loop followed those corrections.

## Limitations and scope

These are static assets. No rig, animation, collision, LOD chain or game-engine integration is supplied. Glazing is opaque; the lighthouse has actual open lantern framing and a modeled lamp but no optical beam or transmission simulation. The boat has no water/physics simulation. Small grooves and narrow openings simplify at half resolution. Per-face flat palette materials need no texture UVs. Studio floor/light/camera objects are absent from GLB and FBX exports; the warehouse's attached loading deck and other architectural foundations are intentional asset geometry.

Only voxel/harbor was authored. The accepted farm files remained frozen and were not read or copied; other themes, ForestDemo, previous Blender creative assets, Git and shared live Blender state were not accessed. The only visual reference was REF/voxel/harbor/reference.png. Shared parent-owned generic voxel utilities were used for export and verification. No external sources were consulted.

The harbor delivery is frozen on submission. Mountain_railway remains queued until explicit parent dispatch.