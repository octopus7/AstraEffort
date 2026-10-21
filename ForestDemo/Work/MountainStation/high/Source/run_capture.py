import unreal as u,traceback
ROOT='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high'
try:
 u.EditorPythonScripting.set_keep_python_script_alive(True)
 exec(compile(open(ROOT+'/Source/capture_unreal.py').read(),ROOT+'/Source/capture_unreal.py','exec'),globals())
except Exception:
 open(ROOT+'/capture_error.txt','w').write(traceback.format_exc())
 u.SystemLibrary.quit_editor()
