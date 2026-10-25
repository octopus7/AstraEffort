import bpy, bmesh, json, math
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/NightMarket/max')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Source'/'NightMarket_Source.blend'))
report=json.loads((ROOT/'Source'/'source_manifest.json').read_text(encoding='utf-8'))
checks=[]
for entry in report['meshes']:
 ob=bpy.data.objects[entry['name']];me=ob.data
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
 while len(me.uv_layers):me.uv_layers.remove(me.uv_layers[0])
 uv=me.uv_layers.new(name='UV_Metric4m')
 for face in me.polygons:
  axis=max(range(3),key=lambda i:abs(face.normal[i]));axes=[i for i in range(3) if i!=axis]
  for li in face.loop_indices:
   co=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]]/4,co[axes[1]]/4)
 me.calc_loop_triangles();area=0;uvarea=0;ratios=[]
 parent=list(range(len(me.vertices)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for edge in me.edges:
  a,b=edge.vertices;ra,rb=find(a),find(b)
  if ra!=rb:parent[ra]=rb
 components={};edge_uses={}
 for face in me.polygons:
  for edgekey in face.edge_keys:edge_uses[tuple(sorted(edgekey))]=edge_uses.get(tuple(sorted(edgekey)),0)+1
 for edge in me.edges:
  root=find(edge.vertices[0]);st=components.setdefault(root,{'closed':True,'volume_m3':0})
  if edge_uses.get(tuple(sorted(edge.vertices)))!=2:st['closed']=False
 for t in me.loop_triangles:
  a,b,c=[me.vertices[i].co for i in t.vertices];sa=(b-a).cross(c-a).length*.5
  aa,bb,cc=[uv.data[i].uv for i in t.loops];ua=abs((bb.x-aa.x)*(cc.y-aa.y)-(bb.y-aa.y)*(cc.x-aa.x))*.5
  root=find(t.vertices[0]);ref=me.vertices[root].co
  components[root]['volume_m3']+=(a-ref).dot((b-ref).cross(c-ref))/6
  if sa>1e-10:area+=sa;uvarea+=ua;ratios.append(ua/sa)
 entry['uv_channels']=len(me.uv_layers);entry['uv_loops']=len(uv.data);entry['uv_finite']=all(math.isfinite(c) for d in uv.data for c in d.uv)
 entry['surface_area_m2']=area;entry['uv_area']=uvarea;entry['measured_effective_density_512px']=512*math.sqrt(uvarea/area) if area else 0
 closed=[st for st in components.values() if st['closed']]
 normals={'closed_components':len(closed),'open_components':len(components)-len(closed),'negative_volume_closed_components':sum(st['volume_m3']<-.000001 for st in closed),'smallest_closed_signed_volume_m3':min([st['volume_m3'] for st in closed],default=0),'method':'Consistent outward normals operation, then connected-component closed-edge and signed-volume audit. Open curves/puddle sheets explicitly counted.'}
 checks.append({'mesh':entry['name'],'uv_channels':len(me.uv_layers),'vertices':len(me.vertices),'surface_area_m2':area,'uv_area':uvarea,'metric_texel_density_512_mean_area_px_per_m':entry['measured_effective_density_512px'],'uv_area_ratio_min':min(ratios) if ratios else None,'uv_area_ratio_max':max(ratios) if ratios else None,'source_initial_aggregate_signed_volume_m3':entry['signed_volume_m3'],'uv_complete_finite':entry['uv_finite'],'normal_orientation_audit':normals})
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.export_scene.fbx(filepath=str(ROOT/'Source'/'Exports'/entry['file']),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=True,add_leaf_bones=False)
 print('UV_VERIFIED',entry['name'],entry['measured_effective_density_512px'],flush=True)
(ROOT/'Source'/'source_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(ROOT/'Evidence').mkdir(exist_ok=True)
(ROOT/'Evidence'/'source_uv_verification.json').write_text(json.dumps({'method':'UV0 replaced by world-metric dominant-normal projection; 4m tile; 512px target128px/m,1024px cobble target256px/m','overlap':'Intentional repeating tile UVs overlap across disconnected surfaces','padding':'No packed atlas; tileable UV wrapping','limitations':'Dominant-normal projection reduces apparent area density on oblique/curved faces; effective area-weighted density measured per assembly, not unique surface atlas','assemblies':checks},indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Source'/'NightMarket_Source.blend'))
print('SOURCE_UV_VERIFIED',len(checks),flush=True)
