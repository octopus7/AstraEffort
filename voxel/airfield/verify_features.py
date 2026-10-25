"""Critical saved-native openings, mechanisms, and common-camera window visibility."""
from pathlib import Path
from datetime import datetime, timezone
import json, sys, time
sys.dont_write_bytecode = True
import numpy as np
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent/'_tools'))
from voxelkit import read_vox


def glass_visibility(grid, reduction):
    data = grid.data
    previous = np.pad(data, ((0,0),(1,0),(0,0)))[:, :-1, :]
    front = np.isin(data, [11,12]) & (previous == 0)
    front[:,:,:int(79/reduction)] = False
    points = np.argwhere(front)
    direction = np.array([1.35, -1.8, 1.2])
    direction /= np.linalg.norm(direction)
    visible = 0
    for p in points:
        samples = np.floor(p+.5+np.arange(.5,180,.5)[:,None]*direction).astype(int)
        valid = np.all(samples >= 0, axis=1) & np.all(samples < np.array(grid.shape), axis=1)
        samples = samples[valid]
        samples = samples[np.any(samples != p, axis=1)]
        if not np.any(data[tuple(samples.T)] > 0):
            visible += 1
    return {'exposed_front_glass_cells': len(points), 'unoccluded_glass_cells': visible, 'ray_direction': direction.tolist(), 'sample_step_cells': .5, 'method': 'Saved native occupancy rays from front glass towards common camera, including roof and railing occluders.'}


def main():
    t0 = time.perf_counter()
    started = datetime.now(timezone.utc).isoformat()
    checks = []
    for asset in ('propeller_plane','airport_tug','maintenance_hangar','control_tower'):
        for variant in ('large','half'):
            grid = read_vox(ROOT/'assets'/asset/variant/(asset+'.vox'))
            divisor = 1 if variant=='large' else 2
            def check(name, passed, evidence):
                checks.append(dict(asset=asset, variant=variant, check=name, passed=bool(passed), evidence=evidence))
            def area(lo, hi):
                low = np.floor(np.array(lo)/divisor).astype(int)
                high = np.ceil(np.array(hi)/divisor).astype(int)
                return grid.data[tuple(slice(a,b) for a,b in zip(low,high))]
            def empty(name, lo, hi):
                d = area(lo,hi)
                n = int(np.count_nonzero(d))
                check(name,n==0,dict(bounds_large=[lo,hi],occupied=n,tested_cells=int(d.size)))
            def color(name, lo, hi, palette, minimum=1):
                n = int(np.count_nonzero(np.isin(area(lo,hi),palette)))
                check(name,n>=minimum,dict(bounds_large=[lo,hi],palette=palette,matched_cells=n,minimum=minimum))
            if asset=='propeller_plane':
                for x in (10,114):
                    color('Broad blunt wing tip %d'%x,(x-3,40,28),(x+3,54,32),[4],20)
                for x,z in ((53,22),(75,48)):
                    color('Propeller blade %d'%x,(x-2,6,z-2),(x+2,10,z+2),[7,9],3)
                for x,y,z in ((35,46,7),(93,46,7),(64,16,5)):
                    color('Landing wheel %d/%d'%(x,y),(x-3,y-4,z-3),(x+3,y+4,z+3),[9,10,13],6)
                color('Cockpit glass retained',(65,29,46),(74,52,54),[11,12],20)
            elif asset=='airport_tug':
                empty('Coupling eye has genuine central hole',(39,6,10),(41,8,12))
                color('Towbar shaft',(38,14,10),(42,34,18),[7,8],10)
                color('Towbar support wheel',(37,18,1),(43,26,9),[9,10,13],10)
                color('Front cab glazing',(27,46,40),(55,51,58),[11,12],20)
                color('Rear power enclosure',(25,88,40),(56,115,48),[10,13],30)
            elif asset=='maintenance_hangar':
                empty('Full-width front portal is open',(20,12,8),(108,22,64))
                empty('Large interior maintenance bay is empty',(24,24,8),(104,76,62))
                color('Arched roof crown',(54,32,94),(74,96,102),[4,5],30)
                color('Right side windows',(119,38,40),(122,97,48),[11,12],20)
                color('Attached rear workbench',(23,89,23),(58,102,27),[18],20)
            else:
                color('Panoramic upper cab glass',(21,16,80),(77,80,102),[11,12],150)
                color('Low balcony rail',(20,13,74),(72,16,78),[13],15)
                visibility = glass_visibility(grid,divisor)
                check('Glazing visible above rail and below roof in shared view',visibility['unoccluded_glass_cells'] >= (80 if divisor==1 else 20),visibility)
    failures = [c for c in checks if not c['passed']]
    result = dict(passed=not failures, started_at_utc=started, finished_at_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.perf_counter()-t0, source='Saved authoritative VOX data only', check_count=len(checks), failures=failures, checks=checks)
    (ROOT/'validation_features.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=result['passed'],check_count=len(checks),failures=failures),indent=2))
    if failures:
        raise SystemExit(1)


if __name__=='__main__':
    main()
