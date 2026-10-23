"""Read actual PNG pixels only; never generates or modifies image evidence."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
PASS=Path(r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max/TextureImprovement');BASE=PASS.parent;S=PASS/'Screenshots'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pixels(path):
 im=bpy.data.images.load(str(path));w,h=im.size;a=np.empty(w*h*4,dtype=np.float32);im.pixels.foreach_get(a);bpy.data.images.remove(im)
 return np.flipud(a.reshape(h,w,4))[:,:,:3]
m=read(S/'capture_manifest.json');rows={r['name']:r for r in m['captures']};assert len(rows)==8
base={r['name']:r for r in read(BASE/'Screenshots/capture_manifest.json')['captures']}
before={r['name']:r for r in read(S/'BeforeDetails/capture_manifest.json')['captures']}
checks=[]
for name,rec in rows.items():
 p=S/rec['file'];d=p.read_bytes();assert sha(p)==rec['sha256'];assert [int.from_bytes(d[16:20],'big'),int.from_bytes(d[20:24],'big')]==[1920,1080]
 old=(base if name in base else before)[name]
 for key in ['location','rotation','target','fov','ortho']:
  if key in old:
   assert key in rec
   assert np.allclose(old[key],rec[key],rtol=0,atol=.0001),(name,key)
 checks.append({'name':name,'sha256':rec['sha256'],'size':[1920,1080],'camera_matches_baseline':True,'baseline_sha256':old['sha256']})
for key in ['location','rotation','target','fov']:assert rows['water_t0'][key]==rows['water_t1'][key]
a=pixels(S/'water_t0.png');b=pixels(S/'water_t1.png');delta=np.abs(a-b)
def stat(box):
 x0,y0,x1,y1=box;d=delta[y0:y1,x0:x1]
 return {'roi_xyxy':box,'mean_abs_png_rgb_0_255':float(d.mean()*255),'max_abs_png_rgb_0_255':float(d.max()*255),'fraction_pixels_delta_gt_1_rgb_value':float((d.max(axis=2)>1/255).mean())}
motion={'clear_water':stat([180,830,600,1030]),'steam_against_ridge':stat([260,30,430,210]),'static_house_control':stat([1060,70,1260,210])}
assert motion['clear_water']['mean_abs_png_rgb_0_255']>motion['static_house_control']['mean_abs_png_rgb_0_255']
assert motion['steam_against_ridge']['mean_abs_png_rgb_0_255']>motion['static_house_control']['mean_abs_png_rgb_0_255']
result={'at_utc':datetime.now(timezone.utc).isoformat(),'captures':checks,'same_camera_timed_pair':True,'time_separation_seconds':rows['water_t1']['monotonic_seconds']-rows['water_t0']['monotonic_seconds'],'motion':motion,'interpretation':'Normalized PNG RGB differences, not verified linear-light values. Separate clear-water and steam ROIs exceed a static house control; material Time nodes provide artistic motion. Minor temporal antialiasing/lighting variance can contribute. No fluid simulation claim.','image_pixels_modified':False}
(PASS/'Validation/capture_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2),flush=True)
