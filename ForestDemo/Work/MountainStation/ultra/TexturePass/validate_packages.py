import unreal as u, json, datetime, traceback, os
ROOT=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/TexturePass'
ASSET='/Game/MountainStation/ultra'
MAP='/Game/Maps/MountainStation_ultra'
def vec(v):return [v.x,v.y,v.z]
def main():
    start=datetime.datetime.now(datetime.timezone.utc)
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
    if globals().get('VALIDATE_RELOAD',True):assert levels.load_level(MAP)
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();editor=u.get_editor_subsystem(u.EditorActorSubsystem)
    assert world.get_path_name() == MAP+'.MountainStation_ultra',world.get_path_name()
    partition=world.get_world_settings().get_editor_property('world_partition')
    assert partition is None, str(partition)
    actors=editor.get_all_level_actors();bylabel={a.get_actor_label():a for a in actors}
    ar=u.AssetRegistryHelpers.get_asset_registry();ar.scan_paths_synchronous(['/Game'],True)
    opt=u.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_game_package_references=True,include_editor_only_package_references=True,include_searchable_names=True,include_soft_management_references=True,include_hard_management_references=True)
    roots=[MAP]+[str(a.package_name) for a in ar.get_assets_by_path(ASSET,recursive=True)]
    seen=set();pending=list(roots);edges={};bad=[]
    while pending:
        pkg=pending.pop()
        if pkg in seen:continue
        seen.add(pkg);deps=[str(x) for x in ar.get_dependencies(pkg,opt)];edges[pkg]=deps
        for dep in deps:
            if dep.startswith('/Game/'):
                if not (dep.startswith(ASSET+'/') or dep==MAP):bad.append([pkg,dep])
                if dep not in seen:pending.append(dep)
    assert not bad,('Foreign game dependencies',bad)
    terrain=bylabel['Terrain'];origin,extent=terrain.get_actor_bounds(False)
    assert abs(extent.x-5000)<2 and abs(extent.y-5000)<2
    assert 'PlayerStart_ArrivalRamp' in bylabel and 'ScreenDebugLogger_Hello' in bylabel
    samples=[]
    locations=[('arrival',-2950,488.46),('ramp_1',-2700,430.77),('ramp_2',-2400,361.54),('ramp_3',-2100,292.31),('ramp_end',-1710,202.31),('platform_start',-1690,200),('platform',500,-100),('platform_detail',800,-190),('tracks_detail',2100,-420),('trail',-1600,1600)]
    for label,x,y in locations:
        hit=u.SystemLibrary.line_trace_single(world,u.Vector(x,y,2500),u.Vector(x,y,-1000),u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],u.DrawDebugTrace.NONE)
        assert hit is not None,'No collision below '+label
        info=hit.to_tuple()
        assert info[0],'Nonblocking collision result at '+label
        loc=info[5]
        assert not info[1],('Trace started overlapping at '+label,str(hit))
        assert -100<loc.z<1000,('Unexpected surface height at '+label,str(hit))
        if label=='arrival':assert abs(loc.z-44.3077)<3,('Arrival ramp top mismatch',loc.z)
        samples.append({'name':label,'xy_cm':[x,y],'ground_hit_cm':vec(loc),'normal':vec(info[7]),'initial_overlap':info[1],'hit_actor':info[9].get_name() if info[9] else None})
    # Low continuous ramp incline and no lip at the platform join.
    ramp=[s for s in samples if s['name'].startswith('ramp_')]
    z1=next(s['ground_hit_cm'][2] for s in samples if s['name']=='ramp_end');z2=next(s['ground_hit_cm'][2] for s in samples if s['name']=='platform_start')
    assert abs(z2-z1)<5,('Ramp lip',z1,z2)
    manifest={'started_at_utc':start.isoformat(),'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'map_reloaded':True,'map':MAP,'actor_count':len(actors),'site_bounds_cm':{'origin':vec(origin),'extent':vec(extent)},'world_path':world.get_path_name(),'world_partition':None,'world_partition_query':'WorldSettings.world_partition read succeeded; pointer is None','force_no_precomputed_lighting':world.get_world_settings().get_editor_property('force_no_precomputed_lighting'),'dependency_packages_checked':len(seen),'foreign_game_dependencies':bad,'dependency_graph':edges,'collision_samples':samples,'ramp_join_difference_cm':abs(z2-z1),'player_start':vec(bylabel['PlayerStart_ArrivalRamp'].get_actor_location()),'native_logger_class':bylabel['ScreenDebugLogger_Hello'].get_class().get_path_name(),'static_meshes':[{ 'label':a.get_actor_label(),'mesh':a.static_mesh_component.static_mesh.get_path_name()} for a in actors if isinstance(a,u.StaticMeshActor)],'limitations':['Collision traces verify sampled surfaces; no character locomotion simulation or railway operations simulation is implemented.']}
    with open(ROOT+'/validation.json','w') as f:json.dump(manifest,f,indent=2)
    u.log('ALDER_VALIDATION_PASSED')
try:main()
except Exception:
    with open(ROOT+'/validation_error.json','w') as f:json.dump({'traceback':traceback.format_exc()},f,indent=2)
    raise
