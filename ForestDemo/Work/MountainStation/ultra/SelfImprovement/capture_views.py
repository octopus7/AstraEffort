import unreal as u,json,time,datetime,hashlib,struct,traceback
from pathlib import Path
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement')
phase=globals().get('CAPTURE_PHASE','before_fixed');OUT=R/'Screenshots'/phase
OUT.mkdir(parents=True,exist_ok=True)
assert not list(OUT.glob('*.png')),'Capture destination must be fresh'
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
u.EditorPythonScripting.set_keep_python_script_alive(True)
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
if phase.startswith('before'):assert levels.load_level('/Game/Maps/MountainStation_ultra')
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();editor=u.get_editor_subsystem(u.EditorActorSubsystem)
original=json.loads((R.parent/'TexturePass/Screenshots/capture_manifest.json').read_text())
views=[{k:v for k,v in row.items() if k!='captured_at_utc'} for row in original['captures']]
for name,pos,at in [('path_junction',[-3650,250,1000],[-3090,920,320]),('crossing',[-3910,-430,640],[-3310,200,135])]:
    rot=u.MathLibrary.find_look_at_rotation(u.Vector(*pos),u.Vector(*at))
    views.append({'name':name,'location':pos,'rotation':[rot.pitch,rot.yaw,rot.roll],'projection':'perspective','horizontal_fov':62})
settings={f'sg.{n}Quality':2 for n in ['ViewDistance','AntiAliasing','Shadow','GlobalIllumination','Reflection','PostProcess','Texture','Effects','Foliage']}
settings.update({'r.ScreenPercentage':100,'r.MotionBlurQuality':0,'r.DepthOfFieldQuality':0,'r.Streaming.FullyLoadUsedTextures':1})
for name,value in settings.items():u.SystemLibrary.execute_console_command(world,name+' '+str(value))
u.SystemLibrary.execute_console_command(world,'DisableAllScreenMessages')
actual={name:u.SystemLibrary.get_console_variable_float_value(name) for name in settings}
assert all(abs(actual[k]-v)<.01 for k,v in settings.items())
editor.clear_actor_selection_set();cap=editor.spawn_actor_from_class(u.SceneCapture2D,u.Vector(*views[0]['location']));comp=cap.capture_component2d
rt=u.RenderingLibrary.create_render_target2d(world,1920,1080,u.TextureRenderTargetFormat.RTF_RGBA8);comp.texture_target=rt;comp.capture_source=u.SceneCaptureSource.SCS_FINAL_COLOR_LDR;comp.capture_every_frame=True;comp.capture_on_movement=False;comp.always_persist_rendering_state=True;comp.auto_calculate_ortho_planes=False;comp.post_process_blend_weight=1.
pp=comp.post_process_settings
for k,v in {'override_auto_exposure_method':True,'auto_exposure_method':u.AutoExposureMethod.AEM_MANUAL,'override_auto_exposure_bias':True,'auto_exposure_bias':0.,'override_auto_exposure_apply_physical_camera_exposure':True,'auto_exposure_apply_physical_camera_exposure':False,'override_motion_blur_amount':True,'motion_blur_amount':0.}.items():pp.set_editor_property(k,v)
comp.post_process_settings=pp
manifest={'phase':phase,'map':world.get_path_name(),'started_at_utc':stamp(),'actual_cvars':actual,'resolution':[1920,1080],'exposure':'Manual bias0 physical exposure disabled','capture_source':str(comp.capture_source),'captures':[],'baseline_commit':'3e13e569b0e8725f4a9faaeee8e3d13ddf7b5737','common_camera_reference':'TexturePass/Screenshots/capture_manifest.json'}
if phase=='after':manifest['validated_package_manifest_sha256']=hashlib.sha256((R/'validated_packages.json').read_bytes()).hexdigest()
state={'phase':'warmup','since':time.monotonic(),'i':0}
def configure(v):
    rot=v['rotation'];cap.set_actor_location_and_rotation(u.Vector(*v['location']),u.Rotator(pitch=rot[0],yaw=rot[1],roll=rot[2]),False,True)
    comp.projection_type=u.CameraProjectionMode.ORTHOGRAPHIC if v['projection']=='orthographic' else u.CameraProjectionMode.PERSPECTIVE;comp.ortho_width=v.get('ortho_width_cm',20000);comp.fov_angle=v.get('horizontal_fov',70)
    assert (cap.get_actor_location()-u.Vector(*v['location'])).length()<.01
    comp.capture_scene()
def tick(dt):
    try:
        now=time.monotonic()
        if state['phase']=='warmup' and now-state['since']>40:configure(views[0]);state.update(phase='capture',since=now)
        elif state['phase']=='capture' and now-state['since']>12:
            v=views[state['i']];p=OUT/(v['name']+'.png');assert not p.exists()
            u.RenderingLibrary.export_render_target(world,rt,str(OUT),p.name);raw=p.read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',raw[16:24])==(1920,1080)
            manifest['captures'].append({**v,'captured_at_utc':stamp(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'actual_projection':str(comp.projection_type),'actual_fov':comp.fov_angle,'actual_ortho_width':comp.ortho_width})
            (OUT/'capture_manifest.json').write_text(json.dumps(manifest,indent=2));state['i']+=1
            if state['i']==len(views):
                manifest.update(finished_at_utc=stamp(),passed=True);(OUT/'capture_manifest.json').write_text(json.dumps(manifest,indent=2));u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
            else:configure(views[state['i']]);state['since']=now
    except Exception:
        (R/('capture_error_'+phase+'.json')).write_text(json.dumps({'utc':stamp(),'error':traceback.format_exc()},indent=2));u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
