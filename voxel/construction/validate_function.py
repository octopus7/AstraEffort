"""Saved-native checks of meaningful hollows, support geometry and functional parts."""
from pathlib import Path
from datetime import datetime, timezone
import json
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / '_tools'))
from voxelkit import read_vox

t0 = time.perf_counter()
started = datetime.now(timezone.utc).isoformat()
records = []

def check(slug, size, name, passed, evidence):
    records.append({'asset': slug, 'variant': size, 'check': name, 'passed': bool(passed), 'evidence': evidence})

def point(grid, xyz, divisor):
    return int(grid.data[tuple(int(c // divisor) for c in xyz)])

def volume(grid, lo, hi, divisor):
    return grid.data[tuple(slice(int(a // divisor), int(b // divisor)) for a, b in zip(lo, hi))]

for slug in ('concrete_mixer', 'wheel_loader', 'tower_crane', 'site_office'):
    for size, d in (('large', 1), ('half', 2)):
        g = read_vox(ROOT / 'assets' / slug / size / (slug + '.vox'))
        if slug == 'concrete_mixer':
            floor = point(g, (59, 116, 50), d)
            wall = point(g, (52, 116, 55), d)
            channel = volume(g, (56, 114, 54), (62, 120, 58), d)
            check(slug, size, 'Discharge chute has a floor, a sidewall and empty space above its floor', floor > 0 and wall > 0 and not channel.any(), {'floor_color': floor, 'wall_color': wall, 'channel_empty_cells': int((channel == 0).sum()), 'channel_total_cells': int(channel.size)})
            hopper = volume(g, (32, 114, 66), (40, 118, 74), d)
            check(slug, size, 'Feed hopper remains open from above', not hopper.any(), {'empty_cells': int((hopper == 0).sum()), 'total_cells': int(hopper.size)})
            z = int(56 // d)
            middle = np.flatnonzero(g.data[:, int(79 // d), z] > 0)
            end = np.flatnonzero(g.data[:, int(48 // d), z] > 0)
            widths = [int(np.ptp(a) + 1) if len(a) else 0 for a in (middle, end)]
            check(slug, size, 'Drum swells toward its center rather than a rectangular cargo box', widths[0] > widths[1] + 4 / d, {'middle_width_cells': widths[0], 'end_width_cells': widths[1]})
        elif slug == 'wheel_loader':
            void = volume(g, (18, 12, 18), (70, 30, 32), d)
            floor = point(g, (44, 20, 10), d)
            back = point(g, (44, 34, 30), d)
            check(slug, size, 'Scoop interior is empty with retained floor and back wall', not void.any() and floor > 0 and back > 0, {'empty_cells': int((void == 0).sum()), 'interior_cells': int(void.size), 'floor_color': floor, 'back_color': back})
            arms = [point(g, (x, 50, 45), d) for x in (28, 60)]
            gap = point(g, (44, 50, 45), d)
            check(slug, size, 'Two lift arms remain separate across the open center', all(arms) and gap == 0, {'arm_colors': arms, 'center_color': gap})
        elif slug == 'tower_crane':
            core = volume(g, (38, 28, 26), (42, 32, 88), d)
            check(slug, size, 'Tower has a continuous empty central shaft', not core.any(), {'empty_cells': int((core == 0).sum()), 'shaft_cells': int(core.size)})
            bay = point(g, (66, 24, 109), d)
            rail = point(g, (66, 24, 112), d)
            check(slug, size, 'Jib truss bay contains an opening beside its upper rail', bay == 0 and rail > 0, {'opening_color': bay, 'rail_color': rail})
            throat = volume(g, (104, 28, 54), (108, 32, 58), d)
            hook = point(g, (103, 30, 46), d)
            ropes = [point(g, (x, 30, 80), d) for x in (98, 105)]
            block = point(g, (101, 30, 64), d)
            check(slug, size, 'Suspended block has two ropes and a blunt hook with an open throat', not throat.any() and hook > 0 and block > 0 and all(ropes), {'throat_empty_cells': int((throat == 0).sum()), 'throat_cells': int(throat.size), 'hook_color': hook, 'block_color': block, 'rope_colors': ropes})
            contacts = [(x, y) for x in (19, 61) for y in (10, 50) if point(g, (x, y, 1), d) > 0]
            check(slug, size, 'All four separated support shoes contact Z=0 around the tower', len(contacts) == 4, {'contact_centers_large_grid': contacts, 'tower_center_large_grid': [40, 30]})
        else:
            windows = [point(g, p, d) for p in ((25, 15, 40), (95, 15, 40), (125, 32, 40))]
            door = point(g, (65, 15, 25), d)
            glass = point(g, (66, 14, 41), d)
            check(slug, size, 'Three framed blue windows and closed glazed door retain their readable palette regions', all(c in (9, 10) for c in windows) and door == 5 and glass in (9, 10), {'window_colors': windows, 'door_color': door, 'door_glass_color': glass})
            treads = [point(g, p, d) for p in ((67, 3, 2), (67, 9, 6), (67, 15, 9))]
            above = [point(g, p, d) for p in ((67, 3, 8), (67, 9, 12))]
            check(slug, size, 'Three rising access treads have clear space above the lower steps', all(treads) and not any(above), {'tread_colors': treads, 'above_lower_steps': above})

report = {'passed': all(r['passed'] for r in records), 'source': 'Reopened final native VOX files; no in-memory source grids used', 'started_at_utc': started, 'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'elapsed_seconds': time.perf_counter() - t0, 'check_count': len(records), 'records': records}
(ROOT / 'validation_function.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
if not report['passed']:
    raise SystemExit(1)
