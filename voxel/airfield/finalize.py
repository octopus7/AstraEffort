"""Freeze verified airfield deliverables and actual review/timing records."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json

root = Path(__file__).resolve().parent
def read(name):
    return json.loads((root/name).read_text(encoding='utf-8'))
def write(name, value):
    (root/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')

status = read('STATUS.json')
formats = read('validation_export.json')
features = read('validation_features.json')
build = read('build_process.json')
verify = read('verify_process.json')
captures = read('capture_manifest.json')['captures']
assert formats['passed'] and formats['asset_count']==4 and formats['variant_count']==8
assert features['passed'] and features['check_count']==42
assert len(captures)==8 and build['exit_code']==verify['exit_code']==0
for name in status['assets']:
    pair = [c for c in captures if c['asset']==name]
    assert len(pair)==2 and pair[0]['settings']==pair[1]['settings']

observations = {
    'propeller_plane': 'Broad blue-tipped wings, diagonal two-blade propeller, rounded cockpit and landing gear read clearly in both resolutions.',
    'airport_tug': 'Ivory/blue tug, rear power pack, wheeled ochre towbar and tall glazing remain recognizable at both sizes. Coupling eye opening is additionally checked in native occupancy.',
    'maintenance_hangar': 'Wide front portal and empty bay are clearly open at both sizes; arched roof, side windows and service door are legible. Rear equipment is dark under the common studio lighting.',
    'control_tower': 'Broad glazed cab remains readable above the low balcony rail and below the roof in both primary previews; native rays independently confirm unoccluded window cells.'
}
write('visual_review.json', dict(passed=True, reviewer='worker1', recorded_at_utc=datetime.now(timezone.utc).isoformat(), actual_primary_previews_inspected=8,
    method='Direct view_image inspection of all eight final 768px actual Blender PNGs; no optional views or generated scene evidence.',
    records=[dict(asset=c['asset'],variant=c['variant'],image=c['image'],sha256=c['image_sha256'],passed=True,observation=observations[c['asset']]) for c in captures]))
finished = datetime.now(timezone.utc)
start = datetime.fromisoformat(status['started_at_utc'].replace('Z','+00:00'))
duration = (finished-start).total_seconds()
render_time = sum(c['elapsed_seconds'] for c in captures)
visibility = {c['variant']:c['evidence']['unoccluded_glass_cells'] for c in features['checks'] if c['check'].startswith('Glazing visible')}
status.update(status='ready_for_review', finished_at_utc=finished.isoformat(), finished_at_kst=finished.astimezone(timezone(timedelta(hours=9))).isoformat(), elapsed_seconds=duration, frozen=True,
    process_timing_seconds=dict(build=build['elapsed_seconds'],rendering_included_in_build=render_time,fresh_three_format_validation=verify['elapsed_seconds'],saved_native_feature_checks=features['elapsed_seconds']),
    validation=dict(passed=True,variants=8,fresh_imports=24,saved_native_feature_checks=42,actual_previews_inspected=8,same_camera_pairs=4,tower_unoccluded_front_glass_cells=visibility),
    limitations=['Static opaque palette assets; no rig, animation, collision, LOD chain or game-engine integration.', 'Rear hangar equipment is dark in common studio view; the maintenance bay remains visibly open.', 'Conservative reduction may expand occupied bounds by one large cell (0.05m).'],blockers=[])
write('STATUS.json',status)
report = f'''# Airfield — ready for review

Four original models / eight variants are frozen under `assets/{{propeller_plane,airport_tug,maintenance_hangar,control_tower}}/{{large,half}}/`. Each variant has native VOX 150, BLEND, GLB, FBX, actual `preview.png`, and metadata.

| Model | Large grid | Half grid |
|---|---|---|
| propeller_plane | 128×104×64 | 64×52×32 |
| airport_tug | 80×128×72 | 40×64×36 |
| maintenance_hangar | 128×112×104 | 64×56×52 |
| control_tower | 92×92×128 | 46×46×64 |

Large cells are 0.05m; half cells are 0.10m, preserving physical grid extents. Geometry and the ivory/aviation-blue/ochre palette were newly authored from this theme's `REF/voxel/airfield/reference.png` only. `build.py` supplies pure `make_assets()`; no other theme creative resources were read or reused.

**Evidence:** one isolated four-thread build, no rebuild or optional views. All eight actual previews inspected. `validation_export.json` passes **24 fresh BLEND/GLB/FBX imports**, checking native hashes/palette, exact exposed surface, outward normals, triangle counts, materials, bounds and export studio exclusion. `validation_features.json` passes **42 saved-native probes** for broad wings, both propeller blades, landing wheels, towbar/open eye, the empty hangar portal/bay and tower glazing. Tower rays toward the common camera find **{visibility['large']} large / {visibility['half']} half unoccluded front-glass cells**. All four camera pairs match.

**Actual timing:** start {status['started_at_utc']} / {status['started_at_kst']}; finish {status['finished_at_utc']} / {status['finished_at_kst']}. Wall **{duration:.3f}s**. Build **{build['elapsed_seconds']:.3f}s** (rendering included: {render_time:.3f}s). Fresh-format verifier **{verify['elapsed_seconds']:.3f}s**; native probes **{features['elapsed_seconds']:.3f}s**. Exact commands, UTC process timings and logs are retained. No UE or worker image-generation process was used.

Limits: static opaque palette assets, without rig/animation/collision/LOD chain/engine integration. Rear hangar equipment is dark under the common studio lighting; its open bay remains clear. Half reduction can expand occupied bounds by 0.05m. No GUI inspection is claimed. Source, palette, capture manifest, visual review and a frozen file-hash manifest accompany this result. Parent acceptance is pending; canal was not started.
'''
(root/'RESULT.md').write_text(report,encoding='utf-8')
files = {p.relative_to(root).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
         for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='delivery_manifest.json'}
write('delivery_manifest.json',dict(theme='airfield',frozen_at_utc=finished.isoformat(),files=files))
print(json.dumps(dict(status=status['status'],elapsed_seconds=duration,files_frozen=len(files),finished_at_utc=status['finished_at_utc'],tower_visibility=visibility),indent=2))
