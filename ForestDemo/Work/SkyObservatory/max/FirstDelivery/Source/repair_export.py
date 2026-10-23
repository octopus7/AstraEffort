import bpy,bmesh,json,math,time,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from collections import defaultdict
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max');ART=ROOT/'SourceArt';EVID=ROOT/'Evidence'
bpy.ops.wm.open_mainfile(filepath=str(ART/'SkyObservatory_Master.blend'))
ob=bpy.data.objects['SM_CloudLayer'];mesh=ob.data
# Stretch each closed cloud puff about its own centroid, never translating islands or changing XY footprint.
adj=defaultdict(list)
for e in mesh.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
seen=set();components=[]
for vi in range(len(mesh.vertices)):
 if vi in seen:continue
 ids=[];todo=[vi]
 while todo:
  j=todo.pop()
  if j in seen:continue
  seen.add(j);ids.append(j);todo.extend(k for k in adj[j] if k not in seen)
 center=sum(mesh.vertices[j].co.z for j in ids)/len(ids)
 for j in ids:mesh.vertices[j].co.z=center+(mesh.vertices[j].co.z-center)*1.6
 components.append(ids)
mesh.update();uv=mesh.uv_layers.active;sx=sy=sh=0.;dens=[]
for p in mesh.polygons:
 a,b,c=[mesh.vertices[i].co for i in p.vertices];ab=b-a;ac=c-a;n=ab.cross(ac);t=ab.normalized();v=n.normalized().cross(t)
 raw=[(0.,0.),(ab.length/16,0.),(ac.dot(t)/16,ac.dot(v)/16)];minx=min(x for x,y in raw);miny=min(y for x,y in raw);maxx=max(x for x,y in raw);maxy=max(y for x,y in raw);pad=4/1024
 w=maxx-minx+pad*2;h=maxy-miny+pad*2
 if sx+w>16:sx=0.;sy+=sh;sh=0.
 for li,(x,y) in zip(p.loop_indices,raw):uv.data[li].uv=(x-minx+sx+pad,y-miny+sy+pad)
 sx+=w;sh=max(sh,h)
 uvp=[uv.data[li].uv for li in p.loop_indices];ua=abs((uvp[1].x-uvp[0].x)*(uvp[2].y-uvp[0].y)-(uvp[2].x-uvp[0].x)*(uvp[1].y-uvp[0].y))*.5
 dens.append(1024*math.sqrt(ua/(n.length*.5)))
# Save corrected design source before export-axis transformation. Purge unused startup datablocks.
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'SkyObservatory_Master.blend'))
report=json.loads((EVID/'source_validation.json').read_text());bounds=[[min(v.co[k] for o in bpy.data.objects if o.type=='MESH' for v in o.data.vertices) for k in range(3)],[max(v.co[k] for o in bpy.data.objects if o.type=='MESH' for v in o.data.vertices) for k in range(3)]]
report['bounds_m']=bounds;report['cloud_correction']={'z_radius_multiplier':1.6,'closed_puffs':len(components),'density_min':min(dens),'density_max':max(dens)}
for item in report['groups']:
 if item['name']=='SM_CloudLayer':
  item['bounds_m']=[[min(v.co[k] for v in mesh.vertices),max(v.co[k] for v in mesh.vertices)] for k in range(3)];item['density_min']=min(dens);item['density_max']=max(dens);item['density_average']=sum(dens)/len(dens)
(EVID/'source_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
proof=[]
for ob in bpy.data.objects:
 if ob.type!='MESH':continue
 mesh=ob.data;original=[[min(v.co[k] for v in mesh.vertices),max(v.co[k] for v in mesh.vertices)] for k in range(3)]
 mesh.transform(Matrix.Diagonal((1.,-1.,1.,1.)))
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update()
 # Validate face orientation by every closed connected component in the exported mesh.
 edges=defaultdict(list)
 for f in mesh.polygons:
  ids=list(f.vertices)
  for a,b in zip(ids,ids[1:]+ids[:1]):edges[tuple(sorted((a,b)))].append((f.index,a,b))
 assert all(len(e)==2 and (e[0][1],e[0][2])==(e[1][2],e[1][1]) for e in edges.values())
 adjacent=defaultdict(list)
 for e in edges.values():adjacent[e[0][0]].append(e[1][0]);adjacent[e[1][0]].append(e[0][0])
 seen=set();volumes=[]
 for pi in range(len(mesh.polygons)):
  if pi in seen:continue
  todo=[pi];vol=0.
  while todo:
   fi=todo.pop()
   if fi in seen:continue
   seen.add(fi);a,b,c=[mesh.vertices[v].co for v in mesh.polygons[fi].vertices];vol+=a.dot(b.cross(c))/6
   todo.extend(i for i in adjacent[fi] if i not in seen)
  volumes.append(vol)
 assert min(volumes)>-1e-4,(ob.name,min(volumes))
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 path=ART/'Meshes'/(ob.name+'.fbx')
 bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,global_scale=1.0,mesh_smooth_type='FACE',path_mode='AUTO')
 proof.append({'mesh':ob.name,'design_bounds_m':original,'export_transform':'baked Y reflection plus face-winding reversal; UE importer Y reflection returns design axes','negative_actor_scale_required':False,'inconsistent_or_open_edges':0,'closed_components':len(volumes),'min_component_volume_m3':min(volumes),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(EVID/'export_axis_validation.json').write_text(json.dumps({'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'meshes':proof},indent=2),encoding='utf-8')
print('AXIS_EXPORT_AND_CLOUD_CORRECTION_PASS',bounds,flush=True)
