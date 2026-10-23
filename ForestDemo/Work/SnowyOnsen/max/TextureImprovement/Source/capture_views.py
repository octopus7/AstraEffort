"""Actual UE captures, preserving first-delivery lighting and common cameras."""
import unreal as u,json,time,hashlib,traceback
from pathlib import Path
from datetime import datetime,timezone
PASS=Path(r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max/TextureImprovement')
BASE=PASS.parent;MAP='/Game/Maps/SnowyOnsen_max'
DETAILS=[{'name':'detail_timber','location':[500,-2450,420],'target':[-350,-2150,160],'fov':48},
         {'name':'detail_stone_snow','location':[-1850,-2100,300],'target':[-1150,-1550,160],'fov':48}]
def now():return datetime.now(timezone.utc).isoformat()
def capture(before=False):
 levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
 world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
 camera=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='CaptureCamera');cc=camera.get_component_by_class(u.CameraComponent)
 for cmd in ['sg.ViewDistanceQuality 2','sg.AntiAliasingQuality 2','sg.ShadowQuality 2','sg.GlobalIlluminationQuality 2','sg.ReflectionQuality 2','sg.PostProcessQuality 2','sg.TextureQuality 2','sg.EffectsQuality 2','sg.FoliageQuality 2','sg.ShadingQuality 2','r.ScreenPercentage 100','r.DynamicRes.OperationMode 0','r.MotionBlurQuality 0','r.Streaming.PoolSize 2000','r.TextureStreaming 0','r.VSync 0']:
  u.SystemLibrary.execute_console_command(world,cmd)
 base=json.loads((BASE/'Screenshots'/'capture_manifest.json').read_text())
 views=[] if before else [{k:v for k,v in r.items() if k in ['name','location','rotation','target','ortho','fov']} for r in base['captures']]
 views+=DETAILS
 dest=PASS/'Screenshots'/('BeforeDetails' if before else '');dest.mkdir(parents=True,exist_ok=True)
 state={'index':0,'phase':'set','at':time.monotonic()+15,'busy':False,'deadline':time.monotonic()+750,'records':[]}
 def tick(dt):
  if state['busy']:return
  state['busy']=True
  try:
   if time.monotonic()>state['deadline']:raise RuntimeError('Capture deadline exceeded')
   if time.monotonic()<state['at']:return
   if state['index']>=len(views):
    (dest/'capture_manifest.json').write_text(json.dumps({'pass':'before_detail' if before else 'TextureImprovement','render':'actual UE5.7 editor viewport','resolution':[1920,1080],'quality':'High2 all sg values','screen_percentage':100,'mode':'Lit','game_view':True,'captures':state['records']},indent=2),encoding='utf8')
    u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor();return
   spec=views[state['index']];path=dest/(spec['name']+'.png')
   if state['phase']=='set':
    if path.exists():path.unlink()
    loc=u.Vector(*spec['location']);rot=u.Rotator(pitch=spec['rotation'][0],yaw=spec['rotation'][1],roll=spec['rotation'][2]) if 'rotation' in spec else u.MathLibrary.find_look_at_rotation(loc,u.Vector(*spec['target']))
    camera.set_actor_location_and_rotation(loc,rot,False,False);cc.set_editor_property('projection_mode',u.CameraProjectionMode.ORTHOGRAPHIC if 'ortho' in spec else u.CameraProjectionMode.PERSPECTIVE)
    if 'ortho' in spec:cc.set_editor_property('ortho_width',spec['ortho'])
    else:cc.set_editor_property('field_of_view',spec['fov'])
    levels.pilot_level_actor(camera);levels.editor_set_game_view(True);u.AutomationLibrary.set_editor_viewport_view_mode(u.ViewModeIndex.VMI_LIT);u.AutomationLibrary.set_editor_active_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
    assert u.AutomationLibrary.get_editor_active_viewport_view_mode()==u.ViewModeIndex.VMI_LIT
    state['rotation']=[rot.pitch,rot.yaw,rot.roll];state['phase']='take';state['at']=time.monotonic()+9
   elif state['phase']=='take':
    if spec['name'] in ['overview','detail_timber','detail_stone_snow']:
     u.log('TEXTURE_RESIDENCY_AT_CAPTURE '+spec['name']);u.SystemLibrary.execute_console_command(world,'ListTextures -CSV')
    state['phase']='wait';state['at']=time.monotonic()+4;state['capture_utc']=now();state['capture_monotonic']=time.monotonic()
    state['task']=u.AutomationLibrary.take_high_res_screenshot(1920,1080,str(path),camera=None,force_game_view=True)
   else:
    if not path.exists():state['at']=time.monotonic()+2;return
    data=path.read_bytes();assert(data[:8],int.from_bytes(data[16:20],'big'),int.from_bytes(data[20:24],'big'))==(b'\x89PNG\r\n\x1a\n',1920,1080)
    record=dict(spec);record.update(rotation=state['rotation'],captured_at_utc=state['capture_utc'],monotonic_seconds=state['capture_monotonic'],sha256=hashlib.sha256(data).hexdigest(),file=path.name,active_view_mode=str(u.AutomationLibrary.get_editor_active_viewport_view_mode()))
    state['records'].append(record);state['index']+=1;state['phase']='set';state['at']=time.monotonic()+1
  except Exception:
   (PASS/'Validation'/'capture_error.json').write_text(json.dumps({'at_utc':now(),'traceback':traceback.format_exc()},indent=2));u.log_error(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
  finally:state['busy']=False
 u.EditorPythonScripting.set_keep_python_script_alive(True);handle=u.register_slate_post_tick_callback(tick)
 globals()['_alive']=(tick,handle,state,camera)
