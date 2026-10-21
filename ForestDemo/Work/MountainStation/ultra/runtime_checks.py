import unreal as u, datetime, traceback
def v3(v):return [v.x,v.y,v.z]
def runtime_checks(pw):
    result={'world':pw.get_path_name(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':False}
    try:
        pc=u.GameplayStatics.get_player_controller(pw,0);pawn=u.GameplayStatics.get_player_pawn(pw,0)
        assert pc and pawn,'Player controller or pawn missing'
        result.update(player_controller=pc.get_class().get_path_name(),player_pawn=pawn.get_class().get_path_name(),possessed=(pc.get_controlled_pawn()==pawn and pawn.get_controller()==pc),player_start_cm=v3(pawn.get_actor_location()))
        assert result['possessed'],'Controller/Pawn possession mismatch'
        start=pawn.get_actor_location();assert abs(start.x+2950)<100 and abs(start.y-488.46)<100,'Pawn did not spawn at arrival PlayerStart'
        loggers=u.GameplayStatics.get_all_actors_of_class(pw,u.load_class(None,'/Script/ForestDemo.ScreenDebugLogger'))
        result['native_logger_count']=len(loggers);result['native_logger_class']='/Script/ForestDemo.ScreenDebugLogger'
        assert len(loggers)==1,'Expected one baseline native logger in live game world'
        result['ramp_movement']=[]
        for x in [-2950,-2750,-2550,-2350,-2150,-1950,-1750,-1600]:
            y=max(200,500-(x+3000)*3/13)
            hit=u.SystemLibrary.line_trace_single(pw,u.Vector(x,y,2400),u.Vector(x,y,-100),u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[pawn],u.DrawDebugTrace.NONE)
            assert hit is not None,'Runtime ramp collision absent at '+str(x)
            info=hit.to_tuple();assert info[0]
            target=u.Vector(x,y,info[5].z+65)
            moved=pawn.set_actor_location(target,True,False);actual=pawn.get_actor_location()
            distance=sum((a-b)**2 for a,b in zip(v3(actual),v3(target)))**.5
            result['ramp_movement'].append({'target_cm':v3(target),'actual_cm':v3(actual),'ground_hit_cm':v3(info[5]),'ground_actor':info[9].get_name() if info[9] else None,'error_cm':distance,'sweep_result':str(moved)})
            assert distance<3,'Ramp movement sweep was blocked unexpectedly'
        # Require positive real Pawn movement from a clear start and decode
        # its own blocking HitResult. A separate trace is corroboration only.
        side_start=u.Vector(500,-800,170);side_target=u.Vector(500,-400,170)
        pawn.set_actor_location(side_start,False,True)
        root=pawn.root_component;radius=root.get_scaled_sphere_radius();profile=root.get_collision_profile_name()
        initial=u.SystemLibrary.sphere_trace_single_by_profile(pw,side_start,side_start+u.Vector(0,.1,0),radius,profile,False,[pawn],u.DrawDebugTrace.NONE)
        assert initial is None,'Platform test starts in blocking overlap'
        hit=u.SystemLibrary.sphere_trace_single_by_profile(pw,side_start,side_target,radius,profile,False,[pawn],u.DrawDebugTrace.NONE)
        assert hit is not None
        move=pawn.set_actor_location(side_target,True,False);actual=pawn.get_actor_location()
        assert move is not None,'Pawn failed to move; no blocking HitResult is available'
        h=move.to_tuple();trace=hit.to_tuple();moved=sum((a-b)**2 for a,b in zip(v3(actual),v3(side_start)))**.5
        mesh=h[10].static_mesh.get_path_name() if isinstance(h[10],u.StaticMeshComponent) else None
        result['platform_blocking_sweep']={'from_cm':v3(side_start),'target_cm':v3(side_target),'actual_cm':v3(actual),'sphere_radius_cm':radius,'profile':str(profile),'initial_start_probe':None,'actual_distance_moved_cm':moved,'blocking_hit':h[0],'initial_overlap':h[1],'hit_time':h[2],'hit_location_cm':v3(h[4]),'hit_impact_point_cm':v3(h[5]),'hit_normal':v3(h[7]),'hit_actor':h[9].get_path_name(),'hit_component':h[10].get_path_name(),'hit_static_mesh':mesh,'same_profile_trace_matches':h[9]==trace[9] and h[10]==trace[10],'blocked_before_platform':actual.y<side_target.y-1}
        assert h[0] and not h[1] and 0<h[2]<1 and moved>1 and actual.y<side_target.y-1
        assert mesh in ('/Game/MountainStation/ultra/Meshes/SM_Platform.SM_Platform','/Game/MountainStation/ultra/Meshes/SM_PlatformCoping.SM_PlatformCoping') and h[9]==trace[9] and h[10]==trace[10]
        pawn.set_actor_location(start,False,True)
        # Transient test subclass: its ReceiveBeginPlay can only be dispatched
        # when the unchanged native ScreenDebugLogger::BeginPlay calls Super.
        # No class, actor, blueprint or test asset is saved in the delivered map.
        global native_probe_called
        native_probe_called=False
        native_type=type(loggers[0])
        @u.uclass()
        class NativeLifecycleProbe(native_type):
            @u.ufunction(override=True)
            def receive_begin_play(self):
                global native_probe_called
                native_probe_called=True
                u.log('ALDER_NATIVE_LOGGER_BEGINPLAY_DISPATCHED')
        # GameplayStatics deferred-spawn helpers are Blueprint-internal and not
        # exported by this UE Python build. The development PIE cheat command
        # uses UWorld::SpawnActor and dispatches the real native lifecycle.
        probe_path=u.get_default_object(NativeLifecycleProbe).get_class().get_path_name()
        u.SystemLibrary.execute_console_command(pw,'EnableCheats',pc)
        u.SystemLibrary.execute_console_command(pw,'Summon '+probe_path,pc)
        probes=u.GameplayStatics.get_all_actors_of_class(pw,NativeLifecycleProbe)
        result['native_probe_instances']=len(probes)
        result['native_begin_play_probe_called']=native_probe_called
        result['native_begin_play_probe_note']='Transient Python subclass overrides ReceiveBeginPlay only; unchanged native ScreenDebugLogger::BeginPlay dispatches Super then its existing Hello message. The original placed native logger remains unchanged.'
        for probe in probes:probe.destroy_actor()
        assert native_probe_called,'Native logger BeginPlay did not dispatch its inherited event'
        result['passed']=True
        u.log('ALDER_RUNTIME_SWEEPS_PASSED: possessed pawn traversed ramp; platform side blocked movement')
    except Exception:result['error']=traceback.format_exc();u.log_error(result['error'])
    return result
