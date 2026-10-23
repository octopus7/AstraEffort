# Mine haul truck addition

One original `haul_truck` in large and half native grids is ready for review and frozen on submission. Accepted original mine assets and the factory addition remain unchanged. Construction and all phase B work remain unstarted.

## Actual timing

- Start UTC: 2026-10-23T15:41:35+00:00; KST: 2026-10-24T00:41:35+09:00.
- Finish UTC: 2026-10-23T15:49:04.970858+00:00; KST: 2026-10-24T00:49:04.970858+09:00.
- Elapsed wall time: 449.971 seconds, including authoring, visual review and documentation.
- Single build/export/render process: 20.956 seconds.
- Saved-native feature checks: 0.665 seconds.
- Independent native/format verification process: 4.757 seconds.
- Image generation: none (0 seconds). No rebuilds, optional views or polish passes.

Process timings include startup. Every Blender process used background factory-startup mode, four threads and `--python-exit-code 1`.

## Asset and native statistics

| Variant | Grid | Cell size (m) | Occupied voxels | Triangles |
|---|---|---:|---:|---:|
| Large | 104 x 128 x 96 | 0.055 | 389,324 | 19,378 |
| Half | 52 x 64 x 48 | 0.11 | 56,236 | 6,706 |

Exact physical grid extents are 5.72 x 7.04 x 5.28 m at both sizes. All large axes are even and longest 128. Half occupancy independently divides every axis by two and doubles cell size. Native uint8 VOX is authoritative, with index 0 empty and visible indices 1+. Conservative occupied-bound expansion by one large cell is permitted. No hand-edited half grid or scaled-mesh substitute was used.

The six-wheel off-road ore hauler includes huge treaded tires, front offset cab and engine deck, a deep EMPTY tapered dump body, thick rim, cab canopy, reinforcing ribs, rear hinge, two external hoist cylinders, access ladder and purposeful service grilles. Its mine palette is preserved by permission; all geometry was independently authored.

## Delivered paths

- `build.py`: pure `make_assets()` returning only this asset, using the absolute parent generic `_tools` path.
- `assets/haul_truck/{large,half}/`: VOX, BLEND, GLB, FBX, actual `preview.png`, and metadata.
- `palette.json`, `capture_manifest.json`, `build_validation.json`, `validation_export.json`, `feature_validation.json`, `visual_review.json`, timing JSON and logs.
- `check_features.py`, `STATUS.json`, this report and the bookkeeping script.

GLB/FBX contain only exposed voxel asset surfaces. BLEND separates ASSET from its preview STUDIO; the studio floor/camera/lights are excluded from native occupancy and exchange exports.

## Evidence

Independent verification passed both native grids and all six fresh BLEND/GLB/FBX inspections. It checked native count, palette, coordinate uniqueness/range, occupancy and file hashes; exact halving and physical grid sizes; finite coordinates, grid alignment, nonzero triangles, outward occupied-to-empty boundary surfaces, correct materials, bounds, triangle count and area. No studio objects entered GLB/FBX.

Five semantic checks passed per reopened native resolution: a deep empty bed region, six occupied wheel centers, bed floor/rim, offset cabin window, and hinge/hoist. The empty-region test examined 59,800 large-grid cells and 6,336 half-grid cells, all empty. Both actual previews were inspected and show the empty bed clearly; no correction was required. The parent also reported personal preview review and independent format verification passing before this record was finalized.

Capture settings: matched orthographic cameras, 768 x 768, Cycles CPU, four threads, 24 samples, AgX and denoising. Reference imagery is never used as rendered evidence.

## Limitations and provenance

Static colored voxel model only: no dump articulation/animation, rig, collision, LOD chain or engine integration. Cab glass is opaque stylized color. Palette materials require no texture UVs; no image textures were used. Tire lugs, ribs and small grille/bolt details simplify at half resolution. Mechanics depict useful forms rather than simulate machinery.

Inputs were the assigned `REF/voxel/mine/additions/reference.png`, permitted original mine palette, expansion/common brief/API and parent-owned generic utilities. No other creative theme source, original asset modification, ForestDemo, Git, image generation, installation, other agents or shared live Blender session was used.
