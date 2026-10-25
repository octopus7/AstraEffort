# Corn source-art validation

Three original meshes were generated and exported, then independently reimported in the same script from the actual FBX files. Each mesh has 2,168 triangles, 1,520 source vertices, two UV channels, and linear `Col` vertex colours. The source origin is the stalk root `(0,0,0)`, metres, Z up. FBX axis settings are `-Y` forward and `Z` up.

| Asset | Width X × depth Y × height Z (m) | Actual UV1 density at 1024 px |
|---|---|---:|
| SM_CornA | 1.7942 × 0.9268 × 2.3509 | 127.99974 px/m |
| SM_CornB | 1.4936 × 1.5299 × 2.1809 | 128.00008 px/m |
| SM_CornC | 1.2750 × 1.5658 × 2.4809 | 128.00009 px/m |

All FBX roundtrip checks passed: zero collapsed geometry or UV triangles, zero UV0 coordinates outside 0–1, preserved RGBA channels, and root R exactly zero. Maximum R error from the measured `z / actual height` is below 3e-8. All four material slots survived: `CornLeaf`, `CornStalk`, `CornKernel`, `CornTassel`.

UV0 uses one physically shaped triangle per separate grid cell. Every cell has a 2 px internal inset at 1024 px; separate occupied cells therefore have at least 4 px between their triangle contents. The disjoint-cell construction guarantees no UV0 overlap. UV1 repeats intentionally, with a common physical scale; all triangles measure 127.946–128.069 px/m after float32 FBX roundtrip. This approach trades efficient atlas occupancy for strong density and overlap guarantees. UV0 is approximately 52 px/m; the actual material should use UV1.

`Col` is FLOAT_COLOR/CORNER in Blender and exported with `colors_type='LINEAR'`. R is the measured normalized plant height, G is flutter strength (0 stalk, 0.7–1 leaf, 0.3–0.35 ear, 1 tassel), B=0, A=1. UE must import colours with REPLACE and make CornLeaf two-sided. Multiply any WPO by R or R² to keep roots fixed. Use subdued flutter amplitudes because G differs between attached stalk and leaf surfaces; large local flutter can visibly separate a leaf's attachment from the stalk. Global bending should be shared across all material slots.

The actual source-art preview `preview.png` was rendered with Blender Cycles and directly inspected: all three plants have upright rooted stems, curved broad leaves, two visible ears, and airy golden tassels. This is a source-art inspection, **not UE scene evidence**. Scene lighting and materials remain the root worker's integration responsibility. No external imagery or image generation was used.

The first Blender invocation loaded unrelated user add-ons that emitted handler warnings, while still producing passing geometry. The final build and preview were run with `--factory-startup`, avoiding those add-ons. A preview-only missing-world error was corrected by creating an explicit preview world. Final source geometry and FBX validations have no known exceptions.
