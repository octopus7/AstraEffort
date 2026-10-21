"""Actual PIE world, controller possession, pawn sweep, Hello viewport evidence."""
import unreal as u, time, json, traceback, hashlib
from pathlib import Path
from datetime import datetime, timezone
WORK=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh/TexturePass')
def utc():return datetime.now(timezone.utc).isoformat()
def vec(v):return [v.x,v.y,v.z]
def hit_data(hit):
 if not hit:return {'blocking':False}
 v=hit.to_tuple();actor=next((x for x in v if isinstance(x,u.Actor)),None);comp=next((x for x in v if isinstance(x,u.PrimitiveComponent)),None)
 mesh=comp.static_mesh if isinstance(comp,u.StaticMeshComponent) else None
 return {'blocking':bool(v[0]),'initial_overlap':bool(v[1]),'location_cm':vec(v[4]),'actor':actor.get_path_name() if actor else None,'actor_label':actor.get_actor_label() if actor else None,'component':comp.get_path_name() if comp else None,'mesh':mesh.get_path_name() if mesh else None}
def save():
 (WORK/'Evidence/runtime_validation.json').write_text(json.dumps(result,indent=2))
def start():
 global result,started,stage,last,handle
 started=time.time();last=started;stage='waiting_game'
 result={'texture_pass_started_at_utc':'2026-10-21T14:47:03+00:00','pie_requested_at_utc':utc(),'checks':{},'errors':[],'limitations':['DefaultPawn uses floating movement. These are real collision sweeps, not a new character controller or railway simulation.']}
 world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
 u.SystemLibrary.execute_console_command(world,'EnableAllScreenMessages')
 u.EditorLevelLibrary.set_level_viewport_camera_info(u.Vector(-3800,-300,135),u.Rotator(0,0,0))
 try:
  settings=u.get_default_object(u.LevelEditorPlaySettings)
  enum=u.PlayModeLocations
  value=next(getattr(enum,n) for n in dir(enum) if 'DEFAULT_PLAYER_START' in n)
  settings.set_editor_property('last_executed_play_mode_location',value)
  result['spawn_setting']=str(value)
 except Exception as e:result['spawn_setting_note']=str(e)
 u.get_editor_subsystem(u.LevelEditorSubsystem).editor_request_begin_play()
 handle=u.register_slate_post_tick_callback(tick);save()
def tick(dt):
 global stage,last
 try:
  now=time.time();world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
  if now-started>75:raise RuntimeError('PIE lifecycle timeout: '+stage)
  if stage=='waiting_game':
   if not world:return
   result['game_world']=world.get_path_name();result['pie_started_at_utc']=utc();result['checks']['actual_pie_world']='UEDPIE_' in world.get_path_name()
   last=now;stage='hello';return
  if stage=='hello':
   if now-last<1.5:return
   u.SystemLibrary.execute_console_command(world,'Shot SHOWUI filename="'+str(WORK/'Evidence/runtime_hello.png').replace('\\','/')+'" -nosuffix')
   result['hello_viewport_screenshot_requested_at_utc']=utc();last=now;stage='checks';return
  if stage=='checks':
   if now-last<1.5:return
   pc=u.GameplayStatics.get_player_controller(world,0);pawn=pc.get_controlled_pawn() if pc else None
   result['checks']['controller_exists']=pc is not None;result['checks']['pawn_exists']=pawn is not None
   if not pawn:raise RuntimeError('No possessed player pawn in actual PIE')
   result['controller']=pc.get_path_name();result['pawn']=pawn.get_path_name();result['pawn_class']=pawn.get_class().get_path_name();result['initial_location_cm']=vec(pawn.get_actor_location())
   result['checks']['controller_possesses_pawn']=pawn.get_controller()==pc
   starts=u.GameplayStatics.get_all_actors_of_class(world,u.PlayerStart)
   result['player_start_locations_cm']=[vec(a.get_actor_location()) for a in starts]
   result['checks']['spawn_at_player_start']=any((pawn.get_actor_location()-a.get_actor_location()).length()<5 for a in starts)
   logger_class=u.load_class(None,'/Script/ForestDemo.ScreenDebugLogger');loggers=u.GameplayStatics.get_all_actors_of_class(world,logger_class)
   result['native_hello_actors']=[a.get_path_name() for a in loggers];result['checks']['native_hello_in_game_world']=len(loggers)==1
   source=Path(u.Paths.project_dir())/'Source/ForestDemo/ScreenDebugLogger.cpp'
   result['hello_source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
   result['hello_implementation']='Unmodified baseline native BeginPlay adds green Hello for 10 seconds. Separate runtime_hello.png is requested during that interval; visual verification recorded separately.'
   original=pawn.get_actor_location();target=original+u.Vector(100,0,0)
   move=pawn.set_actor_location(target,True,False)
   result['short_move']={'from':vec(original),'target':vec(target),'reached':vec(pawn.get_actor_location()),'sweep':hit_data(move)}
   result['checks']['short_move_100cm']=(pawn.get_actor_location()-target).length()<1
   result['floor_traces']=[];result['blocking_pawn_sweeps']=[]
   for name,x,y,lo,hi in [('approach',-3800,-300,20,45),('terrain',-4000,-1800,15,80),('ramp_middle',-3200,-600,71,76),('platform',-2200,-1250,120,128)]:
    h=u.SystemLibrary.line_trace_single(world,u.Vector(x,y,450),u.Vector(x,y,-300),u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[pawn],u.DrawDebugTrace.NONE)
    data=hit_data(h);data['name']=name;data['height_correct']=data['blocking'] and lo<=data['location_cm'][2]<=hi;result['floor_traces'].append(data)
    pawn.set_actor_location(u.Vector(x,y,450),False,True)
    sweep_start=pawn.get_actor_location();sweep=pawn.set_actor_location(u.Vector(x,y,-150),True,False);d=hit_data(sweep);d['movement_start_cm']=vec(sweep_start);d['positive_distance_cm']=(pawn.get_actor_location()-sweep_start).length();d['name']=name;d['pawn_stopped_at_cm']=vec(pawn.get_actor_location());d['same_ground_actor_as_trace']=d.get('actor')==data.get('actor');d['same_component_mesh_as_trace']=d.get('component')==data.get('component') and d.get('mesh')==data.get('mesh');result['blocking_pawn_sweeps'].append(d)
   result['checks']['runtime_floor_heights']=all(x['height_correct'] for x in result['floor_traces'])
   expected_meshes={'approach':'SM_Paths','terrain':'SM_Terrain','ramp_middle':'SM_Platform','platform':'SM_Platform'}
   result['checks']['exact_expected_ground_meshes']=all(x['mesh'].endswith('/'+expected_meshes[x['name']]+'.'+expected_meshes[x['name']]) for x in result['blocking_pawn_sweeps'])
   result['checks']['runtime_pawn_sweeps_blocked']=all(x['blocking'] and not x['initial_overlap'] and x['positive_distance_cm']>1 and x['same_ground_actor_as_trace'] and x['same_component_mesh_as_trace'] and bool(x['component']) and bool(x['mesh']) for x in result['blocking_pawn_sweeps'])
   pawn.set_actor_location(original,False,True)
   result['checks_completed_at_utc']=utc();u.get_editor_subsystem(u.LevelEditorSubsystem).editor_request_end_play();stage='ending';last=now;save();return
  if stage=='ending':
   if world is not None:return
   result['checks']['normal_pie_end']=True;result['finished_at_utc']=utc();result['pie_execution_seconds']=now-started
   result['errors']=[k for k,v in result['checks'].items() if not v];result['success']=not result['errors'];save()
   print('ALDER_RUNTIME_VALIDATION',result['success'],result['checks'])
   u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
 except Exception:
  result['exception']=traceback.format_exc();result['success']=False;result['finished_at_utc']=utc();result['pie_execution_seconds']=time.time()-started;save();u.log_error(result['exception'])
  u.get_editor_subsystem(u.LevelEditorSubsystem).editor_request_end_play();u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
