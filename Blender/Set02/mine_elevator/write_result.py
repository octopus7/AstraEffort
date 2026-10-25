import os, json, hashlib
from datetime import datetime, timezone, timedelta
ROOT=os.path.dirname(os.path.abspath(__file__))
def read(n):
    with open(os.path.join(ROOT,n),encoding='utf-8') as f:return json.load(f)
v=read('validation.json');b=read('build_record.json');c=read('capture_manifest.json');fix=read('clearance_fix_record.json')
assert v['passed'] and all(v['checks'].values())
def sha(n):
    h=hashlib.sha256()
    with open(os.path.join(ROOT,n),'rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()
for name,meta in v['files'].items():assert sha(name)==meta['sha256'],name+' changed after validation'
end=datetime.now(timezone.utc);start=datetime.fromisoformat(b['started_at_utc']);kst=timezone(timedelta(hours=9))
elapsed=(end-start).total_seconds();stats=v['formats'][0]
captures=c['captures']+c.get('superseded_first_capture',[])+c.get('superseded_additional_captures',[])
render_seconds=sum(x['elapsed_seconds'] for x in captures)
review={'reviewed_at_utc':end.isoformat(),'method':'Assistant inspected both actual final PNGs with view_image after final geometry correction.',
 'views':[{ 'path':x['path'],'sha256':sha(x['path'])} for x in c['captures']],
 'findings':['Entire canopy and ground-contact feet are in frame at 80 percent of image height.','Open portal and separate safety cage/gate remain visible in hero.','Four posts, spoked sheave, taut rope paths, roof winch and annex are readable.','Rear image shows complete ground-to-deck stair, landings, guardrails and structural bracing.'],
 'corrections':['Corrected initial landscape orthographic cropping.','Lowered sheave and axle carrier 0.12 m for nominal 0.097 m canopy liner clearance; rebuilt analytical tangent ropes.'],
 'no_further_changes_after_validation':True}
with open(os.path.join(ROOT,'visual_review.json'),'w',encoding='utf-8') as f:json.dump(review,f,indent=2)
result=f'''# Mine elevator headhouse — ready for review

Delivered `mine_elevator.blend`, `mine_elevator.glb`, `mine_elevator.fbx`, reproducible `build.py`, actual `renders/hero.png` and `renders/rear.png`, `capture_manifest.json`, `validation.json`, and `visual_review.json`. All files are under `D:/github/AstraEffort/Blender/Set02/mine_elevator/`.

626 named editable mesh parts; **145,712 triangles**. True transformed-vertex dimensions: **5.2200 × 4.8793 × 8.0600 m**. Bounds minimum: ({stats['bounds_min'][0]:.6f}, {stats['bounds_min'][1]:.6f}, {stats['bounds_min'][2]:.6f}); maximum: ({stats['bounds_max'][0]:.6f}, {stats['bounds_max'][1]:.6f}, {stats['bounds_max'][2]:.6f}). Meters, Z up, front −Y, lowest surface Z=0.

The open portal contains a separate floor-equipped lift cage, two diamond-mesh gate leaves, two I-section guide rails and four carriage stations. Above are four stout posts, a two-groove sheave with six spokes per face, a through axle, two continuous tangent-routed ropes and a powered winding drum. A fourteen-step stair reaches the open service deck. The rounded annex has a door, twelve vent louvers, maintenance panel and conduits. Rear bracing and a softly curved canopy complete the structure.

Hidden-geometry decisions: the full stair descends behind the annex; the winding drum is visible on its roof, giving the ropes explicit endpoints. The rear lower shaft is lined. The source reference is `D:/github/AstraEffort/REF/Set02/mine_elevator.png`, supplied by the parent; no other creative asset or external web reference was used.

Final hero and rear were rendered with Blender 4.5.12 LTS, Cycles CPU, four threads, 32 samples, denoising, 1440×1080, orthographic cameras and soft studio lighting. Both actual final images were inspected. Initial cropping was corrected; an observed pulley/canopy interference was corrected by lowering the axle 0.12 m, leaving nominal 0.097 m clearance. Superseded capture timings remain in the manifest.

Fresh-process verification opened the saved BLEND, then independently imported GLB and FBX into empty scenes: all **13 checks passed**. Mesh counts, exact triangle counts and transformed bounds agree. All faces have UVs and materials; no nonfinite geometry, zero-area geometric/UV triangles, missing images, cameras/lights/floor in exports, or nonmanifold edges after position-only seam welding. Final hashes are in `validation.json`; no render or asset was changed after validation.

Production timer began after brief/reference inspection: **{start.isoformat()} UTC** / **{start.astimezone(kst).isoformat()} KST**. Finished **{end.isoformat()} UTC** / **{end.astimezone(kst).isoformat()} KST**. Elapsed **{elapsed:.3f} wall seconds**. First build/export/render run: {b['build_elapsed_seconds']:.3f} s; all six actual capture operations, including superseded framing passes: {render_seconds:.3f} s; fresh final validation: {v['elapsed_seconds']:.3f} s. These phase times overlap the build time and are not additive.

Commands: private `blender.exe --background --factory-startup --threads 4 --python-exit-code 1 --python <script>` ran `build.py`, `finalize_captures.py`, `clearance_fix.py`, and `validate.py`; each exited 0. Logs and correction scripts are included locally. No shared Blender scene, child agents, image generation, installations, Git operations or unrelated creative resources were used.

Limitations: solid named PBR materials with per-component UV islands; no image textures or shared atlas. Static visualization, not a load-certified lifting mechanism; no rig, animation, collision or LODs. Clearances and structural proportions are artistic reconstruction, not engineering certification. Separate mating parts intentionally overlap at joints. Source uses baked triangulated geometry for stable exports.
'''
with open(os.path.join(ROOT,'RESULT.md'),'w',encoding='utf-8') as f:f.write(result)
status={'asset':'mine_elevator','status':'ready_for_review','started_at_utc':start.isoformat(),'finished_at_utc':end.isoformat(),
 'started_at_kst':start.astimezone(kst).isoformat(),'finished_at_kst':end.astimezone(kst).isoformat(),'elapsed_seconds':elapsed,
 'triangles':stats['triangles'],'mesh_objects':stats['mesh_objects'],'dimensions_m':stats['dimensions'],
 'validation':'All 13 checks passed in fresh saved BLEND and separate GLB / FBX imports; final render hashes verified.',
 'blockers':[],'stable_paths':['mine_elevator.blend','mine_elevator.glb','mine_elevator.fbx','build.py','renders/hero.png','renders/rear.png','capture_manifest.json','validation.json','RESULT.md']}
with open(os.path.join(ROOT,'STATUS.json'),'w',encoding='utf-8') as f:json.dump(status,f,indent=2)
print(json.dumps(status,indent=2))
