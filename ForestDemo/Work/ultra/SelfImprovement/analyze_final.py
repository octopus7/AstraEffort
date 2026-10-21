from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib,datetime
out=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement');folder=out/'Screenshots/Final'
report={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':[],'same_camera_checks':[],'initial_after_evidence_unchanged':True}
before=json.loads((out/'Screenshots/Before/capture_manifest.json').read_text());final=json.loads((folder/'capture_manifest.json').read_text())
for v in final['views']:
 b=next(x for x in before['views'] if x['name']==v['name']);keys=['location','target','rotation','projection','ortho_width_cm','horizontal_fov'];report['same_camera_checks'].append({'name':v['name'],'passed':all(b.get(k)==v.get(k) for k in keys)})
for p in sorted(folder.glob('*.png')):
 im=Image.open(p);report['files'].append({'name':p.name,'size':list(im.size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
for r in json.loads((out/'initial_after_evidence_hashes.json').read_text())['files']:
 if hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()!=r['sha256']:report['initial_after_evidence_unchanged']=False
debug=np.asarray(Image.open(out/'Screenshots/After/tree_rim_debug.png').convert('RGB')).astype(np.float32);mask=(debug.max(2)-debug.min(2)<2)&(debug.max(2)<180)
def stats(path):
 im=Image.open(path).convert('RGB');rgb=np.asarray(im).astype(np.float32)/255;hsv=np.asarray(im.convert('HSV')).astype(np.float32)/255;y=rgb@np.array([.2126,.7152,.0722]);return {'mean_saturation':float(hsv[:,:,1][mask].mean()),'mean_value':float(hsv[:,:,2][mask].mean()),'luma_p10':float(np.percentile(y[mask],10)),'luma_p90':float(np.percentile(y[mask],90)),'luma_p90_minus_p10':float(np.percentile(y[mask],90)-np.percentile(y[mask],10))}
report['canopy_mask_pixels']=int(mask.sum());report['source_default_palette']=stats(out/'Screenshots/After/tree_detail.png');report['final_palette']=stats(folder/'tree_detail.png');report['method_note']='Same camera, canopy mask taken from actual initial rim debug image. Wind time differs; these are supporting image statistics, not perceptual guarantees.'
report['success']=len(report['files'])==5 and all(r['size']==[1920,1080] for r in report['files']) and all(r['passed'] for r in report['same_camera_checks']) and report['initial_after_evidence_unchanged']
(out/'final_render_analysis.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
