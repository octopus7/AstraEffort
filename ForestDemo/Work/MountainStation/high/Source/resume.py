import unreal as u,traceback,json
ROOT='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high'
try:
 u.EditorPythonScripting.set_keep_python_script_alive(True)
 u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Maps/MountainStation_high')
 data=json.load(open(ROOT+'/build_evidence.json'));data['cameras']['top_down']['rotation']=[-90,0,0]
 for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
  if isinstance(a,u.PlayerStart):a.set_actor_rotation(u.Rotator(pitch=0,yaw=90,roll=0),False)
  if isinstance(a,u.DirectionalLight):a.set_actor_rotation(u.Rotator(pitch=-48,yaw=-35,roll=0),False)
  if a.get_actor_label().startswith('Camera_'):
   c=data['cameras'][a.get_actor_label()[7:]];r=c['rotation'];a.set_actor_rotation(u.Rotator(pitch=r[0],yaw=r[1],roll=r[2]),False)
 u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level();json.dump(data,open(ROOT+'/build_evidence.json','w'),indent=2)
 exec(compile(open(ROOT+'/Source/validate_unreal.py').read(),ROOT+'/Source/validate_unreal.py','exec'),globals())
 exec(compile(open(ROOT+'/Source/runtime_unreal.py').read(),ROOT+'/Source/runtime_unreal.py','exec'),globals())
except Exception:
 open(ROOT+'/resume_error.txt','w').write(traceback.format_exc());u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
