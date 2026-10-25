"""Validate the final theme inventory and write its review records once."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import ast
import hashlib
import json
import sys
import time
sys.dont_write_bytecode = True
import numpy as np
from validate_functional import load_vox, SPECS

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def write(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    t0 = time.perf_counter()
    audit_start = datetime.now(timezone.utc)
    exported = read('validation_export.json')
    functional = read('validation_functional.json')
    assert exported['passed'] and functional['passed']
    assert exported['asset_count'] == 4 and exported['variant_count'] == 8
    assert functional['check_count'] == 68
    assert {p.name for p in (ROOT / 'assets').iterdir()} == set(SPECS)
    captures = read('capture_manifest.json')
    assert captures['actual_blender_renders'] and len(captures['captures']) == 8
    old = read('build_validation_initial.json')
    old_by_slug = {r['asset']: r for r in old['assets']}
    current_build = read('build_validation.json')
    assert current_build['passed']
    pairs, final_build_records, unchanged = [], [], 0
    for slug, (shape, unit) in SPECS.items():
        metas = {v: read(f'assets/{slug}/{v}/metadata.json') for v in ('large', 'half')}
        grids = {v: load_vox(ROOT / 'assets' / slug / v / (slug + '.vox')) for v in metas}
        assert tuple(grids['large'].shape) == shape
        assert max(shape) == 128 and all(n % 2 == 0 for n in shape)
        assert tuple(grids['half'].shape) == tuple(n // 2 for n in shape)
        blocks = grids['large'].reshape(shape[0] // 2, 2, shape[1] // 2, 2, shape[2] // 2, 2).transpose(0, 2, 4, 1, 3, 5).reshape(*grids['half'].shape, 8)
        assert np.array_equal(grids['half'] > 0, np.any(blocks > 0, axis=-1))
        for variant, factor in (('large', 1), ('half', 2)):
            meta = metas[variant]
            assert abs(meta['voxel_size_m'] - unit * factor) < 1e-12
            assert np.allclose(meta['grid_extents_m'], np.array(shape) * unit)
            directory = ROOT / 'assets' / slug / variant
            assert {p.name for p in directory.iterdir()} == {slug + ext for ext in ('.vox', '.blend', '.glb', '.fbx')} | {'metadata.json', 'preview.png'}
            for name, expected in meta['sha256'].items():
                assert sha(directory / name) == expected
            capture = [c for c in captures['captures'] if (c['asset'], c['variant']) == (slug, variant)]
            assert len(capture) == 1
            capture = capture[0]
            assert capture['image_sha256'] == sha(directory / 'preview.png')
            assert capture['source_blend_sha256'] == sha(directory / (slug + '.blend'))
            if slug != 'geothermal_drill':
                assert meta['sha256'] == old_by_slug[slug][variant]['sha256']
                unchanged += 1
        pair_captures = [c for c in captures['captures'] if c['asset'] == slug]
        assert pair_captures[0]['settings'] == pair_captures[1]['settings']
        pairs.append(dict(asset=slug, large_grid=list(shape), half_grid=list(grids['half'].shape),
                          grid_extents_m=metas['large']['grid_extents_m'], native_half_occupancy_is_exact_2x_block_union=True,
                          matching_capture_settings=True))
        final_build_records.append(dict(asset=slug, **metas))
    counts = {ext: len(list((ROOT / 'assets').rglob('*.' + ext))) for ext in ('vox', 'blend', 'glb', 'fbx', 'png')}
    assert set(counts.values()) == {8}
    counts['metadata'] = len(list((ROOT / 'assets').rglob('metadata.json')))
    assert counts['metadata'] == 8
    # Preserve the actual selective build report separately; the canonical report
    # then summarizes the current saved four-model set with both process records.
    write('build_validation_selective_fix.json', current_build)
    write('build_validation.json', dict(passed=True, scope='Final current four-model delivery', assets=final_build_records,
          original_build_report='build_validation_initial.json', selective_fix_report='build_validation_selective_fix.json',
          final_fresh_import_report='validation_export.json', functional_report='validation_functional.json'))
    palette_node = next(n.value for n in ast.parse((ROOT / 'build.py').read_text(encoding='utf-8')).body
                        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'PALETTE' for t in n.targets))
    palette = ast.literal_eval(palette_node)
    names = ['empty', 'ceramic insulation', 'ceramic shade', 'weathered copper', 'copper light', 'basalt rubber',
             'structural steel', 'pale alloy', 'blue-grey opaque glazing', 'glazing reflection', 'signal amber',
             'warm lamp', 'dark recess', 'restrained safety yellow', 'equipment insulation']
    used = set().union(*(set(r[v]['palette_indices']) for r in final_build_records for v in ('large', 'half')))
    write('palette.json', dict(theme='geothermal', material_model='Flat opaque per-face palette; roughness 0.74; no UV image textures',
          colors=[dict(index=i, name=names[i], rgba=list(c) + ([255] if len(c) == 3 else []), used=i in used)
                  for i, c in enumerate(palette)]))
    visual_notes = {
        'thermal_rover': 'Both sizes show protected rounded glazing, independent track wheels, suspended sampler and radiator; no framing or silhouette defect observed.',
        'geothermal_drill': 'Final pair shows open mast, drill string, separate feet, connected manifold and the repaired front handwheel. All four handwheel sectors remain open in native half occupancy.',
        'cooling_tower': 'Both sizes show uncapped stepped throat, waisted shell, intake slats, four feet and twin risers. The side-riser centerline intentionally obscures part of each side intake; off-center intake corridors remain empty.',
        'volcano_observatory': 'Both sizes show curved opaque window band, visible vestibule depth and steps, thermal pack and roof instruments.'}
    review_time = datetime.now(timezone.utc).isoformat()
    write('visual_review.json', dict(review_completed_at_utc=review_time, method='Assistant inspected each actual PNG with view_image; revised drill pair re-inspected after selective rebuild.',
          final_preview_count=8, records=[dict(asset=c['asset'], variant=c['variant'], path=c['image'], image_sha256=c['image_sha256'],
          accepted=True, observation=visual_notes[c['asset']]) for c in captures['captures']],
          defect='Initial drill handwheel intersected pump housing; saved-native baseline reproduced it. Repositioned clear of housing and widened its open sectors; no other geometry changed.'))
    audit_end = datetime.now(timezone.utc)
    write('validation_delivery.json', dict(passed=True, started_at_utc=audit_start.isoformat(), finished_at_utc=audit_end.isoformat(),
          elapsed_seconds=time.perf_counter() - t0, asset_count=4, variant_count=8, counts=counts,
          unchanged_non_drill_variants=unchanged, pairs=pairs,
          checks=['Exact requested asset and per-variant file set', 'Final metadata SHA256 values', 'Capture PNG and BLEND hashes',
                  'Same-camera pair settings', 'Even longest128 large dimensions and exact half axes',
                  'Equal physical grid extents', 'Native half occupancy is conservative 2x block union',
                  'Six non-drill variants unchanged from first build']))
    status = read('STATUS.json')
    start = datetime.fromisoformat(status['started_at_utc'].replace('Z', '+00:00'))
    pause = datetime.fromisoformat(status['checkpoint_at_utc'])
    resume = datetime.fromisoformat(status['resumed_at_utc'].replace('Z', '+00:00'))
    finish = datetime.now(timezone.utc)
    paused = (resume - pause).total_seconds()
    wall = (finish - start).total_seconds()
    kst = timezone(timedelta(hours=9))
    processes = {name: read(name + '_process.json') for name in ('build', 'fix_geothermal_drill', 'validation_before_fix', 'validation')}
    assert all(r['exit_code'] == 0 for r in processes.values())
    status.update(status='ready_for_review', finished_at_utc=finish.isoformat(), finished_at_kst=finish.astimezone(kst).isoformat(),
          elapsed_seconds=wall, total_wall_seconds=wall, paused_duration_seconds=paused, active_elapsed_seconds=wall - paused,
          resumed_active_seconds=(finish - resume).total_seconds(), asset_count=4, variant_count=8, final_file_counts=counts,
          paused_by_user=False, frozen=True, blockers=[], remaining=[],
          validation_summary='8/8 native variants; 24/24 fresh BLEND/GLB/FBX mesh imports; 68/68 saved-native functional probes; 8/8 final previews inspected; capture hashes and native half reduction pass.',
          process_seconds={name: r['elapsed_seconds'] for name, r in processes.items()},
          functional_verification_seconds=functional['elapsed_seconds'],
          model='gpt-6-astra', reasoning_effort='max', separate_fast_toggle_available=False,
          limitations=['Static palette geometry; no rig, animation, collision, LOD chain or game-engine integration.',
                       'Glazing is opaque; observatory main chamber is solid, with only vestibule modeled as open space.',
                       'No heat, airflow, fluid or drilling simulation; no image textures or UV unwrap.'],
          reference='REF/voxel/geothermal/reference.png', checkpoint_commit='b3992e3')
    write('STATUS.json', status)
    result = f'''# Geothermal — ready for review

Four models, eight native variants: `thermal_rover`, `geothermal_drill`, `cooling_tower`, `volcano_observatory`. Each `assets/<model>/<large|half>/` contains VOX, BLEND, GLB, FBX, metadata and an actual 768×768 Blender preview. Large longest axis is 128; half axes are exactly divided by two, with doubled cell size and unchanged physical grid extent. No manual half correction was needed.

Start: {start.isoformat()} UTC / {start.astimezone(kst).isoformat()} KST. Paused: {pause.isoformat()} UTC. Resumed: {resume.isoformat()} UTC / {resume.astimezone(kst).isoformat()} KST. Finished: {finish.isoformat()} UTC / {finish.astimezone(kst).isoformat()} KST. Total wall: {wall:.3f}s; paused: {paused:.3f}s; active: {wall - paused:.3f}s (resume segment {(finish - resume).total_seconds():.3f}s). Original start and checkpoint records remain preserved; prior binaries/evidence are in checkpoint `b3992e3`.

Original build: {processes['build']['elapsed_seconds']:.3f}s. One selective drill-pair fix build: {processes['fix_geothermal_drill']['elapsed_seconds']:.3f}s. Fresh verification: {processes['validation_before_fix']['elapsed_seconds']:.3f}s before the fix, {processes['validation']['elapsed_seconds']:.3f}s final. All isolated Blender processes used four threads, factory startup and Python exit-code 1; all completed with exit 0.

All eight final previews were inspected. The original drill handwheel intersected the pump housing and its sectors closed at half resolution. Saved-native probes reproduced the defect; moving the wheel ahead of the housing and opening its sectors fixed it. Only that model pair was rebuilt. The other six variants retain their initial binary and preview hashes. No optional views were made.

Final independent verification passed 8/8 native files and 24/24 fresh BLEND/GLB/FBX imports: occupied exterior boundaries, outward normals, palette assignments, bounds, areas, counts, finite coordinates and no degenerate triangles. `validation_functional.json` passes 68/68 checks in {functional['elapsed_seconds']:.6f}s: sampler bore/ground clearance, track hubs, drill string/annulus/mast/handwheel, tower throat/intakes, and airlock/instruments. The tower side intakes are tested off their intentional external riser centerlines. `validation_delivery.json` verifies exact counts, capture hashes, same cameras, real native reduction and unchanged extents.

Evidence: `build.py`, `palette.json`, `capture_manifest.json`, `visual_review.json`, `validate_functional.py`, `validation_functional_before_fix.json`, `validation_functional.json`, `validation_export.json`, `validation_delivery.json`, process JSON/logs and `frozen_files.json`. `build_validation_initial.json` and `capture_manifest_initial.json` describe the preserved checkpoint; the final manifest describes current files. Reference input only: `REF/voxel/geothermal/reference.png`; generic utilities are `voxel/_tools`. No image generation or external source reuse occurred in this pass.

Limitations: static opaque palette geometry, no rig/animation, collision, LOD chain or engine integration. The main observatory chamber is solid behind opaque glazing; its airlock vestibule is open. No physical drilling, airflow, heat or fluid simulation. No image textures/UV unwrap. No GUI validation was claimed. Parent performs final acceptance and Git commit; worker files are frozen.
'''
    (ROOT / 'RESULT.md').write_text(result, encoding='utf-8')
    files = [p for p in ROOT.rglob('*') if p.is_file() and p.name != 'frozen_files.json']
    write('frozen_files.json', dict(frozen_at_utc=finish.isoformat(), asset_count=4, variant_count=8,
          files={p.relative_to(ROOT).as_posix(): dict(bytes=p.stat().st_size, sha256=sha(p)) for p in sorted(files)},
          note='Inventory excludes this manifest itself. No extra model binary copies; prior versions remain in checkpoint b3992e3.'))
    print(json.dumps(dict(passed=True, status=status['status'], asset_count=4, variant_count=8, counts=counts,
                         finished_at_utc=finish.isoformat(), total_wall_seconds=wall, active_elapsed_seconds=wall - paused,
                         paused_duration_seconds=paused, frozen_file_count=len(files))))


if __name__ == '__main__':
    main()
