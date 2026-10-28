# Platform and track module

A freestanding, repeatable 20 m wide by 6 m long Victorian station bay. The GLB contains real geometry and embedded PBR base-color textures; it is not a flat drawing or image plane.

## Files

- `platform_track_bay.glb` — finished model, with 11 named mesh/material groups and embedded textures.
- `preview_overview.png` and `preview_track_detail.png` — orthographic renders made directly from the exported GLB meshes and UV textures.
- `build_platform.py` — deterministic generator for geometry, materials and packaged textures.
- `render_preview.py` — lightweight CPU rasterizer used to render the exported GLB.
- `verify_platform.py` — checks mesh dimensions, gauge, repeat spacing, and embedded texture integrity.
- `mesh_stats.json` — machine-readable bounds, component triangle counts and rail coordinates.
- `textures/` — copies of all five base-color images used by the model.

## Placement and dimensions

All units are metres. Up is +Y; +Z runs along the railway. The bay occupies X = -10 to 10, Y = 0 to 0.9, and Z = 0 to 6. Duplicate at integer multiples of 6 m along Z without scaling. The two track-bed centers are X = -4 and +4. Each track has two continuous rail profiles with a nominal top of Y = 0.240 m; the cosmetic polished surface is at Y = 0.24015 m to prevent coincident surfaces. The running faces are 1.435 m apart measured 14 mm below the rail top. Rail center positions are -4.7515, -3.2485, 3.2485, and 4.7515 m.

The left, center and right platforms occupy X ranges [-10,-6], [-2,2], and [6,10], respectively. Their tops are at Y = 0.9 m. Each platform has masonry sides, pale chamfered coping and a UV-mapped paved top. The sleepers run across X, repeat at 0.6 m intervals along Z, and have a 0.24 m longitudinal width. The dark ballast plane is at Y = 0.045 m and contains additional low-poly stones. The track and walkway are clear of canopy, columns, people, trains and props so other station modules can be placed separately.

## Textures and rendering

`textures/paving.png` is based on the AI-generated project image `materials/ai_worn_platform_paving.png`; `textures/ballast.png` is based on the AI-generated project image `materials/ai_railway_ballast.png`. The copies are UV-mapped to the model and embedded in the GLB. The eight-pixel longitudinal edges of those images were blended to improve joins between consecutive bays. `ashlar.png`, `coping.png`, and `wood.png` were generated procedurally in the source script. The material roughness and metalness are constant PBR values; no normal maps are supplied.

To rebuild, run `python build_platform.py` with NumPy, Pillow, SciPy and trimesh installed. If moved out of the full project, the script retains the already-baked textures in `textures/`; if those images are missing too, it creates procedural fallbacks. Run `python render_preview.py` to regenerate the previews from the GLB, and `python verify_platform.py` to check the model (also requires pygltflib).
