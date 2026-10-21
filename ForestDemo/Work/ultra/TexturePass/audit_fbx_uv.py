import bpy, json, math, time, datetime
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/TexturePass')
source=json.loads((ROOT/'uv_report.json').read_text()); N=source['texture_resolution'][0]
bpy.ops.wm.read_factory_settings(use_empty=True)
report={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'Independent FBX re-import in Blender; actual stored float32 UVs and world-space triangulated mesh areas, rectangle intersection check using spatial bins.','meshes':[]}
for index,record in enumerate(source['meshes']):
 bpy.ops.import_scene.fbx(filepath=str(ROOT/'SourceArt'/(record['variant']+'.fbx')),use_custom_normals=True)
 ob=next(o for o in bpy.context.scene.objects if o.type=='MESH');mesh=ob.data;mesh.calc_loop_triangles();uv=mesh.uv_layers.active.data
 density=[];areas=[];uvareas=[];boxes=[];buckets={};overlap=0;min_gap=999.;degenerate=0
 for t in mesh.loop_triangles:
  p=[ob.matrix_world@mesh.vertices[v].co for v in t.vertices];xy=[uv[l].uv.copy() for l in t.loops]
  area=(p[1]-p[0]).cross(p[2]-p[0]).length*.5
  ua=abs((xy[1].x-xy[0].x)*(xy[2].y-xy[0].y)-(xy[1].y-xy[0].y)*(xy[2].x-xy[0].x))*.5
  areas.append(area);uvareas.append(ua)
  if area>1e-12:density.append(N*math.sqrt(ua/area))
  else:degenerate+=1
  b=(min(x.x for x in xy),min(x.y for x in xy),max(x.x for x in xy),max(x.y for x in xy))
  cells=[(x,y) for x in range(int(b[0]*40)-1,int(b[2]*40)+2) for y in range(int(b[1]*40)-1,int(b[3]*40)+2)]
  candidates=set(i for c in cells for i in buckets.get(c,[]))
  for i in candidates:
   a=boxes[i];dx=max(a[0]-b[2],b[0]-a[2],0);dy=max(a[1]-b[3],b[1]-a[3],0)
   if dx==0 and dy==0:overlap+=1
   min_gap=min(min_gap,math.hypot(dx,dy)*N)
  for cell in cells:buckets.setdefault(cell,[]).append(len(boxes))
  boxes.append(b)
 density.sort(); total=sum(areas);uatotal=sum(uvareas)
 row={'variant':record['variant'],'triangles':len(areas),'world_area_m2':total,'uv_area':uatotal,'area_weighted_px_m':N*math.sqrt(uatotal/total),'per_triangle_px_m_min':min(density),'per_triangle_px_m_p01':density[int(len(density)*.01)],'per_triangle_px_m_p99':density[int(len(density)*.99)],'per_triangle_px_m_max':max(density),'island_bbox_overlap_count':overlap,'minimum_bbox_gap_pixels':min_gap,'uv_in_unit_square':all(b[0]>=0 and b[1]>=0 and b[2]<=1 and b[3]<=1 for b in boxes),'degenerate_triangles':degenerate}
 row['passed']=overlap==0 and row['uv_in_unit_square'] and abs(row['area_weighted_px_m']-32)<.02 and min_gap>=2.99
 report['meshes'].append(row)
 bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(mesh)
 if index%50==0:print('UV_FBX_AUDIT',index,flush=True);(ROOT/'uv_fbx_validation.json').write_text(json.dumps(report,indent=2))
report['success']=all(x['passed'] for x in report['meshes']);report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(ROOT/'uv_fbx_validation.json').write_text(json.dumps(report,indent=2));print('UV_FBX_AUDIT_COMPLETE',report['success'],flush=True)
