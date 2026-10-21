"""Correct first-pass exports to centimetres and refine the access ramp.
The primary build_art.py contains these changes for clean reproduction.
"""
import bpy, math, os
ROOT=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra'
bpy.ops.wm.open_mainfile(filepath=ROOT+'/SourceArt/AlderPass.blend')
o=bpy.data.objects['SM_Terrain']
for v in o.data.vertices:
    x,y,z=v.co
    access=math.exp(-((x+23.5)/10)**8-((y-.5)/3.5)**8)
    v.co.z=z*(1-access)+.38*access
for name in ['SM_AccessRamp','SM_Railings']:
    for v in bpy.data.objects[name].data.vertices:v.co.x-=5
for o in bpy.data.objects:
    if o.type!='MESH':continue
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.export_scene.fbx(filepath=ROOT+'/SourceArt/'+o.name+'.fbx',use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,axis_forward='Y',axis_up='Z',mesh_smooth_type='FACE',use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False)
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/SourceArt/AlderPass.blend')
print('ALDER_ART_FINALIZED',flush=True)
