import unreal as u,json,datetime,time,traceback,math,hashlib
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra')
OUT=ROOT/'BlockingSupplement'
MAP='/Game/Maps/MountainStation_ultra'
u.EditorPythonScripting.set_keep_python_script_alive(True)
levels=u.get_editor_subsystem(u.LevelEditorSubsystem);assert levels.load_level(MAP)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def v3(v):return [v.x,v.y,v.z]
def distance(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(v3(a),v3(b))))
def path(o):return o.get_path_name() if o else None
def hit_record(h):
    if h is None:return None
    t=h.to_tuple();assert len(t)==18,'Unexpected BreakHitResult tuple length: '+str(len(t))
    component=t[10];sm=component.static_mesh if isinstance(component,u.StaticMeshComponent) else None
    return {'blocking_hit':t[0],'initial_overlap':t[1],'time':t[2],'distance_cm':t[3],'location_cm':v3(t[4]),'impact_point_cm':v3(t[5]),'normal':v3(t[6]),'impact_normal':v3(t[7]),'physical_material':path(t[8]),'actor':path(t[9]),'component':path(component),'static_mesh':path(sm),'hit_bone_name':str(t[11]),'bone_name':str(t[12]),'hit_item':t[13],'element_index':t[14],'face_index':t[15],'trace_start_cm':v3(t[16]),'trace_end_cm':v3(t[17])}
result={'started_at_utc':utc(),'passed':False,'map':MAP,'geometry_saved':False,'hit_tuple_fields':['blocking_hit','initial_overlap','time','distance','location','impact_point','normal','impact_normal','physical_material','hit_actor','hit_component','hit_bone_name','bone_name','hit_item','element_index','face_index','trace_start','trace_end'],'mapping_basis':'Installed UE 5.7 GameplayStatics.h BreakHitResult declaration, Actor.cpp K2_SetActorLocation implementation, and live Python HitResult.to_tuple documentation','live_api_docs':{'hit_tuple':u.HitResult.to_tuple.__doc__,'set_actor_location':u.Actor.set_actor_location.__doc__},'tests':[]}
def save():(OUT/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
state={'phase':'warmup','since':time.monotonic(),'start':time.monotonic()}
terrain_samples=[]
def inspect_terrain():
    sm=u.load_asset('/Game/MountainStation/ultra/Meshes/SM_Terrain');ss=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    terrain=next(a for a in actors if isinstance(a,u.StaticMeshActor) and a.static_mesh_component.static_mesh==sm)
    transform=terrain.get_actor_transform()
    info={'mesh':sm.get_path_name(),'lod':0,'num_sections':sm.get_num_sections(0),'material_slots':[str(s.material_slot_name) for s in sm.static_materials],'sections':[]}
    result['terrain_lod0']=info
    for i in range(info['num_sections']):
        slot=ss.get_lod_material_slot(sm,0,i)
        geometry=u.ProceduralMeshLibrary.get_section_from_static_mesh(sm,0,i)
        vertices,indices=geometry[0],geometry[1]
        section={'index':i,'material_slot':slot,'material':path(sm.get_material(slot)),'collision_enabled':ss.is_section_collision_enabled(sm,0,i),'vertices':len(vertices),'triangles':len(indices)//3}
        info['sections'].append(section)
        assert section['collision_enabled'],'Actual Terrain section has collision disabled: '+str(i)
        # Read actual imported LOD0 triangle vertices, selecting a centroid in
        # open southern terrain. A true slot-1 section, if present, is tested too.
        choices=[]
        for k in range(0,len(indices),3):
            tri=[u.MathLibrary.transform_location(transform,vertices[indices[k+j]]) for j in range(3)]
            center=u.Vector(sum(p.x for p in tri)/3,sum(p.y for p in tri)/3,sum(p.z for p in tri)/3)
            choices.append(((center.x-300)**2+(center.y+3000)**2,k//3,tri,center))
        candidates=[]
        for _,triangle,tri,center in sorted(choices,key=lambda x:x[0])[:24]:
            candidates.append({'section':i,'material_slot':slot,'section_triangle_index':triangle,'vertex_indices':[int(indices[triangle*3+j]) for j in range(3)],'vertices_world_cm':[v3(p) for p in tri],'barycentric':[1/3,1/3,1/3],'centroid_world_cm':v3(center),'basis':'Actual UE LOD0 index and position buffers via ProceduralMeshLibrary; transformed by the placed Terrain actor'})
        section['triangle_candidates']=candidates;terrain_samples.append(candidates)
    info['slot1_triangle_count']=sum(s['triangles'] for s in info['sections'] if s['material_slot']==1)
    info['slot1_note']='No slot-1 faces exist in final imported LOD0; final presentation refinement assigned every terrain face to Meadow slot 0.' if info['slot1_triangle_count']==0 else 'Slot 1 exists and its selected triangle is tested by actual Pawn downward sweep.'
    save()
def test_move(pw,pawn,label,start,target,expected_mesh,sample=None):
    root=pawn.root_component;radius=root.get_scaled_sphere_radius();channel=root.get_collision_object_type();profile=root.get_collision_profile_name()
    pawn.set_actor_location(start,False,True);actual_start=pawn.get_actor_location()
    rec={'name':label,'requested_start_cm':v3(start),'actual_start_cm':v3(actual_start),'requested_target_cm':v3(target),'root_component':path(root),'root_class':root.get_class().get_path_name(),'sphere_radius_cm':radius,'collision_object_channel':str(channel),'profile':str(root.get_collision_profile_name()),'source_triangle':sample}
    result['tests'].append(rec)
    assert distance(start,actual_start)<.01
    direction=(target-start)/distance(start,target)
    initial=u.SystemLibrary.sphere_trace_single_by_profile(pw,start,start+direction*.1,radius,profile,False,[pawn],u.DrawDebugTrace.NONE)
    rec['start_probe']=hit_record(initial);assert initial is None,'Start sphere is blocked/overlapping'
    h=u.SystemLibrary.sphere_trace_single_by_profile(pw,start,target,radius,profile,False,[pawn],u.DrawDebugTrace.NONE)
    rec['same_shape_same_channel_trace']=hit_record(h)
    assert h is not None and rec['same_shape_same_channel_trace']['blocking_hit'] and not rec['same_shape_same_channel_trace']['initial_overlap']
    moved=pawn.set_actor_location(target,True,False);actual=pawn.get_actor_location()
    rec.update(movement_hit=hit_record(moved),actual_end_cm=v3(actual),actual_distance_moved_cm=distance(actual_start,actual),remaining_distance_to_target_cm=distance(actual,target))
    assert rec['actual_distance_moved_cm']>1,'Pawn did not make a positive movement'
    assert rec['remaining_distance_to_target_cm']>1,'Pawn reached target through intended blocker'
    assert moved is not None,'Partial Pawn movement must expose its actual HitResult'
    mh=rec['movement_hit'];th=rec['same_shape_same_channel_trace']
    assert mh['blocking_hit'] and not mh['initial_overlap'],'Pawn hit not a non-overlapping blocking sweep'
    allowed=[expected_mesh] if isinstance(expected_mesh,str) else expected_mesh
    rec['expected_platform_or_terrain_meshes']=allowed
    assert mh['static_mesh'] in allowed,'Unexpected actual blocking mesh '+str(mh['static_mesh'])
    assert mh['actor']==th['actor'] and mh['component']==th['component'],'Trace and actual movement hit different components'
    assert 0<mh['time']<1
    if sample is not None:
        a,b,c=sample['vertices_world_cm'];p=mh['impact_point_cm']
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        wa=((b[1]-c[1])*(p[0]-c[0])+(c[0]-b[0])*(p[1]-c[1]))/den
        wb=((c[1]-a[1])*(p[0]-c[0])+(a[0]-c[0])*(p[1]-c[1]))/den
        bary=[wa,wb,1-wa-wb]
        rec['actual_impact_xy_barycentric_in_selected_triangle']=bary
        assert min(bary)>.05,'Actual terrain contact was not safely inside the selected triangle'
    rec['passed']=True;save()
def play_checks():
    worlds=u.EditorLevelLibrary.get_pie_worlds(False);assert len(worlds)==1
    pw=worlds[0];pc=u.GameplayStatics.get_player_controller(pw,0);pawn=u.GameplayStatics.get_player_pawn(pw,0)
    result.update(world=pw.get_path_name(),player_controller=path(pc),player_pawn=path(pawn),possessed=pc.get_controlled_pawn()==pawn and pawn.get_controller()==pc)
    assert result['possessed'];initial=pawn.get_actor_location()
    result['candidate_path_queries']=[];errors=[]
    def choose(label,options,expected):
        for start,target,sample in options:
            h=u.SystemLibrary.sphere_trace_single_by_profile(pw,start,target,pawn.root_component.get_scaled_sphere_radius(),pawn.root_component.get_collision_profile_name(),False,[pawn],u.DrawDebugTrace.NONE)
            info=hit_record(h);result['candidate_path_queries'].append({'test':label,'start_cm':v3(start),'target_cm':v3(target),'hit':info})
            if info and info['blocking_hit'] and not info['initial_overlap'] and info['static_mesh'] in expected:return start,target,sample
        raise AssertionError('No unobstructed candidate path reaches intended mesh: '+label)
    def attempt(label,options,expected):
        try:
            a,b,sample=choose(label,options,expected)
            if sample is not None:result['terrain_lod0']['sections'][sample['section']]['test_triangle']=sample
            test_move(pw,pawn,label,a,b,expected,sample)
        except Exception:errors.append({'test':label,'error':traceback.format_exc()})
    options=[(u.Vector(x,y,800),u.Vector(x,y,40),None) for x in [300,800,1100,-300,-500,0] for y in [-300,-400,-200,100]]
    attempt('platform_downward',options,['/Game/MountainStation/ultra/Meshes/SM_Platform.SM_Platform'])
    for candidates in terrain_samples:
        options=[]
        for sample in candidates:
            p=u.Vector(*sample['centroid_world_cm']);options.append((p+u.Vector(0,0,400),p-u.Vector(0,0,100),sample))
        attempt('terrain_section_'+str(candidates[0]['section']),options,['/Game/MountainStation/ultra/Meshes/SM_Terrain.SM_Terrain'])
    attempt('platform_front_side',[(u.Vector(500,-800,170),u.Vector(500,-400,170),None)],['/Game/MountainStation/ultra/Meshes/SM_Platform.SM_Platform','/Game/MountainStation/ultra/Meshes/SM_PlatformCoping.SM_PlatformCoping'])
    pawn.set_actor_location(initial,False,True)
    result['test_errors']=errors;result['checks_passed']=not errors
def tick(dt):
    try:
        now=time.monotonic()
        if now-state['start']>120:raise RuntimeError('Supplement timeout')
        if state['phase']=='warmup' and now-state['since']>10:
            inspect_terrain();levels.editor_request_begin_play();state.update(phase='play',since=now)
        elif state['phase']=='play' and now-state['since']>3:
            try:play_checks()
            except Exception:result['error']=traceback.format_exc();u.log_error(result['error'])
            save();levels.editor_request_end_play();state.update(phase='end',since=now)
        elif state['phase']=='end' and now-state['since']>5:
            result.update(normal_shutdown=not levels.is_in_play_in_editor(),finished_at_utc=utc())
            result['passed']=bool(result.get('checks_passed') and result['normal_shutdown']);save()
            u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
    except Exception:
        result.update(error=traceback.format_exc(),finished_at_utc=utc(),normal_shutdown=False);save();u.log_error(result['error'])
        u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
