"""Read actual UE PNGs without editing, recoloring or compositing them."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib,datetime
root=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement');folder=root/'Screenshots/After'
report={'analyzed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':[],'pairs':[],'camera_comparison':[]}
for p in sorted(folder.glob('*.png')):
 im=Image.open(p);a=np.asarray(im.convert('RGB'));report['files'].append({'name':p.name,'size':list(im.size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rgb_mean':a.mean((0,1)).tolist(),'rgb_std':a.std((0,1)).tolist()})
for a,b,label in [('tree_rim_off','tree_rim_on','rim toggle, wind strength zero'),('tree_rim_on','tree_gradient_shifted','gradient guide +450 cm, wind strength zero'),('tree_wind_t0','tree_wind_t1','same camera and parameters, time advanced'),('water_t0','water_t1','same water camera, time advanced')]:
 x=np.asarray(Image.open(folder/(a+'.png')).convert('RGB')).astype(np.float32);y=np.asarray(Image.open(folder/(b+'.png')).convert('RGB')).astype(np.float32);delta=np.abs(x-y);crop=delta[100:850,480:1440]
 report['pairs'].append({'a':a,'b':b,'test':label,'mean_absolute_rgb_difference_0_255':float(delta.mean()),'changed_pixels_over_2':int((delta.max(2)>2).sum()),'central_canopy_roi':[480,100,1440,850],'roi_mean_absolute_difference':float(crop.mean()),'roi_changed_pixels_over_2':int((crop.max(2)>2).sum())})
before=json.loads((root/'Screenshots/Before/capture_manifest.json').read_text());after=json.loads((folder/'capture_manifest.json').read_text())
for v in before['views']:
 w=next(x for x in after['views'] if x['name']==v['name']);keys=['location','target','rotation','projection','ortho_width_cm','horizontal_fov'];same=all(v.get(k)==w.get(k) for k in keys)
 report['camera_comparison'].append({'view':v['name'],'identical_camera':same})
report['time_samples']={v['name']:v.get('shader_world_time_seconds') for v in after['views']}
debug=np.asarray(Image.open(folder/'tree_rim_debug.png').convert('RGB')).astype(np.float32)
mask=(debug.max(2)-debug.min(2)<2)&(debug.max(2)<180)
report['canopy_mask_pixels']=int(mask.sum());report['canopy_mask_method']='Achromatic dark/grey pixels from actual canopy rim debug render, excluding colored terrain, water and pines.'
for pair in report['pairs'][:3]:
 x=np.asarray(Image.open(folder/(pair['a']+'.png')).convert('RGB')).astype(np.float32);y=np.asarray(Image.open(folder/(pair['b']+'.png')).convert('RGB')).astype(np.float32);d=np.abs(x-y)[mask]
 pair['canopy_mask_mean_absolute_difference']=float(d.mean());pair['canopy_mask_changed_pixels_over_2']=int((d.max(1)>2).sum())
report['success']=len(report['files'])==14 and all(v['size']==[1920,1080] for v in report['files']) and all(v['identical_camera'] for v in report['camera_comparison']) and all(p['roi_changed_pixels_over_2']>50 for p in report['pairs'][:3])
(root/'render_analysis.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))
