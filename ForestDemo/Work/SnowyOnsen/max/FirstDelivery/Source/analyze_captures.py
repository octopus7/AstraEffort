import bpy,numpy as np,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
r=Path(r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max');s=r/'Screenshots'
m=json.loads((s/'capture_manifest.json').read_text());rows={p['name']:p for p in m['captures']}
assert set(rows)=={'overview','top_down','onsen','village','water_t0','water_t1'}
for name,rec in rows.items():
 data=(s/rec['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==rec['sha256'];assert (int.from_bytes(data[16:20],'big'),int.from_bytes(data[20:24],'big'))==(1920,1080)
def pixels(name):
 im=bpy.data.images.load(str(s/(name+'.png')));w,h=im.size;p=np.empty(w*h*4,dtype=np.float32);im.pixels.foreach_get(p);return np.flipud(p.reshape(h,w,4))[:,:,:3]
a=pixels('water_t0');b=pixels('water_t1');delta=np.abs(a-b)
def stat(x0,y0,x1,y1):
 # Independent PNG decoding reproduced these as normalized PNG channels, not verified linear-light RGB.
 d=delta[y0:y1,x0:x1];return {'roi_xyxy':[x0,y0,x1,y1],'mean_abs_normalized_png_rgb':float(d.mean()),'max_abs_normalized_png_rgb':float(d.max()),'fraction_pixels_delta_gt_0_002':float((d.max(axis=2)>.002).mean())}
for key in ['location','rotation','target','fov']:assert rows['water_t0'][key]==rows['water_t1'][key]
res={'at_utc':datetime.now(timezone.utc).isoformat(),'png_manifest_hash_checks':'6/6 passed','resolution':'1920x1080 all6','same_camera_timed_pair':True,'time_separation_seconds':rows['water_t1']['monotonic_seconds']-rows['water_t0']['monotonic_seconds'],'water_and_steam_roi':stat(700,550,1300,1000),'architecture_control_roi':stat(1060,70,1260,210),'whole_image':stat(0,0,1920,1080),'interpretation':'Difference in water/steam ROI is evidence of rendered time variation; material graph supplies panner/Time source. Minor antialiasing/lighting variance can contribute, so this is not a fluid simulation measurement.'}
assert res['water_and_steam_roi']['fraction_pixels_delta_gt_0_002']>.01
(r/'Validation'/'capture_validation.json').write_text(json.dumps(res,indent=2),encoding='utf8');print(json.dumps(res,indent=2),flush=True)
