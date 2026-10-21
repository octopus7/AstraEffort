import unreal as u,json,datetime,traceback
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/TexturePass'
r={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fresh_process':True,'read_only':True}
try:
 assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Maps/MountainStation_medium')
 world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
 settings=world.get_world_settings()
 partition=settings.get_editor_property('world_partition')
 r['world_path']=world.get_path_name();r['settings_path']=settings.get_path_name();r['partition_is_none']=partition is None;r['partition_value']=str(partition)
 r['passed']=r['world_path']=='/Game/Maps/MountainStation_medium.MountainStation_medium' and partition is None
except Exception:
 r['passed']=False;r['error']=traceback.format_exc()
finally:
 r['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 json.dump(r,open(W+'/world_partition_validation.json','w'),indent=2)
 u.SystemLibrary.quit_editor()
