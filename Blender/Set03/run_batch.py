"""Run Set03 sequential private Blender processes, inventory outputs, no reviews."""
import subprocess
import time
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT=Path(__file__).resolve().parent
BLENDER=Path('C:/Program Files/Blender Foundation/Blender 4.5/blender.exe')
SLUGS=['street_sweeper','pipe_inspection_robot','road_maintenance_depot','compact_pump_station']
KST=timezone(timedelta(hours=9))

def now():return datetime.now(timezone.utc)
def write_json(path,data):path.write_text(json.dumps(data,indent=2),encoding='utf-8')
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while chunk:=f.read(1024*1024):h.update(chunk)
    return h.hexdigest()

def main():
    startdata=json.loads((ROOT/'production_start.json').read_text(encoding='utf-8'))
    started=datetime.fromisoformat(startdata['started_at_utc'])
    status={'set':'Set03','theme':'Urban maintenance','status':'working','review_status':'deferred_by_user',
            'started_at_utc':started.isoformat(),'started_at_kst':started.astimezone(KST).isoformat(),
            'assets':SLUGS,'completed_assets':[],'processes':[],'blockers':[]}
    write_json(ROOT/'STATUS.json',status)
    logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    for slug in SLUGS:
        cmd=[str(BLENDER),'--background','--factory-startup','--threads','4','--python-exit-code','1','--python',str(ROOT/'build.py'),'--',slug]
        t0=time.perf_counter();utc0=now();log=logs/(slug+'.log')
        print('START '+slug+' '+utc0.isoformat(),flush=True)
        with log.open('w',encoding='utf-8') as f:
            result=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,cwd=ROOT,check=False)
        entry={'slug':slug,'command':cmd,'started_at_utc':utc0.isoformat(),'finished_at_utc':now().isoformat(),
               'duration_seconds':time.perf_counter()-t0,'returncode':result.returncode,'log':log.relative_to(ROOT).as_posix()}
        status['processes'].append(entry)
        expected=[ROOT/slug/(slug+ext) for ext in ('.blend','.glb','.fbx')]+[ROOT/slug/'metadata.json',ROOT/slug/'renders'/'hero.png',ROOT/slug/'renders'/'rear.png']
        missing=[p.relative_to(ROOT).as_posix() for p in expected if not p.is_file() or p.stat().st_size==0]
        entry['expected_files_nonempty']=not missing
        if result.returncode or missing:
            status['status']='needs_attention';status['blockers']=[{'slug':slug,'returncode':result.returncode,'missing_or_empty':missing}]
            write_json(ROOT/'STATUS.json',status)
            print('EXECUTION_FAILURE '+json.dumps(status['blockers']),flush=True)
            return 1
        status['completed_assets'].append(slug);write_json(ROOT/'STATUS.json',status)
        print('PRODUCED '+slug+' '+str(round(entry['duration_seconds'],2))+' seconds; returncode '+str(result.returncode),flush=True)
    finish=now();status.update({'status':'produced_unreviewed','finished_at_utc':finish.isoformat(),'finished_at_kst':finish.astimezone(KST).isoformat(),
                             'elapsed_seconds':(finish-started).total_seconds(),'total_blender_process_seconds':sum(x['duration_seconds'] for x in status['processes']),
                             'completion_checks':'Process return codes and expected file existence/nonzero size only. Hashes are inventory, not validation.',
                             'review_and_validation':'Deferred by user; no generated render inspection, reopen, reimport or geometry/UV validators.'})
    write_json(ROOT/'STATUS.json',status)
    rows=[]
    for slug in SLUGS:
        for rel in [slug+ext for ext in ('.blend','.glb','.fbx')]+['metadata.json','renders/hero.png','renders/rear.png']:
            path=ROOT/slug/rel
            rows.append({'asset':slug,'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':digest(path)})
    for path in [ROOT/'build.py',ROOT/'run_batch.py',ROOT/'production_start.json']+sorted(logs.glob('*.log')):
        rows.append({'asset':None,'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':digest(path)})
    manifest={'set':'Set03','status':'produced_unreviewed','review_status':'deferred_by_user','started_at_utc':started.isoformat(),
              'finished_at_utc':finish.isoformat(),'elapsed_seconds':status['elapsed_seconds'],'processes':status['processes'],
              'inventory_note':'File hashes and nonzero sizes record produced files only. Review and validation are deferred.','files':rows}
    write_json(ROOT/'delivery_manifest.json',manifest)
    lines=['# Set03 — urban maintenance','', 'Status: **produced_unreviewed**. Review: **deferred_by_user**.','',
           'Four original editable rounded mesh assets, geometry-only GLB/FBX and neutral 960×960 studio renders. The images have been generated but not inspected.','',
           '| Asset | Editable / exports | Preview images for later review |','|---|---|---|']
    for slug in SLUGS:
        lines.append(f'| {slug} | [BLEND]({slug}/{slug}.blend) · [GLB]({slug}/{slug}.glb) · [FBX]({slug}/{slug}.fbx) | [Hero]({slug}/renders/hero.png) · [Rear]({slug}/renders/rear.png) |')
    lines += ['', '[Production record](RESULT.md) · [Status](STATUS.json) · [File inventory](delivery_manifest.json) · [Build source](build.py)', '',
              'Reproduce all four with the bundled Python: `"C:/Program Files/Blender Foundation/Blender 4.5/4.5/python/bin/python.exe" -X utf8 run_batch.py`. This overwrites the owned generated files.', '',
              'Native files separate `ASSET` and `STUDIO`. Each mesh part has a meaningful primitive, planar or parameterized UV layout. Materials are named solid PBR palette surfaces. Static assets only; no rig, animation, collision or LOD delivery.', '',
              'Main-supplied design inputs are preserved in the local [REF folder](REF/): [sweeper](REF/street_sweeper.png), [inspection robot](REF/pipe_inspection_robot.png), [depot](REF/road_maintenance_depot.png), and [pump station](REF/compact_pump_station.png). These inputs are separate from the actual generated studio renders.']
    (ROOT/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    result=['# Set03 production record','', 'Status: **produced_unreviewed**. `review_status=deferred_by_user`.','',
            f'- Start UTC: {started.isoformat()}',f'- Start KST: {started.astimezone(KST).isoformat()}',
            f'- Finish UTC: {finish.isoformat()}',f'- Finish KST: {finish.astimezone(KST).isoformat()}',
            f'- Elapsed wall seconds: {status["elapsed_seconds"]:.3f}',f'- Blender process seconds: {status["total_blender_process_seconds"]:.3f}',
            '- Timing starts at recorded reference intake completion, before geometry authoring; process durations use Python perf_counter.', '',
            '| Asset | Process seconds | Return code | Expected nonempty files |','|---|---:|---:|---|']
    for p in status['processes']:result.append(f'| {p["slug"]} | {p["duration_seconds"]:.3f} | {p["returncode"]} | {p["expected_files_nonempty"]} |')
    result += ['', 'Delivered paths are listed in [README.md](README.md) and in [delivery_manifest.json](delivery_manifest.json) with bytes and SHA256. Source and individual process logs are retained.', '',
               'The source authors original ordinary mesh geometry from the four supplied `REF/Set03/*.png` design inputs. Rounded bodies and architecture use editable component meshes, bevels, curved sweeps, purpose-built cylindrical structures and named PBR palette materials. The models preserve functional reference structures: sweeper brushes/hopper/suction shoe, articulated inspection modules/camera/tether reel, open service bay/office/tool alcove, and paired volute pumps/manifold/valve/cabinet.', '',
               'Only process completion and expected output existence/nonzero size were checked. Hashes are file inventory. Visual inspection, fresh BLEND reopen, GLB/FBX reimport, geometry validation, UV validation and independent review were deferred by the user. No claim of validated geometry, UVs, framing, material appearance or export roundtrips is made.', '',
               'Known limitations: proportions and engineering details are simplified game art; materials are solid-color PBR; glass uses opaque reflective shading for a readable game palette; no rig, animation, collision or LODs. Renders are actual Cycles renders, 960×960 with 40 samples and denoising, but have not been inspected. Each metadata file contains direct authoring measurements and camera/render timestamps, not independent validation.', '',
               'External references: only the four main-supplied PNGs and prompt text under `REF/Set03`. No other set, voxel, ForestDemo or shared live Blender scene was read or reused. No installation, image generation, Git operation or reviewer dispatch was performed.', '',
               'The set is frozen after these four assets pending main integration and later user review.']
    (ROOT/'RESULT.md').write_text('\n'.join(result)+'\n',encoding='utf-8')
    print('SET03_FROZEN '+json.dumps({'elapsed_seconds':status['elapsed_seconds'],'files':len(rows)}),flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
