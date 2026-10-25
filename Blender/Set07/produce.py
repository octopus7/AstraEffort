"""Launch four isolated production processes and record return codes/file inventory.

This wrapper deliberately performs no scene/model/UV/image validation and never
opens generated renders or reimports any exported asset.
"""
import json
import sys
import time
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parent
BLENDER = Path("C:/Program Files/Blender Foundation/Blender 4.5/blender.exe")
SLUGS = ["rail_inspection_trolley", "side_loading_freight_shuttle",
         "barrel_roof_freight_station", "mechanical_signal_house"]
LABELS = ["Rail inspection trolley", "Side-loading freight shuttle",
          "Barrel-roof freight station", "Mechanical signal house"]
KST = timezone(timedelta(hours=9))
STARTED = datetime.fromisoformat("2026-10-25T06:02:52+00:00")
LOGS = ROOT / "logs"
LOGS.mkdir(exist_ok=True)
RECORD = ROOT / "process_records.json"
records = json.loads(RECORD.read_text(encoding="utf-8")) if RECORD.exists() else []


def expected(slug):
    base = ROOT / slug
    return [base / (slug + ext) for ext in (".blend", ".glb", ".fbx")] + [
        base / "metadata.json", base / "renders" / "hero.png", base / "renders" / "rear.png"]


def inventory(path):
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def status(state, completed, active=None, end=None, errors=None):
    stamp = datetime.now(timezone.utc)
    data = {"set": "Set07", "theme": "Rail freight", "status": state,
            "review_status": "deferred_by_user", "started_at_utc": STARTED.isoformat(),
            "started_at_kst": STARTED.astimezone(KST).isoformat(),
            "finished_at_utc": end.isoformat() if end else None,
            "finished_at_kst": end.astimezone(KST).isoformat() if end else None,
            "elapsed_seconds": ((end or stamp) - STARTED).total_seconds(),
            "completed_assets": completed, "active_asset": active,
            "successful_blender_processes": sum(r["returncode"] == 0 for r in records),
            "process_seconds": sum(r["elapsed_seconds"] for r in records),
            "blockers": errors or [],
            "checks": "Only actual subprocess return codes and required nonempty file presence. SHA256 inventory is not model validation.",
            "deferred": ["visual inspection", "BLEND reopen", "GLB/FBX reimport", "geometry/UV validation", "reviewer agents"]}
    (ROOT / "STATUS.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


completed = []
for slug in SLUGS:
    prior = [r for r in records if r["asset"] == slug and r["returncode"] == 0]
    if prior and all(p.is_file() and p.stat().st_size > 0 for p in expected(slug)):
        completed.append(slug)
        print("ALREADY_PRODUCED", slug, flush=True)
        continue
    status("working", completed, active=slug)
    attempt = 1 + sum(r["asset"] == slug for r in records)
    logpath = LOGS / f"{slug}.attempt{attempt:02}.log"
    cmd = [str(BLENDER), "--background", "--factory-startup", "--threads", "4",
           "--python-exit-code", "1", "--python", str(ROOT / "build.py"), "--", slug]
    begin = datetime.now(timezone.utc)
    perf = time.perf_counter()
    print("START", slug, begin.isoformat(), flush=True)
    with logpath.open("w", encoding="utf-8") as log:
        result = subprocess.run(cmd, cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT, check=False)
    end = datetime.now(timezone.utc)
    rec = {"asset": slug, "attempt": attempt, "command": cmd,
           "started_at_utc": begin.isoformat(), "finished_at_utc": end.isoformat(),
           "started_at_kst": begin.astimezone(KST).isoformat(), "finished_at_kst": end.astimezone(KST).isoformat(),
           "elapsed_seconds": time.perf_counter() - perf, "returncode": result.returncode,
           "log": logpath.relative_to(ROOT).as_posix()}
    records.append(rec)
    RECORD.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print("EXIT", slug, result.returncode, round(rec["elapsed_seconds"], 3), flush=True)
    if result.returncode != 0:
        status("production_failed", completed, errors=[f"{slug}: Blender returned {result.returncode}; see {rec['log']}"])
        sys.exit(result.returncode if 0 < result.returncode < 256 else 1)
    missing = [p.relative_to(ROOT).as_posix() for p in expected(slug)
               if not p.is_file() or p.stat().st_size <= 0]
    if missing:
        status("production_failed", completed, errors=["Missing/empty deliverables: " + ", ".join(missing)])
        raise RuntimeError("Missing/empty expected production files: " + ", ".join(missing))
    completed.append(slug)
    status("working", completed)

finish = datetime.now(timezone.utc)
assets = []
for slug, label in zip(SLUGS, LABELS):
    metadata = json.loads((ROOT / slug / "metadata.json").read_text(encoding="utf-8"))
    assets.append({"asset": slug, "label": label, "status": "produced_unreviewed",
                   "review_status": "deferred_by_user", "files": [inventory(p) for p in expected(slug)],
                   "dimensions_m_at_authoring": metadata["dimensions_m_at_authoring"],
                   "reference": f"REF/{slug}.png", "prompt": f"REF/{slug}.prompt.txt"})
successful = [next(r for r in reversed(records) if r["asset"] == slug and r["returncode"] == 0) for slug in SLUGS]
manifest = {"set": "Set07", "theme": "Rail freight", "status": "produced_unreviewed",
            "review_status": "deferred_by_user", "started_at_utc": STARTED.isoformat(),
            "started_at_kst": STARTED.astimezone(KST).isoformat(),
            "finished_at_utc": finish.isoformat(), "finished_at_kst": finish.astimezone(KST).isoformat(),
            "elapsed_seconds": (finish - STARTED).total_seconds(),
            "blender_process_seconds": sum(r["elapsed_seconds"] for r in records),
            "successful_processes": successful, "all_process_attempts": records,
            "file_check": "Each expected file exists and is nonempty. Hashes are inventory only.",
            "assets": assets,
            "production_sources_and_logs": [inventory(p) for p in [ROOT / "build.py", ROOT / "produce.py", RECORD] +
                                             sorted(LOGS.glob("*.log"))],
            "limitations": ["No generated preview was opened.", "No model/geometry/UV checks, reopen, or export reimport was performed.",
                            "No reviewer agent was used. All review remains deferred by user instruction."]}
(ROOT / "delivery_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

rows = []
for a in assets:
    slug = a["asset"]
    dims = " × ".join(f"{v:.2f}" for v in a["dimensions_m_at_authoring"])
    rows.append(f"| {a['label']} | [Reference](REF/{slug}.png) · [Prompt](REF/{slug}.prompt.txt) | "
                f"[BLEND]({slug}/{slug}.blend) · [GLB]({slug}/{slug}.glb) · [FBX]({slug}/{slug}.fbx) | "
                f"[Hero]({slug}/renders/hero.png) · [Rear]({slug}/renders/rear.png) | {dims} m |")
readme = """# Set07 · Rail freight

Four original ordinary rounded mesh game assets, authored from this set's supplied references. Brick red, warm ivory, graphite and restrained brass form a shared solid PBR palette. Named editable parts remain grouped by their mechanical or architectural function.

Status: **produced_unreviewed**. Review: **deferred_by_user**. The linked preview files are actual 1024 × 1024 Cycles studio renders, generated without opening them for inspection.

| Asset | Local reference | Editable / geometry exports | Actual renders | Authoring dimensions X × Y × Z |
|---|---|---|---|---|
""" + "\n".join(rows) + """

The rail trolley has four flanged steel wheels, exposed axles, an open protective cab, steps, front inspection sensors and a rear toolbox. The six-wheel shuttle carries a secured container and has a side-facing hydraulic mast with two blunt forks. The station includes a raised loading deck, attached ramp, open cargo doorway, column-supported canopy and side office under barrel roofs. The signal house includes an upper glazed room, external stairs, an open mechanical linkage cabinet and a short semaphore.

Each BLEND has separate `ASSET` and `STUDIO` collections. GLB/FBX exports select only asset meshes; studio floor, cameras and lights are excluded. Bevel and weighted-normal modifiers remain editable in BLEND and are evaluated on export. Primitive side/cap UVs, planar component islands and authored tube/roof strips provide per-component surface coordinates. Glazing uses a solid muted blue-gray PBR material. No rigging, animation, collision or LOD deliverables were requested.

[Production source](build.py) · [Process wrapper](produce.py) · [Process records](process_records.json) · [Delivery inventory](delivery_manifest.json) · [Result and timing](RESULT.md) · [Status](STATUS.json) · [Local reference generation record](REF/generation_manifest.json)

Reproduction on the assigned machine: run the bundled Blender Python with `-X utf8 produce.py`. The wrapper launches a separate Blender 4.5.12 background process for each asset using `--factory-startup --threads 4 --python-exit-code 1`. A completed asset is skipped when its successful process record and nonempty required files already exist.

Only subprocess return codes and expected nonempty file presence were checked. SHA256 values are an inventory, not validation. Visual inspection, model/UV/geometry validation, fresh BLEND reopen and export roundtrips are deliberately deferred by the user. No preview inspection or reviewer agent was used. Set07 is frozen after production; Git integration belongs to the coordinating chat.
"""
(ROOT / "README.md").write_text(readme, encoding="utf-8")
duration = (finish - STARTED).total_seconds()
proc = sum(r["elapsed_seconds"] for r in records)
result_text = f"""# Set07 production record

Status: **produced_unreviewed** · review_status: **deferred_by_user**.

- Start UTC: {STARTED.isoformat()}
- Start KST: {STARTED.astimezone(KST).isoformat()}
- Finish UTC: {finish.isoformat()}
- Finish KST: {finish.astimezone(KST).isoformat()}
- Wall time: {duration:.3f} seconds, including reference reading, geometry/source authoring, export and rendering.
- Blender subprocess time, summed across actual attempts: {proc:.3f} seconds.
- Successful final Blender subprocess records: {len(successful)}, all return code 0.
- Required deliverables: 24 nonempty files across four asset folders; exact paths, byte sizes and SHA256 inventory are in [delivery_manifest.json](delivery_manifest.json).

The four models are `rail_inspection_trolley`, `side_loading_freight_shuttle`, `barrel_roof_freight_station` and `mechanical_signal_house`. Each folder contains editable named-part BLEND, geometry-only GLB/FBX, metadata and actual hero/rear PNG renders. [README.md](README.md) links all outputs and local references.

Only actual process completion and required nonempty-file presence were checked. Dimensions in metadata are production measurements used to frame the studio, not independent validation. Images were rendered but never opened. Visual inspection, BLEND reopen, GLB/FBX roundtrips and model/UV/geometry validation remain deferred by explicit user instruction.

Known limits: stylized opaque glazing; no rigging, animation, collisions or LODs; visual, shading, UV and export quality await later review. Each asset uses original independently authored polygon geometry and a solid PBR palette. No image generation, other-set models, voxel resources or ForestDemo creative assets were used. No shared live Blender scene, installations, reviewer agents or Git operations were used.

External references: only the main-provided [Set07 references](REF/generation_manifest.json) and their adjacent prompts. The worker did not create or alter these reference files.

Production is frozen; awaiting the coordinating chat's integration and any next explicit assignment.
"""
(ROOT / "RESULT.md").write_text(result_text, encoding="utf-8")
status("produced_unreviewed", completed, end=finish)
print("SET07_FROZEN", finish.isoformat(), "wall_seconds", round(duration, 3),
      "blender_seconds", round(proc, 3), "successful_processes", len(successful), flush=True)
