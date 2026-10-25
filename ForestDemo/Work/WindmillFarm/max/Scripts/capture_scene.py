"""Actual offscreen UE editor rendering, with tick-based asynchronous screenshots."""
import unreal, json, time, traceback, os
from pathlib import Path
from datetime import datetime, timezone

WORK=Path(r'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/max')
OUT=WORK/'Screenshots'
OUT.mkdir(parents=True,exist_ok=True)
MAP='/Game/Maps/WindmillFarm_max'
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert level.load_level(MAP),'Cannot load saved map for actual capture'
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actor_subsystem=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actor_subsystem.set_selected_level_actors([])
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationLibrary.set_editor_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT)
unreal.AutomationLibrary.set_editor_active_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT)
CAMERAS={a.get_actor_label().replace('Capture_',''):a for a in actor_subsystem.get_all_level_actors() if a.get_actor_label().startswith('Capture_')}
COMMANDS=['sg.ViewDistanceQuality 2','sg.AntiAliasingQuality 2','sg.ShadowQuality 2','sg.GlobalIlluminationQuality 2','sg.ReflectionQuality 2',
          'sg.PostProcessQuality 2','sg.TextureQuality 2','sg.EffectsQuality 2','sg.FoliageQuality 2','sg.ShadingQuality 2',
          'r.ScreenPercentage 100','r.MotionBlurQuality 0','r.VSync 0','r.Streaming.FullyLoadUsedTextures 1','DisableAllScreenMessages']
for command in COMMANDS:unreal.SystemLibrary.execute_console_command(world,command)
manifest={'map':MAP,'engine':'Unreal Engine 5.7','renderer':'Actual UnrealEditor-Cmd DX12 renderer, offscreen, High scalability',
 'resolution':[1920,1080],'screen_percentage':100,'scalability':'High (2)','generated_image_substitution':False,'post_capture_image_adjustments':False,
 'motion_blur':False,'game_view':True,'visual_review_status':'pending','created_at_utc':datetime.now(timezone.utc).isoformat(),'console_commands':COMMANDS,'captures':[],
 'scope_note':'100x100m original farm; common overview/top-down cameras; farm-specific perspective close views.',
 'animation_note':'Time-driven shader rotor at 0.12 radians/second. Timed shots are actual editor rendering; packaged-game execution is not claimed.'}
jobs=[('overview','overview',10),('top_down','top_down',10),('windmill','windmill',10),('farm','farm',10),('windmill_t0','windmill',10),('windmill_t1','windmill',10)]
state={'index':0,'next':time.monotonic()+35,'task':None,'request':None,'done':False,'started':time.monotonic()}

def persist():
    (OUT/'capture_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

def quit_safely():
    unreal.unregister_slate_post_tick_callback(TICK_HANDLE)
    unreal.SystemLibrary.quit_editor()

def tick(delta):
    try:
        if state['done']:return
        now=time.monotonic()
        if now-state['started']>480:raise RuntimeError('Capture exceeded eight-minute limit')
        if now<state['next']:return
        if state['request']:
            request=state['request'];path=Path(request['path'])
            if not path.is_file() or path.stat().st_mtime<request['unix_requested_at']:
                if now-request['monotonic_requested_at']>90:raise RuntimeError('Actual screenshot was not written: '+str(path))
                state['next']=now+1;return
            request['completed_at_utc']=datetime.now(timezone.utc).isoformat()
            request['file_bytes']=path.stat().st_size
            request.pop('unix_requested_at');request.pop('monotonic_requested_at')
            manifest['captures'].append(request);persist()
            unreal.log('WINDMILL_CAPTURE_WRITTEN '+request['file'])
            state['request']=None;state['task']=None;state['index']+=1;state['next']=now+10
            return
        if state['index']>=len(jobs):
            manifest['finished_at_utc']=datetime.now(timezone.utc).isoformat();manifest['passed']=True;persist()
            state['done']=True;unreal.log('WINDMILL_CAPTURES_COMPLETE');quit_safely();return
        filename,camera_key,delay=jobs[state['index']]
        cam=CAMERAS[camera_key];comp=cam.get_component_by_class(unreal.CameraComponent)
        unreal.EditorLevelLibrary.pilot_level_actor(cam)
        unreal.AutomationLibrary.set_editor_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT)
        unreal.AutomationLibrary.set_editor_active_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT)
        unreal.EditorLevelLibrary.editor_set_game_view(True)
        assert unreal.AutomationLibrary.get_editor_active_viewport_view_mode()==unreal.ViewModeIndex.VMI_LIT,'Viewport is not Lit'
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        loc=cam.get_actor_location();rot=cam.get_actor_rotation()
        request={'file':filename+'.png','path':str(OUT/(filename+'.png')),'camera_actor':cam.get_actor_label(),
          'location_cm':[loc.x,loc.y,loc.z],'rotation_pitch_yaw_roll':[rot.pitch,rot.yaw,rot.roll],
          'projection':str(comp.get_editor_property('projection_mode')),'ortho_width_cm':comp.get_editor_property('ortho_width'),
          'horizontal_fov_degrees':comp.get_editor_property('field_of_view'),'requested_at_utc':datetime.now(timezone.utc).isoformat(),
          'viewport_view_mode':str(unreal.AutomationLibrary.get_editor_active_viewport_view_mode()),
          'unix_requested_at':time.time(),'monotonic_requested_at':now,'seconds_since_capture_script_start':now-state['started']}
        state['request']=request
        state['task']=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,request['path'],camera=None,delay=2.0,force_game_view=True)
        state['next']=time.monotonic()+delay
    except Exception:
        manifest['passed']=False;manifest['error']=traceback.format_exc();persist()
        unreal.log_error(manifest['error']);state['done']=True;quit_safely()

TICK_HANDLE=unreal.register_slate_post_tick_callback(tick)
unreal.log('WINDMILL_CAPTURE_TICK_REGISTERED')
