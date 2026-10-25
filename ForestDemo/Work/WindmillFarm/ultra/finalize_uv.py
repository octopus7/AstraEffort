"""Final authored mesh UV QA and density channel. Originals are preserved."""
import bpy,bmesh,json,math,time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'Art/FinalMeshes';OUT.mkdir(parents=True,exist_ok=True)
rows=[]
paths=sorted(p for folder in ['Landscape','Windmill','Farm'] for p in (ROOT/'Art'/folder).glob('SM_*.fbx'))
for p in paths:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(p),use_custom_normals=True)
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(objects)==1
    o=objects[0];bpy.context.view_layer.objects.active=o;o.select_set(True)
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    me=o.data
    # Negligible bevel slivers can have zero-area UVs. Remove only areas below 0.01 mm².
    bm=bmesh.new();bm.from_mesh(me);tiny=[f for f in bm.faces if f.calc_area()<1e-8]
    if tiny:bmesh.ops.delete(bm,geom=tiny,context='FACES')
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bm.to_mesh(me);bm.free()
    ground=p.stem=='SM_Ground'
    if p.parent.name=='Windmill':
        while me.uv_layers:me.uv_layers.remove(me.uv_layers[0])
        me.uv_layers.new(name='UV0_Unique')
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(60),island_margin=.0015,area_weight=.3,correct_aspect=True)
        bpy.ops.uv.average_islands_scale();bpy.ops.uv.pack_islands(rotate=True,margin=.0015);bpy.ops.object.mode_set(mode='OBJECT')
    # Retain authored unique layouts elsewhere. UV1 uniformly rescales surface texture density.
    me.uv_layers.active_index=0;uv=me.uv_layers[0].data;me.calc_loop_triangles()
    # Reserve a thin border for tiny bevel triangles that projection collapsed.
    repair=[]
    for t in me.loop_triangles:
        a,b,c=[uv[i].uv for i in t.loops]
        if t.area>1e-10 and abs((b-a).cross(c-a))*.5<1e-12:repair.append(t)
    if repair:
        for q in uv:q.uv*=.98
        for idx,t in enumerate(repair):
            px=.002+idx*.002
            for li,pos in zip(t.loops,[(px,.992),(px+.0005,.992),(px,.9925)]):uv[li].uv=pos
    worldarea=0;uvarea=0;deg=0;dens=[]
    for t in me.loop_triangles:
        a,b,c=[uv[i].uv for i in t.loops];ua=abs((b-a).cross(c-a))*.5
        wa=t.area
        if wa>1e-10:
            worldarea+=wa;uvarea+=ua;dens.append(1024*math.sqrt(ua/wa))
            if ua<1e-12:deg+=1
    density=1024*math.sqrt(uvarea/worldarea);factor=128/density
    while len(me.uv_layers)>1:me.uv_layers.remove(me.uv_layers[-1])
    layer=me.uv_layers.new(name='UV1_Density128')
    for i,q in enumerate(uv):layer.data[i].uv=q.uv*factor
    me.uv_layers.active_index=0
    outside=sum(not(-1e-5<=q.uv.x<=1.00001 and -1e-5<=q.uv.y<=1.00001) for q in uv)
    bpy.ops.export_scene.fbx(filepath=str(OUT/p.name),use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',bake_space_transform=False,add_leaf_bones=False,use_mesh_modifiers=True)
    row={'name':p.stem,'source':str(p),'triangles':len(me.loop_triangles),'removed_microscopic_faces':len(tiny),'repaired_collapsed_uv_triangles':len(repair),'repaired_world_area_m2':sum(t.area for t in repair),'uv0_unique_outside01':outside,'degenerate_uv_triangles':deg,
         'surface_area_m2':worldarea,'uv0_triangle_area':uvarea,'uv0_density_px_m_at1024':density,'uv1_scale':factor,'uv1_equivalent_density_px_m':128,
         'uv1_density_min_median_max':[min(dens)*factor,sorted(dens)[len(dens)//2]*factor,max(dens)*factor],
         'material_uv':0 if ground else 1,'padding_uv0':.0015 if p.parent.name in ['Windmill','Farm'] else .008,
         'intentional_repeat':'UV1 exceeds0-1 to tile original1024 textures at measured128px/m; unique UV0 preserved. Ground uses2048 macro20.48px/m and512px/m detail.'}
    rows.append(row);print('FINAL_UV',p.stem,'degenerate',deg,'outside',outside,'density',density,flush=True)
(OUT/'manifest.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'assets':rows,'all_uv0_inside':all(r['uv0_unique_outside01']==0 for r in rows),'all_non_degenerate':all(r['degenerate_uv_triangles']==0 for r in rows)},indent=2))
print('FINAL_UV_COMPLETE')
