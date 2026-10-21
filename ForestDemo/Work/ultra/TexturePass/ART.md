# Quietwater Grove texture pass

Original first-delivery geometry/layout is retained. Each of the 922 placed props has a scale-baked mesh variant. Actor world position and rotation are preserved from the actual saved level, including the first-pass boundary corrections. Actor scale becomes (1,1,1).

## UV method

The target is 32 source pixels per metre at actual world scale. Each triangle is flattened isometrically using its longest edge and geometric altitude. It gets an independent UV island. The rectangles enclosing these islands are shelf packed with 1.5 pixels of inset on each side: 3 pixels minimum separation between neighbouring island bounds. UVs remain within [0,1], do not mirror, tile, stack or overlap, including between material slots. This method handles nonuniformly scaled rocks without introducing UV stretch. UE uses full precision UV storage.

The tradeoff is many seams and low atlas utilization on small plants. The images are low-contrast surface fields, but no seamless paint continuity across every triangle is claimed. Very small plant triangles can cover less than a source pixel. Four 1254×1254 NPOT image outputs are retained without resampling; UE textures use NoMipmaps and NeverStream. This avoids padding/mip bleed but is a performance/aliasing tradeoff.

`uv_report.json` lists world scale, world area, UV area, density and packing for every placement. `uv_fbx_validation.json` independently re-imports every exported FBX, measures its stored float32 coordinates, and tests all candidate island bounding boxes for intersection. `uv_summary.json` aggregates the actual results. Ground, lake, sea and surf are explicit continuous world-space shader exceptions; their detail has wavelength in world metres, not an atlas texel density.

## Original generated texture mapping

All four files were generated with the built-in image_gen tool, inspected, and copied unchanged into `Generated/`. Prompts, exact tool output paths and actual call timestamps are in `Generated/generation_records.json`. They are original asset texture images, never scene-render evidence.

| Original image | UE texture | Material surfaces |
|---|---|---|
| Bark.png | /Game/Forest/ultra/Textures/T_Bark | Bark, BarkLight |
| Canopy.png | /Game/Forest/ultra/Textures/T_Canopy | LeafSage, LeafMoss, LeafLight, Pine, PineTip, Grass, Fern, Stem |
| Stone.png | /Game/Forest/ultra/Textures/T_Stone | Rock, RockLight, RockMoss |
| Wood.png | /Game/Forest/ultra/Textures/T_Wood | Wood, Endgrain, ReedHead |

The generated texture luminance modulates each retained palette tint using `Tint * (0.94 + 0.28 * luminance(texture))`. The original color art direction remains restrained. UV channel 0 is sampled at scale 1. Petals, iron and sand accents retain their original materials; the associated prop geometry still receives measured unique islands. No imported external assets or other effort resources are used.

## Water

Sea and lake use different translucent surfaces with world-position normal ripples, time-varying vertex displacement and muted reflection. The sea has advancing white crest bands near shore. Existing surf ribbons have a white translucent material with soft width falloff, irregular opacity, no cast shadow, and time-varying position following the water height. Caustics are animated interference patterns projected in world coordinates onto the ground underneath the lake and sea, visible through the water.

This is an artistic approximation. There is no physical wave solver, ray-traced caustic transport or physically solved refraction. Original lake topology has a center fan, so its small displacement is deliberately restrained. The `Time` node drives all animation in the saved materials. Timed water screenshots use the same fixed UE camera and record world shader time and actual UTC capture time.

## Source and reproducibility

`build_uv.py` produces owned scale-baked FBX files from this effort's original source blend. `audit_fbx_uv.py` independently reads the exported artifacts. `build_texture_pass.py` imports textures/meshes and changes only the private level and owned materials. `review_texture_pass.py` reloads the saved map in a fresh process, validates dependencies and UV/material/collision bindings, renders common cameras, then runs actual PIE possession and sweep tests.

FBX round-trip measurement found 32 pre-existing zero-area triangles among 466,996 source triangles. These are excluded from density statistics and handled by UE degenerate removal. Nondegenerate triangle density spans 31.8926–32.0937px/m due to float precision on extremely small triangles; per-mesh area-weighted density remains within 0.00002px/m of target.



Final material polish is applied by refine_materials.py after the initial build. normal_audit.json checks representative broadleaf, pine and rock FBX corner normals: all sampled shared-vertex normal differences were zero. The final soft foam follows the sea displacement approximately two centimetres above its surface, with smooth width falloff and no cast shadow. ReviewAttempt1 preserves rejected pre-polish renders for diagnosis.


After the final close beach inspection, refine_foam.py adds animated cellular breakup to the sea crest bands and hides the legacy thin surf ribbons. Visible white foam is now entirely part of the sea material: it follows the displaced water and creates no separate shadow. The retained hidden ribbon asset/material is historical owned content, not visible scene evidence.


The final PIE test records the actual downward sweep HitResult, including blocking_hit, initial_overlap, hit fraction/distance, actual pawn displacement and exact owned ground actor/component/static_mesh identity. Passing requires a blocking, non-overlapping hit after positive motion against SM_Ground, in addition to the existing possession/horizontal movement checks.

