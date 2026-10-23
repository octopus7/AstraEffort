from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json

root = Path(__file__).resolve().parent
def load(p): return json.loads((root/p).read_text(encoding="utf-8-sig"))
def save(p,v): (root/p).write_text(json.dumps(v,indent=2),encoding="utf-8")
validation=load("validation_export.json")
features=load("feature_validation.json")
build=load("build_timing.json")
checks=load("check_timings.json")
assert validation["passed"] and validation["asset_count"]==1 and validation["variant_count"]==2
assert features["passed"] and all(x["exit_code"]==0 for x in [build]+checks)
metadata={v:load(f"assets/robot_workcell/{v}/metadata.json") for v in ("large","half")}
for variant,m in metadata.items():
    for name,digest in m["sha256"].items():
        assert hashlib.sha256((root/"assets/robot_workcell"/variant/name).read_bytes()).hexdigest()==digest
capture=load("capture_manifest.json")
assert len(capture["captures"])==2
started=datetime.fromisoformat("2026-10-23T15:32:45+00:00")
finished=datetime.now(timezone.utc)
kst=timezone(timedelta(hours=9))
wall=(finished-started).total_seconds()
save("palette.json",{"empty_index":0,"source":"Permitted existing factory palette, copied for continuity; all geometry independently authored.","rgba":metadata["large"]["palette"]})
save("visual_review.json",{"reviewed_at_utc":finished.isoformat(),"actual_previews_inspected":2,"observations":"Both sizes show robust round shoulder/elbow/wrist housings, separated blunt fingers hovering over the bored workpiece, a supported fixture table, pedestal, compact fork-pocket skid and independent side console. No functional defect requiring rebuilding observed.","remaining_defects":[]})
save("STATUS.json",{"theme":"factory","addition":"robot_workcell","status":"ready_for_review","phase":"submitted_frozen","started_at_utc":started.isoformat(),"started_at_kst":started.astimezone(kst).isoformat(),"finished_at_utc":finished.isoformat(),"finished_at_kst":finished.astimezone(kst).isoformat(),"elapsed_seconds":wall,"asset_count":1,"variant_count":2,"validation_summary":"2 native variants and 6 fresh BLEND/GLB/FBX inspections passed; 10 native feature checks passed; both actual previews inspected.","build_seconds":build["elapsed_seconds"],"validation_process_seconds":sum(x["elapsed_seconds"] for x in checks),"image_generation_seconds":0,"blockers":[],"next_assignment_started":False})
lg,half=metadata["large"],metadata["half"]
report=f"""# Factory robot workcell addition

One original `robot_workcell`, in two native voxel resolutions, is ready for parent review and frozen on submission. Existing accepted factory assets were not modified. The mine addition and phase B remain unstarted.

## Actual time

- Start UTC: {started.isoformat()}; KST: {started.astimezone(kst).isoformat()}.
- Finish UTC: {finished.isoformat()}; KST: {finished.astimezone(kst).isoformat()}.
- Elapsed wall time: {wall:.3f} seconds, including authoring, inspection and documentation.
- One build/export/render process: {build['elapsed_seconds']:.3f} seconds.
- Native feature check process: {checks[0]['elapsed_seconds']:.3f} seconds.
- Independent format verification process: {checks[1]['elapsed_seconds']:.3f} seconds.
- Image generation: none (0 seconds). No rebuild, optional view or polish cycle.

All Blender processes ran isolated, background, factory-startup, four threads and `--python-exit-code 1`. Process times include startup.

## Model and deliverables

| Variant | Grid | Cell size (m) | Occupied voxels | Triangles |
|---|---|---:|---:|---:|
| Large | 112 x 104 x 128 | 0.04 | {lg['occupied_voxels']:,} | {lg['surface']['triangles']:,} |
| Half | 56 x 52 x 64 | 0.08 | {half['occupied_voxels']:,} | {half['surface']['triangles']:,} |

Both physical grid extents are 4.48 x 4.16 x 5.12 m. Native uint8 VOX is authoritative, index 0 empty and visible palette indices 1+. Half occupancy independently reduces each axis by exactly two, doubles cell size and preserves physical grid size; it is not a scaled large mesh. Conservative boundary expansion up to one large cell is permitted. No manual half-grid correction was used.

`assets/robot_workcell/{{large,half}}/` contains named VOX, BLEND, GLB, FBX, `preview.png` and `metadata.json`. `build.py` provides pure `make_assets()` returning one asset, with an absolute import path to the parent-owned generic utilities. `palette.json`, `capture_manifest.json`, `build_validation.json`, `validation_export.json`, `feature_validation.json`, `visual_review.json`, logs and actual timing JSON are included.

The model has round shoulder/elbow/wrist housings, two blunt gripper fingers separated over a bored workpiece, four-legged fixture table, rotary pedestal, fork-pocket machine skid, cable routing and cream operator console. The permitted factory palette was used for continuity; geometry was newly authored.

## Validation and visual review

Independent native parsing and all six fresh BLEND/GLB/FBX asset inspections passed. Checks covered native grid/count/palette/coordinate/occupancy hashes, exact halving and physical grid sizes, file hashes, finite coordinates, nonzero triangles, grid alignment, correct palette assignment, outward exact occupied-to-empty boundaries, bounds, triangle counts and exposed surface area. GLB/FBX contain only the asset surface mesh with no studio objects.

Five semantic checks passed on each reopened resolution: empty gripper gap, both blunt finger pads, three joint centers, empty workpiece bore, and fixture-table/console occupancy. Both actual primary previews were inspected; all required mechanisms remain readable and no functional correction was needed. Capture settings: matching orthographic cameras, 768 x 768, Cycles CPU, four threads, 24 samples, AgX, denoising. Generated reference imagery is design input only.

## Limits and provenance

Static colored voxel surface mesh; no rig, animation, collision, LOD chain or engine integration. Flat palette materials have no image textures/UV requirement. Small bolt details and the workpiece bore become chunkier at half resolution. The skid is part of this machine assembly. BLEND retains separate ASSET/STUDIO collections for preview reproduction; studio elements do not enter native VOX or GLB/FBX.

Inputs: `voxel/EXPANSION_PLAN.md`, parent generic `_tools/API.md` and utilities, permitted original factory `palette.json`, and `REF/voxel/factory/additions/reference.png`. No other creative theme resources, accepted original model source, ForestDemo, Git, installations, image generation, other agents or shared live Blender were used.
"""
(root/"RESULT.md").write_text(report,encoding="utf-8")
print(json.dumps({"status":"ready_for_review","finished_at_utc":finished.isoformat(),"elapsed_seconds":wall,"native_variants":2,"format_inspections":6},indent=2))
