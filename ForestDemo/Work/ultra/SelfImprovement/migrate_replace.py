"""Run only in the ultra SelfImprovement scratch project; never shared/source."""
import unreal as u,json,datetime,traceback,math
from pathlib import Path
OUT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement')
eas=u.get_editor_subsystem(u.EditorAssetSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
SRC='/Game/Environment/AnimeTree';DST='/Game/Forest/ultra/AnimeTree';MAP='/Game/Maps/ultra'
report={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':{},'replacements':[],'errors':[]}
def xyz(v):return [v.x,v.y,v.z]
def check(key,value,detail=None):
 report['checks'][key]={'passed':bool(value),'detail':detail}
 if not value:raise AssertionError(key+': '+str(detail))
def snapshot(a):
 t=a.get_actor_transform();r=a.get_actor_rotation()
 row={'class':a.get_class().get_path_name(),'label':a.get_actor_label(),'location':xyz(a.get_actor_location()),'rotation':[r.pitch,r.yaw,r.roll],'scale':xyz(a.get_actor_scale3d())}
 if isinstance(a,u.StaticMeshActor):
  c=a.static_mesh_component;row.update(mesh=c.static_mesh.get_path_name() if c.static_mesh else None,materials=[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())])
 return row
def geometry_bounds(a):
 points=[]
 for c in a.get_components_by_class(u.StaticMeshComponent):
  if not c.static_mesh or 'AnimeTreeShadow' in [str(t) for t in c.component_tags]:continue
  b=c.static_mesh.get_bounds();t=c.get_world_transform()
  for x in [-1,1]:
   for y in [-1,1]:
    for z in [-1,1]:
     v=b.origin+u.Vector(b.box_extent.x*x,b.box_extent.y*y,b.box_extent.z*z)
     points.append(xyz(u.MathLibrary.transform_location(t,v)))
 lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
 return {'min':lo,'max':hi,'size':[hi[i]-lo[i] for i in range(3)]}
try:
 inspect=json.loads((OUT/'source_tree_inspection.json').read_text());check('source_inspection_passed',inspect['success'])
 check('baseline_map_loaded',levels.load_level(MAP))
 packages=sorted(inspect['source_ue_dependency_graph'])
 already_migrated=eas.does_asset_exist(DST+'/BP_AnimeFoliageTree')
 source_assets=[eas.load_asset((DST+'/'+p.rsplit('/',1)[1]) if already_migrated else p) for p in packages if p.startswith(SRC+'/')]
 check('all_ten_source_assets_loaded',len(source_assets)==10 and all(source_assets))
 bp=eas.load_asset((DST if already_migrated else SRC)+'/BP_AnimeFoliageTree');native=u.load_class(None,'/Script/ForestUltraTrees.ForestUltraAnimeTreeActor')
 u.BlueprintEditorLibrary.reparent_blueprint(bp,native);u.BlueprintEditorLibrary.compile_blueprint(bp)
 if not already_migrated:
  renames=[u.AssetRenameData(asset=a,new_package_path=DST,new_name=a.get_name()) for a in source_assets]
  check('ue_asset_rename',u.AssetToolsHelpers.get_asset_tools().rename_assets(renames))
 else:report['assets_already_migrated_in_prior_run']=True
 check('renamed_assets_saved',eas.save_loaded_assets(source_assets,only_if_is_dirty=False))
 cls=u.EditorAssetLibrary.load_blueprint_class(DST+'/BP_AnimeFoliageTree');check('migrated_class_loaded',bool(cls))
 allactors=list(actors.get_all_level_actors())
 old=[a for a in allactors if isinstance(a,u.StaticMeshActor) and a.static_mesh_component.static_mesh and a.static_mesh_component.static_mesh.get_name().startswith('SM_Broadleaf')]
 check('expected_broadleaf_count',len(old)==63,len(old))
 report['untouched_before']={a.get_name():snapshot(a) for a in allactors if a not in old}
 for a in old:
  saved=snapshot(a);center,extent=a.get_actor_bounds(False);pos=a.get_actor_location();rot=a.get_actor_rotation()
  new=actors.spawn_actor_from_class(cls,pos,rot);check('spawn_'+a.get_name(),new is not None)
  initial=geometry_bounds(new);oldsize=[extent.x*2,extent.y*2,extent.z*2]
  scale=min(oldsize[i]/initial['size'][i] for i in range(3))
  new.set_actor_scale3d(u.Vector(scale,scale,scale));new.refresh_tree()
  # Preserve source defaults, including full rim renderer and gradient/wind features.
  label=a.get_actor_label();new.set_actor_label(label);new.set_folder_path(a.get_folder_path())
  final=geometry_bounds(new)
  record={'old':saved,'old_bounds_center':xyz(center),'old_bounds_extent':xyz(extent),'new':snapshot(new),'new_geometry_bounds':final,'uniform_fit_scale':scale,'source_geometry_bounds':initial,'new_actor_name':new.get_name()}
  report['replacements'].append(record);actors.destroy_actor(a)
 report['untouched_after']={a.get_name():snapshot(a) for a in actors.get_all_level_actors() if a.get_name() in report['untouched_before']}
 check('all_other_actor_properties_unchanged',report['untouched_before']==report['untouched_after'],len(report['untouched_before']))
 max_position_delta=max(abs(r['old']['location'][i]-r['new']['location'][i]) for r in report['replacements'] for i in range(3))
 max_rotation_delta=max(abs(r['old']['rotation'][i]-r['new']['rotation'][i]) for r in report['replacements'] for i in range(3))
 check('preserved_positions_and_yaw',max_position_delta<1e-8 and max_rotation_delta<1e-8,{'max_position_delta_cm':max_position_delta,'max_rotation_delta_degrees':max_rotation_delta})
 check('bounds_no_wider_or_taller',all(all(r['new_geometry_bounds']['size'][i]<=2*r['old_bounds_extent'][i]+.1 for i in range(3)) for r in report['replacements']))
 check('migrated_assets_resaved',eas.save_loaded_assets(source_assets,only_if_is_dirty=False))
 check('map_saved',levels.save_current_level())
 registry=u.AssetRegistryHelpers.get_asset_registry();registry.scan_paths_synchronous([DST,'/Game/Maps'],True)
 options=u.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True,include_searchable_names=True,include_hard_management_references=True,include_soft_management_references=True,include_editor_only_package_references=True,include_game_package_references=True)
 pending=[MAP]+[str(a.package_name) for a in registry.get_assets_by_path(DST,recursive=True)];edges={};bad=[]
 while pending:
  p=pending.pop()
  if p in edges:continue
  deps=[str(x) for x in registry.get_dependencies(p,options)];edges[p]=deps
  for d in deps:
   if d.startswith('/Script/TunaSweeper') or (d.startswith('/Game/') and not(d.startswith('/Game/Forest/ultra/') or d==MAP)):bad.append([p,d])
   if d.startswith('/Game/') and d not in edges:pending.append(d)
 report['dependency_graph']=edges;check('owned_dependency_closure',not bad,bad)
 report['success']=True
except Exception:report['success']=False;report['errors'].append(traceback.format_exc())
finally:
 report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(OUT/'migration_result.json').write_text(json.dumps(report,indent=2));u.log('ULTRA_TREE_MIGRATION '+str(report['success']));u.SystemLibrary.quit_editor()
