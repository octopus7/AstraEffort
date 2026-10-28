# Victorian station props and façade canopy

These five GLB files are independent, metre-scale glTF 2.0 modules. Each contains its own UV-mapped PNG base-color materials and explicit vertex normals; none requires external images at runtime. The coordinate system is **Y up**, and every local pivot is `(0, 0, 0)` with the lowest geometry at ground level Y=0. Bounds are in metres; counts are triangles, not polygon faces before triangulation.

| GLB | Bounds X | Bounds Y | Bounds Z | Triangles |
| --- | --- | --- | --- | ---: |
| `station_lamp.glb` | −0.33 to 0.33 | 0 to 3.56 | −0.33 to 0.33 | 690 |
| `station_bench.glb` | −0.98 to 0.98 | 0 to 1.0965 | −0.3716 to 0.35 | 1,036 |
| `luggage_trolley.glb` | −0.98 to 0.98 | 0 to 1.0533 | −0.402 to 0.4 | 1,616 |
| `wall_clock.glb` | −0.69 to 0.79 | 0 to 1.68 | −0.15 to 0.135 | 1,168 |
| `facade_canopy.glb` | −10 to 10 | 0 to 4.09 | −2.5 to 0 | 5,832 |

Place the canopy at the same origin as the façade. Its rear edge meets the façade at Z=0, and it projects forward into negative Z. Its upper surface slopes from approximately Y=4.00 at the front to Y=4.09 at the wall; ten posts stand at ground level. For the wall clock, Y=0 is the bottom of its decorative finial, not its final installed height; translate it vertically to mount it. Its main readable dial faces −Z, and the mounting bracket occupies the negative-X end. The trolley's trunks are part of the trolley GLB and are static.

## Modeled features and textures

The lamp has a modeled stepped pedestal, fluted post, four lantern panes, roof and finial. The panes are opaque, warm emissive surfaces; the flame is drawn into their texture, and the model emits no engine light. The bench has individual wood slats, feet, arms, side supports and wheel-like ornaments. The trolley has four open, spoked wheels, a plank deck, posts and three strapped trunks with modeled handles and hardware. The wall clock has a thick circular case, rim, bracket, scrolls and finials; Roman numerals and hands are part of the dial texture. The canopy has a physical roof, posts, crossbeams, curved braces and hanging light shapes; the small fascia scrollwork is painted into a repeatable texture. The hanging lights are also emissive surfaces, not actual light sources. These are static meshes without animation or custom collision.

`textures/ai_aged_cast_iron_768.png` is a reduced-resolution copy of the supplied AI-generated `materials/ai_aged_cast_iron.png`; the iron surfaces use it through UVs. The wood, leather, brass, roof, glow and frieze images are procedural base-color textures from `generate_props.py`. The clock face is copied from the adjacent façade's procedurally generated face, with a procedural fallback. References were the supplied concept drawings in `../../references/01_facade_reference.png` and `06`–`09` in that same folder. No other external texture source was used.

## Rebuild and inspection

Run `python generate_props.py` to regenerate all five GLBs and `model_stats.json`; Python, NumPy, Pillow and trimesh are required. The local iron texture copy is used if the shared source is unavailable. Run `python render_glb_previews.py` to reimport each GLB and render its geometry, UVs and embedded textures on the CPU. The `preview_*.png` files are renders of the exported meshes, not concept art; `preview_facade_and_canopy.png` shows the two modules at their shared origin. `verification.json` records bounds, counts, and image counts after GLB reimport. All files were checked for embedded images and buffers, UVs and normals, finite data, zero degenerate triangles, and the specified canopy interface bounds.
