import bpy,csv,math,json
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/TexturePass/UVRevision'
bpy.ops.wm.open_mainfile(filepath=W+'/Source/SharedScene.blend')
rows=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 a_sum=0;uv_sum=0;ds=[];resolved=[]
 for f in o.data.polygons:
  p=[o.matrix_world@o.data.vertices[o.data.loops[i].vertex_index].co for i in f.loop_indices];uv=[o.data.uv_layers[0].data[i].uv for i in f.loop_indices]
  a=(p[1]-p[0]).cross(p[2]-p[0]).length*.5;ua=abs((uv[1].x-uv[0].x)*(uv[2].y-uv[0].y)-(uv[1].y-uv[0].y)*(uv[2].x-uv[0].x))*.5;a_sum+=a;uv_sum+=ua
  if a>0:
   d=math.sqrt(ua*448**2/a);ds.append(d)
   if a*128**2>=4:resolved.append(d)
 rows.append({'object':o.name,'world_scale':list(o.matrix_world.to_scale()),'area_m2':a_sum,'uv_area':uv_sum,'area_weighted_density':math.sqrt(uv_sum*448**2/a_sum) if a_sum else None,'density_min':min(ds) if ds else None,'density_max':max(ds) if ds else None,'resolved_density_min':min(resolved) if resolved else None,'resolved_density_max':max(resolved) if resolved else None,'triangles':len(o.data.polygons),'resolved_triangles':len(resolved)})
with open(W+'/source_object_metrics.csv','w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
print('SOURCE_OBJECT_METRICS',len(rows))
