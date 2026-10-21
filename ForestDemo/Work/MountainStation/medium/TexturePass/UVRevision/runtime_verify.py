import unreal as u, time, datetime, json, traceback
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/TexturePass/UVRevision'; MAP='/Game/Maps/MountainStation_medium'; ROOT='/Game/MountainStation/medium'
L=u.get_editor_subsystem(u.LevelEditorSubsystem); E=u.get_editor_subsystem(u.EditorActorSubsystem)
assert L.load_level(MAP)
report={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'map':MAP,'fresh_process_reload':True,'checks':{},'limitations':[]}
def state(a):
 c=a.get_component_by_class(u.PrimitiveComponent)
 return {'actor':a.get_path_name(),'actor_collision':a.get_actor_enable_collision(),'profile':str(c.get_collision_profile_name()),'enabled':str(c.get_collision_enabled()),'object_type':str(c.get_collision_object_type()),'pawn_response':str(c.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN))}
back=next(a for a in E.get_all_level_actors() if a.get_actor_label()=='Quiet blue horizon')
report['saved_backdrop']=state(back)
report['checks']['saved_backdrop_actor_collision_off']=not back.get_actor_enable_collision()
report['checks']['saved_backdrop_profile_no_collision']=str(back.static_mesh_component.get_collision_profile_name())=='NoCollision'
report['checks']['saved_backdrop_component_collision_off']=back.static_mesh_component.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION
reg=u.AssetRegistryHelpers.get_asset_registry(); reg.scan_paths_synchronous([ROOT,'/Game/Maps'],force_rescan=True)
opt=u.AssetRegistryDependencyOptions(True,True,False,False,False); todo=[MAP]; visited=set(); deps={}; bad=[]
while todo:
 p=todo.pop()
 if p in visited: continue
 visited.add(p); children=[str(x) for x in reg.get_dependencies(p,opt)]; deps[p]=children
 for ch in children:
  if ch.startswith('/Game/'):
   if ch==MAP or ch.startswith(ROOT+'/'): todo.append(ch)
   else: bad.append(ch)
report['checks']['scoped_dependencies']=len(bad)==0
v={}; v['dependencies']=deps; v['visited_packages']=len(visited); v['foreign_game_dependencies']=sorted(set(bad)); v['fresh_process_collision_fix_reload_utc']=report['started_at_utc']; json.dump(v,open(W+'/validation.json','w'),indent=2)
stage=0; stamp=time.time(); begun=stamp
u.SystemLibrary.execute_console_command(u.EditorLevelLibrary.get_editor_world(),'EnableAllScreenMessages'); L.editor_request_begin_play()
def vec(p): return [float(p.x),float(p.y),float(p.z)]
def sweep(p,target):
 before=vec(p.get_actor_location()); h=p.set_actor_location(u.Vector(*target),True,False); after=vec(p.get_actor_location())
 parts=h.to_tuple() if h else None
 hitdata=None
 if parts:
  actor=parts[9];component=parts[10]
  hitdata={'blocking':bool(parts[0]),'initial_overlap':bool(parts[1]),'actor':actor.get_path_name() if actor else None,'component':component.get_path_name() if component else None,'mesh':component.static_mesh.get_path_name() if component and isinstance(component,u.StaticMeshComponent) and component.static_mesh else None,'impact_point_cm':vec(parts[5])}
 return {'hit_data':hitdata,'from':before,'target':target,'to':after,'distance_cm':u.Vector(*before).distance(u.Vector(*after)),'hit':str(h.to_tuple()) if h else None}
def tick(dt):
 global stage,stamp
 try:
  if stage==0 and time.time()-stamp>3:
   stage=10; worlds=u.EditorLevelLibrary.get_pie_worlds(False)
   if not worlds: raise RuntimeError('No PIE world')
   world=worlds[0]; pc=u.GameplayStatics.get_player_controller(world,0); pawn=u.GameplayStatics.get_player_pawn(world,0)
   report['game_world']=world.get_path_name(); report['checks']['pie_active']=L.is_in_play_in_editor(); report['checks']['pawn_created']=bool(pawn); report['checks']['controller_created']=bool(pc); report['checks']['possessed']=bool(pc and pawn and pc.get_controlled_pawn()==pawn)
   report['pawn']=state(pawn); report['spawn_location_cm']=vec(pawn.get_actor_location())
   report['checks']['expected_spawn']=pawn.get_actor_location().distance(u.Vector(-1900,-1150,120))<2
   b=next(a for a in u.GameplayStatics.get_all_actors_of_class(world,u.StaticMeshActor) if a.get_actor_label()=='Quiet blue horizon')
   report['pie_backdrop']=state(b); report['checks']['pie_backdrop_collision_off']=not b.get_actor_enable_collision() and b.static_mesh_component.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION and str(b.static_mesh_component.get_collision_profile_name())=='NoCollision'
   h=u.SystemLibrary.sphere_trace_single_by_profile(world,u.Vector(-1900,-1150,120),u.Vector(-1900,-1149,120),35,'Pawn',False,[pawn],u.DrawDebugTrace.NONE)
   report['pawn_start_overlap_probe']=str(h.to_tuple()) if h else None; report['checks']['pawn_start_no_blocking_overlap']=not(h and h.to_tuple()[0])
   report['spawn_move']=sweep(pawn,[-1900,-950,120]); report['checks']['actual_possessed_pawn_moves_200cm']=report['spawn_move']['distance_cm']>195
   report['direct_actor_move_succeeded']=report['checks']['actual_possessed_pawn_moves_200cm']; report['short_move']=report['spawn_move']
   for name,x,y,surface in [('terrain',2000,-3000,0),('ramp',-1900,-600,36.5),('platform',-2200,400,72)]:
    # Teleport to clear height, then use actual possessed Pawn sweep against its own collision channels.
    pawn.set_actor_location(u.Vector(x,y,250),False,True)
    move=sweep(pawn,[x,y,-100]); report[name+'_pawn_downward_sweep']=move
    # Terrain chosen point has a low hill; use runtime Pawn-profile ground trace for exact surface height.
    hit=u.SystemLibrary.line_trace_single_by_profile(world,u.Vector(x,y,250),u.Vector(x,y,-500),'Pawn',False,[pawn],u.DrawDebugTrace.NONE)
    parts=hit.to_tuple() if hit else None
    report[name+'_pawn_profile_trace']=str(parts)
    actual_surface=float(parts[4].z) if parts else surface
    report['checks'][name+'_pawn_collision_blocks']=bool(parts and parts[0] and move['hit_data'] and move['hit_data']['blocking'] and not move['hit_data']['initial_overlap'] and move['hit_data']['mesh']=='/Game/MountainStation/medium/TexturePass/UVRevision/Meshes/SM_AlderPass_UV.SM_AlderPass_UV' and move['distance_cm']>20 and abs(move['to'][2]-(actual_surface+35))<5)
   loggers=u.GameplayStatics.get_all_actors_of_class(world,u.load_class(None,'/Script/ForestDemo.ScreenDebugLogger'))
   report['checks']['baseline_logger_in_pie']=len(loggers)==1
   u.SystemLibrary.execute_console_command(world,'Shot SHOWUI filename='+W+'/runtime_hello.png -nosuffix')
   stage=1; stamp=time.time()
  elif stage==1 and time.time()-stamp>2:
   stage=10; L.editor_request_end_play(); stage=2; stamp=time.time()
  elif stage==2 and time.time()-stamp>3:
   stage=10; report['checks']['normal_pie_shutdown']=not L.is_in_play_in_editor(); report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat(); report['runtime_execution_seconds']=time.time()-begun
   report['passed']=all(report['checks'].values())
   for name in ['movement_runtime_validation.json','runtime_validation.json']: json.dump(report,open(W+'/'+name,'w'),indent=2)
   print('MOVEMENT_RUNTIME_VALIDATION '+json.dumps(report)); u.unregister_slate_post_tick_callback(handle); assert report['passed'],report['checks']; exec(compile(open(W+'/capture.py',encoding='utf-8-sig').read(),W+'/capture.py','exec'),globals())
 except Exception:
  report['error']=traceback.format_exc(); report['passed']=False
  for name in ['movement_runtime_validation.json','runtime_validation.json']: json.dump(report,open(W+'/'+name,'w'),indent=2)
  L.editor_request_end_play(); u.unregister_slate_post_tick_callback(handle); u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)



