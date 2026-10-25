"""Write the completion record only after actual render/visual verification exists."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text(encoding='utf8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
uv=read('validation/uv_validation.json');mesh=read('validation/mesh_validation.json')
native=read('validation/blend_validation.json');glb=read('validation/glb_validation.json')
bake=read('validation/bake_export.json');renders=read('validation/render_summary.json')
capture=read('renders/capture_manifest.json');visual=read('validation/visual_review.json')
reimport=read('validation/reimport_validation.json');prov=read('source/imagegen_provenance.json')
ground=read('validation/ground_alignment.json')
header_seating=read('validation/header_seating.json')
glb_geometry=read('validation/glb_geometry_validation.json')
assert uv['passed'] and glb['passed'] and visual['passed'] and glb_geometry['passed']
assert len(capture)==6 and all((ROOT/x['file']).is_file() for x in capture)
assert all(x['timestamp_utc']>ground['timestamp_utc'] for x in capture)
assert all(x['timestamp_utc']>header_seating['timestamp_utc'] for x in capture)
assert glb['sha256']==glb_geometry['glb_sha256']==sha(ROOT/'VendingMachine.glb')
assert abs(native['bounds_min_m'][2])<1e-7
assert sum(x['nonmanifold_edges'] for x in mesh)==0
started=datetime.strptime(prov['started_at_utc'],'%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=timezone.utc)
finished=datetime.now(timezone.utc);kst=timezone(timedelta(hours=9));elapsed=(finished-started).total_seconds()
dims=native['dimensions_xyz_m'];pcts=uv['area_weighted_density_p05_p50_p95']
README=f'''VENDING MACHINE - editable Blender + self-contained GLB

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
  width {dims[0]:.3f} m x depth {dims[1]:.3f} m x height {dims[2]:.3f} m.
The supplied reference gives approximate 1.2 m x 1.8 m proportions; this model
is 1.271 m wide across the protruding side lights/armor. Depth is inferred.
Feet are aligned to Z=0; no ground plane, camera, or studio light is exported.
There are {native['object_count']} editable mesh objects, {native['vertices']:,} Blender vertices,
and {glb['triangles']:,} exported triangles in {glb['primitive_count']} GLB primitives.

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
both actually {1254} x {1254} pixels. Full prompts, original tool output paths and
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
  SHA-256: {bake['atlas_sha256']}

UV validation and measured limits
One globally unique UV_Unique layout, normalized by physical island area.
Analytical quad-strip UVs are used for the twelve tapered bottle bodies.
Other surfaces use stable smart projection, with explicit text cap triangulation
to remove Blender font-conversion degeneracies before packing.
Global packing uses UV select sync, CONVEX shapes, no merged overlaps,
rotation/scaling, and a requested margin fraction of 0.002.

4096 validation: {uv['strict_triangle_interior_overlap_pixels']} strict interior overlap pixels,
{len(uv['out_of_bounds_triangle_ids'])} out-of-bounds triangles, {uv['zero_area_uv_triangles']} zero-area UV triangles,
{uv['zero_area_3d_triangles']} zero-area geometric triangles. All {len(mesh)} separate mesh pieces have
0 nonmanifold/boundary edges. Assembly pieces intentionally intersect at joins.
{uv['island_count']} unique islands; {uv['occupancy_fraction']*100:.2f}% raster occupancy.

Nominal density target was 800 px/m. The achieved global effective density is
{uv['effective_global_density_px_per_m']:.2f} px/m, with area-weighted mean {uv['area_weighted_mean_density_px_per_m']:.2f} px/m.
Area-weighted per-triangle 5th / 50th / 95th percentiles:
{pcts[0]:.2f} / {pcts[1]:.2f} / {pcts[2]:.2f} px/m. Object-scale density is consistent;
local bevels and tapered necks produce the measured per-face variation.
The 800 target was not achieved while fitting all exterior and hidden faces of
{uv['total_surface_area_m2']:.2f} square meters into one padded 4K map. This is documented,
not reported as 800. Per-object values are in validation/mesh_validation.json.

Requested padding is 8.192 pixels of margin at 4096. The raster island dilation
first contacts another island at step {uv['island_dilation_first_collision_step']}, bounding occupied-pixel separation
to roughly 16-18 pixels across two margins. Bake dilation is 8 pixels. This is
a pixel-grid measurement, not an exact continuous edge-distance certificate.
{uv['triangles_with_no_pixel_center_coverage']:,} thin/small triangles cover no pixel center at 4096; the raster
test cannot rule out every subpixel intersection. UV bounds/areas are checked
numerically in addition to the raster. No UV mirroring or intentional stacking.

Verification
All {glb['primitive_count']} GLB primitives have TEXCOORD_0. All images are embedded; no external
buffer/image URI dependencies. The exported body factor remains [1,1,1,1].
A direct parse of the final GLB vertex/UV accessors and hierarchical transforms
also confirms zero degenerate triangles, unit-square UV bounds, matching native
dimensions and feet at Y=0 in the GLB's Y-up coordinate system.
The delivered blend was freshly reopened, and the GLB was freshly re-imported
after removal of the native model. Actual same-camera Cycles renders were
visually inspected. Loaded-image RGB mean absolute render difference:
{reimport['rgb_mean_absolute_difference_in_loaded_pixels']:.8f}.
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
Start UTC: {started.isoformat()}
Start KST: {started.astimezone(kst).isoformat()}
Finish UTC: {finished.isoformat()}
Finish KST: {finished.astimezone(kst).isoformat()}
Elapsed wall seconds: {elapsed:.3f}
Combined parallel image-generation wall seconds: {prov['imagegen_elapsed_seconds']:.3f}
Last successful UV/bake/export wall seconds: {bake['total_finalize_seconds']:.3f}
Last successful bake/material/export seconds: {bake['bake_material_export_seconds']:.3f}
Final six actual render seconds: {renders['total_render_seconds']:.3f}
Wall time includes previews, font diagnosis, an abandoned slow per-object bake,
the ground alignment and header placement corrections, final renders, checks
and documentation.
Per-stage values are actual recorded runs, not an invented sum of every attempt.
'''
(ROOT/'README.txt').write_text(README,encoding='utf-8-sig')
record={'asset':'VendingMachine','status':'ready_for_review','started_at_utc':started.isoformat(),'started_at_kst':started.astimezone(kst).isoformat(),'finished_at_utc':finished.isoformat(),'finished_at_kst':finished.astimezone(kst).isoformat(),'elapsed_seconds':elapsed,'imagegen_wall_seconds':prov['imagegen_elapsed_seconds'],'main_files':['VendingMachine.blend','VendingMachine.glb','README.txt'],'validation_summary':{'uv_passed':uv['passed'],'glb_passed':glb['passed'],'visual_review_passed':visual['passed'],'body_factor_white':glb['body_material_is_white'],'images_identical':glb['all_image_bytes_match_external_atlas'],'feet_at_z_zero':True,'effective_texel_density_px_m':uv['effective_global_density_px_per_m']},'blockers':[],'limitations':['No mechanics, rig, collision or LODs.','523 px/m achieved versus original nominal 800 px/m.','Raster UV test has explicitly reported subpixel limits.','Low-alpha glass is an artistic cross-viewer choice.']}
(ROOT/'STATUS.json').write_text(json.dumps(record,indent=2),encoding='utf8')
files=[]
for rel in ['VendingMachine.blend','VendingMachine.glb','README.txt','STATUS.json']:
    p=ROOT/rel;files.append({'file':rel,'bytes':p.stat().st_size,'sha256':sha(p)})
for dirname in ['textures','renders','validation','source']:
    for p in sorted((ROOT/dirname).rglob('*')):
        if p.is_file() and p.name!='delivery_manifest.json' and not p.name.endswith(('.blend1','.blend2')):
            files.append({'file':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
(ROOT/'validation/delivery_manifest.json').write_text(json.dumps({'created_at_utc':finished.isoformat(),'files':files},indent=2),encoding='utf8')
print(json.dumps(record),flush=True)
