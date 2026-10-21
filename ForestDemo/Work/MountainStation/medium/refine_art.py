import bpy, os
from mathutils import Matrix
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium'
bpy.ops.wm.open_mainfile(filepath=W+'/AlderPass.blend')
bpy.data.objects['Earth plinth'].location.z=-2.12
bpy.ops.wm.save_as_mainfile(filepath=W+'/AlderPass.blend')
bpy.ops.object.select_all(action='SELECT')
bpy.context.view_layer.objects.active=next(o for o in bpy.context.scene.objects if o.type=='MESH')
bpy.ops.object.join()
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
o=bpy.context.object
# UE's handedness conversion negates FBX Y; bake the inverse to preserve site coordinates.
o.data.transform(Matrix.Diagonal((1,-1,1,1))); o.data.flip_normals(); o.data.update()
bpy.ops.export_scene.fbx(filepath=W+'/AlderPass.fbx',use_selection=True,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',add_leaf_bones=False,bake_anim=False)
