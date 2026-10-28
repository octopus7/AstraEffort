# Coal tender module

A static, self-contained 3D coal tender for the station's steam locomotive. The underframe, two bogies, four axles, eight spoked wheels, buffers, couplers, end ladders and grab rails are actual meshes. The coal has a low-density modeled surface with its fine lumps and highlights in the UV texture; rivets and the side pinstripe are also textured. It contains no track or station geometry.

## Files

- `coal_tender.glb` — the model, with named UV-mapped mesh groups and embedded textures.
- `preview_three_quarter.png`, `preview_side.png`, `preview_rear.png` — actual renders of the exported GLB meshes and embedded textures.
- `build_tender.py`, `geometry.py` — deterministic source generator and geometry helpers.
- `render_preview.py` — a CPU rasterizer that reads and renders the saved GLB.
- `verify_tender.py` — checks the bounding box, wheel contact positions, coupling and embedded textures.
- `mesh_stats.json` — dimensions and triangle counts by mesh.
- `textures/` — the four base-color images used by the model.

## Dimensions and assembly

Units are meters and Y is up. Front faces -Z, with the front coupler at local Z = 0; the rear coupler ends at Z = 6.90. Bounds are X = -1.35 to +1.35, Y = 0 to approximately 3.160, and Z = 0 to 6.90 m. The overall width is 2.70 m. Wheel contact is at local Y = 0, with tread centerlines at X = -0.7515 and +0.7515 m. Axles are at Z = 1.50, 2.55, 4.45 and 5.50 m; wheel radius is 0.42 m.

The coupler center is at Y = 1.30 m. For the station rail module, place the tender at Y = 0.24 m and at X = -4 or +4 m. If the companion locomotive is at Z = 0, placing this tender's origin at Z = 12.95 m meets the locomotive's rear coupler at the tender's front coupling face. The wheels and fittings are modeled in a fixed pose; no animation or physics constraints are included.

## Texture provenance

`aged_iron.png` is a brightened copy of the project-provided AI-generated `materials/ai_aged_cast_iron.png`. `riveted_side.png` derives from it, with procedurally drawn seams, rivets and pinstripes. `coal.png` derives from the project-provided AI-generated `materials/ai_railway_ballast.png`, cropped, desaturated and darkened for a coal appearance. `red_oxide.png` is procedurally generated. The remainder are constant PBR colors, with no normal maps. The coal silhouette mesh has 512 triangles; the small coal shapes are texture detail. All four images are embedded in the GLB.

## Rebuilding

Run `python build_tender.py` with NumPy, Pillow and trimesh. If the project-level AI sources are unavailable, the generator uses the baked `textures/aged_iron.png` and `textures/coal.png`. Run `python render_preview.py` to reproduce the previews from the exported GLB, and `python verify_tender.py` with pygltflib installed to check the model.
