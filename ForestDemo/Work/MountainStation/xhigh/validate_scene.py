import unreal as u, json, time
from pathlib import Path
from datetime import datetime, timezone
WORK=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh')
ROOT='/Game/MountainStation/xhigh';MAP='/Game/Maps/MountainStation_xhigh'
def validate():
 start=time.time();report={'started_at_utc':datetime.now(timezone.utc).isoformat(),'map':MAP,'checks':{},'errors':[]}
 assert u.EditorLevelLibrary.load_level(MAP),'Saved map reload failed'
 world=u.EditorLevelLibrary.get_editor_world();actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
 report['actors']=[{'label':a.get_actor_label(),'class':a.get_class().get_path_name(),'location':str(a.get_actor_location()),'scale':str(a.get_actor_scale3d())} for a in actors]
 report['checks']['player_start']=any(isinstance(a,u.PlayerStart) for a in actors)
 report['checks']['native_hello_actor']=any(a.get_class().get_path_name()=='/Script/ForestDemo.ScreenDebugLogger' for a in actors)
 report['checks']['dynamic_lighting']=world.get_world_settings().get_editor_property('force_no_precomputed_lighting')
 terrain=u.load_asset(ROOT+'/Meshes/SM_Terrain');bounds=terrain.get_bounds()
 report['terrain_bounds_cm']={'origin':[bounds.origin.x,bounds.origin.y,bounds.origin.z],'extent':[bounds.box_extent.x,bounds.box_extent.y,bounds.box_extent.z]}
 report['checks']['site_100m']=abs(bounds.box_extent.x*2-10000)<.1 and abs(bounds.box_extent.y*2-10000)<.1
 reg=u.AssetRegistryHelpers.get_asset_registry();reg.scan_paths_synchronous(['/Game'],force_rescan=True)
 options=u.AssetRegistryDependencyOptions(True,True,True,True,True,True,True)
 queue=[MAP]+[str(a.package_name) for a in reg.get_assets_by_path(ROOT,recursive=True)]
 visited=set();graph={};foreign=[]
 while queue:
  pkg=queue.pop()
  if pkg in visited:continue
  visited.add(pkg);deps=[str(d) for d in reg.get_dependencies(pkg,options)];graph[pkg]=deps
  for dep in deps:
   if dep.startswith('/Game/'):
    if not (dep.startswith(ROOT+'/') or dep==MAP):foreign.append({'from':pkg,'to':dep})
    elif dep not in visited:queue.append(dep)
 report['dependency_graph']=graph;report['foreign_game_dependencies']=foreign
 report['checks']['recursive_dependencies_owned_only']=not foreign
 content=Path(u.Paths.project_content_dir())
 report['external_packages']=[str(p.relative_to(content)) for p in content.rglob('*') if p.is_file() and ('__External' in str(p) or 'BuiltData' in p.name)]
 report['checks']['no_external_or_builtdata']=not report['external_packages']
 report['collision_samples']=[]
 positions=[('player_floor',-3800,-300,500),('ramp_bottom',-3550,-600,500),('ramp_middle',-3200,-600,500),('ramp_top',-2820,-600,500),('platform_west',-2350,-1220,400),('platform_center',-1000,-1280,400),('platform_east',500,-1130,400),('track_bed',2000,-1240,300),('hill_trail',-1800,2200,5000)]
 expected={'player_floor':(20,45),'ramp_bottom':(29,34),'ramp_middle':(71,76),'ramp_top':(117,123),'platform_west':(120,128),'platform_center':(120,128),'platform_east':(120,128),'track_bed':(35,65),'hill_trail':(100,2000)}
 for name,x,y,z in positions:
  hit=u.SystemLibrary.line_trace_single(world,u.Vector(x,y,z),u.Vector(x,y,-500),u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],u.DrawDebugTrace.NONE)
  record={'name':name,'start':[x,y,z],'hit':hit is not None}
  if hit:
   vals=hit.to_tuple();record['blocking']=bool(vals[0]);record['location_cm']=[vals[4].x,vals[4].y,vals[4].z];record['actor']=vals[9].get_actor_label() if vals[9] else None
   record['expected_z_range_cm']=expected[name];record['height_correct']=expected[name][0]<=vals[4].z<=expected[name][1]
  report['collision_samples'].append(record)
 report['checks']['floor_samples_blocking']=all(x.get('blocking',False) for x in report['collision_samples'])
 report['checks']['floor_samples_heights']=all(x.get('height_correct',False) for x in report['collision_samples'])
 report['mesh_collision']={}
 for a in actors:
  if isinstance(a,u.StaticMeshActor) and a.get_actor_label().startswith('Alder_'):
   report['mesh_collision'][a.get_actor_label()]=str(a.static_mesh_component.static_mesh.get_editor_property('body_setup').get_editor_property('collision_trace_flag'))
 report['checks']['required_assemblies']=all(any(a.get_actor_label()=='Alder_'+name for a in actors) for name in ['Terrain','Railway','Platform','Station','Tunnel','Cargo','Props','Paths','LandscapeDetails'])
 report['errors']=[key for key,value in report['checks'].items() if not value]
 report['success']=not report['errors'];report['finished_at_utc']=datetime.now(timezone.utc).isoformat();report['elapsed_seconds']=time.time()-start
 (WORK/'Evidence/validation.json').write_text(json.dumps(report,indent=2))
 print('ALDER_VALIDATION',report['success'],report['checks'])
 return report
if __name__=='__main__':validate()
