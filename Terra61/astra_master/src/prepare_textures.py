"""Technical slicing of image-generated atlases and approximate PBR-map derivation."""
from pathlib import Path
import json, shutil
import numpy as np
from PIL import Image, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT.parent/'generated_images'
OUT=ROOT/'textures'
OUT.mkdir(exist_ok=True)
surfaces=SRC/'exec-c9e9974f-871b-4399-8500-b0901942ef6c.png'
detail=SRC/'exec-e38af978-1973-4017-b89e-5d545438656e.png'
if surfaces.exists():shutil.copy2(surfaces,OUT/'station_surfaces_source.png')
else:surfaces=OUT/'station_surfaces_source.png'
if detail.exists():shutil.copy2(detail,OUT/'facade_details_source.png')
else:detail=OUT/'facade_details_source.png'
locoref=SRC/'exec-c140e5b3-7510-41c6-a7c3-e6bbec86e894.png'
if locoref.exists():shutil.copy2(locoref,ROOT/'references/06_locomotive_reference.png')

info={}
def maps(name,im,metallic=0.0,rough=.78,strength=.65):
    im=im.convert('RGB')
    im.save(OUT/f'{name}_basecolor.png')
    h=np.asarray(im.convert('L').filter(ImageFilter.GaussianBlur(.6)),dtype=float)/255
    gy,gx=np.gradient(h)
    n=np.stack((-gx*strength,-gy*strength,np.ones_like(h)),axis=-1)
    n/=np.linalg.norm(n,axis=-1,keepdims=True)
    Image.fromarray(np.uint8(np.clip((n*.5+.5)*255,0,255))).save(OUT/f'{name}_normal.png')
    rr=np.clip(rough+(h-h.mean())*.12,0,1)
    orm=np.stack([np.ones_like(h),rr,np.ones_like(h)*metallic],axis=-1)
    Image.fromarray(np.uint8(orm*255)).save(OUT/f'{name}_orm.png')
    Image.fromarray(np.uint8(rr*255)).save(OUT/f'{name}_roughness.png')
    info[name]={'basecolor':f'{name}_basecolor.png','normal':f'{name}_normal.png','orm':f'{name}_orm.png','size':list(im.size),'normal_source':'approximate luminance gradient; not a measured scan','orm_channels':'R=1 occlusion neutral, G=roughness, B=metallic'}

im=Image.open(surfaces).convert('RGB');w,h=im.size
names=['brick','stone','iron','slate','wood','ballast','paving','retaining_brick','rail']
for i,name in enumerate(names):
    c,r=i%3,i//3
    tile=im.crop((round(w*c/3)+2,round(h*r/3)+2,round(w*(c+1)/3)-2,round(h*(r+1)/3)-2))
    maps(name,tile,.72 if name in ('iron','slate','rail') else 0,.48 if name in ('iron','slate','rail') else .84,.85)

d=Image.open(detail).convert('RGB');w,h=d.size
regions={'window':(0,0,.5,.52),'clock':(.5,0,1,.52),'ornament':(0,.52,.5,1),'sign':(.5,.66,1,.81)}
for name,rect in regions.items():
    tile=d.crop(tuple(round(v*(w if i%2==0 else h)) for i,v in enumerate(rect)))
    maps(name,tile,.45 if name in ('ornament','sign') else .05,.58,.15)
info['notes']='Generated source atlases are included. Crops preserve their painted detail. Tile borders are not guaranteed perfectly periodic. UV reuse is deliberate on repeated structures; detailed hero panels use dedicated maps.'
vehicle=SRC/'exec-435db299-b98f-47fc-8f1d-7512ca56b30f.png'
if not vehicle.exists():vehicle=OUT/'rolling_stock_source.png'
if vehicle.exists():
    if vehicle.resolve()!=(OUT/'rolling_stock_source.png').resolve():shutil.copy2(vehicle,OUT/'rolling_stock_source.png')
    v=Image.open(vehicle).convert('RGB');w,h=v.size
    for i,name in enumerate(['boiler','wheel','cab','carriage_window','carriage_wood','brass']):
        c,r=i%3,i//3
        # Generated row seam is at 48 percent height.
        ys=[0,round(h*.48),h]
        tile=v.crop((round(w*c/3)+2,ys[r]+2,round(w*(c+1)/3)-2,ys[r+1]-2))
        maps(name,tile,.75 if name in ('boiler','wheel','cab','brass') else .1,.43 if name=='brass' else .65,.3)
(OUT/'materials_manifest.json').write_text(json.dumps(info,indent=2))
print(json.dumps({'textures':len(info)-1,'out':str(OUT)},indent=2))
