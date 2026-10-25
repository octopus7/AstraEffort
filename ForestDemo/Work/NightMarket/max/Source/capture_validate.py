import unreal as u, json, datetime, time, traceback, struct, hashlib
from pathlib import Path

WORK=Path(r'D:/github/AstraEffort/ForestDemo/Work/NightMarket/max');ROOT='/Game/NightMarket/max';MAP='/Game/Maps/NightMarket_max'
SHOTS=WORK/'Screenshots';SHOTS.mkdir(exist_ok=True)
EVID=WORK/'Evidence';EVID.mkdir(exist_ok=True)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(path,data):path.write_text(json.dumps(data,indent=2,default=str),encoding='utf-8')
def arr(v):return [v.x,v.y,v.z]
levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
def cmd(s):u.SystemLibrary.execute_console_command(u.EditorLevelLibrary.get_editor_world(),s)
manifest={'theme':'NightMarket','effort':'max','map':MAP,'capture_started_at_utc':now(),'source':'Unreal Engine 5.7 full editor HighResScreenshot; actual saved scene','resolution':[1920,1080],'quality':'High (2)','screen_percentage':100,'view_mode':'Lit','game_view':True,'camera_piloted':True,'animation':False,'physical_approximations':['Opaque low-roughness puddle surfaces with Lumen reflections','Static sculpted steam; no rain/fluid simulation'],'screenshots':[]}
state={'phase':'setup','deadline':0,'index':0,'task':None,'callback':None}
def finish_error():
 write(EVID/'capture_error.json',{'at_utc':now(),'traceback':traceback.format_exc(),'phase':state['phase']})
 u.log_error(traceback.format_exc())
 if state.get('callback'):u.unregister_slate_post_tick_callback(state['callback'])
 u.SystemLibrary.quit_editor()

def validate():
 assert levels.load_level(MAP),'Saved map load failed'
 world=u.EditorLevelLibrary.get_editor_world();ws=world.get_world_settings();wp=ws.get_editor_property('world_partition')
 reg=u.AssetRegistryHelpers.get_asset_registry();reg.scan_paths_synchronous(['/Game'],True)
 opt=u.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True,include_game_package_references=True,include_editor_only_package_references=True,include_hard_management_references=True,include_soft_management_references=True)
 pending=[MAP];visited=set();graph={};violations=[]
 while pending:
  p=pending.pop()
  if p in visited:continue
  visited.add(p);deps=[str(x) for x in reg.get_dependencies(p,opt)];graph[p]=deps
  for d in deps:
   if d.startswith('/Game/'):
    if not(d.startswith(ROOT+'/') or d==MAP):violations.append({'from':p,'to':d})
    if d not in visited:pending.append(d)
 mesh_actors=[];bad_materials=[];cameras={};sources=set();expected_resources=set();lighting=[];actual_materials={}
 for actor in actors.get_all_level_actors():
  if isinstance(actor,u.CameraActor):cameras[actor.get_actor_label().removeprefix('Capture_')]=actor
  if isinstance(actor,u.StaticMeshActor):
   c=actor.static_mesh_component;me=c.get_editor_property('static_mesh');path=me.get_path_name() if me else None
   materials=[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())]
   if path and path.startswith('/Game/'):expected_resources.add(path.split('.')[0])
   for i in range(c.get_num_materials()):
    mat=c.get_material(i)
    if mat and mat.get_path_name().startswith('/Game/'):
     expected_resources.add(mat.get_path_name().split('.')[0]);actual_materials[mat.get_path_name()]=mat
   if not path:bad_materials.append(actor.get_actor_label()+':missing mesh')
   for mat in materials:
    if not mat or not mat.startswith(ROOT+'/'):bad_materials.append(actor.get_actor_label()+':'+str(mat))
   org,ext=actor.get_actor_bounds(False);mesh_actors.append({'label':actor.get_actor_label(),'mesh':path,'materials':materials,'bounds_origin_cm':arr(org),'bounds_extent_cm':arr(ext),'scale':arr(actor.get_actor_scale3d())});sources.add(path)
  for cls in [u.PointLightComponent,u.DirectionalLightComponent,u.SkyLightComponent]:
   lc=actor.get_component_by_class(cls)
   if lc:
    mobility=lc.get_editor_property('mobility')
    lighting.append({'actor':actor.get_actor_label(),'class':lc.get_class().get_name(),'mobility':str(mobility),'movable':mobility==u.ComponentMobility.MOVABLE,'intensity':lc.get_editor_property('intensity')})
 used_textures={}
 for path,mat in actual_materials.items():
  textures=[t.get_path_name() for t in u.MaterialEditingLibrary.get_used_textures(mat)]
  used_textures[path]=textures
  expected_resources.update(t.split('.')[0] for t in textures if t.startswith('/Game/'))
 missing_dependency_resources=sorted(expected_resources-visited)
 owned_assets=[str(a.package_name) for a in reg.get_assets_by_path(ROOT,True)]
 extfiles=[str(p) for p in Path(u.Paths.project_content_dir()).rglob('*') if p.is_file() and ('__ExternalActors__' in str(p) or '__ExternalObjects__' in str(p) or '_BuiltData' in p.name)]
 source=json.loads((WORK/'Source'/'source_manifest.json').read_text(encoding='utf-8'))
 names={a['label'] for a in mesh_actors};missing=[e['name'] for e in source['meshes'] if e['name'] not in names]
 ground=next(a for a in mesh_actors if a['label']=='SM_NM_Ground');size=[2*f for f in ground['bounds_extent_cm']]
 assert abs(size[0]-10000)<2 and abs(size[1]-10000)<2,('Ground footprint mismatch',size)
 assert wp is None,'World partition unexpectedly set'
 assert graph.get(MAP) and len(visited)>1,'Empty or incomplete map dependency graph'
 assert not missing_dependency_resources,('Placed resource absent from recursive dependency graph',missing_dependency_resources)
 expected_textures={ROOT+'/Textures/'+m['texture'] for m in source['materials'].values() if m['texture']}
 assert expected_textures.issubset(expected_resources),('Authored texture not used in placed materials',sorted(expected_textures-expected_resources))
 assert len(lighting)==len(source['lights'])+2 and all(l['movable'] for l in lighting),'Dynamic light count/mobility mismatch'
 assert ws.get_editor_property('force_no_precomputed_lighting'),'Precomputed lighting was not disabled'
 uv_audit=json.loads((EVID/'source_uv_verification.json').read_text(encoding='utf-8'))
 assert all(m['normal_orientation_audit']['negative_volume_closed_components']==0 for m in uv_audit['assemblies']),'A closed source component has reversed orientation'
 assert not violations and not bad_materials and not missing and not extfiles,('Validation failures',violations,bad_materials,missing,extfiles)
 result={'at_utc':now(),'reloaded_saved_map':MAP,'world_partition_is_null':wp is None,'force_no_precomputed_lighting':ws.get_editor_property('force_no_precomputed_lighting'),'ground_size_cm':size,'game_dependency_packages':sorted(visited),'dependency_graph':graph,'forbidden_game_dependencies':violations,'external_actor_object_or_builtdata_files':extfiles,'missing_assemblies':missing,'null_or_foreign_materials':bad_materials,'owned_asset_count':len(owned_assets),'owned_assets':owned_assets,'placed_mesh_actor_count':len(mesh_actors),'placed_mesh_actors':mesh_actors,'camera_labels':sorted(cameras),'source_uv_loops_finite':all(e['uv_finite'] and e['uv_loops']>0 for e in source['meshes']),'orientation_evidence':'Recomputed closed-component signed-volume audit plus explicit open font-cap inspection after correction. source_manifest aggregate signed volumes are initial/historical and are not used as final orientation proof.'}
 result.update({'expected_placed_resource_packages':sorted(expected_resources),'missing_dependency_resources':missing_dependency_resources,'actual_material_used_textures':used_textures,'authored_texture_coverage':sorted(expected_textures),'dynamic_lighting':lighting,'all_lighting_movable':all(l['movable'] for l in lighting),'closed_source_component_orientation_audit_passed':True})
 write(EVID/'saved_reload_validation.json',result)
 return cameras

def tick(delta):
 if state.get('busy'):return
 state['busy']=True
 try:
  tm=time.monotonic()
  if tm<state['deadline']:return
  if state['phase']=='setup':
   state['cameras']=validate()
   for s in ['sg.ViewDistanceQuality 2','sg.AntiAliasingQuality 2','sg.ShadowQuality 2','sg.GlobalIlluminationQuality 2','sg.ReflectionQuality 2','sg.PostProcessQuality 2','sg.TextureQuality 2','sg.EffectsQuality 2','sg.FoliageQuality 2','sg.ShadingQuality 2','r.ScreenPercentage 100','r.Editor.Viewport.OverridePIEScreenPercentage 0','r.DynamicRes.OperationMode 0','r.MotionBlurQuality 0','r.VSync 0','r.TextureStreaming 0','DisableAllScreenMessages']:
    cmd(s)
   actors.clear_actor_selection_set();levels.editor_set_game_view(True);levels.editor_set_viewport_realtime(True)
   state['phase']='prepare';state['deadline']=tm+30
  elif state['phase']=='prepare':
   if state['index']==4:
    manifest['capture_finished_at_utc']=now();write(SHOTS/'capture_manifest.json',manifest)
    u.unregister_slate_post_tick_callback(state['callback']);u.log('NIGHT_MARKET_CAPTURE_COMPLETE');u.SystemLibrary.quit_editor();return
   name=['overview','top_down','market','alley'][state['index']];cam=state['cameras'][name]
   levels.pilot_level_actor(cam);levels.set_exact_camera_view(True);levels.editor_set_game_view(True)
   u.AutomationLibrary.set_editor_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
   u.AutomationLibrary.set_editor_active_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
   state['active_name']=name;state['phase']='capture';state['deadline']=tm+12
  elif state['phase']=='capture':
   name=state['active_name'];cam=state['cameras'][name];path=SHOTS/(name+'.png')
   if path.exists():path.unlink()
   mode=u.AutomationLibrary.get_editor_active_viewport_view_mode()
   assert mode==u.ViewModeIndex.VMI_LIT,('Viewport is not Lit',mode)
   cc=cam.get_component_by_class(u.CameraComponent);rot=cam.get_actor_rotation()
   state['record']={'name':name,'file':name+'.png','requested_at_utc':now(),'camera_actor':cam.get_actor_label(),'position_cm':arr(cam.get_actor_location()),'rotation_deg':[rot.pitch,rot.yaw,rot.roll],'projection':str(cc.get_editor_property('projection_mode')),'ortho_width_cm':cc.get_editor_property('ortho_width'),'fov_deg':cc.get_editor_property('field_of_view'),'active_view_mode':str(mode),'game_view_confirmed':levels.editor_get_game_view(),'piloted_actor':levels.get_pilot_level_actor().get_actor_label(),'screen_percentage':u.SystemLibrary.get_console_variable_float_value('r.ScreenPercentage'),'quality_values':{x:u.SystemLibrary.get_console_variable_int_value('sg.'+x+'Quality') for x in ['ViewDistance','AntiAliasing','Shadow','GlobalIllumination','Reflection','PostProcess','Texture','Effects','Foliage','Shading']}}
   state['phase']='collect';state['deadline']=tm+8;state['timeout']=tm+120
   state['task']=u.AutomationLibrary.take_high_res_screenshot(1920,1080,str(path),camera=None,force_game_view=True)
  elif state['phase']=='collect':
   path=SHOTS/(state['active_name']+'.png')
   if not path.exists():
    if tm>state['timeout']:raise RuntimeError('Screenshot did not arrive: '+str(path))
    state['deadline']=tm+3;return
   data=path.read_bytes();dimensions=list(struct.unpack('>II',data[16:24]));assert dimensions==[1920,1080],dimensions
   state['record'].update({'completed_at_utc':now(),'dimensions':dimensions,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
   manifest['screenshots'].append(state['record']);write(SHOTS/'capture_manifest.json',manifest)
   state['index']+=1;state['phase']='prepare';state['deadline']=tm+1
 except Exception:finish_error()
 finally:state['busy']=False

u.EditorPythonScripting.set_keep_python_script_alive(True)
state['callback']=u.register_slate_post_tick_callback(tick)
