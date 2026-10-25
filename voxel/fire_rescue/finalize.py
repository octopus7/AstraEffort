"""Freeze concise worker evidence from actual saved verification records."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json

ROOT = Path(__file__).resolve().parent
def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8-sig'))
def write(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

native = read('validation_native_features.json')
exports = read('validation_export.json')
first_exports = read('validation_export_initial.json')
capture = read('capture_manifest.json')
assert native['passed'] and exports['passed'] and exports['variant_count'] == 8
assert len(capture['captures']) == 8
assert sum(len(r['checks']) for r in native['records']) == 46
assert read('fix_build_process.json')['exit_code'] == 0
assert read('final_validation_process.json')['exit_code'] == 0
slugs = ['fire_engine', 'rescue_robot', 'fire_station', 'rescue_helicopter']
review_notes = {
    'fire_engine': 'Cab, wheels, shutter lines, hose reel and open ladder rungs readable. Final half correction inspected in actual render.',
    'rescue_robot': 'Distinct tracked chassis, articulated arm, separated gripper jaws and one optical sensor; no character face.',
    'fire_station': 'Both tall vehicle entrances visibly open and deep. Building floor, piers, pitched roof and hose tower readable.',
    'rescue_helicopter': 'Rounded blue cockpit, main/tail rotors, separate skids, rescue opening and hanging winch hook readable.'
}
reviews = []
for slug in slugs:
    for variant in ('large', 'half'):
        p = ROOT / 'assets' / slug / variant / 'preview.png'
        if slug != 'fire_engine':
            original = next(r for r in first_exports['records'] if r['asset'] == slug and r['variant'] == variant)
            assert digest(p) == original['sha256']['preview.png']
        reviews.append(dict(asset=slug, variant=variant, image=str(p.relative_to(ROOT)).replace('\\','/'),
                            sha256=digest(p), inspected=True, notes=review_notes[slug]))
write('visual_review.json', dict(actual_saved_previews=True, reviewed_by='worker3',
      final_review_recorded_at_utc='2026-10-23T16:50:54Z', reviewed_count=8,
      unchanged_non_engine_previews_match_first_verified_hashes=True, records=reviews))

started = datetime.fromisoformat('2026-10-23T16:33:57+00:00')
finished = datetime.now(timezone.utc)
kst = timezone(timedelta(hours=9))
times = {name: read(name + '_process.json')['elapsed_seconds'] for name in ('build', 'validation', 'fix_build', 'final_validation')}
times['native_feature_validation_seconds'] = native['elapsed_seconds']
times['startup_aborted_tool_invocation_wall_seconds'] = 1.4395301
times['startup_aborted_process_seconds'] = None
times['timing_note'] = 'Initial PowerShell process wrappers measured wall time but returned null ExitCode. Final fix and fresh validation use subprocess.run and capture exit 0. The first startup-aborted Blender invocation has only tool-wall timing, not process timing.'
write('timing_summary.json', dict(started_at_utc=started.isoformat(), started_at_kst=started.astimezone(kst).isoformat(),
      finished_at_utc=finished.isoformat(), finished_at_kst=finished.astimezone(kst).isoformat(),
      elapsed_seconds=(finished-started).total_seconds(), processes=times,
      successful_build_invocations=2, full_builds=1, targeted_engine_pair_fixes=1,
      startup_aborted_invocations=1, worker_image_generation_seconds=0))
status = dict(theme='fire_rescue', worker=3, status='ready_for_review',
              started_at_utc=started.isoformat(), started_at_kst=started.astimezone(kst).isoformat(),
              finished_at_utc=finished.isoformat(), finished_at_kst=finished.astimezone(kst).isoformat(),
              elapsed_seconds=(finished-started).total_seconds(), assets=slugs, variant_count=8,
              validation_summary='8 native grids, 24 fresh mesh-format imports and 46 critical native feature checks pass; all 8 actual primary previews inspected.',
              final_validation_exit_code=0, blockers=[])
write('STATUS.json', status)
rows = []
for slug in slugs:
    a = read(f'assets/{slug}/large/metadata.json')
    b = read(f'assets/{slug}/half/metadata.json')
    assert [x*2 for x in b['grid_size']] == a['grid_size']
    assert a['grid_extents_m'] == b['grid_extents_m']
    rows.append('| ' + slug + ' | ' + '×'.join(map(str, a['grid_size'])) + ' → ' + '×'.join(map(str, b['grid_size'])) + ' | ' + str(a['occupied_voxels']) + ' / ' + str(b['occupied_voxels']) + ' |')
result = f'''# Fire rescue — ready for review

Four original models and eight native resolution variants are frozen under `voxel/fire_rescue`. Each `assets/ASSET/{{large,half}}/` contains VOX 150, BLEND, GLB, FBX, `metadata.json` and the actual 768×768 `preview.png`. Source: `build.py`; opaque palette: `palette.json`; camera/render evidence: `capture_manifest.json` and `visual_review.json`.

| Asset | Large → half grid | Occupied voxels large / half |
|---|---|---|
{chr(10).join(rows)}

All half axes are exactly halved; cell size doubles and physical grid extents remain equal. Shapes are native stepped voxel boundaries with flat palette materials. The station has two open bays and its own structural floor. The other three assets have no permanent base.

Validation: `validation_export.json` passes all eight independent VOX reparses and 24 fresh BLEND/GLB/FBX inspections (occupancy, palette, file hashes, bounds, triangle count, exposed surface area, outward boundary orientation, material indices and grid alignment). `validation_native_features.json` passes all 46 checks, including both station entry passages, ladder opening, gripper gap, cabin loading opening, skid clearance, hook throat and cable continuity. Final validation process exit code: **0**. All eight final primary previews were visually inspected; six unchanged preview hashes match the initially verified files.

One demonstrated correction: reduction erased the half truck's shutter lines and hose-turn separation. A documented native half-grid postprocess restores those details; only the engine pair was rebuilt and re-inspected. `fix_evidence/` preserves the observed first half render and initial native-check report. The initial cable probe included the amber hook connection while requiring black cable color; its corrected span now tests the actual black cable only.

Start: **{started.isoformat()} UTC / {started.astimezone(kst).isoformat()} KST**. Finish: **{finished.isoformat()} UTC / {finished.astimezone(kst).isoformat()} KST**. Wall: **{(finished-started).total_seconds():.3f} s**. Full build **{times['build']:.3f} s**; necessary engine fix **{times['fix_build']:.3f} s**; first/final fresh validation **{times['validation']:.3f} / {times['final_validation']:.3f} s**; final native probes **{native['elapsed_seconds']:.3f} s**. See `timing_summary.json` and process logs. One prior startup aborted on an installed Blender load handler; successful isolated runs use `--factory-startup`, four threads and `--python-exit-code 1`. Initial PowerShell exit-code capture was null; final subprocess records capture exit 0. No worker image generation.

Limitations: static models, opaque stylized glazing, no rig, animation, simulation, collision, LOD chain or engine integration. Smaller bolt/roof detail simplifies at half resolution. No interactive GUI checks were claimed. Design reference: parent-supplied `REF/voxel/fire_rescue/reference.png`, viewed as input only; all scene evidence is actual Blender rendering. No other-theme creative resources were inspected or reused.
'''
(ROOT / 'RESULT.md').write_text(result, encoding='utf-8')
required = [ROOT / n for n in ('build.py', 'palette.json', 'capture_manifest.json', 'visual_review.json',
            'validation_export.json', 'validation_native_features.json', 'RESULT.md', 'STATUS.json', 'timing_summary.json')]
required += sorted(p for p in (ROOT / 'assets').rglob('*') if p.is_file())
write('delivery_manifest.json', dict(theme='fire_rescue', frozen_at_utc=finished.isoformat(),
      files=[dict(path=str(p.relative_to(ROOT)).replace('\\','/'), bytes=p.stat().st_size, sha256=digest(p)) for p in required]))
print(json.dumps(dict(status=status, timing_seconds=times), indent=2))
