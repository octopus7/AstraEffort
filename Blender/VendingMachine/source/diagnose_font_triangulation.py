import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/VendingMachine_prebake.blend'))
original=bpy.data.objects['Price_1_4']
results={}
for mode in ['current','alltri','planar_alltri']:
    o=original.copy();o.data=original.data.copy();bpy.context.collection.objects.link(o)
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges))
    if mode=='planar_alltri':bmesh.ops.dissolve_limit(bm,angle_limit=1e-6,use_dissolve_boundaries=True,verts=list(bm.verts),edges=list(bm.edges),delimit=set())
    bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>(4 if mode=='current' else 3)],quad_method='BEAUTY',ngon_method='BEAUTY')
    bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges))
    if mode!='current':bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3],quad_method='BEAUTY',ngon_method='BEAUTY')
    bm.to_mesh(o.data);bm.free();o.data.update()
    bpy.context.scene.tool_settings.use_uv_select_sync=True
    if not o.data.uv_layers:o.data.uv_layers.new()
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=0,area_weight=0,correct_aspect=True,scale_to_bounds=False);bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.select_all(action='SELECT');bpy.ops.uv.average_islands_scale(scale_uv=False,shear=False);bpy.ops.uv.pack_islands('EXEC_DEFAULT',rotate=True,scale=True,merge_overlap=False,margin_method='FRACTION',margin=.002,shape_method='CONVEX');bpy.ops.object.mode_set(mode='OBJECT')
    me=o.data;me.calc_loop_triangles();bad=[];uvbad=0;mtx=np.array(o.matrix_world,dtype=np.float64)
    for t in me.loop_triangles:
        vs=np.array([me.vertices[i].co[:] for i in t.vertices],dtype=np.float64)
        area=float(np.linalg.norm(np.cross(vs[1]-vs[0],vs[2]-vs[0]))*.5)
        vworld=[o.matrix_world@me.vertices[i].co for i in t.vertices]
        worldarea=(vworld[1]-vworld[0]).cross(vworld[2]-vworld[0]).length*.5
        u=np.array([me.uv_layers.active.data[li].uv[:] for li in t.loops],dtype=np.float64);ua=abs(np.cross(u[1]-u[0],u[2]-u[0]))*.5
        uvbad+=int(ua<1e-16)
        if area<1e-14 or worldarea<1e-14:bad.append({'triangle':t.index,'localarea':area,'worldarea':worldarea,'t_area':t.area,'uvarea':float(ua),'verts':vs.tolist()})
    bm=bmesh.new();bm.from_mesh(me);nm=sum(not e.is_manifold for e in bm.edges);bm.free()
    results[mode]={'bad':bad,'uvbad':uvbad,'nonmanifold':nm,'triangles':len(me.loop_triangles)}
(ROOT/'validation/font_triangulation_diagnosis.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results),flush=True)
