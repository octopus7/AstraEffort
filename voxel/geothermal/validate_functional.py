"""Functional probes of saved native VOX only; never imports authoring source.

Probe coordinates use large-grid cell units for both sizes. Empty corridors test
the entire indicated volume, and positive witnesses prevent vacuous empty tests.
Run with Blender's bundled Python. --baseline preserves the pre-fix failure.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import struct
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parent
SPECS = {
    'thermal_rover': ((98, 128, 104), .035),
    'geothermal_drill': ((128, 104, 128), .045),
    'cooling_tower': ((112, 112, 128), .05),
    'volcano_observatory': ((128, 112, 128), .05),
}


def load_vox(path):
    raw = path.read_bytes()
    assert raw[:8] == b'VOX ' + struct.pack('<I', 150)
    pos, chunks = 20, {}
    while pos < len(raw):
        tag, size, child = struct.unpack_from('<4sII', raw, pos)
        assert child == 0
        chunks[tag] = raw[pos + 12:pos + 12 + size]
        pos += 12 + size
    shape = struct.unpack('<III', chunks[b'SIZE'])
    block = chunks[b'XYZI']
    count = struct.unpack_from('<I', block)[0]
    cells = np.frombuffer(block[4:], np.uint8).reshape(count, 4)
    data = np.zeros(shape, np.uint8)
    data[tuple(cells[:, :3].T)] = cells[:, 3]
    return data


class Probes:
    def __init__(self, data, scale):
        self.data, self.scale, self.checks = data, scale, []

    def record(self, name, passed, **evidence):
        self.checks.append(dict(name=name, passed=bool(passed), **evidence))

    def empty(self, name, lo, hi):
        assert all(v % self.scale == 0 for v in (*lo, *hi))
        region = self.data[tuple(slice(a // self.scale, b // self.scale) for a, b in zip(lo, hi))]
        occupied = int(np.count_nonzero(region))
        self.record(name, region.size > 0 and occupied == 0,
                    large_cell_box=[list(lo), list(hi)], tested_voxels=int(region.size), occupied=occupied)

    def solid_points(self, name, points, color=None):
        values = [int(self.data[tuple(int(c // self.scale) for c in p)]) for p in points]
        self.record(name, all(v == color if color is not None else v > 0 for v in values),
                    large_cell_points=[list(p) for p in points], palette_indices=values)


def probes_for(slug, p):
    if slug == 'thermal_rover':
        p.empty('sampler_core_bore', (86, 14, 24), (90, 18, 34))
        p.solid_points('sampler_crown_surrounds_bore', [(83, 16, 30), (93, 16, 30), (88, 11, 30), (88, 21, 30)])
        p.empty('sampler_ground_clearance', (80, 8, 2), (96, 24, 22))
        p.solid_points('sampler_arm_and_joints_present', [(76, 66, 58), (82, 55, 66), (88, 44, 75), (88, 31, 67), (88, 17, 58), (88, 16, 44)])
        p.solid_points('eight_track_wheel_hubs', [(x, y, 18) for x in (5, 93) for y in (52, 70, 88, 107)], color=3)
    elif slug == 'geothermal_drill':
        p.solid_points('continuous_drill_string', [(40, 45, z) for z in range(20, 106)])
        for name, lo, hi in (
            ('east', (46, 44, 20), (48, 46, 36)),
            ('west', (32, 44, 20), (34, 46, 36)),
            ('front', (38, 36, 20), (42, 38, 36)),
            ('rear', (38, 52, 20), (42, 54, 36)),
        ):
            p.empty('deck_annulus_clearance_' + name, lo, hi)
        p.solid_points('deck_ring_and_four_stabilizer_feet', [(55, 45, 28), (25, 45, 28), (10, 13, 4), (73, 13, 4), (10, 82, 4), (73, 82, 4)])
        p.empty('mast_left_open_bay', (28, 48, 48), (34, 60, 102))
        p.empty('mast_right_open_bay', (46, 48, 48), (52, 60, 102))
        p.solid_points('front_accessible_handwheel_rim_and_hub', [(94, 18, 24), (114, 18, 24), (104, 18, 14), (104, 18, 34), (104, 18, 24)])
        for x in (98, 108):
            for z in (18, 28):
                p.empty(f'handwheel_open_sector_{x}_{z}', (x, 16, z), (x + 2, 20, z + 2))
        p.empty('handwheel_front_access_clearance', (94, 10, 14), (114, 16, 34))
    elif slug == 'cooling_tower':
        p.empty('continuous_uncapped_central_airflow', (40, 40, 2), (72, 72, 128))
        p.solid_points('top_rim_and_waist_shell_present', [(17, 56, 124), (95, 56, 124), (56, 17, 124), (56, 95, 124), (26, 56, 82), (86, 56, 82)])
        for name, lo, hi in (
            ('front', (46, 12, 30), (66, 30, 32)),
            ('right', (82, 46, 30), (102, 50, 32)),
            ('rear', (46, 82, 30), (66, 102, 32)),
            ('left', (10, 46, 30), (30, 50, 32)),
        ):
            p.empty('open_intake_slot_' + name, lo, hi)
        p.solid_points('four_separate_feet_and_two_risers', [(18, 18, 4), (94, 18, 4), (18, 94, 4), (94, 94, 4), (9, 56, 40), (103, 56, 40)])
    elif slug == 'volcano_observatory':
        p.empty('open_airlock_walkway_to_inner_door', (100, 26, 20), (112, 56, 40))
        p.solid_points('airlock_frame_floor_and_inner_door', [(92, 30, 28), (118, 30, 28), (105, 30, 47), (105, 35, 14), (105, 62, 30)])
        p.solid_points('roof_instrument_mounts', [(35, 53, 82), (65, 65, 100), (52, 78, 85)])
        p.solid_points('four_wind_instrument_cups', [(43, 78, 94), (61, 78, 94), (52, 69, 94), (52, 87, 94)])


def main():
    t0 = time.perf_counter()
    started = datetime.now(timezone.utc).isoformat()
    records = []
    for slug, (expected_shape, cell_size) in SPECS.items():
        for variant, factor in (('large', 1), ('half', 2)):
            path = ROOT / 'assets' / slug / variant / (slug + '.vox')
            data = load_vox(path)
            p = Probes(data, factor)
            p.record('native_dimensions', tuple(data.shape) == tuple(v // factor for v in expected_shape), grid_size=list(data.shape))
            probes_for(slug, p)
            record = dict(asset=slug, variant=variant, vox_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                          checks=p.checks, passed=all(c['passed'] for c in p.checks))
            if '--baseline' in sys.argv and slug == 'geothermal_drill':
                points = [(85, 36, 24), (91, 36, 24), (85, 36, 30), (91, 36, 30)]
                record['old_handwheel_quadrant_diagnostic'] = {
                    'center_large_cells': [88, 36, 27],
                    'points_large_cells': points,
                    'palette_indices': [int(data[tuple(c // factor for c in point)]) for point in points],
                    'expected_for_open_quadrants': 0,
                    'cause': 'Wheel plane Y36 lies inside pump body Y27..48; positive-X quadrants intersect pump.'}
            records.append(record)
    failures = [f"{r['asset']}/{r['variant']}: {c['name']}" for r in records for c in r['checks'] if not c['passed']]
    report = dict(theme='geothermal', passed=not failures, asset_count=4, variant_count=len(records),
                  started_at_utc=started, finished_at_utc=datetime.now(timezone.utc).isoformat(),
                  elapsed_seconds=time.perf_counter() - t0, check_count=sum(len(r['checks']) for r in records),
                  failures=failures, records=records,
                  scope='Saved-native static openings and positive structural witnesses; no rig or fluid simulation.')
    target = ROOT / ('validation_functional_before_fix.json' if '--baseline' in sys.argv else 'validation_functional.json')
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('passed', 'asset_count', 'variant_count', 'check_count', 'elapsed_seconds', 'failures')}))
    raise SystemExit(0 if not failures else 1)


if __name__ == '__main__':
    main()
