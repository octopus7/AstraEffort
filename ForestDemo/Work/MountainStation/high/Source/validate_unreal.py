import unreal as u,json,datetime,traceback,os,time
validation_started=time.time()
ROOT='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high'
BASE='/Game/MountainStation/high'
MAP='/Game/Maps/MountainStation_high'
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert level.load_level(MAP),'Map reload failed'
lib=u.EditorAssetLibrary;reg=u.AssetRegistryHelpers.get_asset_registry();reg.scan_paths_synchronous(['/Game'],True)
opts=u.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_searchable_names=False,include_soft_management_references=True,include_hard_management_references=True)
todo=[MAP]+[str(a.package_name) for a in reg.get_assets_by_path(BASE,recursive=True)];seen=set();edges={};bad=[]
while todo:
 p=todo.pop()
 if p in seen:continue
 seen.add(p);deps=[str(x) for x in reg.get_dependencies(p,opts)];edges[p]=deps
 for d in deps:
  if d.startswith('/Game/'):
   if not(d==MAP or d.startswith(BASE+'/')):bad.append({'from':p,'to':d})
   if d not in seen:todo.append(d)
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
records=[];collision=[]
for a in actors:
 rec={'label':a.get_actor_label(),'class':a.get_class().get_name(),'location':str(a.get_actor_location())}
 if isinstance(a,u.StaticMeshActor):
  c=a.static_mesh_component;m=c.static_mesh;rec['mesh']=m.get_path_name() if m else None
  if m and m.get_path_name().startswith(BASE):
   mode=str(m.get_editor_property('body_setup').get_editor_property('collision_trace_flag'));rec['collision']=mode;collision.append('CTF_USE_COMPLEX_AS_SIMPLE' in mode)
 records.append(rec)
terrain=next(a for a in actors if a.get_actor_label()=='Terrain');origin,extent=terrain.get_actor_bounds(False)
checks={
 'map_reload':True,'owned_game_dependencies':not bad,
 'terrain_100m_x':abs(extent.x-5000)<5,'terrain_100m_y':abs(extent.y-5000)<5,
 'player_start':any(isinstance(a,u.PlayerStart) for a in actors),
 'screen_debug_logger':any(a.get_class().get_name()=='ScreenDebugLogger' for a in actors),
 'complex_collision':all(collision) and len(collision)>0,
 'assemblies_present':all(any(a.get_actor_label()==n for a in actors) for n in ['Terrain','Railway','Platform','Station','Tunnel','Cargo','GroundPaths','Furniture','Vegetation']),
 'dynamic_lighting':u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_world_settings().get_editor_property('force_no_precomputed_lighting')}
result={'validated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'validation_seconds':time.time()-validation_started,'map':MAP,'checks':checks,'passed':all(checks.values()),'terrain_origin_cm':str(origin),'terrain_extent_cm':str(extent),'checked_package_count':len(seen),'forbidden_dependencies':bad,'dependency_graph':edges,'actors':records}
json.dump(result,open(ROOT+'/validation.json','w'),indent=2)
u.log('SOLMARU_VALIDATION '+json.dumps(checks))
assert result['passed'],'Validation failed'
