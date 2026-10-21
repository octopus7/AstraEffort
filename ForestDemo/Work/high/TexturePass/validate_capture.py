import unreal as u, json, math, traceback, datetime, time
from pathlib import Path
ROOT=Path('D:/github/AstraEffort/ForestDemo/Work/high/TexturePass');OUT=ROOT/'Screenshots';OUT.mkdir(exist_ok=True)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
E=u.EditorAssetLibrary;ls=u.get_editor_subsystem(u.LevelEditorSubsystem);a=u.get_editor_subsystem(u.EditorActorSubsystem)
assert ls.load_level('/Game/Maps/high')

world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
allactors=a.get_all_level_actors()

ms=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
tex=u.EditorAssetLibrary.load_asset('/Game/Forest/high/TexturePass/Textures/T_GeneratedSurfaceAtlas')
assert tex
texture_audit={'generated_texture':tex.get_path_name(),'actual_texture_size':[tex.blueprint_get_size_x(),tex.blueprint_get_size_y()],'prop_actor_count':0,'unique_meshes':{},'materials':{},'instances':[]}
for actor in allactors:
 if isinstance(actor,u.StaticMeshActor) and '_UV' in actor.static_mesh_component.static_mesh.get_name():
  texture_audit['prop_actor_count']+=1;mesh=actor.static_mesh_component.static_mesh
  uvcount=ms.get_num_uv_channels(mesh,0);assert uvcount>=1
  sc=actor.get_actor_scale3d();texture_audit['instances'].append({'actor':actor.get_actor_label(),'mesh_name':mesh.get_name(),'world_scale':[sc.x,sc.y,sc.z]})
  build_settings=ms.get_lod_build_settings(mesh,0);assert build_settings.use_full_precision_u_vs
  texture_audit['unique_meshes'][mesh.get_path_name()]={'uv_channels':uvcount,'full_precision_uvs':build_settings.use_full_precision_u_vs}
  for material in actor.static_mesh_component.get_materials():
   assert material and '/TexturePass/Materials/' in material.get_path_name()
   used=[t.get_path_name() for t in u.MaterialEditingLibrary.get_used_textures(material)]
   assert tex.get_path_name() in used,(material.get_path_name(),used)
   texture_audit['materials'][material.get_path_name()]=used
assert texture_audit['prop_actor_count']==742
bed_actor=next(x for x in allactors if x.get_actor_label()=='Animated underwater caustics')
bed_origin,bed_extent=bed_actor.get_actor_bounds(False);assert bed_origin.z+bed_extent.z<=64.01
texture_audit['seabed_max_world_z_cm']=bed_origin.z+bed_extent.z
exports=ROOT/'Source/UEExports';exports.mkdir(exist_ok=True)
for prefix in ['SM_Broadleaf_0_UV','SM_Rock_2_UV','SM_Grass_0_UV']:
 candidates=[p for p in texture_audit['unique_meshes'] if p.split('.')[-1].startswith(prefix)]
 chosen=min(candidates,key=lambda p:abs(int(p.split('_UV')[-1])-10000))
 mesh=u.EditorAssetLibrary.load_asset(chosen)
 task=u.AssetExportTask();task.object=mesh;task.filename=str(exports/(mesh.get_name()+'.fbx'));task.automated=True;task.prompt=False;task.replace_identical=True;task.exporter=u.StaticMeshExporterFBX()
 options=u.FbxExportOption();options.set_editor_property('collision',False);options.set_editor_property('level_of_detail',False);task.options=options
 assert u.Exporter.run_asset_export_task(task)
(ROOT/'texture_binding_validation.json').write_text(json.dumps(texture_audit,indent=2))

reg=u.AssetRegistryHelpers.get_asset_registry();reg.scan_paths_synchronous(['/Game/Forest/high','/Game/Maps'],True)
opts=u.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_searchable_names=True,include_soft_management_references=True,include_hard_management_references=True)
todo=['/Game/Maps/high']+[str(x.package_name) for x in reg.get_assets_by_path('/Game/Forest/high',recursive=True)]
seen=set();deps={};bad=[]
while todo:
 p=todo.pop()
 if p in seen:continue
 seen.add(p);dd=[str(v) for v in reg.get_dependencies(p,opts)];deps[p]=dd
 for d in dd:
  if d.startswith('/Game/'):
   if not(d.startswith('/Game/Forest/high/') or d=='/Game/Maps/high'):bad.append([p,d])
   else:todo.append(d)
assert not bad,str(bad)
redirectors=[str(x.package_name) for x in reg.get_assets_by_path('/Game/Forest/high',recursive=True) if str(x.asset_class_path.asset_name)=='ObjectRedirector'];assert not redirectors
old_refs=[[p,d] for p,dd in deps.items() for d in dd if d.startswith('/Game/high')];assert not old_refs
wp=world.get_world_settings().get_editor_property('world_partition');assert wp is None
terrain=next(x for x in allactors if x.get_actor_label()=='Terrain');origin,extent=terrain.get_actor_bounds(False)
assert abs(extent.x-5000)<5 and abs(extent.y-5000)<5
player=[x for x in allactors if isinstance(x,u.PlayerStart)];logger=[x for x in allactors if x.get_class().get_name()=='ScreenDebugLogger']
assert len(player)==1 and len(logger)==1
collision=[]
for actor in allactors:
 if isinstance(actor,u.StaticMeshActor):
  c=actor.static_mesh_component;name=c.static_mesh.get_name()
  if any(w in name for w in ['Terrain','EarthRim','Broadleaf','Fir','Rock','FallenLog','Bridge','TrailPost']):
   assert str(c.get_collision_profile_name())=='BlockAll',actor.get_actor_label()
   collision.append(actor.get_actor_label())
scratch=Path('D:/github/AstraEffort/ForestDemo/Saved/Workers/high/ForestDemo/Content')
external=[str(x) for x in scratch.rglob('*') if '__External' in str(x)]
assert not external
groundhits={}
for name,x,y in [('PlayerStart',650,-1900),('LakeBed',-1700,700),('Beach',1800,-2580),('LakeCamera',600,450)]:
 hit=u.SystemLibrary.line_trace_single(world,u.Vector(x,y,2500),u.Vector(x,y,-900),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[actor for actor in allactors if actor!=terrain],u.DrawDebugTrace.NONE,True)
 parts=hit.to_tuple()
 blocking=parts[0]
 assert blocking,name+' has no blocking ground'
 p=parts[4];groundhits[name]={'blocking_hit':blocking,'location':[p.x,p.y,p.z]}
report={'checked_at_utc':utc(),'map_reloaded':True,'actor_count':len(allactors),'owned_packages_checked':len(seen),'forbidden_dependencies':bad,'dependencies':deps,'terrain_extent_cm':[extent.x*2,extent.y*2],'player_start':[player[0].get_actor_location().x,player[0].get_actor_location().y,player[0].get_actor_location().z],'native_hello_logger_count':len(logger),'blocking_mesh_actor_count':len(collision),'external_packages':external,'world_partition':str(world.get_world_settings().get_editor_property('world_partition')) if hasattr(world.get_world_settings(),'world_partition') else 'No external packages; created with new_level (non-WP)','dynamic_lighting':world.get_world_settings().get_editor_property('force_no_precomputed_lighting')}
(ROOT/'validation.json').write_text(json.dumps(report,indent=2))
report['ground_traces']=groundhits
report['world_partition']=None;report['world_partition_check']='WorldSettings.get_editor_property(world_partition) returned None after saved map reload'
report['redirector_packages']=redirectors;report['old_root_dependencies']=old_refs
report['built_data_files']=[str(p) for p in scratch.rglob('*BuiltData*')];assert not report['built_data_files']
(ROOT/'validation.json').write_text(json.dumps(report,indent=2))
# Offscreen engine SceneCapture avoids editor overlays and debug messages entirely.
for cmd in ['sg.ViewDistanceQuality 2','sg.AntiAliasingQuality 2','sg.ShadowQuality 2','sg.GlobalIlluminationQuality 2','sg.ReflectionQuality 2','sg.PostProcessQuality 2','sg.TextureQuality 2','sg.EffectsQuality 2','sg.FoliageQuality 2','r.ScreenPercentage 100','r.MotionBlurQuality 0','r.EyeAdaptationQuality 0']:
 u.SystemLibrary.execute_console_command(world,cmd)
cap=a.spawn_actor_from_class(u.SceneCapture2D,u.Vector(12000,-12000,16300));cap.set_actor_label('Temporary evidence capture')
c=cap.get_component_by_class(u.SceneCaptureComponent2D)
c.set_editor_property('capture_source',u.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
c.set_editor_property('capture_every_frame',True);c.set_editor_property('capture_on_movement',True);c.set_editor_property('always_persist_rendering_state',True)
rt=u.RenderingLibrary.create_render_target2d(world,1920,1080,u.TextureRenderTargetFormat.RTF_RGBA8)
c.set_editor_property('texture_target',rt)
# Use the final map's post-process settings and manual exposure.
pp=next(x for x in allactors if isinstance(x,u.PostProcessVolume))
c.set_editor_property('post_process_settings',pp.get_editor_property('settings'));c.set_editor_property('post_process_blend_weight',1.0)
shots=[
 {'name':'overview','position':[12000,-12000,16300],'target':[0,0,300],'projection':'orthographic','ortho_width_cm':20000},
 {'name':'top_down','position':[0,0,20300],'rotation':[-90,0,0],'projection':'orthographic','ortho_width_cm':20000},
 {'name':'lake','position':[600,450,groundhits['LakeCamera']['location'][2]+170],'target':[-2100,1050,260],'projection':'perspective','horizontal_fov_degrees':70},
 {'name':'beach','position':[1800,-2580,groundhits['Beach']['location'][2]+170],'target':[-1300,-3600,180],'projection':'perspective','horizontal_fov_degrees':70}
]
shots += [dict(shots[-1],name='water_t0'),dict(shots[-1],name='water_t1')]
manifest={'map':'/Game/Maps/high','site_center_cm':[0,0],'ground_reference_z_cm':300,'resolution':[1920,1080],'quality':'High (all sg categories = 2); screen percentage 100','method':'UE SceneCapture2D final-color LDR to RGBA8 render target; no UI/debug/selection overlays','capture_started_at_utc':utc(),'shots':[],'comparison_limit':'lake/beach use distinct local positions, so their framing is not directly equivalent across scenes'}
state={'i':0,'t':time.monotonic(),'started':time.monotonic(),'phase':0}
def setup(s):
 loc=u.Vector(*s['position']);rot=u.Rotator(pitch=s['rotation'][0],yaw=s['rotation'][1],roll=s['rotation'][2]) if 'rotation'in s else u.MathLibrary.find_look_at_rotation(loc,u.Vector(*s['target']))
 cap.set_actor_location_and_rotation(loc,rot,False,False)
 c.set_editor_property('projection_type',u.CameraProjectionMode.ORTHOGRAPHIC if s['projection']=='orthographic' else u.CameraProjectionMode.PERSPECTIVE)
 if s['projection']=='orthographic':c.set_editor_property('ortho_width',20000)
 else:c.set_editor_property('fov_angle',70)
 s['rotation_pitch_yaw_roll']=[rot.pitch,rot.yaw,rot.roll]
 u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(loc,rot)
 c.capture_scene()
setup(shots[0])
u.EditorPythonScripting.set_keep_python_script_alive(True)
def tick(dt):
 try:
  elapsed=time.monotonic()-state['t'];wait=25 if state['i']==0 else 12
  if elapsed<wait:return
  s=shots[state['i']];c.capture_scene()
  u.RenderingLibrary.export_render_target(world,rt,str(OUT),s['name']+'.png')
  s['captured_at_utc']=utc();s['elapsed_capture_seconds']=time.monotonic()-state['started'];s['editor_world_seconds']=u.GameplayStatics.get_time_seconds(world);manifest['shots'].append(s.copy());u.log('HIGH_CAPTURE '+s['name'])
  state['i']+=1;state['t']=time.monotonic()
  if state['i']<len(shots):setup(shots[state['i']])
  else:
   manifest['capture_finished_at_utc']=utc();(OUT/'capture_manifest.json').write_text(json.dumps(manifest,indent=2))
   a.destroy_actor(cap);u.unregister_slate_post_tick_callback(handle);exec(compile((ROOT/'runtime_validate.py').read_text(encoding='utf-8-sig'),str(ROOT/'runtime_validate.py'),'exec'),globals())
 except Exception:
  (ROOT/'capture_error.txt').write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False)
handle=u.register_slate_post_tick_callback(tick)
