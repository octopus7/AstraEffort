import bpy,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source.blend'))
for name,x in [('SM_MeadowTall',-1.8),('SM_MeadowPlume',0),('SM_MeadowReed',1.8)]:bpy.data.objects[name].location.x=x
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.008))
ground=bpy.data.materials.new('preview soil');ground.diffuse_color=(.22,.25,.18,1);bpy.context.object.data.materials.append(ground)
world=bpy.data.worlds.new('PreviewWorld');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.5,.56,.64,1);world.node_tree.nodes['Background'].inputs[1].default_value=.7;bpy.context.scene.world=world
bpy.ops.object.light_add(type='AREA',location=(-3,-4,7));bpy.context.object.data.energy=900;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=5
bpy.ops.object.camera_add(location=(4,-8,3.6));camera=bpy.context.object;direction=Vector((0,0,.75))-camera.location;camera.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=6.2
scene=bpy.context.scene;scene.camera=camera;scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=650;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ROOT/'source_preview.png')
scene.view_settings.view_transform='AgX';bpy.ops.render.render(write_still=True)
