import unreal as u,json,datetime,math,traceback
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/TexturePass/UVRevision';ROOT='/Game/MountainStation/medium';MAP='/Game/Maps/MountainStation_medium'
L=u.get_editor_subsystem(u.LevelEditorSubsystem);E=u.get_editor_subsystem(u.EditorActorSubsystem)
assert L.load_level(MAP)
report={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fresh_process':True,'checks':{}}
import sys,csv
sys.path.insert(0,W)
from uv_audit import audit,bounds
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();settings=world.get_world_settings();partition=settings.get_editor_property('world_partition')
report['world_path']=world.get_path_name();report['partition_is_none']=partition is None;report['checks']['direct_non_world_partition']=partition is None and report['world_path']==MAP+'.MountainStation_medium'
mapping=json.load(open(W+'/material_mapping.json'));mesh=u.load_asset(mapping['mesh']);a=next(a for a in E.get_all_level_actors() if a.get_actor_label().startswith('Alder Pass |'))
report['actor']=a.get_path_name();report['scale']=list(a.get_actor_scale3d().to_tuple());report['checks']['saved_actor_mesh']=a.static_mesh_component.static_mesh==mesh
report['checks']['unit_world_scale']=all(abs(x-1)<1e-6 for x in report['scale'])
report['materials']=[]
for rec in mapping['materials']:
 m=u.load_asset(rec['material']);textures=[t.get_path_name() for t in u.MaterialEditingLibrary.get_used_textures(m)];node=u.MaterialEditingLibrary.get_material_property_input_node(m,u.MaterialProperty.MP_BASE_COLOR)
 actual={'material':m.get_path_name(),'textures':textures,'base_color_input':node.get_class().get_name() if node else None}
 actual['passed']=bool(node) and (rec['expected_texture'] in textures if rec['expected_texture'] else not textures);report['materials'].append(actual)
 if rec['expected_texture']:
  actual['packed_uv_scale']=u.MaterialEditingLibrary.get_material_default_scalar_parameter_value(m,'PackedUVScale')
  todo_nodes=[node];seen_nodes=set();classes=[];params=[]
  while todo_nodes:
   n=todo_nodes.pop()
   if not n or n.get_path_name() in seen_nodes:continue
   seen_nodes.add(n.get_path_name());classes.append(n.get_class().get_name())
   if isinstance(n,u.MaterialExpressionScalarParameter):
    params.append(str(n.get_editor_property('parameter_name')))
    if str(n.get_editor_property('parameter_name'))=='PackedUVScale':actual['custom_primitive_scaling']=n.get_editor_property('use_custom_primitive_data') and n.get_editor_property('primitive_data_index')==0
   todo_nodes+=list(u.MaterialEditingLibrary.get_inputs_for_material_expression(m,n))
  actual['base_color_upstream_classes']=classes;actual['upstream_parameters']=params
  actual['passed']=actual['passed'] and actual['packed_uv_scale']==1 and actual.get('custom_primitive_scaling',False) and 'PackedUVScale' in params and 'MaterialExpressionFrac' in classes and 'MaterialExpressionTextureCoordinate' in classes
report['checks']['material_texture_links']=all(r['passed'] for r in report['materials'])
report['checks']['mesh_material_slots']=all(mesh.get_material(r['slot']).get_path_name()==r['material'] for r in mapping['slots'])
reg=u.AssetRegistryHelpers.get_asset_registry();reg.scan_paths_synchronous([ROOT],force_rescan=True);opt=u.AssetRegistryDependencyOptions(True,True,False,False,False)
todo=[MAP]+[str(x.package_name) for x in reg.get_assets_by_path(ROOT,recursive=True)];deps={};bad=[]
while todo:
 p=todo.pop()
 if p in deps:continue
 children=[str(x) for x in reg.get_dependencies(p,opt)];deps[p]=children
 for ch in children:
  if ch.startswith('/Game/'):
   if ch==MAP or ch.startswith(ROOT+'/'):todo.append(ch)
   else:bad.append(ch)
report['dependencies']=deps;report['foreign_dependencies']=sorted(set(bad));report['checks']['all_owned_asset_dependencies_scoped']=not bad
dm=u.DynamicMesh();lod=u.GeometryScriptMeshReadLOD();lod.lod_type=u.GeometryScriptLODType.RENDER_DATA;lod.lod_index=0
copied=u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(mesh,dm,u.GeometryScriptCopyMeshFromAssetOptions(),lod)
report['copy_result']=str(copied);Q=u.GeometryScript_MeshQueries
report['uv_sets']=Q.get_num_uv_sets(dm);report['uv_islands_result']=str(Q.get_num_uv_islands(dm,0))
packed_tris=[];count=next(getattr(Q,n) for n in dir(Q) if n.replace('_','').lower()=='getnumtriangleids')(dm);rows=[];invalid=0;area_total=0;large=[];all_d=[];stable=[];outliers=[];thin=0
for i in range(count):
 if not next(getattr(Q,n) for n in dir(Q) if n.replace('_','').lower()=='isvalidtriangleid')(dm,i):continue
 valid,p0,p1,p2=Q.get_triangle_positions(dm,i);v0,v1,v2,uvvalid=Q.get_triangle_u_vs(dm,0,i)
 if not valid or not uvvalid:invalid+=1;continue
 packed_tris.append({'p':[[v.x,v.y,v.z] for v in [p0,p1,p2]],'uv':[[v.x,v.y] for v in [v0,v1,v2]]})
 ab=[p1.x-p0.x,p1.y-p0.y,p1.z-p0.z];ac=[p2.x-p0.x,p2.y-p0.y,p2.z-p0.z]
 cross=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]];area=math.sqrt(sum(x*x for x in cross))*.5/10000
 uvarea=abs((v1.x-v0.x)*(v2.y-v0.y)-(v1.y-v0.y)*(v2.x-v0.x))*.5
 if area<=1e-16:continue
 density=math.sqrt(uvarea*448**2/area);all_d.append(density);area_total+=area
 edge_max=max(math.sqrt(sum(x*x for x in ab)),math.sqrt(sum(x*x for x in ac)),math.sqrt((p2.x-p1.x)**2+(p2.y-p1.y)**2+(p2.z-p1.z)**2))/100
 min_altitude_px=2*area/edge_max*128 if edge_max else 0
 if area*128*128>=4:
  large.append(density)
  if min_altitude_px>=.25:stable.append(density)
  else:thin+=1
  if abs(density-128)>2.56:
   material_id,material_valid=next(getattr(u.GeometryScript_Materials,n) for n in dir(u.GeometryScript_Materials) if n.replace('_','').lower()=='gettrianglematerialid')(dm,i)
   label_region=(abs(p0.y-319)<3 and 250<p0.z<290 and (-2500<p0.x<-2100 or 1200<p0.x<1600)) or (abs(p0.y+599)<3 and 350<p0.z<400 and 1700<p0.x<2100)
   exception=material_valid and material_id==7 and area<.001 and min_altitude_px<2 and label_region
   outliers.append({'documented_lettering_exception':bool(exception),'material_slot':material_id,'triangle':i,'area_m2':area,'density_px_m':density,'min_altitude_px':min_altitude_px,'vertices_cm':[[v.x,v.y,v.z] for v in [p0,p1,p2]]})
def stats(values):
 v=sorted(values);return {'count':len(v),'min':v[0],'median':v[len(v)//2],'max':v[-1],'outside_2_percent':sum(abs(x-128)>2.56 for x in v)} if v else {}
report['saved_render_lod0']={'triangle_id_count':count,'audited_triangles':len(all_d),'invalid':invalid,'world_surface_area_m2':area_total,'all_triangle_density_px_m':stats(all_d),'at_least_four_target_texels_density_px_m':stats(large),'tiny_triangle_count':len(all_d)-len(large),'subquarterpixel_width_large_triangles':thin,'resolved_surface_density_px_m':stats(stable),'non_tiny_outliers':outliers,'scope':'Every valid RenderData LOD0 triangle, unit actor scale; material atlas usable 448px, including intentionally untextured glass/dark UVs','overlap':'Unique packed UV0; shader custom primitive scale followed by Frac reuses source pixels only after geometric UV allocation. 8 effective pixels per island side, 16 target inter-island gap.'}
report['checks']['all_saved_uv_valid']=invalid==0 and len(all_d)>0
report['checks']['density_with_recorded_lettering_exceptions']=bool(large) and all(r['documented_lettering_exception'] for r in outliers)
packing,island_groups=audit(packed_tris,448);report['saved_uv_packing']=packing
report['checks']['saved_uv_no_overlap']=packing['positive_area_overlap_pairs']==0
report['checks']['saved_island_gap']=packing['minimum_island_bbox_gap_pixels_within_32px_search'] is not None and packing['minimum_island_bbox_gap_pixels_within_32px_search']>=15.8
sms=u.get_editor_subsystem(u.StaticMeshEditorSubsystem);report['full_precision_uv']=sms.get_lod_build_settings(mesh,0).get_editor_property('use_full_precision_u_vs');report['checks']['full_precision_uv']=report['full_precision_uv']
with open(W+'/saved_uv_islands.csv','w',newline='') as f:
 writer=csv.writer(f);writer.writerow(['island','triangles','min_u','min_v','max_u','max_v'])
 for i,ids in enumerate(island_groups):writer.writerow([i,len(ids)]+bounds([v for t in ids for v in packed_tris[t]['uv']]))
tree_mapping=json.load(open(W+'/tree_instance_mapping.json'));tree_mesh=u.load_asset(tree_mapping['mesh']);tree_dm=u.DynamicMesh();u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(tree_mesh,tree_dm,u.GeometryScriptCopyMeshFromAssetOptions(),lod)
tree_tris=[];tree_density=[];tree_area=0
for i in range(next(getattr(Q,n) for n in dir(Q) if n.replace('_','').lower()=='getnumtriangleids')(tree_dm)):
 valid,p0,p1,p2=Q.get_triangle_positions(tree_dm,i);v0,v1,v2,valid_uv=Q.get_triangle_u_vs(tree_dm,0,i)
 assert valid and valid_uv
 pp=[p0,p1,p2];vv=[v0,v1,v2];tree_tris.append({'p':[[v.x,v.y,v.z] for v in pp],'uv':[[v.x,v.y] for v in vv]})
 ab=[p1.x-p0.x,p1.y-p0.y,p1.z-p0.z];ac=[p2.x-p0.x,p2.y-p0.y,p2.z-p0.z];cross=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]];area=math.sqrt(sum(x*x for x in cross))*.5/10000;ua=abs((v1.x-v0.x)*(v2.y-v0.y)-(v1.y-v0.y)*(v2.x-v0.x))*.5
 tree_area+=area;tree_density.append(math.sqrt(ua*448**2/area))
tree_packing,_=audit(tree_tris,448);report['tree_uv_packing']=tree_packing;report['tree_prototype_density']=stats(tree_density)
instances=[];expanded_density=[];expanded_area=0
for actor in E.get_all_level_actors():
 if not actor.get_actor_label().startswith('Shared Pine |'):continue
 scale=actor.get_actor_scale3d();comp=actor.static_mesh_component;data=list(comp.get_editor_property('custom_primitive_data').get_editor_property('data'))
 idx=int(actor.get_actor_label().split('|')[1]);expected=tree_mapping['instances'][idx];loc=actor.get_actor_location();expected_loc=u.Vector(*[v*100 for v in expected['location_m']])
 passed=comp.static_mesh==tree_mesh and abs(scale.x-scale.y)<1e-6 and abs(scale.x-scale.z)<1e-6 and len(data)>0 and abs(data[0]-scale.x)<1e-6 and loc.distance(expected_loc)<.01 and abs(scale.x-expected['scale'])<1e-6
 instances.append({'actor':actor.get_path_name(),'mesh':comp.static_mesh.get_path_name(),'scale':[scale.x,scale.y,scale.z],'shader_scale':data[0] if data else None,'passed':passed})
 if passed:expanded_density.extend([d*data[0]/scale.x for d in tree_density]);expanded_area+=tree_area*scale.x*scale.x
report['tree_instances']=instances;report['tree_instance_world_density']=stats(expanded_density);report['tree_instanced_world_area_m2']=expanded_area
report['checks']['shared_tree_mesh_instances']=len(instances)==64 and all(i['passed'] for i in instances)
report['checks']['tree_world_density']=len(expanded_density)==64*len(tree_tris) and all(abs(d-128)<2.56 for d in expanded_density)
report['checks']['tree_uv_packing']=tree_packing['positive_area_overlap_pairs']==0 and tree_packing['minimum_island_bbox_gap_pixels_within_32px_search']>=15.8
report['passed']=all(report['checks'].values());report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();json.dump(report,open(W+'/saved_asset_validation.json','w'),indent=2)
assert report['passed'],report['checks']
exec(compile(open(W+'/runtime_verify.py',encoding='utf-8-sig').read(),W+'/runtime_verify.py','exec'),globals())






