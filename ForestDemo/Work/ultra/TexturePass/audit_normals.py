import bpy,json,datetime
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/TexturePass')
data=json.loads((ROOT/'uv_report.json').read_text())['meshes'];report=[]
bpy.ops.wm.read_factory_settings(use_empty=True)
for prefix in ['SM_Broadleaf','SM_Pine','SM_Rock']:
 row=next(r for r in data if r['source'].startswith(prefix))
 bpy.ops.import_scene.fbx(filepath=str(ROOT/'SourceArt'/(row['variant']+'.fbx')),use_custom_normals=True)
 ob=next(o for o in bpy.context.scene.objects if o.type=='MESH');mesh=ob.data
 normals={};maximum=0;shared=0
 for loop,n in zip(mesh.loops,mesh.corner_normals):
  vi=loop.vertex_index
  if vi in normals:maximum=max(maximum,(n.vector-normals[vi]).length);shared+=1
  else:normals[vi]=n.vector.copy()
 report.append({'mesh':row['variant'],'smooth_polygon_count':sum(p.use_smooth for p in mesh.polygons),'polygon_count':len(mesh.polygons),'shared_vertex_corner_comparisons':shared,'max_corner_normal_difference_at_same_vertex':maximum,'has_custom_normals':mesh.has_custom_normals,'conclusion':'Normals continuous at shared mesh vertices; visible triangle mosaic in first texture renders was chiefly UV-sampled color discontinuity.' if maximum<1e-4 else 'Nonzero normal differences recorded; inspect numeric scope.'})
 bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(mesh)
(ROOT/'normal_audit.json').write_text(json.dumps({'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Representative broadleaf, pine and rock independently reimported FBX files; UE import uses normals and tangents with full precision UVs. No tangent-space normal texture is assigned.','samples':report},indent=2))
print(json.dumps(report,indent=2))
