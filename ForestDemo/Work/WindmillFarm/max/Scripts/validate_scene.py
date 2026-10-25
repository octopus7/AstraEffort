import unreal,json,traceback
from pathlib import Path
from datetime import datetime,timezone

WORK=Path(r'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/max')
PROJECT=Path(r'D:/github/AstraEffort/ForestDemo/Saved/Workers/WindmillFarm/max/Project')
ROOT='/Game/WindmillFarm/max'
MAP='/Game/Maps/WindmillFarm_max'
result={'at_utc':datetime.now(timezone.utc).isoformat(),'map':MAP,'passed':False,'failures':[]}
try:
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert level.load_level(MAP),'Saved map failed to load'
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    registry=unreal.AssetRegistryHelpers.get_asset_registry()
    registry.scan_paths_synchronous(['/Game'],force_rescan=True)
    options=unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,
        include_searchable_names=False,include_soft_management_references=True,include_hard_management_references=True)
    visited=set();pending=[MAP];edges={};forbidden=[]
    while pending:
        p=pending.pop()
        if p in visited:continue
        visited.add(p)
        raw_dependencies=registry.get_dependencies(p,options)
        deps=[str(x) for x in (raw_dependencies or [])]
        if p==MAP and not deps:raise RuntimeError('Asset registry did not return the saved map dependency data')
        edges[p]=deps
        for dep in deps:
            if dep.startswith('/Game/'):
                if not (dep.startswith(ROOT+'/') or dep==MAP):forbidden.append(dep)
                elif dep not in visited:pending.append(dep)
    if forbidden:result['failures'].append('Forbidden game dependencies')
    required={'Terrain','WindmillTower','WindmillRotor','Farmhouse','Barn','Wheat','Paths','Fences','Orchard','Props'}
    categories={str(t) for a in actors for t in a.tags}
    if required-categories:result['failures'].append('Missing required scene categories: '+str(sorted(required-categories)))
    static=[];missing_materials=[]
    for a in actors:
        if isinstance(a,unreal.StaticMeshActor):
            c=a.static_mesh_component
            if not c.static_mesh:result['failures'].append('Missing mesh: '+a.get_actor_label());continue
            for i in range(c.get_num_materials()):
                if not c.get_material(i):missing_materials.append(a.get_actor_label()+':'+str(i))
            origin,ext=a.get_actor_bounds(False)
            static.append({'label':a.get_actor_label(),'mesh':c.static_mesh.get_path_name(),'materials':[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())],
             'center_cm':[origin.x,origin.y,origin.z],'extent_cm':[ext.x,ext.y,ext.z]})
    terrain=next(x for x in static if x['label']=='Farm_Terrain')
    if abs(terrain['extent_cm'][0]*2-10000)>5 or abs(terrain['extent_cm'][1]*2-10000)>5:result['failures'].append('Wrong FBX scale / terrain extent')
    tower=next(x for x in static if x['label']=='Farm_WindmillTower')
    rotor_actor=next(a for a in actors if a.get_actor_label()=='Farm_WindmillRotor')
    pivot=rotor_actor.get_actor_location()
    source=json.loads((WORK/'Source/scene_manifest.json').read_text(encoding='utf-8'))
    target_pivot=[q*100 for q in source['rotor_pivot_m']]
    if abs(tower['center_cm'][0]+2300)>1 or abs(tower['center_cm'][1]-1700)>1:result['failures'].append('Tower layout handedness mismatch')
    if any(abs(a-b)>1 for a,b in zip([pivot.x,pivot.y,pivot.z],target_pivot)):result['failures'].append('Rotor placed away from its material rotation pivot')
    if abs((tower['center_cm'][1]-pivot.y)-600)>1:result['failures'].append('Rotor axial separation is not 6 meters')
    if missing_materials:result['failures'].append('Unassigned materials')
    expected_packages={s['mesh'].split('.')[0] for s in static}
    expected_packages.update(m.split('.')[0] for s in static for m in s['materials'] if m)
    uncovered=sorted(p for p in expected_packages-visited if p.startswith('/Game/'))
    if uncovered:result['failures'].append('Recursive registry traversal missed placed resources: '+str(uncovered))
    external=[str(p.relative_to(PROJECT/'Content')) for root in ['__ExternalActors__','__ExternalObjects__'] for p in (PROJECT/'Content'/root).rglob('*') if p.is_file()]
    baked=[str(p.relative_to(PROJECT/'Content')) for p in (PROJECT/'Content/Maps').glob('*BuiltData*')]
    if external or baked:result['failures'].append('External packages or baked lighting present')
    wp_classes=[a.get_class().get_name() for a in actors if 'WorldPartition' in a.get_class().get_name()]
    if wp_classes:result['failures'].append('World partition actors found')
    no_precomputed=world.get_world_settings().get_editor_property('force_no_precomputed_lighting')
    world_partition=world.get_world_settings().get_editor_property('world_partition')
    if world_partition is not None:result['failures'].append('WorldSettings has a WorldPartition object')
    if not no_precomputed:result['failures'].append('Precomputed lighting not disabled')
    result.update(passed=not result['failures'],actor_count=len(actors),static_mesh_actors=static,required_categories_present=sorted(required&categories),
      forbidden_game_dependencies=sorted(set(forbidden)),recursive_game_package_count=len(visited),dependency_graph=edges,missing_materials=missing_materials,
      placed_resource_packages_not_covered=uncovered,
      external_packages=external,baked_lighting_files=baked,world_partition_actor_classes=wp_classes,force_no_precomputed_lighting=no_precomputed,
      world_partition_object_path=world_partition.get_path_name() if world_partition else None,world_partition_directly_checked=True,
      map_file_exists=(PROJECT/'Content/Maps/WindmillFarm_max.umap').is_file())
    result['rotor_alignment']={'tower_center_cm':tower['center_cm'],'rotor_pivot_cm':[pivot.x,pivot.y,pivot.z],'expected_material_pivot_cm':target_pivot,'axial_separation_cm':tower['center_cm'][1]-pivot.y}
except Exception:
    result['failures'].append(traceback.format_exc())
(WORK/'Evidence/saved_scene_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
if not result['passed']:raise RuntimeError(json.dumps(result['failures']))
unreal.log('WINDMILL_SAVED_SCENE_VALIDATION_PASSED')
