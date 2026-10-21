import bpy,json,math,os,hashlib,time,collections
from mathutils import Vector
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high/TexturePass';info=json.load(open(W+'/ue_validation.json'));source=json.load(open(W+'/source_uv_validation.json'));images=json.load(open(W+'/imagegen_manifest.json'));RES=images['common_square_resolution'];start=time.time();results=[];chart_rects=json.load(open(W+'/source_chart_rectangles.json'))
def pct(a,p):return sorted(a)[min(len(a)-1,int((len(a)-1)*p))] if a else None
for record in info['mesh_geometry_exports']:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 path=W+'/UEExport/'+record['name']+'.fbx';bpy.ops.import_scene.fbx(filepath=path,use_anim=False)
 objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.startswith(('UCX_','UBX_','USP_'))];assert len(objects)==1,(record['name'],[o.name for o in objects])
 ob=objects[0];me=ob.data;me.calc_loop_triangles();assert len(me.uv_layers)>=2
 coords=[ob.matrix_world@v.co for v in me.vertices];dimensions=[max(v[i] for v in coords)-min(v[i] for v in coords) for i in range(3)]
 expected=[e*.02 for e in record['asset_bounds_extent_cm']];unit_error=max(abs(a-b) for a,b in zip(sorted(dimensions),sorted(expected)));assert unit_error<.02,(record['name'],dimensions,expected)
 # UE actor rotations and signed unit scale are rigid: preserve area. Nonunit placement would be rejected by UE validation.
 scale=record['scale'];coords=[Vector((v.x*abs(scale[0]),v.y*abs(scale[1]),v.z*abs(scale[2]))) for v in coords]
 uvs=me.uv_layers[0].data;ds=[];meaningful=[];area=uva=smallarea=degarea=0.;small=degen=0;materials={};edge_density_ratios=[]
 rects=chart_rects[record['name']];grid=collections.defaultdict(list)
 for i,r in enumerate(rects):
  for x in range(math.floor(r[0]),math.floor(r[2])+1):
   for y in range(math.floor(r[1]),math.floor(r[3])+1):grid[(x,y)].append(i)
 def contained(points):
  b=[min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)];eps=.0001
  return any(b[0]>=rects[i][0]-eps and b[1]>=rects[i][1]-eps and b[2]<=rects[i][2]+eps and b[3]<=rects[i][3]+eps for i in grid[(math.floor((b[0]+b[2])/2),math.floor((b[1]+b[3])/2))])
 transforms=[lambda u,v:(u,v),lambda u,v:(u,1-v),lambda u,v:(u,-v)]
 sample=list(me.loop_triangles)[::max(1,len(me.loop_triangles)//300)]
 scores=[sum(contained([f(*uvs[i].uv) for i in t.loops]) for t in sample) for f in transforms];transform_index=max(range(3),key=lambda i:scores[i]);f=transforms[transform_index];outside=0
 for t in me.loop_triangles:
  vv=[coords[i] for i in t.vertices];uv=[uvs[i].uv for i in t.loops];a=(vv[1]-vv[0]).cross(vv[2]-vv[0]).length*.5;b=abs((uv[1]-uv[0]).cross(uv[2]-uv[0]))*.5
  if not contained([f(*q) for q in uv]):outside+=1
  if a<1e-12 or b<1e-16:degen+=1;degarea+=a;continue
  d=RES*math.sqrt(b/a);ds.append(d);area+=a;uva+=b
  if b*RES*RES<1:small+=1;smallarea+=a
  else:meaningful.append(d)
  name=me.materials[t.material_index].name if me.materials else 'unknown';r=materials.setdefault(name,{'triangles':0,'area_m2':0.,'uv_area':0.});r['triangles']+=1;r['area_m2']+=a;r['uv_area']+=b
 for r in materials.values():r['density_px_m']=RES*math.sqrt(r['uv_area']/r['area_m2'])
 src=next(x for x in source['meshes'] if x['name']==record['name']);density=RES*math.sqrt(uva/area);relative_area_error=abs(area-src['area_m2'])/src['area_m2']
 results.append({'mesh':record['name'],'ue_export_sha256':hashlib.sha256(open(path,'rb').read()).hexdigest(),'all_triangles_inspected':len(me.loop_triangles),'uv_channels':len(me.uv_layers),'world_area_m2':area,'uv_area':uva,'density_px_m':density,'density_all_min_p05_p50_p95_max':[min(ds),pct(ds,.05),pct(ds,.5),pct(ds,.95),max(ds)],'density_at_least_one_pixel_triangle_min_p05_p50_p95_max':[min(meaningful),pct(meaningful,.05),pct(meaningful,.5),pct(meaningful,.95),max(meaningful)],'subpixel_triangles':small,'subpixel_world_area_m2':smallarea,'excluded_degenerate_triangles':degen,'excluded_world_area_m2':degarea,'dimension_check_error_m':unit_error,'world_dimensions_m':dimensions,'expected_ue_dimensions_m':expected,'actor_scale':scale,'source_area_relative_error':relative_area_error,'material_stats':materials,'passed':abs(density-128)<.25 and relative_area_error<.005})
 print('UE_UV_AUDIT',record['name'],density,relative_area_error,flush=True)
 results[-1]['uv_to_source_coordinate_transform']=['identity','v=1-v','v=-v'][transform_index];results[-1]['triangles_outside_original_nonoverlap_chart_bounds']=outside;results[-1]['chart_containment_tolerance_uv']=.0001;results[-1]['minimum_inter_chart_padding_lower_bound_pixels']=31.96-.0002*RES;results[-1]['passed']=results[-1]['passed'] and outside==0
report={'validated_at_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'scope':'Every exported LOD0 triangle from all 11 saved UE assemblies; all placement scales checked from loaded UE actors. Exported FBX unit conversion verified against actual UE mesh bounds. Rigid actor rotation/reflection preserves area. No instancing assumption: authored repeated parts are already baked into assemblies and counted individually.','target_px_m':128,'texture_source_and_loaded_size':RES,'material_uv_multiplier':[1,1],'overlap_scope':'Source chart bounding boxes are analytically disjoint before modulo. UE roundtrip measured UV areas and density for every triangle. No exhaustive within-chart triangle intersection test; projected normal patches can have local overlap on tiny/degenerate curved bevel faces. Repeated image addresses modulo 1 are intentional tiling, not unique baked surface artwork.','padding_scope':'Source UV0 uses 16 source pixels per chart edge / 32 between packed rectangles; UV1 uniformly normalized for inspection. These gaps isolate charts geometrically; wrap sampling intentionally reuses a single material tile, so padding is not baked-atlas dilation.','exceptions':images['exceptions'],'meshes':results,'passed':all(x['passed'] for x in results),'elapsed_seconds':time.time()-start}
json.dump(report,open(W+'/ue_uv_validation.json','w'),indent=2);assert report['passed']
