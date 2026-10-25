import json,math
from pathlib import Path
import numpy as np
from PIL import Image
from landscape_design import PATHS,FIELDS
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'Art/Landscape';OUT.mkdir(parents=True,exist_ok=True)
N=2048
x,y=np.meshgrid(np.linspace(-50,50,N),np.linspace(50,-50,N))
rng=np.random.default_rng(2237)
# Continuous multi-scale variation perturbs the actual path boundary, not just its color.
noise=np.sin(x*1.17+y*.73)*.18+np.sin(x*3.9-y*2.2)*.065+np.cos(y*7.1+x*4.3)*.035
d=np.full((N,N),100.)
for points,w in PATHS:
    for a,b in zip(points,points[1:]):
        vx,vy=b[0]-a[0],b[1]-a[1];t=np.clip(((x-a[0])*vx+(y-a[1])*vy)/(vx*vx+vy*vy),0,1)
        d=np.minimum(d,np.hypot(x-a[0]-t*vx,y-a[1]-t*vy)-w)
d=np.minimum(d,(np.sqrt((x/12)**2+((y-1)/9)**2)-1)*8)
d+=noise
path=np.clip(.5-d/.9,0,1)
macro=(np.sin(x*.19+y*.05)+np.sin(y*.34-x*.12))*.5
fine=rng.normal(0,1,(N,N));grain=np.sin(x*17+y*9)*.8+fine*1.8
grass=np.stack([107+macro*5+grain,123+macro*6+grain,77+macro*3+grain],-1)
earth=np.stack([143+grain*1.1,120+grain,86+grain*.8],-1)
rgb=grass*(1-path[:,:,None])+earth*path[:,:,None]
for f in FIELDS:
    cx,cy=f['center'];sx,sy=f['size']
    edge=np.maximum(np.abs(x-cx)-sx/2,np.abs(y-cy)-sy/2)+noise*.4
    mask=np.clip(.5-edge/.5,0,1)
    ridges=(np.sin((x-cx)*math.tau/.75)*3.5)
    col=np.stack([112+ridges+grain,91+ridges*.8+grain,60+ridges*.5+grain],-1)
    rgb=rgb*(1-mask[:,:,None])+col*mask[:,:,None]
Image.fromarray(np.uint8(np.clip(rgb,0,255))).save(OUT/'T_Ground_BaseColor.png')
# Neutral small-scale detail is combined multiplicatively in Unreal with the macro map.
n=512;xx,yy=np.meshgrid(np.arange(n)/n,np.arange(n)/n)
detail=128+np.sin(xx*math.tau*21+np.sin(yy*math.tau*7))*7+np.sin(yy*math.tau*29+xx*math.tau*13)*5
Image.fromarray(np.uint8(detail)).save(OUT/'T_Ground_Detail.png')
(OUT/'ground_texture_manifest.json').write_text(json.dumps({'resolution':[N,N],'coverage_m':[100,100],'macro_density_px_m':N/100,'detail_texture_px':512,'detail_repeat_per100m':100,'detail_density_px_m':512,'source':'original deterministic numpy painting','paths':PATHS,'fields':FIELDS,'transition_width_m':.9,'edge_perturbation':'three continuous sine frequencies, amplitude0.28m','colorspace':'sRGB albedo; linear grayscale detail'},indent=2))
print('GROUND_TEXTURE_COMPLETE')
