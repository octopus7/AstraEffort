"""Read actual exported FBX through Blender, checking transforms and surface orientation."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
result={'at_utc':datetime.now(timezone.utc).isoformat(),'passed':True,'checks':[],'failures':[]}
source=json.loads((ROOT/'Source/scene_manifest.json').read_text(encoding='utf-8'))
for name in ['SM_Terrain','SM_Paths','SM_Stones','SM_Orchard','SM_WindmillRotor']:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(ROOT/'Source/Models'/(name+'.fbx')))
    ob=next(o for o in bpy.context.scene.objects if o.type=='MESH');mesh=ob.data
    vs=[ob.matrix_world@v.co for v in mesh.vertices]
    bounds_min=[min(v[i] for v in vs) for i in range(3)];bounds_max=[max(v[i] for v in vs) for i in range(3)]
    check={'mesh':name,'imported_world_dimensions_m':[b-a for a,b in zip(bounds_min,bounds_max)]}
    mesh.calc_loop_triangles()
    if name=='SM_WindmillRotor':
        # Full-revolution sweep: only vertices reaching gallery height need deck clearance.
        pivot=source['rotor_pivot_m'];gallery_radius=5.2;gallery_top=5.5
        candidates=[v for v in vs if (v.x*v.x+v.z*v.z)**.5>=pivot[2]-gallery_top]
        clearance=min(abs(pivot[1]+v.y-17.0)-gallery_radius for v in candidates)
        check['full_revolution_gallery_clearance_m']=clearance
        check['minimum_sweep_z_m']=pivot[2]-max((v.x*v.x+v.z*v.z)**.5 for v in vs)
        if clearance<.25:result['failures'].append('Rotor swept blades do not clear the gallery with 0.25m margin')
    if name=='SM_Terrain':
        if any(abs(check['imported_world_dimensions_m'][i]-100)>.05 for i in [0,1]):result['failures'].append('Terrain FBX transform does not span 100x100 meters')
    if name=='SM_Paths':
        normals=[(vs[t.vertices[1]]-vs[t.vertices[0]]).cross(vs[t.vertices[2]]-vs[t.vertices[0]]).normalized().z for t in mesh.loop_triangles]
        check['up_triangles']=sum(n>.5 for n in normals);check['down_triangles']=sum(n<-.5 for n in normals)
        if check['down_triangles'] or not check['up_triangles']:result['failures'].append('Path FBX has reversed top-surface faces')
    if name in ['SM_Stones','SM_Orchard']:
        # Signed closed-surface volume catches inward primitives even when two-sided rendering masks them.
        parents=list(range(len(vs)))
        def root(v):
            while parents[v]!=v:parents[v]=parents[parents[v]];v=parents[v]
            return v
        for edge in mesh.edges:
            a,b=edge.vertices;parents[root(a)]=root(b)
        volumes={}
        for tri in mesh.loop_triangles:
            a,b,c=tri.vertices;k=root(a);volumes[k]=volumes.get(k,0)+vs[a].dot(vs[b].cross(vs[c]))/6
        negative=[v for v in volumes.values() if v<-.0001]
        check['component_count']=len(volumes);check['negative_volume_components']=len(negative);check['signed_volume_sum']=sum(volumes.values())
        if negative:result['failures'].append(name+' has inward closed primitive faces')
    result['checks'].append(check)
result['passed']=not result['failures']
(ROOT/'Evidence/fbx_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2),flush=True)
if not result['passed']:sys.exit(1)
