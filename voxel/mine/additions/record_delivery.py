from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib
root=Path(__file__).resolve().parent
def load(p): return json.loads((root/p).read_text(encoding="utf-8-sig"))
def save(p,v): (root/p).write_text(json.dumps(v,indent=2),encoding="utf-8")
validation=load("validation_export.json")
features=load("feature_validation.json")
build=load("build_timing.json")
checks=load("check_timings.json")
assert validation["passed"] and validation["asset_count"]==1 and validation["variant_count"]==2
assert features["passed"] and all(p["exit_code"]==0 for p in [build]+checks)
m={v:load(f"assets/haul_truck/{v}/metadata.json") for v in ("large","half")}
for variant,meta in m.items():
    for name,digest in meta["sha256"].items():
        assert hashlib.sha256((root/"assets/haul_truck"/variant/name).read_bytes()).hexdigest()==digest
assert len(load("capture_manifest.json")["captures"])==2
start=datetime.fromisoformat("2026-10-23T15:41:35+00:00")
finish=datetime.now(timezone.utc)
kst=timezone(timedelta(hours=9))
wall=(finish-start).total_seconds()
save("palette.json",{"empty_index":0,"source":"Permitted mine palette continuity; geometry independently authored.","rgba":m["large"]["palette"]})
save("visual_review.json",{"reviewed_at_utc":finish.isoformat(),"actual_previews_inspected":2,"observations":"Both actual previews clearly show the deep empty bed, six-wheel heavy truck layout, offset cab, separate engine deck, canopy, external ribs and hoist cylinder. No visual correction was needed.","remaining_functional_defects":[]})
save("STATUS.json",{"theme":"mine","addition":"haul_truck","status":"ready_for_review","phase":"submitted_frozen","started_at_utc":start.isoformat(),"started_at_kst":start.astimezone(kst).isoformat(),"finished_at_utc":finish.isoformat(),"finished_at_kst":finish.astimezone(kst).isoformat(),"elapsed_seconds":wall,"asset_count":1,"variant_count":2,"validation_summary":"2 native variants, 6 fresh BLEND/GLB/FBX inspections and 10 native feature checks passed; both actual previews inspected, including empty half-resolution bed.","build_seconds":build["elapsed_seconds"],"validation_process_seconds":sum(p["elapsed_seconds"] for p in checks),"image_generation_seconds":0,"blockers":[],"phase_b_started":False})
lg,sm=m["large"],m["half"]
report=f"""# Mine haul truck addition

One original `haul_truck` in large and half native grids is ready for review and frozen on submission. Accepted original mine assets and the factory addition remain unchanged. Construction and all phase B work remain unstarted.

## Actual timing

- Start UTC: {start.isoformat()}; KST: {start.astimezone(kst).isoformat()}.
- Finish UTC: {finish.isoformat()}; KST: {finish.astimezone(kst).isoformat()}.
- Elapsed wall time: {wall:.3f} seconds, including authoring, visual review and documentation.
- Single build/export/render process: {build['elapsed_seconds']:.3f} seconds.
- Saved-native feature checks: {checks[0]['elapsed_seconds']:.3f} seconds.
- Independent native/format verification process: {checks[1]['elapsed_seconds']:.3f} seconds.
- Image generation: none (0 seconds). No rebuilds, optional views or polish passes.

Process timings include startup. Every Blender process used background factory-startup mode, four threads and `--python-exit-code 1`.

## Asset and native statistics

| Variant | Grid | Cell size (m) | Occupied voxels | Triangles |
|---|---|---:|---:|---:|
| Large | 104 x 128 x 96 | 0.055 | {lg['occupied_voxels']:,} | {lg['surface']['triangles']:,} |
| Half | 52 x 64 x 48 | 0.11 | {sm['occupied_voxels']:,} | {sm['surface']['triangles']:,} |

Exact physical grid extents are 5.72 x 7.04 x 5.28 m at both sizes. All large axes are even and longest 128. Half occupancy independently divides every axis by two and doubles cell size. Native uint8 VOX is authoritative, with index 0 empty and visible indices 1+. Conservative occupied-bound expansion by one large cell is permitted. No hand-edited half grid or scaled-mesh substitute was used.

The six-wheel off-road ore hauler includes huge treaded tires, front offset cab and engine deck, a deep EMPTY tapered dump body, thick rim, cab canopy, reinforcing ribs, rear hinge, two external hoist cylinders, access ladder and purposeful service grilles. Its mine palette is preserved by permission; all geometry was independently authored.

## Delivered paths

- `build.py`: pure `make_assets()` returning only this asset, using the absolute parent generic `_tools` path.
- `assets/haul_truck/{{large,half}}/`: VOX, BLEND, GLB, FBX, actual `preview.png`, and metadata.
- `palette.json`, `capture_manifest.json`, `build_validation.json`, `validation_export.json`, `feature_validation.json`, `visual_review.json`, timing JSON and logs.
- `check_features.py`, `STATUS.json`, this report and the bookkeeping script.

GLB/FBX contain only exposed voxel asset surfaces. BLEND separates ASSET from its preview STUDIO; the studio floor/camera/lights are excluded from native occupancy and exchange exports.

## Evidence

Independent verification passed both native grids and all six fresh BLEND/GLB/FBX inspections. It checked native count, palette, coordinate uniqueness/range, occupancy and file hashes; exact halving and physical grid sizes; finite coordinates, grid alignment, nonzero triangles, outward occupied-to-empty boundary surfaces, correct materials, bounds, triangle count and area. No studio objects entered GLB/FBX.

Five semantic checks passed per reopened native resolution: a deep empty bed region, six occupied wheel centers, bed floor/rim, offset cabin window, and hinge/hoist. The empty-region test examined {features['records'][0]['empty_bed_probe_voxels']:,} large-grid cells and {features['records'][1]['empty_bed_probe_voxels']:,} half-grid cells, all empty. Both actual previews were inspected and show the empty bed clearly; no correction was required. The parent also reported personal preview review and independent format verification passing before this record was finalized.

Capture settings: matched orthographic cameras, 768 x 768, Cycles CPU, four threads, 24 samples, AgX and denoising. Reference imagery is never used as rendered evidence.

## Limitations and provenance

Static colored voxel model only: no dump articulation/animation, rig, collision, LOD chain or engine integration. Cab glass is opaque stylized color. Palette materials require no texture UVs; no image textures were used. Tire lugs, ribs and small grille/bolt details simplify at half resolution. Mechanics depict useful forms rather than simulate machinery.

Inputs were the assigned `REF/voxel/mine/additions/reference.png`, permitted original mine palette, expansion/common brief/API and parent-owned generic utilities. No other creative theme source, original asset modification, ForestDemo, Git, image generation, installation, other agents or shared live Blender session was used.
"""
(root/"RESULT.md").write_text(report,encoding="utf-8")
print(json.dumps({"status":"ready_for_review","finished_at_utc":finish.isoformat(),"elapsed_seconds":wall,"variants":2,"native_and_export_validation":validation["passed"]},indent=2))
