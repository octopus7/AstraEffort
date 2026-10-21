import unreal as u,json,time,datetime,traceback
from pathlib import Path
R=Path('D:/github/AstraEffort/ForestDemo/Work/high')
ls=u.get_editor_subsystem(u.LevelEditorSubsystem);es=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert ls.load_level('/Game/Maps/high')
ls.editor_set_viewport_realtime(True)
u.EditorPythonScripting.set_keep_python_script_alive(True)
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
report={'supplement_started_at_utc':'2026-10-21T12:41:24+00:00','runtime_script_started_at_utc':now(),'map':'/Game/Maps/high','map_modified':False,'checks':{},'status':'working'}
state={'phase':'request','start':time.monotonic(),'phase_time':time.monotonic()}
def vec(v):return [v.x,v.y,v.z]
def write():
 (R/'runtime_validation.json').write_text(json.dumps(report,indent=2))
 u.log('HIGH_RUNTIME '+json.dumps(report))
ls.editor_request_begin_play()
def tick(dt):
 try:
  if time.monotonic()-state['start']>85:raise RuntimeError('PIE/runtime validation timed out')
  world=es.get_game_world()
  if state['phase']=='request':
   if not world or not ls.is_in_play_in_editor():return
   pc=u.GameplayStatics.get_player_controller(world,0)
   if not pc or not pc.get_controlled_pawn():return
   pawn=pc.get_controlled_pawn();state['world']=world;state['pawn']=pawn;state['pc']=pc
   actors=u.GameplayStatics.get_all_actors_of_class(world,u.Actor)
   starts=[a for a in actors if isinstance(a,u.PlayerStart)]
   logs=[a for a in actors if a.get_class().get_name()=='ScreenDebugLogger']
   terrain=next(a for a in actors if a.get_actor_label()=='Terrain')
   assert len(starts)==1 and len(logs)==1
   pos=pawn.get_actor_location();sp=starts[0].get_actor_location();delta=(pos-sp).length()
   assert delta<100,'Pawn was not spawned at PlayerStart: '+str(delta)
   assert pawn.get_controller()==pc,'Pawn not possessed'
   report['checks'].update({'actual_pie_world':world.get_path_name(),'pie_active':True,'player_controller_class':pc.get_class().get_name(),'pawn_class':pawn.get_class().get_name(),'pawn_spawn_location':vec(pos),'player_start_location':vec(sp),'spawn_distance_cm':delta,'pawn_possessed_by_player_0':True,'runtime_logger_count':len(logs),'runtime_logger_path':logs[0].get_path_name(),'logger_seconds_since_creation':logs[0].get_game_time_since_creation()})
   state['original']=pos
   hit=u.SystemLibrary.line_trace_single(world,u.Vector(pos.x,pos.y,pos.z+1000),u.Vector(pos.x,pos.y,-900),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[a for a in actors if a!=terrain],u.DrawDebugTrace.NONE,True).to_tuple()
   assert hit[0];ground=hit[4]
   result=pawn.set_actor_location(u.Vector(pos.x,pos.y,ground.z-200),True,False)
   after=pawn.get_actor_location();parts=result.to_tuple()
   assert parts[0] and after.z>ground.z+10,'Pawn sweep did not block on terrain'
   report['checks']['runtime_ground_collision']={'ground':vec(ground),'sweep_blocking_hit':parts[0],'pawn_after_downward_sweep':vec(after),'pawn_ground_clearance_cm':after.z-ground.z}
   pawn.set_actor_location(pos,False,True)
   u.SystemLibrary.execute_console_command(world,'EnableAllScreenMessages')
   u.SystemLibrary.execute_console_command(world,'Shot SHOWUI filename="'+str(R/'Screenshots/runtime_hello.png')+'" -nosuffix')
   state['phase']='move';state['phase_time']=time.monotonic();write()
  elif state['phase']=='move':
   pawn=state['pawn'];pawn.add_movement_input(u.Vector(0,1,0),1.0,True)
   if time.monotonic()-state['phase_time']<2:return
   pos=pawn.get_actor_location();distance=(pos-state['original']).length();assert distance>30,'Pawn movement did not advance'
   report['checks']['movement']={'mode':'default pawn movement input, +Y for 2 wall seconds','from':vec(state['original']),'to':vec(pos),'distance_cm':distance,'note':'DefaultPawn uses floating movement; no custom walking character was added.'}
   pawn.set_actor_location(state['original'],False,True)
   ls.editor_request_end_play();state['phase']='end';state['phase_time']=time.monotonic()
  elif state['phase']=='end':
   if ls.is_in_play_in_editor():return
   report['checks']['pie_ended']=True
   u.SystemLibrary.execute_console_command(es.get_editor_world(),'Automation RunTests ForestDemo.ScreenDebugLogger.HelloOnBeginPlay')
   report['checks']['native_hello_automation_test_requested']='ForestDemo.ScreenDebugLogger.HelloOnBeginPlay'
   state['phase']='automation';state['phase_time']=time.monotonic()
  elif state['phase']=='automation':
   if time.monotonic()-state['phase_time']<18:return
   report['runtime_script_finished_at_utc']=now();report['status']='runtime_checks_passed_pending_native_log_review';write()
   u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False)
 except Exception:
  report['status']='failed';report['error']=traceback.format_exc();report['runtime_script_finished_at_utc']=now();write()
  if ls.is_in_play_in_editor():ls.editor_request_end_play()
  u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False)
handle=u.register_slate_post_tick_callback(tick)

