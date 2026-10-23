"""Semantic probes of reopened spaceport native grids at both resolutions."""
from pathlib import Path
import sys
import json
import numpy as np

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root.parent / "_tools"))
from voxelkit import read_vox

def color(grid, point, scale):
    return int(grid.data[tuple(np.floor(np.asarray(point) / scale).astype(int))])

def filled(grid, points, scale):
    return all(color(grid, point, scale) > 0 for point in points)

def empty(grid, lo, hi, scale):
    lo = np.ceil(np.asarray(lo) / scale).astype(int)
    hi = np.floor(np.asarray(hi) / scale).astype(int)
    return not np.any(grid.data[tuple(slice(a, b) for a, b in zip(lo, hi))])

def connected(grid, a, b, scale):
    a, b = np.asarray(a), np.asarray(b)
    points = [a + (b - a) * t for t in np.linspace(0, 1, int(np.linalg.norm(b - a) * 2) + 1)]
    return filled(grid, points, scale)

records = []
for variant, scale in (("large", 1), ("half", 2)):
    grids = {s: read_vox(root / "assets" / s / variant / (s + ".vox")) for s in
             ("transport_rocket", "hangar", "exploration_rover", "fuel_tank", "control_tower")}
    rocket, hangar, rover, tank, tower = (grids[s] for s in
        ("transport_rocket", "hangar", "exploration_rover", "fuel_tank", "control_tower"))
    glazing_rows = 0
    for z in range(60 // scale, 98 // scale):
        front_line = tower.data[61 // scale, :50 // scale, z]
        nonempty = np.flatnonzero(front_line)
        if len(nonempty) and int(front_line[nonempty[0]]) == 12:
            glazing_rows += 1
    checks = {
        "rocket_four_landing_pads": filled(rocket, [(x, y, 5) for x in (14, 82) for y in (14, 82)], scale),
        "rocket_three_engine_mouths_empty": all(color(rocket, p, scale) == 0 for p in ((39, 41, 18), (57, 41, 18), (48, 59, 18))),
        "rocket_access_hatch": filled(rocket, ((48, 21, 67), (48, 18, 77)), scale),
        "hangar_open_spacecraft_portal": empty(hangar, (35, 15, 16), (93, 72, 52), scale),
        "hangar_floor_roof_back_wall": filled(hangar, ((64, 50, 8), (64, 60, 76), (64, 101, 35)), scale),
        "rover_six_wheel_centers": filled(rover, [(x, y, 16) for x in (14, 78) for y in (30, 66, 102)], scale),
        "rover_open_sample_tray": empty(rover, (29, 96, 58), (62, 116, 60), scale),
        "rover_sensor_mast_and_head": filled(rover, ((30, 53, 86), (30, 52, 95)), scale),
        "fuel_two_capsule_vessels": filled(tank, [(x, 40, z) for x in (36, 92) for z in (17, 70, 97)], scale),
        "fuel_joined_overhead_manifold": connected(tank, (36, 40, 104), (92, 40, 104), scale),
        "fuel_two_valve_controls": filled(tank, ((49, 4, 31), (79, 4, 31)), scale),
        "tower_hollow_cabin": empty(tower, (42, 40, 83), (66, 60, 93), scale),
        "tower_window_palette": color(tower, (61, 18, 94), scale) == 12,
        "tower_exposed_front_glazing_height": glazing_rows >= 20 // scale,
        "tower_shaft_roof_and_antennae": filled(tower, ((54, 50, 40), (54, 50, 106), (40, 49, 124), (70, 56, 121)), scale),
    }
    records.append({"variant": variant, "passed": all(checks.values()), "exposed_front_glazing_rows": glazing_rows, "checks": checks})
result = {"passed": all(record["passed"] for record in records), "checks_per_variant": 15,
          "source": "Reopened authoritative VOX occupancy", "records": records}
(root / "feature_validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
assert result["passed"], "A required spaceport native feature probe failed."
