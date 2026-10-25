import bpy,bmesh,json,math
from pathlib import Path
ROOT=Path('D:/github/AstraEffort/ForestDemo/Work/LighthouseHarbor/max');ART=ROOT/'SourceArt'
bpy.ops.wm.open_mainfile(filepath=str(ART/'harbor.blend'))
report=[]
for o in list(bpy.data.objects):
    if o.type!='MESH':continue
    bad=[p for p in o.data.polygons if p.area<1e-10]
    if not bad:continue
    record={'mesh':o.name,'zero_area_faces_before':len(bad),'example_coordinates':[[list(o.data.vertices[i].co) for i in p.vertices] for p in bad[:2]]}
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges))
    deg=[f for f in bm.faces if f.calc_area()<1e-10]
    if deg:bmesh.ops.delete(bm,geom=deg,context='FACES_ONLY')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
    # Font bevel tessellation can round a near-collinear n-gon to zero in MeshPolygon.area
    # while bmesh reports a tiny positive area. Remove by the same delivered-mesh metric.
    for _ in range(3):
        bad_indices=[p.index for p in o.data.polygons if p.area<1e-10]
        if not bad_indices:break
        bm=bmesh.new();bm.from_mesh(o.data);bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm,geom=[bm.faces[i] for i in bad_indices],context='FACES_ONLY')
        bm.to_mesh(o.data);bm.free();o.data.update()
    record['zero_area_faces_after']=sum(p.area<1e-10 for p in o.data.polygons);assert not record['zero_area_faces_after'],o.name
    report.append(record)
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.export_scene.fbx(filepath=str(ART/'FBX'/(o.name+'.fbx')),use_selection=True,apply_unit_scale=True,global_scale=1,
      axis_forward='-Y',axis_up='Z',mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,object_types={'MESH'},path_mode='STRIP')
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'harbor.blend'))
(ROOT/'Validation'/'degenerate_cleanup.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
manifest=json.loads((ART/'mesh_manifest.json').read_text())
for m in manifest['meshes']:
    ob=bpy.data.objects[m['name']];m['vertices']=len(ob.data.vertices);m['polygons']=len(ob.data.polygons)
(ART/'mesh_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
roundtrip=[]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for m in manifest['meshes']:
    bpy.ops.import_scene.fbx(filepath=str(ART/'FBX'/(m['name']+'.fbx')),use_custom_normals=True)
    objs=[o for o in bpy.context.selected_objects if o.type=='MESH'];assert len(objs)==1
    o=objs[0];pts=[o.matrix_world@v.co for v in o.data.vertices]
    bounds=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
    err=max(abs(bounds[j][i]-m['bounds_m'][j][i]) for j in range(2) for i in range(3));assert err<.001,(m['name'],err)
    normals=[p.normal.length for p in o.data.polygons];assert min(normals)>.99,(m['name'],min(normals))
    roundtrip.append({'mesh':m['name'],'bounds_max_error_m':err,'normal_length_min':min(normals),'uv_layers':len(o.data.uv_layers)})
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
(ROOT/'Validation'/'fbx_roundtrip.json').write_text(json.dumps({'pass':True,'meshes':roundtrip,'removed_zero_area_faces':sum(r['zero_area_faces_before'] for r in report)},indent=2),encoding='utf-8')
print('FBX_ROUNDTRIP_PASS',len(roundtrip))
