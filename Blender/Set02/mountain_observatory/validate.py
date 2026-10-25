"""Independent saved-file/export reimport verification, run in a new Blender process."""
import bpy, bmesh, math, json, hashlib, time
from pathlib import Path
from datetime import datetime, timezone
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
NAME='mountain_observatory'
def utc(): return datetime.now(timezone.utc).isoformat()
begin=utc(); timer=time.perf_counter()

def measure(objects,label):
    deps=bpy.context.evaluated_depsgraph_get()
    total_tri=0; total_vert=0; finite=True; zero_geo=0; zero_uv=0
    uv_missing=[]; material_missing=[]; uv_outside=[]; failures=[]; details=[]
    lo=[math.inf]*3; hi=[-math.inf]*3
    for o in objects:
        if o.type!='MESH': continue
        ev=o.evaluated_get(deps); me=ev.to_mesh(); me.calc_loop_triangles()
        coords=[o.matrix_world@v.co for v in me.vertices]
        for co in coords:
            for a in range(3):
                finite=finite and math.isfinite(co[a]); lo[a]=min(lo[a],co[a]); hi[a]=max(hi[a],co[a])
        total_vert+=len(coords); total_tri+=len(me.loop_triangles)
        geo_bad=0; uv_bad=0
        if not me.uv_layers: uv_missing.append(o.name)
        uv=me.uv_layers.active.data if me.uv_layers else None
        if not len(me.materials): material_missing.append(o.name)
        elif any(p.material_index>=len(me.materials) or me.materials[p.material_index] is None for p in me.polygons): material_missing.append(o.name)
        for t in me.loop_triangles:
            a,b,c=[coords[i] for i in t.vertices]
            if (b-a).cross(c-a).length*.5<=1e-12: geo_bad+=1
            if uv:
                a,b,c=[uv[i].uv for i in t.loops]
                area=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5
                if area<=1e-14: uv_bad+=1
        if uv and any(p.uv.x<-.0001 or p.uv.y<-.0001 or p.uv.x>1.0001 or p.uv.y>1.0001 for p in uv): uv_outside.append(o.name)
        zero_geo+=geo_bad; zero_uv+=uv_bad
        bm=bmesh.new(); bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
        boundary=sum(e.is_boundary for e in bm.edges)
        nonmanifold=sum(not e.is_manifold for e in bm.edges)
        bm.free()
        if geo_bad or uv_bad or nonmanifold:
            details.append({'object':o.name,'zero_area_triangles':geo_bad,'degenerate_uv_triangles':uv_bad,'position_weld_boundary_edges':boundary,'position_weld_nonmanifold_edges':nonmanifold})
        ev.to_mesh_clear()
    missing_images=[]
    for im in bpy.data.images:
        if im.source=='FILE' and im.filepath and not im.packed_file:
            if not Path(bpy.path.abspath(im.filepath)).exists(): missing_images.append(im.filepath)
    non_asset=[o.name for o in objects if o.type in {'CAMERA','LIGHT'} or 'STUDIO' in o.name]
    ok=bool(total_tri and finite and not zero_geo and not zero_uv and not uv_missing and not material_missing and not missing_images and not non_asset)
    return {'label':label,'mesh_objects':sum(o.type=='MESH' for o in objects),'vertices':total_vert,'evaluated_triangles':total_tri,'bounds_min_m':lo,'bounds_max_m':hi,'dimensions_m':[hi[i]-lo[i] for i in range(3)],'finite_geometry':finite,'zero_area_triangles':zero_geo,'degenerate_uv_triangles':zero_uv,'missing_uv_objects':uv_missing,'uv_outside_unit_square_objects':uv_outside,'missing_material_objects':material_missing,'missing_external_images':missing_images,'studio_objects_in_asset_export':non_asset,'topology_exception_details':details,'metric_pass':ok}

bpy.ops.wm.open_mainfile(filepath=str(ROOT/(NAME+'.blend')))
native=measure(list(bpy.data.collections['ASSET'].all_objects),'Saved BLEND / ASSET')
assert all(o.type=='MESH' for o in bpy.data.collections['ASSET'].all_objects),'Non-mesh asset object'
native['asset_collection_present']=True
native['studio_collection_present']='STUDIO' in bpy.data.collections
native['unapplied_modifier_count']=sum(len(o.modifiers) for o in bpy.data.collections['ASSET'].all_objects)
native['render_resolution']=[bpy.context.scene.render.resolution_x,bpy.context.scene.render.resolution_y]
deps=bpy.context.evaluated_depsgraph_get()
axis=Vector((0,-.66,.751265)).normalized(); pivot=Vector((0,-.90,4.18))
hit,loc,normal,idx,obj,mat=bpy.context.scene.ray_cast(deps,pivot+axis*1.55,-axis,distance=1.2)
native['optical_axis_ray']={'hit':hit,'first_object':obj.name if obj else None,'hit_location_m':list(loc),'lens_visible_through_open_barrel':bool(hit and obj.name=='Telescope deeply inset coated lens')}
hit,loc,normal,idx,obj,mat=bpy.context.scene.ray_cast(deps,Vector((0,-3.5,5.45)),Vector((0,1,0)),distance=7.0)
native['open_slit_ray']={'origin_m':[0,-3.5,5.45],'direction':[0,1,0],'first_object':obj.name if obj else None,'hit_location_m':list(loc),'front_open_to_closed_rear_panel':bool(hit and obj.name=='Dome closed rear shutter panel' and loc.y>0)}
print('NATIVE',json.dumps(native),flush=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/(NAME+'.glb')))
glb=measure(list(bpy.context.scene.objects),'Fresh GLB import')
print('GLB',json.dumps(glb),flush=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/(NAME+'.fbx')))
fbx=measure(list(bpy.context.scene.objects),'Fresh FBX import')
print('FBX',json.dumps(fbx),flush=True)
cross={}
for label,item in [('glb',glb),('fbx',fbx)]:
    delta=max(abs(item[k][i]-native[k][i]) for k in ['bounds_min_m','bounds_max_m'] for i in range(3))
    cross[label]={'exact_triangle_match':item['evaluated_triangles']==native['evaluated_triangles'],'max_bounds_delta_m':delta,'bounds_match_within_0_1_mm':delta<.0001}
checks={
    'native_geometry_uv_material_pass':native['metric_pass'],
    'glb_geometry_uv_material_pass':glb['metric_pass'],
    'fbx_geometry_uv_material_pass':fbx['metric_pass'],
    'all_modifiers_baked':native['unapplied_modifier_count']==0,
    'exports_exact_triangle_consistency':all(v['exact_triangle_match'] for v in cross.values()),
    'exports_transformed_vertex_bounds_consistency':all(v['bounds_match_within_0_1_mm'] for v in cross.values()),
    'asset_bottom_z_is_zero':abs(native['bounds_min_m'][2])<.0001,
    'required_actual_renders_present':all((ROOT/'renders'/f'{v}.png').is_file() for v in ['hero','rear']),
    'optical_lens_visible_in_hollow_barrel':native['optical_axis_ray']['lens_visible_through_open_barrel'],
    'real_open_front_slit_closed_rear':native['open_slit_ray']['front_open_to_closed_rear_panel'],
    'native_closed_component_topology':all(v['position_weld_nonmanifold_edges']==0 for v in native['topology_exception_details']),
}
hashes={}
for rel in [NAME+'.blend',NAME+'.glb',NAME+'.fbx','renders/hero.png','renders/rear.png','build.py','capture_manifest.json']:
    p=ROOT/rel; hashes[rel]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
report={'asset':NAME,'validation_started_at_utc':begin,'validation_finished_at_utc':utc(),'validation_seconds':time.perf_counter()-timer,'blender_version':bpy.app.version_string,'method':'Separate Blender process; saved BLEND ASSET, then fresh empty-scene imports of GLB and FBX; true matrix_world transformed vertices, evaluated triangulation, area and UV area tests. Topology measured after position-only weld at 1 micrometer.','tolerances':{'geometry_triangle_area_m2':1e-12,'uv_triangle_area':1e-14,'bounds_m':.0001},'checks':checks,'passed':all(checks.values()),'native':native,'glb':glb,'fbx':fbx,'cross_format':cross,'stable_artifact_hashes':hashes,'limits':['Static production asset; no animations, collision, LODs or rig.','Independent component UV layouts and solid PBR colors; no generated or bitmap surface textures.','Intersecting assembled components are intentional; mesh topology checks are component-wise, not a boolean union of the building.']}
(ROOT/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('VALIDATION_PASS',report['passed'],json.dumps(checks),flush=True)
if not report['passed']: raise RuntimeError('Validation failed; see validation.json')
