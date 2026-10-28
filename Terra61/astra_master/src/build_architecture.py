#!/usr/bin/env python3
"""Build Riverdale's reusable, textured Victorian station architecture.

Authored coordinates are X across the facade, Y into the building, Z up.
Each GLB contains one -90-degree X root rotation to convert to glTF Y-up.
The assembly contains seven nodes pointing at three genuinely shared meshes.
"""
from __future__ import annotations

import io
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from pygltflib import (
    GLTF2, Asset, Scene, Node, Mesh, Primitive, Attributes, Accessor,
    BufferView, Buffer, Material, PbrMetallicRoughness, TextureInfo,
    Texture, Sampler, Image as GLTFImage, NormalMaterialTexture,
)

STATION = Path(__file__).resolve().parents[1]
OUT = STATION / 'modules' / 'architecture'
REF = STATION / 'references' / '01_station_architecture_reference.png'

# The tiles are separate images, so repeated charts never repeat an entire
# multi-material atlas. Detail images are mapped once onto their hero panels.
MATERIAL_SOURCES = {
    'stone': ('stone', None), 'brick': ('brick', None), 'iron': ('iron', None),
    'slate': ('slate', None), 'gold': ('ornament', None),
    'window': ('window', (95, 75, 533, 628)),
    'grand_window': ('window', (95, 75, 533, 628)),
    'clock': ('clock', (16, 25, 613, 628)), 'sign': ('sign', None),
}
METAL = {'stone': 0.0, 'brick': 0.0, 'iron': 0.8, 'slate': 0.35, 'gold': 0.75,
         'window': 0.12, 'door': 0.05, 'grand_window': 0.1, 'clock': 0.25, 'sign': 0.3}
ROUGH = {'stone': 0.87, 'brick': 0.92, 'iron': 0.55, 'slate': 0.66, 'gold': 0.48,
         'window': 0.42, 'door': 0.58, 'grand_window': 0.42, 'clock': 0.54, 'sign': 0.55}


def write_png_atomic(image, target):
    """Never expose a truncated intermediate map to concurrent asset readers."""
    encoded=io.BytesIO()
    image.save(encoded,format='PNG',optimize=True)
    fd,tmp=tempfile.mkstemp(prefix='.texture-',suffix='.png',dir=target.parent)
    with os.fdopen(fd,'wb') as f:
        f.write(encoded.getvalue())
    os.replace(tmp,target)


def prepare_textures():
    """Copy coordinated PBR tiles, and crop detail images consistently."""
    OUT.mkdir(parents=True, exist_ok=True)
    result = {}
    for name, (stem, crop) in MATERIAL_SOURCES.items():
        record = {'source': f'textures/{stem}_basecolor.png' + (f' crop {crop}' if crop else '')}
        for key, suffix in [('base', 'basecolor'), ('normal', 'normal'), ('orm', 'orm')]:
            source = STATION / 'textures' / f'{stem}_{suffix}.png'
            if not source.exists():
                raise FileNotFoundError(f'missing generated PBR source: {source}')
            image = Image.open(source).convert('RGB')
            if crop:
                image = image.crop(crop)
            target = OUT / f'mat_{name}_{suffix}.png'
            write_png_atomic(image,target)
            record[key] = target
        result[name] = record
    # The dedicated high-resolution door has a warm glazed fanlight. Crop the
    # outside margins and fit its arch spring explicitly in panel() below.
    source=STATION/'textures'/'door_basecolor.png'
    if not source.exists():
        raise FileNotFoundError(f'missing generated door image: {source}')
    crop=(48,0,976,1536)
    image=Image.open(source).convert('RGB').crop(crop)
    target = OUT / 'panel_door.png'
    write_png_atomic(image,target)
    result['door'] = {'base': target, 'source': f'textures/door_basecolor.png crop {crop}'}
    return result


class Geometry:
    """Triangle soup per material, with explicit normals and UV for every face."""
    def __init__(self, name):
        self.name = name
        self.parts = {}

    def triangle(self, material, positions, uvs):
        p = np.asarray(positions, dtype=np.float64)
        cross = np.cross(p[1] - p[0], p[2] - p[0])
        ln = float(np.linalg.norm(cross))
        if ln < 1e-9:
            return
        n = cross / ln
        d = self.parts.setdefault(material, {'p': [], 'n': [], 'uv': [], 'i': []})
        base = len(d['p'])
        d['p'].extend(p.tolist())
        d['n'].extend([n.tolist()] * 3)
        d['uv'].extend([list(map(float, uv)) for uv in uvs])
        d['i'].extend([base, base + 1, base + 2])

    def quad(self, mat, pts, uv=None):
        if uv is None:
            # Map each architectural surface by its physical dimensions.
            a = np.linalg.norm(np.subtract(pts[1], pts[0])) * 0.48
            b = np.linalg.norm(np.subtract(pts[3], pts[0])) * 0.48
            uv = [(0, b), (a, b), (a, 0), (0, 0)]
        self.triangle(mat, [pts[0], pts[1], pts[2]], [uv[0], uv[1], uv[2]])
        self.triangle(mat, [pts[0], pts[2], pts[3]], [uv[0], uv[2], uv[3]])

    def box(self, mat, x0, x1, y0, y1, z0, z1):
        assert x1 > x0 and y1 > y0 and z1 > z0
        # All faces wound counter-clockwise from outside.
        self.quad(mat, [(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)])
        self.quad(mat, [(x1,y1,z0),(x0,y1,z0),(x0,y1,z1),(x1,y1,z1)])
        self.quad(mat, [(x0,y1,z0),(x0,y0,z0),(x0,y0,z1),(x0,y1,z1)])
        self.quad(mat, [(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)])
        self.quad(mat, [(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)])
        self.quad(mat, [(x0,y1,z0),(x1,y1,z0),(x1,y0,z0),(x0,y0,z0)])

    def panel(self, mat, cx, y, z_bottom, spring, radius, segments=28, spring_v=None):
        """Curved window/door polygon, whose opening is genuinely recessed."""
        h = spring + radius - z_bottom
        outline = [(cx-radius,z_bottom),(cx+radius,z_bottom),(cx+radius,spring)]
        outline += [(cx+radius*math.cos(t), spring+radius*math.sin(t))
                    for t in np.linspace(0, math.pi, segments+1)[1:]]
        center=(cx,y,(z_bottom+spring)/2)
        def uv_v(z):
            if spring_v is None:
                return 1-(z-z_bottom)/h
            if z<=spring:
                return 1-(1-spring_v)*(z-z_bottom)/(spring-z_bottom)
            return spring_v*(1-(z-spring)/radius)
        center_uv=(0.5, uv_v(center[2]))
        for i, a in enumerate(outline):
            b=outline[(i+1)%len(outline)]
            pa=(a[0],y,a[1]); pb=(b[0],y,b[1])
            uv_a=((a[0]-cx+radius)/(2*radius), uv_v(a[1]))
            uv_b=((b[0]-cx+radius)/(2*radius), uv_v(b[1]))
            self.triangle(mat, [center, pa, pb], [center_uv, uv_a, uv_b])

    def circle(self, mat, cx, y, cz, radius, segments=48):
        for i in range(segments):
            t0=2*math.pi*i/segments; t1=2*math.pi*(i+1)/segments
            # Going from right toward top is CCW in X/Z, front faces -Y.
            a=(cx+radius*math.cos(t0),y,cz+radius*math.sin(t0))
            b=(cx+radius*math.cos(t1),y,cz+radius*math.sin(t1))
            uv=lambda t:(.5+.5*math.cos(t), .5-.5*math.sin(t))
            self.triangle(mat, [(cx,y,cz),a,b],[(.5,.5),uv(t0),uv(t1)])

    def image_panel(self, mat, x0, x1, y, z0, z1):
        self.quad(mat,[(x0,y,z0),(x1,y,z0),(x1,y,z1),(x0,y,z1)],
                  [(0,1),(1,1),(1,0),(0,0)])

    def ring(self, mat, cx, cy, cz, r0, r1, start=0, end=math.pi, segments=32, depth=0.12):
        """Visible arch/circle molding with real depth, tiled stone or metal."""
        for i in range(segments):
            t0=start+(end-start)*i/segments; t1=start+(end-start)*(i+1)/segments
            def pos(r,t,y): return (cx+r*math.cos(t),y,cz+r*math.sin(t))
            a,b,c,d=pos(r0,t0,cy),pos(r1,t0,cy),pos(r1,t1,cy),pos(r0,t1,cy)
            self.quad(mat,[a,b,c,d])
            self.quad(mat,[pos(r1,t1,cy),pos(r1,t0,cy),pos(r1,t0,cy+depth),pos(r1,t1,cy+depth)])
            self.quad(mat,[pos(r0,t0,cy),pos(r0,t1,cy),pos(r0,t1,cy+depth),pos(r0,t0,cy+depth)])

    def sloped_roof(self, mat, halfwidth, yfront, yback, spring, radius, segments=40):
        """Half-barrel roof with an actual arched silhouette."""
        for i in range(segments):
            t0=math.pi*i/segments; t1=math.pi*(i+1)/segments
            x0,z0=halfwidth*math.cos(t0),spring+radius*math.sin(t0)
            x1,z1=halfwidth*math.cos(t1),spring+radius*math.sin(t1)
            self.quad(mat,[(x1,yfront,z1),(x0,yfront,z0),(x0,yback,z0),(x1,yback,z1)])
        # End infill under the roof; front is partly covered by the decorative arch.
        for i in range(segments):
            t0=math.pi*i/segments; t1=math.pi*(i+1)/segments
            p=lambda t,y:(halfwidth*math.cos(t),y,spring+radius*math.sin(t))
            self.triangle(mat,[(0,yback,spring),p(t1,yback),p(t0,yback)],[(.5,1),(0,0),(1,0)])

    def lathe(self, mat, cx, cy, levels, segments=32):
        for j in range(len(levels)-1):
            z0,r0=levels[j]; z1,r1=levels[j+1]
            for i in range(segments):
                t0=2*math.pi*i/segments; t1=2*math.pi*(i+1)/segments
                p=lambda z,r,t:(cx+r*math.cos(t),cy+r*math.sin(t),z)
                u0=i/segments; u1=(i+1)/segments
                v0=1-j/(len(levels)-1); v1=1-(j+1)/(len(levels)-1)
                self.quad(mat,[p(z0,r0,t0),p(z0,r0,t1),p(z1,r1,t1),p(z1,r1,t0)],
                          [(u0,v0),(u1,v0),(u1,v1),(u0,v1)])

    def bounds(self):
        p=np.concatenate([np.asarray(v['p']) for v in self.parts.values()])
        return [p.min(axis=0).round(4).tolist(),p.max(axis=0).round(4).tolist()]

    def triangles(self):
        return sum(len(d['i'])//3 for d in self.parts.values())


def wall_level(g, width, low, high, openings, wall='brick', yfront=2.45, yback=3.0):
    """Facade infill surrounding openings. Their shallow reveals have depth."""
    ordered=sorted(openings, key=lambda x:x['cx'])
    cursor=-width/2
    for o in ordered:
        cx,r,z0,spring=o['cx'],o['r'],o['bottom'],o['spring']
        left,right=cx-r,cx+r
        if left > cursor + 1e-6:
            g.box(wall,cursor,left,yfront,yback,low,high)
        if z0 > low + 1e-6:
            g.box(wall,left,right,yfront,yback,low,z0)
        if high > spring+r+1e-6:
            g.box(wall,left,right,yfront,yback,spring+r,high)
        # Arch spandrel above curve: segmented front/back face plus intrados.
        for i in range(28):
            t0=math.pi*i/28; t1=math.pi*(i+1)/28
            a=(cx+r*math.cos(t0),spring+r*math.sin(t0))
            b=(cx+r*math.cos(t1),spring+r*math.sin(t1))
            top=spring+r
            g.quad(wall,[(b[0],yfront,b[1]),(a[0],yfront,a[1]),(a[0],yfront,top),(b[0],yfront,top)])
            g.quad(wall,[(a[0],yback,a[1]),(b[0],yback,b[1]),(b[0],yback,top),(a[0],yback,top)])
            g.quad('stone',[(a[0],yfront,a[1]),(b[0],yfront,b[1]),(b[0],yback,b[1]),(a[0],yback,a[1])])
        g.panel(o['texture'],cx,yfront+0.42,z0,spring,r,
                spring_v=.25 if o['texture']=='door' else None)
        # Raised surrounds, side jambs, and a projecting sill.
        ringw=o.get('trim',0.17)
        g.ring('stone',cx,yfront-0.12,spring,r,r+ringw,segments=28,depth=0.14)
        g.box('stone',left-ringw,left,yfront-0.12,yfront+0.12,z0,spring)
        g.box('stone',right,right+ringw,yfront-0.12,yfront+0.12,z0,spring)
        g.box('stone',left-ringw-0.06,right+ringw+0.06,yfront-0.18,yfront+0.2,z0-0.12,z0)
        cursor=right
    if cursor < width/2-1e-6:
        g.box(wall,cursor,width/2,yfront,yback,low,high)


def moulding(g, width, z, depth=0.14, height=0.18, mat='stone', yfront=2.45, yback=10):
    g.box(mat,-width/2,width/2,max(0,yfront-depth),yback,z,z+height)


def pilaster(g, x, z0, z1, width=0.42, yfront=2.1):
    g.box('stone',x-width/2,x+width/2,yfront,2.60,z0,z1)
    g.box('stone',x-width/2-.1,x+width/2+.1,yfront-.09,2.68,z0,z0+.36)
    g.box('stone',x-width/2-.12,x+width/2+.12,yfront-.1,2.68,z1-.32,z1)


def finial(g,x,y,z,s=1.0):
    levels=[(z,.22*s),(z+.12*s,.29*s),(z+.21*s,.20*s),(z+.36*s,.14*s),
            (z+.54*s,.22*s),(z+.74*s,.12*s),(z+.95*s,.025*s)]
    g.lathe('stone',x,y,levels,segments=12)


def cornice(g,width,z,yfront=2.45):
    for dz,d,h in [(0,.12,.17),(.17,.25,.20),(.37,.38,.17),(.54,.20,.18)]:
        moulding(g,width,z+dz,d,h,yfront=yfront)


def canopy(g, width):
    """Projecting iron canopy and columns; repeated as an integral module part."""
    g.box('iron',-width/2+.10,width/2-.10,0.12,2.50,6.95,7.13)
    g.box('iron',-width/2+.10,width/2-.10,0.10,0.24,6.61,6.97)
    g.box('gold',-width/2+.10,width/2-.10,0.00,0.15,6.82,6.88)
    # Cast-iron supports and broad curved brackets are silhouette geometry;
    # their fine floral motifs remain in the iron texture.
    for x in (-width/2+.42,width/2-.42):
        g.box('iron',x-.16,x+.16,.18,.50,.05,6.63)
        g.box('iron',x-.29,x+.29,.12,.56,.05,.58)
        g.box('gold',x-.22,x+.22,.10,.58,.58,.67)
        g.box('iron',x-.28,x+.28,.12,.57,6.18,6.52)
        # Quarter-ring brackets turn inward without crossing module boundaries.
        start,end=(0,math.pi/2) if x < 0 else (math.pi/2,math.pi)
        g.ring('iron',x,0.10,5.60,.99,1.10,start=start,end=end,segments=12,depth=.10)


def central_hall():
    g=Geometry('central_hall')
    g.box('stone',-8,8,3,10,0,12.3)
    g.sloped_roof('slate',7.1,3,10,12.3,7.1)
    openings=[{'cx':x,'r':.95,'bottom':.25,'spring':4.32,'texture':'door','trim':.15}
              for x in (-5.55,-1.85,1.85,5.55)]
    wall_level(g,16,0,7.6,openings,wall='stone')
    wall_level(g,16,7.6,12.3,[{'cx':0,'r':5.05,'bottom':7.8,'spring':12.3,
                               'texture':'grand_window','trim':.26}],wall='brick')
    # Between upper window and outer barrel-roof silhouette are concentric arches.
    g.ring('brick',0,2.45,12.3,5.05,6.54,segments=44,depth=.55)
    g.ring('stone',0,2.21,12.3,5.08,5.38,segments=44,depth=.24)
    g.ring('stone',0,2.12,12.3,6.50,6.90,segments=44,depth=.35)
    g.ring('gold',0,2.04,12.3,6.40,6.49,segments=44,depth=.14)
    g.ring('stone',0,2.06,12.3,6.94,7.12,segments=44,depth=.3)
    # The clock is a raised disk atop the photographically detailed grand window.
    g.circle('clock',0,2.00,14.0,1.82,segments=48)
    g.ring('iron',0,1.97,14.0,1.82,2.03,0,2*math.pi,48,.18)
    g.ring('gold',0,1.94,14.0,1.77,1.84,0,2*math.pi,48,.10)
    for x in (-7.6,7.6):
        pilaster(g,x,.05,12.6,.55)
        finial(g,x,2.2,12.65,.9)
    for z in (.05,1.0,7.44): moulding(g,16,z,.20,.20)
    g.box('stone',-1.0,1.0,2.0,2.62,19.10,19.42)
    finial(g,0,2.18,19.42,.80)
    canopy(g,16)
    # One hero sign uses the full image; stone and metal boxes use tiles only.
    g.box('iron',-3.2,3.2,.10,.31,7.15,9.07)
    g.image_panel('sign',-3.18,3.18,.085,7.17,9.05)
    return g


def facade_bay():
    g=Geometry('facade_bay')
    g.box('brick',-2,2,3,10,0,9.9)
    wall_level(g,4,0,9.9,[{'cx':0,'r':.96,'bottom':1.35,'spring':5.4,
                           'texture':'window','trim':.16}])
    for x in (-1.68,1.68): pilaster(g,x,.05,10.0,.30)
    for z in (.06,.78,7.88): moulding(g,4,z,.18,.16)
    cornice(g,4,9.9)
    g.box('stone',-1.76,1.76,2.33,2.70,10.62,11.12)
    g.box('iron',-1.6,1.6,2.25,2.32,10.74,11.03)
    for x in (-1.72,1.72):
        g.box('stone',x-.21,x+.21,2.18,2.78,10.58,11.05)
        finial(g,x,2.35,11.05,.78)
    return g


def dome_tower():
    g=Geometry('dome_tower')
    g.box('brick',-4,4,3,10,0,16.35)
    wall_level(g,8,0,7.6,[{'cx':0,'r':1.10,'bottom':.25,'spring':4.62,
                           'texture':'door','trim':.18}],wall='stone')
    wall_level(g,8,7.6,16.35,[{'cx':0,'r':1.10,'bottom':9.0,'spring':13.25,
                               'texture':'window','trim':.20}],wall='brick')
    for x in (-3.60,3.60): pilaster(g,x,.05,16.35,.55)
    for z in (.06,.88,7.45,8.45,15.85): moulding(g,8,z,.18,.17)
    cornice(g,8,16.35)
    # Parapet and stone drum support the substantial iron-clad dome.
    g.box('stone',-3.7,3.7,2.38,9.65,17.05,17.38)
    g.box('stone',-3.5,3.5,2.56,9.48,17.38,17.65)
    levels=[(17.60,3.25),(18.05,3.28),(18.72,3.20),(19.40,3.04),
            (20.12,2.70),(20.78,2.21),(21.40,1.57),(21.82,.91),(22.08,.34)]
    g.lathe('slate',0,6.0,levels,segments=32)
    # Prominent seam ribs: low count and tied to the dome's silhouette.
    for i in range(12):
        t=2*math.pi*i/12
        # Straight ribs stepped over the curved dome surface.
        for j in range(len(levels)-1):
            z0,r0=levels[j]; z1,r1=levels[j+1]
            dt=.018
            p=lambda r,z,a:(r*math.cos(a),6+r*math.sin(a),z)
            g.quad('iron',[p(r0+0.015,z0,t-dt),p(r0+0.015,z0,t+dt),
                           p(r1+0.015,z1,t+dt),p(r1+0.015,z1,t-dt)])
    g.lathe('iron',0,6,[(22.05,.37),(22.19,.68),(22.35,.68),(22.48,.43),
                       (23.0,.43),(23.11,.68),(23.23,.40)],segments=16)
    g.lathe('gold',0,6,[(23.23,.30),(23.45,.19),(23.58,.10),(24.36,.015)],segments=12)
    for x in (-3.55,3.55): finial(g,x,2.45,17.22,.9)
    canopy(g,8)
    return g


class GLBWriter:
    def __init__(self):
        self.gltf=GLTF2(asset=Asset(version='2.0',generator='Riverdale station architecture generator'))
        self.gltf.scenes=[Scene(nodes=[0])]
        self.gltf.scene=0
        self.gltf.nodes=[Node(name='Z_UP_TO_GLTF_Y_UP',rotation=[-math.sqrt(.5),0,0,math.sqrt(.5)],children=[])]
        self.gltf.bufferViews=[]; self.gltf.accessors=[]; self.gltf.meshes=[]
        self.gltf.images=[]; self.gltf.textures=[]; self.gltf.materials=[]
        self.gltf.samplers=[Sampler(magFilter=9729,minFilter=9987,wrapS=10497,wrapT=10497)]
        self.data=bytearray()
        self.texture_cache={}

    def blob(self, data, target=None):
        while len(self.data)%4: self.data.append(0)
        start=len(self.data); self.data.extend(data)
        idx=len(self.gltf.bufferViews)
        self.gltf.bufferViews.append(BufferView(buffer=0,byteOffset=start,byteLength=len(data),target=target))
        return idx

    def texture(self,path):
        data=Path(path).read_bytes()
        digest=hashlib.sha256(data).digest()
        if digest in self.texture_cache:
            return self.texture_cache[digest]
        view=self.blob(data)
        i=len(self.gltf.images)
        self.gltf.images.append(GLTFImage(name=Path(path).name,bufferView=view,mimeType='image/png'))
        tex=len(self.gltf.textures)
        self.gltf.textures.append(Texture(sampler=0,source=i))
        self.texture_cache[digest]=tex
        return tex

    def add_material(self,name,record):
        texture=self.texture(record['base'])
        # glTF reads roughness from G and metallic from B; the art pipeline's
        # ORM images already have those channels in precisely that order.
        factors=(1.0,1.0) if 'orm' in record else (METAL[name],ROUGH[name])
        pbr=PbrMetallicRoughness(baseColorFactor=[1,1,1,1],baseColorTexture=TextureInfo(index=texture),
                                 metallicFactor=factors[0],roughnessFactor=factors[1])
        if 'orm' in record:
            pbr.metallicRoughnessTexture=TextureInfo(index=self.texture(record['orm']))
        normal=None
        if 'normal' in record:
            normal=NormalMaterialTexture(index=self.texture(record['normal']),scale=.75)
        index=len(self.gltf.materials)
        self.gltf.materials.append(Material(name=name,pbrMetallicRoughness=pbr,normalTexture=normal,doubleSided=False))
        return index

    def accessor(self,arr,component,typ,target):
        arr=np.ascontiguousarray(arr)
        view=self.blob(arr.tobytes(),target)
        if typ=='SCALAR':
            mn=[int(arr.min())]; mx=[int(arr.max())]; count=len(arr)
        else:
            mn=np.min(arr,axis=0).astype(float).tolist(); mx=np.max(arr,axis=0).astype(float).tolist(); count=len(arr)
        index=len(self.gltf.accessors)
        self.gltf.accessors.append(Accessor(bufferView=view,byteOffset=0,componentType=component,count=count,type=typ,min=mn,max=mx))
        return index

    def add_mesh(self,geo,material_lookup):
        prims=[]
        for material,d in geo.parts.items():
            p=np.asarray(d['p'],dtype='<f4'); n=np.asarray(d['n'],dtype='<f4')
            uv=np.asarray(d['uv'],dtype='<f4'); indices=np.asarray(d['i'],dtype='<u4')
            attrs=Attributes(POSITION=self.accessor(p,5126,'VEC3',34962),
                             NORMAL=self.accessor(n,5126,'VEC3',34962),
                             TEXCOORD_0=self.accessor(uv,5126,'VEC2',34962))
            a=self.accessor(indices,5125,'SCALAR',34963)
            prims.append(Primitive(attributes=attrs,indices=a,material=material_lookup[material],mode=4))
        idx=len(self.gltf.meshes)
        self.gltf.meshes.append(Mesh(name=geo.name,primitives=prims))
        return idx

    def instance(self, mesh, name, x):
        node=len(self.gltf.nodes)
        self.gltf.nodes.append(Node(name=name,mesh=mesh,translation=[float(x),0,0]))
        self.gltf.nodes[0].children.append(node)

    def save(self,path):
        while len(self.data)%4: self.data.append(0)
        self.gltf.buffers=[Buffer(byteLength=len(self.data))]
        self.gltf.set_binary_blob(bytes(self.data))
        # A renderer may read a previous export while a rebuild is running.
        # Replace the finished binary atomically instead of truncating in place.
        fd,tmp=tempfile.mkstemp(prefix='.glb-',suffix='.glb',dir=path.parent)
        os.close(fd)
        self.gltf.save_binary(tmp)
        os.replace(tmp,path)


def export(path, modules, placements, texture_records):
    wr=GLBWriter()
    used=sorted(set(k for geo in modules.values() for k in geo.parts))
    materials={name:wr.add_material(name,texture_records[name]) for name in used}
    meshes={name:wr.add_mesh(geo,materials) for name,geo in modules.items()}
    for module,label,x in placements: wr.instance(meshes[module],label,x)
    wr.save(path)


def main():
    textures=prepare_textures()
    modules={'central_hall':central_hall(),'facade_bay':facade_bay(),'dome_tower':dome_tower()}
    for name,geo in modules.items():
        export(OUT / (name+'.glb'),{name:geo},[(name,name,0)],textures)
    placement=[('facade_bay','west_outer_bay',-22),('facade_bay','west_inner_bay',-18),
               ('dome_tower','west_tower',-12),('central_hall','clock_hall',0),
               ('dome_tower','east_tower',12),('facade_bay','east_inner_bay',18),
               ('facade_bay','east_outer_bay',22)]
    export(OUT/'architecture_assembled.glb',modules,placement,textures)
    bounds=[]
    for module,_,x in placement:
        lo,hi=np.asarray(modules[module].bounds())
        bounds.append([lo + np.array([x,0,0]),hi + np.array([x,0,0])])
    bounds=np.asarray(bounds)
    assembly_bounds=[bounds[:,0,:].min(axis=0).round(4).tolist(),
                     bounds[:,1,:].max(axis=0).round(4).tolist()]
    manifest={'coordinate_system':{'units':'meters','authored_up':'Z','front':'-Y',
                 'gltf_root_rotation_xyzw':[-math.sqrt(.5),0,0,math.sqrt(.5)],
                 'origins':'centered X, ground Z=0; facade canopy front at Y=0'},
              'modules':{},'assembly':{'file':'architecture_assembled.glb',
                 'placements':[{'module':a,'node':b,'x_m':c} for a,b,c in placement],
                 'bounds_author_z_up':assembly_bounds,
                 'unique_triangles':sum(g.triangles() for g in modules.values()),
                 'drawn_triangles':sum(modules[a].triangles() for a,_,_ in placement)},
              'textures':{k:{kk:(str(vv.relative_to(STATION)) if isinstance(vv,Path) else vv)
                              for kk,vv in record.items()} for k,record in textures.items()}}
    for name,geo in modules.items():
        manifest['modules'][name]={'file':name+'.glb','bounds_author_z_up':geo.bounds(),
                                    'triangles':geo.triangles(),
                                    'materials':list(geo.parts),'uv_coverage':'all triangles',
                                    'origin':'center X, floor Z=0; facade fronts toward -Y'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'modules':manifest['modules'],'assembly':manifest['assembly']},indent=2))

if __name__=='__main__': main()
