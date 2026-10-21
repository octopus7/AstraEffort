import unreal as u, json, datetime
PW='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium'
PL=u.get_editor_subsystem(u.LevelEditorSubsystem)
PL.load_level('/Game/Maps/MountainStation_medium')
PE=u.get_editor_subsystem(u.EditorActorSubsystem)
for a in PE.get_all_level_actors():
 if isinstance(a,u.DirectionalLight): a.set_actor_rotation(u.Rotator(pitch=-48,yaw=40,roll=0),False)
 if isinstance(a,u.SkyLight):
  a.light_component.set_editor_property('intensity',2.5)
  a.light_component.set_editor_property('lower_hemisphere_is_black',False)
  a.light_component.recapture_sky()
PL.save_current_level(); PL.load_level('/Game/Maps/MountainStation_medium')
v=json.load(open(PW+'/validation.json')); v['lighting_polish_saved_and_reloaded_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat(); v['lighting_polish']='Sun yaw 40; skylight intensity 2.5, lower hemisphere enabled; geometry unchanged after successful collision rebuild'; json.dump(v,open(PW+'/validation.json','w'),indent=2)
SKIP_RUNTIME=True
exec(compile(open(PW+'/capture_ue.py',encoding='utf-8').read(),PW+'/capture_ue.py','exec'),globals())
