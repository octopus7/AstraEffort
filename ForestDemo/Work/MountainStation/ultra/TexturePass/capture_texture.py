import unreal as u,json,time,datetime,traceback
from pathlib import Path
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/TexturePass');OUT=R/'Screenshots';OUT.mkdir(exist_ok=True)
original=json.loads((R.parent/'FirstDelivery/Screenshots/capture_manifest.json').read_text());views=original['captures']
for v in views:v.pop('captured_at_utc',None)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();editor=u.get_editor_subsystem(u.EditorActorSubsystem);editor.clear_actor_selection_set()
for cmd in ['sg.ViewDistanceQuality 2','sg.AntiAliasingQuality 2','sg.ShadowQuality 2','sg.GlobalIlluminationQuality 2','sg.ReflectionQuality 2','sg.PostProcessQuality 2','sg.TextureQuality 2','sg.EffectsQuality 2','sg.FoliageQuality 2','r.ScreenPercentage 100','r.MotionBlurQuality 0','r.DepthOfFieldQuality 0','r.Streaming.FullyLoadUsedTextures 1','DisableAllScreenMessages']:u.SystemLibrary.execute_console_command(world,cmd)
cap=editor.spawn_actor_from_class(u.SceneCapture2D,u.Vector(*views[0]['location']));comp=cap.capture_component2d
rt=u.RenderingLibrary.create_render_target2d(world,1920,1080,u.TextureRenderTargetFormat.RTF_RGBA8);comp.texture_target=rt;comp.capture_source=u.SceneCaptureSource.SCS_FINAL_COLOR_LDR;comp.capture_every_frame=True;comp.capture_on_movement=False;comp.always_persist_rendering_state=True;comp.auto_calculate_ortho_planes=False;comp.post_process_blend_weight=1.
pp=comp.post_process_settings
for k,v in {'override_auto_exposure_method':True,'auto_exposure_method':u.AutoExposureMethod.AEM_MANUAL,'override_auto_exposure_bias':True,'auto_exposure_bias':0.,'override_auto_exposure_apply_physical_camera_exposure':True,'auto_exposure_apply_physical_camera_exposure':False,'override_motion_blur_amount':True,'motion_blur_amount':0.}.items():pp.set_editor_property(k,v)
comp.post_process_settings=pp
manifest={k:v for k,v in original.items() if k not in ['captures','capture_started_at_utc','capture_finished_at_utc']};manifest.update(captures=[],comparison_reference='FirstDelivery/Screenshots/capture_manifest.json',settings_identical_to_first_delivery=True,pass_name='TexturePass',exposure='Manual; bias 0; physical camera exposure disabled',camera_and_geometry_changes=False)
state={'phase':'warmup','since':time.monotonic(),'i':0}
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def configure(v):
    rot=v['rotation'];cap.set_actor_location_and_rotation(u.Vector(*v['location']),u.Rotator(pitch=rot[0],yaw=rot[1],roll=rot[2]),False,True)
    comp.projection_type=u.CameraProjectionMode.ORTHOGRAPHIC if v['projection']=='orthographic' else u.CameraProjectionMode.PERSPECTIVE;comp.ortho_width=v.get('ortho_width_cm',20000);comp.fov_angle=v.get('horizontal_fov',70);comp.capture_scene()
def tick(dt):
    try:
        now=time.monotonic()
        if state['phase']=='warmup' and now-state['since']>40:manifest['capture_started_at_utc']=stamp();configure(views[0]);state.update(phase='capture',since=now)
        elif state['phase']=='capture' and now-state['since']>12:
            v=views[state['i']];u.RenderingLibrary.export_render_target(world,rt,str(OUT),v['name']+'.png');v['captured_at_utc']=stamp();manifest['captures'].append(v.copy())
            (OUT/'capture_manifest.json').write_text(json.dumps(manifest,indent=2));state['i']+=1
            if state['i']==4:
                manifest['capture_finished_at_utc']=stamp();(OUT/'capture_manifest.json').write_text(json.dumps(manifest,indent=2));u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
            else:configure(views[state['i']]);state['since']=now
    except Exception:(R/'capture_error.json').write_text(json.dumps({'error':traceback.format_exc()},indent=2));u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
