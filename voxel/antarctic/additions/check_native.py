"""Check the scientific rig's actual saved voxel openings and mechanisms."""
from pathlib import Path
import json
import sys
import numpy as np

root = Path(__file__).resolve().parent
sys.path.insert(0, "D:/github/AstraEffort/voxel/_tools")
from voxelkit import read_vox

records = []
for size, divisor in (("large", 1), ("half", 2)):
    grid = read_vox(root / "assets" / "ice_core_drill" / size / "ice_core_drill.vox")
    at = lambda p: int(grid.data[tuple(int(n // divisor) for n in p)])
    slot = [at((xx, 37, zz)) for xx in (47, 65) for zz in (24, 28, 32)]
    barrel = [at((56, 42, zz)) for zz in (12, 26, 46, 89)]
    pads = [at((xx, yy, 2)) for xx in (8, 104) for yy in (25, 81)]
    runners = [at((xx, 55, 7)) for xx in (25, 87)]
    cylinders = [at((xx, 74, 57)) for xx in (78, 88, 98)]
    separations = [at((xx, 74, 57)) for xx in (83, 93)]
    checks = [
        {"check": "Through-deck clearance beside barrel", "passed": all(v == 0 for v in slot), "colors": slot},
        {"check": "Vertical barrel continues below and above deck", "passed": all(v > 0 for v in barrel), "colors": barrel},
        {"check": "Four independent stabilizer pads", "passed": all(v > 0 for v in pads), "colors": pads},
        {"check": "Two sled runners", "passed": all(v > 0 for v in runners), "colors": runners},
        {"check": "Three sample cylinders separated by air", "passed": all(v > 0 for v in cylinders) and separations == [0, 0], "cylinders": cylinders, "gaps": separations},
        {"check": "Correct longest grid axis", "passed": max(grid.shape) == 128 // divisor, "grid": list(grid.shape)},
        {"check": "Occupied color indices are nonzero and opaque", "passed": all(grid.palette[int(i)][3] == 255 for i in np.unique(grid.data) if i > 0)},
    ]
    records.append({"variant": size, "passed": all(c["passed"] for c in checks), "checks": checks})
result = {"passed": all(r["passed"] for r in records), "source": "Reparsed authoritative native VOX", "records": records}
(root / "native_feature_checks.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(0 if result["passed"] else 1)
