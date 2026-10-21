import unreal as u, json, datetime, time, traceback, os
u.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra'
MAP='/Game/Maps/MountainStation_ultra'
OUT=ROOT+'/Screenshots';os.makedirs(OUT,exist_ok=True)
levels=u.get_editor_subsystem(u.LevelEditorSubsystem);assert levels.load_level(MAP)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
editor=u.get_editor_subsystem(u.EditorActorSubsystem)
for cmd in ['sg.ViewDistanceQuality 2','sg.AntiAliasingQuality 2','sg.ShadowQuality 2','sg.GlobalIlluminationQuality 2','sg.ReflectionQuality 2','sg.PostProcessQuality 2','sg.TextureQuality 2','sg.EffectsQuality 2','sg.FoliageQuality 2','r.ScreenPercentage 100','r.MotionBlurQuality 0','r.DepthOfFieldQuality 0','r.Streaming.FullyLoadUsedTextures 1']:
    u.SystemLibrary.execute_console_command(world,cmd)
editor.clear_actor_selection_set()
cap=editor.spawn_actor_from_class(u.SceneCapture2D,u.Vector(12000,-12000,16000));comp=cap.capture_component2d
rt=u.RenderingLibrary.create_render_target2d(world,1920,1080,u.TextureRenderTargetFormat.RTF_RGBA8)
comp.texture_target=rt;comp.capture_source=u.SceneCaptureSource.SCS_FINAL_COLOR_LDR;comp.capture_every_frame=True;comp.capture_on_movement=False;comp.always_persist_rendering_state=True
comp.auto_calculate_ortho_planes=False
comp.post_process_blend_weight=1.0
pp=comp.post_process_settings
for k,v in {'override_auto_exposure_method':True,'auto_exposure_method':u.AutoExposureMethod.AEM_MANUAL,'override_auto_exposure_bias':True,'auto_exposure_bias':0.0,'override_auto_exposure_apply_physical_camera_exposure':True,'auto_exposure_apply_physical_camera_exposure':False,'override_motion_blur_amount':True,'motion_blur_amount':0.0}.items():pp.set_editor_property(k,v)
comp.post_process_settings=pp
views=[
 {'name':'overview','location':[12000,-12000,16000],'target':[0,0,0],'projection':'orthographic','ortho_width_cm':20000},
 {'name':'top_down','location':[0,0,20000],'rotation':[-90,0,0],'projection':'orthographic','ortho_width_cm':20000},
 {'name':'platform','location':[800,-190,330],'target':[-550,260,360],'projection':'perspective','horizontal_fov':70,'ground_height_cm':160},
 {'name':'tracks','location':[2100,-420,205],'target':[3160,520,315],'projection':'perspective','horizontal_fov':70,'ground_height_cm':35}]
ground_samples={p['name']:p['ground_hit_cm'][2] for p in json.load(open(ROOT+'/validation.json'))['collision_samples']}
for view in views:
    if view['name'] in ('platform','tracks'):
        view['ground_height_cm']=ground_samples[view['name']+'_detail']
        view['location'][2]=view['ground_height_cm']+170
        view['camera_height_above_ground_cm']=170
    else:
        view['clip_planes']='SceneCapture2D engine defaults with automatic ortho plane shifting disabled'
manifest={'map':MAP,'renderer':'UE 5.7 SceneCapture2D FinalColorLDR; actual scene render','resolution':[1920,1080],'site_center_cm':[0,0,0],'quality':'High (scalability groups 2)','screen_percentage':100,'lighting':'Dynamic key + two non-shadowing fill directionals + movable cubemap skylight','capture_method':'Offscreen editor with real RHI; render-target PNG export; no generated imagery','camera_notes':'Overview and top-down use exact common capture specification. Details use walking-height cameras. No editor overlay or debug draw is included.','captures':[]}
state={'i':-1,'since':time.monotonic(),'phase':'warmup','start':time.monotonic()}
exec(compile(open(ROOT+'/runtime_checks.py').read(),ROOT+'/runtime_checks.py','exec'),globals())
def configure(v):
    loc=u.Vector(*v['location']);rot=u.Rotator(pitch=v['rotation'][0],yaw=v['rotation'][1],roll=v['rotation'][2]) if 'rotation' in v else u.MathLibrary.find_look_at_rotation(loc,u.Vector(*v['target']))
    cap.set_actor_location_and_rotation(loc,rot,False,True)
    comp.projection_type=u.CameraProjectionMode.ORTHOGRAPHIC if v['projection']=='orthographic' else u.CameraProjectionMode.PERSPECTIVE
    comp.ortho_width=v.get('ortho_width_cm',20000);comp.fov_angle=v.get('horizontal_fov',70)
    v['rotation']=[rot.pitch,rot.yaw,rot.roll];v['resolution']=[1920,1080]
    comp.capture_scene()
def tick(dt):
    try:
        now=time.monotonic()
        if now-state['start']>600:raise RuntimeError('Capture timeout')
        if state['phase']=='warmup' and now-state['since']>40:
            u.SystemLibrary.execute_console_command(world,'EnableAllScreenMessages')
            state['runtime_started_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
            levels.editor_request_begin_play();state.update(phase='runtime',since=now)
        elif state['phase']=='runtime' and now-state['since']>3:
            worlds=u.EditorLevelLibrary.get_pie_worlds(False)
            runtime={'started_at_utc':state['runtime_started_at_utc'],'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pie_world_count':len(worlds),'worlds':[]}
            for pw in worlds:
                runtime['worlds'].append(runtime_checks(pw))
                u.SystemLibrary.execute_console_command(pw,'Shot filename='+OUT+'/runtime_hello.png')
            runtime['hello_evidence']='Additional runtime_hello.png requested from live PIE viewport while baseline 10-second Hello is active. Inspect pixels; SceneCapture comparison views exclude debug text.'
            state['runtime']=runtime
            with open(ROOT+'/runtime_validation.json','w') as f:json.dump(runtime,f,indent=2)
            state.update(phase='runtime_evidence',since=now)
        elif state['phase']=='runtime_evidence' and now-state['since']>2:
            levels.editor_request_end_play();state.update(phase='post_play',since=now)
        elif state['phase']=='post_play' and now-state['since']>5:
            state['runtime']['normal_shutdown']=not levels.is_in_play_in_editor()
            state['runtime']['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
            with open(ROOT+'/runtime_validation.json','w') as f:json.dump(state['runtime'],f,indent=2)
            u.SystemLibrary.execute_console_command(world,'DisableAllScreenMessages')
            manifest['capture_started_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
            state['i']=0;configure(views[0]);state.update(phase='settle',since=now)
        elif state['phase']=='settle' and now-state['since']>12:
            v=views[state['i']];u.RenderingLibrary.export_render_target(world,rt,OUT,v['name']+'.png');v['captured_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();manifest['captures'].append(v.copy())
            if state['i']==len(views)-1:manifest['capture_finished_at_utc']=v['captured_at_utc']
            with open(OUT+'/capture_manifest.json','w') as f:json.dump(manifest,f,indent=2)
            state['i']+=1
            if state['i']>=len(views):
                u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor();return
            configure(views[state['i']]);state['since']=now
    except Exception:
        with open(ROOT+'/capture_error.json','w') as f:json.dump({'traceback':traceback.format_exc()},f,indent=2)
        u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
u.log('ALDER_CAPTURE_SCHEDULED')
