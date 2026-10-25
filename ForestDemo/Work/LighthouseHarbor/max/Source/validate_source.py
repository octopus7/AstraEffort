"""Artifact contract, run with Blender background after author_scene.py."""
import bpy, json, math
from pathlib import Path
ROOT=Path('D:/github/AstraEffort/ForestDemo/Work/LighthouseHarbor/max')
SOURCE=ROOT/'SourceArt'
assert (SOURCE/'harbor.blend').exists(), 'Original scene artifact is not authored yet'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'harbor.blend'))
objects=[o for o in bpy.data.objects if o.type=='MESH']
assert len(objects)>=20, f'Expected independently readable scene modules, got {len(objects)}'
required=['Cliff','Lighthouse','Keeper','Stairs','Pier','Boat','Fishing','Water']
for name in required:
    assert any(name.lower() in o.name.lower() for o in objects), f'Missing semantic group {name}'
issues=[]
records=[]
for o in objects:
    if not o.data.uv_layers: issues.append(o.name+': no UV')
    if not o.data.materials: issues.append(o.name+': no material')
    for p in o.data.polygons:
        if p.area<1e-10: issues.append(o.name+': degenerate face'); break
        if p.material_index>=len(o.data.materials): issues.append(o.name+': invalid material'); break
    pts=[o.matrix_world@v.co for v in o.data.vertices]
    low=[min(v[i] for v in pts) for i in range(3)]
    high=[max(v[i] for v in pts) for i in range(3)]
    if low[0]<-50.01 or low[1]<-50.01 or high[0]>50.01 or high[1]>50.01:
        issues.append(o.name+': outside 100x100m')
    assert (SOURCE/'FBX'/(o.name+'.fbx')).exists(), f'No exported FBX for {o.name}'
    records.append({'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'bounds_m':[low,high],
                    'uv_layers':len(o.data.uv_layers),'materials':[m.name if m else None for m in o.data.materials]})
assert not issues, '\n'.join(issues[:30])
result={'pass':True,'mesh_count':len(objects),'source_blend':str(SOURCE/'harbor.blend'),'meshes':records,
        'bounds_requirement':'x/y inside [-50,50] metres','uv_method':'dominant-plane projection; repeat UVs intentionally overlap',
        'normal_method':'outward procedural topology; bmesh recalc; bevel segments 2-3; weighted normals where appropriate'}
(ROOT/'Validation').mkdir(exist_ok=True)
(ROOT/'Validation'/'source_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('SOURCE_VALIDATION_PASS',len(objects),'meshes')
