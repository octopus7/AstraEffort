"""Semantic checks against saved authoritative VOX files, at both resolutions."""
from pathlib import Path
from datetime import datetime, timezone
import sys, json, time
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT.parent / '_tools'))
from voxelkit import read_vox


def main():
    started = datetime.now(timezone.utc).isoformat()
    timer = time.perf_counter()
    records = []
    for slug in ('fire_engine', 'rescue_robot', 'fire_station', 'rescue_helicopter'):
        for variant, factor in (('large', 1), ('half', 2)):
            grid = read_vox(ROOT / 'assets' / slug / variant / (slug + '.vox'))
            checks = []

            def region(lo, hi):
                # Probe boxes are on even large-grid boundaries so the exact
                # same physical volume is examined in each saved resolution.
                assert all(v % factor == 0 for v in (*lo, *hi))
                return grid.data[tuple(slice(a//factor, b//factor) for a, b in zip(lo, hi))]

            def empty(name, lo, hi):
                a = region(lo, hi)
                count = int(np.count_nonzero(a))
                checks.append(dict(name=name, physical_probe_large_coordinates=[lo, hi],
                                   expected='empty', occupied_voxels=count, passed=count == 0))

            def color(name, lo, hi, indices, minimum=1):
                a = region(lo, hi)
                count = int(np.count_nonzero(np.isin(a, indices)))
                checks.append(dict(name=name, physical_probe_large_coordinates=[lo, hi],
                                   palette_indices=indices, matched_voxels=count,
                                   minimum=minimum, passed=count >= minimum))

            if slug == 'fire_engine':
                empty('clear aperture through both roof ladder levels', (30, 60, 66), (34, 64, 74))
                color('exposed hose coil rubber', (52, 68, 32), (58, 92, 56), [13], 20)
                color('right shutter grooves', (54, 48, 34), (56, 64, 56), [5], 10)
                color('front windshield glazing', (18, 6, 38), (30, 10, 54), [7, 8], 10)
            elif slug == 'rescue_robot':
                empty('open working gap between gripper jaws', (40, 2, 56), (56, 14, 68))
                empty('clearance beneath chassis between tracks', (34, 80, 6), (62, 100, 18))
                color('single optical camera lens', (42, 74, 82), (54, 82, 96), [7, 8], 8)
                color('left manipulator jaw', (26, 2, 56), (38, 16, 68), [4, 5], 8)
                color('right manipulator jaw', (58, 2, 56), (70, 16, 68), [4, 5], 8)
                color('track roadwheel hub surfaces', (86, 48, 10), (92, 114, 24), [6], 20)
            elif slug == 'fire_station':
                empty('first bay clear entry and full vehicle depth', (18, 8, 18), (40, 70, 54))
                empty('second bay clear entry and full vehicle depth', (62, 8, 18), (84, 70, 54))
                color('load-bearing central pier', (48, 8, 18), (54, 16, 58), [3, 11], 20)
                color('hose drying tower hoses', (106, 40, 62), (120, 46, 104), [13], 20)
                color('back-wall equipment shelves', (64, 74, 12), (88, 80, 44), [6], 20)
            else:
                empty('open rescue-loading cabin volume', (60, 48, 34), (80, 62, 48))
                empty('rotor air clearance above cabin left of shaft', (46, 42, 68), (56, 62, 72))
                empty('space between skids under fuselage', (50, 28, 6), (78, 68, 14))
                empty('open rescue hook throat', (92, 50, 14), (94, 52, 18))
                color('rounded cockpit glazing', (46, 18, 38), (82, 38, 58), [7, 8], 30)
                color('main rotor blades', (8, 12, 76), (122, 94, 80), [4, 9], 50)
                color('tail rotor blades', (70, 106, 44), (76, 128, 66), [4, 9], 15)
                # Black cable ends at the amber hook connection below Z=24.
                cable = region((90, 52, 24), (96, 56, 48))
                every_z = np.any(cable == 14, axis=(0, 1))
                checks.append(dict(name='winch cable remains continuous in every vertical slice',
                                   checked_slices=int(len(every_z)),
                                   present_slices=int(np.count_nonzero(every_z)),
                                   passed=bool(np.all(every_z))))
            records.append(dict(asset=slug, variant=variant, checks=checks,
                                passed=all(c['passed'] for c in checks)))
    result = dict(passed=all(r['passed'] for r in records), started_at_utc=started,
                  finished_at_utc=datetime.now(timezone.utc).isoformat(),
                  elapsed_seconds=time.perf_counter()-timer, records=records)
    (ROOT / 'validation_native_features.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    failed = [(r['asset'], r['variant'], c['name']) for r in records for c in r['checks'] if not c['passed']]
    print(json.dumps(dict(passed=result['passed'], variants=len(records), failures=failed)))
    if failed:
        raise AssertionError(failed)


if __name__ == '__main__':
    main()
