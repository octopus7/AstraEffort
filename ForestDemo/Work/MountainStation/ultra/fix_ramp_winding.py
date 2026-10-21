import bpy,bmesh
ROOT=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra'
bpy.ops.wm.open_mainfile(filepath=ROOT+'/SourceArt/AlderPass.blend')
o=bpy.data.objects['SM_AccessRamp'];bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.export_scene.fbx(filepath=ROOT+'/SourceArt/SM_AccessRamp.fbx',use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,axis_forward='Y',axis_up='Z',mesh_smooth_type='FACE',use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False)
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/SourceArt/AlderPass.blend')
