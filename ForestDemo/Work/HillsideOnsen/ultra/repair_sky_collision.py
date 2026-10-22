"""Persist an explicitly nonblocking sky after the first actual Character probe."""
import unreal as u,json,traceback
from pathlib import Path
from datetime import datetime,timezone
W=Path('D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra')
try:
    assert '/Saved/Workers/HillsideOnsen/ultra/' in u.Paths.get_project_file_path().replace('\\','/')
    assert u.EditorLevelLibrary.load_level('/Game/Maps/HillsideOnsen_ultra')
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    dome=next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='Muted sky backdrop')
    c=dome.static_mesh_component
    def state():return {'actor_collision':dome.get_actor_enable_collision(),'component_collision':str(c.get_collision_enabled()),'profile':str(c.get_collision_profile_name())}
    report={'utc':datetime.now(timezone.utc).isoformat(),'before':state(),'actor':dome.get_path_name()}
    c.set_collision_profile_name('NoCollision');c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);dome.set_actor_enable_collision(False)
    report['after']=state()
    assert u.EditorLoadingAndSavingUtils.save_map(world,'/Game/Maps/HillsideOnsen_ultra')
    report['saved']=True
    (W/'Validation/sky_collision_repair.json').write_text(json.dumps(report,indent=2))
except Exception:
    (W/'Validation/sky_collision_repair_error.json').write_text(traceback.format_exc())
u.SystemLibrary.quit_editor()
