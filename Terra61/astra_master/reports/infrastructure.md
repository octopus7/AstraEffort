# Infrastructure modules

Four independent, reusable GLB modules are in `modules/infrastructure/`. Authoring coordinates are metres, X across the module, Y into its depth, and Z up; X=0 is the module centre, Y=0 is the front, and Z=0 is ground. Each GLB has a single root rotation of −90° around X for glTF Y-up. Geometry remains in the original Z-up authoring coordinates beneath the root.

| Module | Author-space bounds (m) | Triangles | Assembly |
| --- | --- | ---: | --- |
| `platform_segment.glb` | X −2…2, Y 0…8, Z 0…1 | 140 | Repeat every 8 m along Y. |
| `track_segment.glb` | X −1.5…1.5, Y 0…8, Z 0…0.22 | 244 | Repeat every 8 m along Y. |
| `platform_ramp.glb` | X −2…2, Y 0…8, Z 0…1 | 20 | Ground at Y=0; join its high end at Y=8 to the front of a platform segment. |
| `plaza_tile.glb` | X −4…4, Y 0…8, Z 0…0.12 | 24 | Ground-level paving tile; repeat or place independently. |

Track rail centres are X=−0.7175 and +0.7175 m, for a 1.435 m centre gauge; the rail running surface is **Z=0.22 m**. Twelve timber sleepers are evenly spaced in each segment. As one example, an adjacent track on the right of a centred platform can be placed at X=3.5 m, where their outside bounds meet. To place the ramp in front of a platform at Y=0, translate the ramp −8 m along author-space Y.

All materials have embedded base-colour, normal and packed metallic/roughness images made from the generated source files in `textures/`. Brick, paving and ballast UVs are scaled individually so the small surface detail does not require geometry. The plaza has continuous dark paving on its entire top without a contrasting border; ten mirrored image repeats across each 8 m side align the texture at tile seams. Maps use mirrored repeat to reduce boundary seams and are embedded at 512×512 for power-of-two repeat support. The normal/roughness maps are approximate derivatives of image colour, not surveyed physical materials. The manifest records the material-image names, repeats, bounds, mesh names, and triangle counts.

The source is `src/build_infrastructure.py`; run it from any directory to rebuild using the shared `textures/` files, or pass `--only plaza_tile` to rebuild only the plaza and its manifest entry. `python -m unittest station/modules/infrastructure/test_infrastructure.py -v` verifies the GLBs' bounds, triangle budgets, valid and non-degenerate UVs and normals, indices, root rotation, rail gauge/height, embedded image decoding, and plaza top material and seam alignment. Independent reloads with `pygltflib` and `trimesh` confirmed the Y-up bounds and image data. Rendered visual review belongs to the assembled-scene stage.
