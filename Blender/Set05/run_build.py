"""Run four isolated Blender processes and record production output inventory.

No model review, preview opening, import/reopen, or geometry/UV validation.
"""
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BLENDER=Path("C:/Program Files/Blender Foundation/Blender 4.5/blender.exe")
ASSETS=["catamaran_workboat","underwater_service_robot","docking_lift_platform","marine_equipment_workshop"]
KST=timezone(timedelta(hours=9))
LOGS=ROOT/"logs"
LOGS.mkdir(exist_ok=True)


def now():
    return datetime.now(timezone.utc)


def write(path,data):
    path.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")


def inventory(path):
    size=path.stat().st_size
    if not path.is_file() or size<=0:
        raise RuntimeError("Required production output missing/empty: "+str(path))
    digest=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            digest.update(block)
    return {"path":path.relative_to(ROOT).as_posix(),"bytes":size,"sha256":digest.hexdigest()}


def main():
    status=json.loads((ROOT/"STATUS.json").read_text(encoding="utf-8-sig"))
    start=datetime.fromisoformat(status["started_at_utc"])
    records=[]
    for slug in ASSETS:
        log=LOGS/(slug+".log")
        cmd=[str(BLENDER),"--background","--factory-startup","--threads","4","--python-exit-code","1","--python",str(ROOT/"build.py"),"--","--asset",slug]
        started=now();t=time.perf_counter()
        print("PROCESS_START",slug,started.isoformat(),flush=True)
        with log.open("w",encoding="utf-8") as handle:
            result=subprocess.run(cmd,stdout=handle,stderr=subprocess.STDOUT,cwd=ROOT)
        finished=now()
        record={"asset":slug,"command":cmd,"started_at_utc":started.isoformat(),"finished_at_utc":finished.isoformat(),"started_at_kst":started.astimezone(KST).isoformat(),"finished_at_kst":finished.astimezone(KST).isoformat(),"elapsed_seconds":round(time.perf_counter()-t,3),"returncode":result.returncode,"log":log.relative_to(ROOT).as_posix()}
        records.append(record)
        write(LOGS/"process_results.json",records)
        status["process_results"]=records
        write(ROOT/"STATUS.json",status)
        print("PROCESS_FINISH",slug,"returncode",result.returncode,"seconds",record["elapsed_seconds"],flush=True)
        if result.returncode:
            status["status"]="needs_attention"
            status["blockers"]=[slug+" Blender process returned "+str(result.returncode)]
            write(ROOT/"STATUS.json",status)
            return result.returncode
    assets=[]
    for slug in ASSETS:
        paths=[ROOT/slug/(slug+ext) for ext in [".blend",".glb",".fbx"]]
        paths += [ROOT/slug/"metadata.json",ROOT/slug/"renders"/"hero.png",ROOT/slug/"renders"/"rear.png"]
        files=[inventory(p) for p in paths]
        metadata=json.loads((ROOT/slug/"metadata.json").read_text(encoding="utf-8"))
        assets.append({"asset":slug,"review_status":"deferred_by_user","files":files,"dimensions_m_from_authored_scene":metadata["bounds_from_authored_scene_m"]["dimensions"],"production_counts":metadata["counts"],"render_seconds":metadata["timing"]["render_seconds"],"source":"build.py","log":"logs/"+slug+".log"})
    finished=now()
    elapsed=(finished-start).total_seconds()
    process_seconds=sum(r["elapsed_seconds"] for r in records)
    total_bytes=sum(f["bytes"] for a in assets for f in a["files"])
    status.update({"status":"produced_unreviewed","review_status":"deferred_by_user","finished_at_utc":finished.isoformat(),"finished_at_kst":finished.astimezone(KST).isoformat(),"elapsed_seconds":round(elapsed,3),"blender_process_seconds":round(process_seconds,3),"render_seconds":round(sum(a["render_seconds"] for a in assets),3),"process_results":records,"outputs_checked":"Each of 24 required outputs exists and is nonempty. Actual return code 0 for each of four Blender processes.","validation":"Not performed; visual inspection, mesh/UV validation, reopen/reimport and reviewer agents deferred by user.","required_output_count":24,"required_output_bytes":total_bytes,"frozen":True,"blockers":[]})
    write(ROOT/"STATUS.json",status)
    lines=["# Set05 — Marine work","","Status: **produced_unreviewed**. Review: **deferred_by_user**.","",f"Production start: {start.isoformat()} UTC / {start.astimezone(KST).isoformat()} KST.",f"Production finish: {finished.isoformat()} UTC / {finished.astimezone(KST).isoformat()} KST.",f"Wall time: {elapsed:.3f} s, starting after brief/reference intake. Four Blender process durations sum to {process_seconds:.3f} s. Actual CPU render durations sum to {sum(a['render_seconds'] for a in assets):.3f} s.","","All four isolated Blender 4.5.12 processes completed with return code 0. The 24 required deliverable files exist and are nonempty. Sizes and SHA256 hashes are inventory records, not independent validation.","","| Asset | Process seconds | Authored mesh parts | Delivered files |","|---|---:|---:|---|"]
    for a,r in zip(assets,records):
        s=a["asset"]
        lines.append(f"| {s} | {r['elapsed_seconds']:.3f} | {a['production_counts']['mesh_objects']} | [{s}/]({s}/): BLEND, GLB, FBX, metadata, hero/rear PNG |")
    lines += ["","Editable named parts and edge modifiers are preserved in BLEND. ASSET and STUDIO collections are separate. Exports contain selected asset meshes and their solid PBR materials. Each component received a local UV layout during construction. Actual 960×960 Cycles CPU studio renders were produced and were not opened or inspected.","","The supplied references were used as design inputs. [Local reference mirror](REF/) remains read-only. Original geometry is authored in [build.py](build.py); the reproducible process wrapper is [run_build.py](run_build.py). Detailed process records are in [logs/process_results.json](logs/process_results.json) and [delivery_manifest.json](delivery_manifest.json).","","Limitations: visual fidelity/framing, mesh/UV quality and export roundtrips remain unreviewed. These are static solid-palette assets with no weathering maps, rig, animation, collision, LODs or physical simulation. The subdued glazing is opaque. Dimensions/counts come from the authoring scene and are production measurements only.","","The set is frozen after production. No Git operations, installations, additional agents, image generation, cross-set asset reads, shared Blender scene writes or independent review passes were performed."]
    (ROOT/"RESULT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    support=[inventory(ROOT/p) for p in ["build.py","run_build.py","README.md","RESULT.md","STATUS.json","logs/process_results.json"]]
    support += [inventory(LOGS/(slug+".log")) for slug in ASSETS]
    manifest={"set":"Set05","theme":"Marine work","status":"produced_unreviewed","review_status":"deferred_by_user","started_at_utc":start.isoformat(),"started_at_kst":start.astimezone(KST).isoformat(),"finished_at_utc":finished.isoformat(),"finished_at_kst":finished.astimezone(KST).isoformat(),"elapsed_seconds":round(elapsed,3),"blender_process_seconds":round(process_seconds,3),"required_output_count":24,"required_output_bytes":total_bytes,"process_results":records,"assets":assets,"support_files":support,"inventory_note":"Only process completion and expected nonempty output presence checked. Hashes record delivered bytes. No independent model, UV, rendering or export-roundtrip review.","frozen":True}
    write(ROOT/"delivery_manifest.json",manifest)
    print("SET_FROZEN",finished.isoformat(),"files",24,"bytes",total_bytes,flush=True)
    return 0


if __name__=="__main__":
    sys.exit(main())
