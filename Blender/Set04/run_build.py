"""Sequential private Blender invocation, byte inventory and real timing only."""
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BLENDER=Path('C:/Program Files/Blender Foundation/Blender 4.5/blender.exe')
ASSETS=['twin_rotor_cargo_drone','airport_cargo_tug','circular_drone_hangar','low_control_building']
RECORDED_START='2026-10-25T05:40:53+00:00'


def utc():return datetime.now(timezone.utc)
def iso(dt):return dt.isoformat()
def kst(dt):return dt.astimezone(timezone(timedelta(hours=9))).isoformat()
def write(name,data):(ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    (ROOT/'logs').mkdir(exist_ok=True)
    process_start=utc();t0=time.perf_counter();records=[]
    status={'set':'Set04','group':1,'status':'working','review_status':'deferred_by_user','started_at_utc':RECORDED_START,'started_at_kst':kst(datetime.fromisoformat(RECORDED_START)),'process_started_at_utc':iso(process_start),'worker_model':'Astra','worker_effort':'max','assets':ASSETS,'checks':'subprocess returncodes and expected nonempty files only'}
    write('STATUS.json',status)
    for slug in ASSETS:
        start=utc();pt=time.perf_counter();log=ROOT/'logs'/(slug+'.log')
        command=[str(BLENDER),'--background','--factory-startup','--threads','4','--python-exit-code','1','--python',str(ROOT/'build.py'),'--','--asset',slug]
        print('START',slug,iso(start),flush=True)
        with log.open('w',encoding='utf-8') as stream:
            result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,cwd=ROOT)
        end=utc()
        record={'asset':slug,'started_at_utc':iso(start),'started_at_kst':kst(start),'finished_at_utc':iso(end),'finished_at_kst':kst(end),'process_seconds':round(time.perf_counter()-pt,3),'returncode':result.returncode,'log':str(log.relative_to(ROOT)),'command':command}
        records.append(record);write('process_timings.json',records)
        print('END',slug,'returncode',result.returncode,'seconds',record['process_seconds'],flush=True)
        if result.returncode!=0:
            status.update(status='needs_attention',blockers=[f'{slug}: Blender execution returned {result.returncode}'],process_records=records)
            write('STATUS.json',status);return result.returncode or 1
    # Expected output existence/size is the sole completion gate requested.
    inventory=[];missing=[]
    for slug in ASSETS:
        paths=[ROOT/slug/(slug+ext) for ext in ('.blend','.glb','.fbx')]+[ROOT/slug/'metadata.json']+[ROOT/slug/'renders'/(v+'.png') for v in ('hero','rear')]
        files=[]
        for p in paths:
            if not p.is_file() or p.stat().st_size==0:missing.append(str(p));continue
            files.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest()})
        inventory.append({'asset':slug,'files':files})
    end=utc();start=datetime.fromisoformat(RECORDED_START)
    timing={'started_at_utc':iso(start),'started_at_kst':kst(start),'finished_at_utc':iso(end),'finished_at_kst':kst(end),'elapsed_wall_seconds':round((end-start).total_seconds(),3),'wrapper_elapsed_seconds':round(time.perf_counter()-t0,3),'blender_process_seconds':round(sum(r['process_seconds'] for r in records),3),'processes':records}
    write('delivery_manifest.json',{'set':'Set04','status':'produced_unreviewed' if not missing else 'needs_attention','review_status':'deferred_by_user','inventory_only':True,'checks':'actual subprocess returncode 0 and expected nonempty output paths','not_performed':['render inspection','reopen or export reimport','geometry/UV validation','review agents'],'assets':inventory,'source':'build.py','runner':'run_build.py','logs':'logs/','references':'REF/','timing':timing,'missing_or_empty':missing})
    status.update(status='produced_unreviewed' if not missing else 'needs_attention',finished_at_utc=iso(end),finished_at_kst=kst(end),elapsed_seconds=timing['elapsed_wall_seconds'],blender_process_seconds=timing['blender_process_seconds'],blockers=missing,expected_output_files=24,nonempty_output_files=sum(len(a['files']) for a in inventory),manifest='delivery_manifest.json')
    write('STATUS.json',status)
    table='\n'.join(f"| `{a['asset']}` | [BLEND]({a['asset']}/{a['asset']}.blend) · [GLB]({a['asset']}/{a['asset']}.glb) · [FBX]({a['asset']}/{a['asset']}.fbx) | [hero]({a['asset']}/renders/hero.png) · [rear]({a['asset']}/renders/rear.png) | [reference](REF/{a['asset']}.png) |" for a in inventory)
    common=f"""# Set04 — Aerial logistics

Status: **produced_unreviewed**. Review: **deferred_by_user**.

Four original ordinary rounded mesh models, with named editable parts, individually authored component UVs and a warm ivory / slate blue / graphite / ochre PBR palette. Local [reference images and prompts](REF/) informed the silhouettes; no source meshes or other sets were read or reused. Native files separate ASSET and STUDIO. GLB and FBX export only selected asset meshes.

| Asset | Geometry | Actual studio renders | Design input |
|---|---|---|---|
{table}

The renders are actual Cycles CPU images at 960 × 960, 40 samples and four threads. They were generated for later review and were not opened or inspected. Only Blender subprocess completion and the existence of the 24 expected nonempty output files were checked. No fresh BLEND reopening, GLB/FBX reimport, geometry/UV validators or reviewer tasks were performed. Byte counts and SHA256 entries in [delivery_manifest.json](delivery_manifest.json) are an inventory, not independent validation.

Each asset's metadata records authored scene dimensions, parts and material values, UV method, camera settings and actual render timing. UVs use separate per-component surface islands after bevel authoring; overlap, stretch and export roundtrip quality remain unreviewed. Materials are solid PBR colors with opaque stylized glazing. No texture maps, rigs, animation, collision or LODs are supplied. Unseen rear structures are original functional interpretations.

Recorded work start: {iso(start)} UTC / {kst(start)} KST. Finish: {iso(end)} UTC / {kst(end)} KST. Wall: {timing['elapsed_wall_seconds']:.3f} s. Blender subprocess total: {timing['blender_process_seconds']:.3f} s. Detailed per-asset timings: [process_timings.json](process_timings.json). Recorded work start is the initial clock checkpoint during the task setup.

Reproduction: [build.py](build.py), driven by [run_build.py](run_build.py), using Blender 4.5.12 background factory startup with four threads. Build logs are in [logs/](logs/). No image generation, installation, shared live Blender session, Git operation or sub-agent was used. This set is frozen after production pending the main coordinator's group commit.
"""
    (ROOT/'RESULT.md').write_text(common,encoding='utf-8')
    (ROOT/'README.md').write_text(common,encoding='utf-8')
    print('SET04_PRODUCED_UNREVIEWED',status['nonempty_output_files'],'files',flush=True)
    return 1 if missing else 0


if __name__=='__main__':sys.exit(main())
