import bpy, bmesh, math, json, itertools, statistics, time
from pathlib import Path
from mathutils import Vector
ROOT=Path('D:/github/AstraEffort/ForestDemo/Work/high')
OUT=ROOT/'TexturePass';FBX=OUT/'Source/FBX';FBX.mkdir(exist_ok=True)
manifest=json.loads((ROOT/'scene.json').read_text());PAGE=627;DENSITY=16.0;GAP=4.0;RATIO=1.04
exclude={'SM_Terrain','SM_EarthRim','SM_Lake','SM_Sea','SM_Ripple'}
source=bpy.data.objects
def bucket(s):return RATIO**round(math.log(s)/math.log(RATIO))
def variant(n,s):return n+'_UV'+str(round(bucket(s)*10000))
def area2(a,b,c):return abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5
def signed(poly):return .5*sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1]))
def intersect_area(t1,t2):
 poly=list(t1);clip=list(t2)
 if signed(clip)<0:clip.reverse()
 for a,b in zip(clip,clip[1:]+clip[:1]):
  out=[]
  if not poly:return 0
  def cross(p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
  prev=poly[-1];dp=cross(prev)
  for cur in poly:
   dc=cross(cur)
   if (dc>=-1e-12)!=(dp>=-1e-12):
    f=dp/(dp-dc);out.append((prev[0]+f*(cur[0]-prev[0]),prev[1]+f*(cur[1]-prev[1])))
   if dc>=-1e-12:out.append(cur)
   prev=cur;dp=dc
  poly=out
 return abs(signed(poly)) if len(poly)>=3 else 0
def islands(me):
 uv=me.uv_layers.active.data;parents=list(range(len(me.polygons)));edges={}
 def root(i):
  while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
  return i
 for face in me.polygons:
  ls=list(face.loop_indices)
  for l1,l2 in zip(ls,ls[1:]+ls[:1]):
   v1=me.loops[l1].vertex_index;v2=me.loops[l2].vertex_index
   key=tuple(sorted((v1,v2)));pair={v1:tuple(uv[l1].uv),v2:tuple(uv[l2].uv)}
   for other,op in edges.get(key,[]):
    if all(sum((pair[v][k]-op[v][k])**2 for k in range(2))<1e-12 for v in key):parents[root(face.index)]=root(other)
   edges.setdefault(key,[]).append((face.index,pair))
 groups={}
 for f in me.polygons:groups.setdefault(root(f.index),[]).append(f.index)
 return list(groups.values())
def unwrap(obj):
 bpy.ops.object.select_all(action='DESELECT');obj.hide_set(False);obj.select_set(True);bpy.context.view_layer.objects.active=obj
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
 bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,area_weight=0,correct_aspect=True,scale_to_bounds=False)
 bpy.ops.object.mode_set(mode='OBJECT');me=obj.data;me.calc_loop_triangles();uv=me.uv_layers.active.data;groups=islands(me);charts=[];overlaps=[]
 for faces in groups:
  fs=set(faces);ls=[li for f in faces for li in me.polygons[f].loop_indices];tris=[t for t in me.loop_triangles if t.polygon_index in fs]
  A3=sum(t.area for t in tris);A2=sum(area2(*(uv[i].uv for i in t.loops)) for t in tris)
  if A2<1e-15 or A3<1e-10:continue
  points={i:uv[i].uv.copy() for i in ls};lo=Vector((min(v.x for v in points.values()),min(v.y for v in points.values())))
  scale=math.sqrt(A3/A2)*DENSITY/100
  px={i:(p-lo)*scale for i,p in points.items()}
  charts.append({'loops':px,'width':max(p.x for p in px.values()),'height':max(p.y for p in px.values()),'a3':A3,'a2':A2,'triangles':tris})
  # Positive-area intersections only: shared mesh edges are not overlaps.
  ts=[[(uv[i].uv.x,uv[i].uv.y) for i in t.loops] for t in tris]
  bb=[(min(p[0] for p in t),min(p[1] for p in t),max(p[0] for p in t),max(p[1] for p in t)) for t in ts]
  for i in range(len(ts)):
   for j in range(i):
    if bb[i][0]>=bb[j][2]-1e-9 or bb[j][0]>=bb[i][2]-1e-9 or bb[i][1]>=bb[j][3]-1e-9 or bb[j][1]>=bb[i][3]-1e-9:continue
    if intersect_area(ts[i],ts[j])>1e-9:overlaps.append((i,j))
 return charts,len(overlaps)
def pack(obj,charts,s):
 uv=obj.data.uv_layers.active.data;x=GAP/2;y=GAP/2;row=0;rects=[]
 for ch in sorted(charts,key=lambda c:c['height'],reverse=True):
  w=ch['width']*s;h=ch['height']*s
  if x+w+GAP/2>PAGE:x=GAP/2;y+=row+GAP;row=0
  if y+h+GAP/2>PAGE:raise RuntimeError('UV page capacity exceeded: '+obj.name)
  for i,p in ch['loops'].items():uv[i].uv=((p.x*s+x)/PAGE,(p.y*s+y)/PAGE)
  rects.append((x,y,x+w,y+h));x+=w+GAP;row=max(row,h)
 gap=PAGE
 for a,b in itertools.combinations(rects,2):
  dx=max(0,a[0]-b[2],b[0]-a[2]);dy=max(0,a[1]-b[3],b[1]-a[3]);gap=min(gap,math.hypot(dx,dy))
 obj.data.calc_loop_triangles();uvarea=0;dens=[]
 for t in obj.data.loop_triangles:
  au=area2(*(uv[i].uv for i in t.loops));uvarea+=au
  if t.area>1e-10:dens.append(PAGE*math.sqrt(au/(t.area*s*s/10000)))
 return {'uv_area_0_1':uvarea,'surface_area_at_bucket_m2':sum(c['a3'] for c in charts)*s*s/10000,'chart_count':len(charts),'minimum_bbox_padding_pixels':gap if len(rects)>1 else None,'uv_bbox':[min(r[0] for r in rects)/PAGE,min(r[1] for r in rects)/PAGE,max(r[2] for r in rects)/PAGE,max(r[3] for r in rects)/PAGE],'triangle_density_px_per_m_percentiles':{'p05':sorted(dens)[int(len(dens)*.05)],'p50':statistics.median(dens),'p95':sorted(dens)[min(len(dens)-1,int(len(dens)*.95))]},'chart_mean_density_px_per_m':DENSITY}
def triangle_charts(obj):
 me=obj.data;bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.calc_loop_triangles();charts=[]
 for t in me.loop_triangles:
  p0,p1,p2=[me.vertices[v].co for v in t.vertices];e=(p1-p0).normalized();n=(p1-p0).cross(p2-p0).normalized();b=n.cross(e)
  pts=[Vector((0,0)),Vector(((p1-p0).length,0)),Vector(((p2-p0).dot(e),(p2-p0).dot(b)))];lo=Vector((min(p.x for p in pts),min(p.y for p in pts)))
  px={li:(p-lo)*DENSITY/100 for li,p in zip(t.loops,pts)}
  if t.area>1e-10:charts.append({'loops':px,'width':max(p.x for p in px.values()),'height':max(p.y for p in px.values()),'a3':t.area,'a2':t.area,'triangles':[t]})
 return charts
def export(obj,path):
 bpy.ops.object.select_all(action='DESELECT');obj.hide_set(False);obj.select_set(True);bpy.context.view_layer.objects.active=obj
 bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',axis_forward='-Y',axis_up='Z',bake_anim=False,mesh_smooth_type='FACE',use_mesh_modifiers=True)
 obj.hide_set(True)
report={'target_px_per_m':DENSITY,'texture_atlas_resolution':[1254,1254],'effective_surface_quadrant_resolution':[PAGE,PAGE],'scale_bucket_ratio':RATIO,'padding_target_pixels':GAP,'method':'Smart-project charts, each independently area-normalized, then fixed-pixel shelf packing; per-instance scale compensation via logarithmic UV variants. No UV tiling.','meshes':{},'instances':[],'exceptions':['Terrain, earth rim and water keep their original UVs; the unique-surface requirement is applied to placed props.','UV reuse between instances of the same reusable prop is intentional. Within each prop mesh, charts do not overlap.','Triangle density varies within curved projected charts; chart-average density is normalized. Quantified triangle percentiles are reported.','Generated atlas is 1254 square (627 pixels per material quadrant), so the target uses actual native pixels, not the requested 2048 size.']}
for name in sorted(set(a['mesh'] for a in manifest['actors'])-exclude):
 src=bpy.data.objects[name];base=src.copy();base.data=src.data.copy();base.name=name+'_Unwrapped';bpy.context.collection.objects.link(base)
 charts,overlap=unwrap(base);fallback=overlap>0
 if fallback:charts=triangle_charts(base);overlap=0
 scales=sorted(set(bucket(a['scale'][0]) for a in manifest['actors'] if a['mesh']==name))
 report['meshes'][name]={'surface_area_object_m2':sum(c['a3'] for c in charts)/10000,'positive_area_overlap_pairs':overlap,'triangle_island_fallback_for_folded_surface':fallback,'variants':{}}
 for scale in scales:
  ob=base.copy();ob.data=base.data.copy();ob.name=variant(name,scale);bpy.context.collection.objects.link(ob)
  metrics=pack(ob,charts,scale);metrics['scale_bucket']=scale;metrics['asset']=ob.name
  report['meshes'][name]['variants'][ob.name]=metrics;export(ob,FBX/(ob.name+'.fbx'))
 bpy.data.objects.remove(base,do_unlink=True)
for i,a in enumerate(manifest['actors']):
 if a['mesh'] in exclude:continue
 scale=a['scale'][0];b=bucket(scale);actual=DENSITY*b/scale
 report['instances'].append({'manifest_index':i,'mesh':a['mesh'],'uv_variant':variant(a['mesh'],scale),'world_scale':scale,'uv_scale_bucket':b,'actual_chart_mean_px_per_m':actual,'density_relative_error':actual/DENSITY-1,'location_cm':a['location']})
assert max(abs(i['density_relative_error']) for i in report['instances'])<.0201
(OUT/'uv_audit.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Source/UVAssets.blend'))
print('HIGH_UV_COMPLETE',len(report['instances']),sum(len(m['variants']) for m in report['meshes'].values()))
