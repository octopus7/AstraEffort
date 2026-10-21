import unreal as u,json,datetime,traceback,hashlib
from pathlib import Path
OUT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement');MAP=Path(r'D:/github/AstraEffort/ForestDemo/Saved/Workers/ultra/SelfImprovement/ForestDemo/Content/Maps/ultra.umap')
report={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selected_palette':'moss','selection_reason':'Compared both actual tree_detail and overview renders. Moss reduces lime highlights and canopy contrast while harmonizing with teal pines; wind/card/density/geometry algorithms remain intact.','map_sha256_before':hashlib.sha256(MAP.read_bytes()).hexdigest()}
try:
 levels=u.get_editor_subsystem(u.LevelEditorSubsystem);assert levels.load_level('/Game/Maps/ultra')
 actors=u.get_editor_subsystem(u.EditorActorSubsystem);trees=[a for a in actors.get_all_level_actors() if isinstance(a,u.ForestUltraAnimeTreeActor)];assert len(trees)==63
 settings=json.loads((OUT/'palette_candidates.json').read_text())['moss'];report['settings']=settings
 for a in trees:
  for key,value in settings.items():a.set_editor_property(key,u.LinearColor(*value) if isinstance(value,list) else value)
  a.refresh_tree()
 assert levels.save_current_level();report['tree_count']=len(trees);report['map_sha256_after']=hashlib.sha256(MAP.read_bytes()).hexdigest();report['success']=True
except Exception:report['success']=False;report['error']=traceback.format_exc()
finally:
 report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(OUT/'palette_application.json').write_text(json.dumps(report,indent=2));u.log('ULTRA_PALETTE_SAVED '+str(report['success']));u.SystemLibrary.quit_editor()
