from pathlib import Path
from datetime import datetime,timezone
import numpy as np,json,hashlib,sys
from PIL import Image
PASS=Path(__file__).resolve().parent;ROOT=PASS.parent;OUT=PASS/'Art/Textures';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(PASS))
from landscape_design import PATHS,FIELDS
from design import CORN,CORN_PATH
N=1024;x,y=np.meshgrid(np.arange(N)/N,np.arange(N)/N)
palette={'CornLeaf':(98,126,57),'CornStalk':(115,137,66),'CornKernel':(210,166,52),'CornTassel':(178,153,87),
         'MeadowLeaf':(104,122,68),'MeadowStem':(126,137,84),'MeadowSeed':(187,169,115)}
rows=[]
for index,(slot,col) in enumerate(palette.items()):
    grain=2.2*np.sin(2*np.pi*(x*71+np.sin(y*2*np.pi)*.1))+1.1*np.cos(2*np.pi*(x*9+y*7))
    variation=3*np.sin(2*np.pi*(x*3+y*2))+2*np.cos(2*np.pi*(x*7-y*5))
    if slot=='CornKernel':grain+=5*np.cos(2*np.pi*x*23)*np.cos(2*np.pi*y*29)
    rgb=np.stack([c+grain+variation for c in col],-1)
    p=OUT/('T_'+slot+'_BaseColor.png');Image.fromarray(np.uint8(np.clip(rgb,0,255))).save(p)
    rows.append({'slot':slot,'path':str(p),'resolution':[N,N],'srgb':True,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
# Preserve existing atlas exactly outside the new corn soil bed and short entrance.
original=ROOT/'Art/Landscape/T_Ground_BaseColor.png';a=np.asarray(Image.open(original).convert('RGB'),dtype=float)
n=a.shape[0];xx,yy=np.meshgrid(np.linspace(-50,50,n),np.linspace(50,-50,n))
cx,cy=CORN['center'];sx,sy=CORN['size'];edge=np.maximum(abs(xx-cx)-sx/2,abs(yy-cy)-sy/2)
mask=np.clip(.5-edge/.4,0,1);ridges=np.cos(2*np.pi*(xx-cx)/CORN['row_spacing'])*4
grain=np.sin(xx*17+yy*9)+np.sin(xx*27-yy*19)
soil=np.stack([111+ridges+grain,91+ridges*.7+grain,60+ridges*.5+grain],-1)
a=a*(1-mask[:,:,None])+soil*mask[:,:,None]
for points,width in CORN_PATH:
    p,q=points;vx,vy=q[0]-p[0],q[1]-p[1]
    t=np.clip(((xx-p[0])*vx+(yy-p[1])*vy)/(vx*vx+vy*vy),0,1)
    d=np.hypot(xx-p[0]-t*vx,yy-p[1]-t*vy)-width
    m=np.clip(.5-d/.7,0,1);dirt=np.stack([143+grain,120+grain,86+grain],-1)
    a=a*(1-m[:,:,None])+dirt*m[:,:,None]
p=OUT/'T_Ground_BaseColor.png';Image.fromarray(np.uint8(np.clip(a,0,255))).save(p)
rows.append({'slot':'Ground','path':str(p),'resolution':[n,n],'source_base':str(original),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'manifest.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'source':'Original deterministic numpy procedural colors; no external images or imagegen','textures':rows,'corn_field':CORN,'corn_entrance':CORN_PATH},indent=2))
print('Created',len(rows),'original vegetation/ground textures')
