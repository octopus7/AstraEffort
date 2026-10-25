import os,json,hashlib
from datetime import datetime, timezone, timedelta

ROOT=os.path.dirname(os.path.abspath(__file__))
def read(name):
    with open(os.path.join(ROOT,name),encoding='utf8') as f: return json.load(f)
v=read('validation.json'); b=read('build_run.json'); cap=read('capture_manifest.json')
assert v['passed'] and not v['failed_checks']
for name,record in v['files'].items():
    digest=hashlib.sha256(open(os.path.join(ROOT,name),'rb').read()).hexdigest()
    assert digest==record['sha256'], 'Post-validation change: '+name
start=datetime.fromisoformat(b['started_at_utc'].replace('Z','+00:00'))
end=datetime.now(timezone.utc); kst=timezone(timedelta(hours=9)); elapsed=(end-start).total_seconds()
s=v['formats']['blend']; d=s['dimensions_xyz_m']
text=f'''# Quadruped Surveyor — ready for review

Finished static terrain survey robot, based only on `REF/Set02/quadruped_surveyor.png`. Four connected articulated legs, four separate round ground-contact pads, rounded ivory/sage shell and graphite underbelly, rotary hips, knee and ankle joints, rotating lidar housing, a single optical telescope inside a two-sided gimbal, rear power pack, service panels and cable runs.

## Deliverables

- `quadruped_surveyor.blend`, `quadruped_surveyor.glb`, `quadruped_surveyor.fbx`
- `build.py` reproducible private Blender source; `validate.py` independent reimport checks
- Actual Cycles renders: `renders/hero.png`, `renders/rear.png`
- `capture_manifest.json`, `validation.json`, `build_run.json`, `build.log`, `validation.log`

## Timing

| Measurement | Actual value |
|---|---|
| Work start UTC | {start.isoformat()} |
| Work start KST | {start.astimezone(kst).isoformat()} |
| Record completion UTC | {end.isoformat()} |
| Record completion KST | {end.astimezone(kst).isoformat()} |
| Total elapsed wall time | {elapsed:.3f} seconds |
| Final build/export/two-render process | {b['build_script_elapsed_seconds']:.3f} seconds |
| Final independent validation | {v['validation_elapsed_seconds']:.3f} seconds |

Total wall time includes source authoring, three visual build iterations, image inspection and validation. The initial consistency check overlapped the second build's final save and correctly rejected mixed file versions; repeating it after process completion passed. The final delivered set was rebuilt and validated again sequentially.

## Verified geometry

- {s['mesh_objects']} named editable mesh parts; **{s['evaluated_triangles']:,} triangles**, exactly equal in saved BLEND, freshly imported GLB and freshly imported FBX.
- True transformed-vertex dimensions: **X {d[0]:.6f} × Y {d[1]:.6f} × Z {d[2]:.6f} m**. Front is -Y; Z is up; minimum Z is {s['bounds_min_m'][2]:.9f} m.
- {s['material_count']} named asset PBR materials. All triangle faces have a material and component UVs. All modifiers baked; real bevelled/rounded geometry.
- Zero nonfinite vertices, zero-area geometric triangles, degenerate UV triangles, missing UV/material coverage, or missing external images in all three formats.
- Zero boundary/nonmanifold edges after position-only seam welding in every format. GLB seams deliberately split vertices; vertex count is not used for triangle equivalence.
- `ASSET` contains only model meshes. `STUDIO` contains the floor, three area lights and camera. No studio object, camera or light is present in either export.
- Exactly four named hip assemblies and four `circular rubber footpad` meshes; all four pads visually readable in both delivered views.
- SHA-256 hashes of native/export/source/render files recorded in `validation.json` and rechecked unchanged when this record was written.

## Commands and outcomes

Windows private CLI, Blender 4.5.12 LTS:

```text
"C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background --factory-startup --threads 4 --python-exit-code 1 --python build.py
"C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background --factory-startup --threads 4 --python-exit-code 1 --python validate.py
```

Both final commands exited 0. Validation opened the saved native file, then separately cleared the scene and imported each exchange file. All {len(v['checks'])} final checks passed.

## Render inspection and production limits

Both final images were opened and visually inspected. Cycles CPU, four threads, 32 samples, denoising, 1440×1080, orthographic 3.65 m scale, three broad studio lights and warm pale gray background. Camera poses, render times and image hashes are in `capture_manifest.json`. Cameras were lowered after the first inspection to expose the far foot. Upper-leg covers were changed to rounded tapered shells; lidar ports, conduits and small fasteners were seated against their supports.

The reference's small rear views were reconciled as a symmetrical four-leg mechanism with a complete rear battery enclosure and solid telescope back cap. The optical housing has one front lens; the back is not a second lens. Hidden structural links and service covers are coherent reconstructions, not a claim of manufacturing accuracy.

Static display asset: no rig, animation, collision or LODs. Solid PBR groups only, with no image textures or wear maps. Component UV islands are independently packed per part; there is no shared texture atlas. Assembled mechanical parts intentionally intersect at joints. Blender/Cycles is the appearance reference; exchange-format material conversion, especially FBX glass/roughness, can vary by destination renderer. No additional generated images or external creative resources were used.
'''
with open(os.path.join(ROOT,'RESULT.md'),'w',encoding='utf8',newline='\n') as f:f.write(text)
with open(os.path.join(ROOT,'completion.json'),'w',encoding='utf8') as f:json.dump({'status':'ready_for_review','started_at_utc':start.isoformat(),'finished_at_utc':end.isoformat(),'elapsed_seconds':round(elapsed,3),'final_file_hashes_rechecked':True,'checks_passed':len(v['checks']),'triangles':s['evaluated_triangles'],'bounds_xyz_m':d},f,indent=2)
print(json.dumps({'status':'ready_for_review','elapsed_seconds':round(elapsed,3),'triangles':s['evaluated_triangles'],'dimensions_xyz_m':d,'result':os.path.join(ROOT,'RESULT.md')},indent=2))
