import bpy,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'service_mech.blend'))
out=[]
for ob in bpy.data.collections['ASSET'].objects:
    me=ob.data;me.calc_loop_triangles();bad=[]
    uv=me.uv_layers.active;bad_uv=0
    for tr in me.loop_triangles:
        a,b,c=[ob.matrix_world@me.vertices[i].co for i in tr.vertices]
        area=(b-a).cross(c-a).length*.5
        if area<1e-12:bad.append({'polygon':tr.polygon_index,'vertices':list(tr.vertices),'area':area})
        if uv:
            a,b,c=[uv.data[i].uv for i in tr.loops]
            if abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5<1e-12:bad_uv+=1
    if bad or bad_uv:out.append({'name':ob.name,'bad_triangles':len(bad),'bad_uv':bad_uv,'triangle_count':len(me.loop_triangles),'examples':bad[:3]})
out.sort(key=lambda q:q['bad_triangles'],reverse=True)
(ROOT/'degenerate_diagnosis.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps(out,indent=2))
