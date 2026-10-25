from pathlib import Path
import sys, json
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import validate as v
import numpy as np
from voxelkit import read_vox

findings=[]
for slug in v.EXPECTED:
    for variant,divisor in [('large',1),('half',2)]:
        g=read_vox(v.ROOT/'assets'/slug/variant/(slug+'.vox'))
        for name,point,occupied in v.FEATURES[slug]:
            c=tuple(q//divisor for q in point)
            value=int(g.data[c])
            nearby=int(np.count_nonzero(g.data[tuple(slice(q-1,q+1) for q in c)]))
            if bool(value)!=occupied or (not occupied and nearby):
                findings.append({'asset':slug,'variant':variant,'feature':name,'point':point,'value':value,'nearby_occupied':nearby})
        if slug=='toaster':
            for x in (27,28,29,30):
                p=(x//divisor,55//divisor,58//divisor)
                print('toaster slot end',variant,x,int(np.count_nonzero(g.data[tuple(slice(q-1,q+1) for q in p)])))
print(json.dumps(findings,indent=2))
