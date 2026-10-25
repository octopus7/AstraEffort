import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
rows=[]
for n in ['overview','top_down','windmill','farm_detail','prop_contact','windmill_motion_t0','windmill_motion_t1']:
    p=ROOT/'Screenshots'/(n+'.png');im=Image.open(p).convert('RGB');a=np.asarray(im)
    rows.append({'name':n,'dimensions':list(im.size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rgb_std':np.std(a,axis=(0,1)).tolist(),'unique_colors':len(np.unique(a.reshape(-1,3),axis=0))})
a=np.asarray(Image.open(ROOT/'Screenshots/windmill_motion_t0.png').convert('RGB'),dtype=np.int16)
b=np.asarray(Image.open(ROOT/'Screenshots/windmill_motion_t1.png').convert('RGB'),dtype=np.int16)
diff=np.max(abs(a-b),axis=2);mask=diff>12;yy,xx=np.where(mask)
manifest=json.loads((ROOT/'Screenshots/capture_manifest.json').read_text());times={r['name']:r['world_time_seconds'] for r in manifest['captures']}
d={'utc':datetime.now(timezone.utc).isoformat(),'images':rows,'all_1920x1080':all(r['dimensions']==[1920,1080] for r in rows),
   'all_nonblank':all(min(r['rgb_std'])>10 for r in rows),'motion':{'changed_pixels_threshold12':int(mask.sum()),'difference_bbox_xyxy':[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())] if len(xx) else None,
   'world_time_t0':times['windmill_motion_t0'],'world_time_t1':times['windmill_motion_t1'],'delta_seconds':times['windmill_motion_t1']-times['windmill_motion_t0'],
   'interpretation':'Pixel changes in same-camera actual renders support visible material-driven sail motion. No mechanical physics or torque simulation.'}}
(ROOT/'render_analysis.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
