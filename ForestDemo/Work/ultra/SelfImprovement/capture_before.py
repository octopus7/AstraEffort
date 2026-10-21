"""Real UE renders; no image post-processing. Run in a ticking private editor."""
import unreal as u, json, time, datetime, traceback, math
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement');OUT=ROOT/'Screenshots/Before';OUT.mkdir(exist_ok=True)
levels=u.get_editor_subsystem(u.LevelEditorSubsystem);levels.load_level('/Game/Maps/ultra');levels.editor_set_viewport_realtime(False);levels.editor_set_viewport_realtime(True)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
def cmd(c):u.SystemLibrary.execute_console_command(world,c)
for c in ['sg.ViewDistanceQuality 2','sg.AntiAliasingQuality 2','sg.ShadowQuality 2','sg.GlobalIlluminationQuality 2','sg.ReflectionQuality 2','sg.PostProcessQuality 2','sg.TextureQuality 2','sg.EffectsQuality 2','sg.FoliageQuality 2','sg.ShadingQuality 2','r.ScreenPercentage 100','r.Streaming.PoolSize 1600','DisableAllScreenMessages','r.MotionBlurQuality 0']:
 cmd(c)
actors.select_nothing()
capture=actors.spawn_actor_from_class(u.SceneCapture2D,u.Vector(12000,-12000,16000))
capture.set_actor_label('Temporary evidence capture - never saved')
comp=capture.get_component_by_class(u.SceneCaptureComponent2D)
comp.set_editor_property('capture_source',u.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
comp.set_editor_property('capture_every_frame',False)
comp.set_editor_property('capture_on_movement',True)
comp.set_editor_property('always_persist_rendering_state',True)
comp.set_editor_property('auto_calculate_ortho_planes',True)
# Scene captures do not contain editor selection, grids, widgets or screen messages.
rt=u.RenderingLibrary.create_render_target2d(world,1920,1080,u.TextureRenderTargetFormat.RTF_RGBA8,u.LinearColor(0,0,0,1),False)
comp.set_editor_property('texture_target',rt)
for a in actors.get_all_level_actors():
 if isinstance(a,u.PostProcessVolume):comp.set_editor_property('post_process_settings',a.get_editor_property('settings'))
comp.set_editor_property('post_process_blend_weight',1.0)
views=[
 {'name':'overview','location':[12000,-12000,16000],'target':[0,0,0],'projection':'orthographic','ortho_width_cm':20000},
 {'name':'top_down','location':[0,0,20000],'rotation':[-90,0,0],'projection':'orthographic','ortho_width_cm':20000},
 {'name':'lake','location':[-200,400,343.771],'target':[-1800,-900,180],'projection':'perspective','horizontal_fov':70,'ground_z_cm':173.771,'eye_height_cm':170},
 {'name':'beach','location':[400,3100,205.613],'target':[-2200,3300,120],'projection':'perspective','horizontal_fov':70,'ground_z_cm':35.613,'eye_height_cm':170},
 {'name':'water_t0','location':[400,3100,205.613],'target':[-2200,3300,120],'projection':'perspective','horizontal_fov':70},
 {'name':'water_t1','location':[400,3100,205.613],'target':[-2200,3300,120],'projection':'perspective','horizontal_fov':70},
 {'name':'hero','location':[10500,12500,10700],'target':[0,0,250],'projection':'perspective','horizontal_fov':53}
]
choices=[a for a in actors.get_all_level_actors() if isinstance(a,u.StaticMeshActor) and a.static_mesh_component.static_mesh and a.static_mesh_component.static_mesh.get_name().startswith('SM_Broadleaf')]
tree=min(choices,key=lambda a:(a.get_actor_location()-u.Vector(-400,1700,0)).length())
center,extent=tree.get_actor_bounds(False)
loc=center+u.Vector(1000,1000,500)
views.append({'name':'tree_detail','location':[loc.x,loc.y,loc.z],'target':[center.x,center.y,center.z],'projection':'perspective','horizontal_fov':65,'baseline_actor':tree.get_actor_label(),'baseline_mesh':tree.static_mesh_component.static_mesh.get_path_name()})
manifest={'map':'/Game/Maps/ultra','asset_root':'/Game/Forest/ultra','site_center_cm':[0,0],'ground_reference_z_cm':0,'resolution':[1920,1080],'quality':'High scalability (all sg groups 2), screen percentage 100','renderer':'UE5.7 SceneCapture2D final color LDR, D3D12 SM5','post_processing':'map exposure/color, no image processing','close_views_comparison_limitation':'Lake and beach viewpoints are individually framed; they are not position-equivalent between scenes.','capture_started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'views':[]}
index=0;started=time.monotonic();last_view_time=started;pending=False;tick_handle=None
def set_view(view):
 loc=u.Vector(*view['location'])
 rot=u.Rotator(pitch=view['rotation'][0],yaw=view['rotation'][1],roll=view['rotation'][2]) if 'rotation' in view else u.MathLibrary.find_look_at_rotation(loc,u.Vector(*view['target']))
 capture.set_actor_location_and_rotation(loc,rot,False,True)
 comp.set_editor_property('projection_type',u.CameraProjectionMode.ORTHOGRAPHIC if view['projection']=='orthographic' else u.CameraProjectionMode.PERSPECTIVE)
 comp.set_editor_property('ortho_width',view.get('ortho_width_cm',20000));comp.set_editor_property('fov_angle',view.get('horizontal_fov',70))
 view['rotation_pitch_yaw_roll']=[rot.pitch,rot.yaw,rot.roll]
 u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(loc,rot)
set_view(views[0])
def tick(dt):
 global index,last_view_time,tick_handle
 try:
  comp.capture_scene()
  warmup=45 if index==0 else (3 if views[index]['name']=='water_t1' else 12)
  if time.monotonic()-last_view_time<warmup:return
  view=views[index]
  u.RenderingLibrary.export_render_target(world,rt,str(OUT),view['name']+'.png')
  view['shader_world_time_seconds']=u.GameplayStatics.get_time_seconds(world);view['captured_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();view['warmup_seconds']=warmup;manifest['views'].append(dict(view))
  (OUT/'capture_manifest.json').write_text(json.dumps(manifest,indent=2))
  u.log('ULTRA_CAPTURE '+view['name'])
  index+=1
  if index>=len(views):
   manifest['capture_finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(OUT/'capture_manifest.json').write_text(json.dumps(manifest,indent=2))
   u.unregister_slate_post_tick_callback(tick_handle)
   if globals().get('RUN_RUNTIME_VALIDATION',False):
    import runpy
    runpy.run_path(str(ROOT/'validate_runtime.py'))
   else:u.SystemLibrary.quit_editor()
   return
  set_view(views[index]);last_view_time=time.monotonic()
 except Exception:
  (OUT/'capture_error.txt').write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(tick_handle);u.SystemLibrary.quit_editor()
tick_handle=u.register_slate_post_tick_callback(tick)
u.log('ULTRA_CAPTURE_TICK_REGISTERED')



