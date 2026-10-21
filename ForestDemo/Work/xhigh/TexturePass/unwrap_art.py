"""UV production on xhigh's private original artwork; Blender background only."""
import bpy, math, json, os, datetime, collections
from mathutils import Vector
ROOT='D:/github/AstraEffort/ForestDemo/Work/xhigh'
OUT=ROOT+'/TexturePass/SourceArt'
os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=ROOT+'/SourceArt/QuietCove_Source.blend')
report={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'target_effective_px_per_m':128,'texture_resolution_px':1254,
 'method':'Unique packed UV0 islands; average island scale; per-mesh sampling factor and uniform ObjectScale compensate actual placed world scale. Generated surface images intentionally repeat outside 0..1 after shader scaling.',
 'padding_requested_uv':.0064,'meshes':{},'placements':[]}
data=json.load(open(ROOT+'/scene_manifest.json'))

def area2(a,b,c):return abs((b-a).cross(c-a))*.5
def cross(a,b):return a.x*b.y-a.y*b.x
def tri_clip_area(poly,clip):
 # Positive-area intersection excludes shared triangle borders.
 sign=1 if cross(clip[1]-clip[0],clip[2]-clip[0])>0 else -1
 for i in range(3):
  a,b=clip[i],clip[(i+1)%3];edge=b-a;new=[]
  if not poly:return 0
  prev=poly[-1];d0=sign*cross(edge,prev-a)
  for p in poly:
   d=sign*cross(edge,p-a)
   if (d>=0)!=(d0>=0):new.append(prev+(p-prev)*(d0/(d0-d)))
   if d>=0:new.append(p)
   prev=p;d0=d
  poly=new
 return abs(sum(cross(poly[i],poly[(i+1)%len(poly)]) for i in range(len(poly))))*.5 if len(poly)>2 else 0

def summarize(obj):
 me=obj.data;uv=me.uv_layers.active.data;me.calc_loop_triangles()
 tris=[];ratios=[];total_area=0;total_uv=0;deg=0
 for t in me.loop_triangles:
  a,b,c=[me.vertices[v].co for v in t.vertices];area=(b-a).cross(c-a).length*.5
  pts=[uv[i].uv.copy() for i in t.loops];ua=abs(cross(pts[1]-pts[0],pts[2]-pts[0]))*.5
  if area<1e-10 or ua<1e-13:deg+=1;continue
  total_area+=area;total_uv+=ua;ratios.append((math.sqrt(ua/area)*1254,area))
  tris.append((min(p.x for p in pts),max(p.x for p in pts),min(p.y for p in pts),max(p.y for p in pts),pts))
 base=math.sqrt(total_uv/total_area)*1254;factor=128/base
 # Sweep in x, test exact 2D triangle polygon intersection area.
 tris.sort(key=lambda t:t[0]);active=[];overlaps=0;overlap_area=0
 for tr in tris:
  active=[q for q in active if q[1]>tr[0]+1e-8]
  for q in active:
   if q[2]>=tr[3]-1e-8 or q[3]<=tr[2]+1e-8:continue
   a=tri_clip_area(list(q[4]),tr[4])
   if a>1e-8:overlaps+=1;overlap_area+=a
  active.append(tr)
 weighted=sorted((d*factor,a) for d,a in ratios)
 def pct(p):
  acc=0
  for d,a in weighted:
   acc+=a
   if acc>=total_area*p:return d
  return weighted[-1][0]
 # Island connectivity, using mesh edge + UV endpoint agreement.
 parent=list(range(len(me.polygons)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 edge_owner={};boundaries=[]
 for p in me.polygons:
  loops=list(p.loop_indices)
  for j,l in enumerate(loops):
   l2=loops[(j+1)%len(loops)];v1=me.loops[l].vertex_index;v2=me.loops[l2].vertex_index
   x1=uv[l].uv.copy();x2=uv[l2].uv.copy()
   key=tuple(sorted((v1,v2)))
   oriented=(x1,x2) if v1<v2 else (x2,x1)
   if key in edge_owner:
    old,pts=edge_owner[key]
    if all((pts[k]-oriented[k]).length<1e-6 for k in (0,1)):parent[root(old)]=root(p.index)
    else:boundaries.extend([(old,*pts),(p.index,*oriented)])
   else:edge_owner[key]=(p.index,oriented)
 # Every seam appears above. Border-only meshes also need open boundary edges.
 counts=collections.Counter(tuple(sorted(e.vertices)) for e in me.edges)
 linked=collections.Counter()
 for p in me.polygons:
  for e in p.edge_keys:linked[tuple(sorted(e))]+=1
 for key,(p,pts) in edge_owner.items():
  if linked[key]==1:boundaries.append((p,*pts))
 islands=set(root(i) for i in range(len(parent)))
 segs=[]
 for p,a,b in boundaries:segs.append((root(p),a,b,min(a.x,b.x),max(a.x,b.x),min(a.y,b.y),max(a.y,b.y)))
 def point_seg(p,a,b):
  d=b-a;t=max(0,min(1,(p-a).dot(d)/d.length_squared)) if d.length_squared>1e-18 else 0
  return (p-(a+t*d)).length
 mind=1.0;segs.sort(key=lambda s:s[3]);active=[]
 for s in segs:
  active=[q for q in active if q[4]+mind>s[3]]
  for q in active:
   if s[0]==q[0] or q[5]>s[6]+mind or q[6]<s[5]-mind:continue
   d=min(point_seg(s[1],q[1],q[2]),point_seg(s[2],q[1],q[2]),point_seg(q[1],s[1],s[2]),point_seg(q[2],s[1],s[2]))
   mind=min(mind,d)
  active.append(s)
 return {'surface_area_m2':total_area,'uv_area':total_uv,'uv_occupancy_percent':total_uv*100,
  'island_count':len(islands),'triangles_measured':len(ratios),'degenerate_triangles':deg,
  'base_px_per_m':base,'mesh_sampling_factor':factor,'effective_density_px_per_m':{'area_rms':128,'min':weighted[0][0],'p05':pct(.05),'median':pct(.5),'p95':pct(.95),'max':weighted[-1][0]},
  'positive_area_overlap_pairs':overlaps,'overlap_area_uv2':overlap_area,
  'min_island_gap_uv':mind if len(islands)>1 else None,'min_island_gap_px':mind*1254 if len(islands)>1 else None,
  'uv_bounds':[min(x.uv.x for x in uv),min(x.uv.y for x in uv),max(x.uv.x for x in uv),max(x.uv.y for x in uv)]}

for name in data['meshes']:
 obj=bpy.data.objects[name];obj.hide_set(False);obj.hide_viewport=False
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
 bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.0064,area_weight=0,correct_aspect=True,scale_to_bounds=False)
 bpy.ops.uv.select_all(action='SELECT');bpy.ops.uv.average_islands_scale(scale_uv=True,shear=False)
 bpy.ops.uv.pack_islands(rotate=True,scale=True,margin_method='FRACTION',margin=.0064)
 bpy.ops.object.mode_set(mode='OBJECT');obj.data.uv_layers.active.name='UniqueSurfaceUV'
 metrics=summarize(obj);report['meshes'][name]=metrics
 bpy.ops.export_scene.fbx(filepath=OUT+'/'+name+'.fbx',use_selection=True,object_types={'MESH'},add_leaf_bones=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,bake_anim=False,use_mesh_modifiers=True,mesh_smooth_type='FACE',colors_type='LINEAR')
 obj.hide_set(True)
 print('UV_COMPLETE',name,json.dumps(metrics),flush=True)
 json.dump(report,open(OUT+'/uv_report.json','w'),indent=2)

for i,inst in enumerate(data['instances']):
 s=inst['scale'];m=report['meshes'][inst['mesh']]
 assert max(s)-min(s)<1e-6, 'Nonuniform world scale needs directional correction'
 report['placements'].append({'actor':'%s_%04d'%(inst['mesh'],i),'mesh':inst['mesh'],'world_scale':s,'world_surface_area_m2':m['surface_area_m2']*s[0]**2,'uv_area':m['uv_area'],'material_mesh_factor':m['mesh_sampling_factor'],'shader_object_scale':s[0],'effective_density_area_rms_px_per_m':m['base_px_per_m']*m['mesh_sampling_factor']*s[0]/s[0]})
report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
report['passed']=all(m['positive_area_overlap_pairs']==0 and m['uv_bounds'][0]>=-1e-5 and m['uv_bounds'][1]>=-1e-5 and m['uv_bounds'][2]<=1.00001 and m['uv_bounds'][3]<=1.00001 for m in report['meshes'].values())
json.dump(report,open(OUT+'/uv_report.json','w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/QuietCove_TexturePass.blend')
print('UV_ALL_COMPLETE',report['passed'],flush=True)
