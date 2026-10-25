"""Reopen the native file and inspect each exported file in a fresh scene."""
import bpy
import bmesh
import json
import math
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
report={'asset':'arched_workshop','validated_at_utc':datetime.now(timezone.utc).isoformat(),
        'blender_version':bpy.app.version_string,'geometry_area_epsilon_m2':1e-14,
        'checks':{},'formats':{},'limitations':['Solid named PBR materials; no painted or baked texture maps.','Static architecture; shutter and doors are separate editable geometry but are not rigged.']}

def inspect(label,objects):
    objects=list(objects)
    meshes=[o for o in objects if o.type=='MESH']
    lo=Vector((float('inf'),)*3)
    hi=Vector((float('-inf'),)*3)
    tris=verts=uvloops=0
    zero=[]
    nonfinite=[]
    missinguv=[]
    missingmat=[]
    degenerate_uv=[]
    materialnames=set()
    nonmanifold=0
    welded_nonmanifold=0
    invalid_normals=[]
    for obj in meshes:
        me=obj.data
        me.calc_loop_triangles()
        verts+=len(me.vertices)
        tris+=len(me.loop_triangles)
        for v in me.vertices:
            world=obj.matrix_world@v.co
            if not all(math.isfinite(c) for c in world):
                nonfinite.append(obj.name)
            for i in range(3):
                lo[i]=min(lo[i],world[i])
                hi[i]=max(hi[i],world[i])
        uv=me.uv_layers.active
        if not uv or len(uv.data)!=len(me.loops):
            missinguv.append(obj.name)
        else:
            uvloops+=len(uv.data)
            if not all(math.isfinite(c) for item in uv.data for c in item.uv):
                nonfinite.append(obj.name+' UV')
        for p in me.polygons:
            if p.material_index>=len(me.materials) or me.materials[p.material_index] is None:
                missingmat.append(obj.name)
        materialnames.update(m.name for m in me.materials if m)
        if any(not all(math.isfinite(c) for c in item.vector) or item.vector.length<.9 for item in me.corner_normals):
            invalid_normals.append(obj.name)
        objzero=0
        objuvzero=0
        for tri in me.loop_triangles:
            a,b,c=[obj.matrix_world@me.vertices[v].co for v in tri.vertices]
            area=(b-a).cross(c-a).length*.5
            if area<=1e-14:
                objzero+=1
            if uv:
                a,b,c=[uv.data[i].uv for i in tri.loops]
                uarea=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5
                if uarea<=1e-15:
                    objuvzero+=1
        if objzero:
            zero.append({'object':obj.name,'triangles':objzero})
        if objuvzero:
            degenerate_uv.append({'object':obj.name,'triangles':objuvzero})
        bm=bmesh.new()
        bm.from_mesh(me)
        nonmanifold+=sum(1 for e in bm.edges if not e.is_manifold)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
        welded_nonmanifold+=sum(1 for e in bm.edges if not e.is_manifold)
        bm.free()
    images=[]
    for image in bpy.data.images:
        if image.source=='FILE' and not image.packed_file:
            p=Path(bpy.path.abspath(image.filepath))
            images.append({'name':image.name,'path':str(p),'exists':p.is_file()})
    findings={
        'objects':len(objects),'mesh_objects':len(meshes),'vertices':verts,'evaluated_triangles':tris,
        'bounds_min_m':list(lo),'bounds_max_m':list(hi),'dimensions_m':list(hi-lo),
        'material_count':len(materialnames),'material_names':sorted(materialnames),
        'uv_mesh_coverage':(len(meshes)-len(missinguv))/max(1,len(meshes)),
        'uv_loop_count':uvloops,'missing_uv':missinguv,'missing_materials':sorted(set(missingmat)),
        'nonfinite_geometry_or_uv':sorted(set(nonfinite)),
        'zero_area_triangle_count':sum(x['triangles'] for x in zero),'zero_area_triangle_objects':zero,
        'zero_area_uv_triangle_count':sum(x['triangles'] for x in degenerate_uv),'zero_area_uv_triangle_objects':degenerate_uv,
        'nonmanifold_edge_count':nonmanifold,
        'nonmanifold_after_position_weld_1e_minus_6_m':welded_nonmanifold,
        'invalid_corner_normal_objects':invalid_normals,
        'unapplied_modifier_count':sum(len(o.modifiers) for o in meshes),
        'camera_count':sum(o.type=='CAMERA' for o in objects),
        'light_count':sum(o.type=='LIGHT' for o in objects),
        'studio_named_objects':[o.name for o in objects if o.name.startswith('STUDIO')],
        'external_images':images,
    }
    findings['pass']=bool(meshes) and tris>0 and not zero and not missinguv and not missingmat and not nonfinite and not invalid_normals and all(i['exists'] for i in images)
    if label!='blend':
        findings['pass']=findings['pass'] and findings['camera_count']==0 and findings['light_count']==0 and not findings['studio_named_objects']
    report['formats'][label]=findings
    print('VALIDATED',label,'meshes',len(meshes),'triangles',tris,'zero_area',findings['zero_area_triangle_count'],'uv_coverage',findings['uv_mesh_coverage'],'pass',findings['pass'],flush=True)

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'arched_workshop.blend'))
asset=bpy.data.collections['ASSET']
inspect('blend',asset.all_objects)
report['checks']['native_reopened_in_fresh_process']=True
report['checks']['meters']=bpy.context.scene.unit_settings.system=='METRIC' and bpy.context.scene.unit_settings.scale_length==1
report['checks']['floor_min_z_zero']=abs(report['formats']['blend']['bounds_min_m'][2])<1e-5
deps=bpy.context.evaluated_depsgraph_get()
hit,location,normal,index,obj,matrix=bpy.context.scene.ray_cast(deps,Vector((-.275,-4,.85)),Vector((0,1,0)),distance=10)
report['checks']['garage_opening_lower_ray']={'hit':hit,'first_hit_object':obj.name if obj else None,'first_hit_y':location.y if hit else None,'clear_through_front_wall':bool(hit and location.y>-2.1)}
hit,location,normal,index,obj,matrix=bpy.context.scene.ray_cast(deps,Vector((-.275,-4,2.15)),Vector((0,1,0)),distance=10)
report['checks']['garage_shutter_upper_ray']={'hit':hit,'first_hit_object':obj.name if obj else None,'first_hit_y':location.y if hit else None,'hits_raised_shutter':bool(hit and obj and obj.name.startswith('Shutter'))}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'arched_workshop.glb'))
inspect('glb',bpy.context.scene.objects)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'arched_workshop.fbx'))
inspect('fbx',bpy.context.scene.objects)

native=report['formats']['blend']
report['checks']['matching_export_triangle_counts']=all(x['evaluated_triangles']==native['evaluated_triangles'] for x in report['formats'].values())
report['checks']['matching_export_dimensions']=all(max(abs(a-b) for a,b in zip(x['dimensions_m'],native['dimensions_m']))<1e-4 for x in report['formats'].values())
report['files']={name:{'bytes':ROOT.joinpath(name).stat().st_size,'sha256':hashlib.sha256(ROOT.joinpath(name).read_bytes()).hexdigest()} for name in ['arched_workshop.blend','arched_workshop.glb','arched_workshop.fbx','build.py','finish_lighting.py','renders/hero.png','renders/rear.png','renders/front_detail.png'] if ROOT.joinpath(name).exists()}
report['passed']=all(v['pass'] for v in report['formats'].values()) and report['checks']['meters'] and report['checks']['floor_min_z_zero'] and report['checks']['matching_export_dimensions'] and report['checks']['matching_export_triangle_counts'] and report['checks']['garage_opening_lower_ray']['clear_through_front_wall'] and report['checks']['garage_shutter_upper_ray']['hits_raised_shutter']
ROOT.joinpath('validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('VALIDATION_FINISHED',report['passed'],flush=True)
