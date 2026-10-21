"""Finalize evidence and timestamps after successful owned publication."""
from pathlib import Path
import datetime,json,hashlib,shutil
W=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra')
S=Path(r'D:/github/AstraEffort/ForestDemo/Saved/Workers/MountainStation/ultra')
F=Path(r'D:/github/AstraEffort/ForestDemo')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dt(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
def delta(a,b):return (dt(b)-dt(a)).total_seconds()
def write(name,data):(W/name).write_text(json.dumps(data,indent=2),encoding='utf-8')
pub=read(W/'publication_manifest.json');v=read(W/'validation.json');r=read(W/'runtime_validation.json');art=read(W/'source_summary.json');cap=read(W/'Screenshots/capture_manifest.json')
assert r['normal_shutdown'] and r['pie_world_count']>0 and all(x['passed'] for x in r['worlds'])
for entry in pub['files']:
    assert hashlib.sha256((F/entry['path']).read_bytes()).hexdigest()==entry['sha256']
timings=[]
for p in sorted(W.glob('timing_*.json')):
    if p.name=='timing_summary.json':continue
    t=read(p);t['file']=p.name;timings.append(t)
wait=sum(t['wait_seconds'] for t in timings);execution=sum(t['execution_seconds'] for t in timings)
original=dt('2026-10-21T12:27:25Z');finish=datetime.datetime.now(datetime.timezone.utc);kst=datetime.timezone(datetime.timedelta(hours=9))
supp=read(W/'supplement_timing.json');supp.pop('requested_at_utc',None);supp.pop('combined_session',None)
supp.update(finished_at_utc=r['finished_at_utc'],elapsed_seconds=delta(supp['started_at_utc'],r['finished_at_utc']),final_runtime_seconds=delta(r['started_at_utc'],r['finished_at_utc']),final_capture_seconds=delta(cap['capture_started_at_utc'],cap['capture_finished_at_utc']),combined_sessions=[t['file'] for t in timings if t['file'].startswith('timing_review_') or 'runtime' in t['file']],note='The supplement interval overlaps initial production, geometry corrections, capture debugging, queue waits and final runtime verification. It is not exclusive supervisor overhead. Original production start is unchanged.')
write('supplement_timing.json',supp)
record={'started_at_utc':original.isoformat(),'finished_at_utc':finish.isoformat(),'elapsed_wall_seconds':(finish-original).total_seconds(),'ue_mutex_wait_seconds':wait,'ue_execution_seconds':execution,'timing_records':timings,'runtime_validation_seconds':delta(r['started_at_utc'],r['finished_at_utc']),'capture_seconds':delta(cap['capture_started_at_utc'],cap['capture_finished_at_utc']),'note':'Totals include unsuccessful iterations and one sandbox launch that exited without a UE log. Script-reported checks determine validation success; exit code zero alone does not.'}
write('timing_summary.json',record)
rows='\n'.join('| '+t['file']+' | '+f"{t['wait_seconds']:.6f}"+' | '+f"{t['execution_seconds']:.6f}"+' | '+str(t['exit_code'])+' |' for t in timings)
report=f'''# MountainStation / ultra — Alder Pass

Ready for supervisor review. The independent 100 × 100 m scene, owned assets, saved map, four actual UE renders and validation records are delivered. No Git index or commit operations were performed.

## Time record

| Event | UTC | KST |
|---|---|---|
| Original work start | {original.isoformat()} | {original.astimezone(kst).isoformat()} |
| Review-ready finish | {finish.isoformat()} | {finish.astimezone(kst).isoformat()} |

Elapsed wall time: **{record['elapsed_wall_seconds']:.3f} seconds**. Recorded UE mutex/priority wait: **{wait:.6f} seconds**. Recorded UE process execution: **{execution:.6f} seconds**. Wall time includes CPU authoring, reviews, tool debugging, queue waiting, the supervisor's temporary registration hold while updating the queue runner, and reporting. The registration hold occurred before queue entry and is not counted as mutex wait. Queue wait is not active scene-production time. No migration was required for this MountainStation asset root.

| Timing record | Wait seconds | Execution seconds | Process exit |
|---|---:|---:|---:|
{rows}

`timing_build.json` is an unsuccessful sandbox launch with no engine log; its small launcher time remains in the totals. Earlier zero process exits do not imply successful scene checks: Python failures are preserved under Diagnostics. The first authorized build failed on a Python API field. Subsequent iterations resolved level replacement, capture lifetime/projection, collision initialization/profiles, ramp/path/fence obstruction, lighting and lettering. All time remains counted.

The supervisor runtime supplement began at {supp['started_at_utc']} and ended at {supp['finished_at_utc']}, spanning {supp['elapsed_seconds']:.3f} seconds. This interval overlaps production and retries; it cannot be treated as exclusive supervision overhead. The final actual PIE test lasted {record['runtime_validation_seconds']:.3f} seconds; final four-view capture sequence lasted {record['capture_seconds']:.3f} seconds. Detailed timestamps are in `supplement_timing.json` and the original timing files.

## Delivered paths and scene

- `Content/Maps/MountainStation_ultra.umap` — `/Game/Maps/MountainStation_ultra`.
- `Content/MountainStation/ultra/` — {pub['asset_files']} assets under the sole permitted project asset root.
- `Work/MountainStation/ultra/` — source, scripts, evidence, this report and Screenshots.
- `SourceArt/AlderPass.blend` plus 47 FBX exports are the authoritative final geometry. Historical refinement scripts are not idempotent; follow `REPRODUCTION.md`.

The scene combines a teal timber station, terracotta roof/canopy, glazed window frames, clock/name/number signs, benches, luggage and planting; a curved masonry platform and accessible graded ramp; curved rails with sleepers/fasteners/ballast; a masonry tunnel portal and short lined dark interior; freight shed, crates, sacks and handcart; contour-following loop trail, fences, conifers, shrubs and rounded rock formations. Terrain and props are original background-Blender geometry with a restrained palette. No generated scene imagery or external artistic assets were used.

Final source: {art['mesh_groups']} semantic mesh groups, {art['source_vertices']} vertices and {art['source_polygons']} source polygons. These are source geometry counts, not runtime performance measurements. Unreal has 47 owned mesh assets and 28 owned materials, with dynamic key/fill/skylight illumination. Terrain is mesh-based; there is no Landscape sculpt asset.

## Validation evidence

- Saved private map reloaded: {v['actor_count']} actors; terrain XY extent is exactly 5,000 cm each side (100 × 100 m).
- Recursive dependency audit visited {v['dependency_packages_checked']} packages and found zero foreign `/Game` dependencies. Only `/Game/MountainStation/ultra`, its own map, baseline script classes and engine resources are referenced. See `validation.json`.
- No World Partition external actor/object packages or map BuiltData. The scene was authored with a non-partitioned new level and force-no-precomputed-lighting; `publication_manifest.json` records the package check.
- Ten downward collision samples have no initial overlap. Ramp/platform join differs by approximately 0.862 cm. The ramp has a {art['ramp_plan_run_cm']:.3f} cm plan run, 112 cm rise and approximately {art['ramp_slope_degrees']:.3f}° slope.
- Actual PIE game world created a PlayerController and DefaultPawn, possessed correctly at the arrival PlayerStart. Eight successive swept moves along the ground/ramp/platform reached their targets; a separate side sweep was blocked by the solid platform. This is a short DefaultPawn sweep test, not full character locomotion QA.
- One original baseline ScreenDebugLogger was present. A transient Python subclass overriding only ReceiveBeginPlay proved dispatch through the unchanged native BeginPlay lifecycle. Native implementation still calls its existing green `Hello` message. Comparison renders intentionally omit debug overlays; no screenshot claim is made for visible Hello pixels. No probe actor/class is saved in the delivered map.
- PIE ended normally. Map SHA-256 was identical before/after the runtime-only supplement. The private editor exited before publication. Every copied final asset and map was SHA-256 matched to the validated private files.

Evidence: `validation.json`, `runtime_validation.json`, `native_baseline_evidence.json`, `collision_readiness.json`, `visual_inspection.json`, `publication_manifest.json`, `source_summary.json`, `timing_summary.json`, and `Logs/`.

## Actual renders

All four images were rendered by UE 5.7 SceneCapture2D with a real RHI at 1920 × 1080, High scalability and 100% screen percentage. The author opened and inspected every final image; `visual_inspection.json` binds observations to SHA-256 values. `Screenshots/capture_manifest.json` contains camera, exposure, render settings and actual capture timestamps.

Overview: camera (12000, -12000, 16000) cm aimed at origin, orthographic width 20000 cm. Top-down: (0, 0, 20000) cm, pitch -90°, yaw/roll 0°, same width. Detail cameras have 70° horizontal FOV at 170 cm above sampled local ground. Detail positions differ from other authors' views and should be compared accordingly.

![Overview](Screenshots/overview.png)
![Top down](Screenshots/top_down.png)
![Platform](Screenshots/platform.png)
![Tracks and tunnel](Screenshots/tracks.png)

## Limitations and references

Station and freight structures are exterior shells; the tunnel is a short visual interior with a dark backing. No train movement, railway simulation, custom character movement, NavMesh, full traversal playthrough, packaged-game test or frame-rate benchmark is claimed. Some path seams are angular and distant areas are sparse. The fixed overview sees the tunnel obliquely; the tracks view supplies its frontal evidence. Deep canopy/tunnel shadows remain. Palette materials use no image textures; a future texture/UV pass is separate work.

Original art was authored independently in a background Blender process. Shared Blender MCP, other themes/efforts' resources, shared project saving, shared Source/Config changes and Git mutations were not used. Only read-only baseline ForestDemo native classes and Engine built-ins are shared. Installed UE headers and the official technical API pages linked in `REPRODUCTION.md` informed tooling. No external artistic references.
'''
# Local image links in artifacts use absolute paths for the Codex viewer.
report=report.replace('](Screenshots/',']('+W.as_posix()+'/Screenshots/')
(W/'RESULT.md').write_text(report,encoding='utf-8')
write('STATUS.json',{'theme':'MountainStation','effort':'ultra','status':'ready_for_review','started_at_utc':original.isoformat(),'started_at_kst':original.astimezone(kst).isoformat(),'finished_at_utc':finish.isoformat(),'finished_at_kst':finish.astimezone(kst).isoformat(),'elapsed_seconds':record['elapsed_wall_seconds'],'map':'/Game/Maps/MountainStation_ultra','validation':'Saved private map reload and 100m bounds; 76-package recursive isolation; collision samples; actual PIE possession, eight ramp sweeps, platform blocking and unchanged native BeginPlay lifecycle; normal shutdown; four author-inspected 1920x1080 UE renders; 75 assets and map published with matching SHA-256.','blockers':[],'ue_mutex_wait_seconds':wait,'ue_execution_seconds':execution,'result':'ForestDemo/Work/MountainStation/ultra/RESULT.md'})
print(json.dumps({'status':'ready_for_review','finished_at_utc':finish.isoformat(),'elapsed_seconds':record['elapsed_wall_seconds'],'wait_seconds':wait,'execution_seconds':execution}))
