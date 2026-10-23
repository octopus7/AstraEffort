from pathlib import Path
import json
import sys
import numpy as np
sys.path.insert(0, r"D:\github\AstraEffort\voxel\_tools")
from voxelkit import read_vox
root = Path(__file__).resolve().parent
records = []
for variant, factor in (("large",1),("half",2)):
    g = read_vox(root / "assets/robot_workcell" / variant / "robot_workcell.vox")
    def at(p):
        return int(g.data[tuple(np.floor(np.asarray(p)/factor).astype(int))])
    checks = {
        "separated_gripper_fingers": not np.any(g.data[31//factor:43//factor,18//factor:26//factor,64//factor:77//factor]),
        "both_blunt_finger_pads": all(at(p)>0 for p in ((26,22,65),(48,22,65))),
        "three_round_joint_centers": all(at(p)>0 for p in ((79,67,57),(64,62,105),(37,25,91))),
        "workpiece_bore": at((37,23,50))==0,
        "fixture_table_and_console": all(at(p)>0 for p in ((37,23,35),(97,8,51))),
    }
    records.append({"variant":variant,"passed":all(checks.values()),"checks":checks})
report = {"passed":all(r["passed"] for r in records),"checks_per_variant":5,"records":records}
(root/"feature_validation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
assert report["passed"]
