import unreal as u,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('D:/github/AstraEffort/ForestDemo/Work/LighthouseHarbor/max')
les=u.get_editor_subsystem(u.LevelEditorSubsystem);aes=u.get_editor_subsystem(u.EditorActorSubsystem)
assert les.load_level('/Game/Maps/LighthouseHarbor_max')
stairs=[a for a in aes.get_all_level_actors() if a.get_actor_label()=='Stairs'];assert len(stairs)==1
stairs[0].set_actor_location(u.Vector(0,0,8.5),False,False)
assert abs(stairs[0].get_actor_location().z-8.5)<.001
assert les.save_current_level()
(ROOT/'Validation/final_floor_offset.json').write_text(json.dumps({'saved_at_utc':datetime.now(timezone.utc).isoformat(),
  'actor':'Stairs','actual_location_cm':[0,0,8.5],'reason':'Remove coplanar overlap of flat stair treads with terrace grass; preserves original route and fixed capture cameras.'},indent=2),encoding='utf-8')
exec(compile((ROOT/'Source/capture_unreal.py').read_text(encoding='utf-8'),'capture_unreal.py','exec'))
