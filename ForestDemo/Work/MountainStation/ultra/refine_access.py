import bpy, math
ROOT=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra'
bpy.ops.wm.open_mainfile(filepath=ROOT+'/SourceArt/AlderPass.blend')
for name in ['SM_AccessRamp','SM_Railings']:
    for v in bpy.data.objects[name].data.vertices:v.co.y+=4.5-(v.co.x+30)*3/13
for v in bpy.data.objects['SM_Terrain'].data.vertices:
    x,y,z=v.co;centre=5-(x+30)*3/13
    weight=math.exp(-((x+23.5)/10)**8-((y-centre)/3.5)**8)
    v.co.z=z*(1-weight)+.38*weight
for name in ['SM_Terrain','SM_AccessRamp','SM_Railings']:
    o=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.export_scene.fbx(filepath=ROOT+'/SourceArt/'+name+'.fbx',use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,axis_forward='Y',axis_up='Z',mesh_smooth_type='FACE',use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False)
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/SourceArt/AlderPass.blend')
print('ACCESS_CLEARANCE_REFINED',flush=True)
