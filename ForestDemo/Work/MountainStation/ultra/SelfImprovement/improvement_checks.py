import unreal as u,json,math,datetime
from pathlib import Path
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement');A='/Game/MountainStation/ultra/Meshes/'
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def mesh_grids():
    editor=u.get_editor_subsystem(u.EditorActorSubsystem);grids={};actors={};colors={}
    for actor in editor.get_all_level_actors():
        if not isinstance(actor,u.StaticMeshActor):continue
        c=actor.static_mesh_component;sm=c.static_mesh
        if not sm or sm.get_name() not in ['SM_Terrain','SM_Footpath','SM_Sleepers','SM_Ballast','SM_Rails']:continue
        grid={};triangles=[]
        for section in range(sm.get_num_sections(0)):
            data=u.ProceduralMeshLibrary.get_section_from_static_mesh(sm,0,section);vs=[tuple(u.MathLibrary.transform_location(c.get_world_transform(),p).to_tuple()) for p in data[0]]
            if sm.get_name()=='SM_Footpath':
                colors={'imported_nonwhite_vertex_colors_present':u.get_editor_subsystem(u.StaticMeshEditorSubsystem).has_vertex_colors(sm),'verification_scope':'Imported mesh description contains nonwhite vertex colors; numeric color range is not measured by this API.'}
            for j in range(0,len(data[1]),3):
                t=[vs[data[1][j+k]] for k in range(3)];index=len(triangles);triangles.append(t)
                for x in range(math.floor(min(p[0] for p in t)/100),math.floor(max(p[0] for p in t)/100)+1):
                    for y in range(math.floor(min(p[1] for p in t)/100),math.floor(max(p[1] for p in t)/100)+1):grid.setdefault((x,y),[]).append(index)
        grids[sm.get_name()]=(triangles,grid);actors[sm.get_name()]=actor
    assert len(grids)==5 and colors['imported_nonwhite_vertex_colors_present'],{'mesh_names':list(grids),'colors':colors}
    return grids,actors,colors
def height(mesh,x,y):
    triangles,grid=mesh;heights=[]
    for index in grid.get((math.floor(x/100),math.floor(y/100)),[]):
        a,b,c=triangles[index];den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-8:continue
        wa=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den;wb=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;wc=1-wa-wb
        if min(wa,wb,wc)>=-1e-5:heights.append(wa*a[2]+wb*b[2]+wc*c[2])
    assert heights,('No imported triangle at XY',x,y)
    return max(heights)
def editor_checks():
    grids,actors,colors=mesh_grids();margins=[]
    for tri in grids['SM_Footpath'][0]:
        for w in [(1/3,1/3,1/3),(.5,.5,0),(.5,0,.5),(0,.5,.5)]:
            p=[sum(t[k]*ww for t,ww in zip(tri,w)) for k in range(3)];margins.append(p[2]-height(grids['SM_Terrain'],p[0],p[1]))
    assert min(margins)>=3.0,('Path intersects terrain',min(margins))
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();editor=u.get_editor_subsystem(u.EditorActorSubsystem);allactors=list(editor.get_all_level_actors());samples=[]
    for i in range(8,140,8):
        x=-49.5+i*.68;y=-9+.012*(x+3)**2;angle=math.atan(.024*(x+3));sx,sy=x*100,y*100
        ballast=height(grids['SM_Ballast'],sx,sy);sleeper=height(grids['SM_Sleepers'],sx,sy);assert 13<sleeper-ballast<15
        rx=(x-math.sin(angle)*.76)*100;ry=(y+math.cos(angle)*.76)*100;rail=height(grids['SM_Rails'],rx,ry);assert 23<rail-sleeper<25
        hit=u.SystemLibrary.line_trace_single(world,u.Vector(rx,ry,3000),u.Vector(rx,ry,-500),u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[a for a in allactors if a!=actors['SM_Rails']],u.DrawDebugTrace.NONE)
        assert hit and hit.to_tuple()[0] and abs(hit.to_tuple()[5].z-rail)<.5,'Rail head physics/top geometry mismatch'
        samples.append({'xy_cm':[sx,sy],'ballast_z_cm':ballast,'sleeper_z_cm':sleeper,'rail_head_z_cm':rail,'exposed_sleeper_cm':sleeper-ballast})
    lights=[]
    for actor in allactors:
        if actor.get_actor_label() in ['Tunnel entrance fill','Tunnel inner fill']:
            assert actor.light_component.mobility==u.ComponentMobility.MOVABLE;lights.append({'label':actor.get_actor_label(),'intensity':actor.light_component.intensity,'mobility':str(actor.light_component.mobility)})
    assert len(lights)==2 and world.get_world_settings().get_editor_property('force_no_precomputed_lighting')
    record={'utc':stamp(),'path_triangle_centroid_and_edge_samples':len(margins),'minimum_path_terrain_clearance_cm':min(margins),'path_vertex_color':colors,'rail_samples':samples,'movable_tunnel_lights':lights,'passed':True}
    (R/'improvement_geometry_validation.json').write_text(json.dumps(record,indent=2));return record
def runtime_routes(pw):
    pc=u.GameplayStatics.get_player_controller(pw,0);pawn=u.GameplayStatics.get_player_pawn(pw,0);assert pc and pawn and pc.get_controlled_pawn()==pawn
    original=pawn.get_actor_location();data=json.loads((R/'geometry_changes.json').read_text());cx,cy=data['crossing_center_m'];nx,ny=data['crossing_right']
    crossing=[(cx+nx*b,cy+ny*b) for b in [-5+i*.2 for i in range(51)]]
    junction=[p for p in data['routes'][0] if 6.3<p[1]<13.5 and -32<p[0]<-22]
    end=(cx+nx*5,cy+ny*5);toe=[(-30+(end[0]+30)*i/12,5+(end[1]-5)*i/12) for i in range(13)]
    result={'utc':stamp(),'possessed':True,'pawn':pawn.get_path_name(),'sphere_radius_cm':pawn.root_component.get_scaled_sphere_radius(),'support_offset_cm_by_route':{'crossing':80,'repaired_slope':150,'ramp_toe_connection':80},'routes':[],'passed':False}
    for name,points in [('crossing',crossing),('repaired_slope',junction),('ramp_toe_connection',toe)]:
        assert len(points)>4
        for reverse in [False,True]:
            clearance=150 if name=='repaired_slope' else 80
            rec={'name':name,'reverse':reverse,'moves':[],'support_offset_cm':clearance,'mode':'DefaultPawn flight clearance; not grounded walking'};result['routes'].append(rec);order=list(reversed(points)) if reverse else points
            for k,(x,y) in enumerate(order):
                prev=order[max(0,k-1)];nxt=order[min(len(order)-1,k+1)];dx=nxt[0]-prev[0];dy=nxt[1]-prev[1];length=math.hypot(dx,dy);normal=(-dy/length,dx/length)
                candidates=[];selected=None
                for offset in [0,.45,-.45,.75,-.75]:
                    px=x+normal[0]*offset;py=y+normal[1]*offset
                    hit=u.SystemLibrary.line_trace_single(pw,u.Vector(px*100,py*100,4000),u.Vector(px*100,py*100,-500),u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[pawn],u.DrawDebugTrace.NONE)
                    if not hit or not hit.to_tuple()[0]:continue
                    h=hit.to_tuple();component=h[10];mesh=component.static_mesh.get_path_name() if isinstance(component,u.StaticMeshComponent) else None
                    if mesh not in [A+'SM_Footpath.SM_Footpath',A+'SM_PedestrianCrossing.SM_PedestrianCrossing',A+'SM_Rails.SM_Rails',A+'SM_AccessRamp.SM_AccessRamp']:continue
                    target=u.Vector(px*100,py*100,h[5].z+clearance);start=target if k==0 else pawn.get_actor_location()
                    end=target+u.Vector(.1,0,0) if k==0 else target
                    probe=u.SystemLibrary.sphere_trace_single_by_profile(pw,start,end,pawn.root_component.get_scaled_sphere_radius(),pawn.root_component.get_collision_profile_name(),False,[pawn],u.DrawDebugTrace.NONE)
                    blocked=None
                    if probe is not None:
                        ph=probe.to_tuple();blocked={'blocking':ph[0],'overlap':ph[1],'component':ph[10].get_path_name() if ph[10] else None,'actor':ph[9].get_name() if ph[9] else None}
                    candidates.append({'lateral_offset_m':offset,'target_cm':list(target.to_tuple()),'blocked':blocked})
                    if probe is None:selected=(target,mesh,offset);break
                rec.setdefault('candidate_checks',[]).append(candidates);(R/'Runtime/changed_routes.json').write_text(json.dumps(result,indent=2))
                assert selected is not None,('No clear supported route within path width',name,reverse,k,candidates)
                target,mesh,offset=selected
                if k==0:pawn.set_actor_location(target,False,True);rec['start_cm']=list(target.to_tuple())
                else:
                    start=pawn.get_actor_location();movement=pawn.set_actor_location(target,True,False);actual=pawn.get_actor_location();error=(actual-target).length();distance=(actual-start).length();assert error<3 and distance>.01,(name,k,error,distance,str(movement))
                    rec['moves'].append({'target_cm':list(target.to_tuple()),'actual_cm':list(actual.to_tuple()),'distance_cm':distance,'error_cm':error,'support_mesh':mesh,'lateral_offset_m':offset,'movement_hit':str(movement)})
    pawn.set_actor_location(original,False,True);result['passed']=True
    (R/'Runtime/changed_routes.json').write_text(json.dumps(result,indent=2));return result
