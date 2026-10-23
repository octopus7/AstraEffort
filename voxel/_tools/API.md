# Common authoring API (parent owned)

Import from voxelkit by adding voxel/_tools to sys.path. Utilities are being implemented by main; author geometry first and wait for the tools-ready message before running build/export.

`Grid(shape, palette)` creates a NumPy uint8 `grid.data` in X,Y,Z order. Shape is an even tuple, longest axis exactly 128. Palette is a list of RGB or RGBA 0-255 integer tuples; palette[0] is EMPTY, so insert (0,0,0,0) first. Real colors begin at 1. `grid.x`, `grid.y`, `grid.z` are sparse cell-center arrays (coordinate index + 0.5); you may set `grid.data[mask]=color_index` directly. All operations return self; color 0 carves empty volume.

- `box(lo, hi, color)` fills a half-open axis-aligned integer box.
- `roundbox(lo, hi, radius, color)` rounded SDF box, stepped voxel exterior.
- `ellipsoid(center, radii, color)` fills an ellipsoid.
- `cylinder(center, radius, length, axis, color)` capped cylinder; axis 0=X,1=Y,2=Z.
- `cone(center, radius_bottom, radius_top, length, axis, color)` tapered cylinder.
- `beam(a, b, radius, color)` filled capsule between 3D endpoints.
- `torus(center, major_radius, minor_radius, axis, color)` ring around axis.

`Asset(slug, label, grid, voxel_size=0.05, notes=None, half_postprocess=None)` represents an independent model. Callback `half_postprocess(half_grid)` is optional for deliberate functional detail corrections after conservative 2x reduction; document changes in notes.

Use a pure `make_assets()` function in build.py, returning list[Asset]. At bottom guard `if __name__ == '__main__': run_theme(Path(__file__).resolve().parent, make_assets())`.

`run_theme(root, assets)` writes and reparses both resolutions of native VOX, surfaces and exports, saves per-variant BLEND, actual same-camera PNG, metadata, capture manifest and theme geometry validation. Uses four CPU threads, modest Cycles samples. File paths are assets/SLUG/{large,half}/SLUG.{vox,blend,glb,fbx} and preview.png, metadata.json.

Meters per voxel doubles for half, same physical size by default. Front of asset is -Y, Z up; X left/right. Unit scale meters. Do not place all objects on a permanent shared diorama floor. Surface meshes have per-face palette materials and no interior cube faces; UV is unnecessary for flat colors. No polygon smooth shading or bevel modifiers; voxel data is authoritative.

Workers own only current theme files. Main owns this helper and independent export verification. Do not duplicate the export engine; request any needed change from parent.
