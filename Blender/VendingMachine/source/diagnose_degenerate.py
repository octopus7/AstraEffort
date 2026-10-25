import bpy,bmesh,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/VendingMachine_prebake.blend'))
result={}
for name in ['Price_1_3','Price_1_4','Price_2_4','Price_3_4']:
    o=bpy.data.objects[name];me=o.data;me.calc_loop_triangles()
    bad=[t for t in me.loop_triangles if t.area<1e-14]
    entry={'before':len(bad),'degenerate_triangle_vertices':[[list(me.vertices[i].co) for i in t.vertices] for t in bad]}
    bm=bmesh.new();bm.from_mesh(me)
    bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges))
    bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4],quad_method='BEAUTY',ngon_method='BEAUTY')
    bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges))
    bm.to_mesh(me);bm.free();me.update();me.calc_loop_triangles()
    bm=bmesh.new();bm.from_mesh(me)
    entry['after']=sum(t.area<1e-14 for t in me.loop_triangles)
    entry['after_nonmanifold_edges']=sum(not e.is_manifold for e in bm.edges);bm.free()
    result[name]=entry
(ROOT/'validation/font_degenerate_diagnosis.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result),flush=True)
