"""Finalize the verified five-pair spaceport handoff without changing geometry."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json

root = Path(__file__).resolve().parent
slugs = ("transport_rocket", "hangar", "exploration_rover", "fuel_tank", "control_tower")
started = datetime.fromisoformat("2026-10-23T14:46:36+00:00")

def load(path):
    return json.loads((root / path).read_text(encoding="utf-8-sig"))

def save(path, value):
    (root / path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

verified = load("validation_export.json")
features = load("feature_validation.json")
captures = load("capture_manifest.json")
build = load("build_timing.json")
tower_build = load("tower_correction_timing.json")
checks = load("check_timings.json")
final_checks = load("check_timings_final.json")
assert verified["passed"] and verified["asset_count"] == 5 and verified["variant_count"] == 10
assert features["passed"] and features["checks_per_variant"] == 15
assert len(captures["captures"]) == 10
assert all(row["exit_code"] == 0 for row in [build, tower_build] + checks + final_checks)

stats = {}
for slug in slugs:
    stats[slug] = {}
    for variant in ("large", "half"):
        meta = load(f"assets/{slug}/{variant}/metadata.json")
        directory = root / "assets" / slug / variant
        for filename, digest in meta["sha256"].items():
            assert hashlib.sha256((directory / filename).read_bytes()).hexdigest() == digest
        stats[slug][variant] = meta
        backup = directory / (slug + ".blend1")
        if backup.exists():
            assert backup.resolve().is_relative_to(root.resolve())
            backup.unlink()
for capture in captures["captures"]:
    assert hashlib.sha256((root / capture["image"]).read_bytes()).hexdigest() == capture["image_sha256"]

finished = datetime.now(timezone.utc)
kst = timezone(timedelta(hours=9))
elapsed = (finished - started).total_seconds()
observations = {
    "transport_rocket": "Capsule nose, framed hatch, wide landing stance and visible engine bells read in both sizes; native checks confirm four landing pads and three truly empty bell mouths.",
    "hangar": "Low broad arch and large empty spacecraft portal remain readable in both sizes, with interior floor markings, rear service lockers and attached roof equipment.",
    "exploration_rover": "Rounded pressurized cabin, three visible near-side wheels with six actual wheel positions, sensor head and open sample tray read at both resolutions.",
    "fuel_tank": "Two capsule-ended vessels, overhead manifold, front transfer plumbing, two valve controls and shared skid remain distinct in both sizes.",
    "control_tower": "Stout shaft, broad flared window cabin and rounded roof/antennae read in the final pair. Lowering the cabin floor/platform eight large cells corrected the initially obscured window band.",
}
save("visual_review.json", {"reviewed_at_utc": finished.isoformat(), "actual_final_previews_inspected": 10,
                            "matching_pair_cameras": True, "observations": observations,
                            "tower_exposed_glazing_rows": {r["variant"]: r["exposed_front_glazing_rows"] for r in features["records"]},
                            "remaining_functional_defects": []})
save("palette.json", {"theme": "spaceport", "empty_index": 0,
                      "roles": ["empty", "ivory", "white", "ivory reveal", "dusty blue", "blue edge", "blue shadow",
                                "graphite", "charcoal", "metal", "coral", "coral edge", "glass", "glass edge",
                                "warm light", "rubber", "tread", "rock sample"],
                      "rgba": stats["transport_rocket"]["large"]["palette"]})
save("STATUS.json", {
    "theme": "spaceport", "status": "ready_for_review", "phase": "submitted_frozen",
    "started_at_utc": started.isoformat(), "started_at_kst": started.astimezone(kst).isoformat(),
    "finished_at_utc": finished.isoformat(), "finished_at_kst": finished.astimezone(kst).isoformat(),
    "elapsed_seconds": elapsed, "assigned_assets": list(slugs), "asset_count": 5, "variant_count": 10,
    "formats": ["vox", "blend", "glb", "fbx"],
    "validation_summary": "10 native variants and 30 fresh BLEND/GLB/FBX inspections passed; 15 semantic checks at each resolution (30 total) passed; all 10 final actual previews inspected.",
    "build_seconds": build["elapsed_seconds"], "tower_correction_seconds": tower_build["elapsed_seconds"],
    "recorded_validation_process_seconds": sum(r["elapsed_seconds"] for r in checks + final_checks),
    "image_generation_seconds": 0, "blockers": [], "further_theme_assignments": False,
})

rows = []
for slug in slugs:
    lg, half = stats[slug]["large"], stats[slug]["half"]
    dims = lambda value: " x ".join(str(x) for x in value)
    physical = " x ".join(f"{x:.3f}".rstrip("0").rstrip(".") for x in lg["grid_extents_m"])
    rows.append(f"| {slug} | {dims(lg['grid_size'])} / {dims(half['grid_size'])} | {physical} | {lg['occupied_voxels']:,} / {half['occupied_voxels']:,} | {lg['surface']['triangles']:,} / {half['surface']['triangles']:,} |")
times = [f"- Initial five-pair production build/export/render: {build['elapsed_seconds']:.3f} seconds.",
         f"- Control tower correction and two-variant rebuild: {tower_build['elapsed_seconds']:.3f} seconds."]
for label, records in (("Initial", checks), ("Final", final_checks)):
    times += [f"- {label} {r['name']}: {r['elapsed_seconds']:.3f} seconds." for r in records]

report = f"""# Spaceport voxel delivery

Five original models, ten large/half variants, are ready for parent review. Files are frozen on submission. This is the worker's final assigned theme.

## Actual timing

- Start UTC: {started.isoformat()}; KST: {started.astimezone(kst).isoformat()}.
- Finish UTC: {finished.isoformat()}; KST: {finished.astimezone(kst).isoformat()}.
- Total elapsed wall time: {elapsed:.3f} seconds, including authoring, review and documentation.
{chr(10).join(times)}
- Image generation: none (0 seconds).

Process timers include startup. The brief failing glazing-height diagnostic was not separately timed and is excluded from the process totals; its log is retained. Only the tower pair was rebuilt after the initial run. No optional rear renders or further polish passes were performed. All Blender runs used isolated background factory-startup mode and four CPU threads.

## Models and grids

| Model | Large / half grid | Physical grid size (m) | Large / half occupied voxels | Large / half triangles |
|---|---|---|---:|---:|
{chr(10).join(rows)}

All large dimensions are even and the longest axis is 128. Every half dimension is exactly divided by two, with doubled meters per voxel and exactly matching physical grid extents. Large/half voxel sizes are rocket 0.055/0.11 m, hangar 0.065/0.13 m, rover 0.035/0.07 m, tank 0.04/0.08 m, and tower 0.05/0.1 m. Conservative outward occupied-bound expansion up to one large cell is permitted. Native VOX uses actual uint8 occupancy and 1-based visible palette indices; index 0 is empty. No manually edited half grid or scaled high-resolution mesh substitute was used.

## Delivered paths

- `build.py`: independently authored pure `make_assets()` and original grid geometry.
- `palette.json`: ivory/dusty-blue/graphite/coral palette and functional color roles.
- `assets/{{transport_rocket,hangar,exploration_rover,fuel_tank,control_tower}}/{{large,half}}/`: named `.vox`, `.blend`, `.glb`, `.fbx`, `preview.png` and `metadata.json`.
- `capture_manifest.json`: ten actual Blender renders, matching per-pair cameras, timestamps, settings and hashes.
- `validation_export.json`, `validation_export_final.log`: final independent complete-theme validation; initial results are also retained.
- `feature_validation.json`, `check_features.py`, `feature_check_final.log`, `glazing_check_before.log`: native semantic probes and the observed regression/fix evidence.
- `build_validation_initial.json`: first five-pair build record. `build_validation.json`: later selective control-tower build record. The final complete-theme authority is `validation_export.json` and the per-variant metadata.
- Process logs/timing JSON, `visual_review.json`, `STATUS.json`, and this report.

VOX is authoritative. GLB/FBX contain only exact exposed voxel surfaces. BLEND separates the asset from its reproducible preview studio; cameras, lights and floor are excluded from exchange meshes and native occupancy.

## Validation and visual review

The final independent verifier passed all 10 variants and all 30 fresh BLEND/GLB/FBX asset inspections. Native parsing confirmed valid coordinates, no duplicate/out-of-grid cells, count/palette/occupancy and file hashes, grid halving and physical sizes. Every imported triangle had finite grid-aligned coordinates, nonzero area, correct material, outward orientation and a true occupied-to-empty voxel boundary. Bounds, triangle counts and surface areas matched metadata. Exchange files had no studio objects.

Thirty saved-native semantic checks passed: four landing pads and three empty engine mouths; rocket hatch; open hangar portal plus floor/roof/back wall; six rover wheel centers, open tray and sensor; two capsule vessels, sampled continuous manifold and valve controls; hollow tower cabin, glass palette, exposed front window height, shaft, roof and antennae.

All ten final actual previews were inspected:

{chr(10).join('- **' + key + ':** ' + value for key, value in observations.items())}

One demonstrated issue was corrected: the original tower eave and balcony obscured most of the window band. A saved-native first-visible-surface probe failed its minimum exposed glazing height, then passed after the floor/platform moved down eight large cells and the mullions extended. The new tower renders were inspected; the other four asset pairs were unchanged.

Preview settings: 768 x 768, Cycles CPU, four threads, 24 samples, orthographic matching cameras, AgX and denoising. All scene evidence comes from actual asset renders.

## Limitations and provenance

These are static colored voxel meshes, with no rig, animation, collision, LOD chain or engine integration. Palette materials use no image textures or UVs. Glass is an opaque stylized color; instruments and lights are modeled colored details. Small ribs, collars, valve rings and antennae simplify at half resolution. The hangar contains a building floor; no common permanent display floor is part of the asset set. Mechanical systems are visual representations rather than simulations.

Only the assigned `../../REF/voxel/spaceport/reference.png` was viewed as design input, with read-only parent generic `../_tools` utilities and the common brief/API. No factory/mine creative source, other theme assets, ForestDemo, prior Blender creative scene, external model, Git, image generation, installation, subagent or shared live Blender session was used.
"""
(root / "RESULT.md").write_text(report, encoding="utf-8")
plan = (root / "PLAN.md").read_text(encoding="utf-8").replace("- [ ]", "- [x]")
plan += f"\nSubmitted frozen at {finished.isoformat()}; final full-theme and semantic validation passed.\n"
(root / "PLAN.md").write_text(plan, encoding="utf-8")
print(json.dumps({"status": "ready_for_review", "finished_at_utc": finished.isoformat(),
                  "elapsed_seconds": elapsed, "asset_count": 5, "variant_count": 10}, indent=2))
