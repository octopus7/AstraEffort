import unreal as u, runpy, json, datetime
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra')
ns=runpy.run_path(str(ROOT/'build_level.py'),init_globals={'SKIP_BUILD':True})
for name,color in ns['DATA']['palette'].items():ns['create_mat'](name,color)
ns['create_mat']('Terrain',ns['DATA']['palette']['Grass'])
for name,meta in ns['DATA']['assets'].items():
 if meta['collision']=='simple' and not name.startswith(('SM_Broadleaf','SM_Pine')):
  mesh=ns['eas'].load_asset('/Game/Forest/ultra/Meshes/'+name)
  ns['meshed'].remove_collisions(mesh)
  ns['meshed'].add_simple_collisions(mesh,u.ScriptingCollisionShapeType.NDOP26)
  ns['eas'].save_loaded_asset(mesh)
levels=u.get_editor_subsystem(u.LevelEditorSubsystem);levels.load_level('/Game/Maps/ultra')
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
eas=u.get_editor_subsystem(u.EditorAssetSubsystem)
for a in actors.get_all_level_actors():
 if isinstance(a,u.PostProcessVolume):
  settings=a.get_editor_property('settings')
  settings.set_editor_property('auto_exposure_bias',.65)
  settings.set_editor_property('override_dynamic_global_illumination_method',True)
  settings.set_editor_property('dynamic_global_illumination_method',u.DynamicGlobalIlluminationMethod.NONE)
  settings.set_editor_property('override_ambient_cubemap_intensity',True)
  settings.set_editor_property('ambient_cubemap_intensity',.35)
  settings.set_editor_property('ambient_cubemap',eas.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap'))
  a.set_editor_property('settings',settings)
 if isinstance(a,u.SkyAtmosphere):
  a.get_component_by_class(u.SkyAtmosphereComponent).set_editor_property('sky_luminance_factor',u.LinearColor(20,20,20,1))
 # Keep all physical set-dressing inside the designated square.
 if isinstance(a,u.StaticMeshActor):
  origin,extent=a.get_actor_bounds(False)
  dx=max(0,-5000-(origin.x-extent.x))-max(0,(origin.x+extent.x)-5000)
  dy=max(0,-5000-(origin.y-extent.y))-max(0,(origin.y+extent.y)-5000)
  if abs(dx)>.1 or abs(dy)>.1:
   loc=a.get_actor_location();a.set_actor_location(u.Vector(loc.x+dx,loc.y+dy,loc.z),False,True)
levels.save_current_level();eas.save_directory('/Game/Forest/ultra',only_if_is_dirty=True,recursive=True)
(ROOT/'scene_ready_time.json').write_text(json.dumps({'scene_saved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'changes':'Corrected water graph input names; ambient fill/exposure/sky; site-bound set dressing.'},indent=2))
runpy.run_path(str(ROOT/'review_pipeline.py'))
