import unreal as u, json, datetime
from pathlib import Path
R=Path('D:/github/AstraEffort/ForestDemo/Work/high')
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
record={'requested_path_change_recorded_at_utc':'2026-10-21T12:21:03+00:00','migration_started_at_utc':now(),'method':'Unreal EditorAssetLibrary.rename_directory; save direct references; delete redirector-only old directory','regenerated_art':False}
E=u.EditorAssetLibrary;ls=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert ls.load_level('/Game/Maps/high')
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
for actor in actors:
 if isinstance(actor,u.DirectionalLight):
  actor.light_component.set_editor_property('intensity',50000.0)
  actor.light_component.set_editor_property('atmosphere_sun_light',True)
record['landmark_bounds']={}
for actor in actors:
 if actor.get_actor_label() in ['Lake','Sea','Terrain']:
  origin,extent=actor.get_actor_bounds(False)
  record['landmark_bounds'][actor.get_actor_label()]={'origin':[origin.x,origin.y,origin.z],'extent':[extent.x,extent.y,extent.z]}
assert E.rename_directory('/Game/high','/Game/Forest/high')
E.save_directory('/Game/Forest/high',only_if_is_dirty=False,recursive=True);assert ls.save_current_level()
reg=u.AssetRegistryHelpers.get_asset_registry();reg.scan_paths_synchronous(['/Game/Forest/high','/Game/Maps'],True)
opts=u.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True)
packages=['/Game/Maps/high']+[str(a.package_name) for a in reg.get_assets_by_path('/Game/Forest/high',recursive=True)]
bad=[]
for p in packages:
 for d in reg.get_dependencies(p,opts):
  if str(d).startswith('/Game/high/'):bad.append([p,str(d)])
assert not bad,str(bad)
old=reg.get_assets_by_path('/Game/high',recursive=True)
for a in old:assert str(a.asset_class_path.asset_name)=='ObjectRedirector',str(a)
if E.does_directory_exist('/Game/high'):assert E.delete_directory('/Game/high')
record['migration_finished_at_utc']=now();record['new_asset_count']=len(packages)-1;record['old_root_dependencies']=bad
(R/'migration.json').write_text(json.dumps(record,indent=2));u.log('HIGH_MIGRATION_COMPLETE')
