"""Regression probes for grille slots observed to disappear in half previews.

These inspect the saved native occupancy, tracing the first occupied voxel from
the visible outside. A grille needs multiple exposed dark slots between bars;
merely having dark voxels hidden behind an opaque blue face is insufficient.
"""
from pathlib import Path
import json
import sys
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "_tools"))
from voxelkit import read_vox


def first_color(line):
    occupied = np.flatnonzero(line)
    return int(line[occupied[0]]) if len(occupied) else 0


press = read_vox(ROOT / "assets/production_machine/half/production_machine.vox")
conveyor = read_vox(ROOT / "assets/conveyor/half/conveyor.vox")
press_trace = [first_color(press.data[::-1, y, 46]) for y in range(26, 34)]
conveyor_trace = [first_color(conveyor.data[x, :, 14]) for x in range(40, 47)]
results = []
for name, trace in (("press_motor_grille", press_trace),
                    ("conveyor_motor_grille", conveyor_trace)):
    passed = trace.count(14) >= 2 and trace.count(5) >= 2
    results.append({"feature": name, "visible_palette_trace": trace,
                    "passed": passed})
report = {"passed": all(item["passed"] for item in results),
          "source": "Saved half-resolution native VOX occupancy", "checks": results}
for slug in ("production_machine", "conveyor", "forklift", "generator"):
    bounds = []
    for variant in ("large", "half"):
        grid = read_vox(ROOT / "assets" / slug / variant / (slug + ".vox"))
        occupied = np.argwhere(grid.data > 0)
        bounds.append(np.array((occupied.min(axis=0), occupied.max(axis=0) + 1)))
    passed = np.array_equal(bounds[0], bounds[1] * 2)
    results.append({"feature": slug + "_exact_physical_occupied_bounds",
                    "large_bounds_voxels": bounds[0].tolist(),
                    "half_bounds_voxels": bounds[1].tolist(), "passed": passed})
report["passed"] = all(item["passed"] for item in results)
report["source"] = "Saved large/half native VOX occupancy"
(ROOT / "feature_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
assert report["passed"], "Factory native geometry requirement failed."
