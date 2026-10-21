import unreal,traceback
try:
 unreal.EditorPythonScripting.set_keep_python_script_alive(True)
 globals()['XHIGH_BUILD_KEEP']=True
 exec(compile(open('D:/github/AstraEffort/ForestDemo/Work/xhigh/build_scene.py').read(),'build_scene.py','exec'),globals())
 exec(compile(open('D:/github/AstraEffort/ForestDemo/Work/xhigh/capture_entry.py').read(),'capture_entry.py','exec'),globals())
except Exception:
 open('D:/github/AstraEffort/ForestDemo/Work/xhigh/rebuild_error.txt','w').write(traceback.format_exc())
 unreal.log_error(traceback.format_exc());unreal.SystemLibrary.quit_editor()
