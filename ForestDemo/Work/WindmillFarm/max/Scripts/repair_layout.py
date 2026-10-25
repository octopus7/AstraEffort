import unreal,json
from pathlib import Path
from datetime import datetime,timezone
WORK=Path(r'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/max')
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert level.load_level('/Game/Maps/WindmillFarm_max')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
evidence={'at_utc':datetime.now(timezone.utc).isoformat(),'reason':'Observed UE FBX handedness conversion flipped Y on all imported static meshes. Actor Y mirroring restores authored layout and rotor alignment.','changes':[]}
for a in actors:
    if isinstance(a,unreal.StaticMeshActor):
        before,_=a.get_actor_bounds(False)
        a.set_actor_scale3d(unreal.Vector(1,-1,1))
        after,_=a.get_actor_bounds(False)
        evidence['changes'].append({'label':a.get_actor_label(),'before_center_cm':[before.x,before.y,before.z],'after_center_cm':[after.x,after.y,after.z]})
assert level.save_current_level()
(WORK/'Evidence/layout_correction.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
unreal.log('WINDMILL_LAYOUT_CORRECTED')
