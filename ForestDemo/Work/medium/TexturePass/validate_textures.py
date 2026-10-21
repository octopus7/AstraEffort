tex_report={'status':'working','meshes':{},'instances':[],'water':[]}
owned_redirectors=[str(a.package_name) for a in reg.get_assets_by_path('/Game/Forest/medium',recursive=True) if str(a.asset_class_path.asset_name)=='ObjectRedirector']
assert not owned_redirectors
tex_report['owned_redirectors']=owned_redirectors
def density_from_saved_mesh(mesh):
 desc=mesh.get_static_mesh_description(0);ds=[];area=0.;uvarea=0.
 for index in range(desc.get_triangle_count()):
  tid=u.TriangleID();tid.set_editor_property('id_value',index)
  assert desc.is_triangle_valid(tid)
  vi=desc.get_triangle_vertex_instances(tid)
  p=[desc.get_vertex_position(desc.get_vertex_instance_vertex(v)) for v in vi]
  uv=[desc.get_vertex_instance_uv(v,0) for v in vi]
  a=p[1]-p[0];b=p[2]-p[0];cross=(a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x);wa=math.sqrt(sum(x*x for x in cross))/2/10000
  ua=abs((uv[1].x-uv[0].x)*(uv[2].y-uv[0].y)-(uv[1].y-uv[0].y)*(uv[2].x-uv[0].x))/2
  if wa>1e-12:ds.append(math.sqrt(ua*1254**2/wa));area+=wa;uvarea+=ua
 assert min(ds)>15.9 and max(ds)<16.1,(mesh.get_name(),min(ds),max(ds))
 return {'triangle_count':len(ds),'min_pixels_per_meter':min(ds),'max_pixels_per_meter':max(ds),'world_surface_area_m2':area,'uv_area':uvarea}
tex=u.load_asset('/Game/Forest/medium/Textures/T_SurfaceAtlas');assert tex
variants={x['name']:x for x in json.load(open(ROOT+'/uv_validation.json'))['meshes']}
roundtrips={x['mesh']:x for x in json.load(open(ROOT+'/fbx_roundtrip_validation.json'))['meshes']}
for a in allactors:
 if not isinstance(a,u.StaticMeshActor):continue
 comp=a.static_mesh_component;mesh=comp.static_mesh;name=mesh.get_name()
 if name in variants:
  scale=a.get_actor_scale3d();assert abs(scale.x-1)<1e-6 and abs(scale.y-1)<1e-6 and abs(scale.z-1)<1e-6
  tex_report['instances'].append({'actor':a.get_name(),'mesh':name,'scale':str(scale)})
  if name not in tex_report['meshes']:
   uvchannels=ss.get_num_uv_channels(mesh,0);assert uvchannels>=1
   full_precision=ss.get_lod_build_settings(mesh,0).get_editor_property('use_full_precision_u_vs');assert full_precision
   extent=mesh.get_bounds().box_extent;actual=sorted([extent.x*2,extent.y*2,extent.z*2]);expected=sorted([x*100 for x in roundtrips[name]['bounds_m']]);assert all(abs(a-b)<.2 for a,b in zip(actual,expected)),(name,actual,expected)
   slots=[]
   for i,s in enumerate(mesh.static_materials):
    mat=comp.get_material(i);used=u.MaterialEditingLibrary.get_used_textures(mat);assert tex in used
    slots.append({'material':mat.get_path_name(),'textures':[t.get_path_name() for t in used]})
   tex_report['meshes'][name]={'uv_channels':uvchannels,'imported_dimensions_cm_sorted':actual,'fbx_dimensions_cm_sorted':expected,'materials':slots,'measured_source_uv':variants[name]}
   tex_report['meshes'][name]['saved_mesh_uv_measurement']=density_from_saved_mesh(mesh)
   tex_report['meshes'][name]['full_precision_uvs']=bool(full_precision)
   if name.startswith(('Tree','Rock','Shrub','Log')):
    collisions=ss.get_simple_collision_count(mesh)+ss.get_convex_collision_count(mesh);assert collisions>0
    tex_report['meshes'][name]['solid_collision_shapes']=collisions
 elif name=='SeaWaves':
  assert comp.get_material(0).get_name()=='MT_SeaAnimated';tex_report['water'].append({'actor':a.get_name(),'mesh':mesh.get_path_name(),'material':comp.get_material(0).get_path_name()})
assert len(tex_report['instances'])==len(json.load(open(ROOT+'/../layout.json'))['layout'])
assert len(tex_report['water'])==1
assert set(variants)==set(tex_report['meshes'])
tex_report['status']='passed';json.dump(tex_report,open(ROOT+'/texture_application_validation.json','w'),indent=2)
