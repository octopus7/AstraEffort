import bpy,json,hashlib,struct
import numpy as np
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/DesertVillage/max');S=ROOT/'Screenshots'
manifest=json.loads((S/'capture_manifest.json').read_text());records=[]
for c in manifest['captures']:
    p=S/c['file'];data=p.read_bytes();w,h=struct.unpack('>II',data[16:24]);records.append({'file':p.name,'dimensions':[w,h],'sha256':hashlib.sha256(data).hexdigest(),'actual_view_mode':c['actual_view_mode'],'game_view':c['game_view_confirmed'],'camera':c['piloted_actor'],'size_bytes':len(data)})
def pixels(name):
    im=bpy.data.images.load(str(S/name),check_existing=False);a=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(a);a=a.reshape(im.size[1],im.size[0],4)[::-1,:,:3];return a
a=pixels('water_t0.png');b=pixels('water_later.png');delta=np.abs(a-b)
def roi(x0,y0,x1,y1):
    d=delta[y0:y1,x0:x1];return {'rectangle_xyxy':[x0,y0,x1,y1],'mean_absolute_normalized_rgb_difference':float(d.mean()),'max_absolute_normalized_rgb_difference':float(d.max()),'fraction_pixels_changed_above_0_001':float((d.max(axis=2)>.001).mean())}
c0=next(x for x in manifest['captures'] if x['file']=='water_t0.png');c1=next(x for x in manifest['captures'] if x['file']=='water_later.png')
same=all(c0[k]==c1[k] for k in ['location_cm','rotation_degrees','projection','fov_degrees'])
result={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'screenshots':records,'camera_match_for_timed_pair':same,'request_time_delta_seconds':(datetime.fromisoformat(c1['requested_at_utc'])-datetime.fromisoformat(c0['requested_at_utc'])).total_seconds(),'water_region':roi(850,720,1150,950),'static_wall_control':roi(760,60,1000,120),'measurement':'Blender PNG decoder; normalized decoded RGB pixels, no image edits. Water rectangle chosen within visible water; static facade control measures residual rendering noise.','motion_evidence_limit':'Actual same-camera timed pair, with configured material panning. Pixel differences also contain temporal rendering noise and do not isolate physical or shader motion. No fluid/refraction/PIE validation is claimed.','visually_reviewed_files':[x['file'] for x in records],'visual_review':'Author opened all final PNGs: Lit overview/topdown, no UI/grid/selection, readable plaza, calm water and clean palms; parent independently accepted four common views.'}
result['passed']=len(records)==7 and all(x['dimensions']==[1920,1080] and 'VMI_LIT' in x['actual_view_mode'] and x['game_view'] for x in records) and same and result['water_region']['mean_absolute_normalized_rgb_difference']>0
(ROOT/'Validation/capture_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ['screenshots','visually_reviewed_files']}))
