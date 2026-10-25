import bpy, json, os, math, datetime
from mathutils import Vector
ROOT=os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(ROOT,'manifest.json'),encoding='utf8') as f: m=json.load(f)
results=[]
for info in m['assets']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    path=os.path.join(ROOT,info['name']+'.fbx')
    bpy.ops.import_scene.fbx(filepath=path,use_custom_normals=True)
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    assert len(meshes)==1, (path,len(meshes))
    o=meshes[0]; me=o.data; me.calc_loop_triangles()
    bounds={'min':[min(v.co[i] for v in me.vertices) for i in range(3)],'max':[max(v.co[i] for v in me.vertices) for i in range(3)]}
    for side in ('min','max'):
        for v,expected in zip(bounds[side],info['bounds_local_m'][side]): assert abs(v-expected)<.0001,(o.name,side,v,expected)
    assert o.location.length<.00001,(o.name,'nonzero local origin',o.location[:])
    assert all(abs(v-1)<.00001 for v in o.scale),(o.name,o.scale[:])
    assert me.uv_layers.active.name=='UV0'
    assert sorted(x.name for x in me.materials)==sorted(info['material_slots'])
    assert len(bpy.data.images)==0, 'Unexpected embedded image'
    degenerate=0; out=0
    uv=me.uv_layers.active.data
    for t in me.loop_triangles:
        pts=[uv[i].uv[:] for i in t.loops]
        ua=abs((pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1])-(pts[1][1]-pts[0][1])*(pts[2][0]-pts[0][0]))*.5
        if t.area>1e-12 and ua<=1e-12: degenerate+=1
        out+=sum(1 for u,v in pts if u < -1e-5 or u > 1.00001 or v < -1e-5 or v > 1.00001)
    rays={}
    if o.name.startswith('SM_MillTower'):
        for label,start in [('entry',(0,-6,1.20)),('entry_upper',(.3,-6,2.35)),('front_window',(0.12,-6,4.10))]:
            hit,loc,n,face=o.ray_cast(Vector(start),Vector((0,1,0)))
            rays[label]={'hit':hit,'position_m':list(loc),'material':me.materials[me.polygons[face].material_index].name if hit else None}
        assert rays['entry']['material'] in ('Wood','WoodLight'),rays
        assert rays['front_window']['material']=='Glass',rays
    assert degenerate==0,(o.name,'degenerate_uv_triangles',degenerate)
    assert out==0,(o.name,'outside_01',out)
    results.append({'file':path,'name':o.name,'triangles':len(me.loop_triangles),'bounds_m':bounds,'origin_local':list(o.location),
        'scale':list(o.scale),'material_slots':[x.name for x in me.materials],'uv_layer':me.uv_layers.active.name,
        'degenerate_uv_triangles':degenerate,'outside_01':out,'architectural_front_rays':rays})
report={'validated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'blender_version':bpy.app.version_string,
        'method':'Fresh factory-empty scene and FBX reimport per asset. Bounds/pivots/materials/UVs and entry-window surface raycasts compared.',
        'assets':results,'status':'passed','engine_validation':'Not performed here; parent task owns Unreal import/runtime verification.'}
with open(os.path.join(ROOT,'fbx_roundtrip_validation.json'),'w',encoding='utf8') as f: json.dump(report,f,indent=2)
print('WINDMILL_ROUNDTRIP_PASSED',json.dumps(report),flush=True)
