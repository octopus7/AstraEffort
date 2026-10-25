"""Replay specified opening/mechanism probes against the saved VOX binaries."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_tools'))
from voxelkit import read_vox
r=Path(__file__).resolve().parent;probes=json.loads((r/'feature_validation.json').read_text(encoding='utf-8'));cache={}
for p in probes:
    key=(p['asset'],p['variant'])
    if key not in cache:cache[key]=read_vox(r/'assets'/key[0]/key[1]/(key[0]+'.vox'))
    s=1 if key[1]=='large' else 2
    point=tuple(int(x//s) for x in p['point_large_coordinates']);value=int(cache[key].data[point])
    assert bool(value)==(p['kind']=='solid'),(key,point,value)
out={'passed':True,'saved_native_variants':len(cache),'probe_count':len(probes),'checks':probes}
(r/'validation_features_saved.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps({'passed':True,'probe_count':len(probes)}))
