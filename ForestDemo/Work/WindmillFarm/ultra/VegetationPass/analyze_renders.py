from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
from PIL import Image
import numpy as np
P=Path(__file__).resolve().parent
manifest=json.loads((P/'Screenshots/capture_manifest.json').read_text());rows=[]
for capture in manifest['captures']:
    name=capture['name'];path=P/'Screenshots'/(name+'.png');im=Image.open(path).convert('RGB');a=np.asarray(im)
    rows.append({'name':name,'dimensions':list(im.size),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rgb_std':np.std(a,axis=(0,1)).tolist()})
times={c['name']:c['world_time_seconds'] for c in manifest['captures']};motion={}
for group in ('corn','meadow','windmill'):
    a=np.asarray(Image.open(P/'Screenshots'/(group+'_motion_t0.png')).convert('RGB'),dtype=np.int16)
    b=np.asarray(Image.open(P/'Screenshots'/(group+'_motion_t1.png')).convert('RGB'),dtype=np.int16)
    mask=np.max(abs(a-b),axis=2)>12;y,x=np.where(mask)
    motion[group]={'changed_pixels_threshold12':int(mask.sum()),'world_time_t0':times[group+'_motion_t0'],'world_time_t1':times[group+'_motion_t1'],'delta_seconds':times[group+'_motion_t1']-times[group+'_motion_t0'],
                   'difference_bbox_xyxy':[int(x.min()),int(y.min()),int(x.max()),int(y.max())] if len(x) else None,'interpretation':'Same-camera actual UE renders: visible wind movement plus shadows/temporal differences; not a physics measurement.'}
data={'utc':datetime.now(timezone.utc).isoformat(),'images':rows,'all_1920x1080':all(r['dimensions']==[1920,1080] for r in rows),'all_nonblank':all(min(r['rgb_std'])>10 for r in rows),'motion':motion}
(P/'render_analysis.json').write_text(json.dumps(data,indent=2));print(json.dumps(data,indent=2))
