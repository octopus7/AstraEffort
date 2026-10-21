import bpy,json,collections,math,time
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high/TexturePass';bpy.ops.wm.open_mainfile(filepath=W+'/Solmaru_Textured.blend');R=json.load(open(W+'/imagegen_manifest.json'))['common_square_resolution'];records=[];all_rects={}
def overlaps(rects,grow=0):
 grid=collections.defaultdict(list);hits=[];cell=.2
 for i,(x0,y0,x1,y1) in enumerate(rects):
  a=(x0-grow,y0-grow,x1+grow,y1+grow);keys=[(x,y) for x in range(math.floor(a[0]/cell),math.floor(a[2]/cell)+1) for y in range(math.floor(a[1]/cell),math.floor(a[3]/cell)+1)];candidates=set(j for k in keys for j in grid[k])
  for j in candidates:
   b=rects[j]
   if min(a[2],b[2]+grow)-max(a[0],b[0]-grow)>1e-7 and min(a[3],b[3]+grow)-max(a[1],b[1]-grow)>1e-7:hits.append([j,i])
  for k in keys:grid[k].append(i)
 return hits
for ob in [o for o in bpy.context.scene.objects if o.type=='MESH']:
 me=ob.data;uv=me.uv_layers[0].data;edge=collections.defaultdict(list)
 for p in me.polygons:
  lis=list(p.loop_indices)
  for k,li in enumerate(lis):
   lj=lis[(k+1)%len(lis)];vi,vj=me.loops[li].vertex_index,me.loops[lj].vertex_index
   if vi>vj:vi,vj,li,lj=vj,vi,lj,li
   edge[(vi,vj)].append((p.index,tuple(uv[li].uv),tuple(uv[lj].uv)))
 adj=[[] for p in me.polygons]
 for es in edge.values():
  if len(es)==2:
   a,b=es
   if a[1:]==b[1:]:adj[a[0]].append(b[0]);adj[b[0]].append(a[0])
 todo=set(range(len(me.polygons)));rects=[]
 while todo:
  i=todo.pop();stack=[i];ids=[]
  while stack:
   n=stack.pop();ids.append(n)
   for j in adj[n]:
    if j in todo:todo.remove(j);stack.append(j)
  pts=[uv[li].uv for j in ids for li in me.polygons[j].loop_indices];rects.append([min(p.x for p in pts),min(p.y for p in pts),max(p.x for p in pts),max(p.y for p in pts)])
 o=overlaps(rects);g=overlaps(rects,15.98/R)
 all_rects[ob.name]=rects
 records.append({'mesh':ob.name,'reconstructed_islands':len(rects),'inter_island_aabb_overlap_pairs':len(o),'padding_less_than_31_96_pixel_pairs':len(g),'first_overlap_pairs':o[:8],'first_padding_pairs':g[:8],'passed':not o and not g})
 print('ISLAND_AUDIT',records[-1],flush=True)
json.dump({'resolution':R,'all_source_islands_checked':True,'method':'Reconstructed actual UV continuity from saved .blend, independent spatial grid AABB overlap and expanded-AABB padding tests. 31.96 pixels certified minimum bounding-box separation; 32 target. Does not assert exhaustive triangle nonoverlap within each curved chart.','meshes':records,'passed':all(x['passed'] for x in records)},open(W+'/source_island_validation.json','w'),indent=2)
json.dump(all_rects,open(W+'/source_chart_rectangles.json','w'))
