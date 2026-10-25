import bpy, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'mountain_observatory.blend'))
o=bpy.data.objects['Dome west continuous shell']; me=o.data; me.calc_loop_triangles(); uv=me.uv_layers.active.data
bad=[]
for t in me.loop_triangles:
    a,b,c=[uv[i].uv for i in t.loops]
    area=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5
    if area<=1e-14:
        bad.append({'polygon':t.polygon_index,'uv_area':area,'uv':[list(uv[i].uv) for i in t.loops],'world':[list(o.matrix_world@me.vertices[i].co) for i in t.vertices]})
pivot=Vector((0,-.55,4.18)); axis=Vector((0,-.66,.751265)).normalized()
hit,loc,normal,idx,obj,mat=bpy.context.scene.ray_cast(bpy.context.evaluated_depsgraph_get(),pivot+axis*1.55,-axis,distance=1.2)
result={'uv_collapse_evidence':bad,'optical_axis_front_ray':{'hit':hit,'object':obj.name if obj else None,'location':list(loc)}}
(ROOT/'diagnostic_initial.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2),flush=True)
