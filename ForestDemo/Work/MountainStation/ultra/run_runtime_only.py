"""Run final PIE checks on the saved map without changing or recapturing it."""
import unreal as u,json,datetime,time,traceback,hashlib
ROOT=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra'
MAP_FILE=r'D:/github/AstraEffort/ForestDemo/Saved/Workers/MountainStation/ultra/Project/Content/Maps/MountainStation_ultra.umap'
def map_hash():return hashlib.sha256(open(MAP_FILE,'rb').read()).hexdigest()
u.EditorPythonScripting.set_keep_python_script_alive(True)
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert levels.load_level('/Game/Maps/MountainStation_ultra')
exec(compile(open(ROOT+'/runtime_checks.py').read(),ROOT+'/runtime_checks.py','exec'),globals())
state={'phase':'warmup','since':time.monotonic(),'start':time.monotonic()}
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save():
    with open(ROOT+'/runtime_validation.json','w') as f:json.dump(state['result'],f,indent=2)
def tick(dt):
    try:
        now=time.monotonic()
        if now-state['start']>120:raise RuntimeError('Runtime-only check timed out')
        if state['phase']=='warmup' and now-state['since']>10:
            state['result']={'started_at_utc':utc(),'mode':'Actual PIE game world; runtime-only final supplement; saved map unchanged','map_sha256_before':map_hash()}
            levels.editor_request_begin_play();state.update(phase='play',since=now)
        elif state['phase']=='play' and now-state['since']>3:
            worlds=u.EditorLevelLibrary.get_pie_worlds(False)
            state['result'].update(pie_world_count=len(worlds),worlds=[runtime_checks(pw) for pw in worlds],hello_evidence='Native BeginPlay lifecycle dispatch probe and unchanged baseline implementation; no claim of visible Hello pixels in comparison captures.')
            save();levels.editor_request_end_play();state.update(phase='end',since=now)
        elif state['phase']=='end' and now-state['since']>5:
            state['result'].update(normal_shutdown=not levels.is_in_play_in_editor(),finished_at_utc=utc(),map_sha256_after=map_hash())
            save();u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
    except Exception:
        state.setdefault('result',{}).update(error=traceback.format_exc(),finished_at_utc=utc(),normal_shutdown=False)
        save();u.log_error(state['result']['error']);u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
