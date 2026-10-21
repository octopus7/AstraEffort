import unreal,traceback
try:
 unreal.EditorPythonScripting.set_keep_python_script_alive(True)
 globals()['XHIGH_KEEP_EDITOR']=True
 exec(compile(open('D:/github/AstraEffort/ForestDemo/Work/xhigh/validate_scene.py').read(),'validate_scene.py','exec'),globals())
 exec(compile(open('D:/github/AstraEffort/ForestDemo/Work/xhigh/capture_scene.py').read(),'capture_scene.py','exec'),globals())
except Exception:
 open('D:/github/AstraEffort/ForestDemo/Work/xhigh/capture_error.txt','w').write(traceback.format_exc())
 unreal.SystemLibrary.quit_editor()
