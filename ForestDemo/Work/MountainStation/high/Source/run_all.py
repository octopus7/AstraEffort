import unreal as u,traceback
ROOT='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high'
try:
 u.EditorPythonScripting.set_keep_python_script_alive(True)
 world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
 u.SystemLibrary.execute_console_command(world,'Interchange.FeatureFlags.Import.FBX 0')
 exec(compile(open(ROOT+'/Source/build_unreal.py').read(),ROOT+'/Source/build_unreal.py','exec'),globals())
 exec(compile(open(ROOT+'/Source/runtime_unreal.py').read(),ROOT+'/Source/runtime_unreal.py','exec'),globals())
except Exception:
 open(ROOT+'/pipeline_error.txt','w').write(traceback.format_exc())
 u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
