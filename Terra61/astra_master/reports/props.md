# Station furnishings report

| Asset | Authored bounds, metres (X, Y, Z) | Triangles |
| --- | --- | ---: |
| `station_gaslamp.glb` | (−0.29, −0.29, 0) to (0.29, 0.29, 4.0) | 690 |
| `station_bench.glb` | (−1.05, −0.34, 0) to (1.05, 0.3968, 0.9934) | 540 |
| `station_clock_sign.glb` | (−0.73, −0.22, 0) to (0.72, 0.22, 3.78) | 854 |

Origins are centred on the prop footprint at ground Z=0; the bench faces authoring −Y. The gaslamp’s plinth is 0.45 m across and the lantern’s roof is 0.58 m across. The glTF exports contain the standard single root rotation of −90° around X, so they import Y-up with the bench front toward +Z.

The lamp includes a shaped plinth and post, brass bands, framed tapered lantern, pitched cap and finial. Its amber glazing uses an embedded reference crop as an emissive texture; the emissive material is self-lit but does not add a light source to the scene. The bench uses five separate seat and five back slats, bowed cast-iron arms, legs and curved under-seat supports. The free-standing platform clock includes a thick round casing, a curved cast-iron bracket and a suspended number 3 sign. Its clock face and platform number are readable from either side. Small iron relief is painted on texture rather than modeled as scrollwork. Iron, brass, wood, clock and ornament use generated base-colour, normal and ORM maps; the lantern uses its cropped base-colour and emissive texture, while the platform number uses a reference crop and scalar roughness. The derived normal and roughness maps are approximate. All textures are embedded in each GLB and every triangle has UVs and normals.

Files are in `station/modules/props/`, including `manifest.json`, `test_props.py` and `furnishings_preview.png`. The diagnostic is a software render of the authored triangles and textures. Rebuild with `python station/src/build_props.py`; the script imports the shared geometry/GLB utilities in `station/src/build_architecture.py` and uses the source textures in `station/textures/`.

Validation: `python station/modules/props/test_props.py` reloaded all three GLBs; verified embedded images, finite vertices, UVs and unit normals, valid indices and nondegenerate triangles, Y-up conversion, bounds, triangle budgets and the gaslamp’s emissive material. The clock and sign were reviewed from both sides in the diagnostic renderer.
