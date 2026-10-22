"""Small final read-only audit of saved lighting and package publication invariants."""
import unreal as u,json,hashlib,traceback
from pathlib import Path
from datetime import datetime,timezone
W=Path('D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra')
P=Path('D:/github/AstraEffort/ForestDemo/Saved/Workers/HillsideOnsen/ultra/Project')
report={'started_at_utc':datetime.now(timezone.utc).isoformat(),'passed':False,'read_only':True}
try:
    assert '/Saved/Workers/HillsideOnsen/ultra/' in u.Paths.get_project_file_path().replace('\\','/')
    assert u.EditorLevelLibrary.load_level('/Game/Maps/HillsideOnsen_ultra')
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    actors=u.GameplayStatics.get_all_actors_of_class(world,u.Actor)
    lights=[]
    for a in actors:
        for c in a.get_components_by_class(u.LightComponentBase):
            lights.append({'actor':a.get_actor_label(),'component':c.get_path_name(),'mobility':str(c.get_editor_property('mobility')),'movable':c.get_editor_property('mobility')==u.ComponentMobility.MOVABLE})
    assert lights and all(x['movable'] for x in lights),lights
    report['lights']=lights
    owned=list((P/'Content/HillsideOnsen/ultra').rglob('*.uasset'))
    adjacent=list((P/'Content/Maps').glob('HillsideOnsen_ultra*'))
    forbidden=[str(p) for p in owned+adjacent if 'BuiltData' in p.name or '__External' in str(p)]
    assert not forbidden,forbidden
    report['no_builtdata_or_external_packages']=True
    packages=json.loads((W/'Validation/validated_packages.json').read_text())
    def unchanged():return all(hashlib.sha256((P/e['path']).read_bytes()).hexdigest()==e['sha256'] for e in packages['files'])
    assert unchanged()
    report['validated_packages_digest']=packages['digest'];report['package_hashes_unchanged']=True
    report['passed']=True
except Exception:report['exception']=traceback.format_exc()
report['finished_at_utc']=datetime.now(timezone.utc).isoformat()
(W/'Validation/final_map_checks.json').write_text(json.dumps(report,indent=2))
u.SystemLibrary.quit_editor()
