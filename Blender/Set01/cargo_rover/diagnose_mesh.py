import bpy,bmesh,json
from pathlib import Path
root=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root/'cargo_rover.blend'))
out=[]
for o in bpy.data.collections['ASSET'].all_objects:
 if o.type!='MESH':continue
 o.data.calc_loop_triangles()
 deg=sum(t.area<1e-12 for t in o.data.loop_triangles)
 bm=bmesh.new();bm.from_mesh(o.data)
 odd=sum(not e.is_manifold for e in bm.edges)
 if deg or odd or 'fender' in o.name.lower():out.append({'name':o.name,'degen_triangles':deg,'nonmanifold_edges':odd,'verts':len(bm.verts)})
 bm.free()
(root/'mesh_diagnostics.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
