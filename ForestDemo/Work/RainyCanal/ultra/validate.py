import unreal,json,math
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
ASSET='/Game/RainyCanal/ultra';MAP='/Game/Maps/RainyCanal_ultra'
ACT=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SM=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)

def trace(world,start,end):
    pawn=unreal.GameplayStatics.get_player_pawn(world,0)
    hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(*start),unreal.Vector(*end),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn] if pawn else [],unreal.DrawDebugTrace.NONE)
    if hit is None:return {'hit':False}
    # HitResult properties are protected in Python; to_tuple invokes its native BreakHitResult.
    data=hit.to_tuple();loc=data[4];comp=data[10]
    mesh=comp.get_editor_property('static_mesh') if isinstance(comp,unreal.StaticMeshComponent) else None
    return {'hit':bool(data[0]),'location':[loc.x,loc.y,loc.z],'actor':data[9].get_actor_label() if data[9] else None,'mesh':mesh.get_name() if mesh else None,'distance':data[3]}

def saved(world):
    checks={};details={};actors=ACT.get_all_level_actors();named={a.get_actor_label():a for a in actors}
    checks['saved_map_reload']=MAP in world.get_path_name()
    ws=world.get_world_settings();checks['non_world_partition']=ws.get_editor_property('world_partition') is None
    project=Path(unreal.Paths.project_content_dir()).resolve()
    checks['no_external_packages']=not any('__External' in p.as_posix() or '_BuiltData' in p.name for p in project.rglob('*'))
    registry=unreal.AssetRegistryHelpers.get_asset_registry();registry.scan_paths_synchronous([ASSET,'/Game/Maps'],True)
    opts=unreal.AssetRegistryDependencyOptions();opts.set_editor_property('include_hard_package_references',True);opts.set_editor_property('include_soft_package_references',True);opts.set_editor_property('include_searchable_names',False);opts.set_editor_property('include_soft_management_references',False);opts.set_editor_property('include_hard_management_references',False)
    visited=set();stack=[MAP];bad=[]
    while stack:
        pkg=stack.pop()
        if pkg in visited:continue
        visited.add(pkg)
        for d in registry.get_dependencies(pkg,opts):
            d=str(d)
            if d.startswith('/Game/'):
                if d!=MAP and not d.startswith(ASSET+'/'):bad.append(d)
                if d not in visited:stack.append(d)
    checks['owned_dependencies']=not bad;details['dependencies']={'packages':sorted(visited),'violations':bad}
    boxes=[]
    for key in ('SM_BankWest','SM_BankEast'):
        origin,extent=named[key].get_actor_bounds(False);boxes.append(([origin.x-extent.x,origin.y-extent.y,origin.z-extent.z],[origin.x+extent.x,origin.y+extent.y,origin.z+extent.z]))
    width=max(b[1][0] for b in boxes)-min(b[0][0] for b in boxes);length=max(b[1][1] for b in boxes)-min(b[0][1] for b in boxes)
    checks['footprint_100m']=abs(width-10000)<.2 and abs(length-10000)<.2;details['bank_bounds']=boxes
    grounds=[]
    for key,a in named.items():
        if key.startswith('Building_'):
            o,e=a.get_actor_bounds(False);grounds.append({'label':key,'bottom_cm':o.z-e.z})
    checks['building_grounding']=len(grounds)==8 and all(abs(x['bottom_cm'])<.2 for x in grounds);details['buildings']=grounds
    contacts=[]
    for label,y in [('stone',1500),('timber',-2800)]:
        for x in (-790,-600,0,600,790):
            r=trace(world,(x,y,500),(x,y,-200));r.update({'bridge':label,'x':x});contacts.append(r)
    checks['bridge_contacts']=all(r['hit'] for r in contacts) and all(abs(r['location'][2])<15 for r in contacts if abs(r['x'])==790)
    details['bridge_surface_traces']=contacts
    meshrows=[]
    for a in registry.get_assets_by_path(ASSET+'/Meshes',False):
        mesh=a.get_asset();row={'name':mesh.get_name(),'uv_channels':SM.get_num_uv_channels(mesh,0),'materials':[str(x.material_interface.get_path_name()) if x.material_interface else None for x in mesh.get_editor_property('static_materials')]};meshrows.append(row)
    checks['mesh_uvs_and_materials']=len(meshrows)==24 and all(r['uv_channels']>=2 and all(m and m.startswith(ASSET) for m in r['materials']) for r in meshrows);details['meshes']=meshrows
    graphs=[]
    for name in ('Rain','CanalWater','PuddleWater'):
        m=unreal.load_asset(ASSET+'/Materials/M_'+name)
        exprs=[unreal.MaterialEditingLibrary.get_material_property_input_node(m,unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET if name=='Rain' else unreal.MaterialProperty.MP_NORMAL)]
        rows=[]
        for n in exprs:
            if isinstance(n,unreal.MaterialExpressionCustom):
                inputs=unreal.MaterialEditingLibrary.get_inputs_for_material_expression(m,n)
                rows.append({'code':n.get_editor_property('code'),'connected_inputs':[x.get_class().get_name() if x else None for x in inputs]})
        graphs.append({'material':name,'custom_nodes':rows})
    checks['material_graphs']=all(r['custom_nodes'] and all(row['connected_inputs'] and all(row['connected_inputs']) for row in r['custom_nodes']) for r in graphs)
    details['weather_graphs']=graphs
    sampler_rows=[]
    for data in registry.get_assets_by_path(ASSET+'/Materials',False):
        m=data.get_asset();stack=[];seen=set()
        for prop in (unreal.MaterialProperty.MP_BASE_COLOR,unreal.MaterialProperty.MP_ROUGHNESS,unreal.MaterialProperty.MP_NORMAL):
            n=unreal.MaterialEditingLibrary.get_material_property_input_node(m,prop)
            if n:stack.append(n)
        while stack:
            n=stack.pop()
            if n.get_path_name() in seen:continue
            seen.add(n.get_path_name());stack.extend(x for x in unreal.MaterialEditingLibrary.get_inputs_for_material_expression(m,n) if x)
            if isinstance(n,unreal.MaterialExpressionTextureSample):
                tex=n.get_editor_property('texture')
                if tex and tex.get_name().endswith('_Roughness'):sampler_rows.append({'material':m.get_name(),'texture':tex.get_name(),'linear_grayscale':n.get_editor_property('sampler_type')==unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE})
    checks['roughness_sampler_types']=len(sampler_rows)==11 and all(r['linear_grayscale'] for r in sampler_rows);details['roughness_samplers']=sampler_rows
    rainmesh=unreal.load_asset(ASSET+'/Meshes/SM_RainVolume');checks['rain_vertex_colors']=SM.has_vertex_colors(rainmesh)
    ext=rainmesh.get_editor_property('positive_bounds_extension');checks['rain_bounds']=ext.z>=1400 and ext.x>=65 and ext.y>=22
    checks['dynamic_lighting']=all(c.get_editor_property('mobility')==unreal.ComponentMobility.MOVABLE for a in actors for c in a.get_components_by_class(unreal.LightComponentBase))
    checks['scene_contents']=sum(k.startswith('Building_') for k in named)==8 and all(x in named for x in ('SM_StoneBridge','SM_TimberBridge','CanalWater','RainVolume','Dock','MooredBoat'))
    checks['player_start']=any(isinstance(a,unreal.PlayerStart) for a in actors)
    details['actor_count']=len(actors)
    details['placed_density']={}
    for prefix in ('Tree_','Shrub_','GrassFringe_'):
        scales=[a.get_actor_scale3d().x for a in actors if a.get_actor_label().startswith(prefix)]
        details['placed_density'][prefix]={'count':len(scales),'scale_range':[min(scales),max(scales)],'nominal_uv1_pixels_per_metre_range':[128/max(scales),128/min(scales)]} if scales else {'count':0}
    details['final_lighting']={'skylight':named['OvercastSkyLight'].get_component_by_class(unreal.SkyLightComponent).get_editor_property('intensity'),'fill':named['OvercastFill'].get_component_by_class(unreal.DirectionalLightComponent).get_editor_property('intensity'),'fog_density':named['RainHaze'].get_component_by_class(unreal.ExponentialHeightFogComponent).get_editor_property('fog_density')}
    return {'utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'details':details,'all_passed':False}

def runtime(world,result):
    assert world is not None,'PIE world missing'
    checks=result['checks'];detail={};pawn=unreal.GameplayStatics.get_player_pawn(world,0);controller=unreal.GameplayStatics.get_player_controller(world,0)
    checks['pie_possession']=pawn is not None and controller is not None and pawn.get_controller()==controller
    detail['pawn_class']=pawn.get_class().get_name() if pawn else None
    ground=[trace(world,(x,y,400),(x,y,-200)) for x,y in [(-1050,2100),(1050,800),(-3200,1500)]];checks['ground_collision']=all(r['hit'] and abs(r['location'][2])<2 for r in ground);detail['ground_traces']=ground
    bridges=[trace(world,(0,1500,500),(0,1500,-150)),trace(world,(16.6667,-2800,500),(16.6667,-2800,-150))];checks['bridge_collision']=all(r['hit'] and r.get('mesh') in ('SM_StoneBridge','SM_TimberBridge') for r in bridges);detail['bridge_traces']=bridges
    contacts=[]
    for label,y in [('stone',1500),('timber',-2800)]:
        xs=(-790,-600,0,600,790) if label=='stone' else (-783.333,-616.667,16.667,616.667,783.333)
        for x in xs:
            r=trace(world,(x,y,500),(x,y,-150));r.update({'bridge':label,'x':x});contacts.append(r)
    checks['bridge_contacts']=all(r['hit'] and r.get('mesh')==('SM_StoneBridge' if r['bridge']=='stone' else 'SM_TimberBridge') and -.5<=r['location'][2]<=115 for r in contacts) and all(abs(r['location'][2])<15 for r in contacts if abs(r['x'])>780);detail['bridge_contact_traces']=contacts
    wall=trace(world,(-1500,3500,200),(-2300,3500,200));checks['building_collision']=wall['hit'];detail['building_trace']=wall
    if pawn:
        pawn.set_actor_location(unreal.Vector(-1050,2100,100),False,True)
        pawn.set_actor_location(unreal.Vector(-1050,1800,100),True,False);end=pawn.get_actor_location();checks['pawn_can_move']=abs(end.y-1800)<2
        pawn.set_actor_location(unreal.Vector(-1050,1800,-200),True,False);blocked=pawn.get_actor_location();checks['pawn_sweep_blocks']=blocked.z>0
        detail['quay_move_end']=[end.x,end.y,end.z];detail['blocked_at_z']=blocked.z
        # Swept movement follows the measured bridge deck with a free-fly pawn; no walking-character claim.
        route=[]
        for label,y,xs in [('stone',1500,list(range(-750,751,150))),('timber',-2800,[x+8 for x in range(-750,751,150)]),('dock',-100,list(range(850,449,-50)))]:
            for i,x in enumerate(xs):
                hit=trace(world,(x,y,500),(x,y,-150));z=hit['location'][2]+70 if hit['hit'] else 200
                pawn.set_actor_location(unreal.Vector(x,y,z),False if i==0 else True,False);p=pawn.get_actor_location();route.append({'route':label,'surface_hit':hit['hit'],'surface_mesh':hit.get('mesh'),'target':[x,y,z],'actual':[p.x,p.y,p.z]})
        checks['bridge_traversal']=all(r['surface_hit'] and all(abs(a-b)<2 for a,b in zip(r['actual'],r['target'])) for r in route);detail['bridge_dock_swept_routes']=route
    else:checks.update({'pawn_can_move':False,'pawn_sweep_blocks':False,'bridge_traversal':False})
    result['details']['runtime']=detail;return result
