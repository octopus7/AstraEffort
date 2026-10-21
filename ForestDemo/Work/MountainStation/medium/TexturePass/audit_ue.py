import unreal as u,json,datetime,math,traceback
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/TexturePass';ROOT='/Game/MountainStation/medium';MAP='/Game/Maps/MountainStation_medium'
L=u.get_editor_subsystem(u.LevelEditorSubsystem);E=u.get_editor_subsystem(u.EditorActorSubsystem)
assert L.load_level(MAP)
report={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fresh_process':True,'checks':{}}
mapping=json.load(open(W+'/material_mapping.json'));mesh=u.load_asset(mapping['mesh']);a=next(a for a in E.get_all_level_actors() if a.get_actor_label().startswith('Alder Pass |'))
report['actor']=a.get_path_name();report['scale']=list(a.get_actor_scale3d().to_tuple());report['checks']['saved_actor_mesh']=a.static_mesh_component.static_mesh==mesh
report['checks']['unit_world_scale']=all(abs(x-1)<1e-6 for x in report['scale'])
report['materials']=[]
for rec in mapping['materials']:
 m=u.load_asset(rec['material']);textures=[t.get_path_name() for t in u.MaterialEditingLibrary.get_used_textures(m)];node=u.MaterialEditingLibrary.get_material_property_input_node(m,u.MaterialProperty.MP_BASE_COLOR)
 actual={'material':m.get_path_name(),'textures':textures,'base_color_input':node.get_class().get_name() if node else None}
 actual['passed']=bool(node) and (rec['expected_texture'] in textures if rec['expected_texture'] else not textures);report['materials'].append(actual)
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
count=next(getattr(Q,n) for n in dir(Q) if n.replace('_','').lower()=='getnumtriangleids')(dm);rows=[];invalid=0;area_total=0;large=[];all_d=[];stable=[];outliers=[];thin=0
for i in range(count):
 if not next(getattr(Q,n) for n in dir(Q) if n.replace('_','').lower()=='isvalidtriangleid')(dm,i):continue
 valid,p0,p1,p2=Q.get_triangle_positions(dm,i);v0,v1,v2,uvvalid=Q.get_triangle_u_vs(dm,0,i)
 if not valid or not uvvalid:invalid+=1;continue
 ab=[p1.x-p0.x,p1.y-p0.y,p1.z-p0.z];ac=[p2.x-p0.x,p2.y-p0.y,p2.z-p0.z]
 cross=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]];area=math.sqrt(sum(x*x for x in cross))*.5/10000
 uvarea=abs((v1.x-v0.x)*(v2.y-v0.y)-(v1.y-v0.y)*(v2.x-v0.x))*.5
 if area<=1e-16:continue
 density=math.sqrt(uvarea*448*448/area);all_d.append(density);area_total+=area
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
report['saved_render_lod0']={'triangle_id_count':count,'audited_triangles':len(all_d),'invalid':invalid,'world_surface_area_m2':area_total,'all_triangle_density_px_m':stats(all_d),'at_least_four_target_texels_density_px_m':stats(large),'tiny_triangle_count':len(all_d)-len(large),'subquarterpixel_width_large_triangles':thin,'resolved_surface_density_px_m':stats(stable),'non_tiny_outliers':outliers,'scope':'Every valid RenderData LOD0 triangle, unit actor scale; material atlas usable 448px, including intentionally untextured glass/dark UVs','overlap':'Intentional repeating planar charts; no unique UV packing; 32px inset at each source panel edge. Curved facets may seam.'}
report['checks']['all_saved_uv_valid']=invalid==0 and len(all_d)>0
report['checks']['density_with_recorded_lettering_exceptions']=bool(large) and all(r['documented_lettering_exception'] for r in outliers)
report['passed']=all(report['checks'].values());report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();json.dump(report,open(W+'/saved_asset_validation.json','w'),indent=2)
assert report['passed'],report['checks']
exec(compile(open(W+'/runtime_verify.py',encoding='utf-8-sig').read(),W+'/runtime_verify.py','exec'),globals())




