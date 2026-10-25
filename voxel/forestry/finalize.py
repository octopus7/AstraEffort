"""Record this finite delivery after successful saved-file verification and visual review."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json

root = Path(__file__).resolve().parent
load = lambda p: json.loads((root / p).read_text(encoding='utf-8'))
write = lambda p, d: (root / p).write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding='utf-8')
status = load('STATUS.json')
validation = load('validation_export.json')
features = load('validation_features.json')
build = load('build_process.json')
verify = load('verify_process.json')
captures = load('capture_manifest.json')['captures']
assert validation['passed'] and validation['asset_count'] == 4 and validation['variant_count'] == 8
assert features['passed'] and features['check_count'] == 56
assert len(captures) == 8 and build['exit_code'] == verify['exit_code'] == 0
names = ['logging_harvester', 'timber_forwarder', 'sawmill', 'log_rack']
for name in names:
    pairs = [c for c in captures if c['asset'] == name]
    assert len(pairs) == 2 and pairs[0]['settings'] == pairs[1]['settings']
notes = {
    'logging_harvester': 'Four exposed feed rollers and central slot visible at both sizes; folded boom, opaque cab and stepped tires remain clear.',
    'timber_forwarder': 'Eight-wheel silhouette, loaded stake bunk and curved yellow grapple are readable at both sizes; top log remains enclosed by the open claws.',
    'sawmill': 'Open timber portal, transverse roller bed, input log and side lumber stack read at both sizes. Blade is partly hidden behind the right portal post in the required common view.',
    'log_rack': 'Three separate logs, cut-end rings, yellow stops, green cradles and individual structural feet remain visible at both sizes.'
}
now = datetime.now(timezone.utc)
write('visual_review.json', {'reviewer': 'worker1', 'recorded_at_utc': now.isoformat(),
    'actual_primary_previews_inspected': 8, 'method': 'Direct inspection of every final 768px PNG using view_image; no generated scene evidence or extra views.',
    'passed': True, 'records': [{'asset': c['asset'], 'variant': c['variant'], 'image': c['image'], 'image_sha256': c['image_sha256'], 'passed': True, 'observation': notes[c['asset']]} for c in captures]})
started = datetime.fromisoformat(status['started_at_utc'].replace('Z', '+00:00'))
finished = datetime.now(timezone.utc)
elapsed = (finished - started).total_seconds()
render_seconds = sum(c['elapsed_seconds'] for c in captures)
status.update(status='ready_for_review', finished_at_utc=finished.isoformat(),
    finished_at_kst=finished.astimezone(timezone(timedelta(hours=9))).isoformat(), elapsed_seconds=elapsed,
    frozen=True, process_timing_seconds={'build': build['elapsed_seconds'], 'fresh_three_format_validation': verify['elapsed_seconds'], 'saved_native_feature_checks': features['elapsed_seconds'], 'rendering_included_in_build': render_seconds},
    validation={'fresh_imports': 24, 'variants': 8, 'native_feature_checks': 56, 'actual_previews_inspected': 8, 'same_camera_pairs': 4, 'passed': True},
    limitations=['Static opaque palette assets; no rig, animation, collision, LOD chain or game-engine integration.', 'Sawmill blade is partly obscured by its portal post in the required common camera.', 'Conservative half reduction can expand occupied bounds by one large cell (0.05m).'], blockers=[])
write('STATUS.json', status)
text = f'''# Forestry — ready for review

Four original models and eight native variants are frozen under `assets/{{logging_harvester,timber_forwarder,sawmill,log_rack}}/{{large,half}}/`. Every variant contains VOX 150, BLEND, GLB, FBX, actual `preview.png`, and `metadata.json`.

| Model | Large grid | Half grid |
|---|---|---|
| logging_harvester | 128×96×128 | 64×48×64 |
| timber_forwarder | 80×128×120 | 40×64×60 |
| sawmill | 128×128×118 | 64×64×59 |
| log_rack | 128×70×104 | 64×35×52 |

Large cells are 0.05m; half cells are 0.10m with identical physical grid extent. Native colored occupancy is authoritative. The restrained green/ochre/timber palette, stepped curves, and functional geometry were newly authored in `build.py`; no other theme resources were read or reused. Reference input: `REF/voxel/forestry/reference.png` only.

One isolated four-thread Blender build completed with exit 0. All eight primary renders were directly inspected. `validation_export.json` records **24 fresh BLEND/GLB/FBX checks** across eight variants, including native hashes, correct palette indexing, bounds, exact exposed boundaries, outward normals, materials, triangles and export studio exclusion. `validation_features.json` records **56 passing saved-native probes**, including the harvester throat/four rollers, open forwarder grapple/stakes, sawmill portal/rollers/blade, rack log gaps and six cradles. All four camera pairs match. No correction or extra render pass was required.

Actual tracked start: **{status['started_at_utc']} / {status['started_at_kst']}**. Finish: **{status['finished_at_utc']} / {status['finished_at_kst']}**. Wall: **{elapsed:.3f}s**. Build process: **{build['elapsed_seconds']:.3f}s**, including **{render_seconds:.3f}s** of rendering. Fresh-format verifier process: **{verify['elapsed_seconds']:.3f}s**. Native feature probes: **{features['elapsed_seconds']:.3f}s**. No UE process or worker image-generation process was used. Exact commands and UTC process timing are in `build_process.json` and `verify_process.json`; logs, palette, capture manifest, source and visual notes are retained here.

Limits: static opaque palette assets; no rig, animation, collision, LOD chain or game-engine integration. The sawmill blade is partly hidden by the right portal post in the common view, while the open portal and feed rollers remain readable. Conservative half reduction may expand occupied bounds by one large cell (0.05m). No GUI inspection is claimed. Parent acceptance remains pending; no later theme was started.
'''
(root / 'RESULT.md').write_text(text, encoding='utf-8')
files = {}
for p in sorted(root.rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts and p.name != 'delivery_manifest.json':
        files[p.relative_to(root).as_posix()] = {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
write('delivery_manifest.json', {'theme': 'forestry', 'frozen_at_utc': finished.isoformat(), 'files': files})
print(json.dumps({'status': status['status'], 'elapsed_seconds': elapsed, 'files_frozen': len(files), 'build_seconds': build['elapsed_seconds'], 'verify_seconds': verify['elapsed_seconds']}, indent=2))
