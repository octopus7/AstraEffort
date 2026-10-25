import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source.blend'))
report={}
for ob in bpy.data.objects:
    if ob.type!='MESH':continue
    uv=ob.data.uv_layers.active.data
    bad=[]
    for p in ob.data.polygons:
        a,b,c=[uv[i].uv for i in p.loop_indices]
        au=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5
        if au<1e-12:
            bad.append({'face':p.index,'world_area':p.area,'uv_area':au,'material':ob.data.materials[p.material_index].name,
                        'vertices':[tuple(ob.data.vertices[v].co) for v in p.vertices],
                        'uvs':[tuple(uv[i].uv) for i in p.loop_indices]})
    report[ob.name]={'bad_count':len(bad),'bad_world_area_total':sum(p['world_area'] for p in bad),'samples':bad[:15]}
(ROOT/'uv_diagnosis.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
