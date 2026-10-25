# Independent final FBX review

Blender 4.5.12 LTS; 20 FBX files; source hashes and timestamps unchanged: True.
UTC: 2026-10-22T13:28:47.029422+00:00 to 2026-10-22T13:29:01.010943+00:00; elapsed 13.982 seconds.

UV0 checked by exact triangle clipping after spatial hashing. Positive area threshold 1e-10 UV². UV1 density measured at 1024² using imported world triangle areas. This is source-mesh QA, not Unreal import/runtime validation.

| Mesh | Triangles | UV integrity | UV1 mean px/m (area weighted) | UV1 min–max | Area outside ±15% | Bounds m |
|---|---:|---|---:|---|---:|---|
| SM_Barn | 66448 | PASS | 127.803 | 103.132–133.293 | 0.018520% | 10.861 × 8.968 × 5.816 |
| SM_Barrel | 4900 | PASS | 127.847 | 108.757–134.601 | 0.001408% | 0.820 × 0.820 × 1.006 |
| SM_Cart | 21528 | PASS | 127.892 | 103.076–131.977 | 0.772243% | 2.126 × 4.420 × 1.640 |
| SM_CropClump | 3060 | PASS | 127.347 | 97.066–141.094 | 12.759035% | 0.742 × 0.730 × 0.757 |
| SM_EarthEdge | 800 | PASS | 128.000 | 127.999–128.001 | 0.000000% | 100.000 × 100.000 × 2.085 |
| SM_FenceSegment | 1968 | PASS | 127.972 | 107.832–130.209 | 0.008687% | 3.051 × 0.284 × 1.297 |
| SM_FieldRock | 120 | PASS | 127.145 | 105.816–147.937 | 25.970811% | 1.352 × 0.873 × 0.560 |
| SM_Gate | 2320 | PASS | 127.959 | 100.032–130.670 | 0.056724% | 3.108 × 0.255 × 1.200 |
| SM_GrassTuft | 69 | PASS | 127.812 | 105.383–133.426 | 2.701799% | 1.171 × 1.290 × 0.469 |
| SM_Ground | 20000 | PASS | 128.000 | 127.680–128.041 | 0.000000% | 100.000 × 100.000 × 1.021 |
| SM_HayBale | 3132 | PASS | 127.972 | 115.082–130.388 | 0.000000% | 1.219 × 0.763 × 0.785 |
| SM_MillRotor | 28612 | PASS | 127.956 | 103.025–129.914 | 0.121408% | 11.355 × 0.630 × 11.355 |
| SM_MillSteps | 1296 | PASS | 127.964 | 113.189–130.232 | 0.000000% | 2.220 × 1.200 × 0.260 |
| SM_MillTower | 112648 | REVIEW | 127.728 | 102.243–34117.482 | 0.288379% | 7.239 × 7.639 × 12.630 |
| SM_OrchardTree1 | 880 | PASS | 127.781 | 109.982–139.996 | 0.000000% | 6.518 × 5.868 × 6.164 |
| SM_OrchardTree2 | 880 | PASS | 127.692 | 100.494–141.018 | 3.069585% | 6.920 × 5.373 × 6.663 |
| SM_OrchardTree3 | 880 | PASS | 127.774 | 108.442–140.202 | 0.201573% | 6.326 × 6.002 × 7.162 |
| SM_Shed | 20436 | PASS | 127.973 | 100.952–129.534 | 0.097493% | 4.560 × 3.750 × 3.200 |
| SM_ToolCluster | 7252 | PASS | 127.933 | 102.998–130.621 | 0.011318% | 1.856 × 0.879 × 2.012 |
| SM_WheatPatch | 2976 | PASS | 127.627 | 106.461–138.624 | 2.706965% | 1.162 × 0.911 × 1.198 |

Per-mesh JSON includes every object pivot/transform, bounds, channel names, overlap examples, material-level density statistics and exact outlier triangle/face IDs and centroids. UV0 is constrained to its own 0–1 tile; UV1 is intentionally tiled.

## Findings requiring an explicit exception or source repair

Only `SM_MillTower` fails the strict UV checks. `WoodLight` triangles/polygons 18135, 18148, 18161 and 18174 have zero UV0 and UV1 area; their world area is only 6.31166e-11 m² each. `Plaster` triangle/polygon 1341 also has zero UV1 area (world area 2.75356e-8 m²). These are microscopic source triangles, but the UVs are mathematically degenerate.

Two Plaster UV0 pairs have positive intersection: 57215/57213 is 3.4529528e-9 UV² (0.003621 pixels² at 1024); 57260/57258 is 3.6030188e-9 UV² (0.003778 pixels²). A second Blender import and clipping recheck with classification epsilon exactly zero returned the same areas. The overlaps are real, extremely small, and do not satisfy a literal zero-overlap claim. Exact world vertices, UV vertices, edge lengths and epsilon rechecks are in `tower_findings_detail.json`.

The tower's largest density outlier is Plaster triangle 1269: 34,117.482 px/m, world area 9.95223e-9 m², centroid (0.026987, 2.355805, 8.372342) m. Other extreme tower values likewise occur on tiny triangles. Its whole-surface area-weighted mean is 127.728 px/m and 0.288379% of area lies outside ±15% of target.

All meshes' area-weighted means are 127.145–128.000 px/m. The ±15% screening window is an independent diagnostic, not a supplied acceptance tolerance. Variation on some organic surfaces is broader than an isolated bevel: FieldRock 25.970811% of area outside the window (105.816–147.937 px/m); CropClump 12.759035% (97.066–141.094); OrchardTree2 3.069585% (100.494–141.018); WheatPatch 2.706965%; GrassTuft 2.701799%. The report should preserve these measured exceptions if the parent accepts the mean-density criterion.

All object pivots are at the intended file origin within 2.4e-7 m of floating-point roundoff. The rotor spans ±5.678 m vertically about its hub origin. Ground and EarthEdge are each exactly 100×100 m horizontally. Some props extend 0.01–0.06 m below their origin or begin 0.01–0.02 m above it; final placement/contact remains a UE scene check.

Geometry and UVs were inspected without saving a Blender file or changing source FBX files. No other theme, effort, Unreal session, Git operation, or shared Blender state was accessed.
