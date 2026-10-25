"""Refresh packed PNG bytes after a rebake; do not change mesh or UV data."""
import bpy,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'textures'/'RabbitBike_BaseColor_4096.png'
atlas=bpy.data.images['RabbitBike_BaseColor_4096']
if atlas.packed_file:atlas.unpack(method='REMOVE')
atlas.filepath=str(path);atlas.reload();atlas.pack()
assert hashlib.sha256(bytes(atlas.packed_file.data)).digest()==hashlib.sha256(path.read_bytes()).digest()
bpy.ops.object.select_all(action='DESELECT')
meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('RB_')]
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.export_scene.gltf(filepath=str(ROOT/'RabbitBike.glb'),export_format='GLB',use_selection=True,export_apply=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_animations=False,export_cameras=False,export_lights=False,export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'RabbitBike.blend'))
print('PACKED_ATLAS_REFRESHED',flush=True)
