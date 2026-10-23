from pathlib import Path
import sys,json
import numpy as np
sys.path.insert(0,r"D:\github\AstraEffort\voxel\_tools")
from voxelkit import read_vox
root=Path(__file__).resolve().parent
records=[]
for variant,f in (("large",1),("half",2)):
    g=read_vox(root/"assets/haul_truck"/variant/"haul_truck.vox")
    def at(p): return int(g.data[tuple(np.floor(np.asarray(p)/f).astype(int))])
    lo=np.ceil(np.array((27,63,55))/f).astype(int)
    hi=np.floor(np.array((77,109,81))/f).astype(int)
    empty=not np.any(g.data[tuple(slice(a,b) for a,b in zip(lo,hi))])
    checks={"deep_empty_dump_bed":empty,
            "six_wheel_centers":all(at((x,y,18))>0 for x in (16,88) for y in (28,76,109)),
            "bed_floor_and_rim":all(at(p)>0 for p in ((52,85,46),(14,85,86))),
            "offset_cab_window":at((66,10,63))>0,
            "hinge_and_hoist":all(at(p)>0 for p in ((86,114,40),(88,85,44)))}
    records.append({"variant":variant,"passed":all(checks.values()),"empty_bed_probe_voxels":int(np.prod(hi-lo)),"checks":checks})
report={"passed":all(x["passed"] for x in records),"checks_per_variant":5,"records":records}
(root/"feature_validation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
assert report["passed"]
