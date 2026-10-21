import unreal as u,traceback
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high/TexturePass'
try:
 u.EditorPythonScripting.set_keep_python_script_alive(True)
 exec(compile(open(W+'/Source/validate_unreal.py').read(),W+'/Source/validate_unreal.py','exec'),globals())
 exec(compile(open(W+'/Source/runtime_unreal.py').read(),W+'/Source/runtime_unreal.py','exec'),globals())
except Exception:
 open(W+'/verify_error.txt','w').write(traceback.format_exc());u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
