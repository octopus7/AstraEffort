from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parent
manifest=json.loads((P/'Screenshots/capture_manifest.json').read_text())
captures={r['name']:r for r in manifest['captures']}
images=[]
for name in captures:
    f=P/'Screenshots'/(name+'.png');im=Image.open(f).convert('RGB');a=np.asarray(im)
    images.append({'name':name,'dimensions':list(im.size),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'rgb_std':a.std(axis=(0,1)).tolist()})
motion={}
for group,prefix in [('canal','canal_motion'),('rainy_street','rainy_street_motion'),('water_only','water_only'),('puddle','puddle')]:
    n0=prefix+'_t0';n1=prefix+'_t1';a=np.asarray(Image.open(P/'Screenshots'/(n0+'.png')).convert('RGB'),dtype=np.int16);b=np.asarray(Image.open(P/'Screenshots'/(n1+'.png')).convert('RGB'),dtype=np.int16)
    assert captures[n0]['camera']==captures[n1]['camera']
    d=np.abs(a-b).max(axis=2)
    motion[group]={'world_time_t0':captures[n0]['world_time_seconds'],'world_time_t1':captures[n1]['world_time_seconds'],'delta_seconds':captures[n1]['world_time_seconds']-captures[n0]['world_time_seconds'],'changed_pixels_threshold12':int((d>12).sum()),'changed_pixels_threshold4':int((d>4).sum()),'rain_hidden':captures[n0]['rain_hidden_for_isolation'],'interpretation':'Same-camera actual UE images; rain hidden in water_only/puddle pairs to isolate water, remaining differences include shading and temporal rendering.'}
result={'utc':datetime.now(timezone.utc).isoformat(),'images':images,'all_1920x1080':all(r['dimensions']==[1920,1080] for r in images),'all_nonblank':all(min(r['rgb_std'])>3 for r in images),'motion':motion}
(P/'render_analysis.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='images'},indent=2))
