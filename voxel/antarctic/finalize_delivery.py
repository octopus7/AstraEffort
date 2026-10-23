"""Audit final owned files and write the Antarctic delivery record."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import importlib.util
import json

root = Path(__file__).resolve().parent
started = datetime(2026, 10, 23, 14, 6, 5, tzinfo=timezone.utc)
spec = importlib.util.spec_from_file_location("antarctic_build", root / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
expected = ["research_station", "snowcat", "radar", "weather_instrument"]
validation = json.loads((root / "validation_export.json").read_text(encoding="utf-8"))
semantics = json.loads((root / "geometry_semantics.json").read_text(encoding="utf-8"))
assert validation["passed"] and validation["asset_count"] == 4 and validation["variant_count"] == 8
assert not validation["errors"] and semantics["passed"]
captures = json.loads((root / "capture_manifest.json").read_text(encoding="utf-8"))["captures"]
assert len(captures) == 8
records = []
for slug in expected:
    pair = []
    for variant in ("large", "half"):
        dst = root / "assets" / slug / variant
        meta = json.loads((dst / "metadata.json").read_text(encoding="utf-8"))
        for name, expected_hash in meta["sha256"].items():
            assert hashlib.sha256((dst / name).read_bytes()).hexdigest() == expected_hash, str(dst / name)
        assert meta["native_roundtrip_passed"]
        pair.append(meta)
        records.append({"asset": slug, "variant": variant, "directory": str(dst.relative_to(root)).replace("\\", "/"),
                        "grid": meta["grid_size"], "occupied_voxels": meta["occupied_voxels"],
                        "triangles": meta["surface"]["triangles"], "voxel_size_m": meta["voxel_size_m"],
                        "grid_extents_m": meta["grid_extents_m"], "sha256": meta["sha256"]})
    assert [n * 2 for n in pair[1]["grid_size"]] == pair[0]["grid_size"]
    assert pair[0]["grid_extents_m"] == pair[1]["grid_extents_m"]
    camera_pair = [c["settings"] for c in captures if c["asset"] == slug]
    assert len(camera_pair) == 2 and camera_pair[0] == camera_pair[1]
assert not list((root / "assets").rglob("*.blend1"))
palette_names = ["empty", "ivory", "snow", "shadow", "navy", "blue", "dark", "steel", "silver", "orange", "amber", "glass", "sky", "black", "lamp", "slate"]
(root / "palette.json").write_text(json.dumps({"palette_index_zero_is_empty": True,
    "colors": [{"index": i, "name": name, "rgba": list(build.PALETTE[i])} for i, name in enumerate(palette_names)]}, indent=2), encoding="utf-8")

initial_run = {"started_at_utc": "2026-10-23T14:12:17.497681+00:00", "finished_at_utc": "2026-10-23T14:13:42.086869+00:00", "elapsed_seconds": 84.58887790003791, "assets": expected,
               "evidence": "build.log; initial build_validation.json was read before later selective builds replaced it"}
station_run = json.loads((root / "build_validation_station.json").read_text(encoding="utf-8"))
snowcat_run = json.loads((root / "build_validation_snowcat.json").read_text(encoding="utf-8"))
build_seconds = initial_run["elapsed_seconds"] + station_run["elapsed_seconds"] + snowcat_run["elapsed_seconds"]
finished = datetime.now(timezone.utc)
elapsed = (finished - started).total_seconds()
to_kst = lambda dt: dt.astimezone(timezone(timedelta(hours=9))).isoformat(timespec="seconds")
iso = lambda dt: dt.isoformat(timespec="seconds").replace("+00:00", "Z")
timing = {"started_at_utc": iso(started), "started_at_kst": to_kst(started), "finished_at_utc": iso(finished), "finished_at_kst": to_kst(finished),
          "elapsed_seconds": elapsed, "build_export_render_internal_seconds": build_seconds,
          "independent_validation_internal_seconds": validation["elapsed_seconds"], "worker_image_generation_seconds": 0,
          "tools_wait_seconds": None, "tools_wait_note": "Tools became ready during source authoring; no separate blocking interval was measured.",
          "build_runs": [initial_run] + [{key: run[key] for key in ("started_at_utc", "finished_at_utc", "elapsed_seconds")} for run in (station_run, snowcat_run)]}
manifest = {"theme": "antarctic", "status": "ready_for_review", "timing": timing, "asset_count": 4, "variant_count": 8,
            "native_authority": "VOX 150 occupied uint8 grids", "formats_per_variant": ["vox", "blend", "glb", "fbx"],
            "actual_previews_reviewed": [f"assets/{slug}/{variant}/preview.png" for slug in expected for variant in ("large", "half")],
            "same_camera_verified": True, "final_hash_audit_passed": True,
            "source_sha256": hashlib.sha256((root / "build.py").read_bytes()).hexdigest(), "variants": records}
(root / "delivery_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
status = {"theme": "antarctic", "status": "ready_for_review", **{k: timing[k] for k in ("started_at_utc", "started_at_kst", "finished_at_utc", "finished_at_kst", "elapsed_seconds")},
          "phase": "submitted_for_parent_review", "assets": expected,
          "validation_summary": "4 assets / 8 variants passed native VOX checks and 24 fresh BLEND/GLB/FBX imports. All eight final actual previews inspected. Exact half grids, physical grid extents and paired camera settings verified; final hashes match.",
          "blockers": []}
(root / "STATUS.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
rows = []
for slug in expected:
    a, b = [r for r in records if r["asset"] == slug]
    rows.append(f"| {slug} | {' × '.join(map(str, a['grid']))} / {' × '.join(map(str, b['grid']))} | {a['occupied_voxels']:,} / {b['occupied_voxels']:,} | {a['triangles']:,} / {b['triangles']:,} | {' × '.join(f'{v:g}' for v in a['grid_extents_m'])} |")
gallery = "\n".join(f"| {slug} | ![Large {slug}](assets/{slug}/large/preview.png) | ![Half {slug}](assets/{slug}/half/preview.png) |" for slug in expected)
result = f"""# Antarctic voxel asset delivery

Ready for parent review. Four original voxel models are delivered at two independent grid resolutions. Native VOX files are authoritative; GLB/FBX contain extracted occupied-voxel surfaces. BLEND files also contain the separate preview studio collection.

Started: **{iso(started)} UTC / {to_kst(started)} KST**. Finished: **{iso(finished)} UTC / {to_kst(finished)} KST**. Actual elapsed wall time: **{elapsed:.3f} seconds**. Three build/export/render runs measured **{build_seconds:.3f} seconds** internally; fresh import verification measured **{validation['elapsed_seconds']:.3f} seconds** internally. These internal durations exclude Blender startup. Tools became ready during authoring; no independent wait interval was measured. Worker image-generation time was zero.

| Model | Large / half grid | Occupied voxels, large / half | Triangles, large / half | Shared physical grid extents (m) |
|---|---|---:|---:|---|
{chr(10).join(rows)}

Each `assets/NAME/{{large,half}}/` contains `NAME.vox`, `NAME.blend`, `NAME.glb`, `NAME.fbx`, `preview.png`, and `metadata.json`. All dimensions halve exactly; meters per voxel double, preserving the physical grid extents. There are 8 native grids, 24 mesh/project files and 8 actual previews. Source: [build.py](build.py). Named palette: [palette.json](palette.json). Checksums, paired camera audit and timing: [delivery_manifest.json](delivery_manifest.json).

The research station has six telescopic legs, insulated rounded shell, five-bay window band, orange airlock, eight stair treads, side heat exchanger, aft service bay and roof HVAC. The snowcat has two separate hollow track belts, road wheels and raised treads, a blunt curved blade with attached supports, glazed cab and protected cargo equipment. The radar has an open tilted paraboloid, a real feed with tripod supports, rear ribs, bearing yoke and four-foot electronics base. The weather mast has an open outrigger base, sealed logger, tilted solar cells, radiation-shield plates, three hollow cups, wind vane and cable routes.

[Independent validation](validation_export.json) passed all 4 models / 8 variants and **24 fresh BLEND/GLB/FBX imports**, with no errors. Every imported triangle was checked against the outward native voxel boundary and correct palette; invalid boundary, material, off-grid and degenerate triangle counts are all zero. Native occupancy, bounds, counts, palette indices, duplicates and hashes passed. [Semantic checks](geometry_semantics.json) cover six station pads, front-exposed windshield, air inside both tracks, open radar bowl and hollow weather cup. Final file hashes still match metadata.

All eight final previews below were inspected. Inspection exposed an initially occluded snowcat windshield; a source occupancy probe reproduced it, the cab shell was cut back, and both resolutions were re-rendered. Blade supports were extended into the blade. A visible station service cassette was added and re-rendered. The half grids needed no manual postprocessing. The initial failing diagnostic is retained as [geometry_before_fix.json](geometry_before_fix.json). Separate station/snowcat rebuild records are retained; `build_validation.json` is the last selective run, while `validation_export.json` covers every final deliverable.

| Model | Large actual Blender render | Half actual Blender render |
|---|---|---|
{gallery}

Capture settings: Cycles CPU, 4 threads, 24 samples with denoising, 768 × 768, AgX, matched orthographic camera per large/half pair. [capture_manifest.json](capture_manifest.json) records actual timestamps, cameras and image hashes. The images above are renders of the supplied voxel meshes.

Limitations: glass is opaque stylized color; models have no rig, animation, collision, game-engine integration or automatic LOD chain. Flat palette materials do not require UV textures. Small cosmetic louvers, joints and panel grid lines simplify in half resolution. Conservative reduction can expand the occupied silhouette by a large-grid cell at individual boundaries, while the physical grid domain stays identical. No random color noise or unrelated decorations were used.

Design reference: the parent-supplied `REF/voxel/antarctic/reference.png`, visually inspected before authoring. No other theme assets, prior Blender scenes, ForestDemo files or external creative resources were read or reused. No Git operations, image generation or shared live Blender session were used. Final files are frozen pending parent review.
"""
(root / "RESULT.md").write_text(result, encoding="utf-8")
print(json.dumps({"status": status, "build_seconds": build_seconds, "validation_seconds": validation["elapsed_seconds"], "final_hash_audit_passed": True}, indent=2))
