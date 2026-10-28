#!/usr/bin/env python3
"""Generate low-poly luggage cart, crate and barrel GLBs.

All geometry is authored X across, Y rearward and Z up; ground is Z=0 and
front is Y=0. Shared infrastructure/locomotive helpers provide GLB export and
flat-shaded geometry. Trunk textures are tightly cropped from the generated
luggage reference; small normal and ORM maps are approximate image derivatives.
"""
from __future__ import annotations
import argparse
import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from scipy.ndimage import gaussian_filter
import build_infrastructure as glb
from build_locomotive import Part, cylinder_x, rod

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'modules'/'freight_props'
SRC=ROOT/'textures'
REFERENCE=ROOT/'references'/'11_luggage_cart_reference.png'
CROPS={'case_tan':(1194,68,1368,124),'case_brown':(1152,130,1405,209),
       'case_blue':(1134,216,1429,284)}

glb.MATERIALS.update({
 'freight_wood':{'image':'wood','uv_m':(.80,.65),'roughness':.90,'metallic':0},
 'freight_iron':{'image':'iron','uv_m':(.70,.70),'roughness':.68,'metallic':.75},
 'case_tan':{'image':'case_tan','uv_m':(1,1),'roughness':.86,'metallic':0},
 'case_brown':{'image':'case_brown','uv_m':(1,1),'roughness':.86,'metallic':0},
 'case_blue':{'image':'case_blue','uv_m':(1,1),'roughness':.86,'metallic':0},
})
for _case in CROPS:
    glb.MATERIALS[_case+'_top']={'image':_case+'_top','uv_m':(1,1),'roughness':.86,'metallic':0}


def prepare_textures(destination, source_dir, reference):
    destination.mkdir(parents=True,exist_ok=True)
    for mat in ('wood','iron','brass'):
        for channel in ('basecolor','normal','orm'):
            shutil.copyfile(source_dir/f'{mat}_{channel}.png',destination/f'{mat}_{channel}.png')
    def save_maps(name, image):
        image.save(destination/f'{name}_basecolor.png')
        rgb=np.asarray(image,dtype=np.float32)/255
        lum=gaussian_filter(rgb @ np.array([.2126,.7152,.0722],dtype=np.float32),sigma=.8)
        dy,dx=np.gradient(lum)
        normal=np.dstack([-dx*.7,-dy*.7,np.ones_like(lum)])
        normal/=np.linalg.norm(normal,axis=2,keepdims=True)
        normal=np.clip((normal*.5+.5)*255,0,255).astype(np.uint8)
        Image.fromarray(normal,'RGB').save(destination/f'{name}_normal.png')
        rough=np.clip(.82+(.5-lum)*.15,.65,1)*255
        orm=np.dstack([np.full_like(lum,255),rough,np.zeros_like(lum)]).astype(np.uint8)
        Image.fromarray(orm,'RGB').save(destination/f'{name}_orm.png')
    with Image.open(reference) as ref:
        for name,rect in CROPS.items():
            crop=ref.convert('RGB').crop(rect)
            save_maps(name,crop)
            # Construct a separate top chart from actual leather and strap
            # details in the crop. It avoids stretching a few source rows
            # across the whole lid or painting the side latches on the lid.
            w,h=crop.size
            chip=crop.crop((int(w*.30),int(h*.63),int(w*.40),int(h*.96))).resize((64,64),Image.Resampling.LANCZOS)
            top=Image.new('RGB',(512,256))
            for row in range(4):
                for col in range(8):
                    tile=ImageOps.mirror(chip) if col%2 else chip
                    if row%2: tile=ImageOps.flip(tile)
                    top.paste(tile,(col*64,row*64))
            centers=(.25,.76) if name=='case_blue' else (.20,.76)
            for center in centers:
                strap=crop.crop((int(w*(center-.035)),int(h*.63),int(w*(center+.035)),int(h*.98)))
                strap=strap.resize((36,256),Image.Resampling.LANCZOS)
                top.paste(strap,(round(center*512)-18,0))
            save_maps(name+'_top',top)


def box(part,mat,b): glb.box(part,mat,b)


def tube_between(part,material,a,b,radius,n=10):
    """Simple circular rod between arbitrary 3D endpoints."""
    a=np.asarray(a,dtype=float); b=np.asarray(b,dtype=float); axis=b-a
    axis/=np.linalg.norm(axis)
    ref=np.array([0.,0.,1.]) if abs(axis[2])<.9 else np.array([1.,0.,0.])
    u=np.cross(ref,axis); u/=np.linalg.norm(u); v=np.cross(axis,u)
    for i in range(n):
        t0=2*math.pi*i/n; t1=2*math.pi*(i+1)/n
        q0=radius*(u*math.cos(t0)+v*math.sin(t0)); q1=radius*(u*math.cos(t1)+v*math.sin(t1))
        uv0=(.5+.5*math.cos(t0),.5+.5*math.sin(t0)); uv1=(.5+.5*math.cos(t1),.5+.5*math.sin(t1))
        part.chart(material,[a+q0,a+q1,b+q1,b+q0],[(i/n,0),((i+1)/n,0),((i+1)/n,1),(i/n,1)])
        part.chart(material,[a,a+q1,a+q0],[(.5,.5),uv1,uv0])
        part.chart(material,[b,b+q0,b+q1],[(.5,.5),uv0,uv1])


def wheel(name,x,y,z=.18,r=.18,n=12):
    p=Part(name); x0=x-.04; x1=x+.04; inner=.118
    def yz(rad,t): return (y+rad*math.cos(t),z+rad*math.sin(t))
    for i in range(n):
        a=2*math.pi*i/n; b=2*math.pi*(i+1)/n
        oa=yz(r,a); ob=yz(r,b); ia=yz(inner,a); ib=yz(inner,b)
        p.chart('freight_iron',[(x1,*oa),(x0,*oa),(x0,*ob),(x1,*ob)],[(0,i/n),(1,i/n),(1,(i+1)/n),(0,(i+1)/n)])
        p.chart('freight_iron',[(x0,*ia),(x1,*ia),(x1,*ib),(x0,*ib)],[(0,i/n),(1,i/n),(1,(i+1)/n),(0,(i+1)/n)])
        def u(q): return ((q[0]-y)/.36+.5,(q[1]-z)/.36+.5)
        p.chart('freight_iron',[(x1,*ia),(x1,*oa),(x1,*ob),(x1,*ib)],[u(ia),u(oa),u(ob),u(ib)])
        p.chart('freight_iron',[(x0,*ib),(x0,*ob),(x0,*oa),(x0,*ia)],[u(ib),u(ob),u(oa),u(ia)])
    for k in range(5):
        angle=2*math.pi*k/5
        rod(p,'freight_iron',x0+.012,x1-.012,y,z,y+.14*math.cos(angle),z+.14*math.sin(angle),.021)
    cylinder_x(p,'brass',x0-.006,x1+.006,y,z,.037,n=8)
    return p


def trunk(name,mat,x0,x1,y0,y1,z0,z1):
    p=Part(name)
    # Full crop only on the two long side faces, with readable, undistorted hardware.
    for x,side in ((x1,'right'),(x0,'left')):
        pts=[(x,y0,z0),(x,y1,z0),(x,y1,z1),(x,y0,z1)] if side=='right' else \
            [(x,y1,z0),(x,y0,z0),(x,y0,z1),(x,y1,z1)]
        def uv(y,z): return ((y-y0)/(y1-y0) if side=='right' else (y1-y)/(y1-y0), (z1-z)/(z1-z0))
        p.chart(mat,pts,[uv(y,z) for _,y,z in pts])
    # On end faces use a narrower strip of that case's image, so a full wide
    # front with multiple latches is not squashed onto the short end.
    for y,side in ((y0,'front'),(y1,'back')):
        pts=[(x0,y,z0),(x1,y,z0),(x1,y,z1),(x0,y,z1)] if side=='front' else \
            [(x1,y,z0),(x0,y,z0),(x0,y,z1),(x1,y,z1)]
        p.chart(mat,pts,[(.04+.24*(x-x0)/(x1-x0),(z1-z)/(z1-z0)) for x,_,z in pts])
    # A dedicated leather-and-straps chart avoids placing side latches on top.
    for z,order in ((z1,((x0,y0),(x1,y0),(x1,y1),(x0,y1))),
                    (z0,((x0,y1),(x1,y1),(x1,y0),(x0,y0)))):
        pts=[(x,y,z) for x,y in order]
        p.chart(mat+'_top',pts,[((y-y0)/(y1-y0),(x-x0)/(x1-x0)) for x,y,_ in pts])
    return p


def cart():
    parts=[]
    p=Part('cart_wooden_platform'); box(p,'freight_wood',[(-.6,0,.35),(.6,2,.44)]); parts.append(p)
    p=Part('cart_wooden_end_rails')
    for y0 in (.09,1.81):
        for x0 in (-.57,.50): box(p,'freight_wood',[(x0,y0,.44),(x0+.07,y0+.10,.90)])
        box(p,'freight_wood',[(-.57,y0,.72),(.57,y0+.10,.79)])
    parts.append(p)
    p=Part('cart_handle')
    for sign in (-1,1):
        tube_between(p,'freight_iron',(sign*.53,.05,.44),(sign*.53,.05,1.42),.025)
        tube_between(p,'freight_iron',(sign*.53,.05,1.42),(sign*.45,.05,1.475),.025)
    # Twelve radial segments include a vertex at the exact top of the handle.
    tube_between(p,'freight_iron',(-.45,.05,1.475),(.45,.05,1.475),.025,n=12)
    parts.append(p)
    p=Part('cart_axles')
    for y in (.35,1.65): tube_between(p,'freight_iron',(-.52,y,.18),(.52,y,.18),.018,n=8)
    parts.append(p)
    for row,y in enumerate((.35,1.65),1):
        for side,x in (('L',-.52),('R',.52)):
            parts.append(wheel(f'cart_wheel_{side}_{row}',x,y))
    parts.append(trunk('trunk_blue','case_blue',-.44,.44,.30,1.70,.44,.75))
    parts.append(trunk('trunk_brown','case_brown',-.40,.40,.45,1.55,.75,1.04))
    parts.append(trunk('trunk_tan','case_tan',-.31,.31,.60,1.40,1.04,1.28))
    return parts


def crate():
    p=Part('wooden_crate'); box(p,'freight_wood',[(-.4,0,0),(.4,.8,.8)])
    return [p]


def barrel():
    p=Part('barrel_wood_staves'); n=12; cy=.325
    profile=[(0,.25),(.08,.28),(.22,.31),(.45,.325),(.68,.31),(.82,.28),(.9,.25)]
    for (z0,r0),(z1,r1) in zip(profile,profile[1:]):
        for i in range(n):
            a=2*math.pi*i/n; b=2*math.pi*(i+1)/n
            def point(r,t,z): return (r*math.cos(t),cy+r*math.sin(t),z)
            pts=[point(r0,a,z0),point(r0,b,z0),point(r1,b,z1),point(r1,a,z1)]
            # Rotating U/V makes the source image plank seams vertical staves.
            p.chart('freight_wood',pts,[(z0/.9,i/n),(z0/.9,(i+1)/n),
                                        (z1/.9,(i+1)/n),(z1/.9,i/n)])
    for z,r in (profile[0],profile[-1]):
        for i in range(n):
            a=2*math.pi*i/n; b=2*math.pi*(i+1)/n
            pa=(r*math.cos(a),cy+r*math.sin(a),z); pb=(r*math.cos(b),cy+r*math.sin(b),z)
            uv0=(.5+.5*math.cos(a),.5+.5*math.sin(a)); uv1=(.5+.5*math.cos(b),.5+.5*math.sin(b))
            if z==0: p.chart('freight_wood',[(0,cy,z),pb,pa],[(.5,.5),uv1,uv0])
            else: p.chart('freight_wood',[(0,cy,z),pa,pb],[(.5,.5),uv0,uv1])
    hoop=Part('barrel_iron_hoops')
    def radius_at(z):
        for (z0,r0),(z1,r1) in zip(profile,profile[1:]):
            if z0<=z<=z1: return r0+(r1-r0)*(z-z0)/(z1-z0)
        raise ValueError(z)
    for z0,z1 in ((.13,.18),(.72,.77)):
        r0,r1=radius_at(z0)+.003,radius_at(z1)+.003
        for i in range(n):
            a=2*math.pi*i/n; b=2*math.pi*(i+1)/n
            def point(r,t,z): return (r*math.cos(t),cy+r*math.sin(t),z)
            pts=[point(r0,a,z0),point(r0,b,z0),point(r1,b,z1),point(r1,a,z1)]
            hoop.chart('freight_iron',pts,[(z0/.9,i/n),(z0/.9,(i+1)/n),
                                           (z1/.9,(i+1)/n),(z1/.9,i/n)])
    return [p,hoop]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--textures',type=Path,default=SRC); parser.add_argument('--reference',type=Path,default=REFERENCE)
    parser.add_argument('--out',type=Path,default=OUT)
    args=parser.parse_args()
    tex=args.out/'textures'; prepare_textures(tex,args.textures,args.reference)
    entries={name:glb.export(name,fn(),tex,args.out) for name,fn in
             (('luggage_cart',cart),('crate',crate),('barrel',barrel))}
    for name in CROPS:
        entries['luggage_cart']['texture_repeat_m'].pop(name,None)
        entries['luggage_cart']['texture_repeat_m'].pop(name+'_top',None)
    entries['luggage_cart']['explicit_uv_charts']='Individual case face crops and custom top charts made from leather/strap details in those crops.'
    manifest={'description':'Victorian luggage cart with three trunks, wooden crate and barrel.',
              'author_axes':'X right, Y rearward, Z up; front Y=0 and ground Z=0',
              'export_axes':'glTF Y-up with one -90 degree X root rotation',
              'reference_image':'../../references/11_luggage_cart_reference.png',
              'trunk_source_crops_pixels':{k:list(v) for k,v in CROPS.items()},
              'materials_note':'Individual reference crops map luggage side panels; approximate normal/ORM maps are generated from their colour. Wood, iron, and brass use shared generated surface maps.',
              'modules':entries}
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__': main()
