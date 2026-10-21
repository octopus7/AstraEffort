import unreal as u,traceback,json
ROOT='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high'
try:
 u.EditorPythonScripting.set_keep_python_script_alive(True)
 level=u.get_editor_subsystem(u.LevelEditorSubsystem);level.load_level('/Game/Maps/MountainStation_high')
 for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
  if a.get_actor_label() in ['Quiet blue backdrop','PresentationGround']:
   a.static_mesh_component.set_collision_profile_name('NoCollision')
   a.set_actor_enable_collision(False)
   a.modify()
  if isinstance(a,u.SkyLight):
   a.light_component.set_editor_property('source_type',u.SkyLightSourceType.SLS_CAPTURED_SCENE)
   a.light_component.set_editor_property('sky_distance_threshold',10000.0)
   a.light_component.set_editor_property('intensity',1.0)
   a.light_component.recapture_sky();a.modify()
 data=json.load(open(ROOT+'/build_evidence.json'));c=data['cameras']['platform'];c['location']=[1550,220,275];c['target']=[-850,-180,260]
 rot=u.MathLibrary.find_look_at_rotation(u.Vector(*c['location']),u.Vector(*c['target']));c['rotation']=[rot.pitch,rot.yaw,rot.roll]
 for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
  if a.get_actor_label()=='Camera_platform':a.set_actor_location(u.Vector(*c['location']),False,True);a.set_actor_rotation(rot,False)
 level.save_current_level();json.dump(data,open(ROOT+'/build_evidence.json','w'),indent=2)
 exec(compile(open(ROOT+'/Source/validate_unreal.py').read(),ROOT+'/Source/validate_unreal.py','exec'),globals())
 exec(compile(open(ROOT+'/Source/runtime_unreal.py').read(),ROOT+'/Source/runtime_unreal.py','exec'),globals())
except Exception:
 open(ROOT+'/final_fix_error.txt','w').write(traceback.format_exc());u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
