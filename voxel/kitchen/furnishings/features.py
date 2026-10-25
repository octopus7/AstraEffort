"""Saved-VOX probes. Coordinates below are specified in the large grid."""
import numpy as np

# Interior regions avoid rounded silhouette boundary cells. Each empty probe
# checks all cells, and each material probe checks a meaningful solid subregion.
PROBES={
 'sink_cabinet': [
  ('sink basin open interior',(38,30,80),(54,50,94),0),
  ('sink metal floor',(38,30,70),(54,50,74),7),
  ('left door pull air gap',(44,4,58),(50,7,62),0),
  ('faucet suspended over basin',(61,49,104),(67,59,113),0),
 ],
 'kitchen_island': [
  ('upper side shelf clear bay',(94,25,52),(114,60,74),0),
  ('lower side shelf clearance',(94,25,34),(114,60,42),0),
  ('right shelf floor',(94,25,44),(114,60,48),5),
  ('towel rail opening',(118,29,62),(122,33,66),0),
 ],
 'dish_cabinet': [
  ('lower display shelf front clearance',(14,12,64),(78,19,82),0),
  ('upper display shelf right clearance',(46,12,94),(76,18,114),0),
  ('mug cavity',(60,27,104),(66,31,110),0),
  ('shelf solid base',(14,14,86),(76,42,90),5),
 ],
 'kitchen_cart': [
  ('middle shelf open bay',(20,18,73),(80,58,81),0),
  ('bottom shelf clearance over towels',(20,18,50),(80,54,62),0),
  ('transport handle loop',(94,22,118),(98,52,122),0),
  ('drawer pull empty gap',(42,4,94),(58,6,98),0),
 ],
 'dish_drying_rack': [
  ('first plate slot front air',(23,12,26),(31,18,40),0),
  ('between plates air',(32,34,34),(34,60,44),0),
  ('utensil cup open interior',(95,49,30),(102,52,44),0),
  ('left tray handle opening',(2,40,14),(6,54,18),0),
 ],
 'knife_block': [
  ('unused front slot',(34,18,46),(46,26,64),0),
  ('air between handles',(28,40,106),(32,52,114),0),
  ('left knife broad metal blade',(18,36,80),(22,46,92),7),
  ('oak block front solid',(14,12,14),(62,16,46),5),
 ],
}

def probe_features(slug,grid,variant):
    factor=1 if variant=='large' else 2
    results=[]
    for name,lo,hi,expected in PROBES[slug]:
        # Only half voxels whose full source block is inside the probe box.
        a=np.ceil(np.array(lo)/factor).astype(int)
        b=np.floor(np.array(hi)/factor).astype(int)
        assert np.all(b>a),(slug,variant,name,'empty probe definition')
        region=grid.data[tuple(slice(int(x),int(y)) for x,y in zip(a,b))]
        actual=np.unique(region).astype(int).tolist()
        passed=bool(np.all(region==expected))
        results.append({'feature':name,'bounds_voxels':[a.tolist(),b.tolist()],
                        'expected_palette_index':expected,'found_palette_indices':actual,
                        'cells_checked':int(region.size),'passed':passed})
    return results
