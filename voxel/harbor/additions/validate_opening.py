"""Semantic checks on the SAVED native VOX, independently of authoring functions."""
from pathlib import Path
from datetime import datetime, timezone
from collections import deque
import sys, json, time
import numpy as np

sys.dont_write_bytecode = True
sys.path.insert(0,'D:/github/AstraEffort/voxel/_tools')
from voxelkit import read_vox

ROOT = Path(__file__).resolve().parent

def component_sizes(mask):
    cells = set(map(tuple,np.argwhere(mask)))
    sizes = []
    while cells:
        seed = cells.pop()
        queue = deque([seed]); count = 1
        while queue:
            p = queue.popleft()
            for axis in range(3):
                for direction in (-1,1):
                    q = list(p); q[axis] += direction; q = tuple(q)
                    if q in cells:
                        cells.remove(q); queue.append(q); count += 1
        sizes.append(count)
    return sorted(sizes,reverse=True)

def region(grid,lo,hi,scale):
    a = tuple(int(v//scale) for v in lo)
    b = tuple(int(v//scale) for v in hi)
    return grid.data[tuple(slice(i,j) for i,j in zip(a,b))]

started = datetime.now(timezone.utc).isoformat(); tick = time.perf_counter()
records = []
for variant, scale in (('large',1),('half',2)):
    grid = read_vox(ROOT/'assets'/'repair_dock'/variant/'repair_dock.vox')
    checks = []
    for name,lo,hi in (
        ('front entry is empty above floor',(32,0,10),(96,16,34)),
        ('central upper work volume stays empty',(34,16,32),(94,94,44)),
    ):
        block = region(grid,lo,hi,scale)
        occupied = int(np.count_nonzero(block))
        assert occupied == 0, (variant,name,occupied)
        checks.append({'check':name,'large_coordinate_box':[lo,hi],'occupied_cells':occupied,'tested_cells':int(block.size),'passed':True})
    # Cropping above the continuous floor separates actual equipment components.
    keel_sizes = component_sizes(region(grid,(56,12,8),(72,96,22),scale)>0)
    assert len(keel_sizes)==3,(variant,'expected 3 discrete keel blocks',keel_sizes)
    checks.append({'check':'three disconnected centerline keel blocks above floor','components':len(keel_sizes),'component_voxels':keel_sizes,'passed':True})
    for side,lo,hi in (('left',(36,22,8),(54,90,32)),('right',(74,22,8),(92,90,32))):
        sizes = component_sizes(region(grid,lo,hi,scale)>0)
        assert len(sizes)==2,(variant,side,'expected 2 hull stands',sizes)
        checks.append({'check':f'{side} pair of discrete hull stands','components':len(sizes),'component_voxels':sizes,'passed':True})
    floor_cells = region(grid,(30,0,2),(98,96,4),scale)
    assert np.all(floor_cells>0),(variant,'bay floor must be continuous')
    checks.append({'check':'continuous lowered bay floor','passed':True})
    records.append({'variant':variant,'grid':list(grid.shape),'passed':True,'checks':checks})
report = {'passed':True,'started_at_utc':started,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.perf_counter()-tick,'source':'fresh saved VOX reparse; no authoring module imported','records':records}
(ROOT/'validation_opening.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'passed':True,'variants':2,'semantic_checks_per_variant':len(records[0]['checks'])}))
