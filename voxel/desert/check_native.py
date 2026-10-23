"""Read final native files and check recognizable construction features."""
from pathlib import Path
import json
import sys
import numpy as np

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root.parent / "_tools"))
from voxelkit import read_vox

records = []
for variant, step in (("large", 1), ("half", 2)):
    grids = {name: read_vox(root / "assets" / name / variant / (name + ".vox"))
             for name in ("exploration_rover", "water_tower", "solar_array", "repair_garage")}
    checks = []
    dimension_values = {name: list(grid.shape) for name, grid in grids.items()}
    checks.append({"feature": "All grid dimensions are even", "passed": all(n % 2 == 0 for shape in dimension_values.values() for n in shape), "grids": dimension_values})
    def at(name, p):
        return int(grids[name].data[tuple(int(q // step) for q in p)])
    wheels = [at("exploration_rover", (xx, yy, 22)) for xx in (4, 96) for yy in (28, 68, 108)]
    checks.append({"feature": "Six outboard wheel hubs", "passed": all(wheels), "colors": wheels})
    legs = [at("water_tower", (xx, yy, 25)) for xx in (25, 71) for yy in (27, 73)]
    checks.append({"feature": "Four separate support legs", "passed": all(legs), "colors": legs})
    solar = grids["solar_array"].data
    cuts = (0, 44 // step, 86 // step, solar.shape[0])
    bus_counts = [int(np.count_nonzero(solar[cuts[i]:cuts[i + 1]] == 11)) for i in range(3)]
    checks.append({"feature": "Three solar sections retain consistent bus lines", "passed": min(bus_counts) >= 0.80 * max(bus_counts), "alloy_voxels_per_section": bus_counts})
    passage = [at("repair_garage", (56, yy, 38)) for yy in (14, 24, 36, 48)]
    checks.append({"feature": "Garage front opens into a clear central bay", "passed": passage == [0, 0, 0, 0], "sample_colors": passage})
    records.append({"variant": variant, "passed": all(c["passed"] for c in checks), "checks": checks})

report = {"passed": all(r["passed"] for r in records), "source": "Reparsed delivered native VOX", "records": records}
output_name = sys.argv[1] if len(sys.argv) > 1 else "native_feature_checks.json"
(root / output_name).write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
raise SystemExit(0 if report["passed"] else 1)
