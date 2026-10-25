"""Seat header lettering on the actual round upper-front surface; UVs unchanged."""
import bpy,json,math,hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'VendingMachine.blend'))
tag=bpy.data.objects['Front_Model_Tag'];before={'location':list(tag.location),'rotation_euler':list(tag.rotation_euler)}
r=.135;dz=1.602-1.515;nz=dz/r;ny=-math.sqrt(1-nz*nz);offset=.0007
tag.location=(-.118,-.245+r*ny+offset*ny,1.602+offset*nz+bpy.context.scene.get('asset_ground_alignment_m',0))
tag.rotation_euler[0]=math.atan2(-ny,nz)
asset=[o for o in bpy.data.objects if o.type=='MESH' and o.get('asset_part')]
bpy.ops.object.select_all(action='DESELECT')
for o in asset:o.select_set(True)
bpy.context.view_layer.objects.active=asset[0]
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'VendingMachine.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'VendingMachine.glb'),export_format='GLB',use_selection=True,export_apply=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_image_format='AUTO',export_extras=True,export_cameras=False,export_lights=False,export_animations=False,export_yup=True)
record={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'object':'Front_Model_Tag','before':before,'after':{'location':list(tag.location),'rotation_euler':list(tag.rotation_euler)},'tangent_surface_center_original_z_m':1.602,'normal_offset_m':offset,'uvs_and_atlas_unchanged':True,'glb_sha256':hashlib.sha256((ROOT/'VendingMachine.glb').read_bytes()).hexdigest()}
(ROOT/'validation/header_seating.json').write_text(json.dumps(record,indent=2),encoding='utf8')
print(json.dumps(record),flush=True)
