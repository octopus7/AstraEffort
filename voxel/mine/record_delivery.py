"""Write the mine handoff from verified saved metadata and actual run records."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json

root = Path(__file__).resolve().parent
slugs = ("excavator", "mine_cart", "mine_elevator", "ore_sorter")
started = datetime.fromisoformat("2026-10-23T14:29:23+00:00")

def load(path):
    return json.loads((root / path).read_text(encoding="utf-8-sig"))

def save(path, value):
    (root / path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

verification = load("validation_export.json")
features = load("feature_validation.json")
capture = load("capture_manifest.json")
build = load("build_timing.json")
checks = load("check_timings.json")
assert verification["passed"] and verification["asset_count"] == 4 and verification["variant_count"] == 8
assert features["passed"] and features["checks_per_variant"] == 12
assert len(capture["captures"]) == 8
assert all(item["exit_code"] == 0 for item in [build] + checks)

pairs = {}
for slug in slugs:
    pairs[slug] = {}
    for variant in ("large", "half"):
        meta = load(f"assets/{slug}/{variant}/metadata.json")
        folder = root / "assets" / slug / variant
        for filename, digest in meta["sha256"].items():
            assert hashlib.sha256((folder / filename).read_bytes()).hexdigest() == digest
        pairs[slug][variant] = meta
for item in capture["captures"]:
    assert hashlib.sha256((root / item["image"]).read_bytes()).hexdigest() == item["image_sha256"]

finished = datetime.now(timezone.utc)
kst = timezone(timedelta(hours=9))
wall = (finished - started).total_seconds()
visual = {
    "excavator": "Both previews show a deep empty bucket mouth, separate articulated arm links and rods, framed cab, tread loop and rollers. Native probes additionally confirm both track interiors remain open.",
    "mine_cart": "The deep open tapered bed and thick rim read at both sizes; wheel flanges, braces, couplers and hand brake remain substantial.",
    "mine_elevator": "Four-post headframe, exposed sheave, cage opening, winding drum, continuous cable route and stairs read at both sizes. Close twin strands merge locally in the half grid.",
    "ore_sorter": "Open hopper, sloping perforated screen, short rising discharge belt and three separately framed ore bins read at both sizes; aperture pattern survives reduction.",
}
save("visual_review.json", {"reviewed_at_utc": finished.isoformat(), "actual_previews_inspected": 8,
                            "matching_cameras": True, "observations": visual, "functional_defects": []})
save("palette.json", {"theme": "mine", "index_zero_is_empty": True,
                      "roles": ["empty", "olive", "olive edge", "olive structure", "cream", "cream edge",
                                "steel", "light steel", "charcoal", "tread", "copper orange", "copper edge",
                                "exposed metal", "glass", "deep opening", "brown ore", "stone", "amber"],
                      "rgba": pairs["excavator"]["large"]["palette"]})
save("STATUS.json", {
    "theme": "mine", "status": "ready_for_review", "phase": "submitted_frozen",
    "started_at_utc": started.isoformat(), "started_at_kst": started.astimezone(kst).isoformat(),
    "finished_at_utc": finished.isoformat(), "finished_at_kst": finished.astimezone(kst).isoformat(),
    "elapsed_seconds": wall, "assigned_assets": list(slugs), "asset_count": 4, "variant_count": 8,
    "formats": ["vox", "blend", "glb", "fbx"],
    "validation_summary": "8 native variants and 24 fresh BLEND/GLB/FBX inspections passed; 12 functional probes per resolution (24 total) passed; all 8 actual previews inspected.",
    "build_seconds": build["elapsed_seconds"], "validation_process_seconds": sum(row["elapsed_seconds"] for row in checks),
    "image_generation_seconds": 0, "blockers": [], "next_theme_started": False,
})

table = []
for slug in slugs:
    large, half = pairs[slug]["large"], pairs[slug]["half"]
    dims = lambda values: " x ".join(str(v) for v in values)
    physical = " x ".join(f"{v:.3f}".rstrip("0").rstrip(".") for v in large["grid_extents_m"])
    table.append(f"| {slug} | {dims(large['grid_size'])} / {dims(half['grid_size'])} | {physical} | {large['occupied_voxels']:,} / {half['occupied_voxels']:,} | {large['surface']['triangles']:,} / {half['surface']['triangles']:,} |")
processes = [f"- Full eight-variant build/export/render: {build['elapsed_seconds']:.3f} seconds."]
processes += [f"- {row['name']}: {row['elapsed_seconds']:.3f} seconds." for row in checks]

result = f"""# Mine voxel delivery

Four original mine models are ready for parent review and frozen on submission. Spaceport has not started.

## Actual timestamps and process times

- Start UTC: {started.isoformat()}; KST: {started.astimezone(kst).isoformat()}.
- Finish UTC: {finished.isoformat()}; KST: {finished.astimezone(kst).isoformat()}.
- Total elapsed wall time: {wall:.3f} seconds, including authoring, inspection and documentation.
{chr(10).join(processes)}
- Image generation: none (0 seconds).

Process times above include Blender startup. One production build was needed; no repeated polish build or optional secondary rendering pass was performed. All Blender processes used background factory-startup mode and four CPU threads.

## Models

| Model | Large / half grid | Physical grid size (m) | Large / half occupied voxels | Large / half triangles |
|---|---|---|---:|---:|
{chr(10).join(table)}

All large axes are even and the longest is 128. Every half axis is exactly divided by two and its voxel size doubles, preserving exact physical grid extents. Meters per voxel are 0.035/0.07 for excavator and cart, 0.045/0.09 for elevator, and 0.04/0.08 for sorter. Conservative occupied-bound expansion of up to one large cell is allowed by the assigned reduction semantics. No manual half-grid corrections were made. Native uint8 VOX occupancy is authoritative, with empty index 0 and visible palette indices starting at 1.

## Delivered files

- `build.py`: original pure `make_assets()` geometry authoring through the parent-owned generic API.
- `palette.json`: olive/cream/charcoal and copper-orange palette roles/RGBA values.
- `assets/{{excavator,mine_cart,mine_elevator,ore_sorter}}/{{large,half}}/`: named VOX, BLEND, GLB, FBX, `preview.png` and `metadata.json` for each variant.
- `capture_manifest.json`: eight actual matched-camera renders, actual timestamps, render settings and hashes.
- `validation_export.json` and `.log`: independent native and fresh format verification.
- `feature_validation.json`, `check_features.py`, `feature_check.log`: saved-native opening and cable-path checks.
- `build_validation.json`, `build.log`, `build_timing.json`, `check_timings.json`, `visual_review.json`, `STATUS.json` and this report.

GLB/FBX include only the exposed voxel surface mesh. BLEND retains separate `ASSET` and `STUDIO` collections for reproducible previews; studio floor, camera and lights do not enter native VOX or exchange exports.

## Verification and visual findings

The independent parent verifier passed all 8 variants and all 24 fresh BLEND/GLB/FBX asset inspections with no errors. It reparsed native VOX coordinates, counts, palette and occupancy hashes; confirmed exact grid halving and physical grid sizes; and checked file hashes. Imported triangles were finite, nondegenerate, on the exact occupied-to-empty voxel boundary with outward normals and correct palette assignment. Bounds, triangles and surface area matched metadata. GLB/FBX contained no studio objects.

Twelve additional feature checks passed independently on each saved resolution: hollow bucket volume and solid side/back, two track cavities, open cart bed and four wheel centers, clear cage portal and open sheave web, continuous sampled cage/winch cables, open sorter hopper, screen aperture and occupied screen rail/discharge belt.

All eight actual previews were inspected:

{chr(10).join('- **' + slug + ':** ' + observation for slug, observation in visual.items())}

Preview settings are Cycles CPU, four threads, 24 samples, 768 x 768, orthographic matching cameras, AgX and denoising. No image-generation output is presented as scene evidence.

## Limitations and provenance

Static colored voxel models only: no rig, animation, collision, LOD chain or game-engine integration. Flat palette materials need no texture UVs; cab glass is an opaque stylized color. Small pins, chain-like ribs, cables and screen cells become chunkier at half resolution; two close elevator cable strands may merge locally while their occupied route stays continuous. Mechanics are visual representations rather than engineered simulations.

Only the assigned `../../REF/voxel/mine/reference.png` was viewed as design input. Geometry was independently authored without reading or copying factory creative source, another theme, ForestDemo, prior Blender creative assets, or an external model. Generic parent-owned `../_tools` utilities and the common brief/API were the sole shared implementation resources. No Git operations, installations, image generation, subagents or shared live Blender session were used.
"""
(root / "RESULT.md").write_text(result, encoding="utf-8")
plan = (root / "PLAN.md").read_text(encoding="utf-8").replace("- [ ]", "- [x]")
plan += f"\nCompleted and submitted frozen at {finished.isoformat()}; all required checks passed.\n"
(root / "PLAN.md").write_text(plan, encoding="utf-8")
print(json.dumps({"status": "ready_for_review", "finished_at_utc": finished.isoformat(),
                  "elapsed_seconds": wall, "asset_count": 4, "variant_count": 8}, indent=2))
