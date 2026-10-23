"""Semantic checks for authored mechanisms, independent of mesh exporters."""
from pathlib import Path
import importlib.util
import json
import sys

root = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("antarctic_build", root / "build.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assets = {asset.slug: asset for asset in module.make_assets()}
checks = []

def record(label, passed, evidence):
    checks.append({"check": label, "passed": bool(passed), "evidence": evidence})

station = assets["research_station"].grid.data
feet = [bool(station[x, y, 3]) for x in (22, 64, 106) for y in (38, 75)]
record("Six separated station pads", all(feet), feet)

snow = assets["snowcat"].grid.data
front_samples = []
for x in (32, 44, 60, 74):
    line = snow[x, :, 60]
    occupied = line.nonzero()[0]
    y = int(occupied[0])
    front_samples.append({"x": x, "z": 60, "first_y": y, "color": int(line[y])})
record("Snowcat windshield exposed to front", all(sample["color"] in (module.GLASS, module.SKY) for sample in front_samples), front_samples)
track_gaps = [int(snow[x, 44, 26]) for x in (16, 87)]
record("Both track belts preserve interior air", track_gaps == [0, 0], track_gaps)

radar = assets["radar"].grid.data
dish_void = int(radar[76, 52, 86])
record("Radar bowl has open air above its inner face", dish_void == 0, {"sample_xyz": [76, 52, 86], "color": dish_void})

weather = assets["weather_instrument"].grid.data
cup_void = int(weather[41, 21, 119])
record("Weather rotor cup contains an open cavity", cup_void == 0, {"sample_xyz": [41, 21, 119], "color": cup_void})

report = {"passed": all(c["passed"] for c in checks), "checks": checks}
path = root / (sys.argv[1] if len(sys.argv) > 1 else "geometry_semantics.json")
path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
raise SystemExit(0 if report["passed"] else 1)
