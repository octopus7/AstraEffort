import unreal as u,json,datetime,traceback
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high/TexturePass';MAP='/Game/Maps/MountainStation_high'
result={'queried_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':False}
try:
 assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(MAP)
 world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();settings=world.get_world_settings();partition=settings.get_editor_property('world_partition')
 result.update(world=world.get_path_name(),settings=settings.get_path_name(),partition=partition.get_path_name() if partition else None,is_none=partition is None)
 result['passed']=partition is None and world.get_path_name()==MAP+'.MountainStation_high'
except Exception:result['error']=traceback.format_exc();u.log_error(result['error'])
finally:
 json.dump(result,open(W+'/world_partition_validation.json','w'),indent=2);u.log('TEXTUREPASS_WORLD_PARTITION '+json.dumps(result));u.SystemLibrary.quit_editor()
