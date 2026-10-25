"""Freeze canal evidence after the finite build, visual review and verification."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json

ROOT = Path(__file__).resolve().parent
SLUGS = ('canal_boat', 'lock_gate', 'drawbridge', 'lockkeepers_house')


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    # This source is invoked once, after the author has viewed the final eight PNGs.
    export = read(ROOT / 'validation_export.json')
    features = read(ROOT / 'validation_features.json')
    assert export['passed'] and export['asset_count'] == 4 and export['variant_count'] == 8
    assert features['passed'] and len(features['records']) == 8
    assert sum(len(r['imports']) for r in export['records']) == 24
    current_build = read(ROOT / 'build_validation.json')
    initial_build = read(ROOT / 'evidence/build_validation_initial.json')
    assert current_build['passed'] and initial_build['passed']
    write(ROOT / 'evidence/build_validation_drawbridge_fix.json', current_build)
    captures = read(ROOT / 'capture_manifest.json')
    assert captures['actual_blender_renders'] and len(captures['captures']) == 8
    final_assets = []
    for slug in SLUGS:
        pair = []
        for variant in ('large', 'half'):
            directory = ROOT / 'assets' / slug / variant
            for ext in ('.vox', '.blend', '.glb', '.fbx'):
                assert (directory / (slug + ext)).is_file()
            metadata = read(directory / 'metadata.json')
            assert all(sha(directory / name) == digest for name, digest in metadata['sha256'].items())
            assert max(metadata['grid_size']) == (128 if variant == 'large' else 64)
            pair.append(metadata)
        assert all(n % 2 == 0 for n in pair[0]['grid_size'])
        assert pair[1]['grid_size'] == [n // 2 for n in pair[0]['grid_size']]
        assert pair[1]['voxel_size_m'] == pair[0]['voxel_size_m'] * 2
        assert pair[1]['grid_extents_m'] == pair[0]['grid_extents_m']
        cs = [c for c in captures['captures'] if c['asset'] == slug]
        assert len(cs) == 2 and cs[0]['settings'] == cs[1]['settings']
        assert all(sha(ROOT / c['image']) == c['image_sha256'] for c in cs)
        final_assets.append({'asset': slug, 'large': pair[0], 'half': pair[1]})
    assert {p.name for p in (ROOT / 'assets').iterdir()} == set(SLUGS)
    assert not list(ROOT.rglob('*.blend1')) and not list(ROOT.rglob('*.pyc'))
    combined_build = dict(current_build)
    combined_build.update(assets=final_assets,
        started_at_utc=initial_build['started_at_utc'],
        elapsed_seconds=initial_build['elapsed_seconds'] + current_build['elapsed_seconds'],
        timing_basis='Sum of pipeline execution durations: one four-asset build, one demonstrated-defect drawbridge-only correction.',
        run_reports=['evidence/build_validation_initial.json', 'evidence/build_validation_drawbridge_fix.json'],
        remaining_validation='Complete: validation_export.json, validation_features.json and visual_review.json')
    write(ROOT / 'build_validation.json', combined_build)
    now = datetime.now(timezone.utc)
    kst = timezone(timedelta(hours=9))
    start = datetime.fromisoformat('2026-10-25T05:01:44.530147+00:00')
    elapsed = (now - start).total_seconds()
    initial_timing = read(ROOT / 'build_timing.json')
    fix_timing = read(ROOT / 'build_drawbridge_fix_timing.json')
    verify_timing = read(ROOT / 'verify_timing.json')
    assert fix_timing['exit_code'] == 0 and verify_timing['exit_code'] == 0
    comments = {
        'canal_boat': 'Open cargo well, exposed lower floor, aft crates, wheelhouse, fender and tiller readable in both sizes.',
        'lock_gate': 'Two angled timber leaves, genuine central gap, hinges, straps and operating gears visible in both sizes.',
        'drawbridge': 'Raised span, clear passage, heel and upper pivots, counterweights and corrected deck-nose crossmember visible in both sizes.',
        'lockkeepers_house': 'Compact gabled building, entry steps, chimney and separate gauge/lever/vent control cabinet readable in both sizes.',
    }
    reviews = []
    for asset in final_assets:
        for variant in ('large', 'half'):
            png = ROOT / 'assets' / asset['asset'] / variant / 'preview.png'
            reviews.append({'asset': asset['asset'], 'variant': variant, 'image': png.relative_to(ROOT).as_posix(), 'image_sha256': sha(png), 'passed': True, 'observations': comments[asset['asset']]})
    write(ROOT / 'visual_review.json', {'passed': True, 'review_recorded_at_utc': now.isoformat(), 'method': 'Author inspected every final primary 768px actual Blender PNG with the image viewer; no optional camera views.', 'records': reviews})
    reference = ROOT.parents[1] / 'REF/voxel/canal/reference.png'
    write(ROOT / 'source_manifest.json', {
        'authoring': 'Original finite native-grid geometry from pure make_assets() in build.py.',
        'reference': {'path': 'REF/voxel/canal/reference.png', 'sha256': sha(reference), 'role': 'Main-provided design input only; never scene evidence'},
        'worker_image_generation_seconds': 0,
        'shared_read_only_tools': {str(p.relative_to(ROOT.parents[1])).replace('\\', '/'): sha(p) for p in [ROOT.parent / '_tools/voxelkit.py', ROOT.parent / '_tools/blender_pipeline.py', ROOT.parent / '_tools/verify_theme.py']},
        'half_resolution': 'Independent conservative 2x2x2 native reduction; no manual half edits. Doubled meters per cell; identical physical grid extent.',
        'correction': 'Saved-native red probe found an empty two-voxel lift-link/deck-nose joint in the large bridge. Added one real transverse crossmember and rebuilt only drawbridge. Final probe passes in both variants. Before PNGs/logs preserved; old model backups removed.',
        'launcher_note': 'First build completed all eight outputs and Blender quit, but the initial wrapper discarded ExitCode during Refresh. Original timing preserves null instead of inventing a code. Start-Process -Wait fixed capture; correction and verification returned 0.',
        'external_web_references': [],
    })
    build_seconds = initial_timing['elapsed_seconds'] + fix_timing['elapsed_seconds']
    summary = {'native_variants_passed': 8, 'fresh_imports_passed': 24, 'functional_checks_passed': 24, 'primary_previews_inspected': 8, 'same_camera_pairs': 4, 'manual_half_corrections': 0}
    write(ROOT / 'STATUS.json', {
        'theme': 'canal', 'status': 'ready_for_review',
        'started_at_utc': start.isoformat(), 'started_at_kst': start.astimezone(kst).isoformat(),
        'finished_at_utc': now.isoformat(), 'finished_at_kst': now.astimezone(kst).isoformat(),
        'elapsed_seconds': elapsed, 'build_seconds': build_seconds,
        'initial_build_seconds': initial_timing['elapsed_seconds'], 'selective_correction_seconds': fix_timing['elapsed_seconds'],
        'fresh_import_process_seconds': verify_timing['elapsed_seconds'],
        'native_feature_check_seconds': features['elapsed_seconds'], 'worker_image_generation_seconds': 0,
        'assets': list(SLUGS), 'validation_summary': summary, 'blockers': [],
        'frozen_manifest': 'frozen_file_hashes.json', 'awaiting': 'Main independent review and commit; worker frozen.'})
    result = f'''# Canal — ready for review

Four original assets / eight native variants are frozen: `canal_boat`, `lock_gate`, `drawbridge`, `lockkeepers_house`. Deliverables are under `assets/<asset>/{{large,half}}/`: VOX, BLEND, GLB, FBX, metadata and actual 768px preview PNG. `build.py` contains pure `make_assets()`; `palette.json` records the restrained teal, limestone, timber and terracotta palette.

| Asset | Large grid | Half grid | Large cell |
|---|---|---|---|
'''
    for asset in final_assets:
        result += f"| {asset['asset']} | {'×'.join(map(str, asset['large']['grid_size']))} | {'×'.join(map(str, asset['half']['grid_size']))} | {asset['large']['voxel_size_m']} m |\n"
    result += f'''
All large axes are even and longest 128; half axes divide exactly by two, cell size doubles, and physical grid extent is unchanged. No manual half edits. Geometry uses exposed voxel boundaries and flat opaque palette materials.

Validation passed: 8 native reparses, 24 fresh BLEND/GLB/FBX imports, 24 saved-native feature checks, and inspection of all 8 final primary previews. Bounds, palette assignments, exposed outward faces, surface area, triangles and file hashes passed. Four camera pairs match. See `validation_export.json`, `validation_features.json`, `visual_review.json`, `capture_manifest.json` and the logs.

The boat has an open recessed cargo well; gates have a continuous central gap and hand gears; the 30° raised bridge has an empty navigation corridor, pivots and counterweights; the house has a separate working-form control cabinet. One demonstrated large-bridge lift-link gap was corrected with a transverse deck-nose member, using a bridge-only rebuild. Before PNG/probe evidence is in `evidence/`; no superseded model binaries remain.

Actual start: {start.isoformat()} / {start.astimezone(kst).isoformat()}. Finish: {now.isoformat()} / {now.astimezone(kst).isoformat()}. Wall: **{elapsed:.2f} s**. Initial full build: **{initial_timing['elapsed_seconds']:.2f} s**; selective bridge correction: **{fix_timing['elapsed_seconds']:.2f} s**; fresh-import process: **{verify_timing['elapsed_seconds']:.2f} s**; native probes: **{features['elapsed_seconds']:.2f} s**. Worker image generation: **0 s**. Initial launcher exit code was unavailable; its timing is preserved honestly, and final correction/verification exited 0.

Limitations: static poses, opaque glazing, no rig/animation, collision, LOD chain or engine integration. Half resolution simplifies fine masonry seams and glazing trim; conservative reduction can expand a boundary by one large cell. No river/terrain base or optional views. Reference: only `REF/voxel/canal/reference.png`, documented in `source_manifest.json`; all scene evidence is actual Blender rendering. File freeze: `frozen_file_hashes.json`. Main owns final review and Git.
'''
    (ROOT / 'RESULT.md').write_text(result, encoding='utf-8')
    files = sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name != 'frozen_file_hashes.json')
    write(ROOT / 'frozen_file_hashes.json', {'theme': 'canal', 'frozen_at_utc': now.isoformat(), 'file_count': len(files), 'files': {p.relative_to(ROOT).as_posix(): {'sha256': sha(p), 'bytes': p.stat().st_size} for p in files}})
    print(json.dumps({'status': 'ready_for_review', 'files': len(files), 'wall_seconds': elapsed, 'build_seconds': build_seconds, 'verify_seconds': verify_timing['elapsed_seconds'], 'validation': summary}))


if __name__ == '__main__':
    main()
