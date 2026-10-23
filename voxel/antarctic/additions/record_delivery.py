"""Audit the ice-core addition and write its final scoped delivery records."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import importlib.util
import json

root = Path(__file__).resolve().parent
load = lambda name: json.loads((root / name).read_text(encoding="utf-8"))
save = lambda name, value: (root / name).write_text(json.dumps(value, indent=2), encoding="utf-8")
validation, build = load("validation_export.json"), load("build_validation.json")
assert validation["passed"] and validation["asset_count"] == 1 and validation["variant_count"] == 2 and not validation["errors"]
assert build["passed"] and load("native_feature_checks.json")["passed"]
for record in validation["records"]:
    assert record["passed"] and len(record["imports"]) == 3
    for metrics in record["imports"].values():
        assert all(metrics[k] == 0 for k in ("degenerate_triangles", "invalid_boundary_triangles", "invalid_material_triangles", "offgrid_coordinates"))
variants = []
for size in ("large", "half"):
    directory = root / "assets" / "ice_core_drill" / size
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    for filename, digest in metadata["sha256"].items():
        assert hashlib.sha256((directory / filename).read_bytes()).hexdigest() == digest
    variants.append(metadata)
large, half = variants
assert large["grid_size"] == [v * 2 for v in half["grid_size"]]
assert max(large["grid_size"]) == 128 and all(v % 2 == 0 for v in large["grid_size"])
assert large["grid_extents_m"] == half["grid_extents_m"]
captures = load("capture_manifest.json")["captures"]
assert len(captures) == 2 and captures[0]["settings"] == captures[1]["settings"]
spec = importlib.util.spec_from_file_location("drill_source", root / "build.py")
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)
labels = ["empty", "ivory", "snow", "shadow", "navy", "blue", "dark", "steel", "silver", "orange", "amber", "glass", "sky", "black", "lamp", "slate"]
save("palette.json", {"source": "Authorized accepted Antarctic theme palette", "empty_index": 0,
                      "colors": [{"index": i, "name": label, "rgba": list(source.PALETTE[i])} for i, label in enumerate(labels)]})
start = datetime(2026, 10, 23, 15, 33, 44, tzinfo=timezone.utc)
finish = datetime.now(timezone.utc)
utc = lambda stamp: stamp.isoformat(timespec="seconds").replace("+00:00", "Z")
kst = lambda stamp: stamp.astimezone(timezone(timedelta(hours=9))).isoformat(timespec="seconds")
timing = {"started_at_utc": utc(start), "started_at_kst": kst(start), "finished_at_utc": utc(finish), "finished_at_kst": kst(finish),
          "elapsed_seconds": (finish - start).total_seconds(), "build_export_render_internal_seconds": build["elapsed_seconds"],
          "validation_internal_seconds": validation["elapsed_seconds"], "validation_command_wall_seconds": 3.2473007,
          "worker_image_generation_seconds": 0, "blocking_tool_wait_seconds": 0, "build_runs": 1,
          "timing_note": "Pipeline intervals exclude Blender startup. Validation command wall time is the execution tool's measured duration. Full build command wall time was not separately timed."}
save("delivery_manifest.json", {"theme": "antarctic", "scope": "additions", "status": "ready_for_review", "timing": timing,
                               "asset_count": 1, "variant_count": 2, "both_final_previews_inspected": True,
                               "paired_camera_settings_identical": True, "final_hash_audit_passed": True,
                               "source_sha256": hashlib.sha256((root / "build.py").read_bytes()).hexdigest(),
                               "variants": [{key: metadata[key] for key in ("asset", "variant", "grid_size", "grid_extents_m", "voxel_size_m", "occupied_voxels", "surface", "sha256")} for metadata in variants]})
status = {"theme": "antarctic", "scope": "additions", "status": "ready_for_review",
          **{key: timing[key] for key in ("started_at_utc", "started_at_kst", "finished_at_utc", "finished_at_kst", "elapsed_seconds")},
          "phase": "frozen_for_parent_review", "assets": ["ice_core_drill"],
          "validation_summary": "Both native sizes and six fresh BLEND/GLB/FBX imports passed. Open deck clearance, barrel continuity, two runners, four stabilizers and three separated sample cylinders checked at both sizes. Both final actual previews inspected; hashes and cameras match.", "blockers": []}
save("STATUS.json", status)
rows = "\n".join(f"| {m['variant']} | {'×'.join(map(str, m['grid_size']))} | {m['voxel_size_m']:g} | {m['occupied_voxels']:,} | {m['surface']['triangles']:,} |" for m in variants)
report = f"""# Antarctic addition: ice core drill

Ready for parent review and frozen. One original sled-mounted scientific core rig is delivered at two true voxel resolutions. The accepted original Antarctic models were not modified.

Actual start: **{utc(start)} UTC / {kst(start)} KST**. Actual finish: **{utc(finish)} UTC / {kst(finish)} KST**. Elapsed wall time: **{timing['elapsed_seconds']:.3f} seconds**. The single Blender build/export/render pipeline measured **{build['elapsed_seconds']:.3f} seconds**; independent validation measured **{validation['elapsed_seconds']:.3f} seconds** internally, and its full command measured **3.247 seconds**. Pipeline times exclude Blender startup; the full build command interval was not separately timed. No worker image generation or blocking tool wait occurred.

| Size | Native grid | Meters per voxel | Occupied voxels | Triangles |
|---|---|---:|---:|---:|
{rows}

Both grids occupy the same **{' × '.join(f'{v:g}' for v in large['grid_extents_m'])} m** physical domain. Half dimensions are exactly divided by two and cell size doubles. Each `assets/ice_core_drill/{{large,half}}/` contains `ice_core_drill.vox`, `.blend`, `.glb`, `.fbx`, `preview.png` and `metadata.json`. Native VOX is authoritative. Source is [build.py](build.py); the authorized Antarctic color palette is recorded in [palette.json](palette.json). [delivery_manifest.json](delivery_manifest.json) records final hashes and timings.

The rig has two rounded sled runners, four deployed stabilizers, a platform with a genuinely open coring slot, a blunt vertical barrel passing through it, two mast columns and steel guide rails, a top winch, orange sliding drive, side power cabinet and three capped sample cylinders. Split guard rails preserve access to the coring area. Rear braces, supply lines, couplers and a tow eye provide useful secondary detail.

[Independent native/export validation](validation_export.json) passed both variants and all **six fresh BLEND/GLB/FBX imports**, with `errors: []`. Occupancy, 1-based palette, coordinates, duplicate rejection, bounds, file hashes, exact half sizes and shared physical grid extents passed. Imported surfaces match occupied-cell boundaries with outward orientation and correct materials. Degenerate, invalid-boundary, invalid-material and off-grid triangle counts are zero. [Native mechanism checks](native_feature_checks.json) verify through-deck air beside the barrel, the barrel above/below the deck, both runners, four stabilizers and three sample cylinders separated by air at both sizes.

Both actual final previews were visually inspected. The 64-cell model preserves the opening and principal mechanisms. The first build passed; no geometry fix, optional polish cycle or manual half-grid correction was needed. A final audit confirmed delivered hashes and identical paired camera settings.

| Large actual render | Half actual render |
|---|---|
| ![Large ice core drill](assets/ice_core_drill/large/preview.png) | ![Half ice core drill](assets/ice_core_drill/half/preview.png) |

Captures are actual Blender renders: Cycles CPU, 4 threads, 24 samples, denoising, AgX, 768×768 and paired orthographic cameras. [capture_manifest.json](capture_manifest.json) contains the camera settings, actual timestamps and hashes. BLEND includes a separate studio collection; GLB/FBX contain only asset geometry.

Limitations: static deployed pose, solid opaque palette materials, no rig, animation, collision, LOD chain, game-engine integration or simulated core extraction. Flat-color materials require no image textures or UV layout. Minor grate holes and windings simplify at half resolution; conservative boundary growth is permitted while the grid domain remains unchanged.

Creative input was limited to `REF/voxel/antarctic/additions/reference.png`, inspected before authoring, and the authorized original Antarctic palette. Geometry was authored independently inside this addition root. No previous creative scripts/assets, other themes, ForestDemo, shared Blender scene, image generation, Git operations, installations or other agents were used. Awaiting phase-A acceptance and explicit dispatch before any new theme.
"""
(root / "RESULT.md").write_text(report, encoding="utf-8")
print(json.dumps({"status": status, "build_seconds": build["elapsed_seconds"], "validation_seconds": validation["elapsed_seconds"], "final_hash_audit_passed": True}, indent=2))
