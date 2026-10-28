#!/usr/bin/env python3
"""Build a textured, self-contained, Y-up four-axle steam-engine coal tender."""
from pathlib import Path
import json, math
import numpy as np
from PIL import Image,ImageDraw,ImageEnhance,ImageOps
import trimesh
from geometry import Builder,box,cylinder,annulus,beam

OUT=Path(__file__).resolve().parent; TEX=OUT/'textures'; TEX.mkdir(exist_ok=True)
SEED=118744


def make_textures():
    mats=OUT.parent.parent/'materials'
    ai=mats/'ai_aged_cast_iron.png'; baked=TEX/'aged_iron.png'
    if ai.exists():
        original=Image.open(ai).convert('RGB')
        original=ImageEnhance.Brightness(original).enhance(1.28)
        iron=Image.blend(original,Image.new('RGB',original.size,(52,55,57)),.20)
        iron.save(baked,optimize=True)
    else:iron=Image.open(baked).convert('RGB')
    # AI-derived steel with painted pinstripe and small fasteners in UV space.
    side=iron.resize((2048,1024),Image.Resampling.LANCZOS); d=ImageDraw.Draw(side); w,h=side.size
    d.rounded_rectangle((42,45,w-43,h-52),radius=25,outline=(25,23,22),width=12)
    d.rounded_rectangle((55,58,w-56,h-65),radius=16,outline=(113,36,32),width=11)
    d.rounded_rectangle((72,75,w-73,h-82),radius=11,outline=(157,123,88),width=2)
    for x in (125,410,695,980,1265,1550,1835,1920):
        for y in range(115,h-95,36):
            d.ellipse((x-4,y-4,x+4,y+4),fill=(22,23,23));d.ellipse((x-2,y-2,x+1,y+1),fill=(132,125,114))
    for y in (25,h-29):
        for x in range(28,w-25,45):
            d.ellipse((x-3,y-3,x+3,y+3),fill=(16,17,17));d.point((x-1,y-1),fill=(137,129,117))
    side.save(TEX/'riveted_side.png',optimize=True)
    # Coal derives from the AI-generated ballast image: crop, desaturate, and
    # darken the stone facets. This is baked into the model as a base color.
    ai_coal=mats/'ai_railway_ballast.png'; coal_path=TEX/'coal.png'
    if ai_coal.exists():
        src=Image.open(ai_coal).convert('RGB');cx,cy=src.width//2,src.height//2
        gray=ImageOps.grayscale(src.crop((cx-245,cy-495,cx+245,cy+495)))
        gray=ImageEnhance.Contrast(gray).enhance(1.28)
        coal=ImageOps.colorize(gray,black=(5,7,9),white=(137,135,130)).resize((1024,2048),Image.Resampling.LANCZOS)
        coal.save(coal_path,optimize=True)
    elif not coal_path.exists():raise FileNotFoundError('Packaged coal texture or project AI source is required')
    # Procedural weathered red oxide, reserved for the two buffer beams.
    rng=np.random.default_rng(SEED); h=256;w=512
    a=np.empty((h,w,3),np.float32); a[:]=[94,33,28]
    noise=rng.normal(0,8,(h,w))
    for i in range(3):a[:,:,i]=np.clip(a[:,:,i]+noise,0,255)
    red=Image.fromarray(a.astype('uint8'),'RGB');d=ImageDraw.Draw(red)
    for y in (18,45,h-45,h-18):
        for x in range(20,w,30):
            d.ellipse((x-2,y-2,x+2,y+2),fill=(36,24,23));d.point((x-1,y-1),fill=(152,94,72))
    red.save(TEX/'red_oxide.png',optimize=True)
    print('Wrote 4 base-color textures:',TEX,flush=True)


def build():
    mat={
      'iron':trimesh.visual.material.PBRMaterial(name='AI-derived aged cast iron',baseColorTexture=Image.open(TEX/'aged_iron.png'),metallicFactor=.66,roughnessFactor=.69),
      'side':trimesh.visual.material.PBRMaterial(name='AI-derived riveted tender panels',baseColorTexture=Image.open(TEX/'riveted_side.png'),metallicFactor=.65,roughnessFactor=.67),
      'coal':trimesh.visual.material.PBRMaterial(name='AI-derived coal facets',baseColorTexture=Image.open(TEX/'coal.png'),metallicFactor=.1,roughnessFactor=.80),
      'red':trimesh.visual.material.PBRMaterial(name='Procedural worn red oxide paint',baseColorTexture=Image.open(TEX/'red_oxide.png'),metallicFactor=.36,roughnessFactor=.73),
      'black':trimesh.visual.material.PBRMaterial(name='Sooty chassis steel',baseColorFactor=[.115,.12,.12,1],metallicFactor=.6,roughnessFactor=.68),
      'rim':trimesh.visual.material.PBRMaterial(name='Dark worn wheel rims',baseColorFactor=[.25,.24,.22,1],metallicFactor=.82,roughnessFactor=.46),
      'steel':trimesh.visual.material.PBRMaterial(name='Weathered iron fittings',baseColorFactor=[.36,.34,.31,1],metallicFactor=.72,roughnessFactor=.54),
      'brass':trimesh.visual.material.PBRMaterial(name='Aged brass detail',baseColorFactor=[.51,.37,.20,1],metallicFactor=.76,roughnessFactor=.48)
    }
    B={k:Builder() for k in mat}
    # Main enclosed tank plus underframe. Textured side panels sit just beyond
    # the tank faces to prevent z-fighting, with their UVs spanning each side.
    box(B['iron'],-1.22,1.22,1.10,2.85,.52,6.38)
    box(B['black'],-1.26,1.26,.95,1.13,.44,6.46)
    for side in (-1,1):
        x=side*1.222
        if side<0:pts=[(x,1.10,.52),(x,1.10,6.38),(x,2.85,6.38),(x,2.85,.52)]
        else:pts=[(x,1.10,6.38),(x,1.10,.52),(x,2.85,.52),(x,2.85,6.38)]
        B['side'].quad(pts,[((z-.52)/5.86,(y-1.10)/1.75) for x,y,z in pts])
        # Narrow real raised rub rails at top and bottom of the panels.
        cylinder(B['black'],(side*1.245,2.87,.51),(side*1.245,2.87,6.39),.037,8)
        cylinder(B['black'],(side*1.245,1.10,.51),(side*1.245,1.10,6.39),.034,8)
        for z in (.56,6.34):cylinder(B['steel'],(side*1.25,1.12,z),(side*1.25,2.86,z),.025,8)
    # Containment lip on the ends; coal surface projects slightly above them.
    box(B['iron'],-1.20,1.20,2.85,3.02,.52,.62)
    box(B['iron'],-1.20,1.20,2.85,3.02,6.28,6.38)
    # Low-density mound silhouette; detailed small coal rocks are in its UV.
    rng=np.random.default_rng(SEED);nx=8;nz=32
    xs=np.linspace(-1.16,1.16,nx+1); zs=np.linspace(.64,6.26,nz+1)
    points=[]
    for i,x in enumerate(xs):
        row=[]
        for j,z in enumerate(zs):
            wx=math.sin(math.pi*i/nx)**.7; wz=math.sin(math.pi*j/nz)**.32
            peak=.24*wx*wz
            jitter=float(rng.uniform(-.035,.052))
            y=2.88+peak+jitter
            row.append((float(x),float(y),float(z)))
        points.append(row)
    for i in range(nx):
        for j in range(nz):
            p=[points[i][j],points[i][j+1],points[i+1][j+1],points[i+1][j]]
            B['coal'].quad(p,[((x+1.16)/2.32,(z-.64)/5.62) for x,y,z in p])
    # Solid but simple wheel profile, spokes, bearings and two underframe bogies.
    axles=(1.50,2.55,4.45,5.50)
    for z in axles:
        y=.42
        cylinder(B['black'],(-.79,y,z),(.79,y,z),.075,12)
        for side in (-1,1):
            xc=side*.7515; x0=xc-.065;x1=xc+.065
            annulus(B['rim'],(x0,y,z),(x1,y,z),.42,.345,24)
            annulus(B['black'],(x0-.002,y,z),(x1+.002,y,z),.345,.300,24)
            cylinder(B['black'],(x0-.01,y,z),(x1+.01,y,z),.10,12)
            for i in range(8):
                a=math.tau*i/8; ca,sa=math.cos(a),math.sin(a)
                beam(B['black'],(xc,y+ca*.09,z+sa*.09),(xc,y+ca*.30,z+sa*.30),.045,.045)
            lo,hi=sorted((side*.84,side*1.00))
            box(B['iron'],lo,hi,.29,.58,z-.14,z+.14)
            cylinder(B['steel'],(side*.98,y,z),(side*1.035,y,z),.072,12)
            # Bearing horn connects the axle box to its bogie frame.
            lo,hi=sorted((side*.93,side*1.03))
            box(B['iron'],lo,hi,.52,.83,z-.075,z+.075)
    # Two compact bogie frames, leaf springs and diagonal hangers.
    for za,zb in ((1.50,2.55),(4.45,5.50)):
        box(B['black'],-.90,.90,.75,.97,za-.38,zb+.38)
        for side in (-1,1):
            x=side*.99
            beam(B['black'],(x,.72,za-.25),(x,.72,zb+.25),.12,.12)
            beam(B['black'],(x,.73,za-.30),(x,.95,za+.15),.08,.08)
            beam(B['black'],(x,.73,zb+.30),(x,.95,zb-.15),.08,.08)
            # Three stacked, bowed leaf springs at each bogie.
            for k in range(3):
                y=.90-k*.04
                beam(B['steel'],(x,y,za-.10),(x,y-.07,(za+zb)/2),.032,.026)
                beam(B['steel'],(x,y-.07,(za+zb)/2),(x,y,zb+.10),.032,.026)
    box(B['iron'],-.68,.68,.62,.94,2.94,3.97)
    # Red oxide beams, physically separate buffers and central couplers.
    box(B['red'],-1.18,1.18,1.18,1.43,.40,.56)
    box(B['red'],-1.18,1.18,1.18,1.43,6.34,6.50)
    for end,sgn in ((.4,-1),(6.5,1)):
        for side in (-1,1):
            x=side*.93
            cylinder(B['black'],(x,1.31,end),(x,1.31,end+sgn*.22),.105,16)
            cylinder(B['steel'],(x,1.31,end+sgn*.20),(x,1.31,end+sgn*.28),.16,20)
        cylinder(B['black'],(0,1.30,end),(0,1.30,end+sgn*.29),.09,12)
    box(B['black'],-.12,.12,1.20,1.40,0,.15)
    box(B['black'],-.12,.12,1.20,1.40,6.75,6.90)
    # End grab rails, ladders and rear working platforms in true geometry.
    for side in (-1,1):
        x=side*1.28
        for z in (.57,6.33):
            cylinder(B['steel'],(x,1.00,z),(x,2.90,z),.025,8)
            cylinder(B['steel'],(x,2.90,z),(side*1.15,2.90,z),.025,8)
        for y in (1.04,1.38,1.72,2.06,2.40,2.74):
            beam(B['steel'],(x,y,6.31),(x,y,6.60),.025,.025)
        cylinder(B['steel'],(x,1.00,6.60),(x,2.83,6.60),.025,8)
        box(B['black'],side*1.11 if side>0 else -1.35,side*1.35 if side>0 else -1.11,.75,.82,6.22,6.57)
    names={'iron':'Tank_And_Bogie_Cast_Iron','side':'Riveted_Painted_Side_Panels','coal':'Coal_Surface_Low_Poly','red':'Red_Buffer_Beams','black':'Chassis_Spokes_Couplings','rim':'Wheel_Treads','steel':'Buffers_Springs_Grabrails','brass':'Brass_Details'}
    # Brass is not used in this design, so do not create an empty GLB mesh.
    scene=trimesh.Scene();counts={}
    for key,b in B.items():
        if not b.f:continue
        m=b.mesh(mat[key]);name=names[key]
        scene.add_geometry(m,geom_name=name,node_name=name);counts[name]=len(m.faces)
    path=OUT/'coal_tender.glb';path.write_bytes(scene.export(file_type='glb'))
    data={'units':'meters','up_axis':'Y','forward':'-Z','bounds':scene.bounds.tolist(),'triangles':sum(counts.values()),'triangles_by_mesh':counts,'wheel_centers_x':[-.7515,.7515],'wheel_axles_z':list(axles),'wheel_radius_m':.42,'coupler_height_y':1.30,'rail_head_placement_y':.24,'coal_surface_triangles':len(B['coal'].f)}
    (OUT/'mesh_stats.json').write_text(json.dumps(data,indent=2)+'\n')
    print('GLB:',path,'bounds:',scene.bounds,'triangles:',data['triangles'],flush=True)

if __name__=='__main__':make_textures();build()
