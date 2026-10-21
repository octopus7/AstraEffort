"""Run only after private UE has exited and all four captures were inspected."""
import os,json,hashlib,shutil,datetime,pathlib
from PIL import Image,ImageStat
repo=pathlib.Path('D:/github/AstraEffort/ForestDemo')
work=repo/'Work/MountainStation/high';scratch=repo/'Saved/Workers/MountainStation/high';content=scratch/'Project/Content'
load=lambda p:json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
validation=load(work/'validation.json');runtime=load(work/'runtime_validation.json');review=load(work/'visual_review.json')
assert validation['passed'] and runtime['passed'] and review['passed']
assert review['map_sha256'].lower()==hashlib.sha256((content/'Maps/MountainStation_high.umap').read_bytes()).hexdigest(),'Map changed since captured visual review'
assert len(validation['forbidden_dependencies'])==0
timings=[load(p) for p in sorted(scratch.glob('*_timing.json'))]
assert timings and all(t.get('finished_at_utc') for t in timings)
shots=[]
for name in ['overview','top_down','platform','tracks']:
 p=work/'Screenshots'/f'{name}.png';im=Image.open(p).convert('RGB');assert im.size==(1920,1080)
 assert max(ImageStat.Stat(im).stddev)>15, f'Blank capture: {name}'
 shots.append(hashlib.sha256(p.read_bytes()).hexdigest())
assert len(set(shots))==4,'Duplicate captures'
allowed=pathlib.Path('MountainStation/high');maprel=pathlib.Path('Maps/MountainStation_high.umap')
files=[]
for src in content.rglob('*'):
 if not src.is_file():continue
 rel=src.relative_to(content)
 assert rel==maprel or rel.is_relative_to(allowed),f'Unexpected private content: {rel}'
 assert src.suffix in ['.uasset','.umap'],f'Unexpected package sidecar: {src}'
 assert '__External' not in str(rel) and 'BuiltData' not in src.name
 dest=repo/'Content'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
 sha=hashlib.sha256(src.read_bytes()).hexdigest();assert sha==hashlib.sha256(dest.read_bytes()).hexdigest()
 files.append({'path':str(dest),'bytes':src.stat().st_size,'sha256':sha})
assert any(pathlib.Path(f['path']).name=='MountainStation_high.umap' for f in files)
finish=datetime.datetime.now(datetime.timezone.utc);start=datetime.datetime.fromisoformat('2026-10-21T12:27:18+00:00');elapsed=(finish-start).total_seconds();kst=datetime.timezone(datetime.timedelta(hours=9))
wait=sum(x['wait_seconds'] for x in timings);execution=sum(x['execution_seconds'] for x in timings)
publication={'published_at_utc':finish.isoformat(),'file_count':len(files),'sha256_verified':True,'files':files,'screenshots_sha256':dict(zip(['overview','top_down','platform','tracks'],shots))}
(work/'publication.json').write_text(json.dumps(publication,indent=2),encoding='utf-8')
(work/'timings.json').write_text(json.dumps({'started_at_utc':start.isoformat(),'finished_at_utc':finish.isoformat(),'total_wall_seconds':elapsed,'mutex_wait_seconds':wait,'ue_execution_seconds':execution,'runs':timings,'runtime_supplement':runtime,'note':'Initial non-escalated sandbox probe returned after 1.0717687 seconds with no UE log; excluded from actual UE execution totals. Runtime supplement is included in UE execution, not additive.'},indent=2),encoding='utf-8')
status={'theme':'MountainStation','effort':'high','status':'ready_for_review','started_at_utc':start.isoformat(),'finished_at_utc':finish.isoformat(),'elapsed_seconds':elapsed,'map':'/Game/Maps/MountainStation_high','validation':{'asset_registry':validation['checks'],'runtime':runtime['checks'],'visual':review,'published_files':len(files),'sha256_verified':True},'blockers':[]}
(work/'STATUS.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
rows='\n'.join(f"| {pathlib.Path(t['log']).stem} | {t['wait_seconds']:.3f} | {t['execution_seconds']:.3f} | {t['exit_code']} |" for t in timings)
report=f'''# MountainStation / high — Solmaru station

Status: ready_for_review. Independently authored and self-reviewed; integration and Git belong to the supervisor.

Started: {start.isoformat()} UTC / {start.astimezone(kst).isoformat()} KST.
Finished / first delivery: {finish.isoformat()} UTC / {finish.astimezone(kst).isoformat()} KST.
Actual total wall time: {elapsed:.3f} seconds. Start was preserved through all repairs and supervisor supplementation.
Mutex wait: {wait:.3f} seconds. Actual UE execution: {execution:.3f} seconds (includes import, validation, runtime tests and captures; not additive to wall time).

| Run | Mutex wait seconds | UE execution seconds | Exit |
|---|---:|---:|---:|
{rows}

The runtime supplement was requested at 2026-10-21T12:46:15Z. Its actual start, finish and elapsed are in runtime_validation.json; the containing process timing is listed above. The original build and all failed attempts remain documented in the private logs. No first delivery existed before this report.

## Delivered scene

A 100 × 100 m sculpted mountain meadow supports a cream station with muted teal folded roof, curved stone platform, continuous rails and 145 sleepers, open arched tunnel, freight shed, original crates/barrels, hillside footpath, 34 pines, benches, lanterns, station signs, clock and luggage. Rounded edges and a restrained palette tie the assemblies together. The platform has a 1:12.4 access ramp with handrails. Ground and environment use complex static collision; the baseline DefaultPawn and ScreenDebugLogger are retained.

- Content/MountainStation/high/: original meshes and materials.
- Content/Maps/MountainStation_high.umap: non-World-Partition map, dynamic lighting.
- Work/MountainStation/high/Source/: original Blender scene, 11 FBX assemblies and reproducible scripts.
- Screenshots/: four actual 1920×1080 UE renders, capture_manifest.json.
- validation.json, runtime_validation.json, baseline_validation.json, layout_checks.json, visual_review.json, publication.json, timings.json and UE_evidence.log.

## Validation evidence

The saved map was reloaded. Terrain extents are 5000 cm per half-axis. Recursive Asset Registry inspection covered {validation['checked_package_count']} packages and found zero foreign /Game dependencies. PlayerStart, native ScreenDebugLogger, dynamic lighting, required assemblies and collision configuration passed. Runtime PIE confirmed controller/Pawn creation, possession, arrival position, three blocking collision sweeps, short platform movement and normal PIE shutdown. See the actual per-check results and trace endpoints in runtime_validation.json.

All {len(files)} published files were copied only after the private UE process exited, and SHA-256 equality with scratch was checked. No external actor/object packages, map-adjacent BuiltData, shared project changes or Git mutations were made.

## Actual rendered evidence

![Overview](Screenshots/overview.png)
![Top down](Screenshots/top_down.png)
![Platform](Screenshots/platform.png)
![Tracks](Screenshots/tracks.png)

Capture settings and UTC timestamps are in Screenshots/capture_manifest.json. The prescribed orthographic overview/top-down coordinates and 20000 cm width are used; close views use horizontal FOV 70 degrees. Actual UE SceneCapture2D final-color LDR rendering, High scalability, screen percentage 100. No editor UI or generated substitute imagery.

## Limitations and production notes

Static environment only; no train simulation, station interior or custom walking-character system. The default Pawn is the baseline flying DefaultPawn, and runtime verification is scripted movement/collision rather than an exhaustive human walk-through. The native Hello implementation remains unchanged; clean screenshots hide debug messages. Exact runtime evidence and the observation limit for Hello are recorded in runtime_validation.json.

Visual review notes: {'; '.join(review['limitations'])}

The initial sandbox UE probe produced no engine log. A commandlet import then failed because Slate was not initialized; full-editor offscreen import succeeded. First capture rotations used an incorrect positional Rotator constructor; those blank frames were rejected and replaced after correction. Runtime sweeps exposed the presentation sky sphere reverting to BlockAll on reload; a persistent NoCollision profile and disabled actor collision fixed that obstruction. An optional diagnostic BreakHitResult helper was not exposed to Python and was removed before the final runtime pass. Source geometry sharing also needed an isolated-mesh copy before joining; the final source exports were checked afterward. Timing records include these repairs. A temporary Blender source preview was used for internal geometry QA only and is not substituted for UE evidence.

External references: no third-party artwork or another assignment's resources. Read-only baseline source/config from Git commit 7558c8f, existing baseline binaries, /Engine BasicShapes and DefaultTextureCube, and installed UE 5.7 C++ API headers were used. This author performed the final review; no other model or subagent authored the scene.
'''
(work/'RESULT.md').write_text(report,encoding='utf-8')
print(json.dumps({'status':'ready_for_review','elapsed_seconds':elapsed,'files':len(files),'mutex_wait_seconds':wait,'ue_execution_seconds':execution},indent=2))
