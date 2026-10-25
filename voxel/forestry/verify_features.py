"""Meaningful critical-feature checks against SAVED authoritative native occupancy."""
from pathlib import Path
from datetime import datetime, timezone
import json
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / '_tools'))
from voxelkit import read_vox


def region(g, variant, lo, hi):
    factor = 1 if variant == 'large' else 2
    low = np.floor(np.array(lo) / factor).astype(int)
    high = np.ceil(np.array(hi) / factor).astype(int)
    return g.data[tuple(slice(a, b) for a, b in zip(low, high))]


def main():
    started = datetime.now(timezone.utc).isoformat()
    t0 = time.perf_counter()
    rows = []
    def check(slug, variant, name, okay, evidence):
        rows.append({'asset': slug, 'variant': variant, 'check': name, 'passed': bool(okay), 'evidence': evidence})

    for slug in ('logging_harvester', 'timber_forwarder', 'sawmill', 'log_rack'):
        for variant in ('large', 'half'):
            g = read_vox(ROOT / 'assets' / slug / variant / (slug + '.vox'))
            def empty(name, lo, hi):
                a = region(g, variant, lo, hi)
                check(slug, variant, name, np.count_nonzero(a) == 0, {'bounds_large_grid': [lo, hi], 'occupied_cells': int(np.count_nonzero(a)), 'tested_cells': int(a.size)})
            def colored(name, lo, hi, colors, minimum=1):
                a = region(g, variant, lo, hi)
                n = int(np.count_nonzero(np.isin(a, colors)))
                check(slug, variant, name, n >= minimum, {'bounds_large_grid': [lo, hi], 'palette_indices': colors, 'matched_cells': n, 'minimum': minimum})
            if slug == 'logging_harvester':
                empty('Feed throat stays open between rollers', (108, 8, 40), (110, 20, 66))
                for x in (101, 116):
                    for z in (44, 61):
                        colored('Distinct feed roller %s/%s' % (x, z), (x-3, 6, z-3), (x+3, 12, z+3), [6, 7, 8, 9], 4)
                colored('Hanging head top frame survives', (98, 22, 70), (120, 30, 76), [4, 5], 12)
            elif slug == 'timber_forwarder':
                empty('Grapple central opening above upper log', (36, 102, 94), (44, 108, 96))
                for x in (25, 55):
                    colored('Grapple claw %s' % x, (x-2, 102, 88), (x+2, 108, 94), [4, 5], 3)
                for x in (13, 67):
                    colored('Bunk stake row %s' % x, (x-3, 59, 36), (x+3, 121, 86), [1, 4], 100)
                colored('Five-log load and native end grain', (18, 58, 38), (63, 120, 93), [16, 17, 18, 19, 20], 500)
            elif slug == 'sawmill':
                empty('Front portal left walking clearance', (24, 42, 24), (36, 56, 54))
                for y in (14, 26, 38, 50):
                    colored('Exposed transverse feed roller %s' % y, (74, y-2, 24), (84, y+2, 28), [9], 4)
                colored('Circular saw blade remains silver', (78, 70, 38), (80, 78, 56), [10], 4)
                colored('Right portal upright remains structural', (96, 44, 12), (104, 52, 78), [14, 15], 30)
            else:
                empty('Gap separates lower and middle logs', (38, 30, 38), (92, 40, 40))
                empty('Gap separates middle and upper logs', (38, 30, 64), (92, 40, 66))
                for x in (24, 104):
                    for loz, hiz in ((10, 12), (38, 40), (64, 66)):
                        colored('Concave cradle at %s/%s' % (x, loz), (x-2, 34, loz), (x+2, 36, hiz), [1], 1)
                colored('Native concentric end-grain survives', (118, 27, 16), (121, 43, 88), [19, 20], 40)
    failures = [r for r in rows if not r['passed']]
    report = {'passed': not failures, 'source': 'saved VOX occupancy only', 'started_at_utc': started,
              'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'elapsed_seconds': time.perf_counter()-t0,
              'check_count': len(rows), 'failures': failures, 'checks': rows}
    (ROOT / 'validation_features.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'passed': report['passed'], 'check_count': len(rows), 'failures': failures}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
