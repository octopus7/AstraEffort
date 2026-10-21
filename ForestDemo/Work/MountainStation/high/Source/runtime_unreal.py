import unreal as u,json,time,datetime,traceback
ROOT='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high'
runtime_started=time.time();runtime_frame=0;runtime_state='starting'
runtime_level=u.get_editor_subsystem(u.LevelEditorSubsystem)
runtime_report={'supplement_requested_at_utc':'2026-10-21T12:46:15Z','started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'map':'/Game/Maps/MountainStation_high','checks':{},'observations':{},'limitations':[]}
def vec(v):return [v.x,v.y,v.z]
def save_runtime():
 json.dump(runtime_report,open(ROOT+'/runtime_validation.json','w'),indent=2)
def after_runtime():
 if globals().get('RUNTIME_ONLY',False):u.SystemLibrary.quit_editor()
 else:exec(compile(open(ROOT+'/Source/capture_unreal.py').read(),ROOT+'/Source/capture_unreal.py','exec'),globals())
def runtime_tick(dt):
 global runtime_frame,runtime_state,runtime_handle
 runtime_frame+=1
 try:
  if runtime_state=='starting' and runtime_frame>90:
   w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
   if not w:
    if runtime_frame<600:return
    raise RuntimeError('No PIE game world after 600 ticks')
   pc=u.GameplayStatics.get_player_controller(w,0);pawn=u.GameplayStatics.get_player_pawn(w,0)
   c=runtime_report['checks'];obs=runtime_report['observations'];c['pie_world']=runtime_level.is_in_play_in_editor();c['player_controller_created']=bool(pc);c['pawn_created']=bool(pawn)
   if not pc or not pawn:raise RuntimeError('PIE missing player controller or pawn')
   c['pawn_possessed']=pawn.get_controller()==pc
   loc=pawn.get_actor_location();obs['spawn_location_cm']=vec(loc);obs['pawn_class']=pawn.get_class().get_name();c['spawn_at_arrival']=abs(loc.x+600)<200 and abs(loc.y+3300)<200
   obs['set_actor_location_doc']=pawn.set_actor_location.__doc__
   obs['root_mobility']=str(pawn.root_component.get_editor_property('mobility'))
   obs['runtime_mesh_collision']=[{'label':a.get_actor_label(),'collision':str(a.static_mesh_component.get_collision_enabled()),'profile':str(a.static_mesh_component.get_collision_profile_name())} for a in u.GameplayStatics.get_all_actors_of_class(w,u.StaticMeshActor)]
   obs['line_trace_doc']=u.SystemLibrary.line_trace_single.__doc__
   logger_cls=u.load_class(None,'/Script/ForestDemo.ScreenDebugLogger');loggers=u.GameplayStatics.get_all_actors_of_class(w,logger_cls)
   c['native_logger_in_pie']=len(loggers)==1;obs['logger_runtime_path']=[a.get_path_name() for a in loggers]
   obs['hello_beginplay_evidence']='PIE started with the unchanged native ScreenDebugLogger actor. Baseline 7558c8f BeginPlay calls AddOnScreenDebugMessage(..., TEXT("Hello")). No replacement implementation or manual BeginPlay call.'
   runtime_report['limitations'].append('On-screen Hello text is not captured in clean scene evidence; native BeginPlay execution is supported by PIE startup and unchanged class/source, not by a separately exposed counter.')
   tests=[]
   for label,x,y,top in [('arrival_ground',-600,-3300,0),('access_ramp',1550,-800,40.38),('platform',1000,180,105)]:
    pawn.set_actor_location(u.Vector(x,y,top+180),False,True)
    hit=pawn.set_actor_location(u.Vector(x,y,top-150),sweep=True,teleport=False)
    trace=u.SystemLibrary.line_trace_single(w,u.Vector(x,y,top+180),u.Vector(x,y,top-150),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn],u.DrawDebugTrace.NONE,True)
    end=pawn.get_actor_location();blocked=end.z>top-5 and end.z<top+150
    tests.append({'site':label,'start_cm':[x,y,top+180],'requested_end_cm':[x,y,top-150],'actual_end_cm':vec(end),'sweep_result':str(hit),'line_trace':str(trace),'blocking_trace_hit':trace is not None,'blocked':blocked})
    c[label+'_runtime_blocking_sweep']=blocked
   obs['collision_sweeps']=tests
   pawn.set_actor_location(u.Vector(1000,180,160),False,True);before=pawn.get_actor_location();pawn.set_actor_location(u.Vector(700,180,160),True,False);end=pawn.get_actor_location()
   c['short_platform_movement']=end.x<before.x-250;obs['short_move']={'from':vec(before),'to':vec(end),'sweep':True}
   save_runtime();runtime_level.editor_request_end_play();runtime_state='ending';runtime_frame=0
  elif runtime_state=='ending' and runtime_frame>60:
   runtime_report['checks']['pie_ended_normally']=not runtime_level.is_in_play_in_editor()
   runtime_report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();runtime_report['elapsed_seconds']=time.time()-runtime_started;runtime_report['passed']=all(runtime_report['checks'].values());save_runtime()
   u.log('SOLMARU_RUNTIME '+json.dumps(runtime_report['checks']));u.unregister_slate_post_tick_callback(runtime_handle);after_runtime()
 except Exception:
  runtime_report['error']=traceback.format_exc();runtime_report['passed']=False;runtime_report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();runtime_report['elapsed_seconds']=time.time()-runtime_started;save_runtime();u.log_error(traceback.format_exc())
  runtime_report['checks']['runtime_script_complete']=False;runtime_level.editor_request_end_play();runtime_state='ending';runtime_frame=0
runtime_level.editor_request_begin_play();runtime_handle=u.register_slate_post_tick_callback(runtime_tick)
