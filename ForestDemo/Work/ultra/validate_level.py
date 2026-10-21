import unreal as u, json, traceback, datetime
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra')
ASSET='/Game/Forest/ultra';MAP='/Game/Maps/ultra'
report={'map':MAP,'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':{},'errors':[]}
def check(key,passed,detail=None):
 report['checks'][key]={'passed':bool(passed),'detail':detail}
 if not passed:report['errors'].append(key)
try:
 levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
 check('fresh_map_reload',levels.load_level(MAP))
 world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
 actorlist=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
 classes={}
 for a in actorlist:classes[a.get_class().get_name()]=classes.get(a.get_class().get_name(),0)+1
 check('player_start',classes.get('PlayerStart',0)==1,classes.get('PlayerStart'))
 check('hello_logger',classes.get('ScreenDebugLogger',0)==1,classes.get('ScreenDebugLogger'))
 check('dynamic_lighting',world.get_world_settings().get_editor_property('force_no_precomputed_lighting'))
 wp=world.get_world_settings().get_editor_property('world_partition')
 check('non_world_partition',wp is None,str(wp))
 eas=u.get_editor_subsystem(u.EditorAssetSubsystem)
 bounds=eas.load_asset(ASSET+'/Meshes/SM_Ground').get_bounds()
 check('100m_footprint',abs(bounds.box_extent.x*2-10000)<1 and abs(bounds.box_extent.y*2-10000)<1,[bounds.box_extent.x*2,bounds.box_extent.y*2])
 check('lake_and_sea_are_distinct',eas.does_asset_exist(ASSET+'/Meshes/SM_Lake') and eas.does_asset_exist(ASSET+'/Meshes/SM_Sea'))
 manifest=json.loads((ROOT/'scene_manifest.json').read_text());trace_results=[]
 for x,y,z in manifest['height_samples']:
  hit=u.SystemLibrary.line_trace_single(world,u.Vector(x*100,-y*100,1200),u.Vector(x*100,-y*100,-500),u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],u.DrawDebugTrace.NONE)
  trace_results.append({'xy_m':[x,y],'expected_ground_z_cm':z*100,'hit':str(hit),'blocked':hit is not None})
 report['editor_world_trace_diagnostic']=trace_results
 report['runtime_collision_test_required']=True
 solids=[]
 for a in actorlist:
  if isinstance(a,u.StaticMeshActor):
   c=a.static_mesh_component;mesh=c.static_mesh
   if mesh and mesh.get_name().startswith(('SM_Ground','SM_Rock','SM_Broadleaf','SM_Pine','SM_Log','SM_Bench','SM_LakeLanding')):
    solids.append(c.get_collision_enabled()!=u.CollisionEnabled.NO_COLLISION)
 check('solid_props_collision_enabled',all(solids),{'count':len(solids)})
 mesh_collision=[]
 sme=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
 for name,meta in manifest['assets'].items():
  mesh=eas.load_asset(ASSET+'/Meshes/'+name)
  flag=mesh.get_editor_property('body_setup').get_editor_property('collision_trace_flag')
  count=sme.get_simple_collision_count(mesh)+sme.get_convex_collision_count(mesh)
  if meta['collision']=='complex' or name.startswith(('SM_Broadleaf','SM_Pine')):passed=flag==u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
  elif meta['collision']=='simple':passed=count>=1
  else:passed=True
  mesh_collision.append({'mesh':name,'complexity':str(flag),'simple_shapes':count,'passed':passed})
 check('mesh_collision_geometry',all(x['passed'] for x in mesh_collision),mesh_collision)
 registry=u.AssetRegistryHelpers.get_asset_registry();registry.scan_paths_synchronous(['/Game/Forest/ultra','/Game/Maps'],True)
 options=u.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True,include_searchable_names=True,include_hard_management_references=True,include_soft_management_references=True,include_editor_only_package_references=True,include_game_package_references=True)
 roots=[MAP]+[str(a.package_name) for a in registry.get_assets_by_path(ASSET,recursive=True)]
 queue=list(roots);visited=set();edges={};bad=[]
 while queue:
  p=queue.pop()
  if p in visited:continue
  visited.add(p);deps=[str(x) for x in registry.get_dependencies(p,options)];edges[p]=deps
  for d in deps:
   if d.startswith('/Game/'):
    if not(d.startswith(ASSET+'/') or d==MAP):bad.append({'from':p,'to':d})
    if d not in visited:queue.append(d)
 check('recursive_game_dependencies',not bad,{'packages_checked':len(visited),'violations':bad})
 content=Path(r'D:/github/AstraEffort/ForestDemo/Saved/Workers/ultra/ForestDemo/Content')
 illegal=[str(p.relative_to(content)) for p in content.rglob('*') if p.is_file() and ('__ExternalActors__' in str(p) or '__ExternalObjects__' in str(p) or 'BuiltData' in p.name)]
 check('no_external_or_baked_packages',not illegal,illegal)
 report['actor_classes']=classes;report['dependency_graph']=edges
 report['success']=not report['errors']
except Exception:
 report['errors'].append(traceback.format_exc());report['success']=False
finally:
 (ROOT/'validation.json').write_text(json.dumps(report,indent=2))
 u.log('ULTRA_VALIDATION '+str(report['success']))
 if not globals().get('KEEP_EDITOR_OPEN',False):u.SystemLibrary.quit_editor()
