"""Mechanism and opening checks on reparsed native underwater VOX files."""
from pathlib import Path
import json
import sys
import numpy as np

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root.parent / "_tools"))
from voxelkit import read_vox

slugs = ["submersible", "dome_laboratory", "connecting_tunnel", "seabed_miner", "docking_station"]
records = []
for size, scale in (("large", 1), ("half", 2)):
    grids = {slug: read_vox(root / "assets" / slug / size / f"{slug}.vox") for slug in slugs}
    checks = []
    def occupied(slug, point):
        index = tuple(int(axis // scale) for axis in point)
        return int(grids[slug].data[index])
    shape_ok = all(max(grid.shape) == 128 // scale and (scale == 2 or all(n % 2 == 0 for n in grid.shape)) for grid in grids.values())
    checks.append({"feature": "Required grid dimensions", "passed": shape_ok, "grids": {slug: list(g.shape) for slug, g in grids.items()}})
    duct_samples = [occupied("submersible", (xx, yy, 58)) for xx in (24, 116) for yy in (48, 56, 64, 69)]
    checks.append({"feature": "Both thruster ducts have open water quadrants through their length", "passed": all(v == 0 for v in duct_samples), "sample_colors": duct_samples})
    airlock = [occupied("dome_laboratory", (64, yy, 30)) for yy in (4, 12, 22)]
    checks.append({"feature": "Airlock recess is open before a solid inner door", "passed": airlock[:2] == [0, 0] and airlock[2] > 0, "sample_colors": airlock})
    passage = [occupied("connecting_tunnel", (42, yy, 42)) for yy in (5, 12, 35, 64, 95, 119, 123)]
    checks.append({"feature": "Tunnel ends and central passage remain empty", "passed": all(v == 0 for v in passage), "sample_colors": passage})
    feet = [occupied("seabed_miner", (xx, yy, 4)) for xx in (12, 116) for yy in (36, 79, 117)]
    checks.append({"feature": "Six separate miner footpads", "passed": all(v > 0 for v in feet), "sample_colors": feet})
    arches = [occupied("docking_station", (56, yy, 50)) for yy in (30, 100)]
    checks.append({"feature": "Two docking arch throats remain empty", "passed": arches == [0, 0], "sample_colors": arches})
    opaque = all(all(grid.palette[int(i)][3] == 255 for i in np.unique(grid.data) if i != 0) for grid in grids.values())
    checks.append({"feature": "All used glazing/material colors are explicitly opaque", "passed": opaque})
    records.append({"variant": size, "passed": all(c["passed"] for c in checks), "checks": checks})
report = {"passed": all(record["passed"] for record in records), "source": "Reparsed saved native VOX", "records": records}
(root / "native_feature_checks.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
raise SystemExit(0 if report["passed"] else 1)
