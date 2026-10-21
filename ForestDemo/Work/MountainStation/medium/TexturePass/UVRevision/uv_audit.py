import math
def components(tris):
 parent=list(range(len(tris)));edges={}
 def find(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 for i,t in enumerate(tris):
  vs=[tuple(t['p'][j])+tuple(t['uv'][j]) for j in range(3)]
  for j in range(3):
   key=tuple(sorted((vs[j],vs[(j+1)%3])))
   if key in edges:
    x,y=find(i),find(edges[key]);parent[y]=x
   else:edges[key]=i
 groups={}
 for i in range(len(tris)):groups.setdefault(find(i),[]).append(i)
 return list(groups.values())
def bounds(points):return [min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
def overlap(a,b,eps=1e-5):
 for tri in [a,b]:
  for j in range(3):
   p,q=tri[j],tri[(j+1)%3];dx=q[0]-p[0];dy=q[1]-p[1];l=math.hypot(dx,dy)
   if l<1e-12:continue
   aa=[(-dy*v[0]+dx*v[1])/l for v in a];bb=[(-dy*v[0]+dx*v[1])/l for v in b]
   if min(max(aa),max(bb))-max(min(aa),min(bb))<=eps:return False
 return True
def audit(tris,units_to_pixels):
 groups=components(tris);tri_group={i:g for g,ids in enumerate(groups) for i in ids};items=[];degenerate=0
 for i,t in enumerate(tris):
  uv=[(p[0]*units_to_pixels,p[1]*units_to_pixels) for p in t['uv']]
  area=abs((uv[1][0]-uv[0][0])*(uv[2][1]-uv[0][1])-(uv[1][1]-uv[0][1])*(uv[2][0]-uv[0][0]))*.5
  if area<1e-8:degenerate+=1;continue
  items.append((bounds(uv),i,uv))
 active=[];hits=[];hitcount=0
 for box,i,uv in sorted(items,key=lambda x:x[0][0]):
  active=[x for x in active if x[0][2]>box[0]+1e-5]
  for other,j,uv2 in active:
   if min(box[3],other[3])-max(box[1],other[1])<=1e-5:continue
   if overlap(uv,uv2):
    hitcount+=1
    if len(hits)<100:hits.append([i,j,tri_group[i],tri_group[j]])
  active.append((box,i,uv))
 boxes=[bounds([p for i in ids for p in tris[i]['uv']]) for ids in groups]
 # Conservative inter-island rectangle distance; disjoint rectangles imply disjoint triangles.
 active=[];minimum=float('inf');bbox_overlap=0
 for k,box in sorted(enumerate(boxes),key=lambda x:x[1][0]):
  active=[x for x in active if (box[0]-x[1][2])*units_to_pixels<32]
  for j,other in active:
   dx=max(0,box[0]-other[2],other[0]-box[2])*units_to_pixels;dy=max(0,box[1]-other[3],other[1]-box[3])*units_to_pixels
   distance=math.hypot(dx,dy);minimum=min(minimum,distance)
   if dx==0 and dy==0:bbox_overlap+=1
  active.append((k,box))
 return {'triangles':len(tris),'actual_edge_connected_uv_islands':len(groups),'degenerate_uv_triangles':degenerate,'positive_area_overlap_pairs':hitcount,'overlap_examples':hits,'island_bbox_overlap_pairs':bbox_overlap,'minimum_island_bbox_gap_pixels_within_32px_search':minimum if minimum<float('inf') else None,'algorithm':'Components share an exact geometric edge and matching UV endpoints, independent of normal splits. Global triangle AABB sweep + strict SAT tests interior overlap; shared boundaries allowed. Conservative island AABB gap search covers every pair within 32 effective pixels.','epsilon_pixels':1e-5},groups
