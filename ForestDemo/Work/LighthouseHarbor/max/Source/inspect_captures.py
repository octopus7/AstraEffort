"""Read-only checks on actual UE screenshot pixels; never modifies the images."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
from datetime import datetime
ROOT=Path('D:/github/AstraEffort/ForestDemo/Work/LighthouseHarbor/max');D=ROOT/'Screenshots'
manifest=json.loads((D/'capture_manifest.json').read_text());report=[];arrays={}
for name in ['overview','top_down','lighthouse','harbor','motion_t0','motion_t1']:
    p=D/(name+'.png');img=bpy.data.images.load(str(p),check_existing=False)
    assert list(img.size)==[1920,1080],(name,list(img.size))
    pix=np.array(img.pixels[:],dtype=np.float32).reshape((1080,1920,4));arrays[name]=pix[:,:,:3]
    report.append({'file':p.name,'dimensions':list(img.size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
      'min_rgb':float(pix[:,:,:3].min()),'max_rgb':float(pix[:,:,:3].max()),'mean_rgb':[float(v) for v in pix[:,:,:3].mean(axis=(0,1))],
      'black_pixel_fraction':float(np.all(pix[:,:,:3]<.001,axis=2).mean())})
a,b=manifest['captures'][-2:]
for key in ['location_cm','rotation_deg','projection','ortho_width_cm','aspect_ratio','screen_percentage','quality']:
    assert a[key]==b[key],f'Timed cameras differ: {key}'
delta=np.abs(arrays['motion_t1']-arrays['motion_t0']);fraction=float(np.any(delta>.005,axis=2).mean())
assert fraction>0.00001,'Timed rendered pixels are identical'
top_delta=delta[::-1]
water_region=top_delta[780:930,80:350]
water_fraction=float(np.any(water_region>.0005,axis=2).mean())
assert water_fraction>0,'Water-only region shows no timed pixel change'
out={'pass':True,'images':report,'same_camera_motion_pair':True,'motion_changed_pixel_fraction_at_0_005_linear':fraction,
     'motion_mean_absolute_rgb_delta_linear':float(delta.mean()),'motion_max_rgb_delta_linear':float(delta.max()),
     'requested_timestamp_delta_seconds':(datetime.fromisoformat(b['requested_at_utc'])-datetime.fromisoformat(a['requested_at_utc'])).total_seconds(),
     'water_roi_top_left_pixels':[80,780,350,930],'water_roi_changed_fraction_at_0_0005_linear':water_fraction,
     'water_roi_mean_absolute_rgb_delta_linear':float(water_region.mean()),
     'note':'Pixel change includes temporal renderer sampling; material graph Time connections are separately preserved. This does not claim physical simulation or PIE testing.'}
(ROOT/'Validation'/'capture_pixels.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print('CAPTURE_PIXELS_PASS',len(report),'images; timed fraction',fraction)
