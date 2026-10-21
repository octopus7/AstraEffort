import bpy,math,os,json,collections,time
from mathutils import Vector
ROOT='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high/TexturePass'
started=time.time();os.makedirs(ROOT+'/FBX',exist_ok=True)
config=json.load(open(ROOT+'/imagegen_manifest.json'));RES=config['common_square_resolution'];DENSITY=128.;PAD=16/RES
bpy.ops.wm.open_mainfile(filepath='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high/Source/Solmaru.blend')
report={'target_px_per_m':DENSITY,'texture_resolution':RES,'units':'Blender meter; applied scene assembly transforms; UE placement abs scale 1 expected and rechecked independently','UV0':'nonoverlapping charts outside 0-1; repeating texture addressing deliberately reuses image samples','UV1':'normalized nonoverlapping inspection layout; not used for rendering or baked lighting','padding_per_chart_edge_pixels':16,'minimum_packed_rectangle_gap_pixels':32,'normal_patch_angle_degrees':25,'meshes':[]}
def percentile(xs,p):return sorted(xs)[min(len(xs)-1,int((len(xs)-1)*p))] if xs else None
for ob in [o for o in bpy.context.scene.objects if o.type=='MESH']:
 print('UV_BEGIN',ob.name,flush=True);me=ob.data
 if ob.name=='SM_Furniture':
  for idx,mat in enumerate(me.materials):
   if mat.name=='Ochre':
    leather=mat.copy();leather.name='Leather';me.materials[idx]=leather
 # Connected charts, restricted by seed normal (not merely transitive edge angles).
 normals=[p.normal.copy() for p in me.polygons];areas=[p.area for p in me.polygons]
 edgefaces=collections.defaultdict(list)
 for p in me.polygons:
  for e in p.edge_keys:edgefaces[tuple(sorted(e))].append(p.index)
 neighbors=[[] for p in me.polygons]
 for ids in edgefaces.values():
  if len(ids)==2:
   a,b=ids;neighbors[a].append(b);neighbors[b].append(a)
 unseen=set(range(len(me.polygons)));charts=[];cos=math.cos(math.radians(25))
 while unseen:
  seed=unseen.pop();n=normals[seed];mat=me.polygons[seed].material_index;stack=[seed];ids=[]
  while stack:
   i=stack.pop();ids.append(i)
   for j in neighbors[i]:
    if j in unseen and me.polygons[j].material_index==mat and normals[j].dot(n)>=cos:unseen.remove(j);stack.append(j)
  coords=[me.vertices[i].co for i in me.polygons[seed].vertices]
  edges=[coords[(i+1)%len(coords)]-coords[i] for i in range(len(coords))]
  vv=max(edges,key=lambda e:e.length_squared).normalized();uu=vv.cross(n).normalized()
  if uu.length<.1:uu=Vector((1,0,0));vv=Vector((0,1,0))
  uv={li:(me.vertices[me.loops[li].vertex_index].co.dot(uu),me.vertices[me.loops[li].vertex_index].co.dot(vv)) for i in ids for li in me.polygons[i].loop_indices}
  projected=0.;world=sum(areas[i] for i in ids)
  for i in ids:
   pts=[uv[li] for li in me.polygons[i].loop_indices];projected+=abs(sum(pts[k][0]*pts[(k+1)%len(pts)][1]-pts[(k+1)%len(pts)][0]*pts[k][1] for k in range(len(pts)))/2)
  scale=math.sqrt(world/projected)*DENSITY/RES if projected>1e-16 else DENSITY/RES
  lo=[min(p[a] for p in uv.values()) for a in [0,1]];hi=[max(p[a] for p in uv.values()) for a in [0,1]]
  charts.append({'ids':ids,'uv':{li:((p[0]-lo[0])*scale,(p[1]-lo[1])*scale) for li,p in uv.items()},'w':(hi[0]-lo[0])*scale,'h':(hi[1]-lo[1])*scale,'area':world,'scale':scale,'curved':any(normals[i].dot(n)<.99999 for i in ids)})
 while len(me.uv_layers):me.uv_layers.remove(me.uv_layers[0])
 u0=me.uv_layers.new(name='Surface128pxm');u1=me.uv_layers.new(name='InspectionPacked')
 width=max(16,max(c['w']+2*PAD for c in charts));x=y=rowh=0.;rects=[]
 for c in sorted(charts,key=lambda c:c['h'],reverse=True):
  w,h=c['w']+2*PAD,c['h']+2*PAD
  if x+w>width:x=0;y+=rowh;rowh=0
  for li,p in c['uv'].items():u0.data[li].uv=(p[0]+x+PAD,p[1]+y+PAD)
  rects.append([x+PAD,y+PAD,x+PAD+c['w'],y+PAD+c['h']]);x+=w;rowh=max(rowh,h)
 span=max(width,y+rowh)
 for li in range(len(me.loops)):u1.data[li].uv=u0.data[li].uv/span
 me.uv_layers.active_index=0;me.calc_loop_triangles();stats=[];tiny=degenerate=0;total=uva=0.;material_stats={}
 for t in me.loop_triangles:
  vs=[me.vertices[i].co for i in t.vertices];a=(vs[1]-vs[0]).cross(vs[2]-vs[0]).length*.5
  uv=[u0.data[i].uv for i in t.loops];b=abs((uv[1]-uv[0]).cross(uv[2]-uv[0]))*.5
  if a<1e-12 or b<1e-16:degenerate+=1;continue
  d=RES*math.sqrt(b/a);stats.append(d);total+=a;uva+=b;tiny+=b*RES*RES<1
  name=me.materials[t.material_index].name;rec=material_stats.setdefault(name,{'area_m2':0,'uv_area':0,'triangles':0});rec['area_m2']+=a;rec['uv_area']+=b;rec['triangles']+=1
 for r in material_stats.values():r['area_weighted_density_px_m']=RES*math.sqrt(r['uv_area']/r['area_m2'])
 entry={'name':ob.name,'vertices':len(me.vertices),'polygons':len(me.polygons),'triangles':len(me.loop_triangles),'islands':len(charts),'curved_islands':sum(c['curved'] for c in charts),'area_m2':total,'uv_area':uva,'area_weighted_density_px_m':RES*math.sqrt(uva/total),'density_min_p05_p50_p95_max':[min(stats),percentile(stats,.05),percentile(stats,.5),percentile(stats,.95),max(stats)],'subpixel_triangles':tiny,'degenerate_triangles_excluded':degenerate,'uv_bounds':[width,y+rowh],'island_rectangle_nonoverlap':'all charts analytically disjoint by shelf construction; no 0-1 unique-bake claim','material_statistics':material_stats,'inspection_uv_scale':1/span}
 report['meshes'].append(entry)
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.export_scene.fbx(filepath=ROOT+'/FBX/'+ob.name+'.fbx',use_selection=True,object_types={'MESH'},apply_unit_scale=True,axis_forward='-Y',axis_up='Z',mesh_smooth_type='FACE',add_leaf_bones=False)
 print('UV_COMPLETE',ob.name,len(charts),entry['area_weighted_density_px_m'],flush=True)
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/Solmaru_Textured.blend');report['elapsed_seconds']=time.time()-started
json.dump(report,open(ROOT+'/source_uv_validation.json','w'),indent=2)
