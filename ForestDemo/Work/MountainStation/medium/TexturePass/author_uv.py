import bpy,bmesh,json,os,math,csv,time,datetime
from mathutils import Vector,Matrix
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/TexturePass'
start=time.time(); bpy.ops.wm.open_mainfile(filepath=os.path.dirname(W)+'/AlderPass.blend')
atlas=bpy.data.images.load(W+'/Source/SurfaceAtlas.png',check_existing=True)
width,height=atlas.size; guard=32; pw=width/3-2*guard; ph=height/2-2*guard; target=128.0
bark=bpy.data.materials.new('bark'); bark.diffuse_color=(.36,.23,.14,1)
mapping={'wood':0,'woodlight':0,'cream':1,'stone':2,'rock':2,'gravel':2,'path':2,'white':2,'brick':1,'roof':3,'metal':3,'rail':3,'gold':3,'bark':4,'leaf':5,'leaf2':5,'grass':2,'edge':2}
rows=[]; all_d=[]; large_d=[]; outliers=[]; groups={}; skips=0; small=0; islands=0; curved=0
objects=sorted([o for o in bpy.context.scene.objects if o.type=='MESH'],key=lambda o:o.name)
for oi,o in enumerate(objects):
 if o.name.startswith('Pine trunk'):
  o.data.materials.clear(); o.data.materials.append(bark)
 if o.data.users>1:o.data=o.data.copy()
 mat=o.matrix_world.copy(); origin=mat.translation.copy(); o.data.transform(mat); o.matrix_world=Matrix.Identity(4)
 me=o.data; bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm,faces=list(bm.faces)); bm.to_mesh(me); bm.free(); me.update()
 while me.uv_layers: me.uv_layers.remove(me.uv_layers[0])
 uv=me.uv_layers.new(name='SurfaceMetric_128ppm')
 points=[v.co for v in me.vertices]; ext=[max(p[k] for p in points)-min(p[k] for p in points) for k in range(3)]
 major=sorted(range(3),key=lambda k:ext[k],reverse=True)
 ref=Vector(tuple(1 if k==major[0] else 0 for k in range(3)))
 densities=[]; area_sum=0; uv_sum=0; charts=set(); tiny=0
 for f in me.polygons:
  n=f.normal.copy(); v=ref-n*ref.dot(n)
  if v.length<.05:
   second=Vector(tuple(1 if k==major[1] else 0 for k in range(3))); v=second-n*second.dot(n)
  v.normalize(); uu=v.cross(n).normalized()
  # Exact planar metric projection: texture repeat footprint is 3.5m for a 448px usable swatch.
  for li in f.loop_indices:
   p=me.vertices[me.loops[li].vertex_index].co-origin
   uv.data[li].uv=(p.dot(uu)*target/pw+.5,p.dot(v)*target/ph+.5)
  pts=[me.vertices[me.loops[i].vertex_index].co for i in f.loop_indices]
  uvs=[uv.data[i].uv.copy() for i in f.loop_indices]
  a=(pts[1]-pts[0]).cross(pts[2]-pts[0]).length*.5
  ua=abs((uvs[1].x-uvs[0].x)*(uvs[2].y-uvs[0].y)-(uvs[2].x-uvs[0].x)*(uvs[1].y-uvs[0].y))*.5
  if a<1e-12: skips+=1; continue
  density=math.sqrt(ua*pw*ph/a); densities.append(density); all_d.append(density); area_sum+=a; uv_sum+=ua
  if a*target*target<4: tiny+=1; small+=1
  else:
   large_d.append(density)
   if abs(density-target)>target*.02: outliers.append({'object':o.name,'face':f.index,'area_m2':a,'density':density})
  charts.add(tuple(round(c,4) for c in n)+tuple(round(n.dot(pts[0]),4) for _ in range(1)))
  m=me.materials[f.material_index].name if me.materials else 'none'
  g=groups.setdefault(m,{'triangles':0,'area_m2':0,'uv_area':0,'min_ppm':1e9,'max_ppm':0,'textured':m in mapping,'swatch':mapping.get(m)})
  g['triangles']+=1;g['area_m2']+=a;g['uv_area']+=ua;g['min_ppm']=min(g['min_ppm'],density);g['max_ppm']=max(g['max_ppm'],density)
 for e in me.edges: e.use_seam=True
 islands+=len(charts)
 if len(charts)>6:curved+=1
 rows.append({'object':o.name,'original_world_scale':list(mat.to_scale()),'applied_scale':[1,1,1],'triangles':len(me.polygons),'area_m2':area_sum,'uv_area':uv_sum,'area_weighted_ppm':math.sqrt(uv_sum*pw*ph/area_sum) if area_sum else 0,'min_ppm':min(densities) if densities else 0,'max_ppm':max(densities) if densities else 0,'planar_chart_groups':len(charts),'under_4_texel_triangles':tiny})
 if oi%200==0:print('UV_OBJECT',oi,len(objects),flush=True)
with open(W+'/source_uv_objects.csv','w',newline='',encoding='utf-8') as f:
 writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
def pct(vals,q):return sorted(vals)[int((len(vals)-1)*q)]
report={'started_at_utc':datetime.datetime.fromtimestamp(start,datetime.timezone.utc).isoformat(),'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'execution_seconds':time.time()-start,'scope':'all authored source mesh objects and all nondegenerate triangles; object transforms applied in metres before UV construction','object_count':len(objects),'triangle_count':sum(r['triangles'] for r in rows),'target_pixels_per_metre':target,'atlas_size':[width,height],'grid':[3,2],'swatch_guard_px':guard,'usable_swatch_px':[pw,ph],'physical_repeat_metres':[pw/target,ph/target],'area_m2':sum(r['area_m2'] for r in rows),'density_ppm':{'min':min(all_d),'p01':pct(all_d,.01),'median':pct(all_d,.5),'p99':pct(all_d,.99),'max':max(all_d)},'materials':groups,'planar_chart_group_count':islands,'objects_over_6_chart_groups':curved,'degenerate_triangles_excluded':skips,'triangles_under_4_target_texels':small,'overlap_policy':'UV0 is a repeating metric surface map, not a unique baked atlas. Within each coplanar chart coordinates are coherent; cross-chart and repeated-object overlaps are intentional. Material Frac wraps into its own swatch. No claim of globally overlap-free UVs.','padding':'32 source pixels inset on each swatch edge; no padding between UV0 islands because they intentionally sample a repeating surface, not island-specific baked paint.','curved_surface_policy':'Each triangulated face is mapped isometrically; coplanar triangles share coordinates. Curved facets can split charts and show phase seams. Density measures faceted geometric area, not an analytic smoothed surface.','special_material_exceptions':['glass and dark remain untextured; their UV geometry is still measured','Engine backdrop excluded; no authored texture required','tiny bevel/text faces below 4 target texels are retained and reported; subpixel appearance cannot be guaranteed'],'mapping':mapping}
report['triangles_at_least_4_texels_density']={'count':len(large_d),'min':min(large_d),'median':pct(large_d,.5),'max':max(large_d),'over_2_percent_error_count':len(outliers),'outliers':outliers[:100]}
json.dump(report,open(W+'/source_uv_validation.json','w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=W+'/Source/AlderPass_UV.blend')
bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
o=bpy.context.object;o.data.transform(Matrix.Diagonal((1,-1,1,1)));o.data.flip_normals();o.data.update()
bpy.ops.export_scene.fbx(filepath=W+'/Source/AlderPass_UV.fbx',use_selection=True,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',add_leaf_bones=False,bake_anim=False,mesh_smooth_type='FACE')
print('UV_SOURCE_COMPLETE',json.dumps({'objects':len(objects),'triangles':report['triangle_count'],'area':report['area_m2'],'density':report['density_ppm']}),flush=True)
