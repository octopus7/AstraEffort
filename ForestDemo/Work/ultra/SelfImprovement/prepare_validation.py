from pathlib import Path
root=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra');out=root/'SelfImprovement'
s=(root/'TexturePass/validate_level.py').read_text()
s=s.replace("Work/ultra/TexturePass'","Work/ultra/SelfImprovement'").replace('Saved/Workers/ultra/ForestDemo/Content','Saved/Workers/ultra/SelfImprovement/ForestDemo/Content')
s=s.replace("report['actor_classes']=classes;report['dependency_graph']=edges",'''report['actor_classes']=classes;report['dependency_graph']=edges
 native=u.load_class(None,'/Script/ForestUltraTrees.ForestUltraAnimeTreeActor')
 bp=eas.load_asset(ASSET+'/AnimeTree/BP_AnimeFoliageTree');u.BlueprintEditorLibrary.compile_blueprint(bp)
 tree_class=u.EditorAssetLibrary.load_blueprint_class(ASSET+'/AnimeTree/BP_AnimeFoliageTree')
 check('ported_native_parent',u.MathLibrary.class_is_child_of(tree_class,native))
 trees=[a for a in actorlist if a.get_class()==tree_class]
 check('exactly_63_anime_trees',len(trees)==63,len(trees))
 check('no_old_broadleaf_actors',not any(isinstance(a,u.StaticMeshActor) and a.static_mesh_component.static_mesh and a.static_mesh_component.static_mesh.get_name().startswith('SM_Broadleaf') for a in actorlist))
 ids=[];tree_checks=[]
 for a in trees:
  clumps=a.get_leaf_clumps();shadows=[c for c in a.get_components_by_class(u.StaticMeshComponent) if 'AnimeTreeShadow' in [str(t) for t in c.component_tags]]
  stencil={c.get_editor_property('custom_depth_stencil_value') for c in clumps};ids.extend(stencil)
  trunk=a.get_editor_property('trunk')
  tree_checks.append({'actor':a.get_name(),'clumps':len(clumps),'shadow_proxies':len(shadows),'stencils':list(stencil),'trunk_collision':str(trunk.get_collision_enabled()),'passed':len(clumps)==10 and len(shadows)==10 and len(stencil)==1 and all(c.get_editor_property('render_custom_depth') for c in clumps) and trunk.get_collision_enabled()!=u.CollisionEnabled.NO_COLLISION and all(c.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION for c in clumps)})
 check('all_tree_components_and_collision_flags',all(t['passed'] for t in tree_checks),tree_checks)
 check('unique_stencil_per_tree',len(ids)==len(set(ids))==63 and min(ids)>=16 and max(ids)<=255,ids)
 check('no_original_native_dependency',not any(d.startswith('/Script/TunaSweeper') for deps in edges.values() for d in deps))
 check('no_source_asset_directory',(not (content/'Environment').exists()))
 config=(content.parent/'Config/DefaultEngine.ini').read_text()
 check('no_temporary_native_redirect','/Script/TunaSweeper' not in config)
 report['gradient_cpd_note']='Runtime CPD getter is native-only in UE 5.7; direct Python read was unavailable. Gradient callback is preserved in port source and tested with a rendered guide-transform toggle.'
 migration=json.loads((ROOT/'migration_result.json').read_text())
 check('migration_passed',migration['success'])
 def snap(a):
  r=a.get_actor_rotation();v=a.get_actor_location();s=a.get_actor_scale3d();row={'class':a.get_class().get_path_name(),'label':a.get_actor_label(),'location':[v.x,v.y,v.z],'rotation':[r.pitch,r.yaw,r.roll],'scale':[s.x,s.y,s.z]}
  if isinstance(a,u.StaticMeshActor):
   c=a.static_mesh_component;row.update(mesh=c.static_mesh.get_path_name() if c.static_mesh else None,materials=[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())])
  return row
 actual={a.get_name():snap(a) for a in actorlist if a.get_name() in migration['untouched_before']}
 check('fresh_reload_871_other_actors_unchanged',actual==migration['untouched_before'],len(actual))''')
(out/'validate_level.py').write_text(s)
s=(root/'TexturePass/validate_runtime.py').read_text().replace("Work/ultra/TexturePass'","Work/ultra/SelfImprovement'")
s=s.replace('Fresh texture-pass saved-map process; actual PIE after render evidence.','Fresh migrated map without original asset directory or native redirect; actual PIE after render evidence.')
s=s.replace("for prefix in ['SM_Broadleaf','SM_Pine','SM_Rock']:","for prefix in ['SM_Pine','SM_Rock']:")
s=s.replace("  report['native_logger_count']=",'''  tree_cls=u.load_class(None,'/Script/ForestUltraTrees.ForestUltraAnimeTreeActor')
  trees=list(u.GameplayStatics.get_all_actors_of_class(world,tree_cls));report['anime_tree_runtime_count']=len(trees)
  tree_hits=[]
  for target in trees:
   trunk=target.get_editor_property('trunk');pos=target.get_actor_location();pos=u.Vector(pos.x,pos.y,pos.z+120*target.get_actor_scale3d().z)
   hit=u.SystemLibrary.line_trace_single(world,u.Vector(pos.x-500,pos.y,pos.z),u.Vector(pos.x+500,pos.y,pos.z),u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[a for a in allactors if a!=target],u.DrawDebugTrace.NONE)
   row={'actor':target.get_name(),'blocked':False}
   if hit:
    hv=hit.to_tuple();row.update(blocked=bool(hv[0] and hv[9]==target and hv[10]==trunk),hit_actor=hv[9].get_path_name() if hv[9] else None,hit_component=hv[10].get_path_name() if hv[10] else None,mesh=hv[10].static_mesh.get_path_name() if isinstance(hv[10],u.StaticMeshComponent) else None)
   tree_hits.append(row)
  report['anime_tree_trunk_hits']=tree_hits
  report['runtime_shadow_counts']=[len([c for c in a.get_components_by_class(u.StaticMeshComponent) if 'AnimeTreeShadow' in [str(t) for t in c.component_tags]]) for a in trees]
  testtree=trees[0];testtree.set_tree_parameters(.31,.62,.73);testtree.refresh_tree()
  report['runtime_parameter_refresh']=all(abs(c.get_material(0).get_scalar_parameter_value('WindStrength')-.31)<1e-5 and abs(c.get_material(0).get_scalar_parameter_value('LeafDensity')-.73)<1e-5 for c in testtree.get_leaf_clumps())
  report['native_logger_count']=''')
s=s.replace("and player['passed']\n except", "and player['passed'] and len(trees)==63 and all(t['blocked'] for t in tree_hits) and all(n==10 for n in report['runtime_shadow_counts']) and report['runtime_parameter_refresh']\n except")
(out/'validate_runtime.py').write_text(s)
s=(out/'capture_before.py').read_text().replace("OUT=ROOT/'Screenshots/Before'","OUT=ROOT/'Screenshots/After'")
start=s.index('choices=[a for a');end=s.index("manifest={'map'",start)
s=s[:start]+'''before=json.loads((ROOT/'Screenshots/Before/capture_manifest.json').read_text())
tree_view=next(v for v in before['views'] if v['name']=='tree_detail')
views.append(dict(tree_view))
tree_class=u.load_class(None,'/Script/ForestUltraTrees.ForestUltraAnimeTreeActor')
trees=[a for a in actors.get_all_level_actors() if isinstance(a,u.ForestUltraAnimeTreeActor)]
for name in ['tree_rim_off','tree_rim_on','tree_rim_debug','tree_gradient_shifted','tree_wind_t0','tree_wind_t1']:
 v=dict(tree_view);v['name']=name;views.append(v)
guide_locations={a.get_name():a.get_editor_property('gradient_guide').get_editor_property('relative_location') for a in trees}
''' + s[end:]
s=s.replace("def set_view(view):\n loc=",'''def set_view(view):
 name=view['name'];cmd('r.ForestUltra.CanopyRim '+('0' if name=='tree_rim_off' else '1'));cmd('r.ForestUltra.CanopyRim.Debug '+('3' if name=='tree_rim_debug' else '0'))
 for a in trees:
  a.set_tree_parameters(0 if name in ['tree_rim_off','tree_rim_on','tree_rim_debug','tree_gradient_shifted'] else .75,.8,.45)
  guide=a.get_editor_property('gradient_guide');p=guide_locations[a.get_name()]
  guide.set_relative_location(p+(u.Vector(450,0,0) if name=='tree_gradient_shifted' else u.Vector()),False,False)
 loc=''')
s=s.replace("(3 if views[index]['name']=='water_t1' else 12)","(3 if views[index]['name'] in ['water_t1','tree_wind_t1'] else 8)")
s=s.replace("if globals().get('RUN_RUNTIME_VALIDATION',False):","if True:")
s+='\nu.EditorPythonScripting.set_keep_python_script_alive(True)\n'
(out/'capture_after.py').write_text(s)
(out/'validate_capture_runtime.py').write_text('''import runpy,json,unreal as u
from pathlib import Path
p=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement')
runpy.run_path(str(p/'validate_level.py'),init_globals={'KEEP_EDITOR_OPEN':True})
if json.loads((p/'validation.json').read_text())['success']:runpy.run_path(str(p/'capture_after.py'))
else:u.SystemLibrary.quit_editor()
''')
print('Prepared fresh map, 63-tree runtime collision, render-toggle and comparable-camera validation scripts.')
