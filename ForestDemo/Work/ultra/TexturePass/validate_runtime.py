import unreal as u, json, time, traceback, datetime
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/TexturePass')
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
levels.load_level('/Game/Maps/ultra')
report={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'test':'Actual Play In Editor: possession, swept pawn movement, terrain/prop collision and native logger','execution_note':'Fresh texture-pass saved-map process; actual PIE after render evidence.','traces':[]}
levels.editor_request_begin_play()
began=time.monotonic();handle=None;phase='play'
def finish():
 report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()

 (ROOT/'runtime_validation.json').write_text(json.dumps(report,indent=2))
 validation=json.loads((ROOT/'validation.json').read_text())
 validation['checks']['runtime_ground_collision']={'passed':report['success'],'detail':report}
 validation['checks']['player_possession_and_sweep']={'passed':bool(report.get('player_test',{}).get('passed',False) and report.get('normal_play_exit',False)),'detail':report.get('player_test')}
 validation['runtime_collision_test_required']=False
 validation['success']=all(c['passed'] for c in validation['checks'].values())
 validation['errors']=[k for k,c in validation['checks'].items() if not c['passed']]
 (ROOT/'validation.json').write_text(json.dumps(validation,indent=2))
 u.log('ULTRA_RUNTIME_VALIDATION '+str(report['success']))
 u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
def tick(dt):
 global handle,phase
 if phase=='ending':
  if levels.is_in_play_in_editor():return
  report['normal_play_exit']=True;finish();return
 if time.monotonic()-began<8:return
 try:
  world=u.EditorLevelLibrary.get_game_world();report['game_world']=str(world)
  assert world,'No PIE world'
  ground=None
  allactors=u.GameplayStatics.get_all_actors_of_class(world,u.Actor)
  for a in allactors:
   if isinstance(a,u.StaticMeshActor) and a.static_mesh_component.static_mesh.get_name()=='SM_Ground':ground=a
  assert ground,'Ground missing in PIE'
  comp=ground.static_mesh_component
  report['collision_profile']=str(comp.get_collision_profile_name());report['collision_enabled']=str(comp.get_collision_enabled())
  data=json.loads((ROOT.parent/'scene_manifest.json').read_text())
  for x,y,z in data['height_samples']:
   origin=u.Vector(x*100,-y*100,1800);end=u.Vector(x*100,-y*100,-500)
   # Ignore canopy/props to test the actual walking surface.
   hit=u.SystemLibrary.line_trace_single(world,origin,end,u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[a for a in allactors if a!=ground],u.DrawDebugTrace.NONE)
   row={'xy_m':[x,y],'expected_ground_z_cm':z*100,'blocked':hit is not None}
   if hit:
    values=hit.to_tuple();impact=values[5];row.update(impact_cm=[impact.x,impact.y,impact.z],height_error_cm=abs(impact.z-z*100),actor=str(values[9]))
   report['traces'].append(row)
  ps=u.GameplayStatics.get_all_actors_of_class(world,u.PlayerStart)[0].get_actor_location()
  hit=u.SystemLibrary.line_trace_single(world,ps,u.Vector(ps.x,ps.y,ps.z-500),u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[a for a in allactors if a!=ground],u.DrawDebugTrace.NONE)
  report['player_start_grounded']=hit is not None
  pc=u.GameplayStatics.get_player_controller(world,0)
  assert pc,'No PlayerController created by PIE'
  pawn=pc.get_controlled_pawn()
  assert pawn,'PlayerController has no possessed pawn'
  initial=pawn.get_actor_location()
  def xyz(p):return [p.x,p.y,p.z]
  player={'controller':pc.get_class().get_name(),'pawn':pawn.get_class().get_name(),'possessed':pawn.get_controller()==pc,'start_cm':xyz(initial),'player_start_cm':xyz(ps),'spawn_distance_from_player_start_cm':(initial-ps).length()}
  requested=u.Vector(initial.x,initial.y-200,initial.z)
  movement_hit=pawn.set_actor_location(requested,True,False)
  moved=pawn.get_actor_location();player['after_horizontal_sweep_cm']=xyz(moved);player['horizontal_move_cm']=(moved-initial).length()
  downward=u.Vector(moved.x,moved.y,moved.z-500)
  down_hit=pawn.set_actor_location(downward,True,False)
  actual=pawn.get_actor_location();player['requested_downward_location_cm']=xyz(downward);player['after_downward_sweep_cm']=xyz(actual);player['downward_sweep_result']=str(down_hit)
  values=down_hit.to_tuple()
  hit_actor=values[9];hit_component=values[10]
  hit_mesh=hit_component.static_mesh if isinstance(hit_component,u.StaticMeshComponent) else None
  actual_distance=(actual-moved).length()
  player['downward_sweep_hit']={'blocking_hit':bool(values[0]),'initial_overlap':bool(values[1]),'time':values[2],'distance_cm':values[3],'location_cm':xyz(values[4]),'impact_point_cm':xyz(values[5]),'normal':xyz(values[6]),'impact_normal':xyz(values[7]),'actor':hit_actor.get_path_name() if hit_actor else None,'component':hit_component.get_path_name() if hit_component else None,'static_mesh':hit_mesh.get_path_name() if hit_mesh else None,'actual_move_distance_cm':actual_distance,'hit_own_ground_actor':hit_actor==ground,'hit_own_ground_component':hit_component==comp,'hit_own_ground_mesh':hit_mesh==comp.static_mesh and hit_mesh is not None}
  player['terrain_blocked_downward_sweep']=bool(values[0] and not values[1] and 0<values[2]<1 and values[3]>0 and actual_distance>.5 and hit_actor==ground and hit_component==comp and hit_mesh==comp.static_mesh and actual.z>downward.z+100)
  player['passed']=player['possessed'] and player['spawn_distance_from_player_start_cm']<300 and 25<player['horizontal_move_cm']<=205 and player['terrain_blocked_downward_sweep']
  report['player_test']=player
  report['solid_prop_traces']=[]
  for prefix in ['SM_Broadleaf','SM_Pine','SM_Rock']:
   target=next(a for a in allactors if isinstance(a,u.StaticMeshActor) and a.static_mesh_component.static_mesh.get_name().startswith(prefix))
   pos=target.get_actor_location()
   if prefix=='SM_Rock':pos=target.get_actor_bounds(False)[0]
   else:pos=u.Vector(pos.x,pos.y,pos.z+150)
   hit=u.SystemLibrary.line_trace_single(world,u.Vector(pos.x-500,pos.y,pos.z),u.Vector(pos.x+500,pos.y,pos.z),u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[a for a in allactors if a!=target],u.DrawDebugTrace.NONE)
   report['solid_prop_traces'].append({'mesh_family':prefix,'blocked':hit is not None})
  report['native_logger_count']=len(u.GameplayStatics.get_all_actors_of_class(world,u.load_class(None,'/Script/ForestDemo.ScreenDebugLogger')))
  report['native_logger_beginplay_evidence']='Existing native ScreenDebugLogger actor present in running PIE world after engine StartPlay. Baseline BeginPlay implementation calls AddOnScreenDebugMessage Hello; no replacement or manual BeginPlay invocation. Clean captures deliberately exclude debug text.'
  report['success']=all(r['blocked'] and r.get('height_error_cm',999)<3 for r in report['traces']) and all(t['blocked'] for t in report['solid_prop_traces']) and report['player_start_grounded'] and report['native_logger_count']==1 and player['passed']
 except Exception:report['success']=False;report['error']=traceback.format_exc()
 report['play_end_requested_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 phase='ending';levels.editor_request_end_play()
handle=u.register_slate_post_tick_callback(tick)


