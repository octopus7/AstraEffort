# Locomotive and tender

The two reusable GLBs are in `modules/locomotive/`. Their authoring coordinates use metres, with X across the vehicle, Y toward the rear, Z up, centreline X=0, front Y=0, and wheel contact Z=0. Each has one −90° X root rotation for glTF Y-up.

| Module | Author-space bounds (m) | Triangles | Contents |
| --- | --- | ---: | --- |
| `locomotive.glb` | X −1.4…1.4, Y 0…10, Z 0…4.5 | 2,928 | Boiler, smokebox, headlamp, chimney, two domes, three driving axles, leading axle, rods, buffer beam and open-window cab. |
| `tender.glb` | X −1.4…1.4, Y 0…5, Z 0…3.6 | 772 | Coal bunker and load, two axles, frame and buffers. |

Every wheel centre is at X=±0.7175 m, corresponding to a 1.435 m centre gauge. Main driving-wheel radius is 0.96 m; the locomotive leading-wheel radius is 0.48 m; tender wheels are 0.54 m. Raising both modules by 0.22 m in author Z places their wheels on the track kit's running surface. For a straight coupled consist, put the tender's origin about 10.1 m behind the locomotive origin along author Y.

Wheel spokes and the cab's 726 panel are dedicated image charts, with wheel rims, rods, boiler curves and the cab openings represented in geometry. The inner chassis is 0.84 m wide so it does not obscure the wheels or the connecting rods. The red buffer beam is set behind the buffers, and a small amber headlamp sits above the smokebox. The chassis, cab and stack use dark iron while the wheel edges retain subtle weathering. The bunker load uses a darkened generated ballast image to suggest coal. Colour, approximate image-derived normal, and packed metallic/roughness maps are embedded in each GLB. Materials use the shared power-of-two mirrored-repeat exporter; see the manifest for filenames and named meshes.

The reproducible source is `src/build_locomotive.py`, using `src/build_infrastructure.py` for shared GLB and material export. Run `python station/src/build_locomotive.py` from the project root to regenerate both assets and the manifest, or add `--only locomotive` to rebuild the engine without replacing the tender. `python -m unittest station/modules/locomotive/test_locomotive.py -v` verifies dimensions, gauge, wheel contact, chassis clearance, buffer/lamp positions, triangle budgets, valid UVs and normals, image decoding and embedded material maps. Independent `pygltflib` and `trimesh` reloads confirmed both Y-up scene bounds and the embedded source images. The assembled-scene stage supplies rendered visual review.
