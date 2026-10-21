import unreal as u, json, os, datetime, traceback
PHASE='D:/github/AstraEffort/ForestDemo/Work/xhigh/TexturePass'
try:
 u.EditorPythonScripting.set_keep_python_script_alive(True)
 XHIGH_KEEP_EDITOR=True
 source=open('D:/github/AstraEffort/ForestDemo/Work/xhigh/validate_scene.py').read().replace("ROOT+'/validation.json'","ROOT+'/TexturePass/validation.json'")
 exec(compile(source,'fresh_scene_validation.py','exec'),globals())
 assert REPORT['passed'],REPORT['errors']
 uv=json.load(open(PHASE+'/SourceArt/uv_report.json'))
 build=json.load(open(PHASE+'/build_summary.json'))
 texreport={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':{},'meshes':{},'actors':[],'textures':[]}
 texreport['checks']['source_uv_no_overlaps']=uv['passed']
 smes=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
 for name,metrics in uv['meshes'].items():
  mesh=u.load_asset('/Game/Forest/xhigh/Meshes/'+name)
  channels=smes.get_num_uv_channels(mesh,0)
  texreport['meshes'][name]={'uv_channels':channels,'source_uv_area':metrics['uv_area'],'base_px_per_m':metrics['base_px_per_m'],'source_overlap_pairs':metrics['positive_area_overlap_pairs']}
  texreport['meshes'][name]['full_precision_uv']=smes.get_lod_build_settings(mesh,0).get_editor_property('use_full_precision_u_vs')
 texreport['checks']['all_saved_meshes_have_uv']=all(m['uv_channels']>=1 for m in texreport['meshes'].values())
 texreport['checks']['both_pines_full_precision_uv']=all(texreport['meshes'][n]['full_precision_uv'] for n in ['SM_Pine_0','SM_Pine_1'])
 for a in eas.get_all_level_actors():
  if not isinstance(a,u.StaticMeshActor):continue
  c=a.static_mesh_component;n=c.static_mesh.get_name();scale=a.get_actor_scale3d().x
  stored=list(c.get_editor_property('custom_primitive_data').get_editor_property('data'))
  expected=uv['meshes'][n]['mesh_sampling_factor']*scale
  actual=stored[0] if stored else None
  texreport['actors'].append({'actor':a.get_actor_label(),'mesh':n,'world_scale':scale,'expected_sampling_factor':expected,'saved_sampling_factor':actual,'matches':actual is not None and abs(expected-actual)<1e-4})
 texreport['checks']['all_895_saved_scale_corrections_match']=len(texreport['actors'])==895 and all(a['matches'] for a in texreport['actors'])
 graph=REPORT['dependency_graph']
 for name in ['bark','foliage','stone','wood','caustics']:
  path='/Game/Forest/xhigh/Textures/T_IG_'+name;tex=u.load_asset(path)
  users=[p for p,ds in graph.items() if path in ds]
  texreport['textures'].append({'path':path,'loaded':tex is not None,'material_users':users,'width':tex.blueprint_get_size_x(),'height':tex.blueprint_get_size_y()})
 texreport['checks']['five_generated_textures_used_by_saved_materials']=all(t['loaded'] and t['material_users'] for t in texreport['textures'])
 for water in ['WaterSea','WaterLake','Foam']:
  m=u.load_asset('/Game/Forest/xhigh/Materials/M_'+water)
  texreport['checks'][water+'_translucent']=m.get_editor_property('blend_mode')==u.BlendMode.BLEND_TRANSLUCENT
 # Export representative saved UE meshes back out for independent UV round-trip checking.
 exportdir='D:/github/AstraEffort/ForestDemo/Saved/Workers/xhigh/TextureRoundtrip';os.makedirs(exportdir,exist_ok=True)
 exported=[]
 for name in ['SM_Broadleaf_1','SM_Pine_0','SM_Boulder_0','SM_Dock']:
  task=u.AssetExportTask();task.object=u.load_asset('/Game/Forest/xhigh/Meshes/'+name);task.filename=exportdir+'/'+name+'.fbx'
  task.automated=True;task.prompt=False;task.replace_identical=True;task.exporter=u.StaticMeshExporterFBX()
  options=u.FbxExportOption();options.ascii=False;options.collision=False;options.level_of_detail=False;task.options=options
  assert u.Exporter.run_asset_export_task(task),'UE FBX export failed '+name
  exported.append(task.filename)
 texreport['roundtrip_exports']=exported
 texreport['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();texreport['passed']=all(texreport['checks'].values())
 json.dump(texreport,open(PHASE+'/texture_validation.json','w'),indent=2)
 assert texreport['passed'],texreport['checks']
 u.log('XHIGH_TEXTURE_VALIDATION_COMPLETE')
 exec(compile(open(PHASE+'/capture_scene.py',encoding='utf-8-sig').read(),'texture_capture.py','exec'),globals())
except Exception:
 open(PHASE+'/validate_error.txt','w').write(traceback.format_exc());u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
