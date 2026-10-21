import unreal as u,json,datetime
from pathlib import Path
R=Path('D:/github/AstraEffort/ForestDemo/Work/high/TexturePass')
BASE='/Game/Forest/high/TexturePass'
t=u.AssetImportTask();t.filename=str(R/'Source/SM_CausticsBed.fbx');t.destination_path=BASE+'/Meshes';t.destination_name='SM_CausticsBed';t.automated=True;t.replace_existing=True;t.save=False;t.factory=u.FbxFactory()
opts=u.FbxImportUI();opts.import_mesh=True;opts.import_materials=False;opts.import_textures=False;opts.import_as_skeletal=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
si=opts.static_mesh_import_data;si.combine_meshes=True;si.auto_generate_collision=False;si.generate_lightmap_u_vs=False;t.options=opts
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
sm=u.EditorAssetLibrary.load_asset(BASE+'/Meshes/SM_CausticsBed');sm.set_material(0,u.EditorAssetLibrary.load_asset(BASE+'/Materials/M_TP_AnimatedCaustics'))
box=sm.get_bounding_box();assert box.max.z<=64.01,box.max.z
assert u.EditorAssetLibrary.save_loaded_asset(sm)
(R/'seabed_depth_validation.json').write_text(json.dumps({'saved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bed_max_z_cm':box.max.z,'sea_base_z_cm':78,'sea_max_negative_wave_displacement_cm':7,'minimum_theoretical_submersion_cm':78-7-box.max.z,'physical_simulation':False},indent=2))
u.log('HIGH_SEABED_DEPTH_REPAIR_COMPLETE')
