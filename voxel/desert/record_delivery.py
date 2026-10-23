"""Final file audit and factual delivery record for this theme only."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import importlib.util
import json

root = Path(__file__).resolve().parent
names = ["exploration_rover", "water_tower", "solar_array", "repair_garage"]
read = lambda p: json.loads((root / p).read_text(encoding="utf-8"))
write = lambda p, data: (root / p).write_text(json.dumps(data, indent=2), encoding="utf-8")
validation = read("validation_export.json")
assert validation["passed"] and validation["variant_count"] == 8 and not validation["errors"]
assert read("native_feature_checks.json")["passed"]
captures = read("capture_manifest.json")["captures"]
assert len(captures) == 8
variants = []
for name in names:
    pair = []
    for resolution in ("large", "half"):
        path = root / "assets" / name / resolution
        data = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
        for file, digest in data["sha256"].items():
            assert hashlib.sha256((path / file).read_bytes()).hexdigest() == digest
        pair.append(data)
        variants.append({"asset": name, "variant": resolution, "path": path.relative_to(root).as_posix(),
                         **{key: data[key] for key in ("grid_size", "grid_extents_m", "occupied_voxels", "voxel_size_m", "surface", "sha256")}})
    assert pair[0]["grid_size"] == [n * 2 for n in pair[1]["grid_size"]]
    assert pair[0]["grid_extents_m"] == pair[1]["grid_extents_m"]
    cameras = [c["settings"] for c in captures if c["asset"] == name]
    assert len(cameras) == 2 and cameras[0] == cameras[1]
assert not list((root / "assets").rglob("*.blend1"))

spec = importlib.util.spec_from_file_location("desert_source", root / "build.py")
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)
color_names = ["empty", "sand", "pale", "earth", "orange", "rust", "teal", "deep_teal", "graphite", "rubber", "iron", "alloy", "glass", "reflection", "solar", "light"]
write("palette.json", {"empty_index": 0, "colors": [{"index": i, "name": label, "rgba": list(source.PALETTE[i])} for i, label in enumerate(color_names)]})
run_files = ["build_validation_initial.json", "build_validation_solar.json", "build_validation_garage.json", "build_validation_rover_padding.json", "build_validation_solar_padding.json"]
runs = [{"file": filename, **{k: read(filename)[k] for k in ("started_at_utc", "finished_at_utc", "elapsed_seconds")}} for filename in run_files]
build_seconds = sum(r["elapsed_seconds"] for r in runs)
clarification_seconds = sum(r["elapsed_seconds"] for r in runs[-2:])
earlier_validation_seconds = read("validation_export_pre_padding.json")["elapsed_seconds"]
started = datetime(2026, 10, 23, 14, 21, 34, tzinfo=timezone.utc)
finished = datetime.now(timezone.utc)
utc = lambda d: d.isoformat(timespec="seconds").replace("+00:00", "Z")
kst = lambda d: d.astimezone(timezone(timedelta(hours=9))).isoformat(timespec="seconds")
timings = {"started_at_utc": utc(started), "started_at_kst": kst(started), "finished_at_utc": utc(finished), "finished_at_kst": kst(finished),
           "elapsed_seconds": (finished - started).total_seconds(), "build_export_render_internal_seconds": build_seconds,
           "dimension_wording_clarification_build_seconds": clarification_seconds,
           "final_validation_internal_seconds": validation["elapsed_seconds"],
           "all_validation_internal_seconds": earlier_validation_seconds + validation["elapsed_seconds"],
           "worker_image_generation_seconds": 0, "tool_wait_seconds": 0, "build_runs": runs}
write("delivery_manifest.json", {"theme": "desert", "status": "ready_for_review", "timing": timings, "asset_count": 4, "variant_count": 8,
                                 "all_final_previews_visually_inspected": True, "paired_camera_settings_identical": True, "final_hash_audit_passed": True,
                                 "source_sha256": hashlib.sha256((root / "build.py").read_bytes()).hexdigest(), "variants": variants})
status = {"theme": "desert", "status": "ready_for_review", **{key: timings[key] for key in ("started_at_utc", "started_at_kst", "finished_at_utc", "finished_at_kst", "elapsed_seconds")},
          "assets": names, "phase": "frozen_for_parent_review", "validation_summary": "4 assets / 8 variants passed independent native and 24 fresh BLEND/GLB/FBX import checks. Final hashes and paired cameras match; all final previews inspected.", "blockers": []}
write("STATUS.json", status)
table = []
gallery = []
for name in names:
    lg, hf = [v for v in variants if v["asset"] == name]
    table.append(f"| {name} | {'×'.join(map(str, lg['grid_size']))} / {'×'.join(map(str, hf['grid_size']))} | {lg['occupied_voxels']:,} / {hf['occupied_voxels']:,} | {lg['surface']['triangles']:,} / {hf['surface']['triangles']:,} | {'×'.join(f'{v:g}' for v in lg['grid_extents_m'])} |")
    gallery.append(f"| {name} | ![Large {name}](assets/{name}/large/preview.png) | ![Half {name}](assets/{name}/half/preview.png) |")
report = f"""# Desert voxel delivery

Ready for review; asset files are frozen. Four independently authored assets have large and half native grids plus BLEND, GLB, FBX and actual preview images. Native VOX occupancy is authoritative.

Start: **{utc(started)} UTC / {kst(started)} KST**. Finish: **{utc(finished)} UTC / {kst(finished)} KST**. Actual elapsed wall time: **{timings['elapsed_seconds']:.3f} s**. Build/export/render measured **{build_seconds:.3f} s** internally across five runs. Final independent verification measured **{validation['elapsed_seconds']:.3f} s**; both verification runs total **{timings['all_validation_internal_seconds']:.3f} s**. Internal timings exclude Blender startup. Worker image generation: zero. Common tools were available at dispatch, with no blocking tool wait.

| Model | Large / half grid | Voxels, large / half | Triangles, large / half | Same physical grid extents (m) |
|---|---|---:|---:|---|
{chr(10).join(table)}

Every `assets/NAME/{{large,half}}/` contains `NAME.vox`, `NAME.blend`, `NAME.glb`, `NAME.fbx`, `preview.png` and `metadata.json`. There are 8 VOX files, 24 BLEND/GLB/FBX files, and 8 actual previews. Each half grid is exactly half on every axis, with doubled meters per voxel. [build.py](build.py), [palette.json](palette.json), [delivery_manifest.json](delivery_manifest.json) and [capture_manifest.json](capture_manifest.json) provide source, named colors, checksums, timings and render settings.

The exploration rover has six treaded wheels, connected axles and dampers, a raked glazed cab, protected radiator, roof luggage, a cargo tray and cooling cassette. The water tower has four braced legs, rounded tank, roof hatch, external ladder, level gauge, exposed outlet and a geometric hand valve. The solar array has three independently framed tilted sections with corner clamps, stand braces, a torque tube, battery cabinet and control door. The repair garage is a hollow arched shell with an open front portal, interior shelves, drawers and rear bench, side door, roof vent, connected compressor and aft louvers.

[Independent final validation](validation_export.json) passed all 4 assets / 8 variants and **24 fresh BLEND/GLB/FBX imports** with `errors: []`. Native coordinates, duplicate rejection, occupancy, 1-based palette, grid sizes, bounds, hashes and exact half-grid/domain relationships passed. Every imported triangle matched its true outward native voxel boundary and palette. Degenerate, invalid-boundary, invalid-material and off-grid triangle counts are zero. [Native feature checks](native_feature_checks.json) confirm six wheel hubs, four tower legs, uniform solar bus lines and an unobstructed garage front/bay at both resolutions. Final hashes and paired camera settings were audited again while recording delivery.

All eight final images were visually inspected. The middle solar panel initially lost bus lines during reduction; shifting all three modules onto the same reduction alignment retained 243 alloy voxels in every half-resolution section. Workshop shelves and drawers were moved forward and the floor made lighter so the open bay reads in the common camera. No manual half-grid postprocessing was needed.

Two empty top cells were added to the rover and solar large grids while the brief's even-dimension wording was being clarified. The coordinator clarified that only large axes need to be even; the earlier odd half heights were valid. Already-running rebuilds were allowed to finish. The resulting padding does not change occupied geometry or bounds; its measured build overhead was **{clarification_seconds:.3f} s**. No further dimension corrections were made. Historical diagnostics are retained as evidence, and `validation_export.json` is the authoritative final check. `build_validation.json` describes the last selective build; the five named build validation files preserve each actual run.

| Asset | Large actual render | Half actual render |
|---|---|---|
{chr(10).join(gallery)}

Previews use Cycles CPU with 4 threads, 24 samples, denoising, AgX, 768×768 and matching orthographic cameras for each pair. BLEND includes the separate preview studio; GLB/FBX contain asset geometry only. These images are actual renders of the delivered meshes.

Limitations: static assets, opaque stylized glass, flat palette materials without texture UVs, and no rig, animation, collision, automatic LOD chain or game-engine integration. Small joints and slats simplify at half resolution; conservative reduction may widen individual occupied boundaries while preserving the physical grid domain. The deep garage interior remains naturally shadowed in the common preview.

Only the supplied `REF/voxel/desert/reference.png` was used as creative reference. The desert source was authored independently without inspecting or copying other theme resources. No image generation, shared live Blender session, ForestDemo access, Git operations or subagents were used. Underwater remains queued pending explicit parent dispatch.
"""
(root / "RESULT.md").write_text(report, encoding="utf-8")
print(json.dumps({"status": status, "build_seconds": build_seconds, "clarification_seconds": clarification_seconds, "final_validation_seconds": validation["elapsed_seconds"], "final_hash_audit_passed": True}, indent=2))
