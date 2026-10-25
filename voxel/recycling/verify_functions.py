"""Functional probes reopen final VOX files, independently of source generation."""
from pathlib import Path
from datetime import datetime, timezone
import json
import time
import sys
import numpy as np

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root.parent / '_tools'))
from voxelkit import read_vox

records = []
started = datetime.now(timezone.utc).isoformat()
t0 = time.perf_counter()

def point(grid, xyz, reduction):
    return int(grid.data[tuple(int(n // reduction) for n in xyz)])

def region(grid, lo, hi, reduction):
    return grid.data[tuple(slice(int(a // reduction), int(b // reduction)) for a, b in zip(lo, hi))]

def add(asset, variant, description, passed, evidence):
    records.append({'asset': asset, 'variant': variant, 'description': description, 'passed': bool(passed), 'evidence': evidence})

for slug in ('collection_truck', 'sorting_machine', 'compactor', 'recycling_center'):
    for variant, reduction in (('large', 1), ('half', 2)):
        g = read_vox(root / 'assets' / slug / variant / f'{slug}.vox')
        p = lambda xyz: point(g, xyz, reduction)
        box = lambda lo, hi: region(g, lo, hi, reduction)
        if slug == 'collection_truck':
            cavity = box((24, 12, 44), (50, 30, 64))
            floor, back, lip = p((37, 18, 37)), p((37, 35, 58)), p((37, 5, 35))
            add(slug, variant, 'Rear hopper has an empty cavity, sloped floor, back and loading lip', not cavity.any() and all((floor, back, lip)), {'empty_cells': int((cavity == 0).sum()), 'cavity_cells': int(cavity.size), 'floor_back_lip_colors': [floor, back, lip]})
            access = box((28, 0, 52), (46, 30, 62))
            add(slug, variant, 'Hopper cavity connects to the rear exterior through a real opening', not access.any(), {'empty_access_cells': int((access == 0).sum()), 'access_cells': int(access.size)})
        elif slug == 'sorting_machine':
            values = []
            for cx, cy, throat_x in ((16, 77, 27), (112, 79, 101)):
                cavity = box((cx - 4, cy - 5, 54), (cx + 4, cy + 5, 64))
                values.append({'empty': not bool(cavity.any()), 'empty_cells': int((cavity == 0).sum()), 'total_cells': int(cavity.size), 'throat_color': p((throat_x, cy, 44)), 'throat_floor_color': p((throat_x, cy, 38))})
            add(slug, variant, 'Both receiving funnels have open bowls and lateral throats over solid floors', all(v['empty'] and v['throat_color'] == 0 and v['throat_floor_color'] > 0 for v in values), values)
            belt = box((42, 16, 32), (86, 84, 36))
            add(slug, variant, 'Sorting belt surface is continuous along its working run', bool(np.all(belt > 0)), {'occupied_belt_cells': int((belt > 0).sum()), 'tested_cells': int(belt.size)})
            clearance = box((42, 50, 48), (88, 58, 70))
            emitters = [p((48, 53, 75)), p((78, 53, 75))]
            add(slug, variant, 'Two overhead sensor heads retain a clear sensing gap above the belt', not clearance.any() and emitters == [9, 9], {'empty_gap_cells': int((clearance == 0).sum()), 'gap_cells': int(clearance.size), 'emitter_colors': emitters})
        elif slug == 'compactor':
            gap = box((36, 26, 50), (68, 60, 68))
            entry = box((32, 0, 50), (72, 20, 68))
            add(slug, variant, 'Press chamber is open from the front and above the bale', not gap.any() and not entry.any(), {'empty_chamber_cells': int((gap == 0).sum()), 'chamber_cells': int(gap.size), 'empty_entry_cells': int((entry == 0).sum()), 'entry_cells': int(entry.size)})
            ram, guide, plate = p((52, 47, 93)), p((34, 47, 93)), p((52, 47, 76))
            add(slug, variant, 'Exposed ram, guide column and raised platen remain distinct materials', ram == 9 and guide == 8 and plate == 7, {'ram_guide_platen_colors': [ram, guide, plate]})
            bale, strap, floor = p((52, 36, 36)), p((43, 23, 36)), p((52, 35, 15))
            add(slug, variant, 'Strapped bale remains seated on the chamber floor', bale in (14, 15) and strap == 6 and floor == 7, {'bale_strap_floor_colors': [bale, strap, floor]})
        else:
            portal = box((18, 24, 14), (52, 80, 64))
            floor, rear, access = p((35, 35, 6)), p((35, 87, 40)), p((35, 16, 35))
            add(slug, variant, 'Receiving portal opens into a hollow hall with retained floor and rear wall', not portal.any() and floor > 0 and rear > 0 and access == 0, {'empty_hall_cells': int((portal == 0).sum()), 'hall_cells': int(portal.size), 'floor_rear_access_colors': [floor, rear, access]})
            bins = []
            for cx in (75, 94, 113):
                interior = box((cx - 2, 24, 18), (cx + 2, 38, 50))
                bins.append({'empty_cells': int((interior == 0).sum()), 'interior_cells': int(interior.size), 'floor_color': p((cx, 30, 13)), 'front_rim_color': p((cx, 17, 28)), 'sidewall_color': p((cx - 6, 30, 26))})
            add(slug, variant, 'All three bin bays contain separate open-topped bins with retained floors and rims', all(b['empty_cells'] == b['interior_cells'] and b['floor_color'] == 7 and b['front_rim_color'] == 8 for b in bins) and [b['sidewall_color'] for b in bins] == [1, 9, 7], bins)

result = {'passed': all(r['passed'] for r in records), 'started_at_utc': started, 'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'elapsed_seconds': time.perf_counter() - t0, 'source': 'Reopened saved VOX occupancy; source make_assets() was not called', 'check_count': len(records), 'records': records}
(root / 'validation_function.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({'passed': result['passed'], 'check_count': len(records), 'failures': [r for r in records if not r['passed']]}), flush=True)
raise SystemExit(0 if result['passed'] else 1)
