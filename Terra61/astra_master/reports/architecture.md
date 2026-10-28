# Architecture module report

The facade is a seven-instance assembly: a clock hall at X=0, domed towers at X=±12 m and repeated wing bays at X=±18 and ±22 m. The complete facade spans 48 × 10 × 24.36 m in the authored coordinate system. Each module has its own self-contained GLB and the assembly references three unique meshes rather than duplicating them.

| Asset | Authored bounds, metres (X, Y, Z) | Unique triangles |
| --- | --- | ---: |
| `central_hall.glb` | (-8, 0, 0) to (8, 10, 20.18) | 5,105 |
| `facade_bay.glb` | (-2, 2, 0) to (2, 10, 11.791) | 951 |
| `dome_tower.glb` | (-4, 0, 0) to (4, 10, 24.36) | 2,642 |
| All three unique meshes | — | 8,698 |
| Seven placed instances | (-24, 0, 0) to (24, 10, 24.36) | 14,193 drawn |

Local origins are centered across X, on the floor at Z=0; station depth runs along positive Y, with the main wall at approximately Y=2.45, the canopy front at Y=0, and the rear at Y=10. The wing bays have no canopy and start at Y=2. Their recessed openings use a pane inset of approximately 0.42 m from the front wall. In each export, the sole root node rotates authoring coordinates by −90° around X, so GLB consumers receive a Y-up asset; the facade faces +Z in glTF space.

The broad arches, window reveals, raised clock, cornices, canopy, columns, dome ribs and roof silhouette are geometry. Brick, stone, slate, iron, ornament, warm glazing and the name sign use the generated image materials. The door art uses the dedicated high-resolution `textures/door_basecolor.png` with its fanlight registered to each arch and a scalar roughness; the other materials include embedded base-colour, normal and metallic/roughness maps. The image-derived maps are approximate rather than scanned. Hero window, clock and sign images are individually registered to their panels; structural surfaces use tile materials rather than repeating the complete detail sheet. Every visible triangle carries UVs and normals. The separate PNGs in the module directory document the map inputs; they are not required when importing the self-contained GLBs.

Files: `station/modules/architecture/{central_hall,facade_bay,dome_tower,architecture_assembled}.glb`, `station/modules/architecture/manifest.json`, generator `station/src/build_architecture.py`, and front-elevation diagnostic `station/modules/architecture/architecture_elevation.png`.

Validation: `python station/modules/architecture/test_architecture.py` reloaded all four GLBs, decoded all embedded images, checked UVs/normals/indices and non-degenerate finite triangles, verified declared bounds and the Y-up root conversion, verified the new high-resolution door map, and verified seven nodes reuse exactly three assembly meshes. PNG intermediates are written atomically to prevent parallel preview readers from observing empty files. The diagnostic image is a software front-elevation render of the actual generated triangles and texture maps; the integrated scene still needs its own camera and lighting review.
