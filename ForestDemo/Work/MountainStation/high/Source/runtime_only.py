import unreal as u,traceback
ROOT='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high'
RUNTIME_ONLY=True
try:
 u.EditorPythonScripting.set_keep_python_script_alive(True)
 u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Maps/MountainStation_high')
 exec(compile(open(ROOT+'/Source/runtime_unreal.py').read(),ROOT+'/Source/runtime_unreal.py','exec'),globals())
except Exception:
 open(ROOT+'/runtime_only_error.txt','w').write(traceback.format_exc());u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
