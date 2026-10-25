"""Saved-native functional checks; does not import authoring geometry."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT.parent / '_tools'))
from voxelkit import read_vox


def main():
    started = datetime.now(timezone.utc).isoformat()
    t0 = time.perf_counter()
    records = []
    for slug in ('canal_boat', 'lock_gate', 'drawbridge', 'lockkeepers_house'):
        for variant, divisor in (('large', 1), ('half', 2)):
            path = ROOT / 'assets' / slug / variant / (slug + '.vox')
            native = read_vox(path)
            data = native.data
            checks = []

            def volume(name, lo, hi, empty):
                a = np.ceil(np.array(lo) / divisor).astype(int)
                b = np.floor(np.array(hi) / divisor).astype(int)
                region = data[tuple(slice(x, y) for x, y in zip(a, b))]
                count = int(np.count_nonzero(region))
                passed = count == 0 if empty else count == region.size
                checks.append({'feature': name, 'passed': bool(passed), 'kind': 'empty_volume' if empty else 'solid_volume', 'grid_box': [a.tolist(), b.tolist()], 'occupied': count, 'cells': int(region.size)})

            def occupied_points(name, points):
                coords = [tuple(int(v // divisor) for v in p) for p in points]
                values = [int(data[p]) for p in coords]
                checks.append({'feature': name, 'passed': all(v > 0 for v in values), 'kind': 'support_or_mechanism_samples', 'grid_points': coords, 'palette_indices': values})

            if slug == 'canal_boat':
                volume('cargo_well_open_to_sky', (14, 52, 24), (34, 78, 58), True)
                volume('cargo_well_structural_floor', (14, 52, 18), (34, 78, 20), False)
                occupied_points('aft_cargo_and_hull_rims', [(17, 94, 26), (32, 100, 25), (5, 66, 26), (42, 66, 26)])
            elif slug == 'lock_gate':
                volume('continuous_central_gap_between_leaves', (60, 0, 0), (68, 52, 68), True)
                occupied_points('two_timber_leaves_and_iron_straps', [(42, 20, 34), (86, 20, 34), (42, 20, 24), (86, 20, 24)])
                occupied_points('hinges_and_both_operating_gears', [(24, 30, 51), (104, 30, 51), (21, 26, 78), (123, 26, 78)])
            elif slug == 'drawbridge':
                volume('navigation_corridor_under_raised_span', (0, 48, 0), (84, 76, 30), True)
                occupied_points('raised_deck_and_heel_pivot', [(42, 65, 45), (42, 31, 65), (42, 100, 25)])
                occupied_points('counterweights_pivot_bearings_and_lift_links', [(13, 121, 53), (71, 121, 53), (8, 100, 76), (76, 100, 76), (13, 35, 80), (71, 35, 80)])
                occupied_points('lift_link_to_deck_crossmember', [(15, 31, 64), (16, 31, 64), (67, 31, 64), (68, 31, 64)])
            else:
                occupied_points('entrance_roof_and_chimney', [(50, 20, 26), (48, 50, 111), (73, 77, 126)])
                occupied_points('control_cabinet_gauge_lever_and_conduit', [(110, 40, 28), (105, 26, 45), (116, 22, 38), (95, 63, 20)])
            records.append({'asset': slug, 'variant': variant, 'native_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'passed': all(c['passed'] for c in checks), 'checks': checks})
    passed = all(r['passed'] for r in records)
    result = {'passed': passed, 'source': 'Reopened final VOX files only; coordinates expressed in each saved grid.', 'started_at_utc': started, 'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'elapsed_seconds': time.perf_counter() - t0, 'records': records}
    (ROOT / 'validation_features.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'passed': passed, 'variants': len(records), 'checks': sum(len(r['checks']) for r in records), 'failures': [(r['asset'], r['variant'], c['feature']) for r in records for c in r['checks'] if not c['passed']]}))
    if not passed:
        raise AssertionError('saved-native functional check failed')


if __name__ == '__main__':
    main()
