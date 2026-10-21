"""Private source-art QA only; never substituted for required Unreal evidence."""
import bpy,math
from mathutils import Vector
ROOT='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high'
bpy.ops.wm.open_mainfile(filepath=ROOT+'/Source/Solmaru.blend')
scene=bpy.context.scene
for mat in bpy.data.materials:
 mat.use_nodes=True;p=mat.node_tree.nodes.get('Principled BSDF')
 if p:p.inputs['Base Color'].default_value=mat.diffuse_color;p.inputs['Roughness'].default_value=.75
bpy.ops.object.camera_add(location=(120,-120,160));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=180;scene.camera=cam
bpy.ops.object.light_add(type='SUN',location=(20,-30,60));sun=bpy.context.object;sun.data.energy=2.5;sun.rotation_euler=(.5,-.5,-.5);sun.data.angle=.25
scene.world.color=(.35,.35,.35);scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True
scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
scene.render.filepath='D:/github/AstraEffort/ForestDemo/Saved/Workers/MountainStation/high/source_qa.png'
bpy.ops.render.render(write_still=True)
