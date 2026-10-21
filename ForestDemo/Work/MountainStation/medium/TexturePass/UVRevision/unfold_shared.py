import bpy,bmesh,math,json,os,sys,time,datetime,csv
from mathutils import Vector,Matrix
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/TexturePass/UVRevision';sys.path.insert(0,W)
from uv_audit import audit,bounds,overlap
start=time.time();bpy.ops.wm.open_mainfile(filepath=os.path.dirname(os.path.dirname(W))+'/AlderPass.blend')
objects=sorted([o for o in bpy.context.scene.objects if o.type=='MESH'],key=lambda o:o.name)
trunks=[o for o in objects if o.name.startswith('Pine trunk')];base=trunks[0];base_h=base.dimensions.z/.58;bx,by,bcz=base.location;base_z=bcz-base_h*.29
instances=[{'name':o.name,'location_m':[o.location.x,o.location.y,o.location.z-o.dimensions.z*.5],'scale':o.dimensions.z/.58/base_h} for o in trunks]
tree_objects=[o for o in objects if o.name.startswith(('Pine trunk','Rounded pine tier'))]
prototype=[o for o in tree_objects if abs(o.location.x-bx)<1e-4 and abs(o.location.y-by)<1e-4]
for o in tree_objects:
 if o not in prototype:bpy.data.objects.remove(o,do_unlink=True)
objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];bark=bpy.data.materials.new('bark');bark.diffuse_color=(.36,.23,.14,1)
charts=[];removed=0;rows=[]
for oi,o in enumerate(objects):
 if o.name.startswith('Pine trunk'):o.data.materials.clear();o.data.materials.append(bark)
 o.data.transform(o.matrix_world);o.matrix_world=Matrix.Identity(4)
 if o in prototype:o.data.transform(Matrix.Translation(Vector((-bx,-by,-base_z))))
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bad=[f for f in bm.faces if f.calc_area()<1e-8 or 2*f.calc_area()/max(e.calc_length() for e in f.edges)<1e-4];removed+=len(bad);bmesh.ops.delete(bm,geom=bad,context='FACES_ONLY');bm.to_mesh(o.data);bm.free();o.data.update()
 me=o.data
 while me.uv_layers:me.uv_layers.remove(me.uv_layers[0])
 uv=me.uv_layers.new(name='UniqueDevelopableIslands');faces=[list(f.vertices) for f in me.polygons];pos=[v.co.copy() for v in me.vertices];edges={}
 for i,vs in enumerate(faces):
  for j in range(3):edges.setdefault(tuple(sorted((vs[j],vs[(j+1)%3]))),[]).append(i)
 unassigned=set(range(len(faces)));object_count=0
 while unassigned:
  seed=min(unassigned);vs=faces[seed];p=[pos[v] for v in vs];length=(p[1]-p[0]).length
  if length<1e-12:raise RuntimeError('Degenerate edge')
  d=(p[2]-p[0]).dot((p[1]-p[0])/length);height=math.sqrt(max(0,(p[2]-p[0]).length_squared-d*d))
  vertices={vs[0]:(0.,0.),vs[1]:(length,0.),vs[2]:(d,height)};assigned={seed:[vertices[v] for v in vs]};boxes={seed:bounds(assigned[seed])};unassigned.remove(seed);queue=[seed]
  while queue:
   parent=queue.pop(0);pv=faces[parent]
   for j in range(3):
    a,b=pv[j],pv[(j+1)%3];third=pv[(j+2)%3]
    for candidate in edges[tuple(sorted((a,b)))]:
     if candidate not in unassigned or len(assigned)>=256:continue
     cv=faces[candidate];c=next(v for v in cv if v not in (a,b));A=vertices[a];B=vertices[b];C=vertices[third];dx,dy=B[0]-A[0],B[1]-A[1];el=math.hypot(dx,dy)
     if el<1e-12:continue
     ac=(pos[c]-pos[a]).length;bc=(pos[c]-pos[b]).length;t=(ac*ac-bc*bc+el*el)/(2*el);hh=math.sqrt(max(0,ac*ac-t*t));sign=-1 if dx*(C[1]-A[1])-dy*(C[0]-A[0])>0 else 1
     proposed=(A[0]+t*dx/el-sign*hh*dy/el,A[1]+t*dy/el+sign*hh*dx/el)
     if c in vertices and math.dist(vertices[c],proposed)>1e-6:continue
     temp=dict(vertices);temp[c]=vertices.get(c,proposed);tri=[temp[v] for v in cv];bb=bounds(tri);collision=False
     for k,other in assigned.items():
      ob=boxes[k]
      if min(bb[2],ob[2])-max(bb[0],ob[0])<=1e-8 or min(bb[3],ob[3])-max(bb[1],ob[1])<=1e-8:continue
      if overlap(tri,other,1e-7):collision=True;break
     if collision:continue
     vertices[c]=temp[c];assigned[candidate]=tri;boxes[candidate]=bb;unassigned.remove(candidate);queue.append(candidate)
  # Convert exact intrinsic metric coordinates to 448px texture repeats at 128px/m.
  for i,tri in assigned.items():
   for li,p in zip(me.polygons[i].loop_indices,tri):uv.data[li].uv=(p[0]/3.5,p[1]/3.5)
  charts.append({'object':o,'faces':list(assigned),'bounds':bounds([(p[0]/3.5,p[1]/3.5) for tri in assigned.values() for p in tri])});object_count+=1
 rows.append({'object':o.name,'triangles':len(faces),'islands':object_count,'is_tree_prototype':o in prototype})
 if oi%150==0:print('UNFOLD',oi,len(objects),len(charts),flush=True)
pad=8/448;x=pad;y=pad;rh=0
for c in sorted(charts,key=lambda c:-(c['bounds'][3]-c['bounds'][1])):
 b=c['bounds'];w=b[2]-b[0];h=b[3]-b[1]
 if x+w+pad>128:x=pad;y+=rh+2*pad;rh=0
 c['translation']=(x-b[0],y-b[1]);x+=w+2*pad;rh=max(rh,h)
 for i in c['faces']:
  for li in c['object'].data.polygons[i].loop_indices:
   uv=c['object'].data.uv_layers[0].data[li];uv.uv=(uv.uv.x+c['translation'][0],uv.uv.y+c['translation'][1])
reports={}
for group_name,group_objects in [('station',[o for o in objects if o not in prototype]),('tree',prototype)]:
 tris=[];area=0;large=[];all_density=[]
 for o in group_objects:
  for f in o.data.polygons:
   p=[o.data.vertices[o.data.loops[li].vertex_index].co.copy() for li in f.loop_indices];v=[o.data.uv_layers[0].data[li].uv.copy() for li in f.loop_indices];a=(p[1]-p[0]).cross(p[2]-p[0]).length*.5;ua=abs((v[1].x-v[0].x)*(v[2].y-v[0].y)-(v[1].y-v[0].y)*(v[2].x-v[0].x))*.5
   tris.append({'p':[list(z) for z in p],'uv':[list(z) for z in v]});area+=a
   if a>1e-12:
    d=math.sqrt(ua*448**2/a);all_density.append(d)
    if a*128**2>=4:large.append(d)
 rep,groups=audit(tris,448);rep.update({'area_m2':area,'all_density_min':min(all_density),'all_density_max':max(all_density),'resolved_density_count':len(large),'resolved_density_min':min(large),'resolved_density_max':max(large),'resolved_density_outside_2_percent':sum(abs(d-128)>2.56 for d in large)});reports[group_name]=rep
 assert rep['positive_area_overlap_pairs']==0,rep
 assert rep['minimum_island_bbox_gap_pixels_within_32px_search']>=15.8,rep
json.dump({'started_at_utc':datetime.datetime.fromtimestamp(start,datetime.timezone.utc).isoformat(),'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prototype_height_parameter_m':base_h,'instances':instances,'unique_tree_objects':len(prototype),'original_tree_objects':len(tree_objects),'removed_zero_area_faces':removed,'reports':reports,'padding_each_side_effective_pixels':8,'shader_uv_repeat_scale':1,'uv_domain':'Multiple unfolded UV tiles; unique geometric islands before Frac. Same prototype UV legitimately reused by tree mesh instances.','method':'Greedy intrinsic triangle unfolding across actual shared edges; preserve lengths/areas; cut on inconsistent cycles or overlap. Components are verified from actual final edge/UV connectivity.'},open(W+'/shared_source_validation.json','w'),indent=2)
with open(W+'/shared_source_objects.csv','w',newline='') as f:
 wr=csv.DictWriter(f,fieldnames=rows[0].keys());wr.writeheader();wr.writerows(rows)
bpy.ops.wm.save_as_mainfile(filepath=W+'/Source/SharedScene.blend')
for group_name,group_objects in [('AlderPass_UV',[o for o in objects if o not in prototype]),('PinePrototype',prototype)]:
 bpy.ops.object.select_all(action='DESELECT')
 for o in group_objects:o.select_set(True)
 bpy.context.view_layer.objects.active=group_objects[0];bpy.ops.object.join();o=bpy.context.object;o.data.transform(Matrix.Diagonal((1,-1,1,1)));o.data.flip_normals();o.data.update()
 bpy.ops.export_scene.fbx(filepath=W+'/Source/'+group_name+'.fbx',use_selection=True,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',add_leaf_bones=False,bake_anim=False,mesh_smooth_type='FACE')
print('SHARED_SOURCE_COMPLETE',reports,flush=True)


