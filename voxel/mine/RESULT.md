# Mine voxel delivery

Four original mine models are ready for parent review and frozen on submission. Spaceport has not started.

## Actual timestamps and process times

- Start UTC: 2026-10-23T14:29:23+00:00; KST: 2026-10-23T23:29:23+09:00.
- Finish UTC: 2026-10-23T14:45:11.250225+00:00; KST: 2026-10-23T23:45:11.250225+09:00.
- Total elapsed wall time: 948.250 seconds, including authoring, inspection and documentation.
- Full eight-variant build/export/render: 83.926 seconds.
- native_features: 0.865 seconds.
- independent_export_validation: 17.861 seconds.
- Image generation: none (0 seconds).

Process times above include Blender startup. One production build was needed; no repeated polish build or optional secondary rendering pass was performed. All Blender processes used background factory-startup mode and four CPU threads.

## Models

| Model | Large / half grid | Physical grid size (m) | Large / half occupied voxels | Large / half triangles |
|---|---|---|---:|---:|
| excavator | 104 x 128 x 112 / 52 x 64 x 56 | 3.64 x 4.48 x 3.92 | 271,568 / 38,502 | 11,596 / 4,692 |
| mine_cart | 128 x 80 x 96 / 64 x 40 x 48 | 4.48 x 2.8 x 3.36 | 182,526 / 27,430 | 10,426 / 3,658 |
| mine_elevator | 116 x 92 x 128 / 58 x 46 x 64 | 5.22 x 4.14 x 5.76 | 159,073 / 24,698 | 20,092 / 6,454 |
| ore_sorter | 128 x 100 x 112 / 64 x 50 x 56 | 5.12 x 4 x 4.48 | 118,434 / 20,622 | 18,502 / 6,164 |

All large axes are even and the longest is 128. Every half axis is exactly divided by two and its voxel size doubles, preserving exact physical grid extents. Meters per voxel are 0.035/0.07 for excavator and cart, 0.045/0.09 for elevator, and 0.04/0.08 for sorter. Conservative occupied-bound expansion of up to one large cell is allowed by the assigned reduction semantics. No manual half-grid corrections were made. Native uint8 VOX occupancy is authoritative, with empty index 0 and visible palette indices starting at 1.

## Delivered files

- `build.py`: original pure `make_assets()` geometry authoring through the parent-owned generic API.
- `palette.json`: olive/cream/charcoal and copper-orange palette roles/RGBA values.
- `assets/{excavator,mine_cart,mine_elevator,ore_sorter}/{large,half}/`: named VOX, BLEND, GLB, FBX, `preview.png` and `metadata.json` for each variant.
- `capture_manifest.json`: eight actual matched-camera renders, actual timestamps, render settings and hashes.
- `validation_export.json` and `.log`: independent native and fresh format verification.
- `feature_validation.json`, `check_features.py`, `feature_check.log`: saved-native opening and cable-path checks.
- `build_validation.json`, `build.log`, `build_timing.json`, `check_timings.json`, `visual_review.json`, `STATUS.json` and this report.

GLB/FBX include only the exposed voxel surface mesh. BLEND retains separate `ASSET` and `STUDIO` collections for reproducible previews; studio floor, camera and lights do not enter native VOX or exchange exports.

## Verification and visual findings

The independent parent verifier passed all 8 variants and all 24 fresh BLEND/GLB/FBX asset inspections with no errors. It reparsed native VOX coordinates, counts, palette and occupancy hashes; confirmed exact grid halving and physical grid sizes; and checked file hashes. Imported triangles were finite, nondegenerate, on the exact occupied-to-empty voxel boundary with outward normals and correct palette assignment. Bounds, triangles and surface area matched metadata. GLB/FBX contained no studio objects.

Twelve additional feature checks passed independently on each saved resolution: hollow bucket volume and solid side/back, two track cavities, open cart bed and four wheel centers, clear cage portal and open sheave web, continuous sampled cage/winch cables, open sorter hopper, screen aperture and occupied screen rail/discharge belt.

All eight actual previews were inspected:

- **excavator:** Both previews show a deep empty bucket mouth, separate articulated arm links and rods, framed cab, tread loop and rollers. Native probes additionally confirm both track interiors remain open.
- **mine_cart:** The deep open tapered bed and thick rim read at both sizes; wheel flanges, braces, couplers and hand brake remain substantial.
- **mine_elevator:** Four-post headframe, exposed sheave, cage opening, winding drum, continuous cable route and stairs read at both sizes. Close twin strands merge locally in the half grid.
- **ore_sorter:** Open hopper, sloping perforated screen, short rising discharge belt and three separately framed ore bins read at both sizes; aperture pattern survives reduction.

Preview settings are Cycles CPU, four threads, 24 samples, 768 x 768, orthographic matching cameras, AgX and denoising. No image-generation output is presented as scene evidence.

## Limitations and provenance

Static colored voxel models only: no rig, animation, collision, LOD chain or game-engine integration. Flat palette materials need no texture UVs; cab glass is an opaque stylized color. Small pins, chain-like ribs, cables and screen cells become chunkier at half resolution; two close elevator cable strands may merge locally while their occupied route stays continuous. Mechanics are visual representations rather than engineered simulations.

Only the assigned `../../REF/voxel/mine/reference.png` was viewed as design input. Geometry was independently authored without reading or copying factory creative source, another theme, ForestDemo, prior Blender creative assets, or an external model. Generic parent-owned `../_tools` utilities and the common brief/API were the sole shared implementation resources. No Git operations, installations, image generation, subagents or shared live Blender session were used.
