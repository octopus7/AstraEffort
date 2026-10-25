"""Write concise delivery records from measured build and saved validation evidence."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import importlib.util

ROOT = Path(__file__).resolve().parent

def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))

def write(name, data):
    (ROOT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

status = read('STATUS.json')
initial = read('build_validation_initial.json')
fix = read('build_validation.json')
if len(fix.get('assets', [])) == 1:
    write('build_validation_loader_fix.json', fix)
else:
    fix = read('build_validation_loader_fix.json')
initial_assets = {record['asset']: record for record in initial['assets']}
initial_assets.update({record['asset']: record for record in fix['assets']})
merged = {**initial, 'finished_at_utc': fix['finished_at_utc'], 'elapsed_seconds': initial['elapsed_seconds'] + fix['elapsed_seconds'], 'assets': list(initial_assets.values()), 'build_passes': ['build_validation_initial.json', 'build_validation_loader_fix.json'], 'elapsed_basis': 'Sum of measured initial full build and loader-only demonstrated defect fix; not wall duration'}
write('build_validation.json', merged)

validation = read('validation_export.json')
function = read('validation_function.json')
assert validation['passed'] and validation['asset_count'] == 4 and validation['variant_count'] == 8
assert function['passed'] and function['check_count'] == 22
captures = read('capture_manifest.json')['captures']
assert len(captures) == 8
assert len({(c['asset'], c['variant']) for c in captures}) == 8
for slug in initial_assets:
    pair = [c for c in captures if c['asset'] == slug]
    assert pair[0]['settings'] == pair[1]['settings']
for capture in captures:
    assert sha(ROOT / capture['image']) == capture['image_sha256']

spec = importlib.util.spec_from_file_location('construction_build', ROOT / 'build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
names = ['empty', 'equipment yellow', 'upper yellow', 'recessed ochre', 'rubber and mechanism', 'slate steel', 'bare steel', 'warm ivory', 'light trim', 'blue glazing', 'glazing highlight', 'orange lamp and hub', 'concrete and muted steel']
write('palette.json', {'theme': 'construction', 'materials': 'Opaque flat per-face palette colors; no texture UV required', 'colors': [{'index': i, 'name': name, 'rgba': list(rgba)} for i, (name, rgba) in enumerate(zip(names, build.PALETTE))]})
reference = ROOT.parents[1] / 'REF' / 'voxel' / 'construction' / 'reference.png'
write('source_manifest.json', {'authorship': 'Four newly authored native voxel grids in pure make_assets(); only this theme reference and generic parent tools consulted', 'reference': {'path': 'REF/voxel/construction/reference.png', 'sha256': sha(reference), 'role': 'Main-generated design reference, never scene evidence'}, 'sources': {name: sha(ROOT / name) for name in ('build.py', 'validate_function.py', 'run_process.py', 'finish_records.py')}, 'shared_read_only_utilities': {name: sha(ROOT.parent / '_tools' / name) for name in ('voxelkit.py', 'blender_pipeline.py', 'verify_theme.py')}, 'half_resolution': 'Native conservative 2x2x2 nonempty-majority reduction, with doubled meters/cell. No half-only corrections.'})

processes = [read(name) for name in ('build_process.json', 'fix_loader_process.json', 'verify_process.json')]
assert all(p['exit_code'] == 0 for p in processes)
write('process_timing.json', {'processes': processes, 'blender_process_seconds_total': sum(p['elapsed_seconds'] for p in processes), 'build_and_render_process_seconds': sum(p['elapsed_seconds'] for p in processes[:2]), 'fresh_format_validation_process_seconds': processes[2]['elapsed_seconds'], 'final_native_probe_seconds': function['elapsed_seconds'], 'waiting_seconds': 0, 'waiting_basis': 'No application queue or mutex used; processes launched directly within their assigned four-thread limit', 'image_generation_seconds': 0, 'image_generation_basis': 'Main generated the reference; worker did not invoke image generation'})

now = datetime.now(timezone.utc)
visual = {'reviewed_at_utc': now.isoformat(), 'reviewer': 'Construction worker; actual primary PNGs opened and visually inspected', 'preview_count': 8, 'captures': [{'asset': c['asset'], 'variant': c['variant'], 'image': c['image'], 'sha256': c['image_sha256']} for c in captures], 'findings': ['Rounded mixer drum, six wheels, rear hopper and discharge channel are readable in both sizes.', 'Hollow loader bucket and twin lift arms are readable; the demonstrated arm-tip intrusion was corrected and both final renders inspected.', 'Crane open lattice, four structural support shoes, paired ropes, suspended block and blunt open hook remain readable at both sizes.', 'Office doorway, framed glazing, access steps, corrugation and roof are readable at both sizes.'], 'documented_fix': {'issue': 'Lift-arm capsules protruded through the loader back wall into the scoop', 'before_native_occupied_cells_in_tested_cavity': {'large': 144, 'half': 36}, 'fix': 'Clear the intended bucket interior at the source-grid level while retaining the back wall and arm connection behind it', 'final_native_occupied_cells_in_tested_cavity': {'large': 0, 'half': 0}, 'before_images': ['defect_evidence/loader_large_before.png', 'defect_evidence/loader_half_before.png']}, 'probe_correction': 'Initial office glass point hit a center mullion; moved the probe to the pane without changing office geometry.'}
write('visual_review.json', visual)

start = datetime.fromisoformat(status['started_at_utc'].replace('Z', '+00:00'))
elapsed = (now - start).total_seconds()
kst = timezone(timedelta(hours=9))
limitations = ['Static assets: no rig, animation, collision, LOD chain, or game-engine integration.', 'Flat opaque glazing; site-office interior is not modeled.', 'Conservative half reduction thickens some lattice and cable details and simplifies small tread, grille and trim colors.', 'Crane feet and mechanism checks verify modeled geometry, not real engineering load capacity.', 'Initial brief/reference reading occurred before the first recorded clock and is unmeasured.', 'Pre-existing ValveSource addon handler emitted a missing scene.vs warning during import; the fresh generic verifier finished with zero validation errors and process exit code 0. No addon changes were made.']
status.update(status='ready_for_review', finished_at_utc=now.isoformat(), finished_at_kst=now.astimezone(kst).isoformat(), elapsed_seconds=elapsed, validation_summary={'fresh_formats_passed': True, 'assets': 4, 'variants': 8, 'fresh_format_imports': 24, 'native_function_checks': 22, 'primary_previews_visually_inspected': 8, 'same_camera_pairs': 4}, blockers=[], limitations=limitations)
write('STATUS.json', status)

rows = []
for slug, pair in initial_assets.items():
    a, b = pair['large'], pair['half']
    shape = lambda values: ' × '.join(str(n) for n in values)
    rows.append(f"| {slug} | {shape(a['grid_size'])} | {shape(b['grid_size'])} | {a['voxel_size_m']:.3f} / {b['voxel_size_m']:.3f} |")
text = f'''# Construction — ready for review

Four original assets and eight size variants are frozen under `assets/<asset>/<large|half>/`. Every variant includes authoritative VOX 150, BLEND, GLB, FBX, actual 768px `preview.png`, and metadata with hashes. `build.py` contains the pure native-grid source; `palette.json` and `source_manifest.json` document palette and provenance.

| Asset | Large grid | Half grid | Meters/cell large / half |
|---|---|---|---|
{chr(10).join(rows)}

All grids retain the same physical extent across sizes. Half is genuinely reduced native occupancy. Same-camera Cycles CPU renders use four threads, 24 samples and flat opaque palette materials; camera, time and hashes are in `capture_manifest.json`.

Fresh verification passed for all eight saved native files and all 24 BLEND/GLB/FBX imports: native grids/palettes, hashes, bounds, surface area, outward boundary triangles, grid alignment and material assignments. All 22 saved-native mechanism checks pass. These cover the mixer chute/hopper, hollow loader scoop and separated arms, crane shaft/truss/ropes/open hook/four feet, and office glazing/steps. All eight final primary previews were opened and inspected (`visual_review.json`).

One demonstrated defect was fixed: loader lift-arm tips intruded into the scoop. The failing native check found 144 large / 36 half occupied cells in the tested cavity. A source-grid trim removed them; the final count is zero in both sizes. Only the loader pair was rebuilt. Before images and failed checks are preserved. The office probe was corrected from a mullion to the glass; office geometry was unchanged.

Recorded start: **{start.isoformat()} UTC / {start.astimezone(kst).isoformat()} KST**. Finish: **{now.isoformat()} UTC / {now.astimezone(kst).isoformat()} KST**. Wall: **{elapsed:.3f}s**. Initial build: **{processes[0]['elapsed_seconds']:.3f}s**; loader fix: **{processes[1]['elapsed_seconds']:.3f}s**; fresh format verification: **{processes[2]['elapsed_seconds']:.3f}s**; final native probes: **{function['elapsed_seconds']:.3f}s**. No queue wait or worker image generation. Preliminary brief/reference reading time is unmeasured.

Limitations: static models with no rig, animation, collision, LOD chain or engine integration; opaque windows and no office interior; fine grille/tread/lattice details simplify at half resolution. Crane support checks are geometric, not engineering certification. The pre-existing ValveSource addon emitted a missing `scene.vs` handler warning during imports; the verifier completed with zero validation errors and exit 0. Reference: `REF/voxel/construction/reference.png`, generated by main and used only as design input. No other-theme creative reads/reuse, shared Blender mutation, installs, extra agents or Git actions.

Evidence: `validation_export.json`, `validation_function.json`, `build_validation.json`, `capture_manifest.json`, `visual_review.json`, `process_timing.json`, process logs, and `frozen_manifest.json`. No further changes are planned pending parent review.
'''
(ROOT / 'RESULT.md').write_text(text, encoding='utf-8')
paths = [p for p in ROOT.rglob('*') if p.is_file() and p.name != 'frozen_manifest.json' and '__pycache__' not in p.parts and p.suffix != '.blend1']
write('frozen_manifest.json', {'frozen_at_utc': now.isoformat(), 'file_count': len(paths), 'files': {str(p.relative_to(ROOT)).replace('\\', '/'): {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(paths)}})
print(json.dumps({'status': 'ready_for_review', 'elapsed_seconds': elapsed, 'frozen_files': len(paths), 'format_validation_passed': validation['passed'], 'native_checks': function['check_count']}))
