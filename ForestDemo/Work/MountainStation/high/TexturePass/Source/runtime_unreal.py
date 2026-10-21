import unreal as u,json,time,datetime,traceback
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high/TexturePass';runtime_level=u.get_editor_subsystem(u.LevelEditorSubsystem)
runtime_start=time.time();runtime_frame=0;runtime_state='start';runtime_report={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':{},'sweeps':[]}
def vec(v):return [v.x,v.y,v.z]
def hit_details(hit):
 if hit is None:return {'hit':False}
 t=hit.to_tuple()
 if len(t)!=18:raise RuntimeError('Unexpected HitResult native break layout '+str(t))
 comp=t[10];mesh=comp.static_mesh if isinstance(comp,u.StaticMeshComponent) else None
 return {'hit_result_returned':True,'blocking_hit':bool(t[0]),'initial_overlap':bool(t[1]),'time':t[2],'distance_cm':t[3],'location_cm':vec(t[4]),'impact_point_cm':vec(t[5]),'normal':vec(t[6]),'actor':t[9].get_path_name() if t[9] else None,'actor_label':t[9].get_actor_label() if t[9] else None,'component':comp.get_path_name() if comp else None,'mesh':mesh.get_path_name() if mesh else None,'native_break_field_count':len(t)}
def rtick(dt):
 global runtime_frame,runtime_state,runtime_handle
 runtime_frame+=1
 try:
  if runtime_state=='start' and runtime_frame>120:
   world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
   if not world:
    if runtime_frame<600:return
    raise RuntimeError('PIE world absent')
   pc=u.GameplayStatics.get_player_controller(world,0);pawn=u.GameplayStatics.get_player_pawn(world,0);c=runtime_report['checks']
   c['pie_world']=runtime_level.is_in_play_in_editor();c['controller_and_pawn']=bool(pc and pawn);assert pc and pawn
   c['possession']=pawn.get_controller()==pc;start=pawn.get_actor_location();runtime_report['start_location_cm']=vec(start);c['arrival_start']=abs(start.x+600)<10 and abs(start.y+3300)<10
   for label,x,y,z,expected in [('arrival',-600,-3300,0,['SM_Terrain','SM_GroundPaths']),('ramp',1550,-800,40.38,['SM_Platform']),('platform',1000,180,105,['SM_Platform'])]:
    a=u.Vector(x,y,z+180);b=u.Vector(x,y,z-150);pawn.set_actor_location(a,False,True);hit=pawn.set_actor_location(b,True,False);end=pawn.get_actor_location();details=hit_details(hit);moved=(end-a).length()
    valid=details.get('blocking_hit',False) and not details.get('initial_overlap',True) and moved>1 and details.get('distance_cm',0)>1 and any(details.get('mesh','').endswith('.'+n) for n in expected)
    runtime_report['sweeps'].append({'site':label,'start_cm':vec(a),'requested_end_cm':vec(b),'actual_end_cm':vec(end),'actual_travel_cm':moved,'hit_result':details,'passed':valid});c[label+'_blocking_sweep']=valid
   pawn.set_actor_location(u.Vector(1000,180,160),False,True);a=pawn.get_actor_location();h=pawn.set_actor_location(u.Vector(700,180,160),True,False);b=pawn.get_actor_location();runtime_report['short_movement']={'start':vec(a),'end':vec(b),'travel_cm':(b-a).length(),'hit_result':hit_details(h)};c['short_movement']=(b-a).length()>290
   cls=u.load_class(None,'/Script/ForestDemo.ScreenDebugLogger');ls=u.GameplayStatics.get_all_actors_of_class(world,cls);c['native_logger_in_pie']=len(ls)==1
   runtime_report['hello_observation']='Unchanged native class instance observed in active PIE; baseline source/DLL retained. No separate observation of on-screen Hello or instrumented BeginPlay counter is claimed.'
   runtime_level.editor_request_end_play();runtime_state='end';runtime_frame=0
  elif runtime_state=='end' and runtime_frame>60:
   runtime_report['checks']['normal_pie_end']=not runtime_level.is_in_play_in_editor();runtime_report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();runtime_report['elapsed_seconds']=time.time()-runtime_start;runtime_report['passed']=all(runtime_report['checks'].values())
   json.dump(runtime_report,open(W+'/runtime_validation.json','w'),indent=2);u.log('TEXTUREPASS_RUNTIME '+json.dumps(runtime_report['checks']));u.unregister_slate_post_tick_callback(runtime_handle)
   exec(compile(open(W+'/Source/capture_unreal.py').read(),W+'/Source/capture_unreal.py','exec'),globals())
 except Exception:
  runtime_report['error']=traceback.format_exc();runtime_report['passed']=False;json.dump(runtime_report,open(W+'/runtime_validation.json','w'),indent=2);u.log_error(traceback.format_exc());runtime_level.editor_request_end_play();u.unregister_slate_post_tick_callback(runtime_handle);u.SystemLibrary.quit_editor()
runtime_level.editor_request_begin_play();runtime_handle=u.register_slate_post_tick_callback(rtick)

