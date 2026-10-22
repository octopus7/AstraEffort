import datetime, json, hashlib, shutil, ast
from pathlib import Path
R=Path(__file__).resolve().parent
P=R.parents[3]/'Saved/Workers/MountainStation/ultra/Project'
now=datetime.datetime.now(datetime.timezone.utc)
status=json.loads((R/'STATUS.json').read_text())
assert status['stopped_by_user']
archive=R/'ResumeRecords';archive.mkdir(exist_ok=True)
for name in ['STATUS.json','RESULT.md']:shutil.copy2(R/name,archive/('at_stop_'+name))
checkpoint=json.loads((R/'Checkpoint/manifest.json').read_text())
assert all(hashlib.sha256((P/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in checkpoint['files'])
status.update(status='working',stopped_by_user=False,resumed_at_utc=now.isoformat(),resumed_at_kst=now.astimezone(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),paused_seconds=(now-datetime.datetime.fromisoformat(status['finished_at_utc'])).total_seconds(),stopped_at_utc=status['finished_at_utc'],elapsed_before_pause_seconds=status['elapsed_seconds'],finished_at_utc=None,finished_at_kst=None,validation='Resumed by explicit user request; all 137 private packages match the preserved checkpoint. Final UE review pending.',blockers=[])
(R/'STATUS.json').write_text(json.dumps(status,indent=2))
# Put initialization under the same failure cleanup contract as callbacks.
for name,prefix in [('review_unreal.py','review'),('capture_views.py','capture_initialization')]:
    p=R/name;s=p.read_text();assert not s.startswith('# guarded initialization')
    s=s.replace('u.EditorPythonScripting.set_keep_python_script_alive(True);','').replace('u.EditorPythonScripting.set_keep_python_script_alive(True)\n','')
    s=s.replace('handle=u.register_slate_post_tick_callback(tick)','handle=u.register_slate_post_tick_callback(tick)\nu.EditorPythonScripting.set_keep_python_script_alive(True)')
    s='# guarded initialization\nhandle=None\ntry:\n'+''.join('    '+line+'\n' for line in s.splitlines())+f'''except Exception:
    import unreal as u,traceback,json,datetime
    from pathlib import Path
    Path(r'{R.as_posix()}/{prefix}_error.json').write_text(json.dumps({{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'error':traceback.format_exc()}},indent=2))
    u.log_error(traceback.format_exc())
    if handle is not None:u.unregister_slate_post_tick_callback(handle)
    u.SystemLibrary.quit_editor()
'''
    ast.parse(s);p.write_text(s)
print(json.dumps({'resumed_at_utc':status['resumed_at_utc'],'paused_seconds':status['paused_seconds'],'checkpoint_packages_verified':len(checkpoint['files'])}))
