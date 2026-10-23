"""Audit this theme's completed artifacts and record its actual delivery time."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import importlib.util
import json

root = Path(__file__).resolve().parent
slugs = ["submersible", "dome_laboratory", "connecting_tunnel", "seabed_miner", "docking_station"]
load = lambda name: json.loads((root / name).read_text(encoding="utf-8"))
save = lambda name, value: (root / name).write_text(json.dumps(value, indent=2), encoding="utf-8")
build_report, validation = load("build_validation.json"), load("validation_export.json")
assert build_report["passed"] and len(build_report["assets"]) == 5
assert validation["passed"] and validation["asset_count"] == 5 and validation["variant_count"] == 10 and not validation["errors"]
assert load("native_feature_checks.json")["passed"]
for entry in validation["records"]:
    assert entry["passed"] and len(entry["imports"]) == 3
    for result in entry["imports"].values():
        assert all(result[key] == 0 for key in ("degenerate_triangles", "invalid_boundary_triangles", "invalid_material_triangles", "offgrid_coordinates"))
captures = load("capture_manifest.json")["captures"]
assert len(captures) == 10
assets = []
for slug in slugs:
    sizes = []
    for variant in ("large", "half"):
        folder = root / "assets" / slug / variant
        metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
        for filename, digest in metadata["sha256"].items():
            assert hashlib.sha256((folder / filename).read_bytes()).hexdigest() == digest
        sizes.append(metadata)
    assert all(n % 2 == 0 for n in sizes[0]["grid_size"]) and max(sizes[0]["grid_size"]) == 128
    assert sizes[0]["grid_size"] == [n * 2 for n in sizes[1]["grid_size"]]
    assert sizes[0]["grid_extents_m"] == sizes[1]["grid_extents_m"]
    cameras = [c["settings"] for c in captures if c["asset"] == slug]
    assert len(cameras) == 2 and cameras[0] == cameras[1]
    assets.append({"asset": slug, "large": sizes[0], "half": sizes[1]})

module_spec = importlib.util.spec_from_file_location("underwater_source", root / "build.py")
source = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(source)
labels = ["void", "ivory", "cream", "shade", "petrol", "blue", "glass", "reflection", "ochre", "gold", "graphite", "iron", "silver", "dark_glass", "lamp", "pipe"]
save("palette.json", {"index_zero_empty": True, "all_used_colors_opaque": True, "entries": [{"index": i, "name": name, "rgba": list(source.PALETTE[i])} for i, name in enumerate(labels)]})
started = datetime(2026, 10, 23, 14, 43, 32, tzinfo=timezone.utc)
finished = datetime.now(timezone.utc)
utc_string = lambda value: value.isoformat(timespec="seconds").replace("+00:00", "Z")
kst_string = lambda value: value.astimezone(timezone(timedelta(hours=9))).isoformat(timespec="seconds")
time_record = {"started_at_utc": utc_string(started), "started_at_kst": kst_string(started), "finished_at_utc": utc_string(finished), "finished_at_kst": kst_string(finished),
               "elapsed_seconds": (finished - started).total_seconds(), "build_export_render_internal_seconds": build_report["elapsed_seconds"],
               "validation_internal_seconds": validation["elapsed_seconds"], "build_runs": 1, "worker_image_generation_seconds": 0, "blocking_tool_wait_seconds": 0}
manifest = {"theme": "underwater", "status": "ready_for_review", "timing": time_record, "asset_count": 5, "variant_count": 10,
            "all_ten_final_previews_inspected": True, "paired_camera_settings_identical": True, "final_file_hash_audit_passed": True,
            "source_sha256": hashlib.sha256((root / "build.py").read_bytes()).hexdigest(),
            "variants": [{"asset": a["asset"], "variant": size, **{key: a[size][key] for key in ("grid_size", "grid_extents_m", "occupied_voxels", "voxel_size_m", "surface", "sha256")}} for a in assets for size in ("large", "half")]}
save("delivery_manifest.json", manifest)
status = {"theme": "underwater", "status": "ready_for_review", **{key: time_record[key] for key in ("started_at_utc", "started_at_kst", "finished_at_utc", "finished_at_kst", "elapsed_seconds")},
          "phase": "frozen_for_parent_review", "assets": slugs,
          "validation_summary": "5 assets / 10 variants passed native verification, mechanism/opening checks and 30 fresh BLEND/GLB/FBX imports. All ten final previews inspected. Final hashes and paired cameras match.", "blockers": []}
save("STATUS.json", status)
rows, pictures = [], []
for entry in assets:
    slug, large, half = entry["asset"], entry["large"], entry["half"]
    rows.append(f"| {slug} | {'×'.join(map(str, large['grid_size']))} / {'×'.join(map(str, half['grid_size']))} | {large['occupied_voxels']:,} / {half['occupied_voxels']:,} | {large['surface']['triangles']:,} / {half['surface']['triangles']:,} | {'×'.join(f'{v:g}' for v in large['grid_extents_m'])} |")
    pictures.append(f"| {slug} | ![Large {slug}](assets/{slug}/large/preview.png) | ![Half {slug}](assets/{slug}/half/preview.png) |")
report = f"""# Underwater voxel delivery

Ready for parent review and frozen. Five original assets are delivered as independent large and half voxel grids, with native VOX, BLEND, GLB, FBX and actual render previews. Native occupied-cell data is authoritative.

Actual start: **{utc_string(started)} UTC / {kst_string(started)} KST**. Actual finish: **{utc_string(finished)} UTC / {kst_string(finished)} KST**. Elapsed wall time: **{time_record['elapsed_seconds']:.3f} seconds**. One build/export/render run measured **{build_report['elapsed_seconds']:.3f} seconds** internally; fresh import validation measured **{validation['elapsed_seconds']:.3f} seconds** internally. These internal durations exclude Blender startup. Tools were available at dispatch; no blocking tool wait or worker image generation occurred.

| Model | Large / half grid | Occupied voxels, large / half | Triangles, large / half | Same physical grid extents (m) |
|---|---|---:|---:|---|
{chr(10).join(rows)}

Each `assets/NAME/{{large,half}}/` contains `NAME.vox`, `NAME.blend`, `NAME.glb`, `NAME.fbx`, `preview.png` and `metadata.json`. Totals are 10 native files, 30 BLEND/GLB/FBX files, 10 previews and 10 variant metadata records. Large grids have even axes and longest axis 128; each half dimension is exactly half, with doubled meters per voxel and identical physical grid extents. The docking station's 47-cell half height is valid under the clarified brief.

The submersible has a rounded hull and opaque convex viewport, two real through-bored ducted thrusters with recessed rotors, small manipulators and landing skids. The dome laboratory has eight raised meridian ribs, framed opaque window segments, a ring foundation, crown hatch and recessed airlock with a closed inner door. The connecting tunnel is a rounded pressure shell with genuinely open ends, framed side/roof glazing, a walkway, collars and support feet. The seabed miner has six stout articulated legs, a central observation pod and a real tapered drill with a winding raised cutting ridge. The docking station has two open guide arches, a reinforced deck, guide strips, connector pads/posts, side grates, service cabinet and two attached cable runs.

[Final independent validation](validation_export.json) passed **5 models / 10 variants / 30 fresh BLEND/GLB/FBX imports**, with `errors: []`. Native occupancy, coordinates, duplicate rejection, palette indexing, counts, bounds and hashes passed. All imported triangles matched the true outward voxel boundary and correct palette. Degenerate, invalid-boundary, invalid-material and off-grid triangle counts are zero. [Native feature checks](native_feature_checks.json) confirm open thruster quadrants, open airlock recess before its door, empty tunnel passage/end apertures, six miner footpads, both empty arch throats, valid size dimensions and opaque material colors at both resolutions.

All ten final previews were inspected. No geometry correction or additional modeling pass was required; no manual half-grid postprocessing was used. The final recording script rechecked every delivered file hash and the identical large/half camera settings. [delivery_manifest.json](delivery_manifest.json) records hashes, counts and timings. [build.py](build.py) and [palette.json](palette.json) are the independently authored source and named palette.

| Model | Large actual Blender render | Half actual Blender render |
|---|---|---|
{chr(10).join(pictures)}

Actual capture settings are Cycles CPU, 4 threads, 24 samples, denoising, AgX, 768×768 and paired orthographic cameras. [capture_manifest.json](capture_manifest.json) records each render's timestamps, camera and image hash. BLEND projects contain the asset collection plus a separate preview studio; GLB/FBX exports contain asset geometry only. These images were rendered from the delivered voxel surfaces.

Limitations: glazing is deliberately opaque colored voxel geometry, including the laboratory dome; no transparent simulation or furnished laboratory interior is claimed. These are static asset models without rig, animation, collisions, automatic LOD chain or game-engine integration. Flat palette materials need no texture UVs. Fine fittings and stepped curves simplify at half resolution, and conservative reduction can widen individual occupied boundaries by a large-grid cell while preserving physical grid extents.

Creative reference was limited to the supplied `REF/voxel/underwater/reference.png`. No prior theme creative source/assets, ForestDemo resources, existing Blender scenes or external creative materials were inspected or copied. No image generation, shared live Blender session, Git operations or subagents were used. This is the worker's final assigned theme; no further theme is queued.
"""
(root / "RESULT.md").write_text(report, encoding="utf-8")
print(json.dumps({"status": status, "build_seconds": build_report["elapsed_seconds"], "validation_seconds": validation["elapsed_seconds"], "final_hash_audit_passed": True}, indent=2))
