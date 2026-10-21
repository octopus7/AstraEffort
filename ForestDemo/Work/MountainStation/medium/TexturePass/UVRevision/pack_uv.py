import bpy,sys,os,json,time,datetime,math,csv
from mathutils import Matrix
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/TexturePass/UVRevision';sys.path.insert(0,W)
from uv_audit import audit,bounds,components,overlap
start=time.time();bpy.ops.wm.open_mainfile(filepath=os.path.dirname(W)+'/Source/AlderPass_UV.blend')
objects=sorted([o for o in bpy.context.scene.objects if o.type=='MESH'],key=lambda o:o.name);charts=[];object_rows=[]
for o in objects:
 me=o.data;uv=me.uv_layers[0];tris=[]
 for f in me.polygons:
  tris.append({'p':[list(me.vertices[me.loops[li].vertex_index].co) for li in f.loop_indices],'uv':[list(uv.data[li].uv) for li in f.loop_indices]})
 groups=components(tris)
 for ids in groups:
  # Existing connected charts are planar; test their interiors before packing.
  b=bounds([p for i in ids for p in tris[i]['uv']]);charts.append({'object':o,'faces':ids,'bounds':b})
 object_rows.append({'object':o.name,'world_scale':list(o.matrix_world.to_scale()),'triangles':len(tris),'connected_uv_islands':len(groups)})
# Shelf packing bounds with 8 effective pixels of padding on each island side.
pad=8/448;row_width=128.0;x=pad;y=pad;row_height=0
for chart in sorted(charts,key=lambda c:(-(c['bounds'][3]-c['bounds'][1]),-(c['bounds'][2]-c['bounds'][0]))):
 b=chart['bounds'];width=b[2]-b[0];height=b[3]-b[1]
 if x+width+pad>row_width:x=pad;y+=row_height+2*pad;row_height=0
 chart['translation']=[x-b[0],y-b[1]];x+=width+2*pad;row_height=max(row_height,height)
extent=2**math.ceil(math.log2(max(row_width,y+row_height+pad)));print('PACK',len(charts),extent,flush=True)
for chart in charts:
 uv=chart['object'].data.uv_layers[0];dx,dy=chart['translation']
 for i in chart['faces']:
  for li in chart['object'].data.polygons[i].loop_indices:
   p=uv.data[li].uv.copy();uv.data[li].uv=((p.x+dx)/extent,(p.y+dy)/extent)
all_tris=[];density=[];large=[];area_total=0;mapping=json.load(open(os.path.dirname(W)+'/source_uv_validation.json'))
for o in objects:
 uv=o.data.uv_layers[0];uv.name='PackedUniqueIslands'
 for f in o.data.polygons:
  p=[o.data.vertices[o.data.loops[li].vertex_index].co.copy() for li in f.loop_indices];v=[uv.data[li].uv.copy() for li in f.loop_indices]
  a=(p[1]-p[0]).cross(p[2]-p[0]).length*.5;ua=abs((v[1].x-v[0].x)*(v[2].y-v[0].y)-(v[1].y-v[0].y)*(v[2].x-v[0].x))*.5
  all_tris.append({'p':[list(t) for t in p],'uv':[list(t) for t in v]})
  if a>1e-12:
   d=math.sqrt(ua*(extent*448)**2/a);density.append(d);area_total+=a
   if a*128**2>=4:large.append(d)
report,actual=audit(all_tris,extent*448)
report.update({'source_objects':len(objects),'planned_connected_charts':len(charts),'packed_domain':[0,1,0,1],'shader_uv_repeat_scale':extent,'effective_pixels_per_uv_unit':extent*448,'padding_each_side_pixels':8,'target_minimum_island_gap_pixels':16,'world_area_m2':area_total,'density_target_px_m':128,'density_all':{'min':min(density),'median':sorted(density)[len(density)//2],'max':max(density)},'density_at_least_four_texels':{'count':len(large),'min':min(large),'median':sorted(large)[len(large)//2],'max':max(large),'outside_2_percent':sum(abs(d-128)>2.56 for d in large)},'started_at_utc':datetime.datetime.fromtimestamp(start,datetime.timezone.utc).isoformat(),'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'shader_reuse':'UV0 is unique packed geometry. Shader multiplies UV0 by uniform extent then Frac reuses the same generated 448px swatch. Only the post-wrap sampling is intentionally shared.','scope':'Every authored source mesh face; actual edge connectivity and global geometric overlap test, not face-plane group counts.'})
json.dump(report,open(W+'/source_packing_validation.json','w'),indent=2)
assert report['positive_area_overlap_pairs']==0,report
assert report['minimum_island_bbox_gap_pixels_within_32px_search']>=15.9,report
with open(W+'/source_objects.csv','w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=object_rows[0].keys());writer.writeheader();writer.writerows(object_rows)
with open(W+'/source_islands.csv','w',newline='') as f:
 writer=csv.writer(f);writer.writerow(['island','object','triangle_count','min_u','min_v','max_u','max_v'])
 for i,c in enumerate(charts):
  b=c['bounds'];dx,dy=c['translation'];writer.writerow([i,c['object'].name,len(c['faces']),(b[0]+dx)/extent,(b[1]+dy)/extent,(b[2]+dx)/extent,(b[3]+dy)/extent])
mapping['shader_uv_repeat_scale']=extent;json.dump(mapping,open(W+'/source_uv_validation.json','w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=W+'/Source/AlderPass_UV.blend')
bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
o=bpy.context.object;o.data.transform(Matrix.Diagonal((1,-1,1,1)));o.data.flip_normals();o.data.update()
bpy.ops.export_scene.fbx(filepath=W+'/Source/AlderPass_UV.fbx',use_selection=True,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',add_leaf_bones=False,bake_anim=False,mesh_smooth_type='FACE')
print('PACKED_SOURCE_COMPLETE',report,flush=True)
