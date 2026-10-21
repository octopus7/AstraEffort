import unreal as u,json,datetime
from pathlib import Path
R=Path('D:/github/AstraEffort/ForestDemo/Work/high')
ls=u.get_editor_subsystem(u.LevelEditorSubsystem);a=u.get_editor_subsystem(u.EditorActorSubsystem)
assert ls.load_level('/Game/Maps/high');world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
manifest=json.loads((R/'scene.json').read_text())
placements={(v['mesh'],round(v['location'][0],2),round(v['location'][1],2),round(v['location'][2],2)):v for v in manifest['actors']}
for actor in a.get_all_level_actors():
 if isinstance(actor,u.StaticMeshActor):
  s=actor.get_actor_scale3d();actor.set_actor_scale3d(u.Vector(s.x,-abs(s.y),s.z))
  p=actor.get_actor_location();key=(actor.static_mesh_component.static_mesh.get_name(),round(p.x,2),round(p.y,2),round(p.z,2))
  actor.set_actor_rotation(u.Rotator(pitch=0,yaw=placements[key]['yaw'],roll=0),False)
 if isinstance(actor,u.DirectionalLight) and actor.get_actor_label()=='Late afternoon sun':
  actor.set_actor_rotation(u.Rotator(pitch=-42,yaw=-35,roll=0),False)
  actor.light_component.set_editor_property('intensity',20000)
  actor.light_component.set_editor_property('atmosphere_sun_light',True)
 if isinstance(actor,u.PostProcessVolume):
  settings=actor.get_editor_property('settings');settings.set_editor_property('auto_exposure_bias',-1.0);actor.set_editor_property('settings',settings)
 if isinstance(actor,u.SkyLight):
  sc=actor.light_component;sc.set_editor_property('real_time_capture',False);sc.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
  sc.set_editor_property('cubemap',u.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap.DaylightAmbientCubemap'))
  sc.set_editor_property('intensity',1000.0)
 if isinstance(actor,u.PlayerStart):actor.set_actor_rotation(u.Rotator(pitch=0,yaw=85,roll=0),False)
for label,pitch,yaw,intensity in [('Soft woodland fill',-25,145,4800),('Soft side fill',-50,65,2300)]:
 old=next((v for v in a.get_all_level_actors() if v.get_actor_label()==label),None)
 light=old or a.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,6500),u.Rotator(pitch=pitch,yaw=yaw,roll=0))
 light.set_actor_label(label);lc=light.light_component
 lc.set_editor_property('mobility',u.ComponentMobility.MOVABLE);lc.set_editor_property('intensity',intensity);lc.set_editor_property('cast_shadows',False);lc.set_editor_property('atmosphere_sun_light',False)
assert ls.save_current_level()
evidence={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'coordinate_correction':'FBX handedness mirrors local Y; set negative local Y scale on authored StaticMeshActors, preserving intended world placement','bounds':{},'traces':{}}
for actor in a.get_all_level_actors():
 if actor.get_actor_label() in ['Lake','Sea','Terrain']:
  p,e=actor.get_actor_bounds(False);evidence['bounds'][actor.get_actor_label()]={'origin':[p.x,p.y,p.z],'extent':[e.x,e.y,e.z]}
for name,x,y in [('PlayerStart',650,-1900),('LakeBed',-1700,700),('Beach',1800,-2580),('LakeCamera',50,-450)]:
 hit=u.SystemLibrary.line_trace_single(world,u.Vector(x,y,2500),u.Vector(x,y,-900),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],u.DrawDebugTrace.NONE,True)
 evidence['traces'][name]=str(hit)
(R/'geometry_checks.json').write_text(json.dumps(evidence,indent=2));u.log('HIGH_FINALIZE_COMPLETE')
