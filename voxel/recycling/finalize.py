"""Freeze measured recycling delivery evidence after all eight previews were inspected."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import importlib.util
import json

root = Path(__file__).resolve().parent
load = lambda name: json.loads((root / name).read_text(encoding='utf-8'))
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, value):
    (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

status = load('STATUS.json')
build_check = load('build_validation.json')
export_check = load('validation_export.json')
function_check = load('validation_function.json')
build_process = load('build_process.json')
verify_process = load('verify_process.json')
assert build_check['passed'] and len(build_check['assets']) == 4
assert export_check['passed'] and export_check['asset_count'] == 4 and export_check['variant_count'] == 8
assert function_check['passed'] and function_check['check_count'] == 20
assert build_process['exit_code'] == verify_process['exit_code'] == 0
captures = load('capture_manifest.json')['captures']
assert len(captures) == 8
for record in build_check['assets']:
    pair = [c for c in captures if c['asset'] == record['asset']]
    assert len(pair) == 2 and pair[0]['settings'] == pair[1]['settings']
for c in captures:
    assert digest(root / c['image']) == c['image_sha256']

module_spec = importlib.util.spec_from_file_location('recycling_source', root / 'build.py')
source = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(source)
names = ['empty', 'deep recycling green', 'upper green', 'recessed green', 'warm cladding', 'ivory trim', 'belt and tire charcoal', 'steel frame', 'silver hardware', 'safety yellow', 'recessed yellow', 'dark blue glazing and screen', 'glass highlight', 'tail lamps and stop control', 'compacted cardboard', 'light cardboard layers']
save('palette.json', {'theme': 'recycling', 'material_mode': 'Flat opaque per-face palette materials; no texture UV needed', 'colors': [{'index': i, 'name': name, 'rgba': list(color)} for i, (name, color) in enumerate(zip(names, source.COLORS))]})
ref = root.parents[1] / 'REF' / 'voxel' / 'recycling' / 'reference.png'
save('source_manifest.json', {'authorship': 'Original native voxel geometry in pure make_assets(); no cross-theme creative source, palette or asset reuse', 'reference': {'path': 'REF/voxel/recycling/reference.png', 'sha256': digest(ref), 'purpose': 'Main-generated design input only; previews are actual Blender renders'}, 'source_sha256': {name: digest(root / name) for name in ('build.py', 'verify_functions.py', 'process.py', 'finalize.py')}, 'generic_read_only_tools': {name: digest(root.parent / '_tools' / name) for name in ('voxelkit.py', 'blender_pipeline.py', 'verify_theme.py')}, 'half_method': 'Conservative 2x2x2 native nonempty-majority reduction, double meters/cell, no size-only corrections'})

now = datetime.now(timezone.utc)
kst = timezone(timedelta(hours=9))
start = datetime.fromisoformat(status['started_at_utc'].replace('Z', '+00:00'))
elapsed = (now - start).total_seconds()
save('process_timing.json', {'started_at_utc': start.isoformat(), 'finished_at_utc': now.isoformat(), 'elapsed_wall_seconds': elapsed, 'build_process': build_process, 'format_verification_process': verify_process, 'native_function_check_seconds': function_check['elapsed_seconds'], 'blender_process_seconds_total': build_process['elapsed_seconds'] + verify_process['elapsed_seconds'], 'build_pass_count': 1, 'geometry_fix_passes': 0, 'queue_wait_seconds': 0, 'worker_image_generation_seconds': 0, 'notes': ['Processes launched directly with four threads; no application queue was used.', 'Main supplied the design reference; worker made no image-generation call.']})
save('visual_review.json', {'reviewed_at_utc': now.isoformat(), 'reviewer': 'Recycling worker; opened all eight final actual primary PNGs', 'preview_count': 8, 'captures': [{'asset': c['asset'], 'variant': c['variant'], 'image': c['image'], 'sha256': c['image_sha256']} for c in captures], 'findings': {'collection_truck': 'Rear hopper depth, rising cheeks, sloped floor and low loading lip are clear in both sizes. Cab faces +Y; functional loading face is -Y.', 'sorting_machine': 'Belt, front roller, two sensor heads, separate drive motor and both open funnels are readable. The nearer funnel clearly shows its interior; native checks verify both throats.', 'compactor': 'Raised ram/platen, open chamber, strapped bale and separate controls remain clear in both sizes.', 'recycling_center': 'Tall receiving portal, lower annex and three distinct open collection-bin bays remain readable in both sizes.'}, 'demonstrated_defects': [], 'geometry_fix_passes': 0})

warnings = []
verify_log = (root / 'verify.log').read_text(encoding='utf-8', errors='replace')
if "has no attribute 'vs'" in verify_log:
    warnings.append('Existing ValveSource addon handler emitted a missing scene.vs warning while importing. The generic verifier completed with no validation errors and exit 0; no addon was modified.')
limitations = ['Static models without rig, animation, collision, LOD chain or engine integration.', 'Opaque truck glazing; machinery and feedstock do not simulate motion or sorting.', 'Press is shown idle with raised platen. Geometry checks do not certify real machine safety.', 'The receiving hall is hollow; the annex is modeled only to bay depth.', 'Half resolution simplifies small metal ribs, tread and trim; native functional openings remain clear.', *warnings]
status.update(status='ready_for_review', finished_at_utc=now.isoformat(), finished_at_kst=now.astimezone(kst).isoformat(), elapsed_seconds=elapsed, validation_summary={'native_variants': 8, 'fresh_blend_glb_fbx_imports': 24, 'format_checks_passed': True, 'functional_checks': 20, 'functional_checks_passed': True, 'primary_previews_inspected': 8, 'same_camera_pairs': 4}, blockers=[], limitations=limitations)
save('STATUS.json', status)

rows = []
for record in build_check['assets']:
    a, b = record['large'], record['half']
    fmt = lambda v: ' × '.join(str(n) for n in v)
    rows.append(f"| {record['asset']} | {fmt(a['grid_size'])} | {fmt(b['grid_size'])} | {a['voxel_size_m']:.3f} / {b['voxel_size_m']:.3f} |")
warning_text = (' ' + warnings[0]) if warnings else ''
report = f'''# Recycling — ready for review

Four newly authored models and eight native size variants are frozen under `assets/<asset>/<large|half>/`. Each variant contains VOX 150, BLEND, GLB, FBX, actual 768px `preview.png`, and hashed metadata. Pure source is `build.py`; palette and provenance are in `palette.json` and `source_manifest.json`.

| Asset | Large grid | Half grid | Meters/cell large / half |
|---|---|---|---|
{chr(10).join(rows)}

All large axes are even, with longest axis 128; half axes are exactly divided by two, longest 64, with doubled cell size and equal physical grid extent. Native occupancy is authoritative. Same-camera Cycles CPU previews use four threads and 24 samples; `capture_manifest.json` contains camera settings, actual capture times and hashes.

Fresh generic verification passed all eight saved VOX files and **24 BLEND/GLB/FBX imports**, including palette/grid/hash/bounds checks, exact exposed surfaces, outward normals, grid alignment and valid materials. All **20 saved-native functional checks** passed: rear hopper cavity/access; both sorter funnels and lateral throats, belt continuity and sensor clearance; open compactor chamber, ram/platen and strapped bale; hollow receiving hall and three separate open bins. All **eight primary previews were opened and inspected**. One build, zero geometry-fix passes.

Start: **{start.isoformat()} UTC / {start.astimezone(kst).isoformat()} KST**. Finish: **{now.isoformat()} UTC / {now.astimezone(kst).isoformat()} KST**. Wall: **{elapsed:.3f}s**. Build/render process: **{build_process['elapsed_seconds']:.3f}s**. Fresh format verification process: **{verify_process['elapsed_seconds']:.3f}s**. Native function checks: **{function_check['elapsed_seconds']:.3f}s**. Queue wait and worker image generation: **0s**.

Limitations: static models without rig, animation, collision, LOD chain or engine integration; opaque glazing; no machine simulation or safety certification. The truck's loading end faces -Y and its cab faces +Y to expose the hopper in the primary preview. Receiving hall is hollow; annex interior stops at bay depth. Small ribs/tread/trim simplify at half resolution.{warning_text}

Reference: `REF/voxel/recycling/reference.png` supplied by main, used as design input only. No other-theme creative resources, live Blender scene, installations, Git actions or extra agents were used. Evidence: `validation_export.json`, `validation_function.json`, `build_validation.json`, `visual_review.json`, `capture_manifest.json`, process logs/timing, and `frozen_manifest.json`. Waiting for parent review; no further edits planned.
'''
(root / 'RESULT.md').write_text(report, encoding='utf-8')
files = [p for p in root.rglob('*') if p.is_file() and p.name != 'frozen_manifest.json' and '__pycache__' not in p.parts and p.suffix != '.blend1']
save('frozen_manifest.json', {'frozen_at_utc': now.isoformat(), 'file_count': len(files), 'files': {p.relative_to(root).as_posix(): {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in sorted(files)}})
print(json.dumps({'status': status['status'], 'elapsed_seconds': elapsed, 'frozen_files': len(files), 'variant_count': 8, 'fresh_format_imports': 24, 'native_checks': 20, 'geometry_fix_passes': 0}))
