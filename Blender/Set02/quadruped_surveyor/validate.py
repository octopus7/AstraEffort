import bpy, bmesh, os, json, math, hashlib, time
from mathutils import Vector
from datetime import datetime, timezone

ROOT=os.path.dirname(os.path.abspath(__file__))
SLUG='quadruped_surveyor'
T0=time.time()
START=datetime.now(timezone.utc).isoformat()

def stats(objects):
    meshes=[o for o in objects if o.type=='MESH']
    lo=[math.inf]*3; hi=[-math.inf]*3
    tris=verts=nonfinite=zero=uvzero=missing_uv=missing_mat=0
    boundary=nonmanifold=0; per=[]
    dg=bpy.context.evaluated_depsgraph_get()
    for obj in meshes:
        ev=obj.evaluated_get(dg); me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
        me.calc_loop_triangles(); verts+=len(me.vertices); tris+=len(me.loop_triangles)
        for v in me.vertices:
            p=ev.matrix_world@v.co
            if not all(math.isfinite(x) for x in p): nonfinite+=1
            for k in range(3): lo[k]=min(lo[k],p[k]); hi[k]=max(hi[k],p[k])
        uv=me.uv_layers.active
        if not uv: missing_uv+=len(me.loop_triangles)
        for tri in me.loop_triangles:
            a,b,c=[ev.matrix_world@me.vertices[i].co for i in tri.vertices]
            if (b-a).cross(c-a).length*.5<=1e-14: zero+=1
            if tri.material_index>=len(me.materials) or me.materials[tri.material_index] is None: missing_mat+=1
            if uv:
                a,b,c=[uv.data[i].uv for i in tri.loops]
                uvarea=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5
                if not math.isfinite(uvarea) or uvarea<=1e-14: uvzero+=1
        bm=bmesh.new(); bm.from_mesh(me)
        # glTF deliberately splits vertices at UV/normal seams: test closed geometry after position-only weld.
        bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6)
        obound=sum(e.is_boundary for e in bm.edges)
        onon=sum(not e.is_manifold for e in bm.edges)
        boundary+=obound; nonmanifold+=onon
        per.append({'name':obj.name,'triangles':len(me.loop_triangles),'vertices':len(me.vertices),'boundary_edges_after_position_weld':obound,'nonmanifold_edges_after_position_weld':onon})
        bm.free(); ev.to_mesh_clear()
    materials=sorted(set(m.name for o in meshes for m in o.data.materials if m))
    return {'mesh_objects':len(meshes),'vertices':verts,'evaluated_triangles':tris,'bounds_min_m':lo,'bounds_max_m':hi,'dimensions_xyz_m':[hi[i]-lo[i] for i in range(3)],'material_count':len(materials),'material_names':materials,'nonfinite_vertices':nonfinite,'zero_area_triangles':zero,'uv_degenerate_triangles':uvzero,'triangles_missing_uv':missing_uv,'triangles_missing_material':missing_mat,'boundary_edges_after_position_weld':boundary,'nonmanifold_edges_after_position_weld':nonmanifold,'object_types':sorted(set(o.type for o in objects)),'studio_objects':[o.name for o in objects if 'STUDIO' in o.name or o.type in {'CAMERA','LIGHT'}],'component_details':per}

report={'asset':SLUG,'validation_started_at_utc':START,'blender_version':bpy.app.version_string,'checks':{},'formats':{},'limits':['Static assembly; no rig, animation, collision or LODs.','Solid PBR material groups; no image textures or material wear maps.','Component UVs are individually packed; not a single shared texture atlas.','Mechanical covers and seals intentionally overlap in assembled joints. This is a visualization asset, not a manufacturing CAD assembly.']}
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,SLUG+'.blend'))
native=bpy.data.collections.get('ASSET')
assert native is not None,'Missing ASSET collection'
source=stats(list(native.all_objects)); report['formats']['blend']=source
report['checks']['four_legs']=all(any(o.name.startswith(t+' hip structural hub') for o in native.objects) for t in ['L_Front','L_Rear','R_Front','R_Rear'])
feet=[o.name for o in native.objects if 'circular rubber footpad' in o.name]
report['checks']['four_separate_round_pads']=len(feet)==4
report['footpad_objects']=feet
report['checks']['native_asset_only_meshes']=source['object_types']==['MESH']
report['checks']['floor_at_z_zero']=abs(source['bounds_min_m'][2])<1e-6
report['checks']['modifiers_baked']=all(len(o.modifiers)==0 for o in native.objects)
report['external_images']=[{'name':im.name,'filepath':im.filepath,'packed':bool(im.packed_file)} for im in bpy.data.images if im.source=='FILE']
report['checks']['no_missing_external_images']=all(im.packed_file or os.path.isfile(bpy.path.abspath(im.filepath)) for im in bpy.data.images if im.source=='FILE')
for fmt in ['glb','fbx']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    path=os.path.join(ROOT,SLUG+'.'+fmt)
    if fmt=='glb': bpy.ops.import_scene.gltf(filepath=path)
    else: bpy.ops.import_scene.fbx(filepath=path)
    current=stats(list(bpy.context.scene.objects)); report['formats'][fmt]=current
    report['checks'][fmt+'_exact_triangle_consistency']=current['evaluated_triangles']==source['evaluated_triangles']
    report['checks'][fmt+'_bounds_match']=max(abs(current[key][i]-source[key][i]) for key in ['bounds_min_m','bounds_max_m'] for i in range(3))<1e-5
    report['checks'][fmt+'_mesh_count_match']=current['mesh_objects']==source['mesh_objects']
    report['checks'][fmt+'_no_studio']=not current['studio_objects'] and current['object_types']==['MESH']
for fmt,result in report['formats'].items():
    for key in ['nonfinite_vertices','zero_area_triangles','uv_degenerate_triangles','triangles_missing_uv','triangles_missing_material','boundary_edges_after_position_weld','nonmanifold_edges_after_position_weld']:
        report['checks'][fmt+'_'+key+'_zero']=result[key]==0
    report['checks'][fmt+'_nonempty']=result['mesh_objects']>0 and result['evaluated_triangles']>0
report['files']={}
for file in [SLUG+'.blend',SLUG+'.glb',SLUG+'.fbx','build.py','renders/hero.png','renders/rear.png','capture_manifest.json']:
    p=os.path.join(ROOT,file)
    report['files'][file]={'bytes':os.path.getsize(p),'sha256':hashlib.sha256(open(p,'rb').read()).hexdigest()}
report['passed']=all(report['checks'].values())
report['failed_checks']=[k for k,v in report['checks'].items() if not v]
report['validation_finished_at_utc']=datetime.now(timezone.utc).isoformat()
report['validation_elapsed_seconds']=round(time.time()-T0,3)
with open(os.path.join(ROOT,'validation.json'),'w',encoding='utf8') as f: json.dump(report,f,indent=2)
print(json.dumps({'passed':report['passed'],'failed_checks':report['failed_checks'],'mesh_objects':source['mesh_objects'],'triangles':source['evaluated_triangles'],'bounds':source['dimensions_xyz_m'],'elapsed_seconds':report['validation_elapsed_seconds']},indent=2),flush=True)
if not report['passed']: raise RuntimeError('Validation failed: '+', '.join(report['failed_checks']))
