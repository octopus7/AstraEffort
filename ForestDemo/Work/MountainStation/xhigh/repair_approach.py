import unreal as u
from pathlib import Path
root='/Game/MountainStation/xhigh';work=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh')
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
task=u.AssetImportTask();task.filename=str(work/'SourceArt/Terrain.fbx');task.destination_path=root+'/Meshes';task.destination_name='SM_Terrain';task.automated=True;task.replace_existing=True;task.save=True
opt=u.FbxImportUI();opt.import_mesh=True;opt.import_materials=False;opt.import_textures=False;opt.import_as_skeletal=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.automated_import_should_detect_type=False
data=opt.static_mesh_import_data;data.combine_meshes=True;data.auto_generate_collision=False;data.generate_lightmap_u_vs=False;data.convert_scene=True;data.convert_scene_unit=True
task.options=opt;u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
mesh=u.load_asset(root+'/Meshes/SM_Terrain')
for i,slot in enumerate(mesh.static_materials):mesh.set_material(i,u.load_asset(root+'/Materials/M_'+str(slot.material_slot_name).split('.')[0]))
body=mesh.get_editor_property('body_setup');body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);body.set_editor_property('double_sided_geometry',True)
u.EditorAssetLibrary.save_loaded_asset(mesh)
print('ALDER_APPROACH_REPAIRED')
