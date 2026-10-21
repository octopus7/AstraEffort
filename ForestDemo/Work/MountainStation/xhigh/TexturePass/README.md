# Alder Pass surface pass

Only MountainStation/xhigh. No other worker artwork or assets are referenced. FirstDelivery and the original completion timestamps remain separate and unchanged.

## Artwork and material mapping

Four distinct built-in imagegen requests were issued concurrently. Exact prompts, invocation intervals, output paths, 1254x1254 source dimensions and SHA-256 hashes are in `texture_prompts.json` and `Evidence/imagegen_calls.json`. Requests asked for 1024 square; the actual output is 1254 square. The original PNG bytes are preserved in `Textures/`. No image editing, resizing or synthetic scene evidence is used.

- Wood: Timber, Wood, Cargo.
- Mineral: Rock, RockLight, Ballast, Trail, Paving, EdgeStone, Plaster, Earth.
- PaintedMetal: Roof, RoofSeam, Metal, Rail, Red (subtle texture on luggage).
- Foliage: Pine, PineLight, Bush, Grass, GrassLight.
- Solid exceptions: Glass, Cream (lettering/clock/safety line/light surfaces), Amber, Dark tunnel end, Flowers and Backdrop.

Each textured material samples UV0 without additional tiling, uses the red channel as a linear detail mask, multiplies the existing palette by `1 - amplitude/2 + texture.R * amplitude`, and varies roughness by `baseline - .08 + texture.R * .16`. This retains the original palette. Native non-power-of-two images are kept unchanged, non-streamed, with no mipmaps. This is a known memory/minification limitation, not an optimization claim.

## UV specification and honest scope

Native target density is **256 pixels/metre**, texture width/height 1254, physical repeat **4.8984375m**, UV scale **256/1254 UV units/metre**. For each triangle, density is `sqrt(UV area * width * height / placed world area in m²)`. UE measurements convert centimetres to metres and include the component scale. Existing placement `(1,-1,1)` is a reflection with unit absolute scale. No new object placement scaling is introduced.

`uv_author.py` applies source transforms without moving world geometry, triangulates, collects edge-connected coplanar same-material triangles into islands, and uses orthonormal projection. Curved shapes have faceted islands; grain continuity across curved facets is not guaranteed. Each island rectangle is placed on a shelf with at least 8 native pixels between rectangles, with no normalization shrink. UV0 extends outside 0..1. Disjoint unbounded UV islands and intentionally overlapping modulo-one repeating texture coordinates are different checks. These are reusable surface textures, not unique baked atlases or lightmaps.

All 552,142 source triangles are measured, including repeated trees, all back faces, hidden surfaces and the diorama base. Full source triangle data are stored in compressed CSV, and all island bounds in JSON. Source density deviations on minute bevel/text faces are retained. The `source_exception_audit.json` separates triangles below 16 target pixels in area from larger faces, and lists the six 1..16-pixel fir faces outside ±1%. There are no >16-pixel source faces outside ±1%.

The fresh UE process checks complete saved SourceModel and RenderData triangle/material inventories, aggregate geometric and UV area, island counts and full-precision UV settings. Individual densities are measured on deterministic samples of up to 256 triangles per material per LOD, with raw placed positions, UV triplets and material IDs retained. This is **not** an exhaustive per-triangle UE density, overlap or padding check. Complete source overlap/padding checks and the saved-UE sample scope are reported separately. Large/small area, curved facets, repeated geometry and solid-material exceptions remain visible in the evidence.

## Reproduction

1. Run `uv_author.py` using a private background Blender process. It reads this worker's original source and writes only TexturePass source/evidence.
2. Run `run_build.ps1` via the supervisor queue in a CIM-capable environment. Only the private project is edited. GeometryScripting is enabled in that private project for validation; shared project files/binaries are not changed.
3. Run `prepare_validation.py`, then `run_capture.ps1` (or the recorded later attempt) through the same queue. Fresh-process saved-mesh checks precede static validation, exact-camera captures and actual PIE checks.
4. Inspect the four real UE PNGs and the separate Hello viewport. Publish only after the private editor exits and package hashes agree.

UE camera positions, projection, FOV, resolution and quality settings come from this worker's first delivery. Imagegen images are material source artwork only. Runtime sweeps record blocking, initial overlap, positive travel distance and exact actor/component/mesh; the DefaultPawn remains a flying pawn, not a new walking character controller.
