# Luggage cart and freight props

Three reusable GLBs are in `modules/freight_props/`. The authoring axes are X across, Y toward the rear, and Z up, in metres; X=0 is the centre, front Y=0 and the base is at Z=0. Each export has one root rotation of −90° about X for glTF Y-up.

| Module | Author-space bounds (m) | Triangles | Contents |
| --- | --- | ---: | --- |
| `luggage_cart.glb` | X −0.6…0.6, Y 0…2, Z 0…1.5 | 1,144 | Wooden cart, tubular handle, four open-spoked wheels, and three stacked trunks. |
| `crate.glb` | X −0.4…0.4, Y 0…0.8, Z 0…0.8 | 12 | Square timber shipping crate. |
| `barrel.glb` | X −0.325…0.325, Y 0…0.65, Z 0…0.9 | 216 | Bulging wood barrel with two iron hoops. |

The luggage panels are individual tight crops of the blue, brown and tan case faces from `references/11_luggage_cart_reference.png`, rather than an image of the entire cart. Dedicated lid charts are assembled from the same source crops' leather and strap details. Crop rectangles are recorded in the manifest; the script derives approximate normal and roughness/metalness maps for them. Boards, staves, small straps and latches use image detail. Cart wheels and handles and barrel hoops are geometry.

All GLBs embed their colour, normal and packed metallic/roughness images. The generated cropped textures and copies of the shared wood, iron and brass maps are in `modules/freight_props/textures/`. The source is `src/build_freight_props.py`, which reuses `src/build_infrastructure.py` and `src/build_locomotive.py` for GLB export and geometric helpers. Run `python station/src/build_freight_props.py` to reproduce all three modules and the manifest from the shared material images and luggage reference.

`python -m unittest station/modules/freight_props/test_freight_props.py -v` verifies the bounds, triangle budgets, wheel contact, UVs and normals, image decoding and embedded maps. Independent `pygltflib` and `trimesh` reloads confirmed the Y-up bounds and embedded images. Rendered visual review belongs to the assembled-scene stage.
