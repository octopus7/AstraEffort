import unreal as u,json,time,datetime,traceback,runpy
from pathlib import Path
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/TexturePass');(R/'Runtime').mkdir(exist_ok=True)
u.EditorPythonScripting.set_keep_python_script_alive(True)
levels=u.get_editor_subsystem(u.LevelEditorSubsystem);assert levels.load_level('/Game/Maps/MountainStation_ultra')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
state={'phase':'initialize','since':time.monotonic()};runtime=None
def tick(dt):
    global runtime
    try:
        now=time.monotonic()
        if state['phase']=='initialize' and now-state['since']>10:
            runpy.run_path(str(R/'validate_packages.py'),init_globals={'VALIDATE_RELOAD':False})
            runpy.run_path(str(R/'validate_uv_ue.py'))['validate_uv']()
            runtime=runpy.run_path(str(R/'runtime_helpers.py'),init_globals={'OUT':R/'Runtime','terrain_samples':[],'result':{'started_at_utc':utc(),'tests':[],'passed':False}})
            runtime['inspect_terrain']();levels.editor_request_begin_play();state.update(phase='play',since=time.monotonic())
        elif state['phase']=='play' and now-state['since']>3:
            worlds=u.EditorLevelLibrary.get_pie_worlds(False);assert len(worlds)==1
            scope={'__name__':'__main__'};exec(compile((R/'native_and_ramp_checks.py').read_text(),str(R/'native_and_ramp_checks.py'),'exec'),scope)
            native=scope['runtime_checks'](worlds[0]);(R/'Runtime/native_and_ramp.json').write_text(json.dumps(native,indent=2));assert native['passed']
            runtime['play_checks']();runtime['save']();levels.editor_request_end_play();state.update(phase='ended',since=time.monotonic())
        elif state['phase']=='ended' and now-state['since']>5:
            result=runtime['result'];result.update(normal_shutdown=not levels.is_in_play_in_editor(),finished_at_utc=utc());result['passed']=result.get('checks_passed',False) and result['normal_shutdown'];runtime['save']();assert result['passed']
            u.unregister_slate_post_tick_callback(handle);runpy.run_path(str(R/'capture_texture.py'))
    except Exception:
        (R/'review_error.json').write_text(json.dumps({'utc':utc(),'error':traceback.format_exc()},indent=2));u.log_error(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
