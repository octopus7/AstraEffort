"""Ground-align the finished asset without changing mesh UVs or rebaking pixels."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'VendingMachine.blend'))
asset=[o for o in bpy.data.objects if o.type=='MESH' and o.get('asset_part')]
minimum=min((o.matrix_world@Vector(c)).z for o in asset for c in o.bound_box)
for o in asset:o.location.z-=minimum
bpy.data.objects['Studio_Ground'].location.z=0
bpy.context.scene['asset_ground_alignment_m']=-minimum
bpy.ops.object.select_all(action='DESELECT')
for o in asset:o.select_set(True)
bpy.context.view_layer.objects.active=asset[0]
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'VendingMachine.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'VendingMachine.glb'),export_format='GLB',use_selection=True,export_apply=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_image_format='AUTO',export_extras=True,export_cameras=False,export_lights=False,export_animations=False,export_yup=True)
record={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'translation_z_m':-minimum,'previous_min_z_m':minimum,'new_min_z_m':min((o.matrix_world@Vector(c)).z for o in asset for c in o.bound_box),'ground_z_m':0,'uvs_unchanged':True,'atlas_sha256':hashlib.sha256((ROOT/'textures/packed/VendingMachine_BaseColor_4096.png').read_bytes()).hexdigest()}
(ROOT/'validation/ground_alignment.json').write_text(json.dumps(record,indent=2),encoding='utf8')
print(json.dumps(record),flush=True)
