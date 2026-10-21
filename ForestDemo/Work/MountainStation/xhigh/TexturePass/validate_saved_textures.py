import unreal as u,json,math,time,traceback,hashlib,random
from pathlib import Path
from datetime import datetime,timezone
W=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh/TexturePass');R='/Game/MountainStation/xhigh';start=time.time()
rep={'started_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'New process. Saved SourceModel and RenderData LOD0: complete triangle/material inventories, aggregate geometric/UV areas and island count; deterministic samples up to 256 triangles per material per LOD for individual density and placed geometry. Source Blender audit is exhaustive. Saved UE individual densities are sampled, not exhaustive.','materials':{},'meshes':{},'errors':[]}
try:
 assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Maps/MountainStation_xhigh')
 actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
 build=json.loads((W/'Evidence/build_textures.json').read_text());source=json.loads((W/'Evidence/source_uv_validation.json').read_text());lib=u.MaterialEditingLibrary
 for name,b in build['texture_bindings'].items():
  mat=u.load_asset(R+'/Materials/M_'+name);tex=u.load_asset(b['texture']);used=[t.get_path_name() for t in lib.get_used_textures(mat)]
  dims=[tex.blueprint_get_size_x(),tex.blueprint_get_size_y()]
  rep['materials'][name]={'saved_material':mat.get_path_name(),'compiled_used_textures':used,'expected_texture':b['texture'],'resolution':dims,'srgb':tex.get_editor_property('srgb'),'mips':str(tex.get_editor_property('mip_gen_settings')),'address_x':str(tex.get_editor_property('address_x')),'address_y':str(tex.get_editor_property('address_y')),'uv_channel':0,'uv_multiplier':1,'binding_verified':b['texture'] in used}
  if b['texture'] not in used or dims!=[1254,1254]:rep['errors'].append('texture binding/size '+name)
 q=u.GeometryScript_MeshQueries;lst=u.GeometryScript_List;gmat=u.GeometryScript_Materials
 for name,sr in source['assemblies'].items():
  actor=actors['Alder_'+name];comp=actor.static_mesh_component;mesh=comp.static_mesh;scale=comp.get_world_scale();sc=[scale.x,scale.y,scale.z]
  assert all(abs(abs(x)-1)<1e-6 for x in sc),'Unexpected placed scale '+str(sc)
  settings=u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_lod_build_settings(mesh,0)
  mr={'actor':actor.get_path_name(),'component':comp.get_path_name(),'asset':mesh.get_path_name(),'placement_scale':sc,'build_scale':str(settings.get_editor_property('build_scale3d')),'full_precision_uvs':settings.get_editor_property('use_full_precision_u_vs'),'source_reference_area_m2':sr['area_m2'],'lods':{}}
  assert mr['full_precision_uvs']
  for tag,lodtype in [('source',u.GeometryScriptLODType.SOURCE_MODEL),('render',u.GeometryScriptLODType.RENDER_DATA)]:
   dm=u.DynamicMesh();opt=u.GeometryScriptCopyMeshFromAssetOptions();opt.apply_build_settings=True;opt.use_build_scale=True
   requested=u.GeometryScriptMeshReadLOD();requested.lod_type=lodtype;requested.lod_index=0
   ret=u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(mesh,dm,opt,requested,use_section_materials=False)
   assert 'SUCCESS' in str(ret[-1]).upper(),str(ret)
   idsret=q.get_all_triangle_i_ds(dm);ids=list(lst.convert_index_list_to_array(idsret[1]));matret=gmat.get_all_triangle_material_i_ds(dm);mids=list(lst.convert_index_list_to_array(matret[1]))
   ar,vol=q.get_mesh_volume_area(dm);uva,uvvalid=q.get_mesh_uv_area(dm,0);islands,isvalid=q.get_num_uv_islands(dm,0);area=ar/10000
   assert uvvalid and isvalid and area>0
   bymat={}
   for tid in ids:bymat.setdefault(mids[tid],[]).append(tid)
   rows=[];missing=0
   for matid,triangles in sorted(bymat.items()):
    chosen=triangles if len(triangles)<=256 else [triangles[round(i*(len(triangles)-1)/255)] for i in range(256)]
    slotname=str(mesh.static_materials[matid].material_slot_name).split('.')[0]
    for tid in chosen:
     valid,a,b,c=q.get_triangle_positions(dm,tid);x,y,z,hasuv=q.get_triangle_u_vs(dm,0,tid)
     if not valid or not hasuv:missing+=1;continue
     placed=[u.Vector(v.x*scale.x/100,v.y*scale.y/100,v.z*scale.z/100) for v in [a,b,c]]
     pa,pb,pc=placed;aa=u.MathLibrary.cross_vector_vector(pb-pa,pc-pa).length()/2
     au=abs((y.x-x.x)*(z.y-x.y)-(y.y-x.y)*(z.x-x.x))/2
     density=1254*math.sqrt(au/aa) if aa>1e-14 else None
     rows.append({'triangle':tid,'material_slot':slotname,'area_m2':aa,'uv_area':au,'density_px_per_m':density,'target_pixel_area':aa*256**2,'positions_placed_m':[[v.x,v.y,v.z] for v in placed],'uvs':[[v.x,v.y] for v in [x,y,z]],'solid_exception':slotname not in build['texture_bindings']})
   validrows=[r for r in rows if r['density_px_per_m'] is not None];regular=[r for r in validrows if r['target_pixel_area']>=16]
   bad=[r for r in regular if abs(r['density_px_per_m']/256-1)>.02]
   lr={'all_triangles':len(ids),'all_surface_area_m2':area,'all_uv_area':uva,'area_weighted_density_px_per_m':1254*math.sqrt(uva/area),'all_island_count':islands,'material_triangle_counts':{str(k):len(v) for k,v in bymat.items()},'sampled_triangles':len(rows),'missing_samples':missing,'sample_regular_min':min(r['density_px_per_m'] for r in regular),'sample_regular_max':max(r['density_px_per_m'] for r in regular),'sample_regular_outside_2pct':len(bad),'sample_tiny_under_16_target_pixels':sum(r['target_pixel_area']<16 for r in rows),'source_area_relative_difference':abs(area/sr['area_m2']-1),'sample_file':name+'_'+tag+'_uv_samples.json','saved_overlap_padding_scope':'Source full island shelf audit proves >=8px nominal padding in unbounded UV plane. UE island count/UV area and per-material sample coordinates rechecked; no exhaustive saved-UE island intersection/padding claim. Modulo-one tile reuse deliberately overlaps.'}
   (W/'Evidence'/lr['sample_file']).write_text(json.dumps(rows,separators=(',',':')))
   if missing or bad or abs(lr['area_weighted_density_px_per_m']/256-1)>.005 or lr['source_area_relative_difference']>.001:rep['errors'].append(name+' '+tag+' geometry/UV tolerance')
   mr['lods'][tag]=lr;dm.reset();print('SAVED_UV',name,tag,len(ids),len(rows),lr['area_weighted_density_px_per_m'],flush=True)
  rep['meshes'][name]=mr
 rep['private_package_hashes']={str(p.relative_to(Path(u.Paths.project_content_dir()))):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(u.Paths.project_content_dir())/'MountainStation/xhigh').rglob('*.uasset')}
 mp=Path(u.Paths.project_content_dir())/'Maps/MountainStation_xhigh.umap';rep['private_package_hashes']['Maps/MountainStation_xhigh.umap']=hashlib.sha256(mp.read_bytes()).hexdigest()
 rep['success']=not rep['errors']
except Exception:
 rep['success']=False;rep['exception']=traceback.format_exc();u.log_error(rep['exception'])
rep['finished_at_utc']=datetime.now(timezone.utc).isoformat();rep['elapsed_seconds']=time.time()-start
(W/'Evidence/saved_ue_validation.json').write_text(json.dumps(rep,indent=2));assert rep['success'],rep.get('exception',rep['errors'])
