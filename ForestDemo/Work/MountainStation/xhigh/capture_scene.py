import unreal as u, json, time, sys, traceback
from pathlib import Path
from datetime import datetime, timezone
WORK=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh')
sys.path.insert(0,str(WORK))
from validate_scene import validate
START=time.time()
u.EditorLevelLibrary.load_level('/Game/Maps/MountainStation_xhigh')
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
 if a.get_actor_label().startswith('Alder_'):a.set_actor_scale3d(u.Vector(1,-1,1))
 if a.get_actor_label()=='Sky_Backdrop':a.static_mesh_component.set_collision_profile_name('NoCollision');a.set_actor_enable_collision(False)
u.EditorLevelLibrary.save_current_level()
report=validate()
if not report['success']:u.log_warning('Validation findings retained for repair: '+str(report['errors']))
world=u.EditorLevelLibrary.get_editor_world();actors=u.get_editor_subsystem(u.EditorActorSubsystem)
for a in actors.get_all_level_actors():
 if isinstance(a,u.SkyLight):a.light_component.recapture_sky()
for c in ['sg.ViewDistanceQuality 2','sg.AntiAliasingQuality 2','sg.ShadowQuality 2','sg.GlobalIlluminationQuality 2','sg.ReflectionQuality 2','sg.PostProcessQuality 2','sg.TextureQuality 2','sg.EffectsQuality 2','sg.FoliageQuality 2','sg.ShadingQuality 2','r.ScreenPercentage 100','r.MotionBlurQuality 0','r.Streaming.FullyLoadUsedTextures 1','r.TextureStreaming 0','t.IdleWhenNotForeground 0','t.MaxFPS 30','DisableAllScreenMessages']:
 u.SystemLibrary.execute_console_command(world,c)
cap=actors.spawn_actor_from_class(u.SceneCapture2D,u.Vector(12000,-12000,16000));cap.set_actor_label('Temporary_EvidenceCapture')
comp=cap.capture_component2d
target=u.RenderingLibrary.create_render_target2d(world,1920,1080,u.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
comp.texture_target=target;comp.capture_source=u.SceneCaptureSource.SCS_FINAL_COLOR_LDR
comp.capture_every_frame=True;comp.capture_on_movement=False;comp.always_persist_rendering_state=True
comp.set_editor_property('auto_calculate_ortho_planes',True)
comp.set_editor_property('max_view_distance_override',200000)
pp=next(a for a in actors.get_all_level_actors() if isinstance(a,u.PostProcessVolume))
comp.post_process_settings=pp.settings;comp.post_process_blend_weight=1
specs=[
 {'name':'overview','position':[12000,-12000,16022],'target':[0,0,22],'projection':'orthographic','ortho_width_cm':20000},
 {'name':'top_down','position':[0,0,20022],'rotation':[-90,0,0],'projection':'orthographic','ortho_width_cm':20000},
 {'name':'platform','position':[1380,-1080,292],'target':[-1100,-970,310],'projection':'perspective','horizontal_fov_degrees':70},
 {'name':'tracks','position':[2000,-920,192],'target':[3250,-900,350],'projection':'perspective','horizontal_fov_degrees':70}
]
manifest={'theme':'MountainStation','effort':'xhigh','map':'/Game/Maps/MountainStation_xhigh','site_center_cm':[0,0],'ground_reference_z_cm':22,'resolution':[1920,1080],'scalability':'High (all sg groups 2)','screen_percentage':100,'renderer':'UE 5.7 SceneCapture2D FinalColorLDR, offscreen D3D12, dynamic raster lighting','debug_ui':'SceneCapture does not draw editor overlays; screen messages disabled for evidence only','captures':[]}
manifest['actual_console_values']={key:u.SystemLibrary.get_console_variable_int_value(key) for key in ['sg.ViewDistanceQuality','sg.AntiAliasingQuality','sg.ShadowQuality','sg.GlobalIlluminationQuality','sg.ReflectionQuality','sg.PostProcessQuality','sg.TextureQuality','sg.EffectsQuality','sg.FoliageQuality','sg.ShadingQuality','r.ScreenPercentage']}
manifest['render_target_format']='RTF_RGBA8_SRGB (native sRGB output, no image post-processing)'
index=0;frame=0;last=time.time();stage='warmup'
def apply_camera(s):
 loc=u.Vector(*s['position']);rot=u.Rotator(pitch=s['rotation'][0],yaw=s['rotation'][1],roll=s['rotation'][2]) if 'rotation' in s else u.MathLibrary.find_look_at_rotation(loc,u.Vector(*s['target']))
 if 'rotation' in s:assert abs(rot.pitch-s['rotation'][0])<.001 and abs(rot.yaw-s['rotation'][1])<.001 and abs(rot.roll-s['rotation'][2])<.001
 cap.set_actor_location_and_rotation(loc,rot,False,False)
 comp.projection_type=u.CameraProjectionMode.ORTHOGRAPHIC if s['projection']=='orthographic' else u.CameraProjectionMode.PERSPECTIVE
 comp.ortho_width=s.get('ortho_width_cm',20000);comp.fov_angle=s.get('horizontal_fov_degrees',70)
 s['rotation_pitch_yaw_roll']=[rot.pitch,rot.yaw,rot.roll]
 u.EditorLevelLibrary.set_level_viewport_camera_info(loc,rot)
 comp.capture_scene()
apply_camera(specs[0])
def tick(dt):
 global index,frame,last,stage
 try:
  frame+=1
  if time.time()-START>600:raise RuntimeError('Capture timeout')
  wait=35 if index==0 else 12
  if time.time()-last<wait or frame<80:return
  s=specs[index];comp.capture_scene()
  u.RenderingLibrary.export_render_target(world,target,str(WORK/'Screenshots'),s['name']+'.png')
  path=WORK/'Screenshots'/(s['name']+'.png')
  if not path.exists() or path.stat().st_size<20000:raise RuntimeError('Missing or undersized capture '+str(path))
  s['captured_at_utc']=datetime.now(timezone.utc).isoformat();s['resolution']=[1920,1080];s['bytes']=path.stat().st_size;manifest['captures'].append(s)
  print('ALDER_CAPTURE',s['name'],path.stat().st_size)
  index+=1
  if index==len(specs):
   manifest['elapsed_seconds']=time.time()-START
   (WORK/'Screenshots/capture_manifest.json').write_text(json.dumps(manifest,indent=2))
   u.unregister_slate_post_tick_callback(handle);actors.destroy_actor(cap)
   import runtime_validate
   runtime_validate.start()
   return
  apply_camera(specs[index]);last=time.time();frame=0
 except Exception:
  (WORK/'Evidence/capture_error.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'traceback':traceback.format_exc()},indent=2));u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
