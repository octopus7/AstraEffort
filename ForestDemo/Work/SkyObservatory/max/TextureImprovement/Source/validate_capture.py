import unreal as u, json, time, traceback, hashlib
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max/TextureImprovement'); EVID=ROOT/'Evidence'; SHOTS=ROOT/'Screenshots'
ASSET='/Game/SkyObservatory/max'; MAP='/Game/Maps/SkyObservatory_max'
def write(name,obj):(EVID/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
u.EditorPythonScripting.set_keep_python_script_alive(True)

def validate():
 world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();ws=world.get_world_settings()
 assert ws.get_editor_property('world_partition') is None,'WorldPartition must be absent'
 assert ws.get_editor_property('force_no_precomputed_lighting')
 registry=u.AssetRegistryHelpers.get_asset_registry();registry.scan_paths_synchronous(['/Game'],force_rescan=True)
 opts=u.AssetRegistryDependencyOptions(True,True,True,True,True,True,True)
 graph={};todo=[MAP];seen=set()
 while todo:
  package=todo.pop()
  if package in seen:continue
  seen.add(package);deps=[str(v) for v in registry.get_dependencies(package,opts)]
  graph[package]=deps
  for dep in deps:
   if dep.startswith('/Game/'):
    assert dep==MAP or dep.startswith(ASSET+'/'),('Forbidden dependency',package,dep)
    todo.append(dep)
 assert graph[MAP] and len(graph)>30,('Empty/incomplete graph',len(graph))
 source=json.loads((EVID/'geometry_baseline.json').read_text());source_groups={g['name']:g for g in source['groups']}
 placed=[];required=set();bounds_min=[float('inf')]*3;bounds_max=[-float('inf')]*3
 all_actors=actors.get_all_level_actors();lights=[]
 for a in all_actors:
  # CameraActor carries an editor-only /Engine camera proxy, never rendered in game view.
  comp=None if isinstance(a,u.CameraActor) else a.get_component_by_class(u.StaticMeshComponent)
  if comp:
   mesh=comp.static_mesh;assert mesh is not None
   package=mesh.get_path_name().split('.')[0];assert package.startswith(ASSET+'/');required.add(package)
   mats=[]
   for i in range(comp.get_num_materials()):
    mat=comp.get_material(i);assert mat,('Missing material',a.get_actor_label(),i)
    mp=mat.get_path_name().split('.')[0];assert mp.startswith(ASSET+'/');required.add(mp)
    textures=u.MaterialEditingLibrary.get_used_textures(mat);assert textures,('No authored texture',mp)
    ts=[]
    for tex in textures:
     tp=tex.get_path_name().split('.')[0];assert tp.startswith(ASSET+'/');required.add(tp);ts.append(tp)
    mats.append({'slot':i,'material':mp,'textures':ts})
   center,extent=a.get_actor_bounds(False)
   expected=source_groups[mesh.get_name()]['bounds_m'];actual=[[c-e,c+e] for c,e in zip((center.x,center.y,center.z),(extent.x,extent.y,extent.z))]
   axis_error=max(abs(actual[k][side]-expected[k][side]*100) for k in range(3) for side in range(2))
   assert axis_error<.1,('Source/UE axis or cm-scale mismatch',mesh.get_name(),axis_error)
   scale=a.get_actor_scale3d();assert all(abs(s-1)<1e-6 for s in (scale.x,scale.y,scale.z)),('Unexpected actor scale',mesh.get_name())
   mesh_settings=u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_lod_build_settings(mesh,0)
   assert mesh_settings.get_editor_property('use_full_precision_u_vs')
   for k,(c,e) in enumerate(zip((center.x,center.y,center.z),(extent.x,extent.y,extent.z))):bounds_min[k]=min(bounds_min[k],c-e);bounds_max[k]=max(bounds_max[k],c+e)
   placed.append({'actor':a.get_actor_label(),'mesh':package,'materials':mats,'bounds_center_cm':[center.x,center.y,center.z],'bounds_extent_cm':[extent.x,extent.y,extent.z],'expected_source_bounds_m':expected,'max_axis_bounds_error_cm':axis_error,'full_precision_uvs':True,'uv_channels':u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_num_uv_channels(mesh,0),'scale':[scale.x,scale.y,scale.z],'lod0_vertices':u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_number_verts(mesh,0)})
  lc=a.get_component_by_class(u.LightComponentBase)
  if lc:
   assert lc.mobility==u.ComponentMobility.MOVABLE
   lights.append({'label':a.get_actor_label(),'mobility':str(lc.mobility)})
 missing=sorted(required-set(graph));assert not missing,('Placed asset absent from dependency graph',missing)
 assert len(placed)==17 and len(required)>=59,(len(placed),len(required))
 assert all(bounds_min[k]>=-5001 and bounds_max[k]<=5001 for k in [0,1]),(bounds_min,bounds_max)
 source=json.loads((EVID/'geometry_baseline.json').read_text());source_z=source['bounds_m']
 assert abs(bounds_min[2]-source_z[0][2]*100)<2 and abs(bounds_max[2]-source_z[1][2]*100)<2,'Incorrect unit scale or up axis'
 report={'validated_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'saved_map_reloaded':True,'map':MAP,'world_partition':None,'force_no_precomputed_lighting':True,'graph_packages':len(graph),'graph':graph,'placed_meshes':placed,'placed_required_packages':sorted(required),'required_missing_from_graph':missing,'lights':lights,'bounds_cm':[bounds_min,bounds_max],'xy_footprint_m':[(bounds_max[k]-bounds_min[k])/100 for k in [0,1]],'cm_scale_and_Z_up_verified_against_source':True,'forbidden_dependencies':[],'missing_materials':[],'external_packages':[]}
 write('ue_validation.json',report)
 return report

try:
 assert levels.load_level(MAP)
 VALID=validate()
 world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
 for cmd in ['sg.ViewDistanceQuality 2','sg.AntiAliasingQuality 2','sg.ShadowQuality 2','sg.GlobalIlluminationQuality 2','sg.ReflectionQuality 2','sg.PostProcessQuality 2','sg.TextureQuality 2','sg.EffectsQuality 2','sg.FoliageQuality 2','sg.ShadingQuality 2','r.ScreenPercentage 100','r.DynamicRes.OperationMode 0','r.MotionBlurQuality 0','r.Streaming.PoolSize 2048']:
  u.SystemLibrary.execute_console_command(world,cmd)
 actors.clear_actor_selection_set();levels.editor_set_game_view(True)
 specs=json.loads((EVID/'camera_specs.json').read_text());cams={a.get_actor_label():a for a in actors.get_all_level_actors() if isinstance(a,u.CameraActor)}
 state={'phase':'warmup','index':0,'deadline':time.time()+30,'busy':False,'records':[],'started':time.time()}
 def tick(delta):
  if state['busy']:return
  state['busy']=True
  try:
   now=time.time()
   if now<state['deadline']:return
   if state['phase']=='warmup' or state['phase']=='next':
    spec=specs[state['index']];cam=cams['Capture_'+spec['name']];levels.pilot_level_actor(cam);levels.set_exact_camera_view(True)
    levels.editor_set_game_view(True);u.AutomationLibrary.set_editor_viewport_view_mode(u.ViewModeIndex.VMI_LIT);u.AutomationLibrary.set_editor_active_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
    levels.editor_invalidate_viewports();state['phase']='shoot';state['deadline']=now+8
   elif state['phase']=='shoot':
    assert u.AutomationLibrary.get_editor_active_viewport_view_mode()==u.ViewModeIndex.VMI_LIT
    assert levels.editor_get_game_view()
    spec=specs[state['index']];out=SHOTS/(spec['name']+'.png');state['path']=out;state['capture_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    actual=cams['Capture_'+spec['name']];pos=actual.get_actor_location();rot=actual.get_actor_rotation();cc=actual.get_component_by_class(u.CameraComponent)
    spec['location_cm']=[pos.x,pos.y,pos.z];spec['rotation_degrees']={'pitch':rot.pitch,'yaw':rot.yaw,'roll':rot.roll}
    spec['ortho_width_cm']=cc.ortho_width if cc.projection_mode==u.CameraProjectionMode.ORTHOGRAPHIC else None
    state['phase']='verify';state['deadline']=now+5
    state['task']=u.AutomationLibrary.take_high_res_screenshot(1920,1080,str(out),camera=None,force_game_view=True)
   elif state['phase']=='verify':
    out=state['path']
    if not out.exists():
     assert now-state['started']<600,'Screenshot timeout';state['deadline']=now+2;return
    data=out.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';assert int.from_bytes(data[16:20],'big')==1920 and int.from_bytes(data[20:24],'big')==1080
    record=dict(specs[state['index']]);record.update({'file':out.name,'capture_requested_at_utc':state['capture_utc'],'file_written_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(out.stat().st_mtime)),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'actual_view_mode':'VMI_LIT','actual_game_view':True})
    state['records'].append(record);state['index']+=1
    if state['index']>=len(specs):
     manifest={'engine':'Unreal Engine 5.7','resolution':[1920,1080],'quality':'High / all sg groups 2','screen_percentage':100,'actual_ue_render':True,'motion_claimed':False,'scene':'SkyObservatory/max','map':MAP,'texture_improvement':True,'captures':state['records']}
     (SHOTS/'capture_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
     write('capture_complete.json',{'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'screenshots':len(specs),'capture_seconds':time.time()-state['started']})
     texinfo=[]
     for path in u.EditorAssetLibrary.list_assets(ASSET+'/Textures',recursive=True,include_folder=False):
      tex=u.load_asset(path);w=tex.blueprint_get_size_x();h=tex.blueprint_get_size_y();assert (w,h)==(1024,1024),(path,w,h)
      texinfo.append({'asset':path,'actual_runtime_width':w,'actual_runtime_height':h,'srgb':tex.get_editor_property('srgb'),'mip_gen_settings':str(tex.get_editor_property('mip_gen_settings')),'power_of_two_mode':str(tex.get_editor_property('power_of_two_mode')),'address_x':str(tex.get_editor_property('address_x')),'address_y':str(tex.get_editor_property('address_y'))})
     write('texture_runtime_validation.json',{'textures':texinfo,'runtime_sizes_verified':True,'mip_counts_evidence':'UE ListTextures console output in this phase log; parsed independently after clean exit'})
     u.SystemLibrary.execute_console_command(world,'ListTextures -alphasort')
     state['phase']='done';u.unregister_slate_post_tick_callback(HANDLE);u.SystemLibrary.quit_editor()
    else:state['phase']='next';state['deadline']=now+1
  except Exception:
   write('capture_error.json',{'traceback':traceback.format_exc(),'state':str(state)});u.log_error(traceback.format_exc());u.unregister_slate_post_tick_callback(HANDLE);u.SystemLibrary.quit_editor()
  finally:state['busy']=False
 HANDLE=u.register_slate_post_tick_callback(tick)
except Exception:
 write('validation_error.json',{'traceback':traceback.format_exc()});u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
