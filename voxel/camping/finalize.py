"""Freeze review evidence and delivery hashes after all required checks pass."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json

ROOT = Path(__file__).resolve().parent
UTC = timezone.utc
KST = timezone(timedelta(hours=9))
read = lambda name: json.loads((ROOT / name).read_text(encoding='utf-8-sig'))
write = lambda name, value: (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

build = read('build_validation.json')
exports = read('validation_export.json')
functional = read('validation_functional.json')
bt = read('build_timing.json')
vt = read('verify_timing.json')
captures = read('capture_manifest.json')
assert build['passed'] and exports['passed'] and functional['passed']
assert exports['asset_count'] == 4 and exports['variant_count'] == 8 and not exports['errors']
assert sum(len(r['imports']) for r in exports['records']) == 24
assert functional['probe_count'] == 34 and vt['exit_code'] == 0
assert captures['actual_blender_renders'] and len(captures['captures']) == 8

names = ['camper_van', 'log_cabin', 'generator_trailer', 'shower_block']
comments = {
    'camper_van': 'Rounded touring body, broad windshield, separate framed windows and entry, boarding sill, stowed awning and tires are readable. Half simplifies the center windshield divider.',
    'log_cabin': 'Stepped gable roof, horizontal log shell, framed window, porch rail wings and central stair/door route remain readable at both sizes.',
    'generator_trailer': 'Open hitch ring, A-frame gap, support foot, wheel/fender, slotted ventilation and control panel remain readable at both sizes.',
    'shower_block': 'Three doorways, fixed open central door, heater cylinder and copper connection are visible at both sizes. The interior shower is partly occluded in the common camera; its native occupancy is separately probed.'
}
review = []
for name in names:
    pair = [c for c in captures['captures'] if c['asset'] == name]
    assert {c['variant'] for c in pair} == {'large', 'half'}
    assert pair[0]['settings'] == pair[1]['settings'], 'paired cameras/settings differ'
    for cap in pair:
        assert sha(ROOT / cap['image']) == cap['image_sha256']
        review.append({'asset': name, 'variant': cap['variant'], 'image': cap['image'], 'image_sha256': cap['image_sha256'], 'actual_primary_preview_inspected': True, 'required_correction': False, 'observations': comments[name]})
write('visual_review.json', {'recorded_at_utc': datetime.now(UTC).isoformat(), 'reviewer': 'camping authoring worker; main independent review pending', 'reviewed_count': 8, 'same_camera_pairs_checked': 4, 'optional_views_generated': 0, 'records': review})

ref = ROOT.parents[1] / 'REF' / 'voxel' / 'camping' / 'reference.png'
write('source_manifest.json', {'reference': {'path': 'REF/voxel/camping/reference.png', 'sha256': sha(ref), 'role': 'Parent-provided design input; not scene evidence'}, 'authored_source': 'voxel/camping/build.py', 'palette': 'voxel/camping/palette.json', 'generic_tools_read': ['voxel/_tools/voxelkit.py', 'voxel/_tools/blender_pipeline.py', 'voxel/_tools/verify_theme.py'], 'external_references': [], 'worker_image_generation': False, 'half_manual_corrections': []})
bt['completion_evidence'] = 'All four VOXEL_ASSET_COMPLETE markers, build_validation.json passed, eight renders, and subsequent independent verification passed.'
bt['exit_code_note'] = 'The original Start-Process wrapper used WaitForExit and returned a null child ExitCode. The null is preserved. The launcher exited 0; future wrapper calls now use Start-Process -Wait. No second build was run.'
bt['launcher_exit_code'] = 0
write('build_timing.json', bt)

status = read('STATUS.json')
began = datetime.fromisoformat(status['started_at_utc'].replace('Z', '+00:00'))
finished = datetime.now(UTC)
elapsed = (finished - began).total_seconds()
status.update(status='ready_for_review', finished_at_utc=finished.isoformat(), finished_at_kst=finished.astimezone(KST).isoformat(), elapsed_seconds=elapsed, build_seconds=bt['elapsed_seconds'], build_pipeline_seconds=build['elapsed_seconds'], verification_seconds=vt['elapsed_seconds'], verification_internal_seconds=exports['elapsed_seconds'], native_probe_seconds=functional['elapsed_seconds'], build_count=1, correction_rebuild_count=0, validation_summary='8 VOX roundtrips; 24 fresh BLEND/GLB/FBX imports; 34 saved-native functional probes; 8 inspected primary renders; 4 same-camera pairs.', blockers=[], review_owner='coordinating conversation', git_performed=False)
write('STATUS.json', status)

lines = [
    '# Camping result',
    '',
    'Four original models are **ready for coordinating review**: `camper_van`, `log_cabin`, `generator_trailer`, and `shower_block`. Each has native VOX, BLEND, GLB, FBX, metadata and an actual 768×768 Cycles preview under `assets/<asset>/{large,half}/`.',
    '',
    f"Recorded authoring start: {began.isoformat()} / {began.astimezone(KST).isoformat()} KST. Finish: {finished.isoformat()} / {finished.astimezone(KST).isoformat()} KST. Elapsed wall: **{elapsed:.3f} s**. One isolated four-thread build: **{bt['elapsed_seconds']:.3f} s** (pipeline {build['elapsed_seconds']:.3f} s); independent verifier: **{vt['elapsed_seconds']:.3f} s** (internal {exports['elapsed_seconds']:.3f} s); saved-native probes: **{functional['elapsed_seconds']:.3f} s**. No correction rebuilds or optional renders.",
    '',
    'The cream/olive camper has a sloped windshield, entry and stowed awning. The warm log cabin has rounded log ends, a stepped clay roof and clear porch access. The trailer has an open ring coupling, A-frame, support foot, wheel pair, real ventilation slots and controls. The three-stall shower building has an open central door, shower fixture and side-mounted heater/plumbing. Building foundations are structural; there is no campsite base.',
    '',
    '**Validation:** All eight native roundtrips passed. Independent `validation_export.json` reports 4 models, 8 variants, 24 fresh BLEND/GLB/FBX imports, and no errors; verifier exit code is 0. Bounds, palette assignment, exposed outward surfaces, grid alignment, triangle counts, finite geometry and geometry-only exchange exports passed. `validation_functional.json` records 34 saved-native probes for access gaps, hitch opening, ventilation and fixtures. All eight primary previews were inspected and four matching-camera pairs checked (`visual_review.json`, `capture_manifest.json`).',
    '',
    'Every large grid has even axes and longest axis 128; half grids divide all axes by two, with 0.10 m cells versus 0.05 m large cells and unchanged physical grid extents. Reduction is conservative native occupancy with no manual half corrections. `build.py`, `palette.json`, `source_manifest.json`, logs, validation records and `frozen_files.json` preserve reproducibility and evidence.',
    '',
    '**Limits:** Opaque palette windows, static parts/doors, no furnished interiors, animation, rig, collision, simulation or engine integration. Half reduction simplifies small dividers/details and may expand boundaries by one large cell. The shower head is partly occluded in the primary view and is checked in native occupancy. The original build wrapper lost the child exit code (null preserved in `build_timing.json`); pipeline completion and independent verification establish the finished output. The verifier captured exit 0.',
    '',
    '**Reference:** Only `REF/voxel/camping/reference.png`, supplied by the parent, informed this original theme. No external reference downloads, image generation, cross-theme assets, shared scene changes or Git actions. Main performs final independent review and commit.',
]
(ROOT / 'RESULT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
plan = (ROOT / 'PLAN.md').read_text(encoding='utf-8').replace('- [ ]', '- [x]')
(ROOT / 'PLAN.md').write_text(plan, encoding='utf-8')
files = []
for path in sorted(ROOT.rglob('*')):
    if path.is_file() and '__pycache__' not in path.parts and path.name != 'frozen_files.json':
        files.append({'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha(path)})
write('frozen_files.json', {'theme': 'camping', 'frozen_at_utc': datetime.now(UTC).isoformat(), 'status': 'ready_for_review', 'file_count': len(files), 'files': files, 'self_excluded': 'frozen_files.json', 'excluded_transients': ['__pycache__']})
assert all(sha(ROOT / f['path']) == f['sha256'] for f in files)
print(json.dumps({'status': status['status'], 'elapsed_seconds': elapsed, 'frozen_files': len(files), 'models': exports['asset_count'], 'variants': exports['variant_count'], 'fresh_imports': 24, 'functional_probes': functional['probe_count'], 'previews_inspected': len(review)}, indent=2))
