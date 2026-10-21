from pathlib import Path
import datetime,json
W=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra');D=W/'BlockingSupplement'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.write_text(json.dumps(d,indent=2),encoding='utf-8')
def dt(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
v=read(D/'validation.json');hashes=read(D/'hashes_after.json');old=read(D/'Before/STATUS.json');timing=read(D/'timing.json');closed=read(D/'editor_closed.json')
assert v['passed'] and v['normal_shutdown'] and len(v['tests'])>=3
assert hashes['all_unchanged'] and closed['active_owned_editor_processes']==0
for test in v['tests']:assert test['passed'] and test['movement_hit']['blocking_hit'] and not test['movement_hit']['initial_overlap'] and test['actual_distance_moved_cm']>1
end=datetime.datetime.now(datetime.timezone.utc);kst=datetime.timezone(datetime.timedelta(hours=9))
runs=[dict(read(p),record=p.name) for p in sorted(D.glob('timing_ue_*.json'))]
timing.update(finished_at_utc=end.isoformat(),finished_at_kst=end.astimezone(kst).isoformat(),elapsed_seconds=(end-dt(timing['started_at_utc'])).total_seconds(),ue_mutex_wait_seconds=sum(r['wait_seconds'] for r in runs),ue_execution_seconds=sum(r['execution_seconds'] for r in runs),runs=runs,first_ready_at_utc=old['finished_at_utc'],first_ready_elapsed_seconds=old['elapsed_seconds'],note='Separate post-review validation supplement. Includes failed attempts, queue waits, inspection and reporting. Original production/first-ready timing remains intact.')
write(D/'timing.json',timing)
base=(D/'Before/RESULT.md').read_text(encoding='utf-8')
base=base.replace('| Review-ready finish |','| First submitted ready (retained) |').replace('Elapsed wall time: **','First-delivery elapsed wall time: **',1)
base=base.replace('a separate side sweep was blocked by the solid platform.','the original side-sweep criterion was insufficient because it accepted an unchanged position with no movement HitResult. That original platform-blocking claim is withdrawn and superseded by the verified post-review supplement below.')
base=base.replace('Evidence: `validation.json`, `runtime_validation.json`,','Evidence: `validation.json`, `runtime_validation.json` (original evidence retained; platform-blocking criterion superseded),')
lines=[]
for t in v['tests']:
    mh=t['movement_hit']
    lines.append('| '+t['name']+' | '+str(t['requested_start_cm'])+' | '+str(t['requested_target_cm'])+' | '+str([round(x,4) for x in t['actual_end_cm']])+' | '+f"{t['actual_distance_moved_cm']:.4f}"+' | '+mh['static_mesh'].split('.')[-1]+' |')
section=v['terrain_lod0']['sections'][0];sample=section['test_triangle']
addition=f'''

## Post-review collision evidence correction

This supplement completed at **{end.isoformat()} UTC / {end.astimezone(kst).isoformat()} KST**. First-ready remains **{old['finished_at_utc']}**; its STATUS, RESULT, runtime evidence and package manifest are preserved in `BlockingSupplement/Before/`. The previous eight ramp moves, native BeginPlay probe and normal PIE shutdown are retained. The original platform claim accepted `actual == start` and a `None` move result; it did not exclude initial overlap and is not sufficient evidence of platform blocking.

The new test used a fresh private UE process and the actually possessed DefaultPawn, with its real SphereComponent radius **35 cm**, object channel **ECC_PAWN**, and **Pawn** collision profile. At every test start, an identical sphere/profile query reported no blocking overlap. The Pawn then moved a positive distance and stopped short of the requested target. Its own returned HitResult has **blocking_hit=true**, **initial_overlap=false**, and **0 < time < 1** for every test. Actor, component, static mesh, contact point/normal, requested position and actual end position are recorded in `BlockingSupplement/validation.json`. A second identical sphere/profile trace corroborates the exact same actor/component; the movement result remains the primary evidence.

| Actual Pawn sweep | Start cm | Requested target cm | Actual end cm | Moved cm | Hit static mesh |
|---|---|---|---|---:|---|
{chr(10).join(lines)}

HitResult tuple indices were checked against the installed UE 5.7 `GameplayStatics.h` `BreakHitResult` declaration (line 1079), and `Actor.cpp` `K2_SetActorLocation` (line 6654). The live Python documentation states that set_actor_location returns a HitResult only when movement occurred. `KismetSystemLibrary.cpp` `SphereTraceSingleByProfile` constructs a sphere and calls the world's profile-based sweep. Exact mapping and live API documentation are saved with the test.

### Terrain section audit

The actual final imported Terrain LOD0 has **{v['terrain_lod0']['num_sections']} section**, containing **{section['triangles']} triangles**, with collision enabled and material slot **{section['material_slot']}**. There are **{v['terrain_lod0']['slot1_triangle_count']} slot-1 triangles**. The final presentation refinement changed all terrain faces to Meadow slot 0; `build_art.py` is historical initial-generation source, not the final material assignment. The previous `[true,false]` readiness record came from blindly querying indices 0 and 1; UE returns false for the invalid section-1 index. It was not evidence of a disabled existing terrain section. `run_review.py` now enumerates the actual section count.

The downward Pawn test uses the centroid of actual imported LOD0 section {sample['section']}, triangle {sample['section_triangle_index']}, material slot {sample['material_slot']}, with barycentric weights (1/3,1/3,1/3): {sample['centroid_world_cm']} cm. Its three world-space vertices and section-local vertex indices are recorded. These were read from UE's actual LOD0 position/index buffers through ProceduralMeshLibrary and transformed by the placed Terrain actor. There is no slot-1 interior point to test because that final section has no faces. No collision package change was required.

### Preservation and separate timing

All **76 published map/asset files**, all corresponding private map/asset files, and the **four final PNGs** match their original first-delivery SHA-256 values. `BlockingSupplement/hashes_after.json` contains the per-file proof. No art, lighting, camera, collision settings or package saves were made, and no assets were republished. `BlockingSupplement/editor_closed.json` confirms the private process was closed.

Supplement start: {timing['started_at_utc']} UTC / {dt(timing['started_at_utc']).astimezone(kst).isoformat()} KST. Finish: {end.isoformat()} UTC / {end.astimezone(kst).isoformat()} KST. Separate elapsed wall: **{timing['elapsed_seconds']:.3f} s**; UE queue wait: **{timing['ue_mutex_wait_seconds']:.6f} s**; UE execution: **{timing['ue_execution_seconds']:.6f} s**. Original first-delivery timing above is unchanged.

Four unsuccessful supplement attempts are retained: the first exposed an unavailable Python conversion API; the second rejected a candidate overlapping the rail; the third rejected ballast initial overlap during the intended trace direction; the fourth produced a valid actual Pawn blocking hit but hit a lamp instead of the intended platform. A short probe moving upward out of an overlap had missed the third case, so the final probe uses the intended movement direction. Final candidate paths were queried against actual scene collision, with every query recorded, to select clear routes to the intended meshes before testing actual Pawn movement. The final side start is above the rail/ballast and its concrete hit is `{v['tests'][-1]['movement_hit']['static_mesh'].split('.')[-1]}`, identified separately from the platform slab. All attempts remain included in the separate timing. See `BlockingSupplement/timing.json`, `attempt01_validation.json` through `attempt04_validation.json`, `validation.json` and `Logs/blocking_supplement_*.log`. The ordinary runtime validator uses the same strict non-overlap, positive-motion and actual-hit checks for future runs.
'''
(W/'RESULT.md').write_text(base+addition,encoding='utf-8')
status=read(W/'STATUS.json');status.update(status='ready_for_review',first_ready_at_utc=old['finished_at_utc'],first_ready_at_kst=old['finished_at_kst'],first_ready_elapsed_seconds=old['elapsed_seconds'],finished_at_utc=end.isoformat(),finished_at_kst=end.astimezone(kst).isoformat(),elapsed_seconds=(end-dt(old['started_at_utc'])).total_seconds(),blocking_supplement_finished_at_utc=end.isoformat(),blocking_supplement_elapsed_seconds=timing['elapsed_seconds'],blocking_supplement_ue_mutex_wait_seconds=timing['ue_mutex_wait_seconds'],blocking_supplement_ue_execution_seconds=timing['ue_execution_seconds'],validation='First delivery retained. Fresh-process actual possessed Pawn side/downward platform and terrain sweeps: blocking_hit=true, initial_overlap=false, positive movement, exact actual hit actor/component/mesh and matching same-profile sphere trace. Actual Terrain LOD0: one collision-enabled section, 20000 slot-0 triangles, zero slot-1 faces. Normal PIE shutdown. All 76 packages and four PNG hashes unchanged.',blockers=[])
status['blocking_supplement_phase']='complete'
status['runtime_validation_supplement']='BlockingSupplement/validation.json'
write(W/'STATUS.json',status)
print(json.dumps({'finished_at_utc':end.isoformat(),'first_ready_at_utc':old['finished_at_utc'],'supplement_elapsed_seconds':timing['elapsed_seconds'],'wait_seconds':timing['ue_mutex_wait_seconds'],'execution_seconds':timing['ue_execution_seconds']}))
