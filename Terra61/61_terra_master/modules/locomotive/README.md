# Steam locomotive module

A static, self-contained 3D GLB of a Victorian steam locomotive. The boiler, smokebox door, chimney, cab, three pairs of large spoked driving wheels, side coupling rods, buffers, lamps and slatted cowcatcher are modeled geometry. It includes one small leading axle and one small trailing axle. It does not include a tender, cars, track or station building.

## Files

- `steam_locomotive.glb` — the model with named, UV-mapped material groups and embedded images.
- `preview_three_quarter.png`, `preview_side.png`, `preview_front.png` — rendered directly from the exported GLB meshes and their UV textures.
- `build_locomotive.py` — deterministic geometry, material and texture generator.
- `render_preview.py` — CPU rasterizer that reads and renders the exported GLB.
- `verify_locomotive.py` — checks dimensions, wheel contact locations, geometry and embedded textures.
- `mesh_stats.json` — exact bounding box and component triangle counts.
- `textures/` — the four embedded base-color textures, provided separately as well.

## Coordinates and placement

Units are meters, with Y up. The frontmost pilot edge is at Z = 0; the back of the coupling is at Z = 12.95, and the engine faces toward negative Z. The overall bounds are X = -1.38 to +1.38, Y = 0 to 4.21, Z = 0 to 12.95 m. The locomotive is therefore 2.76 m wide.

All wheel bottoms touch local Y = 0. The right and left wheel running surfaces are centered at X = +0.7515 m and -0.7515 m. This matches the rail-head centers in the station's 1.435 m inside-gauge track. Large driving axles are at Z = 4.05, 6.20 and 8.35 m, with 0.80 m radius; the smaller axles are at Z = 2.10 and 10.90 m, with 0.42 m radius. For the project track, place the model at Y = 0.24 m and at either X = -4 m or X = +4 m; choose Z to position the front pilot. The wheels and linkage are fixed in a single static pose, not rigged or animated.

## Material provenance

`aged_iron.png` is a brightened copy of the project-provided AI-generated `materials/ai_aged_cast_iron.png`. `boiler_sheet.png` and `smokebox_door.png` are derived from that image with added procedural plate seams and rivet details. `red_painted_iron.png` is generated procedurally. Brass, dark iron, cab glazing, polished steel and lamp lenses use constant PBR material colors; no normal maps are included. All image textures are embedded in the GLB.

## Rebuilding

Run `python build_locomotive.py` with NumPy, Pillow and trimesh installed. If the project-level AI source image is unavailable, the generator uses the packaged `textures/aged_iron.png` as its source. Run `python render_preview.py` to recreate previews from the exported GLB. Run `python verify_locomotive.py` with pygltflib installed for dimension, wheel-position, texture and mesh checks.
