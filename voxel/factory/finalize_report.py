"""Record a verified factory handoff. Run only after final visual inspection."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json

ROOT = Path(__file__).resolve().parent
SLUGS = ("production_machine", "conveyor", "forklift", "generator")
START = datetime.fromisoformat("2026-10-23T14:05:47+00:00")

def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8-sig"))

def write(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

validation = read("validation_export.json")
features = read("feature_validation.json")
captures = read("capture_manifest.json")
rear = read("qa/capture_manifest.json")
assert validation["passed"] and validation["asset_count"] == 4 and validation["variant_count"] == 8
assert features["passed"] and len(features["checks"]) == 6
assert len(captures["captures"]) == 8 and len(rear["captures"]) == 4
for capture in captures["captures"] + rear["captures"]:
    assert sha(ROOT / capture["image"]) == capture["image_sha256"]

assets = []
for slug in SLUGS:
    pair = {variant: read(f"assets/{slug}/{variant}/metadata.json") for variant in ("large", "half")}
    assert pair["large"]["bounds_m"] == pair["half"]["bounds_m"], slug
    for variant, meta in pair.items():
        directory = ROOT / "assets" / slug / variant
        for name, expected in meta["sha256"].items():
            assert sha(directory / name) == expected, str(directory / name)
        # Blender's automatic previous-save copies are not final deliverables.
        backup = directory / (slug + ".blend1")
        if backup.exists():
            assert backup.resolve().is_relative_to(ROOT.resolve())
            backup.unlink()
    assets.append({"asset": slug, "large": pair["large"], "half": pair["half"]})

palette = assets[0]["large"]["palette"]
names = ["empty", "mustard enamel", "edge enamel", "recessed yellow", "slate blue",
         "raised blue casing", "blue structure", "ivory panel", "ivory edge", "panel reveal",
         "graphite rubber", "rubber tread", "steel", "exposed metal", "deep opening",
         "instrument glass", "switch red", "warm metal"]
write("palette.json", {"index_zero_is_empty": True,
                       "colors": [{"index": i, "name": names[i], "rgba": c} for i, c in enumerate(palette)]})

builds = [read(name) for name in ("build_timing.json", "refinement_timing.json", "bounds_timing.json")]
checks_previous = read("check_timings.json")
checks_final = read("check_timings_final.json")
assert all(row["exit_code"] == 0 for row in builds + checks_previous + checks_final)
finish = datetime.now(timezone.utc)
elapsed = (finish - START).total_seconds()
kst = timezone(timedelta(hours=9))

observations = {
    "production_machine": "Open ram throat and die slots readable at both sizes; corrected motor grille remains slotted; rear accumulator/hoses and cabinet access details inspected.",
    "conveyor": "Two rounded end roller assemblies, belt ribs, four supports and crates readable; corrected drive grille remains open in half; rear bracing inspected.",
    "forklift": "Two separated forks, mast and open cab readable in both sizes; front and rear views show all four wheel positions; rear grille, step and seat inspected.",
    "generator": "Rounded casing, service doors, end grille, skid pockets, exhaust and lifting eyes readable in both sizes; rear cable loop and outlet panel inspected.",
}
write("visual_review.json", {"reviewed_at_utc": finish.isoformat(), "reviewer": "assigned factory worker",
                             "main_previews_inspected": 8, "rear_qa_previews_inspected": 4,
                             "actual_render_evidence": True, "observations": observations,
                             "remaining_visual_defects": []})

status = {
    "theme": "factory", "status": "ready_for_review", "phase": "submitted_frozen",
    "started_at_utc": START.isoformat(), "started_at_kst": START.astimezone(kst).isoformat(),
    "finished_at_utc": finish.isoformat(), "finished_at_kst": finish.astimezone(kst).isoformat(),
    "elapsed_seconds": elapsed, "assigned_assets": list(SLUGS),
    "asset_count": 4, "variant_count": 8, "formats": ["vox", "blend", "glb", "fbx"],
    "validation_summary": "All 8 native variants and 24 fresh BLEND/GLB/FBX inspections passed; 6 native feature/bounds checks passed; 8 main and 4 rear actual renders inspected.",
    "validation_report": "validation_export.json", "visual_review": "visual_review.json",
    "recorded_blender_process_seconds": sum(row["elapsed_seconds"] for row in builds + checks_previous + checks_final),
    "image_generation_seconds": 0, "blockers": [], "next_theme_started": False,
}
write("STATUS.json", status)

rows = []
for record in assets:
    lg, sm = record["large"], record["half"]
    shape = lambda value: " × ".join(str(v) for v in value)
    dims = lambda value: " × ".join(f"{v:.3f}".rstrip("0").rstrip(".") for v in value)
    rows.append(f"| {record['asset']} | {shape(lg['grid_size'])} / {shape(sm['grid_size'])} | {dims(lg['grid_extents_m'])} | {lg['occupied_voxels']:,} / {sm['occupied_voxels']:,} | {lg['surface']['triangles']:,} / {sm['surface']['triangles']:,} |")
timing_rows = []
for name, timing in zip(("Initial full build", "Grille correction rebuild", "Occupied-bounds alignment rebuild"), builds):
    timing_rows.append(f"| {name} | {timing['elapsed_seconds']:.3f} |")
for suffix, checks in (("First verification/evidence", checks_previous), ("Final verification/evidence", checks_final)):
    for row in checks:
        timing_rows.append(f"| {suffix}: {row['name']} | {row['elapsed_seconds']:.3f} |")

text = f"""# Factory voxel delivery

Four original assets are ready for parent review. Files are frozen after this handoff; the next theme has not started.

## Actual timing

- Start: {START.isoformat()} UTC / {START.astimezone(kst).isoformat()} KST.
- Finish: {finish.isoformat()} UTC / {finish.astimezone(kst).isoformat()} KST.
- Elapsed wall time: {elapsed:.3f} seconds.
- Worker assignment: gpt-6-astra with max reasoning. The dispatch API exposes no separate Fast switch; none is claimed.
- Image generation: none (0 seconds). Only the assigned factory reference was viewed.

| Recorded Blender process | Wall seconds |
|---|---:|
{chr(10).join(timing_rows)}

The above process timers include startup. Two brief failing native-feature diagnostic runs were not separately timed and are excluded from the recorded process total; they remain in the logs. Authoring, review and documentation are included in the overall elapsed wall time. Tool readiness overlapped geometry authoring.

## Models and native grids

Each variant has its own native uint8 occupancy. Large/half meters per voxel are respectively 0.04/0.08 for the press, 0.045/0.09 for the conveyor, 0.035/0.07 for the forklift, and 0.04/0.08 for the generator. Palette index 0 is empty; visible indices begin at 1.

| Asset | Large / half grid | Physical grid extent (m) | Large / half occupied voxels | Large / half triangles |
|---|---|---|---:|---:|
{chr(10).join(rows)}

All axes are even and each large grid's longest axis is 128. Half dimensions divide every axis by exactly two and meters per voxel double. Both grid extents and occupied physical bounds match exactly for each delivered pair. The half mesh is rebuilt from the independent reduced grid. There are no hand-authored half-grid corrections.

## Delivery paths

- `build.py`: original procedural geometry, with pure `make_assets()` returning four `Asset` records.
- `palette.json`: restrained mustard/slate/ivory palette and color roles.
- `assets/{{production_machine,conveyor,forklift,generator}}/{{large,half}}/`: named `.vox`, `.blend`, `.glb`, `.fbx`, `preview.png`, and `metadata.json`.
- `capture_manifest.json`: eight actual same-camera Blender render captures, settings and hashes.
- `qa/`: four actual rear-view renders and their separate capture manifest.
- `build_validation.json`, `validation_export.json`, `feature_validation.json`, `visual_review.json`: validation evidence.
- `build*.log`, `validation_export.log`, `feature_check*.log`, `rear_qa*.log`, and `*_timing*.json`: actual process evidence.

VOX is authoritative. GLB/FBX contain only the surface mesh. The saved BLEND keeps an `ASSET` collection and a separate `STUDIO` collection for reproducible previews; its floor/camera/lights are excluded from exchange exports and native occupancy.

## Validation and visual review

The parent-owned independent verifier passed all 8 variants, reparsed native VOX independently, verified coordinates/color indices/counts/palette/occupancy and file hashes, then freshly opened/imported all 24 BLEND/GLB/FBX asset meshes. Every imported triangle had finite grid-aligned coordinates, nonzero area, the correct palette material, an outward normal and a true occupied-to-empty voxel boundary. Bounds, triangle counts and surface areas matched. No studio objects leaked into GLB/FBX.

All eight final front previews and four rear QA renders were visually inspected:

{chr(10).join('- **' + key + ':** ' + value for key, value in observations.items())}

Two corrections followed observed evidence. Odd-cell motor grille phases caused both half models to appear solid at the motor face; saved-native ray probes reproduced the loss and then passed after even-cell bar/slot alignment. An additional native bounds probe found three one-large-cell conservative expansions; moving the press accumulator cap, conveyor outer hub and forklift beacon extrema onto even cells produced exact occupied-bound equality. These were source-grid changes, not scaled-mesh substitutes.

The final feature report contains six passing checks: two exposed half-resolution grille traces and four exact occupied-bound comparisons. Preview evidence is actual Blender Cycles output (768 × 768, 24 samples, CPU, four threads, AgX). The reference is design input only.

## Limitations and references

Assets are static, joined colored voxel surface meshes. No rig, animation, collision, LOD chain or engine integration is supplied. Small bolts, chain links, slats and cable sections become chunkier at half resolution. Flat palette materials use no texture UVs or image textures. Native enclosed volume is occupied by design; exported meshes contain only exposed boundaries. Mechanical detail is an artistic functional representation, not an engineered simulation.

Design input: `../../REF/voxel/factory/reference.png`. Shared read-only implementation input: `../BRIEF.md`, `../_tools/API.md`, `voxelkit.py`, `blender_pipeline.py`, and `verify_theme.py`. No external asset, ForestDemo, other theme, prior Blender creative asset, image-generation output, shared live scene or Git operation was used.
"""
(ROOT / "RESULT.md").write_text(text, encoding="utf-8")
plan = (ROOT / "PLAN.md").read_text(encoding="utf-8").replace("- [ ]", "- [x]")
plan += f"\n- {finish.isoformat()}: All eight variants, required formats and rendered evidence verified; RESULT/STATUS finalized for parent review. Files frozen on submission.\n"
(ROOT / "PLAN.md").write_text(plan, encoding="utf-8")
print(json.dumps({"status": "ready_for_review", "elapsed_seconds": elapsed,
                  "finished_at_utc": finish.isoformat(), "variants": 8}, indent=2))
