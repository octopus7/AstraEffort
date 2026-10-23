"""Audit final authored base meshes and UV metrics, without changing artwork."""
import bpy,math,json,statistics,time
from collections import defaultdict,Counter
from pathlib import Path
from datetime import datetime,timezone
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max')
bpy.ops.wm.open_mainfile(filepath=str(R/'Source'/'SnowyOnsen_original.blend'))
result={'at_utc':datetime.now(timezone.utc).isoformat(),'objects':[],'material_density':{},'policy':{'repeated_uvs':'Intentional tile reuse across all primitives; exact duplicate UV triangles counted below. No atlas packing claimed.','padding':'Texture uses wrapping, so atlas padding is not applicable. Steam uses dedicated normalized alpha cards, with feathered alpha edges.','overlap_exception':'Shared tile coordinates and projected opposite faces intentionally overlap; decorative snow/stone primitives also intentionally intersect in 3D.','density_targets_px_per_m':{'Snow':64,'Steam':'normalized single-card mask; scales by card dimensions','other':128}}}
dens=defaultdict(list)
for ob in sorted(bpy.data.objects,key=lambda o:o.name):
 if ob.type!='MESH' or not ob.name.startswith('SM_'):continue
 me=ob.data;me.calc_loop_triangles();uv=me.uv_layers.active.data;edges=defaultdict(list);bad_uv=0;deg=0;uvzero=0;triuv=Counter()
 for p in me.polygons:
  ids=list(p.vertices)
  for a,b in zip(ids,ids[1:]+ids[:1]):edges[tuple(sorted((a,b)))].append((a,b))
 for t in me.loop_triangles:
  a,b,c=[me.vertices[i].co for i in t.vertices];area=(b-a).cross(c-a).length*.5;us=[tuple(uv[i].uv) for i in t.loops]
  if not all(math.isfinite(k) for pp in us for k in pp):bad_uv+=1
  ua=abs((us[1][0]-us[0][0])*(us[2][1]-us[0][1])-(us[1][1]-us[0][1])*(us[2][0]-us[0][0]))*.5
  if area<1e-12:deg+=1
  if ua<1e-12:uvzero+=1
  if area>1e-12:dens[me.materials[t.material_index].name].append(1024*math.sqrt(ua/area))
  triuv[tuple(sorted(tuple(round(k,6) for k in p) for p in us))]+=1
 nonmanifold=sum(len(v)>2 for v in edges.values());boundary=sum(len(v)==1 for v in edges.values());inconsistent=sum(len(v)==2 and v[0]==v[1] for v in edges.values())
 record={'mesh':ob.name,'vertices':len(me.vertices),'source_triangles':len(me.loop_triangles),'edge_winding_conflicts':inconsistent,'nonmanifold_edges':nonmanifold,'boundary_edges':boundary,'nonfinite_uv_triangles':bad_uv,'zero_uv_area_triangles':uvzero,'degenerate_geometry_triangles':deg,'exact_reused_uv_triangles':sum(n-1 for n in triuv.values() if n>1),'maximum_uv_triangle_reuse':max(triuv.values()),'modifiers':[(m.name,m.type) for m in ob.modifiers]}
 assert inconsistent==0 and nonmanifold==0 and bad_uv==0 and deg==0 and uvzero==0,record
 if ob.name not in ['SM_Water','SM_Steam']:assert boundary==0,record
 result['objects'].append(record)
for key,values in dens.items():result['material_density'][key]={'triangles':len(values),'min_px_per_m':min(values),'median_px_per_m':statistics.median(values),'max_px_per_m':max(values)}
result['status']='passed'
(R/'Validation'/'uv_winding_audit.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print('AUDIT PASS',len(result['objects']),'objects; per-edge winding, manifoldness, nondegenerate UV and geometry',flush=True)
