import unreal as u, runpy, json, traceback, datetime
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/TexturePass')
try:
 runpy.run_path(str(ROOT/'validate_level.py'),init_globals={'KEEP_EDITOR_OPEN':True})
 validation=json.loads((ROOT/'validation.json').read_text());build=json.loads((ROOT/'build_result.json').read_text());uv=json.loads((ROOT/'uv_fbx_validation.json').read_text())
 eas=u.get_editor_subsystem(u.EditorAssetSubsystem);sme=u.get_editor_subsystem(u.StaticMeshEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
 records=json.loads((ROOT/'uv_report.json').read_text())['meshes'];meshes=[];bad=[]
 for record in records:
  mesh=eas.load_asset('/Game/Forest/ultra/Meshes/UV/'+record['variant']);assert mesh
  channels=sme.get_num_uv_channels(mesh,0);settings=sme.get_lod_build_settings(mesh,0)
  body=mesh.get_editor_property('body_setup');flag=body.get_editor_property('collision_trace_flag')
  shapes=sme.get_simple_collision_count(mesh)+sme.get_convex_collision_count(mesh)
  collision=True
  if record['source'].startswith(('SM_Broadleaf','SM_Pine')) or record['collision']=='complex':collision=flag==u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
  elif record['collision']=='simple':collision=shapes>0
  mats=[str(x.material_interface.get_path_name()) for x in mesh.static_materials]
  expected=['/Game/Forest/ultra/Materials/M_'+n+'.M_'+n for n in record['materials']]
  row={'mesh':record['variant'],'uv_channels':channels,'full_precision_uv':settings.get_editor_property('use_full_precision_u_vs'),'collision_passed':collision,'collision_shapes':shapes,'materials':mats,'materials_match':mats==expected}
  row['passed']=channels>=1 and row['full_precision_uv'] and collision and row['materials_match'];meshes.append(row)
  if not row['passed']:bad.append(row)
 placed=[]
 for actor in actors:
  if isinstance(actor,u.StaticMeshActor) and '_UV_' in actor.static_mesh_component.static_mesh.get_name():
   s=actor.get_actor_scale3d();placed.append(abs(s.x-1)+abs(s.y-1)+abs(s.z-1)<1e-6)
 validation['checks']['unique_metric_uv_fbx_roundtrip']={'passed':uv['success'] and len(uv['meshes'])==922,'detail':{'file':'uv_fbx_validation.json','count':len(uv['meshes']),'target':32}}
 validation['checks']['ue_uv_material_collision']={'passed':not bad and len(meshes)==922,'detail':{'count':len(meshes),'failures':bad}}
 validation['checks']['baked_scale_placements']={'passed':len(placed)==922 and all(placed),'detail':{'count':len(placed),'scale':[1,1,1]}}
 world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
 # Texture2D::GetSizeX returns 32px placeholder while async data compiles.
 # The engine's registered finish command resolves real platform data first.
 u.SystemLibrary.execute_console_command(world,'Editor.AsyncAssetCompilationFinishAll')
 texture_results=[]
 for name in ['Bark','Canopy','Stone','Wood']:
  tex=eas.load_asset('/Game/Forest/ultra/Textures/T_'+name);texture_results.append({'texture':name,'size':[tex.blueprint_get_size_x(),tex.blueprint_get_size_y()],'present':tex is not None})
 validation['checks']['image_generated_textures_imported']={'passed':all(r['present'] and r['size']==[1254,1254] for r in texture_results),'detail':texture_results}
 texture_links=[]
 for name,meta in build['materials'].items():
  if 'texture' not in meta:continue
  package='/Game/Forest/ultra/Materials/M_'+name;tex_package=meta['texture'].split('.')[0]
  mat=eas.load_asset(package);base=u.MaterialEditingLibrary.get_material_property_input_node(mat,u.MaterialProperty.MP_BASE_COLOR)
  texture_links.append({'material':package,'texture':tex_package,'texture_dependency':tex_package in validation['dependency_graph'].get(package,[]),'base_color_connected':base is not None})
 validation['checks']['generated_texture_surface_bindings']={'passed':len(texture_links)==16 and all(r['texture_dependency'] and r['base_color_connected'] for r in texture_links),'detail':texture_links}
 validation['checks']['texture_build_saved']={'passed':build['success'],'detail':{'mesh_count':build['mesh_count'],'actor_count':len(build['actors'])}}
 validation['success']=all(c['passed'] for c in validation['checks'].values());validation['errors']=[k for k,c in validation['checks'].items() if not c['passed']]
 (ROOT/'ue_texture_validation.json').write_text(json.dumps({'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'meshes':meshes,'textures':texture_results,'success':not bad},indent=2))
 (ROOT/'validation.json').write_text(json.dumps(validation,indent=2))
 assert validation['success'],str(validation['errors'])
 runpy.run_path(str(ROOT/'capture_level.py'),init_globals={'RUN_RUNTIME_VALIDATION':True})
except Exception:
 (ROOT/'review_error.txt').write_text(traceback.format_exc());u.SystemLibrary.quit_editor();raise
