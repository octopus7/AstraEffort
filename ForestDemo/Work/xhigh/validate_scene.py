import unreal as u, json, datetime, os, traceback
ROOT='D:/github/AstraEffort/ForestDemo/Work/xhigh'
REPORT={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'map':'/Game/Maps/xhigh','checks':{},'errors':[]}
def check(k,v):
 REPORT['checks'][k]=v
 if not v:REPORT['errors'].append(k)
try:
 les=u.get_editor_subsystem(u.LevelEditorSubsystem)
 check('map_reloaded',les.load_level('/Game/Maps/xhigh'))
 world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
 eas=u.get_editor_subsystem(u.EditorActorSubsystem);actors=eas.get_all_level_actors()
 labels={a.get_actor_label():a for a in actors}
 terrain=labels['SM_Terrain'];origin,extent=terrain.get_actor_bounds(False)
 REPORT['terrain_bounds_cm']={'origin':[origin.x,origin.y,origin.z],'extent':[extent.x,extent.y,extent.z]}
 check('footprint_10000_by_10000_cm',abs(extent.x*2-10000)<.1 and abs(extent.y*2-10000)<.1)
 check('separate_lake_and_sea',all(n in labels for n in ['SM_Lake','SM_Sea']))
 check('player_start_present','PlayerStart_TrailArrival' in labels)
 check('baseline_hello_actor_present','ScreenDebugLogger_Hello' in labels and labels['ScreenDebugLogger_Hello'].get_class().get_path_name()=='/Script/ForestDemo.ScreenDebugLogger')
 check('overview_camera_present','Overview_QuietCove' in labels)
 check('dynamic_lighting',world.get_world_settings().get_editor_property('force_no_precomputed_lighting') and labels['QuietCove_Sun'].light_component.mobility==u.ComponentMobility.MOVABLE)
 external=[a.get_actor_label() for a in actors if a.is_package_external()]
 REPORT['external_actor_packages']=external;check('no_external_actor_packages',not external)
 REPORT['world_settings_class']=world.get_world_settings().get_class().get_path_name()
 try:
  partition=world.get_world_settings().get_editor_property('world_partition')
  REPORT['world_partition']=str(partition);check('non_world_partition',partition is None)
 except Exception as e:
  REPORT['partition_property_note']=str(e)
  check('non_world_partition',not external)
 registry=u.AssetRegistryHelpers.get_asset_registry();registry.scan_paths_synchronous(['/Game/Forest/xhigh','/Game/Maps'],True)
 opts=u.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_searchable_names=True,include_soft_management_references=True,include_hard_management_references=True)
 todo=['/Game/Maps/xhigh']+[str(a.package_name) for a in registry.get_assets_by_path('/Game/Forest/xhigh',True)]
 seen=set();bad=[];graph={}
 while todo:
  p=todo.pop()
  if p in seen:continue
  seen.add(p);deps=[str(x) for x in registry.get_dependencies(p,opts)];graph[p]=deps
  for d in deps:
   if d.startswith('/Game/'):
    if not (d.startswith('/Game/Forest/xhigh/') or d=='/Game/Maps/xhigh'):bad.append({'from':p,'to':d})
    elif d not in seen:todo.append(d)
 REPORT['dependency_graph']=graph;REPORT['forbidden_game_dependencies']=bad;check('recursive_game_dependencies_owned',not bad)
 REPORT['checked_package_count']=len(seen)
 meshchecks=[]
 for a in actors:
  if isinstance(a,u.StaticMeshActor):
   c=a.static_mesh_component;mesh=c.static_mesh
   if not mesh:REPORT['errors'].append('missing_mesh:'+a.get_actor_label());continue
   meshchecks.append({'actor':a.get_actor_label(),'mesh':mesh.get_path_name(),'collision':str(c.get_collision_enabled()),'collision_enabled':c.get_collision_enabled()!=u.CollisionEnabled.NO_COLLISION,'trace_flag':str(mesh.get_editor_property('body_setup').get_editor_property('collision_trace_flag'))})
 REPORT['static_mesh_actor_count']=len(meshchecks);REPORT['collision_enabled_actor_count']=sum(x['collision_enabled'] for x in meshchecks)
 rotations=[]
 for i,inst in enumerate(json.load(open(ROOT+'/scene_manifest.json'))['instances']):
  a=labels['%s_%04d'%(inst['mesh'],i)];r=a.get_actor_rotation()
  if abs(r.pitch)>.01 or abs(r.roll)>.01 or abs((r.yaw-inst['yaw']+180)%360-180)>.01:rotations.append(a.get_actor_label())
 REPORT['misoriented_instances']=rotations;check('instance_rotations_match_manifest',not rotations)
 check('terrain_complex_collision',terrain.static_mesh_component.static_mesh.get_editor_property('body_setup').get_editor_property('collision_trace_flag')==u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
 trace_results=[]
 for sample in json.load(open(ROOT+'/scene_manifest.json'))['terrain_samples']:
  x=sample['x_m']*100;y=sample['y_m']*100
  hit=terrain.static_mesh_component.line_trace_component(u.Vector(x,y,3000),u.Vector(x,y,-1000),True,False,False)
  if hit:
   loc=hit[0]
   trace_results.append({'xy_cm':[x,y],'blocking_hit':True,'impact_point_cm':[loc.x,loc.y,loc.z],'expected_terrain_height_cm':sample['height_m']*100,'height_error_cm':abs(loc.z-sample['height_m']*100)})
  else:trace_results.append({'xy_cm':[x,y],'blocking_hit':False})
 REPORT['terrain_traces']=trace_results
 check('spawn_ground_trace',trace_results[0]['blocking_hit'] and trace_results[0].get('height_error_cm',999)<5)
 check('all_terrain_samples_match_source_within_5cm',all(t['blocking_hit'] and t.get('height_error_cm',999)<5 for t in trace_results))
 check('decorative_foliage_has_no_collision',all(a.static_mesh_component.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION for a in actors if isinstance(a,u.StaticMeshActor) and any(str(t) in ['water','understory','beach_grass','lake_reeds'] for t in a.tags)))
 REPORT['actor_count']=len(actors);REPORT['roles']={}
 for a in actors:
  for t in a.tags:REPORT['roles'][str(t)]=REPORT['roles'].get(str(t),0)+1
 check('forest_tree_population',REPORT['roles'].get('tree',0)>=80)
 check('beach_dressing',REPORT['roles'].get('beach_stones',0)>20)
 REPORT['passed']=not REPORT['errors']
except Exception:
 REPORT['errors'].append(traceback.format_exc());REPORT['passed']=False
finally:
 json.dump(REPORT,open(ROOT+'/validation.json','w'),indent=2)
 u.log('XHIGH_VALIDATION '+str(REPORT['passed']))
 if not globals().get('XHIGH_KEEP_EDITOR',False):u.SystemLibrary.quit_editor()
