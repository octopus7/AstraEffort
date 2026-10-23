# Factory voxel delivery

Four original assets are ready for parent review. Files are frozen after this handoff; the next theme has not started.

## Actual timing

- Start: 2026-10-23T14:05:47+00:00 UTC / 2026-10-23T23:05:47+09:00 KST.
- Finish: 2026-10-23T14:26:59.341220+00:00 UTC / 2026-10-23T23:26:59.341220+09:00 KST.
- Elapsed wall time: 1272.341 seconds.
- Worker assignment: gpt-6-astra with max reasoning. The dispatch API exposes no separate Fast switch; none is claimed.
- Image generation: none (0 seconds). Only the assigned factory reference was viewed.

| Recorded Blender process | Wall seconds |
|---|---:|
| Initial full build | 90.406 |
| Grille correction rebuild | 87.407 |
| Occupied-bounds alignment rebuild | 85.989 |
| First verification/evidence: feature_regression | 0.526 |
| First verification/evidence: independent_export_validation | 7.364 |
| First verification/evidence: rear_qa_renders | 35.200 |
| Final verification/evidence: feature_regression | 1.123 |
| Final verification/evidence: independent_export_validation | 7.545 |
| Final verification/evidence: rear_qa_renders | 37.192 |

The above process timers include startup. Two brief failing native-feature diagnostic runs were not separately timed and are excluded from the recorded process total; they remain in the logs. Authoring, review and documentation are included in the overall elapsed wall time. Tool readiness overlapped geometry authoring.

## Models and native grids

Each variant has its own native uint8 occupancy. Large/half meters per voxel are respectively 0.04/0.08 for the press, 0.045/0.09 for the conveyor, 0.035/0.07 for the forklift, and 0.04/0.08 for the generator. Palette index 0 is empty; visible indices begin at 1.

| Asset | Large / half grid | Physical grid extent (m) | Large / half occupied voxels | Large / half triangles |
|---|---|---|---:|---:|
| production_machine | 112 × 88 × 128 / 56 × 44 × 64 | 4.48 × 3.52 × 5.12 | 457,400 / 60,765 | 6,704 / 2,514 |
| conveyor | 128 × 64 × 76 / 64 × 32 × 38 | 5.76 × 2.88 × 3.42 | 91,777 / 14,296 | 6,422 / 2,794 |
| forklift | 88 × 128 × 112 / 44 × 64 × 56 | 3.08 × 4.48 × 3.92 | 282,869 / 40,591 | 9,686 / 4,522 |
| generator | 128 × 72 × 96 / 64 × 36 × 48 | 5.12 × 2.88 × 3.84 | 386,900 / 50,888 | 5,074 / 2,324 |

All axes are even and each large grid's longest axis is 128. Half dimensions divide every axis by exactly two and meters per voxel double. Both grid extents and occupied physical bounds match exactly for each delivered pair. The half mesh is rebuilt from the independent reduced grid. There are no hand-authored half-grid corrections.

## Delivery paths

- `build.py`: original procedural geometry, with pure `make_assets()` returning four `Asset` records.
- `palette.json`: restrained mustard/slate/ivory palette and color roles.
- `assets/{production_machine,conveyor,forklift,generator}/{large,half}/`: named `.vox`, `.blend`, `.glb`, `.fbx`, `preview.png`, and `metadata.json`.
- `capture_manifest.json`: eight actual same-camera Blender render captures, settings and hashes.
- `qa/`: four actual rear-view renders and their separate capture manifest.
- `build_validation.json`, `validation_export.json`, `feature_validation.json`, `visual_review.json`: validation evidence.
- `build*.log`, `validation_export.log`, `feature_check*.log`, `rear_qa*.log`, and `*_timing*.json`: actual process evidence.

VOX is authoritative. GLB/FBX contain only the surface mesh. The saved BLEND keeps an `ASSET` collection and a separate `STUDIO` collection for reproducible previews; its floor/camera/lights are excluded from exchange exports and native occupancy.

## Validation and visual review

The parent-owned independent verifier passed all 8 variants, reparsed native VOX independently, verified coordinates/color indices/counts/palette/occupancy and file hashes, then freshly opened/imported all 24 BLEND/GLB/FBX asset meshes. Every imported triangle had finite grid-aligned coordinates, nonzero area, the correct palette material, an outward normal and a true occupied-to-empty voxel boundary. Bounds, triangle counts and surface areas matched. No studio objects leaked into GLB/FBX.

All eight final front previews and four rear QA renders were visually inspected:

- **production_machine:** Open ram throat and die slots readable at both sizes; corrected motor grille remains slotted; rear accumulator/hoses and cabinet access details inspected.
- **conveyor:** Two rounded end roller assemblies, belt ribs, four supports and crates readable; corrected drive grille remains open in half; rear bracing inspected.
- **forklift:** Two separated forks, mast and open cab readable in both sizes; front and rear views show all four wheel positions; rear grille, step and seat inspected.
- **generator:** Rounded casing, service doors, end grille, skid pockets, exhaust and lifting eyes readable in both sizes; rear cable loop and outlet panel inspected.

Two corrections followed observed evidence. Odd-cell motor grille phases caused both half models to appear solid at the motor face; saved-native ray probes reproduced the loss and then passed after even-cell bar/slot alignment. An additional native bounds probe found three one-large-cell conservative expansions; moving the press accumulator cap, conveyor outer hub and forklift beacon extrema onto even cells produced exact occupied-bound equality. These were source-grid changes, not scaled-mesh substitutes.

The final feature report contains six passing checks: two exposed half-resolution grille traces and four exact occupied-bound comparisons. Preview evidence is actual Blender Cycles output (768 × 768, 24 samples, CPU, four threads, AgX). The reference is design input only.

## Limitations and references

Assets are static, joined colored voxel surface meshes. No rig, animation, collision, LOD chain or engine integration is supplied. Small bolts, chain links, slats and cable sections become chunkier at half resolution. Flat palette materials use no texture UVs or image textures. Native enclosed volume is occupied by design; exported meshes contain only exposed boundaries. Mechanical detail is an artistic functional representation, not an engineered simulation.

Design input: `../../REF/voxel/factory/reference.png`. Shared read-only implementation input: `../BRIEF.md`, `../_tools/API.md`, `voxelkit.py`, `blender_pipeline.py`, and `verify_theme.py`. No external asset, ForestDemo, other theme, prior Blender creative asset, image-generation output, shared live scene or Git operation was used.
