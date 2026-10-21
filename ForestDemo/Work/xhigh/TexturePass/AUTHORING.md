# Quiet Cove xhigh texture pass

This pass preserves the 100 m forest, small inland lake, separate southern beach, prop placement, lighting and four comparison cameras. All assets and generation outputs are authored independently in xhigh's ownership scope. FirstDelivery is untouched. No Git commands that change the index or history are part of this workflow.

## Production

1. Five separate built-in `image_gen.imagegen` calls generate bark, foliage, stone, wood and a grayscale caustic mask. The exact prompts, unmodified images, generation windows and original tool paths are in `Imagegen/manifest.json`.
2. `unwrap_art.py` operates on xhigh's original Blender scene. It projects distinct UV0 islands, equalizes island area scale and packs them. `refine_uv_water.py` repairs folded cap islands and zero-area foliage tips, increases water tessellation, and authors three soft white foam ribbons. `audit_uv.py` remeasures the final saved source.
3. Triangle intersection tests use a positive-area threshold of 1e-8 UV square units (0.01572516 native texel squared), excluding float-rounding slivers along shared edges. Actual UV occupancy, surface area, island count, minimum segment-to-segment island gap, density distributions and all 889 placed world scales are in `SourceArt/uv_report.json`.
4. Per-mesh base density is `1254 * sqrt(UV_area / surface_area_m2)`. Target effective density is 128 px/m. Saved per-actor Custom Primitive Data[0] equals `(128 / base_density) * uniform_world_scale`; the generated-image materials sample `UV0 * CPD[0]`. This compensates the actual placement scale while retaining non-overlapping unique authoring UVs. These are shared independently generated material surfaces, not bespoke per-instance painted atlases. Texture wrapping is intentional after sampling correction. Curved surfaces retain the measured projection stretch; the per-mesh area RMS is equalized, while triangle percentiles disclose local variation.
5. `apply_textures.py` imports FBX and all five original PNGs into the private UE project. Eighteen prop surface materials consume the generated bark/foliage/stone/wood images. The original palette tints their luminance to keep the restrained game style. The terrain receives faint stone grain plus the moving caustic image below the sea/lake water lines.
6. Sea and lake use translucent surface lighting, analytic animated world-position displacement and normals. White translucent foam ribbons move with time. The caustics are an artistic animated image projection on actual underwater terrain. No optical or ray-traced refraction solver is used. This limitation is deliberate and visible in the material code.
7. `validate_capture.py` runs in a fresh UE process: original world/dependency/collision checks, saved UV and texture dependency checks, all actor density values, representative UE FBX round-trip exports, unchanged-camera 1920x1080 captures, two fixed-camera water-time captures, and actual PIE possession/movement/collision/shutdown plus the baseline Hello automation test.
8. `check_roundtrip.py` independently imports four fresh UE FBX exports in a separate background Blender process and compares surface/UV areas and overlaps. Publication is gated on validation, direct screenshot review and the private UE process being closed.

The first round-trip audit exposed three UV-only degenerate triangles at SM_Pine_0's tips. Their geometry has positive area; narrow UV coordinates collapsed in UE's half-precision built vertex buffer. `repair_precision.py` enables full precision UVs for both pine variants. The final round-trip gate now explicitly requires zero degenerate triangles. See `uv_precision_diagnosis.json` for measured coordinates, areas, the repair timestamp and the final outcome. Round-trip coverage is four representative meshes, not all 28. Source UV checks cover all 28.

The strengthened PIE test records the actual pawn HitResult via `to_tuple()` and `export_text()`: a clear upward move, sphere radius and ground clearance, non-penetrating start, positive travel before contact, blocking flag and the exact terrain actor/component/mesh. It does not infer blocking from the final pawn position alone.

## Reproduction paths

- Private project: `ForestDemo/Saved/Workers/xhigh/Project/ForestDemo/ForestDemo.uproject`.
- Every new UE process is launched through the read-only supervisor utility `ForestDemo/Work/Tools/Run-UnrealIsolated.ps1`, with own logs and `texture_*_timing.json` in xhigh's scratch directory.
- Final source: `SourceArt/QuietCove_TexturePass.blend` and 28 FBX files. Example UV layouts are supplied as SVG.
- Final runtime packages remain `/Game/Forest/xhigh/**` and `/Game/Maps/xhigh`.

## Specific limits

- Original generated images are 1254 square; NPOT images use no mipmaps. Raw images are preserved without resizing or repainting.
- Density correction covers all current uniform actor scales. Editing a scale later requires updating its saved CPD scalar using the formula above.
- Terrain detail uses world XY projection at 127.908 px/m horizontally; surface slope reduces density. Water, caustics and foam have separate moving world-space coordinates.
- UV seams may interrupt local grain direction; the restrained texture blend limits visible seams. This is a reusable stylized material treatment, not individually hand-painted UV atlases.
- The first fresh validation emitted a nonfatal UE `EditorSetViewportRealtime` handled ensure because an expected realtime override was absent. Its original log is preserved. Subsequent captures establish the override before removing it. CaptureEveryFrame plus explicit capture requests also produce efficiency warnings; the captures are evidence, not a runtime capture system.

## External API references

- [UE 5.7 Custom Primitive Data setter](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/PrimitiveComponent?application_version=5.7)
- [UE 5.7 scalar parameter custom data index](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MaterialExpressionScalarParameter?application_version=5.7)
- [UE 5.7 DepthFade](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MaterialExpressionDepthFade?application_version=5.7)
- [UE 5.7 StaticMeshEditorSubsystem](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/StaticMeshEditorSubsystem?application_version=5.7)

No external artwork, other worker output or shared Blender scene was used.
