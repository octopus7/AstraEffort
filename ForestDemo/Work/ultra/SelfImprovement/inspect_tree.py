import unreal as u,json,traceback,datetime
from pathlib import Path
OUT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement')
eas=u.get_editor_subsystem(u.EditorAssetSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
report={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':{},'errors':[]}
def check(k,b,detail=None):report['checks'][k]={'passed':bool(b),'detail':detail}
def xyz(v):return [v.x,v.y,v.z]
def inspect(actor):
 result={'class':actor.get_class().get_path_name(),'properties':{},'components':[]}
 for key in ['wind_strength','leaf_card_scale','leaf_density','gradient_width','gradient_strength','gradient_exponent','clump_shading_strength','rim_strength','rim_width_pixels','rim_brightness','gradient_dark_color','gradient_light_color','rim_color','leaf_material']:
  value=actor.get_editor_property(key);result['properties'][key]=value if isinstance(value,(int,float,str,bool)) else str(value)
 for c in actor.get_components_by_class(u.StaticMeshComponent):
  row={'name':c.get_name(),'tags':[str(x) for x in c.component_tags],'mesh':c.static_mesh.get_path_name() if c.static_mesh else None,'location':xyz(c.get_editor_property('relative_location')),'scale':xyz(c.get_editor_property('relative_scale3d')),'world_location':xyz(c.get_world_location()),'materials':[str(c.get_material(i)) for i in range(c.get_num_materials())]}
  for k in ['cast_shadow','cast_hidden_shadow','render_in_main_pass','render_in_depth_pass','render_custom_depth','custom_depth_stencil_value','bounds_scale']:
   try:row[k]=c.get_editor_property(k)
   except Exception as exc:row[k]=str(exc)
  try:row['custom_primitive_data']=list(c.get_editor_property('custom_primitive_data_internal').get_editor_property('data'))
  except Exception as exc:row['custom_primitive_data_access']=str(exc)
  if 'AnimeTreeClump' in row['tags']:
   mid=c.get_material(0);row['mid_scalars']={k:mid.get_scalar_parameter_value(k) for k in ['WindStrength','LeafCardScale','LeafDensity','GradientStrength','ClumpShadingStrength','StableShadowProxy']}
  result['components'].append(row)
 center,extent=actor.get_actor_bounds(False);result['actor_bounds']={'center':xyz(center),'extent':xyz(extent)}
 return result
try:
 native=u.load_class(None,'/Script/ForestUltraTrees.ForestUltraAnimeTreeActor');assert native,'Ported native class missing'
 package='/Game/Environment/AnimeTree/BP_AnimeFoliageTree';bp=eas.load_asset(package);assert bp,'Original BP did not load with private native redirect'
 u.BlueprintEditorLibrary.compile_blueprint(bp)
 cls=u.EditorAssetLibrary.load_blueprint_class(package);assert cls
 actor=actors.spawn_actor_from_class(cls,u.Vector(0,0,5000));assert actor
 source=inspect(actor);report['source_bp_snapshot']=source
 clumps=actor.get_leaf_clumps();shadows=[c for c in source['components'] if 'AnimeTreeShadow' in c['tags']]
 check('native_parent_loaded',u.MathLibrary.class_is_child_of(cls,native))
 check('clumps_and_shadow_proxies',len(clumps)>0 and len(shadows)==len(clumps),{'clumps':len(clumps),'shadows':len(shadows)})
 check('rim_stencil_registration',all(c.get_editor_property('render_custom_depth') and c.get_editor_property('custom_depth_stencil_value')>=16 for c in clumps))
 check('stable_hidden_shadow_flags',all(c['cast_shadow'] and c['cast_hidden_shadow'] and not c['render_in_main_pass'] and not c['render_in_depth_pass'] for c in shadows))
 saved=[actor.get_editor_property(k) for k in ['wind_strength','leaf_card_scale','leaf_density']]
 actor.set_tree_parameters(10,-2,5);changed=inspect(actor);report['clamp_snapshot']=changed
 check('parameter_clamping',all(abs(actor.get_editor_property(k)-v)<1e-6 for k,v in [('wind_strength',1.5),('leaf_card_scale',.2),('leaf_density',1)]))
 check('mid_parameter_refresh',all(abs(c['mid_scalars']['WindStrength']-1.5)<1e-6 and abs(c['mid_scalars']['LeafDensity']-1)<1e-6 for c in changed['components'] if 'AnimeTreeClump' in c['tags']))
 actor.set_tree_parameters(*saved);actor.refresh_tree();after=inspect(actor)
 check('refresh_no_shadow_accumulation',len([c for c in after['components'] if 'AnimeTreeShadow' in c['tags']])==len(clumps))
 guide=actor.get_editor_property('gradient_guide');p=guide.get_editor_property('relative_location');guide.set_relative_location(p+u.Vector(80,0,0),False,False)
 moved=inspect(actor);report['gradient_moved_snapshot']=moved
 before_data=[c.get('custom_primitive_data') for c in source['components'] if 'AnimeTreeClump' in c['tags']];after_data=[c.get('custom_primitive_data') for c in moved['components'] if 'AnimeTreeClump' in c['tags']]
 report['gradient_cpd_readable']=all(x is not None for x in before_data)
 if report['gradient_cpd_readable']:check('gradient_transform_callback',before_data!=after_data)
 guide.set_relative_location(p,False,False);actors.destroy_actor(actor)
 registry=u.AssetRegistryHelpers.get_asset_registry();registry.scan_paths_synchronous(['/Game/Environment/AnimeTree'],True)
 opts=u.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True,include_searchable_names=True,include_hard_management_references=True,include_soft_management_references=True,include_editor_only_package_references=True,include_game_package_references=True)
 queue=[package];edges={};missing=[]
 while queue:
  p=queue.pop()
  if p in edges:continue
  deps=[str(d) for d in registry.get_dependencies(p,opts)];edges[p]=deps
  for d in deps:
   if d.startswith('/Game/'):
    if not eas.does_asset_exist(d):missing.append(d)
    elif d not in edges:queue.append(d)
 report['source_ue_dependency_graph']=edges;check('source_asset_closure_complete',not missing,missing)
 trunk=eas.load_asset('/Game/Environment/AnimeTree/SM_AnimeTree_Trunk');body=trunk.get_editor_property('body_setup');sme=u.get_editor_subsystem(u.StaticMeshEditorSubsystem);report['trunk_collision']={'complexity':str(body.get_editor_property('collision_trace_flag')),'simple':sme.get_simple_collision_count(trunk),'convex':sme.get_convex_collision_count(trunk)}
 report['asset_tools_redirect_methods']=[x for x in dir(u.AssetToolsHelpers.get_asset_tools()) if any(k in x.lower() for k in ['redirect','rename','fixup'])]
 report['success']=all(c['passed'] for c in report['checks'].values())
except Exception:report['success']=False;report['errors'].append(traceback.format_exc())
finally:
 report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(OUT/'source_tree_inspection.json').write_text(json.dumps(report,indent=2));u.log('FOREST_ULTRA_SOURCE_INSPECTION '+str(report['success']));None if globals().get('KEEP_EDITOR_OPEN',False) else u.SystemLibrary.quit_editor()
