"""Focused functional checks of reopened native occupancy, never render pixels."""
from pathlib import Path
from datetime import datetime, timezone
import json
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / '_tools'))
from voxelkit import read_vox


def check(slug, variant, grid):
    divisor = 1 if variant == 'large' else 2
    results = []

    def region(lo, hi):
        assert all(n % divisor == 0 for n in (*lo, *hi))
        return grid.data[tuple(slice(a // divisor, b // divisor) for a, b in zip(lo, hi))]

    def empty(name, lo, hi):
        part = region(lo, hi)
        count = int(np.count_nonzero(part))
        assert part.size and count == 0, f'{slug}/{variant}: {name}: {count} blocked cells'
        results.append({'probe': name, 'large_coordinate_box': [lo, hi], 'tested_cells': int(part.size), 'occupied_cells': count, 'passed': True})

    def present(name, lo, hi, colors):
        part = region(lo, hi)
        count = int(np.count_nonzero(np.isin(part, colors)))
        assert count > 0, f'{slug}/{variant}: {name}: no expected material'
        results.append({'probe': name, 'large_coordinate_box': [lo, hi], 'palette_indices': colors, 'matching_cells': count, 'passed': True})

    if slug == 'camper_van':
        empty('underbody clearance between right wheels', (60, 48, 2), (68, 76, 14))
        present('distinct broad windshield', (16, 12, 48), (58, 28, 66), [13, 14])
        present('entry door glazing', (64, 82, 54), (66, 92, 64), [13, 14])
        present('stowed awning tube', (64, 50, 70), (70, 114, 76), [3])
    elif slug == 'log_cabin':
        empty('unobstructed porch center between railings', (56, 20, 18), (76, 30, 40))
        empty('doorway recess ahead of inset door, excluding right handle', (56, 34, 20), (70, 40, 56))
        present('inset closed entrance door', (56, 42, 20), (76, 44, 56), [5, 6, 7])
        present('front stair tread', (56, 8, 6), (76, 12, 10), [5, 6, 7])
    elif slug == 'generator_trailer':
        empty('open drawbar ring center', (36, 8, 18), (40, 12, 22))
        empty('A-frame tongue gap', (34, 34, 18), (42, 40, 22))
        empty('real front louver aperture', (26, 50, 42), (50, 56, 44))
        present('support foot and leg', (40, 28, 2), (48, 34, 20), [10, 12])
        present('service controls', (64, 60, 40), (68, 76, 58), [10, 12, 15, 16])
    elif slug == 'shower_block':
        empty('central shower entrance beside open door', (50, 22, 18), (62, 28, 58))
        present('central shower head and riser', (50, 52, 60), (60, 68, 70), [10, 12, 19])
        present('external water heater cylinder', (112, 50, 28), (120, 56, 50), [1, 2])
        present('external hot water plumbing', (104, 50, 68), (120, 56, 74), [10, 19])
    return results


def main():
    began = datetime.now(timezone.utc).isoformat()
    timer = time.perf_counter()
    names = ['camper_van', 'log_cabin', 'generator_trailer', 'shower_block']
    records = []
    for slug in names:
        for variant in ('large', 'half'):
            path = ROOT / 'assets' / slug / variant / (slug + '.vox')
            assert path.is_file(), f'Missing native deliverable: {path}'
            grid = read_vox(path)
            records.append({'asset': slug, 'variant': variant, 'checks': check(slug, variant, grid)})
    report = {'passed': True, 'started_at_utc': began, 'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'elapsed_seconds': time.perf_counter() - timer, 'variant_count': len(records), 'probe_count': sum(len(r['checks']) for r in records), 'records': records}
    (ROOT / 'validation_functional.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'records'}))


if __name__ == '__main__':
    main()
