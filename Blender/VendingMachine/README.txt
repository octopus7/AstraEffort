VENDING MACHINE - editable Blender + self-contained GLB

Main deliverables
  VendingMachine.blend
  VendingMachine.glb
  renders/hero.png, front.png, rear.png, side.png
  renders/material_variations.png
  renders/glb_reimport_hero.png
  renders/capture_manifest.json
  validation/UV_Layout_4096.png and validation/*.json
  textures/generated/: two untouched independent image-generation outputs
  textures/packed/VendingMachine_BaseColor_4096.png
  source/: complete build, UV/bake/export, render/QA scripts and generation prompts

BODY COLOR VARIATIONS / 몸체 밝은 부분의 색상 배리에이션
The light shell is assigned only to BODY_VARIANT_WHITE. Its numeric PBR base
color/default tint is WHITE (1, 1, 1, 1). The delivered GLB baseColorFactor is
also WHITE. The ivory color is supplied by the independently generated enamel
image, baked into the unique albedo atlas. There is no ivory numeric base factor.

In Blender: select a light body part, open BODY_VARIANT_WHITE in the Shader
Editor, and edit Color2 on the clearly named BODY_TINT_WHITE_DEFAULT Multiply
node. White preserves the supplied ivory finish. A colored value multiplies
only the light-body texture. In a GLB viewer/engine, change baseColorFactor on
BODY_VARIANT_WHITE only. The ivory texture makes tinted variants slightly warm.
Do not recolor the shared image globally: all material groups share the atlas.

This body material is used by these five pieces:
  Body_MainShell_LightVariant
  Front_Lower_Access_Plate
  Rear_ServicePanel_LightVariant
  Side_-1_Ivory_Inset
  Side_1_Ivory_Inset
Armor, glass, emission lamps, control surfaces, shelves, bottle bodies/caps,
labels and light graphic lettering use 25 other separately named materials.
The actual Cycles comparison shows ivory, ocean and terracotta BODY-only tints.
It is a real render of three mesh copies, not a generated image.

Model and scale
Blender 4.5.12 LTS; metric units; Z up; front faces -Y. GLB exports standard Y up.
Measured overall size including armor and beacon:
  width 1.271 m x depth 0.900 m x height 1.787 m.
The supplied reference gives approximate 1.2 m x 1.8 m proportions; this model
is 1.271 m wide across the protruding side lights/armor. Depth is inferred.
Feet are aligned to Z=0; no ground plane, camera, or studio light is exported.
There are 255 editable mesh objects, 31,998 Blender vertices,
and 62,932 exported triangles in 255 GLB primitives.

Visible modeled features
Rounded ivory cabinet; real recessed display bay; 3 shelves with 4 distinct
bottle bodies, caps and label/icon meshes per shelf; separate thin transparent
front pane; amber interior strips; narrow right-side touchscreen/payment panel
and luminous square button; genuinely recessed lower delivery pocket; side and
lower amber lamps; slate side/lower armor; four feet; rear panel and vent slats;
top service cover and guarded amber beacon. Exterior only, without vending
mechanics or rigging. No external model was imported.

Textures and PBR
Independent built-in image_gen outputs: ivory enamel and slate powdercoat,
both actually 1254 x 1254 pixels. Full prompts, original tool output paths and
mapping are in source/imagegen_provenance.json. Original PNGs are preserved.
The final 4096 x 4096 atlas contains baked base color only, including generated
surface colors and simple independently authored palette colors for graphics,
products and lamps. Base color was baked through Emission at strength 1 so
metallic shading, transparency and studio lighting cannot darken the albedo.
A temporary joined copy with per-vertex preserved source coordinates was used
for the bake; the delivered original parts remain separate. Material roughness,
metallic, alpha and emission remain separate portable PBR controls. No normal
map is required or supplied. Main blend images are packed; GLB images embedded.

Texture byte identity verified on saved/reopened files:
  external PNG = packed Blender PNG = GLB embedded PNG
  SHA-256: ec54891ff52cd443e241cbda3f321a8fcb790767ab70ce3540eaee93279bab8d

UV validation and measured limits
One globally unique UV_Unique layout, normalized by physical island area.
Analytical quad-strip UVs are used for the twelve tapered bottle bodies.
Other surfaces use stable smart projection, with explicit text cap triangulation
to remove Blender font-conversion degeneracies before packing.
Global packing uses UV select sync, CONVEX shapes, no merged overlaps,
rotation/scaling, and a requested margin fraction of 0.002.

4096 validation: 0 strict interior overlap pixels,
0 out-of-bounds triangles, 0 zero-area UV triangles,
0 zero-area geometric triangles. All 255 separate mesh pieces have
0 nonmanifold/boundary edges. Assembly pieces intentionally intersect at joins.
1702 unique islands; 53.70% raster occupancy.

Nominal density target was 800 px/m. The achieved global effective density is
522.53 px/m, with area-weighted mean 522.22 px/m.
Area-weighted per-triangle 5th / 50th / 95th percentiles:
478.43 / 524.79 / 537.87 px/m. Object-scale density is consistent;
local bevels and tapered necks produce the measured per-face variation.
The 800 target was not achieved while fitting all exterior and hidden faces of
32.98 square meters into one padded 4K map. This is documented,
not reported as 800. Per-object values are in validation/mesh_validation.json.

Requested padding is 8.192 pixels of margin at 4096. The raster island dilation
first contacts another island at step 9, bounding occupied-pixel separation
to roughly 16-18 pixels across two margins. Bake dilation is 8 pixels. This is
a pixel-grid measurement, not an exact continuous edge-distance certificate.
22,497 thin/small triangles cover no pixel center at 4096; the raster
test cannot rule out every subpixel intersection. UV bounds/areas are checked
numerically in addition to the raster. No UV mirroring or intentional stacking.

Verification
All 255 GLB primitives have TEXCOORD_0. All images are embedded; no external
buffer/image URI dependencies. The exported body factor remains [1,1,1,1].
A direct parse of the final GLB vertex/UV accessors and hierarchical transforms
also confirms zero degenerate triangles, unit-square UV bounds, matching native
dimensions and feet at Y=0 in the GLB's Y-up coordinate system.
The delivered blend was freshly reopened, and the GLB was freshly re-imported
after removal of the native model. Actual same-camera Cycles renders were
visually inspected. Loaded-image RGB mean absolute render difference:
0.00154959.
See validation/glb_validation.json, blend_validation.json, texture_validation.json,
reimport_validation.json and visual_review.json for the actual evidence.

Render settings
Cycles CPU, 4 threads, 32 samples, denoised; AgX / Medium High Contrast.
Hero and reimport: 1100 x 1210. Orthographic front/rear/side: 1050 x 1200.
Three-body variation comparison: 2100 x 1000. Camera locations, scale, UTC
timestamps and measured durations are in renders/capture_manifest.json.
The low-opacity glass is an artistic, cross-viewer visibility choice, not
thick physical refraction. Product bottles are opaque stylized plastic.

Rebuild
Use source/Rebuild.ps1 with Blender 4.5. It launches separate background
processes with --factory-startup --threads 4, using the preserved PNG originals.
Individual steps: build_vending.py -> finalize_vending.py -> render_and_validate.py.
write_report.py requires visual_review.json after the new renders are inspected.
source/VendingMachine_prebake.blend preserves the editable pre-bake stage.
No live Blender MCP scene or unrelated creative asset was used. No Git changes
were staged or committed. No UE editor, network asset download or shared source
was used. This asset has no LODs, collision mesh, rig or vending simulation.

Reference
Only the user-supplied D:/github/AstraEffort/REF/vending.png reference sheet.
No other task's assets, textures, scripts, reports or scratch files were read.

Recorded work timing
Start UTC: 2026-10-23T09:39:26+00:00
Start KST: 2026-10-23T18:39:26+09:00
Finish UTC: 2026-10-23T10:34:15.418884+00:00
Finish KST: 2026-10-23T19:34:15.418884+09:00
Elapsed wall seconds: 3289.419
Combined parallel image-generation wall seconds: 42.419
Last successful UV/bake/export wall seconds: 26.554
Last successful bake/material/export seconds: 4.992
Final six actual render seconds: 244.145
Wall time includes previews, font diagnosis, an abandoned slow per-object bake,
the ground alignment and header placement corrections, final renders, checks
and documentation.
Per-stage values are actual recorded runs, not an invented sum of every attempt.
