import unreal as u,json,datetime,traceback
from pathlib import Path
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement')
try:
    level=u.get_editor_subsystem(u.LevelEditorSubsystem);assert level.load_level('/Game/Maps/MountainStation_ultra');changes=[]
    target={'Tunnel entrance fill':35.,'Tunnel inner fill':25.}
    for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        label=actor.get_actor_label()
        if label in target:
            c=actor.light_component;changes.append({'label':label,'before_lumens':c.intensity,'after_lumens':target[label]});c.set_intensity(target[label])
    assert len(changes)==2;assert level.save_current_level()
    (R/'lighting_revision.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'Actual same-camera tracks render showed overbright tunnel fill; reduce intensity while preserving camera exposure.','changes':changes,'saved':True},indent=2))
    build=json.loads((R/'build_evidence.json').read_text())
    for row in build['added_lights']:row['intensity_lumens']=target[row['label']]
    build['lighting_revision_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(R/'build_evidence.json').write_text(json.dumps(build,indent=2))
except Exception:(R/'light_tune_error.json').write_text(traceback.format_exc())
u.SystemLibrary.quit_editor()
