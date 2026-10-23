"""UV-only pass on immutable first-delivery geometry. No generated-image edits."""
import bpy,numpy as np,math,json,hashlib,statistics,time,struct
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime,timezone
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max/TextureImprovement');B=R.parent
start=time.time();bpy.ops.wm.open_mainfile(filepath=str(B/'Source/SnowyOnsen_original.blend'))
def digest(me):
 h=hashlib.sha256();h.update(np.array([tuple(v.co) for v in me.vertices],dtype='<f4').tobytes())
 for p in me.polygons:h.update(struct.pack('<I',len(p.vertices)));h.update(np.array(p.vertices,dtype='<i4').tobytes())
 h.update(np.array([tuple(p.normal) for p in me.polygons],dtype='<f4').tobytes());return h.hexdigest()
def pngsize(p):
 d=p.read_bytes();return [int.from_bytes(d[16:20],'big'),int.from_bytes(d[20:24],'big')]
image_records=[]
for key in ['Timber','Stone','Snow']:
 p=R/'ImageGen'/('T_IMG_'+key+'.png');im=bpy.data.images.load(str(p),check_existing=False);w,h=im.size;a=np.empty(w*h*4,dtype=np.float32);im.pixels.foreach_get(a);a=a.reshape(h,w,4)[:,:,:3]
 image_records.append({'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'resolution':[w,h],'pixels_edited':False,'original_edge_delta_rgb_mean':{'left_right':float(np.abs(a[:,0]-a[:,-1]).mean()),'top_bottom':float(np.abs(a[0]-a[-1]).mean())},'interior_adjacent_pixel_delta_rgb_mean':float((np.abs(a[:,1:]-a[:,:-1]).mean()+np.abs(a[1:]-a[:-1]).mean())/2),'min_rgb':a.min(axis=(0,1)).tolist(),'mean_rgb':a.mean(axis=(0,1)).tolist(),'max_rgb':a.max(axis=(0,1)).tolist(),'wrapping_policy':'UE mirror addressing on both axes; original pixels unchanged. Mirror repeats are position-continuous at every tile boundary, with derivative reversal. Actual render inspection required.'})
(R/'Validation'/'image_source_analysis.json').write_text(json.dumps(image_records,indent=2),encoding='utf8')
TILE=2.5;RES=1254
report={'started_at_utc':datetime.fromtimestamp(start,timezone.utc).isoformat(),'geometry_policy':'Exact vertex coordinates, polygon indices and polygon normals preserved; UV only. Existing Blender Y bake remains unchanged.','wood_mapping':'Each connected wood component: PCA longest axis is V/grain direction. Side U follows continuous rectangular perimeter with seam unwrap, caps use local orthogonal planar UV. Seeded offsets vary phase.','wood_target_px_per_m':RES/TILE,'wood_tile_m':TILE,'other_major_surface_mapping':{'Stone':{'method':'world triplanar shader projection','tile_m':2.5,'nominal_px_per_m':501.6},'Snow':{'method':'world triplanar shader projection','tile_m':5,'nominal_px_per_m':250.8}},'overlap_padding_policy':'Intentional repeating tile coordinates; no unique atlas claimed. Perimeter seams and endcaps are separate islands; no atlas padding needed. Texture mirror addressing supplies continuous boundary values.','meshes':[],'wood_components':[]}
all_dens=defaultdict(list);area_dens=defaultdict(list);total=0
for ob in sorted(bpy.data.objects,key=lambda o:o.name):
 if ob.type!='MESH' or not ob.name.startswith('SM_'):continue
 me=ob.data;me.calc_loop_triangles();before=digest(me);coords=np.array([tuple(v.co) for v in me.vertices],dtype=np.float64);uv=me.uv_layers.active.data
 parent=list(range(len(coords)))
 def find(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 def union(a,b):
  aa,bb=find(a),find(b)
  if aa!=bb:parent[bb]=aa
 for e in me.edges:union(*e.vertices)
 cv=defaultdict(list);cf=defaultdict(list)
 for i in range(len(coords)):cv[find(i)].append(i)
 for p in me.polygons:cf[find(p.vertices[0])].append(p.index)
 sidefaces=caps=0;max_alignment_error=0;component_index=0;face_grain={};face_class={}
 for root,faces in cf.items():
  names={me.materials[me.polygons[i].material_index].name for i in faces}
  if not names.intersection({'Wood','DarkWood'}):continue
  points=coords[cv[root]];center=points.mean(axis=0);evals,vecs=np.linalg.eigh(np.cov((points-center).T));L=vecs[:,2]
  eigen_ratio=float(evals[2]/max(evals[1],1e-12));extent=np.ptp(points,axis=0);policy='PCA longest axis'
  if eigen_ratio<1.25:
   choices=[i for i in range(3) if extent[i]>=max(extent)*.90];L=np.eye(3)[choices[0]];policy='deterministic cardinal longest-extent fallback (X,Y,Z priority within10%)'
  if L[np.argmax(np.abs(L))]<0:L=-L
  # Choose stable cross axes using the cardinal axis least parallel to length.
  basis=np.eye(3)[np.argmin(np.abs(L))];e1=np.cross(L,basis);e1/=np.linalg.norm(e1);e2=np.cross(L,e1)
  local=points-center;a=max(abs(local@e1));b=max(abs(local@e2));curve=None
  hi=int(np.argmax(extent[:2]));oi=1-hi
  curved_bridge=ob.name=='SM_Bridges' and extent[hi]>4 and extent[2]>.45 and extent[oi]<.5
  bent_roof=ob.name in ['SM_InnMain','SM_Bathhouse','SM_GuestEast','SM_GuestWest'] and extent[hi]>6 and extent[2]>2 and extent[oi]<.5
  if curved_bridge or bent_roof:
   hv=points[:,hi];zv=points[:,2];hmin,hmax=min(hv),max(hv);hmid=(hmin+hmax)*.5;bins=np.linspace(hmin,hmax,45);xs=[];zs=[]
   for lo,up in zip(bins,bins[1:]):
    mask=(hv>=lo)&(hv<=up)
    if mask.sum()>0:xs.append(float(np.mean(hv[mask])));zs.append(float((min(zv[mask])+max(zv[mask]))*.5))
   xs=np.array(xs);zs=np.array(zs)
   if curved_bridge:
    poly=np.polyfit(xs-hmid,zs,4);der=np.polyder(poly)
    z_at=lambda h:np.polyval(poly,np.asarray(h)-hmid)
    dz_at=lambda h:np.polyval(der,np.asarray(h)-hmid)
    policy='arched rail centerline quartic fit; integrated arc-length grain'
   else:
    # Symmetric pitched strips: centerline is a continuous two-leg V roof.
    fit=np.linalg.lstsq(np.column_stack([np.ones(len(xs)),np.abs(xs-hmid)]),zs,rcond=None)[0]
    z_at=lambda h:fit[0]+fit[1]*np.abs(np.asarray(h)-hmid)
    dz_at=lambda h:fit[1]*np.sign(np.asarray(h)-hmid)
    policy='pitched timber centerline piecewise-linear fit; integrated arc-length grain'
   grid=np.linspace(hmin,hmax,1025);dz=np.asarray(dz_at(grid));lengthsteps=np.diff(grid)*(np.sqrt(1+dz[:-1]**2)+np.sqrt(1+dz[1:]**2))*.5;arc=np.r_[0,np.cumsum(lengthsteps)]
   crosscenter=(min(points[:,oi])+max(points[:,oi]))*.5;a=float(max(abs(points[:,oi]-crosscenter)));b=float(max(abs((zv-z_at(hv))/np.sqrt(1+np.asarray(dz_at(hv))**2))))
   curve={'axis':hi,'other':oi,'grid':grid,'arc':arc,'z_at':z_at,'dz_at':dz_at,'crosscenter':crosscenter,'fit_rmse_m':float(np.sqrt(np.mean((zs-z_at(xs))**2)))}
  perim=4*(a+b)
  assert a>1e-8 and b>1e-8
  phase_u=(component_index*.38196601125)%1;phase_v=(component_index*.61803398875)%1
  def surface_coord(q):
   if curve:
    wp=q+center;h=wp[hi];slope=float(curve['dz_at'](h));tangent=np.zeros(3);tangent[hi]=1;tangent[2]=slope;tangent/=np.linalg.norm(tangent)
    return float(wp[oi]-curve['crosscenter']),float((wp[2]-curve['z_at'](h))/math.sqrt(1+slope*slope)),float(np.interp(h,curve['grid'],curve['arc'])),tangent
   return float(np.dot(q,e1)),float(np.dot(q,e2)),float(np.dot(q,L)),L
  def perimeter(q):
   x,y,_,_=surface_coord(q)
   if x/a>=abs(y/b):return y+b
   if y/b>=abs(x/a):return 2*b+(a-x)
   if -x/a>=abs(y/b):return 2*b+2*a+(b-y)
   return 4*b+2*a+(x+a)
  this_caps=0;this_sides=0
  for pi in faces:
   p=me.polygons[pi]
   if me.materials[p.material_index].name not in ['Wood','DarkWood']:continue
   pointsface=[coords[me.loops[li].vertex_index]-center for li in p.loop_indices]
   centerface=np.mean(pointsface,axis=0);_,_,_,tangent=surface_coord(centerface);face_grain[pi]=tangent
   endcap=abs(np.dot(np.array(p.normal),tangent))>.72;face_class[pi]='cap' if endcap else ('bend_side' if curve else 'straight_side')
   if endcap:
    this_caps+=1
    for li,q in zip(p.loop_indices,pointsface):
     xx,yy,_,_=surface_coord(q);uv[li].uv=(xx/TILE+phase_u,yy/TILE+phase_v)
   else:
    this_sides+=1;us=[perimeter(q) for q in pointsface]
    if max(us)-min(us)>perim*.5:us=[x+perim if x<perim*.5 else x for x in us]
    for li,q,x in zip(p.loop_indices,pointsface,us):uv[li].uv=(x/TILE+phase_u,surface_coord(q)[2]/TILE+phase_v)
    error=max(abs(uv[li].uv.y-(surface_coord(q)[2]/TILE+phase_v)) for li,q in zip(p.loop_indices,pointsface));max_alignment_error=max(max_alignment_error,error)
  report['wood_components'].append({'mesh':ob.name,'component':component_index,'material':sorted(names),'grain_axis_blender':L.tolist(),'principal_extent_m':float(np.ptp(local@L)),'side_faces':this_sides,'endcap_faces':this_caps,'side_v_is_axial':not bool(curve),'side_v_is_centerline_arclength':bool(curve),'perimeter_m':perim,'eigen_ratio':eigen_ratio,'orientation_policy':policy,'curve_fit_rmse_m':curve['fit_rmse_m'] if curve else None})
  sidefaces+=this_sides;caps+=this_caps;component_index+=1
 # Rare micro-bevel triangles can collapse under cylindrical/perimeter UV.
 # Explicit local planar fallback preserves density and is counted, not hidden.
 fallback=0
 for p in me.polygons:
  if me.materials[p.material_index].name not in ['Wood','DarkWood']:continue
  ls=list(p.loop_indices);v=[np.array(uv[i].uv) for i in ls];area=sum(abs(np.cross(v[j]-v[0],v[j+1]-v[0]))*.5 for j in range(1,len(v)-1))
  stretch=math.sqrt(area/max(p.area,1e-20))*TILE
  if area<1e-13 or stretch<.70 or stretch>1.50:
   fallback+=1;n=np.array(p.normal);y=face_grain[p.index]-n*np.dot(face_grain[p.index],n)
   if np.linalg.norm(y)<.05:y=np.cross(n,np.eye(3)[np.argmin(np.abs(n))])
   y/=np.linalg.norm(y);x=np.cross(y,n);face_class[p.index]='planar_bevel_or_cap_exception'
   for li in ls:
    co=coords[me.loops[li].vertex_index];uv[li].uv=(float(np.dot(co,x))/TILE,float(np.dot(co,y))/TILE)
 me.update();me.calc_loop_triangles();after=digest(me);assert before==after,(ob.name,'Geometry or normals changed')
 nonfinite=zero_uv=degenerate=0;exact=Counter();edges=defaultdict(list)
 for p in me.polygons:
  ids=list(p.vertices)
  for x,y in zip(ids,ids[1:]+ids[:1]):edges[tuple(sorted((x,y)))].append((x,y))
 for t in me.loop_triangles:
  p0,p1,p2=[coords[i] for i in t.vertices];area=np.linalg.norm(np.cross(p1-p0,p2-p0))*.5;uvs=np.array([tuple(uv[i].uv) for i in t.loops]);ua=abs(np.cross(uvs[1]-uvs[0],uvs[2]-uvs[0]))*.5
  if not np.isfinite(uvs).all():nonfinite+=1
  if ua<1e-13:zero_uv+=1
  if area<1e-12:degenerate+=1
  name=me.materials[t.material_index].name
  if area>0:
   density=(RES if name in ['Wood','DarkWood'] else 1024)*math.sqrt(ua/area);all_dens[name].append(density)
   if name in ['Wood','DarkWood']:area_dens[name].append((density,area,face_class.get(t.polygon_index,'other')))
  exact[tuple(sorted(tuple(round(float(k),6) for k in q) for q in uvs))]+=1
 conflicts=sum(len(v)==2 and v[0]==v[1] for v in edges.values());nonmanifold=sum(len(v)>2 for v in edges.values())
 assert nonfinite==zero_uv==degenerate==conflicts==nonmanifold==0,(ob.name,nonfinite,zero_uv,degenerate,conflicts,nonmanifold)
 total+=len(me.loop_triangles)
 rec={'mesh':ob.name,'vertices':len(me.vertices),'triangles':len(me.loop_triangles),'geometry_normal_hash_before':before,'geometry_normal_hash_after':after,'geometry_and_normals_unchanged':True,'wood_components':component_index,'wood_side_faces':sidefaces,'wood_endcap_faces':caps,'micro_bevel_planar_fallback_faces':fallback,'max_grain_alignment_error_uv':max_alignment_error,'nonfinite_uv':nonfinite,'zero_uv_area_triangles':zero_uv,'degenerate_triangles':degenerate,'edge_winding_conflicts':conflicts,'nonmanifold_edges':nonmanifold,'exact_reused_uv_triangles':sum(n-1 for n in exact.values() if n>1)}
 report['meshes'].append(rec)
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.export_scene.fbx(filepath=str(R/'Source'/(ob.name+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,global_scale=1,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,path_mode='STRIP')
 print('UV exported',ob.name,'wood components',component_index,'fallback',fallback,flush=True)
assert total==165742,total
report['final_triangles']=total;report['material_uv_density_px_per_m']={n:{'min':min(d),'median':statistics.median(d),'max':max(d),'count':len(d),'active_mapping':('new_component_grain_uv' if n in ['Wood','DarkWood'] else 'legacy_mesh_uv; Stone/Snow actual sampling is triplanar, see shader mapping')} for n,d in all_dens.items()}
report['wood_area_weighted_density']={}
for name,data in area_dens.items():
 rows=sorted(data,key=lambda r:r[0]);area=sum(x[1] for x in rows);quant={}
 for p in [.01,.05,.5,.95,.99]:
  cumulative=0
  for value,weight,cl in rows:
   cumulative+=weight
   if cumulative>=area*p:quant[str(p)]=value;break
 classes={cl:sum(w for d,w,c in rows if c==cl) for cl in set(x[2] for x in rows)}
 report['wood_area_weighted_density'][name]={'surface_area_m2':area,'percentiles_source_px_per_m':quant,'outlier_area_fraction_outside_70_to_150_percent':sum(w for d,w,c in rows if d<RES/TILE*.7 or d>RES/TILE*1.5)/area,'chart_area_m2':classes}
report['finished_at_utc']=datetime.now(timezone.utc).isoformat();report['seconds']=time.time()-start;report['status']='passed'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Source'/'SnowyOnsen_TextureImproved.blend'))
(R/'Validation'/'uv_geometry_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('UV PASS',total,'triangles geometry unchanged;',report['seconds'],'seconds',flush=True)
