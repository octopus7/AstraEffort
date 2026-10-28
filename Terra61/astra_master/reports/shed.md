# Train shed and canopy modules

All three modules are self-contained GLB 2.0 files in `modules/shed/`, made from individually instanced, reusable beam and column meshes. Dimensions below are in authoring coordinates (meters, X right, Y toward station rear, Z up). Each GLB has one root quaternion `[-0.70710678, 0, 0, 0.70710678]` that converts authoring Z-up to glTF Y-up; positive authoring Y becomes negative glTF Z.

| Module | Design dimensions | Rendered triangles | Unique mesh triangles | Authored bounds min → max |
| --- | --- | ---: | ---: | --- |
| `shed_bay.glb` | 28 m clear span, 8 m depth, eaves 11 m, roof crown 22 m | 2,748 | 152 | `[-14.4, 0, 0]` → `[14.4, 8, 22.12]` |
| `front_arch.glb` | 28 m clear span, eaves 11 m, roof crown 22 m | 2,672 | 144 | `[-14.4, 0, 0]` → `[14.4, 0.8, 22.57]` |
| `platform_canopy_bay.glb` | 6 m wide, 8 m deep, 5 m overall high | 640 | 108 | `[-3, 0, 0]` → `[3, 8, 4.999]` |

The shed bay contains glazing over Y=0..8, thin longitudinal glazing bars, three light intermediate hoops, a cross-braced structural rib and columns at the far seam Y=8. Repeat at authoring Y=0, 8, 16, 24, 32, 40 for a 48 m shed; place `front_arch.glb` at Y=0 to supply the initial arch and supports. The roof panels and steel rib cross-sections slightly exceed the nominal crown, while the front arch's decorative parapet extends to 22.57 m. The interior and ends are open. The canopy has its supports centered at Y=4, avoiding doubled columns at repeat seams; put its ground origin on the platform surface and repeat every 8 m.

The tall shed-column shafts use charcoal iron with the supplied iron texture repeated five times vertically (about one tile per 2 m); the shorter canopy shafts repeat it twice. Ornamental scrollwork is confined to small bases, capitals, and decorative accents. Iron and decorative cast-iron surfaces use generated base-color textures and supplied normal and ORM maps from `textures/`. The glass base-color is a desaturated, blurred, cool-tinted derivative of the generated slate surface, with the supplied slate normal and ORM maps; its glTF material is double-sided and alpha blended at 0.34, so the interior remains visible. Detail is approximate painted relief, not measured material data. All textures are embedded in the GLBs and their source paths/UV rectangles are recorded in `modules/shed/manifest.json`.

Rebuild from the station directory with:

```sh
python src/build_shed.py --config modules/shed/texture_config.json
```

Validation reloaded each GLB with pygltflib and trimesh, checked finite position/normal/UV arrays, wrapped shaft texture coordinates and valid indices, nonzero triangle areas, embedded image decode, PBR texture references, actual node-instanced triangle counts, and agreement between transformed bounds and the authored Z-up bounds. A separate generated geometry preview was inspected for roof curvature, openness, bracing and support placement. Material appearances remain subject to the renderer's transparency sorting and lighting.
