"""Clean 1920x1080 UE SceneCapture render evidence, no image postprocessing."""
import unreal as u,json,os,math,time,datetime,traceback,ast
ROOT='D:/github/AstraEffort/ForestDemo/Work/xhigh';OUT=ROOT+'/TexturePass/Screenshots';os.makedirs(OUT,exist_ok=True)
LES=u.get_editor_subsystem(u.LevelEditorSubsystem);EAS=u.get_editor_subsystem(u.EditorActorSubsystem)
LES.load_level('/Game/Maps/xhigh');world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
LES.editor_set_viewport_realtime(False)
LES.editor_set_viewport_realtime(True)
for cmd in ['Scalability 2','sg.ViewDistanceQuality 2','sg.AntiAliasingQuality 2','sg.ShadowQuality 2','sg.GlobalIlluminationQuality 2','sg.ReflectionQuality 2','sg.PostProcessQuality 2','sg.TextureQuality 2','sg.EffectsQuality 2','sg.FoliageQuality 2','r.ScreenPercentage 100','r.Streaming.PoolSize 3000','r.MotionBlurQuality 0','r.PostProcessAAQuality 4']:
 u.SystemLibrary.execute_console_command(world,cmd)
actor=EAS.spawn_actor_from_class(u.SceneCapture2D,u.Vector(12000,-12000,16000));actor.set_actor_label('xhigh_RenderEvidence_Transient')
comp=actor.capture_component2d
rt=u.RenderingLibrary.create_render_target2d(world,1920,1080,u.TextureRenderTargetFormat.RTF_RGBA8,u.LinearColor(0,0,0,1),False)
rt.set_editor_property('target_gamma',2.2)
comp.set_editor_property('texture_target',rt);comp.set_editor_property('capture_source',u.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
comp.set_editor_property('capture_every_frame',True);comp.set_editor_property('capture_on_movement',True)
comp.set_editor_property('always_persist_rendering_state',True)
comp.set_editor_property('post_process_blend_weight',0.0)
views=[
 {'name':'overview','position_cm':[12000,-12000,16000],'target_cm':[0,0,0],'projection':'orthographic','ortho_width_cm':20000},
 {'name':'top_down','position_cm':[0,0,20000],'rotation_deg':[-90,0,0],'projection':'orthographic','ortho_width_cm':20000},
 {'name':'lake','position_cm':[-170,730,490],'target_cm':[-2100,1800,260],'projection':'perspective','horizontal_fov_deg':70},
 {'name':'beach','position_cm':[900,-1710,350],'target_cm':[-2700,-2520,100],'projection':'perspective','horizontal_fov_deg':70},
]
# Reuse only the three pure geometry functions from our own Blender authoring source.
src=ast.parse(open(ROOT+'/make_art.py').read());nodes=[n for n in src.body if isinstance(n,ast.FunctionDef) and n.name in ('coast','lake_r','height')]
env={'math':math,'sin':math.sin,'cos':math.cos,'sqrt':math.sqrt,'exp':math.exp}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<xhigh_terrain_functions>','exec'),env)
z0=env['height'](0,0)*100
for v in views:
 if v['projection']=='perspective':
  x,y,_=v['position_cm'];ground=env['height'](x/100,y/100)*100
  v['position_cm'][2]=ground+170;v['ground_z_cm']=ground;v['eye_height_cm']=170
 else:
  v['position_cm'][2]+=z0
  if 'target_cm' in v:v['target_cm'][2]+=z0
views.extend([{'name':'water_t0','position_cm':[900,-2650,500],'target_cm':[-500,-3400,-100],'projection':'perspective','horizontal_fov_deg':70},{'name':'water_t1','position_cm':[900,-2650,500],'target_cm':[-500,-3400,-100],'projection':'perspective','horizontal_fov_deg':70}])
manifest={'map':'/Game/Maps/xhigh','site_center_cm':[0,0],'ground_reference_z0_cm':z0,'ground_reference_definition':'terrain height at site center (0,0)',
 'resolution':[1920,1080],'scalability':'High (sg.* = 2)','screen_percentage':100,
 'capture_method':'UE SceneCapture2D FinalColorLDR, RGBA8 render target, target gamma 2.2; no UI and no image manipulation',
 'warmup_seconds':{'first_view':45,'subsequent_views':10,'post_capture_export_delay':3},
 'note':'First four cameras and render settings match xhigh first delivery exactly. water_t0 and water_t1 share a fixed additional camera; actual UE Time animation remains enabled.',
 'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'views':[]}
idx=0;stage='warmup';deadline=time.monotonic()+45;handle=None
def set_view(i):
 v=views[i];actor.set_actor_location(u.Vector(*v['position_cm']),False,False)
 rot=u.Rotator(pitch=v['rotation_deg'][0],yaw=v['rotation_deg'][1],roll=v['rotation_deg'][2]) if 'rotation_deg' in v else u.MathLibrary.find_look_at_rotation(u.Vector(*v['position_cm']),u.Vector(*v['target_cm']))
 actor.set_actor_rotation(rot,False);v['rotation_deg']=[rot.pitch,rot.yaw,rot.roll]
 comp.set_editor_property('projection_type',u.CameraProjectionMode.ORTHOGRAPHIC if v['projection']=='orthographic' else u.CameraProjectionMode.PERSPECTIVE)
 comp.set_editor_property('ortho_width',v.get('ortho_width_cm',20000));comp.set_editor_property('fov_angle',v.get('horizontal_fov_deg',70))
 comp.capture_scene();u.log('XHIGH_CAPTURE_VIEW '+v['name'])
set_view(0)
def tick(dt):
 global idx,stage,deadline,handle
 try:
  if time.monotonic()<deadline:return
  if stage=='warmup':
   comp.capture_scene();stage='export';deadline=time.monotonic()+3;return
  v=views[idx];u.RenderingLibrary.export_render_target(world,rt,OUT,v['name']+'.png')
  v['render_world_time_seconds']=u.GameplayStatics.get_real_time_seconds(world);v['captured_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();manifest['views'].append(v.copy())
  json.dump(manifest,open(OUT+'/capture_manifest.json','w'),indent=2)
  idx+=1
  if idx==len(views):
   manifest['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();json.dump(manifest,open(OUT+'/capture_manifest.json','w'),indent=2)
   u.unregister_slate_post_tick_callback(handle);u.log('XHIGH_CAPTURE_COMPLETE')
   exec(compile(open(ROOT+'/TexturePass/runtime_validate.py').read(),'runtime_validate.py','exec'),globals());return
  set_view(idx);stage='warmup';deadline=time.monotonic()+10
 except Exception:
  open(ROOT+'/TexturePass/capture_error.txt','w').write(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
