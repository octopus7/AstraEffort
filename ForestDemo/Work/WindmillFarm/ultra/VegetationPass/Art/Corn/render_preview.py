import bpy, math
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'source.blend'))
for i,name in enumerate(['SM_CornA','SM_CornB','SM_CornC']):
    bpy.data.objects[name].location.x=(i-1)*2.3
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.005))
mat=bpy.data.materials.new('PreviewFloor');mat.diffuse_color=(.19,.22,.16,1);bpy.context.object.data.materials.append(mat)
bpy.ops.object.light_add(type='AREA',location=(1,-4,7));bpy.context.object.data.energy=1300;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=6
bpy.ops.object.light_add(type='AREA',location=(-4,2,4));bpy.context.object.data.energy=900;bpy.context.object.data.size=5
bpy.ops.object.camera_add(location=(4,-9,4.5));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=8.6
s=bpy.context.scene;s.camera=cam;s.render.engine='CYCLES';s.cycles.samples=24;s.render.resolution_x=1600;s.render.resolution_y=1000;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('PreviewWorld');s.world.color=(.32,.32,.32);s.view_settings.view_transform='AgX';s.render.image_settings.file_format='PNG';s.render.filepath=str(OUT/'preview.png')
bpy.ops.render.render(write_still=True)
