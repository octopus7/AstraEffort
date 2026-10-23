import bpy,bmesh,math,json,time,hashlib
import numpy as np
from pathlib import Path
from collections import defaultdict,Counter
from mathutils import Vector,Matrix
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max');PASS=ROOT/'TextureImprovement';ART=PASS/'SourceArt';OUT=ART/'Meshes';OUT.mkdir(exist_ok=True)
start=time.time();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'SourceArt/SkyObservatory_Master.blend'))
WORLD={'Limestone','StoneDark','RockBlue','RockPale','Grass','Moss','Path','Leaf','LeafLight','Lavender','Cloud','Window','Star'}
UV_M=16.;PAD=8/1024
def geom_hash(mesh):
 a=np.asarray([tuple(v.co) for v in mesh.vertices],dtype='<f4');f=np.asarray([tuple(p.vertices) for p in mesh.polygons],dtype='<i4')
 return hashlib.sha256(a.tobytes()+f.tobytes()).hexdigest()
def edge_data(mesh):
 d=defaultdict(list)
 for f in mesh.polygons:
  ids=list(f.vertices)
  for a,b in zip(ids,ids[1:]+ids[:1]):d[tuple(sorted((a,b)))].append((f.index,a,b))
 return d
def components(mesh,edges):
 adj=defaultdict(list)
 for e in edges.values():
  assert len(e)==2 and (e[0][1],e[0][2])==(e[1][2],e[1][1])
  adj[e[0][0]].append(e[1][0]);adj[e[1][0]].append(e[0][0])
 seen=set();cs=[]
 for i in range(len(mesh.polygons)):
  if i in seen:continue
  todo=[i];faces=[]
  while todo:
   f=todo.pop()
   if f in seen:continue
   seen.add(f);faces.append(f);todo.extend(n for n in adj[f] if n not in seen)
  cs.append(sorted(faces))
 return cs,adj
def pca_axes(points):
 center=points.mean(axis=0);_,vectors=np.linalg.eigh(np.cov((points-center).T));basis=vectors[:,::-1].T
 for i in range(3):
  k=int(np.argmax(abs(basis[i])))
  if basis[i,k]<0:basis[i]*=-1
 if np.linalg.det(basis)<0:basis[2]*=-1
 return center,basis
def stats_density(mesh,uv):
 area_d=[];smins=[];smaxs=[];weights=[]
 for p in mesh.polygons:
  a,b,c=[Vector(mesh.vertices[i].co) for i in p.vertices];ab=b-a;ac=c-a;n=ab.cross(ac);area=n.length*.5;t=ab.normalized();q=n.normalized().cross(t)
  coords=np.asarray([uv.data[i].uv[:] for i in p.loop_indices]);du=np.column_stack([coords[1]-coords[0],coords[2]-coords[0]])
  xyz=np.array([[ab.length,ac.dot(t)],[0,ac.dot(q)]],dtype=float);J=du@np.linalg.inv(xyz)*1024
  sv=np.linalg.svd(J,compute_uv=False);assert sv[-1]>1e-7,(mesh.name,p.index,sv)
  area_d.append(math.sqrt(abs(np.linalg.det(J))));smins.append(float(sv[-1]));smaxs.append(float(sv[0]));weights.append(area)
 return {'nominal_texture_px':1024,'nominal_uv_target_px_per_m':64,'area_density_min':min(area_d),'area_density_max':max(area_d),'area_weighted_mean':float(np.average(area_d,weights=weights)),'directional_density_min':min(smins),'directional_density_max':max(smaxs),'max_anisotropy':max(a/b for a,b in zip(smaxs,smins))}
reports=[];layouts={};before={}
for ob in sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:o.name):
 mesh=ob.data;before[ob.name]=geom_hash(mesh);edges=edge_data(mesh);cs,adj=components(mesh,edges)
 olduv=mesh.uv_layers.active;old_seams=0
 for e in edges.values():
  f1,f2=mesh.polygons[e[0][0]],mesh.polygons[e[1][0]];uv1={v:olduv.data[l].uv for v,l in zip(f1.vertices,f1.loop_indices)};uv2={v:olduv.data[l].uv for v,l in zip(f2.vertices,f2.loop_indices)}
  if any((uv1[v]-uv2[v]).length>1e-5 for v in [e[0][1],e[0][2]]):old_seams+=1
 uv=mesh.uv_layers.active;uv.name='ConnectedSurfaceUV';facechart={};charts=[];component_summary=[]
 for ci,faces in enumerate(cs):
  vids=sorted(set(v for fi in faces for v in mesh.polygons[fi].vertices));pts=np.asarray([tuple(mesh.vertices[v].co) for v in vids]);mat=mesh.materials[mesh.polygons[faces[0]].material_index].name
  center,basis=pca_axes(pts);is_dome=(ob.name=='SM_Observatory' and mat=='RoofTeal' and len(vids)==1404)
  if mat in WORLD or is_dome:basis=np.eye(3)
  keys={};coord_funcs={}
  for fi in faces:
   p=mesh.polygons[fi];normal=np.asarray(tuple(p.normal));mid=np.mean([mesh.vertices[i].co[:] for i in p.vertices],axis=0)
   if is_dome:
    dc=np.array([-5.,8.,float(pts[:,2].min())]);local=np.asarray([mesh.vertices[i].co[:] for i in p.vertices])-dc;radii=np.linalg.norm(local,axis=1)
    if np.max(abs(radii-9.65))<.001:kind='dome_outer';key=(kind,);radius=9.65
    elif np.max(abs(radii-9.43))<.001:kind='dome_inner';key=(kind,);radius=9.43
    elif np.max(abs(local[:,2]))<.001:kind='dome_base_annulus';key=(kind,);radius=0
    elif np.min(local[:,2]/radii)>.999:kind='dome_crown_thickness';key=(kind,);radius=0
    else:
     theta=math.atan2(float(mid[1]-8),float(mid[0]+5));slit=-24 if abs(theta-math.radians(-24))<.1 else -66
     kind='dome_slit_thickness';key=(kind,slit);radius=0
    if kind in ('dome_outer','dome_inner'):
     # Lambert azimuthal equal-area mapping: coherent to the crown, no longitude singularity.
     def project(v,r=radius,dc=dc.copy()):
      d=np.asarray(tuple(v))-dc;s=max(0.,min(1.,float(d[2]/r)));factor=math.sqrt(2/(1+s));return (float(d[0]*factor/UV_M),float(d[1]*factor/UV_M))
    else:
     # Slit lips: tangent/radial plane; crown/base annulus: XY. Distinct cap charts avoid collapse.
     if kind=='dome_base_annulus':
      project=lambda v:(float(v.x/UV_M),float(v.y/UV_M))
     elif kind=='dome_crown_thickness':
      def project(v,dc=dc.copy()):
       d=np.asarray(tuple(v))-dc;r=float(np.linalg.norm(d));theta=math.atan2(float(d[1]),float(d[0]));theta=theta if theta>=math.radians(-24)-.0001 else theta+math.tau
       return (theta*9.54*math.sin(.018)/UV_M,r/UV_M)
     else:
      theta=math.radians(slit);rad=np.array([math.cos(theta),math.sin(theta),0.]);
      project=lambda v,rad=rad:(float(np.dot(np.asarray(tuple(v))-np.array([-5.,8.,0.]),rad)/UV_M),float(v.z/UV_M))
   else:
    n=basis@normal;axis=int(np.argmax(abs(n)));sign=1 if n[axis]>=0 else -1;key=('axis_projection',axis,sign)
    if mat in ('Timber','WoodLight'):
     # Image V is grain direction. PCA axis zero is each individual plank/beam's long axis.
     if axis==0:u_axis=basis[1];v_axis=basis[2];kind='timber_end_cap'
     else:u_axis=basis[2 if axis==1 else 1];v_axis=basis[0];kind='timber_longitudinal_side'
    else:
     other=[k for k in range(3) if k!=axis];u_axis=basis[other[0]];v_axis=basis[other[1]];kind='world_shader_uv_fallback' if mat in WORLD else 'connected_component_projection'
    project=lambda v,u_axis=u_axis.copy(),v_axis=v_axis.copy(),center=center.copy():(float(np.dot(np.asarray(tuple(v))-center,u_axis)/UV_M),float(np.dot(np.asarray(tuple(v))-center,v_axis)/UV_M))
   keys[fi]=key;coord_funcs[fi]=project
  # Each connected projection region is a chart. No independent triangle rotation or rephasing.
  remaining=set(faces);component_charts=[]
  while remaining:
   seed=min(remaining);key=keys[seed];todo=[seed];region=[]
   while todo:
    fi=todo.pop()
    if fi not in remaining or keys[fi]!=key:continue
    remaining.remove(fi);region.append(fi);todo.extend(adj[fi])
   chart_id=len(charts);kind=key[0];coords={}
   # Fix one projection function for the entire region; cap normals cannot vary per face.
   project=coord_funcs[seed]
   for fi in region:
    facechart[fi]=chart_id
    for vi in mesh.polygons[fi].vertices:coords[vi]=project(mesh.vertices[vi].co)
   xs=[c[0] for c in coords.values()];ys=[c[1] for c in coords.values()]
   chart={'id':chart_id,'component':ci,'material':mat,'projection':kind,'faces':sorted(region),'coords':coords,'bbox':[min(xs),min(ys),max(xs),max(ys)]}
   charts.append(chart);component_charts.append(chart_id)
  component_summary.append({'component':ci,'material':mat,'vertices':len(vids),'faces':len(faces),'charts':component_charts,'sampling_path':'smooth_world_triplanar' if mat in WORLD else ('Lambert_equal_area_dome' if is_dome else ('component_grain_axis' if mat in ('Timber','WoodLight') else 'connected_uv')),'principal_axis':basis[0].tolist() if mat in ('Timber','WoodLight') else None})
 sx=sy=sh=0.
 for chart in charts:
  mnx,mny,mxx,mxy=chart['bbox'];w=mxx-mnx+2*PAD;h=mxy-mny+2*PAD
  if sx+w>16:sx=0.;sy+=sh;sh=0.
  offset=(sx+PAD-mnx,sy+PAD-mny);chart['packed_bounds']=[sx+PAD,sy+PAD,sx+PAD+mxx-mnx,sy+PAD+mxy-mny]
  for fi in chart['faces']:
   p=mesh.polygons[fi]
   for vi,li in zip(p.vertices,p.loop_indices):raw=chart['coords'][vi];uv.data[li].uv=(raw[0]+offset[0],raw[1]+offset[1])
  sx+=w;sh=max(sh,h)
 continuous=declared=unexpected=0;maxerr=0.
 for e in edges.values():
  i,j=e[0][0],e[1][0];f1,f2=mesh.polygons[i],mesh.polygons[j];uv1={v:uv.data[l].uv for v,l in zip(f1.vertices,f1.loop_indices)};uv2={v:uv.data[l].uv for v,l in zip(f2.vertices,f2.loop_indices)}
  err=max((uv1[v]-uv2[v]).length for v in [e[0][1],e[0][2]])
  if facechart[i]==facechart[j]:continuous+=1;maxerr=max(maxerr,err);unexpected+=err>1e-5
  else:declared+=1
 assert unexpected==0 and geom_hash(mesh)==before[ob.name]
 ds=stats_density(mesh,uv)
 # Compute strict positive component volumes from original-design coordinates.
 volumes=[]
 for fs in cs:
  origin=mesh.vertices[mesh.polygons[fs[0]].vertices[0]].co.copy();vol=0.
  for fi in fs:
   a,b,c=[mesh.vertices[v].co-origin for v in mesh.polygons[fi].vertices];vol+=a.dot(b.cross(c))/6
  volumes.append(vol)
 assert min(volumes)>0
 item={'mesh':ob.name,'triangles':len(mesh.polygons),'vertices':len(mesh.vertices),'components':len(cs),'charts':len(charts),'baseline_discontinuous_shared_edges':old_seams,'continuous_shared_edges':continuous,'declared_chart_boundary_edges':declared,'unexpected_shared_edge_discontinuities':unexpected,'max_within_chart_edge_error_uv':maxerr,'island_padding_px_nominal':8,'geometry_hash_before':before[ob.name],'geometry_hash_after':geom_hash(mesh),'min_positive_component_volume_m3':min(volumes),'uv_density_nominal':ds,'components_detail':component_summary}
 reports.append(item)
 layouts[ob.name]={'face_chart_ids':[facechart[i] for i in range(len(mesh.polygons))],'charts':[{k:v for k,v in c.items() if k!='coords'} for c in charts]}
 print('UV_CONTINUITY_PASS',ob.name,'charts',len(charts),'continuous',continuous,'boundaries',declared,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'SkyObservatory_TextureImprovement.blend'))
# Export only a reflected working copy. The saved source remains in original design coordinates.
for ob in sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:o.name):
 mesh=ob.data;mesh.transform(Matrix.Diagonal((1.,-1.,1.,1.)));bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update()
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.export_scene.fbx(filepath=str(OUT/(ob.name+'.fbx')),use_selection=True,object_types={'MESH'},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,global_scale=1.,mesh_smooth_type='FACE',path_mode='AUTO')
report={'started_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(start)),'finished_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'execution_seconds':time.time()-start,'objects':reports,'world_projected_materials':sorted(WORLD),'chart_policy':'Connected projection regions, deterministic component PCA for timber; dome outer/inner Lambert equal-area hemispheres and separate thickness caps. 8px nominal padding between packed charts; tiled repeats across disconnected physical parts are intentional. No face-random orientation or phase. UV density is distinct from actual world-shader sample density.','design_to_export_transform':'Y reflection + winding reversal; actors remain +1 scale'}
(PASS/'Evidence/uv_rebuild.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(PASS/'Evidence/uv_chart_layout.json').write_text(json.dumps(layouts),encoding='utf-8')
print('UV_BUILD_COMPLETE',sum(r['triangles'] for r in reports),sum(r['components'] for r in reports),report['execution_seconds'],flush=True)
