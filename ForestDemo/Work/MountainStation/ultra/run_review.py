import unreal, traceback, json, time, datetime
root=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra'
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/Maps/MountainStation_ultra')
review_world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
def terrain_probe():
    h=unreal.SystemLibrary.line_trace_single(review_world,unreal.Vector(2100,-420,2500),unreal.Vector(2100,-420,-1000),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],unreal.DrawDebugTrace.NONE)
    hc=unreal.SystemLibrary.line_trace_single(review_world,unreal.Vector(2100,-420,2500),unreal.Vector(2100,-420,-1000),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],unreal.DrawDebugTrace.NONE)
    result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hit':str(h),'present':h is not None,'complex_trace':str(hc)}
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label()=='Terrain':
            c=actor.static_mesh_component;sm=c.static_mesh;bs=sm.get_editor_property('body_setup');ss=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
            count=sm.get_num_sections(0)
            result['terrain']={'profile':str(c.get_collision_profile_name()),'enabled':str(c.get_collision_enabled()),'complexity':str(bs.get_editor_property('collision_trace_flag')),'scale':str(actor.get_actor_scale3d()),'section_count':count,'section_material_slots':[ss.get_lod_material_slot(sm,0,i) for i in range(count)],'section_collision':[ss.is_section_collision_enabled(sm,0,i) for i in range(count)]}
    return result
readiness={'immediate_after_load':terrain_probe()}
review_started=time.monotonic()
def review_tick(dt):
    if time.monotonic()-review_started<10:return
    unreal.unregister_slate_post_tick_callback(review_handle)
    try:
        readiness['after_10_second_world_ticks']=terrain_probe()
        with open(root+'/collision_readiness.json','w') as f:json.dump(readiness,f,indent=2)
        globals()['VALIDATE_RELOAD']=False
        exec(compile(open(root+'/validate_unreal.py').read(),root+'/validate_unreal.py','exec'),globals())
        exec(compile(open(root+'/capture_unreal.py').read(),root+'/capture_unreal.py','exec'),globals())
    except Exception:
        with open(root+'/review_error.json','w') as f:json.dump({'traceback':traceback.format_exc()},f,indent=2)
        unreal.SystemLibrary.quit_editor()
review_handle=unreal.register_slate_post_tick_callback(review_tick)
