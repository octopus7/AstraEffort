"""Finish records after real native validation and image inspection are present."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def write(name, data):
    (ROOT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    status = read('STATUS.json')
    validation = read('validation.json')
    capture = read('capture_manifest.json')
    inspection = read('image_inspection.json')
    pipeline = read('pipeline_timing.json')
    reruns = [json.loads(p.read_text(encoding='utf-8')) for p in ROOT.glob('pipeline_timing_*.json')]
    all_runs = [pipeline] + reruns
    assert validation['passed'] and validation['assets'] == 7 and validation['variants'] == 14
    assert len(capture['captures']) == 14
    assert len(inspection['images']) == 14 and all(i['inspected'] for i in inspection['images'])
    for item in inspection['images']:
        assert item['sha256'] == sha(ROOT / item['image'])
    assert struct.unpack('>II', (ROOT / 'overview_half.png').read_bytes()[16:24]) == (1600, 1000)
    now = datetime.now(timezone.utc)
    started = datetime.fromisoformat(status['started_at_utc'])
    wall = (now - started).total_seconds()
    kst = timezone(timedelta(hours=9))
    render_seconds = sum(r['render_seconds'] for r in all_runs)
    timing = {
        'started_at_utc': started.isoformat(), 'finished_at_utc': now.isoformat(),
        'started_at_kst': started.astimezone(kst).isoformat(),
        'finished_at_kst': now.astimezone(kst).isoformat(),
        'elapsed_wall_seconds': wall,
        'source_authoring_until_first_pipeline_start_seconds':
            (datetime.fromisoformat(pipeline['started_at_utc']) - started).total_seconds(),
        'authored_grid_build_seconds': sum(r['authored_grid_build_seconds'] for r in all_runs),
        'surface_build_seconds': sum(r['surface_build_seconds'] for r in all_runs),
        'native_write_roundtrip_seconds': sum(r['native_write_roundtrip_seconds'] for r in all_runs),
        'pipeline_seconds': sum(r['elapsed_seconds'] for r in all_runs),
        'render_seconds': render_seconds,
        'final_delivered_preview_render_seconds': sum(c['elapsed_seconds'] for c in capture['captures']),
        'additional_render_runs': len(reruns),
        'validation_seconds': validation['elapsed_seconds'],
        'timing_note': 'Wall begins at the recorded production clock sample; preceding brief reading is not timed. Build/render/validation measures overlap with no modeled waiting or invented duration.',
    }
    write('timing.json', timing)
    status.update({'status': 'ready_for_review', 'finished_at_utc': now.isoformat(),
                   'finished_at_kst': now.astimezone(kst).isoformat(), 'elapsed_seconds': wall,
                   'stage': 'native verification and inspection complete; awaiting coordinated cross-review',
                   'models': 7, 'native_vox_files': 14, 'actual_preview_pngs': 14,
                   'contact_sheet': 'overview_half.png',
                   'validation_summary': {'passed': True, 'feature_probes': validation['meaningful_feature_probe_count'],
                                          'inspected_previews': 14, 'same_camera_pairs': 7,
                                          'forbidden_outputs': 0}, 'blockers': []})
    write('STATUS.json', status)
    rows = []
    for a in ('double_door_fridge', 'range_oven', 'microwave', 'dishwasher', 'range_hood', 'rice_cooker', 'electric_kettle'):
        large = read(f'assets/{a}/large/metadata.json')
        half = read(f'assets/{a}/half/metadata.json')
        rows.append(f"| {a} | {' x '.join(map(str, large['grid_size']))} | {' x '.join(map(str, half['grid_size']))} | {large['occupied_voxels']:,} / {half['occupied_voxels']:,} | {large['voxel_size_m'] * 1000:g} / {half['voxel_size_m'] * 1000:g} |")
    result = f'''# Kitchen appliances result

Seven newly authored appliances are delivered as **14 native VOX 150 files and 14 actual 768 x 768 PNG previews**, plus a labeled half-resolution contact sheet. Status: ready for coordinated cross-review.

![Half-resolution appliance overview](overview_half.png)

## Delivered paths

Each of `double_door_fridge`, `range_oven`, `microwave`, `dishwasher`, `range_hood`, `rice_cooker`, and `electric_kettle` has `assets/SLUG/{{large,half}}/SLUG.vox`, `preview.png`, and `metadata.json`.

The source is `build.py`; native-to-preview runner is `preview_pipeline.py`; fresh validator is `validate.py`. Evidence includes `palette.json`, `capture_manifest.json`, `validation.json`, `image_inspection.json`, `pipeline_timing.json`, `timing.json`, `frozen_file_hashes.json`, `STATUS.json`, and `logs/render.log`.

| Appliance | Large grid | Half grid | Occupied voxels large / half | Cell mm large / half |
|---|---|---|---:|---:|
{chr(10).join(rows)}

## Verification and inspection

- Full authored-to-reparsed occupancy and palette comparisons passed for all 14 VOX files; VOX 150, coordinate uniqueness/bounds, palette indices and nonzero occupancy passed.
- Every large grid has even axes and longest axis 128. Every half grid has exactly halved axes, doubled cell size and identical physical grid extents; actual occupied-cell count decreases. There are no half-postprocess corrections.
- **{validation['meaningful_feature_probe_count']} functional native feature probes** passed across both sizes: separated refrigerator doors and pulls; oven grip and four burner rests; microwave grip/vent/window; dishwasher rack slots/chamber/cup opening; hood duct/filter gap; cooker carry handle; kettle handle/vessel/open spout.
- All 14 previews are actual Blender 4.5 Cycles CPU renders of temporary exact boundary geometry built from reopened VOX files. Every pair uses identical large-source camera bounds, camera, lights and render settings: 768px, 24 samples, denoising, AgX, four threads. Native and image hashes are in metadata/capture evidence.
- Every preview was directly viewed using the image tool. Observations and timestamps are in `image_inspection.json`. The contact sheet was composed from the seven actual half previews and also inspected.
- One observed hood defect was corrected: the original underside cutout breached a sloped side shell. A failing native shell probe reproduced it; a shallower inlet plus continuous central airway passed new probes, and only the hood pair was rerendered. Rework render time is included in the totals; `logs/hood_regression_red.log` records the original failure.
- No `.blend`, exchange mesh, engine, image-generated, rigging, animation or collision files were produced. The studio floor exists only transiently for rendering.

## Actual timing

Start: **{timing['started_at_utc']} UTC / {timing['started_at_kst']} KST**. Finish: **{timing['finished_at_utc']} UTC / {timing['finished_at_kst']} KST**.

Wall: **{wall:.3f} s**. Source authoring until pipeline start: **{timing['source_authoring_until_first_pipeline_start_seconds']:.3f} s**. Pure grid build: **{timing['authored_grid_build_seconds']:.3f} s**. Native write/roundtrip: **{timing['native_write_roundtrip_seconds']:.3f} s**. Surface build: **{timing['surface_build_seconds']:.3f} s**. Actual rendering: **{render_seconds:.3f} s**. Pipeline total: **{timing['pipeline_seconds']:.3f} s**. Final native validation: **{validation['elapsed_seconds']:.3f} s**. Timed production starts at the first recorded clock sample after brief reading; the earlier read is not assigned an invented duration.

## Limits and references

Glass is intentionally opaque blue-gray. The dishwasher has a single static lowered-door pose; remaining doors/lids are closed. Functional elements are stylized and chunky so their voids survive reduction; this is not a mechanical appliance simulation. The single specified camera does not expose every underside feature, so hidden functional geometry is additionally checked directly in native data. No UVs or bitmap materials are required for the supplied solid palette. No external reference artwork was used. The binding reference was `../BRIEF.md`; read-only generic utilities were `../../_tools/voxelkit.py` and `../../_tools/blender_pipeline.py`. No other batch geometry or creative resource was read or reused. Cross-review is coordinated separately by main. Fast mode is not exposed by the spawn API and is not claimed.
'''
    (ROOT / 'RESULT.md').write_text(result, encoding='utf-8')
    plan = (ROOT / 'PLAN.md').read_text(encoding='utf-8').replace('- [ ]', '- [x]')
    (ROOT / 'PLAN.md').write_text(plan, encoding='utf-8')
    # Exclude mutable cache and this manifest itself, and freeze all delivery evidence.
    files = [p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts
             and p.name != 'frozen_file_hashes.json']
    write('frozen_file_hashes.json', {'algorithm': 'SHA256', 'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
                                    'sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(files)}})
    print(json.dumps({'status': 'ready_for_review', 'wall_seconds': wall, 'render_seconds': render_seconds,
                      'frozen_files': len(files)}))


if __name__ == '__main__':
    main()
