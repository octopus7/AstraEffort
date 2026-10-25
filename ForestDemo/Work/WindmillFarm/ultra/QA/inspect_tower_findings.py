"""Read-only precision recheck of first independent tower findings."""
import bpy
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('qa_module', OUT/'inspect_final_meshes.py')
qa=importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)
path=OUT.parent/'Art'/'FinalMeshes'/'SM_MillTower.fbx'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(path),use_anim=False,use_custom_normals=False)
obj=next(o for o in bpy.context.scene.objects if o.type=='MESH')
mesh=obj.data
mesh.calc_loop_triangles()
indices=[1269,1288,1305,1341,1355,18135,18148,18161,18174,56034,57213,57215,57258,57260]
items=[]
for idx in indices:
    tri=mesh.loop_triangles[idx]
    points=[obj.matrix_world@mesh.vertices[i].co for i in tri.vertices]
    rec={'triangle':idx,'polygon':tri.polygon_index,'vertices':list(tri.vertices),
        'material':mesh.materials[tri.material_index].name,
        'world_vertices_m':[list(v) for v in points],
        'world_area_m2':(points[1]-points[0]).cross(points[2]-points[0]).length*.5,
        'edge_lengths_m':[(points[(i+1)%3]-points[i]).length for i in range(3)]}
    for li in range(2):
        uv=tuple(tuple(mesh.uv_layers[li].data[i].uv) for i in tri.loops)
        rec[f'uv{li}']=uv
        rec[f'uv{li}_area']=qa.triangle_area(uv)
    items.append(rec)
overlap=[]
for a,b in [(57215,57213),(57260,57258)]:
    ta=next(x['uv0'] for x in items if x['triangle']==a)
    tb=next(x['uv0'] for x in items if x['triangle']==b)
    checks=[]
    for epsilon in [0.0,1e-15,1e-14,1e-12]:
        qa.CLIP_EPSILON=epsilon
        checks.append({'classification_epsilon':epsilon,'area_uv2':qa.intersection_area(ta,tb)})
    overlap.append({'triangles':[a,b],'epsilon_rechecks':checks})
result={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':qa.hashfile(path),
        'triangles':items,'overlap_precision_recheck':overlap}
(OUT/'tower_findings_detail.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'overlap_precision_recheck':overlap}),flush=True)
