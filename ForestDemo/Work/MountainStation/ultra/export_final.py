"""Export the authoritative final .blend without applying historical refinements."""
import bpy,json,datetime
ROOT=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra'
bpy.ops.wm.open_mainfile(filepath=ROOT+'/SourceArt/AlderPass.blend')
data=json.load(open(ROOT+'/art_manifest.json'))
for entry in data['meshes']:
    o=bpy.data.objects[entry['name']]
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.export_scene.fbx(filepath=entry['file'],use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,axis_forward='Y',axis_up='Z',mesh_smooth_type='FACE',use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False)
    entry['vertices']=len(o.data.vertices);entry['polygons']=len(o.data.polygons);entry['materials']=[m.name for m in o.data.materials]
data['final_export_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();data['ramp_plan_run_cm']=(1300**2+300**2)**.5;data['authoritative_source']='SourceArt/AlderPass.blend'
with open(ROOT+'/art_manifest.json','w') as f:json.dump(data,f,indent=2)
