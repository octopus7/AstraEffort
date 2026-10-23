"""Check required openings and mechanical paths in saved native voxel grids."""
from pathlib import Path
import sys
import json
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "_tools"))
from voxelkit import read_vox

def occupied(grid, point, factor):
    p = tuple(np.floor(np.asarray(point) / factor).astype(int))
    return bool(grid.data[p])

def empty_box(grid, lo, hi, factor):
    a = np.ceil(np.asarray(lo) / factor).astype(int)
    b = np.floor(np.asarray(hi) / factor).astype(int)
    return not np.any(grid.data[tuple(slice(x, y) for x, y in zip(a, b))])

def path_occupied(grid, a, b, factor):
    a, b = np.asarray(a), np.asarray(b)
    count = int(np.linalg.norm(b - a) * 2) + 1
    return all(occupied(grid, a + (b - a) * t, factor) for t in np.linspace(0, 1, count))

records = []
for variant, factor in (("large", 1), ("half", 2)):
    grids = {slug: read_vox(ROOT / "assets" / slug / variant / (slug + ".vox"))
             for slug in ("excavator", "mine_cart", "mine_elevator", "ore_sorter")}
    e, c, lift, sorter = (grids[s] for s in ("excavator", "mine_cart", "mine_elevator", "ore_sorter"))
    checks = {
        "excavator_bucket_open_volume": empty_box(e, (26, 4, 26), (50, 20, 40), factor),
        "excavator_bucket_side_and_back": all(occupied(e, p, factor) for p in ((20, 17, 34), (38, 31, 34))),
        "excavator_two_track_internal_spaces": all(not occupied(e, p, factor) for p in ((20, 76, 19), (84, 76, 19))),
        "cart_open_bed": empty_box(c, (35, 29, 62), (94, 51, 78), factor),
        "cart_four_wheel_centers": all(occupied(c, (x, y, 15), factor) for x in (30, 98) for y in (14, 66)),
        "elevator_clear_cage_portal": empty_box(lift, (36, 26, 23), (50, 34, 48), factor),
        "elevator_open_sheave_web": not occupied(lift, (47, 44, 119), factor),
        "elevator_cage_cable": path_occupied(lift, (31, 42, 115), (31, 42, 65), factor),
        "elevator_winch_cable": path_occupied(lift, (55, 42, 115), (96, 60, 61), factor),
        "sorter_open_hopper": empty_box(sorter, (22, 58, 90), (48, 80, 101), factor),
        "sorter_screen_aperture": not occupied(sorter, (60, 52, 59), factor),
        "sorter_screen_rail_and_discharge": all(occupied(sorter, p, factor) for p in ((60, 36, 59), (104, 40, 60))),
    }
    records.append({"variant": variant, "passed": all(checks.values()), "checks": checks})
report = {"passed": all(row["passed"] for row in records), "source": "Reopened authoritative VOX files",
          "checks_per_variant": 12, "records": records}
(ROOT / "feature_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
assert report["passed"], "A required mine opening or mechanical path failed its saved-native probe."
