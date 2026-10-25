import bpy, bmesh, json, math, os, hashlib, time
from mathutils import Vector
from datetime import datetime, timezone

ROOT=os.path.dirname(os.path.abspath(__file__))
START=time.time()
def utc():return datetime.now(timezone.utc).isoformat()
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def inspect(label, objects):
    meshes=[o for o in objects if o.type=='MESH']
    tri_count=0;verts=[];bad_geometry=[];bad_uv=[];no_uv=[];bad_material=[]
    missing_images=[];manifold=[];raw_boundary=[];bad_normals=[]
    for o in meshes:
        m=o.data;m.calc_loop_triangles()
        uv=m.uv_layers.active.data if m.uv_layers.active else None
        if uv is None:no_uv.append(o.name)
        for v in m.vertices:
            p=o.matrix_world@v.co
            if not all(math.isfinite(c) for c in p):bad_geometry.append([o.name,'nonfinite vertex',v.index])
            verts.append(p)
        for t in m.loop_triangles:
            tri_count+=1
            p=[o.matrix_world@m.vertices[i].co for i in t.vertices]
            area=(p[1]-p[0]).cross(p[2]-p[0]).length*.5
            if not math.isfinite(area) or area<=1e-13:bad_geometry.append([o.name,'zero area triangle',t.index,area])
            if uv:
                a,b,c=[uv[i].uv for i in t.loops]
                area_uv=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5
                if not all(math.isfinite(v) for p in (a,b,c) for v in p) or area_uv<=1e-13:bad_uv.append([o.name,t.index,area_uv])
            if t.material_index>=len(m.materials) or not m.materials[t.material_index]:bad_material.append([o.name,t.index,t.material_index])
        bm=bmesh.new();bm.from_mesh(m)
        before=sum(1 for e in bm.edges if not e.is_manifold)
        if before:raw_boundary.append({'object':o.name,'edges':before})
        # glTF splits vertices along UV/normal seams. Weld positions only for connectivity inspection.
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
        after=sum(1 for e in bm.edges if not e.is_manifold)
        if after:manifold.append({'object':o.name,'edges':after})
        bm.free()
    for im in bpy.data.images:
        if im.source=='FILE' and not im.packed_file and not os.path.exists(bpy.path.abspath(im.filepath)):
            missing_images.append(im.name)
    lo=[min(v[i] for v in verts) for i in range(3)] if verts else None
    hi=[max(v[i] for v in verts) for i in range(3)] if verts else None
    out={'format':label,'mesh_objects':len(meshes),'triangles':tri_count,'vertices':len(verts),'bounds_min':lo,'bounds_max':hi,
         'dimensions':[hi[i]-lo[i] for i in range(3)] if verts else None,'non_mesh_objects':[{'name':o.name,'type':o.type} for o in objects if o.type!='MESH'],
         'nonfinite_or_zero_area_geometry':bad_geometry,'missing_uv_objects':no_uv,'degenerate_or_nonfinite_uv_triangles':bad_uv,
         'missing_material_faces':bad_material,'missing_external_images':missing_images,
         'nonmanifold_before_position_weld':raw_boundary,'nonmanifold_after_position_weld':manifold,
         'studio_named_meshes':[o.name for o in meshes if 'STUDIO' in o.name or o.name.lower() in ('floor','ground','plane')],
         'material_names':sorted(set(mat.name for o in meshes for mat in o.data.materials if mat))}
    print('VALIDATION',label,'meshes',len(meshes),'tris',tri_count,'bad_geo',len(bad_geometry),'bad_uv',len(bad_uv),'weld_nonmanifold',len(manifold),flush=True)
    return out

begin=utc()
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'mine_elevator.blend'))
blend=inspect('BLEND',list(bpy.data.collections['ASSET'].all_objects))
scene_units={'system':bpy.context.scene.unit_settings.system,'scale_length':bpy.context.scene.unit_settings.scale_length}
saved_collections=[c.name for c in bpy.context.scene.collection.children]
results=[blend]
for ext in ('glb','fbx'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if ext=='glb':bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT,'mine_elevator.glb'))
    else:bpy.ops.import_scene.fbx(filepath=os.path.join(ROOT,'mine_elevator.fbx'))
    results.append(inspect(ext.upper(),list(bpy.context.scene.objects)))

checks={
 'all_formats_nonempty':all(r['mesh_objects']>0 and r['triangles']>0 for r in results),
 'exact_triangle_consistency':len(set(r['triangles'] for r in results))==1,
 'mesh_object_consistency':len(set(r['mesh_objects'] for r in results))==1,
 'transformed_vertex_bounds_consistent':all(max(abs(r[k][i]-blend[k][i]) for k in ('bounds_min','bounds_max') for i in range(3))<1e-5 for r in results),
 'finite_nonzero_geometry':all(not r['nonfinite_or_zero_area_geometry'] for r in results),
 'uv_coverage_and_finite_nonzero_area':all(not r['missing_uv_objects'] and not r['degenerate_or_nonfinite_uv_triangles'] for r in results),
 'material_coverage':all(not r['missing_material_faces'] for r in results),
 'no_missing_external_images':all(not r['missing_external_images'] for r in results),
 'exports_geometry_only':all(not r['non_mesh_objects'] and not r['studio_named_meshes'] for r in results[1:]),
 'all_components_closed_after_position_weld':all(not r['nonmanifold_after_position_weld'] for r in results),
 'ground_contact_at_zero':abs(blend['bounds_min'][2])<1e-6,
 'meters':scene_units['system']=='METRIC' and abs(scene_units['scale_length']-1)<1e-8,
 'asset_and_studio_collections_separated':'ASSET' in saved_collections and 'STUDIO' in saved_collections,
}
files={}
for name in ('mine_elevator.blend','mine_elevator.glb','mine_elevator.fbx','renders/hero.png','renders/rear.png','build.py','capture_manifest.json'):
    p=os.path.join(ROOT,name);files[name]={'bytes':os.path.getsize(p),'sha256':sha(p)}
report={'asset':'mine_elevator','started_at_utc':begin,'finished_at_utc':utc(),'elapsed_seconds':time.time()-START,
 'blender_version':bpy.app.version_string,'checks':checks,'passed':all(checks.values()),'formats':results,'files':files,
 'topology_note':'Position-only weld at 1 micrometre used solely for seam-split topology validation, without changing delivered files.',
 'limitations':['Static visualization; not a certified lifting mechanism or an engineering load calculation.','Named solid PBR materials; no image textures, rig, animation, collision, or LODs.','Separate component UV islands; no shared baked texture atlas.']}
with open(os.path.join(ROOT,'validation.json'),'w',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps(checks,indent=2),flush=True)
print('PASS' if report['passed'] else 'FAIL',flush=True)
if not report['passed']:raise RuntimeError('Asset validation failed. See validation.json.')
