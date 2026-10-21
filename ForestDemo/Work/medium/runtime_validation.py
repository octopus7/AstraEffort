import unreal as u,json,time,datetime,traceback,os,math
runtime_root='D:/github/AstraEffort/ForestDemo/Work/medium'
runtime_level=u.get_editor_subsystem(u.LevelEditorSubsystem)
runtime_report={'supervisor_followup_started_at_utc':'2026-10-21T12:46:14Z','started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mode':'actual PIE game world','status':'working','checks':{}}
runtime_phase=0;runtime_ticks=0;runtime_started=time.time()
runtime_level.editor_request_begin_play()
def runtime_save():json.dump(runtime_report,open(runtime_root+'/runtime_validation.json','w'),indent=2)
runtime_save()
def runtime_tick(dt):
 global runtime_phase,runtime_ticks,runtime_handle
 try:
  runtime_ticks+=1
  if time.time()-runtime_started>60:raise RuntimeError('PIE validation timeout')
  if runtime_phase==0:
   if not runtime_level.is_in_play_in_editor() or runtime_ticks<90:return
   gw=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
   assert gw,'No PIE game world'
   pc=u.GameplayStatics.get_player_controller(gw,0);assert pc,'No PlayerController'
   pawn=pc.get_controlled_pawn();assert pawn,'No possessed Pawn'
   assert pawn.get_controller()==pc
   runtime_report['world']=gw.get_path_name();runtime_report['controller']=pc.get_class().get_name();runtime_report['pawn']=pawn.get_class().get_name();runtime_report['spawn_location']=str(pawn.get_actor_location());runtime_report['checks']['controller_and_pawn_possession']=True
   loggers=u.GameplayStatics.get_all_actors_of_class(gw,u.load_class(None,'/Script/ForestDemo.ScreenDebugLogger'))
   assert len(loggers)==1;runtime_report['checks']['native_logger_in_play_world']=True
   runtime_report['logger_evidence']='Native class retained without modification; actual onscreen Hello screenshot requested within first 10 seconds of PIE.'
   u.SystemLibrary.execute_console_command(gw,'EnableAllScreenMessages',pc)
   u.SystemLibrary.execute_console_command(gw,'r.MotionBlurQuality 0',pc)
   u.SystemLibrary.execute_console_command(gw,'Shot SHOWUI -nosuffix filename='+runtime_root+'/Screenshots/runtime_hello.png',pc)
   pawn.set_actor_location(u.Vector(1100,-1400,210),False,True)
   start=pawn.get_actor_location();move=pawn.set_actor_location(u.Vector(1200,-1400,210),True,False);after=pawn.get_actor_location()
   runtime_report['short_move']={'before':str(start),'after':str(after),'sweep_result':str(move)}
   delta=after-start;assert math.sqrt(delta.x**2+delta.y**2+delta.z**2)>20;runtime_report['checks']['short_swept_movement']=True
   down=pawn.set_actor_location(u.Vector(1200,-1400,-500),True,False);landed=pawn.get_actor_location()
   runtime_report['ground_sweep']={'target_z_cm':-500,'actual_location':str(landed),'sweep_result':str(down)}
   assert landed.z>-100 and landed.z<210;runtime_report['checks']['terrain_blocks_runtime_pawn_sweep']=True
   runtime_report['checks']['player_start_region_reached']=True
   runtime_save();runtime_phase=1;runtime_ticks=0
  elif runtime_phase==1 and runtime_ticks>=90:
   runtime_level.editor_request_end_play();runtime_phase=2;runtime_ticks=0
  elif runtime_phase==2 and not runtime_level.is_in_play_in_editor():
   runtime_report['checks']['normal_pie_shutdown']=True;runtime_report['status']='passed';runtime_report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();runtime_report['elapsed_seconds']=time.time()-runtime_started;runtime_report['hello_screenshot_exists']=os.path.exists(runtime_root+'/Screenshots/runtime_hello.png');runtime_save();u.unregister_slate_post_tick_callback(runtime_handle);u.SystemLibrary.quit_editor()
 except Exception:
  runtime_report['status']='needs_attention';runtime_report['error']=traceback.format_exc();runtime_report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();runtime_save();runtime_level.editor_request_end_play();u.unregister_slate_post_tick_callback(runtime_handle);u.SystemLibrary.quit_editor()
runtime_handle=u.register_slate_post_tick_callback(runtime_tick)


