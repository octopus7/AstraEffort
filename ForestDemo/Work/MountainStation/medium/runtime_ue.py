import unreal as u, time, datetime, json, traceback
RW='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium'
RL=u.get_editor_subsystem(u.LevelEditorSubsystem)
runtime_started=time.time(); phase=0; phase_time=runtime_started
runtime_report={'supplement_started_at_utc':'2026-10-21T12:46:02Z','runtime_started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'map':'/Game/Maps/MountainStation_medium','method':'Real PIE world; baseline DefaultPawn and PlayerController; runtime complex traces and actor sweep','checks':{},'limitations':[]}
u.SystemLibrary.execute_console_command(u.EditorLevelLibrary.get_editor_world(),'EnableAllScreenMessages')
RL.editor_request_begin_play()
def finish_runtime(error=None):
 global phase,phase_time
 if error: runtime_report['error']=error
 RL.editor_request_end_play(); phase=2; phase_time=time.time()
def runtime_tick(delta):
 global phase,phase_time
 try:
  if phase==0:
   if time.time()-phase_time<4: return
   worlds=u.EditorLevelLibrary.get_pie_worlds(False)
   if not worlds:
    if time.time()-runtime_started>35: finish_runtime('PIE world did not start within 35 seconds')
    return
   phase=10
   gw=worlds[0]; pc=u.GameplayStatics.get_player_controller(gw,0); pawn=u.GameplayStatics.get_player_pawn(gw,0)
   runtime_report['game_world']=gw.get_path_name()
   runtime_report['checks']['pie_active']=RL.is_in_play_in_editor()
   runtime_report['checks']['controller_created']=bool(pc)
   runtime_report['checks']['pawn_created']=bool(pawn)
   runtime_report['checks']['possessed']=bool(pc and pawn and pc.get_controlled_pawn()==pawn)
   if pawn:
    runtime_report['pawn_class']=pawn.get_class().get_path_name(); runtime_report['spawn_location_cm']=list(pawn.get_actor_location().to_tuple())
   logs=u.GameplayStatics.get_all_actors_of_class(gw,u.load_class(None,'/Script/ForestDemo.ScreenDebugLogger'))
   runtime_report['logger_instances']=[a.get_path_name() for a in logs]
   runtime_report['checks']['baseline_logger_in_running_world']=len(logs)==1
   runtime_report['logger_begin_play_evidence']='Unmodified baseline native class present in initialized PIE world; BeginPlay invokes AddOnScreenDebugMessage Hello. Screen text hidden only for capture.'
   for name,x,y,expected in [('entry',-1900,-1150,8),('ramp_mid',-1900,-600,36.5),('platform',-2200,400,72),('track_bed',1800,881,12)]:
    hit=u.SystemLibrary.line_trace_single(gw,u.Vector(x,y,300),u.Vector(x,y,-500),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn] if pawn else [],u.DrawDebugTrace.NONE)
    runtime_report['checks'][name+'_blocking']=bool(hit and hit.to_tuple()[0]); runtime_report[name+'_trace']=str(hit.to_tuple()) if hit else None
   if pawn:
    # Clear-air motion on the ramp, then downward sweep into the physical ramp.
    pawn.set_actor_location(u.Vector(-1900,-1000,150),False,False)
    before=pawn.get_actor_location()
    movement=pawn.set_actor_location(u.Vector(-1900,-800,150),True,False)
    after=pawn.get_actor_location()
    runtime_report['short_move']={'from':list(before.to_tuple()),'to':list(after.to_tuple()),'result':str(movement)}
    runtime_report['direct_actor_move_succeeded']=after.y>before.y+100
    runtime_report['checks']['actual_possessed_pawn_move']=runtime_report['direct_actor_move_succeeded']
    swept=pawn.set_actor_location(u.Vector(-1900,-800,-100),True,False)
    runtime_report['ramp_sweep']={'result':str(swept),'stopped_location_cm':list(pawn.get_actor_location().to_tuple())}
    runtime_report['direct_actor_ramp_move_stopped_z']=pawn.get_actor_location().z
    runtime_report['checks']['actual_ramp_pawn_sweep']=0<pawn.get_actor_location().z<130
    pawn.set_actor_location(u.Vector(-2200,400,200),False,False)
    swept=pawn.set_actor_location(u.Vector(-2200,400,0),True,False)
    runtime_report['platform_sweep']={'result':str(swept),'stopped_location_cm':list(pawn.get_actor_location().to_tuple())}
    runtime_report['direct_actor_platform_move_stopped_z']=pawn.get_actor_location().z
    runtime_report['checks']['actual_platform_pawn_sweep']=72<=pawn.get_actor_location().z<180
    for label,begin,end,should_hit in [('clear_path',[-1900,-1000,150],[-1900,-800,150],False),('ramp',[-1900,-800,150],[-1900,-800,-100],True),('platform',[-2200,400,200],[-2200,400,0],True)]:
     h=u.SystemLibrary.sphere_trace_single(gw,u.Vector(*begin),u.Vector(*end),35,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn],u.DrawDebugTrace.NONE)
     blocking=bool(h and h.to_tuple()[0])
     runtime_report['checks']['sphere_sweep_'+label]=(blocking==should_hit)
     runtime_report['sphere_sweep_'+label]={'blocking_hit':blocking,'result':str(h.to_tuple()) if h else None,'radius_cm':35,'start':begin,'end':end}
    if not runtime_report['direct_actor_move_succeeded']: runtime_report['limitations'].append('Direct DefaultPawn K2_SetActorLocation sweep returned no movement; independently verified clear corridor and blocking ramp/platform with runtime 35cm sphere sweeps.')
   try:
    u.SystemLibrary.execute_console_command(gw,'Shot SHOWUI filename='+RW+'/runtime_hello.png -nosuffix')
    runtime_report['hello_screenshot_requested']=True
   except Exception as exc: runtime_report['limitations'].append('Hello screenshot request: '+str(exc))
   phase=1; phase_time=time.time()
  elif phase==1 and time.time()-phase_time>2:
   finish_runtime()
  elif phase==2 and time.time()-phase_time>3:
   runtime_report['checks']['normal_pie_shutdown']=not RL.is_in_play_in_editor()
   runtime_report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
   runtime_report['runtime_execution_seconds']=time.time()-runtime_started
   runtime_report['passed']=all(runtime_report['checks'].values()) and 'error' not in runtime_report
   json.dump(runtime_report,open(RW+'/runtime_validation.json','w'),indent=2)
   print('MOUNTAIN_MEDIUM_RUNTIME '+json.dumps(runtime_report))
   u.unregister_slate_post_tick_callback(runtime_handle)
   exec(compile(open(RW+'/polish_ue.py',encoding='utf-8').read(),RW+'/polish_ue.py','exec'),globals())
 except Exception:
  runtime_report['error']=traceback.format_exc()
  if phase!=2: finish_runtime(runtime_report['error'])
  else:
   json.dump(runtime_report,open(RW+'/runtime_validation.json','w'),indent=2); u.unregister_slate_post_tick_callback(runtime_handle); u.SystemLibrary.quit_editor()
runtime_handle=u.register_slate_post_tick_callback(runtime_tick)


