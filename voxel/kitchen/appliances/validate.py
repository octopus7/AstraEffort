"""Independent saved-native integrity and functional-feature verification."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import struct
import sys
sys.dont_write_bytecode = True
import time
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parents[1] / '_tools'))
from build import make_assets, PALETTE
from voxelkit import read_vox, reduce_half

# These fixed test volumes describe functional openings/parts in large grid cells.
# All boundaries are even, so both resolutions probe the same physical volumes.
PROBES = {
    'double_door_fridge': [
        ('door_separation', (42, 14, 30), (46, 20, 110), 0),
        ('left_pull_clearance', (34, 10, 70), (38, 14, 92), 0),
        ('right_pull_clearance', (50, 10, 70), (54, 14, 92), 0),
        ('left_pull_structure', (34, 6, 70), (36, 8, 92), 3),
    ],
    'range_oven': [
        ('oven_pull_clearance', (30, 4, 78), (66, 8, 80), 0),
        ('oven_pull_structure', (30, 0, 78), (66, 4, 80), 3),
        ('front_left_pan_rest', (26, 32, 114), (30, 36, 118), 6),
        ('front_right_pan_rest', (66, 32, 114), (70, 36, 118), 6),
        ('rear_left_pan_rest', (26, 60, 114), (30, 64, 118), 6),
        ('rear_right_pan_rest', (66, 60, 114), (70, 64, 118), 6),
    ],
    'microwave': [
        ('pull_clearance', (84, 6, 32), (86, 10, 52), 0),
        ('pull_structure', (84, 2, 32), (86, 6, 52), 3),
        ('right_side_vent', (116, 32, 30), (120, 36, 50), 0),
        ('opaque_window', (30, 10, 30), (60, 14, 48), 9),
    ],
    'dishwasher': [
        ('lower_wire_rack_slot', (22, 70, 34), (26, 74, 38), 0),
        ('upper_wire_rack_slot', (22, 70, 72), (26, 74, 76), 0),
        ('wash_chamber_clearance', (70, 84, 48), (74, 88, 60), 0),
        ('cup_open_top', (30, 88, 84), (34, 92, 96), 0),
        ('lower_rack_front_rail', (22, 60, 44), (68, 64, 48), 7),
    ],
    'range_hood': [
        ('intact_right_canopy_shell', (104, 36, 26), (108, 50, 28), 1),
        ('continuous_central_airway', (54, 40, 24), (74, 54, 60), 0),
        ('open_chimney_duct', (54, 40, 60), (74, 54, 104), 0),
        ('filter_gap', (28, 32, 16), (32, 40, 20), 0),
        ('chimney_wall', (44, 38, 62), (48, 54, 96), 1),
        ('filter_bar', (34, 32, 16), (38, 40, 20), 8),
    ],
    'rice_cooker': [
        ('carry_handle_through_gap', (40, 54, 112), (72, 66, 118), 0),
        ('carry_handle_top_structure', (40, 56, 122), (72, 64, 124), 3),
        ('opaque_front_display', (48, 8, 54), (64, 10, 58), 6),
    ],
    'electric_kettle': [
        ('handle_loop_clearance', (98, 48, 48), (110, 60, 80), 0),
        ('hollow_vessel', (52, 52, 52), (60, 60, 68), 0),
        ('spout_mouth_open', (16, 14, 90), (20, 18, 94), 0),
        ('handle_outer_structure', (120, 50, 48), (122, 58, 80), 3),
    ],
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def features(slug, grid, factor):
    out = []
    for name, lo, hi, expected in PROBES[slug]:
        sl = tuple(slice(l // factor, h // factor) for l, h in zip(lo, hi))
        observed = grid.data[sl]
        assert observed.size > 0
        passed = bool(np.all(observed == expected))
        out.append({'name': name, 'large_grid_box': [lo, hi], 'expected_index': expected,
                    'sampled_cells': int(observed.size),
                    'observed_indices': np.unique(observed).astype(int).tolist(), 'passed': passed})
        assert passed, f'{slug} {factor} {name}: {np.unique(observed)} != {expected}'
    return out


def main():
    t0 = time.perf_counter()
    started = datetime.now(timezone.utc).isoformat()
    if '--hash-only' in sys.argv:
        frozen = json.loads((ROOT / 'frozen_file_hashes.json').read_text(encoding='utf-8'))
        for rel, expected_hash in frozen['sha256'].items():
            assert sha(ROOT / rel) == expected_hash, f'Frozen hash mismatch: {rel}'
        print(json.dumps({'frozen_hashes_passed': True, 'files': len(frozen['sha256']),
                          'checked_at_utc': datetime.now(timezone.utc).isoformat()}))
        return
    authored = make_assets()
    source_only = '--source-only' in sys.argv
    manifest = None if source_only else json.loads((ROOT / 'capture_manifest.json').read_text(encoding='utf-8'))
    all_records = []
    for a in authored:
        half = reduce_half(a.grid)
        if a.half_postprocess:
            a.half_postprocess(half)
        assert max(a.grid.shape) == 128 and all(n % 2 == 0 for n in a.grid.shape)
        assert half.shape == tuple(n // 2 for n in a.grid.shape) and max(half.shape) == 64
        large_count = int(np.count_nonzero(a.grid.data))
        half_count = int(np.count_nonzero(half.data))
        assert 0 < half_count < large_count
        pair_cameras = []
        for variant, expected, factor in [('large', a.grid, 1), ('half', half, 2)]:
            if source_only:
                grid = expected
                record = {'asset': a.slug, 'variant': variant, 'source_only': True}
            else:
                folder = ROOT / 'assets' / a.slug / variant
                vox = folder / (a.slug + '.vox')
                png = folder / 'preview.png'
                raw = vox.read_bytes()
                assert raw[:4] == b'VOX ' and struct.unpack_from('<I', raw, 4)[0] == 150
                grid = read_vox(vox)  # Parser also rejects duplicate/out-of-bounds coordinates.
                assert np.array_equal(grid.data, expected.data), f'{a.slug}/{variant} occupancy roundtrip'
                assert grid.palette[:len(PALETTE)] == PALETTE
                assert int(grid.data.max()) < len(PALETTE)
                meta = json.loads((folder / 'metadata.json').read_text(encoding='utf-8'))
                assert meta['grid_size'] == list(expected.shape)
                assert meta['voxel_size_m'] == a.voxel_size * factor
                assert np.allclose(meta['grid_extents_m'], np.array(a.grid.shape) * a.voxel_size, rtol=0, atol=1e-12)
                assert meta['occupied_voxels'] == int(np.count_nonzero(grid.data))
                assert meta['sha256'] == {'native': sha(vox), 'preview': sha(png)}
                assert png.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n'
                assert struct.unpack('>II', png.read_bytes()[16:24]) == (768, 768)
                captures = [c for c in manifest['captures'] if c['asset'] == a.slug and c['variant'] == variant]
                assert len(captures) == 1
                capture = captures[0]
                assert capture['source_vox_sha256'] == sha(vox) and capture['image_sha256'] == sha(png)
                assert capture['rendered_from_reparsed_vox'] and capture['actual_blender_render']
                s = capture['settings']
                assert s['engine'] == 'CYCLES' and s['device'] == 'CPU' and s['threads'] == 4
                assert s['samples'] == 24 and s['denoising'] and s['view_transform'] == 'AgX'
                assert s['resolution'] == [768, 768]
                pair_cameras.append(s)
                record = {'asset': a.slug, 'variant': variant,
                          'native_file': vox.relative_to(ROOT).as_posix(),
                          'native_sha256': sha(vox), 'preview_sha256': sha(png),
                          'native_roundtrip_passed': True, 'palette_roundtrip_passed': True,
                          'png_size': [768, 768], 'voxel_size_m': meta['voxel_size_m'],
                          'grid_extents_m': meta['grid_extents_m']}
            record.update({'grid_size': list(grid.shape), 'occupied_voxels': int(np.count_nonzero(grid.data)),
                           'feature_probes': features(a.slug, grid, factor)})
            all_records.append(record)
        if not source_only:
            assert pair_cameras[0] == pair_cameras[1], f'{a.slug}: same camera and lighting'
    forbidden = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*')
                 if p.suffix.lower() in {'.blend', '.blend1', '.glb', '.gltf', '.fbx', '.obj', '.umap'}]
    assert not forbidden, forbidden
    if not source_only:
        expected_vox = {f'assets/{a.slug}/{v}/{a.slug}.vox' for a in authored for v in ('large', 'half')}
        expected_previews = {f'assets/{a.slug}/{v}/preview.png' for a in authored for v in ('large', 'half')}
        assert {p.relative_to(ROOT).as_posix() for p in (ROOT / 'assets').rglob('*.vox')} == expected_vox
        assert {p.relative_to(ROOT).as_posix() for p in (ROOT / 'assets').rglob('*.png')} == expected_previews
    report = {'passed': True, 'source_only': source_only, 'started_at_utc': started,
              'finished_at_utc': datetime.now(timezone.utc).isoformat(),
              'elapsed_seconds': time.perf_counter() - t0,
              'assets': len(authored), 'variants': len(all_records),
              'meaningful_feature_probe_count': sum(len(x['feature_probes']) for x in all_records),
              'forbidden_output_files': forbidden,
              'checks': ['VOX 150 and parser coordinate integrity', 'Full source-to-saved occupancy roundtrip',
                         'Palette roundtrip and index bounds', 'Exact half grid, doubled cell size and physical extents',
                         'Native occupancy genuinely reduces', 'Native functional feature probes at both sizes',
                         'Actual PNG dimensions', 'SHA256 agreement', 'Same large-bound camera/light/render settings'],
              'records': all_records}
    filename = 'source_validation.json' if source_only else 'validation.json'
    (ROOT / filename).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('passed', 'source_only', 'assets', 'variants', 'meaningful_feature_probe_count', 'elapsed_seconds')}))


if __name__ == '__main__':
    main()
