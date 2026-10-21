import unreal as u,json,datetime
from pathlib import Path
R=Path('D:/github/AstraEffort/ForestDemo/Work/high/TexturePass');BASE='/Game/Forest/high/TexturePass'
E=u.EditorAssetLibrary;ms=u.get_editor_subsystem(u.StaticMeshEditorSubsystem);tasks=[]
for f in sorted((R/'Source/FBX').glob('*.fbx')):
 t=u.AssetImportTask();t.filename=str(f);t.destination_path=BASE+'/Meshes';t.destination_name=f.stem;t.automated=True;t.replace_existing=True;t.save=False;t.factory=u.FbxFactory()
 opts=u.FbxImportUI();opts.import_mesh=True;opts.import_materials=False;opts.import_textures=False;opts.import_as_skeletal=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
 si=opts.static_mesh_import_data;si.combine_meshes=True;si.auto_generate_collision=False;si.generate_lightmap_u_vs=False;si.remove_degenerates=False;t.options=opts;tasks.append(t)
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
for f in sorted((R/'Source/FBX').glob('*.fbx')):
 sm=E.load_asset(BASE+'/Meshes/'+f.stem)
 for i,slot in enumerate(sm.static_materials):
  key=str(slot.material_slot_name).removeprefix('M_');m=E.load_asset(BASE+'/Materials/M_TP_'+key);assert m;sm.set_material(i,m)
 settings=ms.get_lod_build_settings(sm,0);settings.use_full_precision_u_vs=True;settings.remove_degenerates=False;ms.set_lod_build_settings(sm,0,settings)
 ms.remove_collisions(sm)
 if 'Bridge' in f.stem:sm.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
 elif any(k in f.stem for k in ['Broadleaf','Fir','Rock','FallenLog','TrailPost']):ms.add_simple_collisions(sm,u.ScriptingCollisionShapeType.NDOP26)
 assert E.save_loaded_asset(sm)
(R/'ue_uv_precision_repair.json').write_text(json.dumps({'saved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'variants_reimported':len(tasks),'explicit_source_triangles':True,'use_full_precision_uvs':True,'remove_degenerates':False},indent=2))
u.log('HIGH_UV_PRECISION_REPAIR_COMPLETE')
