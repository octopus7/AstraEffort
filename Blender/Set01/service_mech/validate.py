"""Fresh-process validation of the saved blend and both round-trip exports."""
import bpy
import json
import math
import struct
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
START=datetime.now(timezone.utc).isoformat()
T0=time.time()

def inspect(objects):
    bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get()
    result={'mesh_objects':0,'vertices':0,'evaluated_triangles':0,'material_names':set(),
      'missing_uv':[],'invalid_uv':[],'missing_material':[],'nonfinite_geometry':[],
      'empty_meshes':[],'remaining_modifiers':[],'degenerate_triangles':0,
      'degenerate_uv_triangles':0,'uv_triangles':0,'non_mesh_objects':[],
      'mesh_names':[],'min':[float('inf')]*3,'max':[-float('inf')]*3}
    for ob in objects:
        if ob.type!='MESH':
            result['non_mesh_objects'].append({'name':ob.name,'type':ob.type});continue
        result['mesh_objects']+=1
        result['mesh_names'].append(ob.name)
        if ob.modifiers:result['remaining_modifiers'].append(ob.name)
        ev=ob.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles()
        result['vertices']+=len(me.vertices)
        result['evaluated_triangles']+=len(me.loop_triangles)
        if not me.vertices or not me.polygons:result['empty_meshes'].append(ob.name)
        if not me.materials or any(p.material_index>=len(me.materials) or me.materials[p.material_index] is None for p in me.polygons):
            result['missing_material'].append(ob.name)
        for mat in me.materials:
            if mat:result['material_names'].add(mat.name)
        for v in me.vertices:
            co=ob.matrix_world@v.co
            if any(not math.isfinite(n) for n in co):result['nonfinite_geometry'].append(ob.name)
            for k in range(3):
                result['min'][k]=min(result['min'][k],co[k]);result['max'][k]=max(result['max'][k],co[k])
        uv=me.uv_layers.active
        if not uv or len(uv.data)!=len(me.loops):
            result['missing_uv'].append(ob.name)
        else:
            if any(not math.isfinite(n) for d in uv.data for n in d.uv):result['invalid_uv'].append(ob.name)
            for tri in me.loop_triangles:
                a,b,c=[uv.data[i].uv for i in tri.loops]
                area=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5
                if area<1e-12:result['degenerate_uv_triangles']+=1
                result['uv_triangles']+=1
        for tri in me.loop_triangles:
            a,b,c=[ob.matrix_world@me.vertices[i].co for i in tri.vertices]
            if (b-a).cross(c-a).length*.5<1e-12:result['degenerate_triangles']+=1
        ev.to_mesh_clear()
    result['dimensions_m']=[result['max'][i]-result['min'][i] for i in range(3)]
    result['material_names']=sorted(result['material_names'])
    result['uv_coverage_percent']=100*(result['mesh_objects']-len(result['missing_uv']))/max(1,result['mesh_objects'])
    result['nondegenerate_uv_triangle_percent']=100*(result['uv_triangles']-result['degenerate_uv_triangles'])/max(1,result['uv_triangles'])
    result['geometry_only']=not result['non_mesh_objects']
    result['passed']=all(not result[k] for k in ['missing_uv','invalid_uv','missing_material','nonfinite_geometry','empty_meshes','remaining_modifiers','non_mesh_objects']) and result['mesh_objects']>0 and result['evaluated_triangles']>0 and result['degenerate_triangles']==0 and result['nondegenerate_uv_triangle_percent']>99.5
    return result

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'service_mech.blend'))
coll=bpy.data.collections.get('ASSET')
blend=inspect(list(coll.all_objects))
blend['source_collection']='ASSET'
blend['studio_collection_present']=bpy.data.collections.get('STUDIO') is not None
blend['units']=bpy.context.scene.unit_settings.system
blend['unit_scale_length']=bpy.context.scene.unit_settings.scale_length
blend['front_axis']=bpy.context.scene.get('front_axis')
blend['missing_external_images']=[]
for im in bpy.data.images:
    if im.source=='FILE' and im.filepath and not im.packed_file:
        if not Path(bpy.path.abspath(im.filepath)).exists():blend['missing_external_images'].append(im.filepath)
blend['passed']=blend['passed'] and not blend['missing_external_images'] and abs(blend['min'][2])<1e-5 and abs(blend['dimensions_m'][2]-2.8)<1e-4
materials=blend['material_names']

with (ROOT/'service_mech.glb').open('rb') as f:
    raw=f.read()
magic,version,size=struct.unpack('<4sII',raw[:12])
chunk_size,chunk_type=struct.unpack('<II',raw[12:20])
gltf=json.loads(raw[20:20+chunk_size].decode('utf-8'))
gltf_meta={'magic':magic.decode(),'version':version,'declared_size_matches':size==len(raw),
 'mesh_count':len(gltf.get('meshes',[])),'has_cameras':bool(gltf.get('cameras')),
 'has_animations':bool(gltf.get('animations')),'external_uris':[],
 'primitives_missing_uv':[],'primitives_missing_normals':[]}
for group in ['buffers','images']:
    for entry in gltf.get(group,[]):
        if entry.get('uri') and not entry['uri'].startswith('data:'):gltf_meta['external_uris'].append(entry['uri'])
for mi,mesh in enumerate(gltf.get('meshes',[])):
    for pi,p in enumerate(mesh.get('primitives',[])):
        if 'TEXCOORD_0' not in p.get('attributes',{}):gltf_meta['primitives_missing_uv'].append([mi,pi])
        if 'NORMAL' not in p.get('attributes',{}):gltf_meta['primitives_missing_normals'].append([mi,pi])

imports={}
for ext in ['glb','fbx']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if ext=='glb':bpy.ops.import_scene.gltf(filepath=str(ROOT/'service_mech.glb'))
    else:bpy.ops.import_scene.fbx(filepath=str(ROOT/'service_mech.fbx'))
    data=inspect(list(bpy.context.scene.objects))
    data['dimensions_match_blend']=all(abs(data['dimensions_m'][i]-blend['dimensions_m'][i])<1e-4 for i in range(3))
    data['triangle_count_matches_blend']=data['evaluated_triangles']==blend['evaluated_triangles']
    data['studio_names_present']=[o.name for o in bpy.context.scene.objects if any(t in o.name.lower() for t in ['studio','camera','key','fill','edgebox'])]
    data['passed']=data['passed'] and data['dimensions_match_blend'] and data['triangle_count_matches_blend'] and not data['studio_names_present']
    imports[ext]=data

files={}
for name in ['service_mech.blend','service_mech.glb','service_mech.fbx','renders/hero.png','renders/rear.png','build.py']:
    path=ROOT/name
    files[name]={'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

passed=blend['passed'] and all(v['passed'] for v in imports.values()) and not gltf_meta['has_cameras'] and not gltf_meta['has_animations'] and not gltf_meta['external_uris'] and not gltf_meta['primitives_missing_uv'] and not gltf_meta['primitives_missing_normals']
report={'status':'passed' if passed else 'needs_attention','started_at_utc':START,
 'finished_at_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.time()-T0,
 'blender_version':bpy.app.version_string,'blend':blend,'glb_structure':gltf_meta,
 'round_trip_imports':imports,'files':files,
 'limitations':['Static asset; no armature or animation.','Solid PBR materials; no painted wear texture maps.',
 'UVs are independently packed per component; no single globally packed texture atlas is claimed.']}
(ROOT/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('SERVICE_MECH_VALIDATION',json.dumps({'status':report['status'],'mesh_objects':blend['mesh_objects'],
 'triangles':blend['evaluated_triangles'],'dimensions_m':blend['dimensions_m'],
 'uv_coverage_percent':blend['uv_coverage_percent'],'nondegenerate_uv_triangle_percent':blend['nondegenerate_uv_triangle_percent'],
 'degenerate_triangles':blend['degenerate_triangles'],'glb_passed':imports['glb']['passed'],'fbx_passed':imports['fbx']['passed']}),flush=True)
if not passed:raise SystemExit(1)
