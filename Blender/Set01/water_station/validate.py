"""Fresh-process delivery validation; reopen .blend and import both exports."""
import bpy
import math
import json
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
started=datetime.now(timezone.utc).isoformat()


def inspect(label, objects):
    meshes=[o for o in objects if o.type=='MESH']
    lo=[float('inf')]*3; hi=[float('-inf')]*3
    result={'label':label,'object_count':len(objects),'mesh_count':len(meshes),'non_mesh_objects':[o.name for o in objects if o.type!='MESH'],
            'vertices':0,'triangles':0,'materials':set(),'missing_uv':[],'missing_materials':[], 'nonfinite_geometry':[],
            'nonfinite_uv':[],'nonfinite_normals':[],'degenerate_triangles':0,'degenerate_triangle_objects':{},'degenerate_uv_triangles':0,
            'degenerate_uv_objects':{},'uv_out_of_range':[],'negative_scale_objects':[],'remaining_modifiers':[],
            'object_details':[]}
    for o in meshes:
        data=o.data
        data.calc_loop_triangles()
        result['vertices']+=len(data.vertices)
        result['triangles']+=len(data.loop_triangles)
        if o.scale.x*o.scale.y*o.scale.z<0: result['negative_scale_objects'].append(o.name)
        if o.modifiers: result['remaining_modifiers'].append(o.name)
        if not data.materials or any(p.material_index>=len(data.materials) or data.materials[p.material_index] is None for p in data.polygons):
            result['missing_materials'].append(o.name)
        result['materials'].update(m.name for m in data.materials if m)
        for v in data.vertices:
            p=o.matrix_world@v.co
            if not all(math.isfinite(x) for x in p): result['nonfinite_geometry'].append(o.name)
            if not all(math.isfinite(x) for x in v.normal): result['nonfinite_normals'].append(o.name)
            for i in range(3): lo[i]=min(lo[i],p[i]); hi[i]=max(hi[i],p[i])
        deg=0; uvdeg=0
        uv=data.uv_layers.active
        if uv is None or len(uv.data)!=len(data.loops): result['missing_uv'].append(o.name)
        else:
            for x in uv.data:
                if not all(math.isfinite(v) for v in x.uv): result['nonfinite_uv'].append(o.name)
                if any(v<-.0001 or v>1.0001 for v in x.uv): result['uv_out_of_range'].append(o.name); break
        for tri in data.loop_triangles:
            a,b,c=[o.matrix_world@data.vertices[i].co for i in tri.vertices]
            area=.5*(b-a).cross(c-a).length
            if area<=1e-12: deg+=1
            if uv:
                a,b,c=[uv.data[i].uv for i in tri.loops]
                area2=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5
                if area2<=1e-14: uvdeg+=1
        result['degenerate_triangles']+=deg
        result['degenerate_uv_triangles']+=uvdeg
        if deg: result['degenerate_triangle_objects'][o.name]=deg
        if uvdeg: result['degenerate_uv_objects'][o.name]=uvdeg
        result['object_details'].append({'name':o.name,'vertices':len(data.vertices),'triangles':len(data.loop_triangles),
            'uv_layers':len(data.uv_layers),'material_slots':len(data.materials),'degenerate_triangles':deg,'degenerate_uv_triangles':uvdeg})
    result['materials']=sorted(result['materials'])
    result['material_count']=len(result['materials'])
    result['bounds_min_m']=lo
    result['bounds_max_m']=hi
    result['dimensions_m']=[hi[i]-lo[i] for i in range(3)]
    result['missing_external_images']=[im.filepath for im in bpy.data.images if im.source=='FILE' and im.filepath and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()]
    result['image_texture_count']=sum(1 for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE')
    result['pass']=bool(meshes) and result['triangles']>0 and not any(result[k] for k in ['non_mesh_objects','missing_uv','missing_materials','nonfinite_geometry','nonfinite_normals','nonfinite_uv','degenerate_triangles','degenerate_uv_triangles','missing_external_images','negative_scale_objects','uv_out_of_range'])
    print('VALIDATED',label,'pass=',result['pass'],'meshes=',len(meshes),'tris=',result['triangles'],'deg=',result['degenerate_triangles'],'uvdeg=',result['degenerate_uv_triangles'],flush=True)
    return result


bpy.ops.wm.open_mainfile(filepath=str(ROOT/'water_station.blend'))
source=inspect('reopened_blend_ASSET',list(bpy.data.collections['ASSET'].all_objects))
source['primary_tank_count']=sum(1 for o in bpy.data.collections['ASSET'].objects if o.get('component_role')=='primary_tank')
source['primary_tanks']=[{'name':o.name,'radius_m':o['tank_radius_m'],'body_height_m':o['tank_body_height_m']} for o in bpy.data.collections['ASSET'].objects if o.get('component_role')=='primary_tank']
source['stair_tread_count']=sum(1 for o in bpy.data.collections['ASSET'].objects if o.name.startswith('Stair | step '))
source['studio_collection_separate']='STUDIO' in bpy.data.collections and not any(o.name.startswith('Studio ') for o in bpy.data.collections['ASSET'].objects)
source['unit_system']=bpy.context.scene.unit_settings.system
source['unit_scale']=bpy.context.scene.unit_settings.scale_length
source['pass']=source['pass'] and source['primary_tank_count']==2 and source['stair_tread_count']==5 and source['studio_collection_separate'] and abs(source['bounds_min_m'][2])<1e-5

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'water_station.glb'))
glb=inspect('reimported_GLB',list(bpy.context.scene.objects))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'water_station.fbx'),use_custom_normals=True)
fbx=inspect('reimported_FBX',list(bpy.context.scene.objects))
for r in [glb,fbx]:
    r['dimension_difference_vs_blend_m']=[abs(r['dimensions_m'][i]-source['dimensions_m'][i]) for i in range(3)]
    r['pass']=r['pass'] and max(r['dimension_difference_vs_blend_m'])<.001 and r['mesh_count']==source['mesh_count'] and r['triangles']==source['triangles'] and abs(r['bounds_min_m'][2])<1e-5

files={}
for rel in ['water_station.blend','water_station.glb','water_station.fbx','build.py','renders/hero.png','renders/rear.png']:
    p=ROOT/rel
    files[rel]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
report={'started_at_utc':started,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'blender_version':bpy.app.version_string,
        'overall_pass':source['pass'] and glb['pass'] and fbx['pass'],'source':source,'glb':glb,'fbx':fbx,'files':files,
        'axis_note':'Blend/FBX authored in meters, Z up, front -Y. GLB uses native glTF Y-up convention; Blender roundtrip restores identical Z-up bounds.',
        'scope':'Geometry only exports, no studio objects, cameras, lights, animation or rig. Named solid PBR materials; independent per-component UV islands.'}
(ROOT/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('VALIDATION_OVERALL_PASS',report['overall_pass'],flush=True)
if not report['overall_pass']:
    raise RuntimeError('Delivery checks failed; inspect validation.json before delivery')
