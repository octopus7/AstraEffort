import unreal as u,json,traceback
from pathlib import Path
from datetime import datetime,timezone
W=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh/TexturePass')
d={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'map':'/Game/Maps/MountainStation_xhigh','method':'WorldSettings.get_editor_property("world_partition") after a fresh saved-map load','engine_source_evidence':'UE5.7 GameFramework/WorldSettings.h:515-516 declares VisibleAnywhere Instanced WorldPartition; Engine/Private/World.cpp:6858-6861 UWorld::GetWorldPartition delegates to WorldSettings.','direct_check_available':False}
try:
 assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(d['map'])
 world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();settings=world.get_world_settings();wp=settings.get_editor_property('world_partition')
 d.update(world=world.get_path_name(),settings=settings.get_path_name(),direct_check_available=True,world_partition_object=wp.get_path_name() if wp else None,non_world_partition=wp is None,success=wp is None)
except Exception:d.update(success=False,exception=traceback.format_exc())
(W/'Evidence/world_partition_validation.json').write_text(json.dumps(d,indent=2));print('DIRECT_NON_WP',d);u.SystemLibrary.quit_editor()
