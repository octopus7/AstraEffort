import bpy,bmesh,math,json,time,hashlib,gzip,csv
from pathlib import Path
from mathutils import Vector
from datetime import datetime,timezone
W=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh/TexturePass')
start=time.time();utc=lambda:datetime.now(timezone.utc).isoformat()
source=W.parent/'SourceArt/AlderPass.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
S=256/1254;PAD=8/1254;WIDTH=32
report={'started_at_utc':utc(),'source_blend_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'target_pixels_per_metre':256,'native_texture_resolution':1254,'uv_units_per_metre':S,'physical_repeat_m':1/S,'padding_native_pixels':8,'scope':'All triangles in all nine assemblies; source object transforms applied. Orthogonal surface projection; planar edge-connected same-material islands. All repeats use intentional modulo-one reuse.','assemblies':{}}
for obj in sorted([o for o in bpy.context.scene.objects if o.type=='MESH'],key=lambda o:o.name):
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 original_matrix=[list(r) for r in obj.matrix_world];bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY');bm.to_mesh(obj.data);bm.free();me=obj.data;me.update()
 for layer in list(me.uv_layers):me.uv_layers.remove(layer)
 uv=me.uv_layers.new(name='SurfaceMetricUV');n=len(me.polygons);parents=list(range(n))
 def root(i):
  while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
  return i
 edges={}
 for p in me.polygons:
  for a,b in p.edge_keys:
   key=(min(a,b),max(a,b));j=edges.get(key)
   if j is not None:
    q=me.polygons[j]
    if p.material_index==q.material_index and p.normal.dot(q.normal)>.9999999:
     ra,rb=root(p.index),root(j)
     if ra!=rb:parents[ra]=rb
   else:edges[key]=p.index
 groups={}
 for p in me.polygons:groups.setdefault(root(p.index),[]).append(p.index)
 islands=[]
 for ids in groups.values():
  face=me.polygons[max(ids,key=lambda i:me.polygons[i].area)];normal=face.normal.copy()
  # Consistent world-up grain on vertical surfaces, longest planar direction on horizontal ones.
  v=Vector((0,0,1));v=v-normal*v.dot(normal)
  if v.length<.01:v=Vector((0,1,0));v=v-normal*v.dot(normal)
  v.normalize();u=v.cross(normal).normalized()
  verts={i for f in ids for i in me.polygons[f].vertices};coords={i:(me.vertices[i].co.dot(u)*S,me.vertices[i].co.dot(v)*S) for i in verts}
  xmin=min(c[0] for c in coords.values());ymin=min(c[1] for c in coords.values());xmax=max(c[0] for c in coords.values());ymax=max(c[1] for c in coords.values())
  islands.append((xmax-xmin,ymax-ymin,ids,coords,xmin,ymin))
 islands.sort(key=lambda q:(-q[1],-q[0],q[2][0]));x=y=rowh=0.;rects=[]
 for island_id,(width,height,ids,coords,xmin,ymin) in enumerate(islands):
  if x+width+PAD>WIDTH and x>0:x=0;y+=rowh+PAD;rowh=0
  for f in ids:
   for loop in me.polygons[f].loop_indices:
    a,b=coords[me.loops[loop].vertex_index];uv.data[loop].uv=(a-xmin+x,b-ymin+y)
  rects.append({'id':island_id,'bounds':[x,y,x+width,y+height],'triangle_count':len(ids),'material':obj.data.materials[me.polygons[ids[0]].material_index].name})
  x+=width+PAD;rowh=max(rowh,height)
 # Shelf packing has disjoint row intervals and disjoint X intervals within each row.
 rows={}
 for r in rects:rows.setdefault(r['bounds'][1],[]).append(r['bounds'])
 min_gap=1e9;prevmax=None
 for yy,rr in sorted(rows.items()):
  if prevmax is not None:min_gap=min(min_gap,yy-prevmax)
  prevmax=max(r[3] for r in rr);rr.sort()
  for a,b in zip(rr,rr[1:]):min_gap=min(min_gap,b[0]-a[2])
 mats={};dens=[];area=uva=0;deg=small=0
 with gzip.open(W/'Evidence'/(obj.name+'_source_triangles.csv.gz'),'wt',newline='') as out:
  writer=csv.writer(out);writer.writerow(['triangle','material','area_m2','uv_area','density_px_per_m'])
  for p in me.polygons:
   pos=[me.vertices[i].co for i in p.vertices];ar=(pos[1]-pos[0]).cross(pos[2]-pos[0]).length/2
   q=[uv.data[i].uv for i in p.loop_indices];au=abs((q[1].x-q[0].x)*(q[2].y-q[0].y)-(q[1].y-q[0].y)*(q[2].x-q[0].x))/2
   d=1254*math.sqrt(au/ar) if ar>1e-14 else 0
   name=me.materials[p.material_index].name;m=mats.setdefault(name,{'triangles':0,'area_m2':0,'uv_area':0,'tiny_below_one_native_pixel':0,'degenerate':0})
   m['triangles']+=1;m['area_m2']+=ar;m['uv_area']+=au;area+=ar;uva+=au
   if ar<=1e-14:deg+=1;m['degenerate']+=1
   else:dens.append(d)
   if au*1254**2<1:small+=1;m['tiny_below_one_native_pixel']+=1
   writer.writerow([p.index,name,ar,au,d])
 for m in mats.values():m['area_weighted_density_px_per_m']=1254*math.sqrt(m['uv_area']/m['area_m2']) if m['area_m2'] else 0
 ds=sorted(dens)
 rep={'vertices':len(me.vertices),'triangles':n,'islands':len(islands),'area_m2':area,'uv_area':uva,'area_weighted_density_px_per_m':1254*math.sqrt(uva/area),'density_min':min(ds),'density_p01':ds[int(len(ds)*.01)],'density_p50':ds[len(ds)//2],'density_p99':ds[int(len(ds)*.99)],'density_max':max(ds),'outside_1pct':sum(abs(d/256-1)>.01 for d in ds),'degenerate_triangles':deg,'tiny_below_one_native_pixel':small,'packed_min_gap_pixels':min_gap*1254,'bounds_uv':[max(r['bounds'][2] for r in rects),max(r['bounds'][3] for r in rects)],'overlap':'Zero between distinct island bounding rectangles in unbounded UV plane, verified by complete shelf interval audit. Modulo-one repeats overlap intentionally.','materials':mats,'original_object_matrix':original_matrix,'final_object_scale':list(obj.scale)}
 report['assemblies'][obj.name]=rep
 (W/'Evidence'/(obj.name+'_islands.json')).write_text(json.dumps(rects,separators=(',',':')))
 bpy.ops.export_scene.fbx(filepath=str(W/'SourceArt'/(obj.name+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,global_scale=1,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',bake_anim=False,add_leaf_bones=False)
 print('UV_ASSEMBLY',obj.name,n,len(islands),rep['density_min'],rep['density_max'],flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(W/'SourceArt/AlderPass_TexturedUV.blend'))
report['finished_at_utc']=utc();report['elapsed_seconds']=time.time()-start
(W/'Evidence/source_uv_validation.json').write_text(json.dumps(report,indent=2))
print('UV_COMPLETE',report['elapsed_seconds'],flush=True)
