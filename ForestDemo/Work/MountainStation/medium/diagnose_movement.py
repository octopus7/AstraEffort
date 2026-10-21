import unreal as u, time, datetime, json, traceback
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium'
L=u.get_editor_subsystem(u.LevelEditorSubsystem); E=u.get_editor_subsystem(u.EditorActorSubsystem)
MAP='/Game/Maps/MountainStation_medium'
L.load_level(MAP)
report={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'map':MAP,'phase':'before_fix'}
def snapshot(a):
 c=a.get_component_by_class(u.PrimitiveComponent)
 return {'actor':a.get_path_name(),'label':a.get_actor_label(),'actor_collision':a.get_actor_enable_collision(),'profile':str(c.get_collision_profile_name()),'enabled':str(c.get_collision_enabled()),'object_type':str(c.get_collision_object_type()),'pawn_response':str(c.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN))} if c else {'actor':a.get_path_name()}
report['saved_editor_backdrop']=[snapshot(a) for a in E.get_all_level_actors() if a.get_actor_label()=='Quiet blue horizon']
def movecheck(p):
 p.set_actor_location(u.Vector(-1900,-1000,150),False,True)
 before=list(p.get_actor_location().to_tuple())
 hit=p.set_actor_location(u.Vector(-1900,-800,150),True,False)
 after=list(p.get_actor_location().to_tuple())
 return {'from':before,'to':after,'distance_cm':u.Vector(*before).distance(u.Vector(*after)),'hit':str(hit.to_tuple()) if hit else None}
stage=0; stamp=time.time(); L.editor_request_begin_play()
def tick(dt):
 global stage,stamp
 try:
  if stage==0 and time.time()-stamp>3:
   stage=10
   worlds=u.EditorLevelLibrary.get_pie_worlds(False)
   if not worlds: raise RuntimeError('No PIE world')
   world=worlds[0]; pawn=u.GameplayStatics.get_player_pawn(world,0); pc=u.GameplayStatics.get_player_controller(world,0)
   report['pawn']=snapshot(pawn); report['possessed']=pc.get_controlled_pawn()==pawn
   report['spawn_location_cm']=list(pawn.get_actor_location().to_tuple())
   backdrops=[a for a in u.GameplayStatics.get_all_actors_of_class(world,u.StaticMeshActor) if a.get_actor_label()=='Quiet blue horizon']
   report['pie_backdrop_before']=[snapshot(a) for a in backdrops]
   trace=u.SystemLibrary.sphere_trace_single_by_profile(world,u.Vector(-1900,-1000,150),u.Vector(-1900,-800,150),35,'Pawn',False,[pawn],u.DrawDebugTrace.NONE)
   report['pawn_profile_sweep_before']=str(trace.to_tuple()) if trace else None
   report['movement_before']=movecheck(pawn)
   for a in backdrops:
    a.set_actor_enable_collision(False); a.static_mesh_component.set_collision_profile_name('NoCollision'); a.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
   report['pie_backdrop_disabled']=[snapshot(a) for a in backdrops]
   report['movement_after_backdrop_disabled']=movecheck(pawn)
   report['backdrop_cause_confirmed']=report['movement_before']['distance_cm']<1 and report['movement_after_backdrop_disabled']['distance_cm']>150
   L.editor_request_end_play(); stage=1; stamp=time.time()
  elif stage==1 and time.time()-stamp>3:
   stage=10
   report['normal_pie_shutdown']=not L.is_in_play_in_editor()
   if not report['backdrop_cause_confirmed']: raise RuntimeError('Backdrop not proven causal; inspect diagnostics before modifying saved map')
   for a in E.get_all_level_actors():
    if a.get_actor_label()=='Quiet blue horizon':
     a.set_actor_enable_collision(False); a.static_mesh_component.set_collision_profile_name('NoCollision'); a.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
   L.save_current_level(); L.load_level(MAP)
   report['saved_reloaded_backdrop_after']=[snapshot(a) for a in E.get_all_level_actors() if a.get_actor_label()=='Quiet blue horizon']
   report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
   json.dump(report,open(W+'/movement_diagnosis.json','w'),indent=2)
   print('MOVEMENT_DIAGNOSIS '+json.dumps(report)); u.unregister_slate_post_tick_callback(handle); u.SystemLibrary.quit_editor()
 except Exception:
  report['error']=traceback.format_exc(); json.dump(report,open(W+'/movement_diagnosis.json','w'),indent=2)
  L.editor_request_end_play(); u.unregister_slate_post_tick_callback(handle); u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
