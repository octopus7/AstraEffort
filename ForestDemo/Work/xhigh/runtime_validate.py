"""Actual PIE world, possession and swept pawn collision; no saved map mutation."""
import unreal as u,json,time,datetime,traceback,os,re
RP_ROOT='D:/github/AstraEffort/ForestDemo/Work/xhigh'
RP_LES=u.get_editor_subsystem(u.LevelEditorSubsystem)
RP_UES=u.get_editor_subsystem(u.UnrealEditorSubsystem)
RP_REPORT={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'map':'/Game/Maps/xhigh','mode':'PlayInEditor','checks':{},'errors':[]}
RP_STAGE='start';RP_DEADLINE=time.monotonic()+45;RP_HANDLE=None;RP_GW=None;RP_PAWN=None
RP_LOG_MATCH=re.search(r'-abslog=(?:"([^"]+)"|(\S+))',u.SystemLibrary.get_command_line(),re.IGNORECASE)
RP_LOG=(RP_LOG_MATCH.group(1) or RP_LOG_MATCH.group(2)) if RP_LOG_MATCH else ''
RP_LOG_OFFSET=0
def rp_vec(p):return [p.x,p.y,p.z]
def rp_dist(a,b):return ((a.x-b.x)**2+(a.y-b.y)**2+(a.z-b.z)**2)**.5
def rp_check(k,v):
 RP_REPORT['checks'][k]=bool(v)
 if not v:RP_REPORT['errors'].append(k)
def rp_finish():
 global RP_HANDLE
 RP_REPORT['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 RP_REPORT['elapsed_seconds']=(datetime.datetime.fromisoformat(RP_REPORT['finished_at_utc'])-datetime.datetime.fromisoformat(RP_REPORT['started_at_utc'])).total_seconds()
 RP_REPORT['passed']=not RP_REPORT['errors']
 json.dump(RP_REPORT,open(RP_ROOT+'/runtime_validation.json','w'),indent=2)
 u.unregister_slate_post_tick_callback(RP_HANDLE)
 u.log('XHIGH_RUNTIME_VALIDATION '+json.dumps(RP_REPORT))
 u.SystemLibrary.quit_editor()
def rp_tick(dt):
 global RP_STAGE,RP_DEADLINE,RP_GW,RP_PAWN,RP_LOG_OFFSET
 try:
  if time.monotonic()>RP_DEADLINE:
   RP_REPORT['errors'].append('PIE timeout at '+RP_STAGE)
   RP_LES.editor_request_end_play();rp_finish();return
  if RP_STAGE=='start':
   RP_GW=RP_UES.get_game_world()
   if not RP_GW:return
   pc=u.GameplayStatics.get_player_controller(RP_GW,0)
   if not pc:return
   RP_PAWN=pc.get_controlled_pawn()
   if not RP_PAWN:return
   rp_check('actual_pie_world',RP_LES.is_in_play_in_editor() and 'UEDPIE_' in RP_GW.get_path_name())
   rp_check('player_controller_created',pc is not None);rp_check('pawn_spawned_and_possessed',RP_PAWN.get_controller()==pc)
   RP_REPORT['world']=RP_GW.get_path_name();RP_REPORT['controller_class']=pc.get_class().get_path_name();RP_REPORT['pawn_class']=RP_PAWN.get_class().get_path_name()
   starts=u.GameplayStatics.get_all_actors_of_class(RP_GW,u.PlayerStart);rp_check('runtime_player_start',len(starts)==1)
   spawn=RP_PAWN.get_actor_location();start=starts[0].get_actor_location()
   RP_REPORT['spawn_cm']=rp_vec(spawn);RP_REPORT['player_start_cm']=rp_vec(start)
   rp_check('spawn_matches_player_start',rp_dist(spawn,start)<150)
   logger_cls=u.load_class(None,'/Script/ForestDemo.ScreenDebugLogger');loggers=u.GameplayStatics.get_all_actors_of_class(RP_GW,logger_cls)
   rp_check('baseline_logger_exists_in_play_world',len(loggers)==1)
   RP_REPORT['hello_evidence']='Baseline native actor in actual PIE. The existing BeginPlay calls AddOnScreenDebugMessage(Hello, 10 seconds). runtime_hello.png requested immediately after pawn possession; direct visual inspection records whether Hello is visible.'
   RP_STAGE='warm';RP_DEADLINE=time.monotonic()+25;RP_REPORT['possession_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();RP_REPORT['test_after_monotonic']=time.monotonic()+1.5
   return
  if RP_STAGE=='warm':
   if time.monotonic()<RP_REPORT['test_after_monotonic']:return
   u.SystemLibrary.execute_console_command(RP_GW,'Shot filename="'+RP_ROOT+'/Screenshots/runtime_hello.png" -nosuffix',u.GameplayStatics.get_player_controller(RP_GW,0))
   RP_STAGE='check';RP_REPORT['test_after_monotonic']=time.monotonic()+1.5;return
  if RP_STAGE=='check':
   if time.monotonic()<RP_REPORT['test_after_monotonic']:return
   terrain=next(a for a in u.GameplayStatics.get_all_actors_of_class(RP_GW,u.StaticMeshActor) if a.static_mesh_component.static_mesh.get_path_name().endswith('SM_Terrain.SM_Terrain'))
   sample=json.load(open(RP_ROOT+'/scene_manifest.json'))['terrain_samples'][0];x=sample['x_m']*100;y=sample['y_m']*100;z=sample['height_m']*100
   trace=terrain.static_mesh_component.line_trace_component(u.Vector(x,y,2000),u.Vector(x,y,-1000),True,False,False)
   rp_check('runtime_terrain_trace_blocks',trace is not None)
   if trace:RP_REPORT['runtime_ground_hit_cm']=rp_vec(trace[0]);rp_check('runtime_ground_matches_source',abs(trace[0].z-z)<5)
   RP_PAWN.set_actor_location(u.Vector(x,y,z+120),False,True)
   desired=u.Vector(x,y,z-200);RP_PAWN.set_actor_location(desired,True,False);stopped=RP_PAWN.get_actor_location()
   RP_REPORT['downward_sweep']={'requested_cm':rp_vec(desired),'actual_cm':rp_vec(stopped),'ground_z_cm':z}
   rp_check('pawn_sweep_blocked_by_ground',stopped.z>z+10 and stopped.z<z+100 and rp_dist(stopped,desired)>200)
   RP_PAWN.set_actor_location(u.Vector(x,y,z+130),False,True);before=RP_PAWN.get_actor_location()
   RP_PAWN.set_actor_location(u.Vector(x,y+100,z+130),True,False);after=RP_PAWN.get_actor_location()
   RP_REPORT['short_path_sweep']={'before_cm':rp_vec(before),'after_cm':rp_vec(after),'distance_cm':rp_dist(before,after)}
   rp_check('short_path_movement_succeeds',rp_dist(before,after)>90)
   RP_PAWN.set_actor_location(u.Vector(*RP_REPORT['spawn_cm']),False,True)
   RP_LES.editor_request_end_play();RP_STAGE='ending';RP_DEADLINE=time.monotonic()+20;return
  if RP_STAGE=='ending':
   if RP_LES.is_in_play_in_editor():return
   rp_check('normal_pie_shutdown',RP_UES.get_game_world() is None)
   RP_REPORT.pop('test_after_monotonic',None)
   RP_LOG_OFFSET=len(open(RP_LOG,encoding='utf-8',errors='replace').read()) if os.path.isfile(RP_LOG) else 0
   RP_REPORT['native_hello_test_name']='ForestDemo.ScreenDebugLogger.HelloOnBeginPlay';RP_REPORT['native_test_log']=RP_LOG
   u.SystemLibrary.execute_console_command(RP_UES.get_editor_world(),'Automation RunTests ForestDemo.ScreenDebugLogger.HelloOnBeginPlay')
   RP_STAGE='native_test';RP_DEADLINE=time.monotonic()+45;return
  if RP_STAGE=='native_test':
   if not os.path.isfile(RP_LOG):return
   txt=open(RP_LOG,encoding='utf-8',errors='replace').read()[RP_LOG_OFFSET:]
   lines=[line for line in txt.splitlines() if 'Test Completed' in line and 'HelloOnBeginPlay' in line]
   if not lines:return
   RP_REPORT['native_hello_test_result']=lines[-1]
   rp_check('baseline_native_hello_beginplay_test','Success' in lines[-1]);rp_finish()
 except Exception:
  RP_REPORT['errors'].append(traceback.format_exc());u.log_error(traceback.format_exc())
  if RP_STAGE=='ending':rp_finish()
  else:RP_LES.editor_request_end_play();RP_STAGE='ending';RP_DEADLINE=time.monotonic()+20
RP_LES.editor_request_begin_play()
RP_HANDLE=u.register_slate_post_tick_callback(rp_tick)
u.log('XHIGH_RUNTIME_BEGIN_REQUESTED')
