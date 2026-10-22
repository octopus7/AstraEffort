# guarded initialization
handle=None
try:
    import unreal as u,json,time,datetime,traceback,runpy
    from pathlib import Path
    R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement');(R/'Runtime').mkdir(exist_ok=True)
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem);assert levels.load_level('/Game/Maps/MountainStation_ultra')
    package=runpy.run_path(str(R/'package_state.py'));package['snapshot']();package['baseline_check']();package['validate_allocations']()
    state={'phase':'initialize','since':time.monotonic()};runtime=None;improvement=None
    def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
    def tick(dt):
        global runtime,improvement
        try:
            if state['phase']=='initialize' and time.monotonic()-state['since']>10:
                runpy.run_path(str(R/'validate_packages.py'),init_globals={'VALIDATE_RELOAD':False})
                runpy.run_path(str(R/'validate_uv_ue.py'))['validate_uv']()
                improvement=runpy.run_path(str(R/'improvement_checks.py'));improvement['editor_checks']()
                package['confirm']()
                runtime=runpy.run_path(str(R/'runtime_helpers.py'),init_globals={'OUT':R/'Runtime','terrain_samples':[],'result':{'started_at_utc':stamp(),'tests':[],'passed':False}});runtime['inspect_terrain']();levels.editor_request_begin_play();state.update(phase='play',since=time.monotonic())
            elif state['phase']=='play' and time.monotonic()-state['since']>3:
                pw=u.EditorLevelLibrary.get_pie_worlds(False)[0];scope={'__name__':'__main__'};exec(compile((R/'native_and_ramp_checks.py').read_text(),str(R/'native_and_ramp_checks.py'),'exec'),scope)
                native=scope['runtime_checks'](pw);(R/'Runtime/native_and_ramp.json').write_text(json.dumps(native,indent=2));assert native['passed']
                runtime['play_checks']();runtime['save']();assert runtime['result']['checks_passed'];improvement['runtime_routes'](pw)
                levels.editor_request_end_play();state.update(phase='ended',since=time.monotonic())
            elif state['phase']=='ended' and time.monotonic()-state['since']>5:
                runtime['result'].update(normal_shutdown=not levels.is_in_play_in_editor(),finished_at_utc=stamp());runtime['result']['passed']=runtime['result']['checks_passed'] and runtime['result']['normal_shutdown'];runtime['save']();assert runtime['result']['passed']
                record=package['confirm']();record.update(validated=True,validated_at_utc=stamp());(R/'validated_packages.json').write_text(json.dumps(record,indent=2));package['baseline_check']()
                u.unregister_slate_post_tick_callback(handle);runpy.run_path(str(R/'capture_views.py'),init_globals={'CAPTURE_PHASE':'after_final'})
        except Exception:
            (R/'review_error.json').write_text(json.dumps({'utc':stamp(),'error':traceback.format_exc()},indent=2));u.log_error(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
    handle=u.register_slate_post_tick_callback(tick)
    u.EditorPythonScripting.set_keep_python_script_alive(True)
except Exception:
    import unreal as u,traceback,json,datetime
    from pathlib import Path
    Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement/review_error.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'error':traceback.format_exc()},indent=2))
    u.log_error(traceback.format_exc())
    if handle is not None:u.unregister_slate_post_tick_callback(handle)
    u.SystemLibrary.quit_editor()
