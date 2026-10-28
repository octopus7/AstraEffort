#!/usr/bin/env python3
"""Build an individually textured Y-up, Z-forward 3D steam locomotive GLB."""
from pathlib import Path
import json,math
import numpy as np
from PIL import Image,ImageDraw,ImageEnhance,ImageFilter
import trimesh

OUT=Path(__file__).resolve().parent
TEX=OUT/'textures'; TEX.mkdir(exist_ok=True)
SEED=891301


def make_textures():
    # The supplied project image is AI-generated. Keep a baked copy so the
    # generator also remains portable when moved out of the station project.
    src=OUT.parent.parent/'materials'/'ai_aged_cast_iron.png'
    if src.exists():
        im=Image.open(src).convert('RGB')
        # Brighten a little for PBR illumination; retain the generated patina.
        im=ImageEnhance.Brightness(im).enhance(1.28)
        iron=Image.blend(im,Image.new('RGB',im.size,(52,55,57)),.20)
        iron.save(TEX/'aged_iron.png',optimize=True)
    else:
        iron=Image.open(TEX/'aged_iron.png').convert('RGB')
    # Boiler sheet overlays are drawn on top of the AI-generated cast iron.
    boiler=iron.copy(); d=ImageDraw.Draw(boiler); w,h=boiler.size
    for fraction in (.05,.18,.32,.46,.60,.74,.88,.97):
        y=int(fraction*h)
        d.line([(0,y-2),(w,y-2)],fill=(22,24,25),width=3)
        d.line([(0,y+2),(w,y+2)],fill=(91,90,86),width=1)
        for x in range(12,w,28):
            d.ellipse((x-2,y-1,x+2,y+3),fill=(20,22,23))
            d.point((x-1,y),fill=(114,110,103))
    for fraction in (.12,.38,.64,.88):
        x=int(fraction*w)
        d.line([(x,0),(x,h)],fill=(30,31,31),width=2)
        for y in range(10,h,34):
            d.ellipse((x-2,y-2,x+2,y+2),fill=(22,23,23));d.point((x-1,y-1),fill=(107,104,97))
    boiler.save(TEX/'boiler_sheet.png',optimize=True)
    # Planar smokebox door: circular rim and tiny rivets are in the image.
    door=iron.resize((1024,1024),Image.Resampling.LANCZOS)
    d=ImageDraw.Draw(door); cx=cy=512; radius=466
    for rr,col,ww in [(radius,(15,17,18),8),(radius-10,(105,104,98),2),(radius-20,(28,30,31),4)]:
        d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),outline=col,width=ww)
    for i in range(28):
        a=2*math.pi*i/28; x=cx+int(math.cos(a)*(radius-30)); y=cy+int(math.sin(a)*(radius-30))
        d.ellipse((x-5,y-5,x+5,y+5),fill=(16,17,18));d.ellipse((x-3,y-3,x,y),fill=(145,139,128))
    door.save(TEX/'smokebox_door.png',optimize=True)
    # Procedural painted iron for the crimson buffer beam and wheel spokes.
    rng=np.random.default_rng(SEED); w,h=1024,512
    base=np.empty((h,w,3),dtype=np.float32);base[:]=[103,31,26]
    grain=rng.normal(0,8,(h,w))
    for c in range(3): base[:,:,c]=np.clip(base[:,:,c]+grain,0,255)
    paint=Image.fromarray(base.astype('uint8'),'RGB'); d=ImageDraw.Draw(paint)
    for y in (30,85,h-85,h-30):
        for x in range(20,w,35):
            d.ellipse((x-3,y-3,x+3,y+3),fill=(46,28,24));d.point((x-1,y-1),fill=(161,103,77))
    paint.save(TEX/'red_painted_iron.png',optimize=True)
    print('Wrote textures to',TEX,flush=True)


def unit(v):
    a=np.asarray(v,dtype=float);return a/np.linalg.norm(a)

class Builder:
    def __init__(self):self.v=[];self.f=[];self.uv=[]
    def quad(self,p,uv=None):
        if uv is None:uv=[(0,0),(0,1),(1,1),(1,0)]
        n=len(self.v);self.v.extend(p);self.uv.extend(uv);self.f.extend([(n,n+1,n+2),(n,n+2,n+3)])
    def tri(self,p,uv=None):
        if uv is None:uv=[(0,0)]*3
        n=len(self.v);self.v.extend(p);self.uv.extend(uv);self.f.append((n,n+1,n+2))
    def mesh(self,material):
        m=trimesh.Trimesh(vertices=np.asarray(self.v,dtype=np.float32),faces=np.asarray(self.f,dtype=np.int64),process=False)
        m.visual=trimesh.visual.texture.TextureVisuals(uv=np.asarray(self.uv,dtype=np.float32),material=material)
        return m


def box(b,x0,x1,y0,y1,z0,z1):
    # Faces point outward. Spatial UVs are continuous at sensible scale.
    faces=[([(x0,y1,z0),(x0,y1,z1),(x1,y1,z1),(x1,y1,z0)],lambda x,y,z:(x/2,z/4)),
      ([(x1,y0,z0),(x1,y0,z1),(x0,y0,z1),(x0,y0,z0)],lambda x,y,z:(x/2,z/4)),
      ([(x0,y0,z0),(x0,y0,z1),(x0,y1,z1),(x0,y1,z0)],lambda x,y,z:(z/4,y/2)),
      ([(x1,y0,z1),(x1,y0,z0),(x1,y1,z0),(x1,y1,z1)],lambda x,y,z:(z/4,y/2)),
      ([(x0,y0,z0),(x0,y1,z0),(x1,y1,z0),(x1,y0,z0)],lambda x,y,z:(x/2,y/2)),
      ([(x1,y0,z1),(x1,y1,z1),(x0,y1,z1),(x0,y0,z1)],lambda x,y,z:(x/2,y/2))]
    for p,fn in faces:b.quad(p,[fn(*v) for v in p])


def frame(axis):
    axis=unit(axis); ref=np.array([0.,1.,0.]) if abs(axis[1])<.85 else np.array([1.,0.,0.])
    u=unit(ref-axis*np.dot(ref,axis));v=np.cross(axis,u)
    return axis,u,v


def cylinder(b,p0,p1,r,segments=16,caps=True,uvscale=1):
    p0=np.asarray(p0,float);p1=np.asarray(p1,float);axis,u,v=frame(p1-p0)
    ring=[]
    for i in range(segments+1):
        a=2*math.pi*i/segments; ring.append(math.cos(a)*u+math.sin(a)*v)
    for i in range(segments):
        a,beta=ring[i],ring[i+1]
        b.quad([p0+r*a,p0+r*beta,p1+r*beta,p1+r*a],[(i/segments,0),((i+1)/segments,0),((i+1)/segments,uvscale),(i/segments,uvscale)])
        if caps:
            ua=(.5+.5*math.cos(2*math.pi*i/segments),.5+.5*math.sin(2*math.pi*i/segments));ub=(.5+.5*math.cos(2*math.pi*(i+1)/segments),.5+.5*math.sin(2*math.pi*(i+1)/segments))
            b.tri([p0,p0+r*beta,p0+r*a],[(.5,.5),ub,ua]);b.tri([p1,p1+r*a,p1+r*beta],[(.5,.5),ua,ub])


def annulus(b,p0,p1,outer,inner,segments=32):
    p0=np.asarray(p0,float);p1=np.asarray(p1,float);axis,u,v=frame(p1-p0)
    for i in range(segments):
        a=2*math.pi*i/segments;c=2*math.pi*(i+1)/segments
        A=math.cos(a)*u+math.sin(a)*v;C=math.cos(c)*u+math.sin(c)*v
        # Outer wall, inner wall, and annular end faces.
        b.quad([p0+outer*A,p0+outer*C,p1+outer*C,p1+outer*A])
        b.quad([p0+inner*C,p0+inner*A,p1+inner*A,p1+inner*C])
        b.quad([p0+outer*C,p0+outer*A,p0+inner*A,p0+inner*C])
        b.quad([p1+outer*A,p1+outer*C,p1+inner*C,p1+inner*A])


def beam(b,p0,p1,width,depth):
    p0=np.asarray(p0,float);p1=np.asarray(p1,float);axis,u,v=frame(p1-p0)
    ring=[width*u/2+depth*v/2,-width*u/2+depth*v/2,-width*u/2-depth*v/2,width*u/2-depth*v/2]
    for i in range(4):
        a=ring[i]; c=ring[(i+1)%4];b.quad([p0+a,p0+c,p1+c,p1+a])
    b.quad([p0+ring[3],p0+ring[2],p0+ring[1],p0+ring[0]])
    b.quad([p1+ring[0],p1+ring[1],p1+ring[2],p1+ring[3]])


def disc(b,center,normal,r,segments=40):
    c=np.asarray(center,float);axis,u,v=frame(normal)
    for i in range(segments):
        a=2*math.pi*i/segments;z=2*math.pi*(i+1)/segments
        A=math.cos(a)*u+math.sin(a)*v;Z=math.cos(z)*u+math.sin(z)*v
        b.tri([c,c+r*A,c+r*Z],[(.5,.5),(.5+.5*math.cos(a),.5+.5*math.sin(a)),(.5+.5*math.cos(z),.5+.5*math.sin(z))])


def roof(b):
    # Curved sheet with a modest cab overhang, arching across X.
    xs=np.linspace(-1.27,1.27,13)
    y=lambda x:4.02-.20*(x/1.27)**2
    for a,c in zip(xs[:-1],xs[1:]):
        b.quad([(a,y(a),9.02),(a,y(a),12.48),(c,y(c),12.48),(c,y(c),9.02)],[(0,0),(0,1),(1,1),(1,0)])
        for z in (9.02,12.48):
            p=[(a,y(a)-.07,z),(a,y(a),z),(c,y(c),z),(c,y(c)-.07,z)]
            b.quad(p if z==9.02 else p[::-1])
    for x in (-1.27,1.27):
        b.quad([(x,y(x)-.07,9.02),(x,y(x)-.07,12.48),(x,y(x),12.48),(x,y(x),9.02)])


def build():
    mat={
     'boiler':trimesh.visual.material.PBRMaterial(name='AI-derived riveted boiler steel',baseColorTexture=Image.open(TEX/'boiler_sheet.png'),metallicFactor=.72,roughnessFactor=.62),
     'iron':trimesh.visual.material.PBRMaterial(name='AI-derived aged cast iron',baseColorTexture=Image.open(TEX/'aged_iron.png'),metallicFactor=.66,roughnessFactor=.69),
     'door':trimesh.visual.material.PBRMaterial(name='AI-derived smokebox door and rivet detail',baseColorTexture=Image.open(TEX/'smokebox_door.png'),metallicFactor=.7,roughnessFactor=.66),
     'red':trimesh.visual.material.PBRMaterial(name='Procedural worn red iron',baseColorTexture=Image.open(TEX/'red_painted_iron.png'),metallicFactor=.35,roughnessFactor=.73),
     'rim':trimesh.visual.material.PBRMaterial(name='Dark steel wheel rims',baseColorFactor=[.24,.24,.23,1],metallicFactor=.84,roughnessFactor=.42),
     'steel':trimesh.visual.material.PBRMaterial(name='Worn linkage steel',baseColorFactor=[.45,.44,.41,1],metallicFactor=.8,roughnessFactor=.44),
     'black':trimesh.visual.material.PBRMaterial(name='Soot-dark iron',baseColorFactor=[.12,.13,.14,1],metallicFactor=.58,roughnessFactor=.69),
     'brass':trimesh.visual.material.PBRMaterial(name='Aged brass handrails',baseColorFactor=[.56,.40,.20,1],metallicFactor=.80,roughnessFactor=.40),
     'glass':trimesh.visual.material.PBRMaterial(name='Dark cab glazing',baseColorFactor=[.095,.14,.16,1],metallicFactor=.22,roughnessFactor=.26),
     'lamp':trimesh.visual.material.PBRMaterial(name='Warm locomotive lamp lenses',baseColorFactor=[.88,.69,.40,1],emissiveFactor=[.18,.10,.025],metallicFactor=.18,roughnessFactor=.30)
    }
    B={k:Builder() for k in mat}
    # The large boiler, extra smokebox collar, front door, and raised bands.
    cylinder(B['boiler'],(0,2.44,1.67),(0,2.44,9.47),.94,48,uvscale=1)
    cylinder(B['iron'],(0,2.44,1.52),(0,2.44,2.20),.96,48)
    for z in (2.16,3.34,4.56,5.78,7.0,8.22,9.25):
        annulus(B['rim'],(0,2.44,z-.025),(0,2.44,z+.025),.963,.939,48)
    # Flat circular front with a physical rim and a textured concentric face.
    disc(B['door'],(0,2.44,1.503),(0,0,-1),.88,48)
    annulus(B['rim'],(0,2.44,1.495),(0,2.44,1.545),.96,.885,48)
    annulus(B['brass'],(0,2.44,1.465),(0,2.44,1.490),.18,.145,24)
    for a in np.linspace(0,math.tau,6,endpoint=False):
        cylinder(B['brass'],(0,2.44,1.45),(math.cos(a)*.15,2.44+math.sin(a)*.15,1.45),.012,8)
    cylinder(B['brass'],(0,2.44,1.40),(0,2.44,1.48),.045,12)
    # High stack with flared lip, steam dome and safety valves.
    cylinder(B['iron'],(0,3.20,2.03),(0,4.16,2.03),.245,24)
    cylinder(B['rim'],(0,4.10,2.03),(0,4.20,2.03),.285,24)
    annulus(B['steel'],(0,4.18,2.03),(0,4.21,2.03),.295,.205,24)
    cylinder(B['iron'],(0,3.28,4.30),(0,3.77,4.30),.31,24)
    cylinder(B['rim'],(0,3.73,4.30),(0,3.80,4.30),.325,24)
    cylinder(B['brass'],(0,3.31,6.50),(0,3.70,6.50),.12,16)
    cylinder(B['brass'],(0,3.67,6.50),(0,3.75,6.50),.17,16)
    # Long pipes and handrails, visible on both sides.
    for side in (-1,1):
        x=side*.96
        for y in (2.11,2.86):
            cylinder(B['brass'],(x,y,1.98),(x,y,9.20),.018,8)
            for z in (2.15,3.55,4.95,6.35,7.75,9.03):
                cylinder(B['brass'],(side*.90,y,z),(side*1.00,y,z),.027,8)
        cylinder(B['iron'],(side*1.02,1.91,2.05),(side*1.02,1.91,9.20),.055,12)
        # Main iron longitudinal chassis, with a thin crimson painted edge.
        box(B['black'],side*1.14 if side>0 else -1.26,side*1.26 if side>0 else -1.14,1.42,1.63,1.18,10.05)
        box(B['red'],side*1.255 if side>0 else -1.285,side*1.285 if side>0 else -1.255,1.52,1.60,1.19,10.02)
    box(B['black'],-1.13,1.13,1.46,1.66,1.25,10.15)
    # A continuation beneath the cab keeps the rear of the locomotive
    # structurally connected to the running gear and rear buffer beam.
    box(B['black'],-.96,.96,1.18,1.50,9.35,12.38)
    # Front steam chest cylinders, valve gear and small pipes.
    for side in (-1,1):
        xa,xb=sorted((side*.92,side*1.27))
        box(B['iron'],xa,xb,.82,1.44,1.90,3.02)
        cylinder(B['rim'],(side*1.10,1.13,1.77),(side*1.10,1.13,1.91),.28,20)
        cylinder(B['steel'],(side*1.10,1.13,1.72),(side*1.10,1.13,1.79),.15,16)
        beam(B['steel'],(side*1.09,1.02,2.72),(side*1.09,.91,4.23),.07,.07)
        cylinder(B['brass'],(side*1.24,.76,2.10),(side*1.24,.76,3.25),.025,8)
    # Three pairs of large, open-spoked driving wheels and a smaller leading pair.
    def wheel(z,r,driving):
        y=r
        cylinder(B['black'],(-.79,y,z),(.79,y,z),.078,12)
        for side in (-1,1):
            xc=side*.7515
            x0=xc-.065;x1=xc+.065
            annulus(B['rim'],(x0,y,z),(x1,y,z),r,r-.08,32 if driving else 24)
            annulus(B['red'],(x0-.002,y,z),(x1+.002,y,z),r-.08,r-.135,32 if driving else 24)
            cylinder(B['red'],(x0-.012,y,z),(x1+.012,y,z),.145 if driving else .11,16)
            n=12 if driving else 8
            for i in range(n):
                a=math.tau*i/n;ca,sa=math.cos(a),math.sin(a)
                beam(B['red'],(xc,y+ca*.12,z+sa*.12),(xc,y+ca*(r-.13),z+sa*(r-.13)),.065 if driving else .05,.06)
            # Axle outer cap and raised crank pin.
            xo=xc+side*.09
            cylinder(B['steel'],(xo-side*.035,y,z),(xo+side*.035,y,z),.105 if driving else .075,16)
            if driving:
                cylinder(B['steel'],(xc+side*.07,y+.105,z+.18),(xc+side*.25,y+.105,z+.18),.065,12)
    driver_z=(4.05,6.20,8.35)
    for z in driver_z:wheel(z,.80,True)
    wheel(2.10,.42,False)
    wheel(10.90,.42,False)
    # Forks connect the small trailing axle physically to the cab underframe.
    for side in (-1,1):
        beam(B['black'],(side*.65,1.25,10.90),(side*.65,.42,10.90),.13,.13)
        beam(B['black'],(side*.65,1.20,10.45),(side*.65,1.20,11.35),.12,.12)
    # Coupling rods and crank-pin washers on the outside of each wheel.
    for side in (-1,1):
        xx=side*1.01
        beam(B['steel'],(xx,.905,driver_z[0]+.04),(xx,.905,driver_z[-1]+.22),.095,.075)
        for z in (d+.18 for d in driver_z):
            cylinder(B['steel'],(xx-side*.06,.905,z),(xx+side*.06,.905,z),.09,16)
            cylinder(B['rim'],(xx+side*.055,.905,z),(xx+side*.075,.905,z),.038,12)
        # An upper rod gives the side linkage a recognizable steam-engine silhouette.
        beam(B['steel'],(side*1.04,1.11,2.70),(side*1.04,1.11,6.45),.055,.055)
    # Crimson front buffer beam, paired physical buffers, and front lamps.
    box(B['red'],-1.28,1.28,1.22,1.48,1.10,1.35)
    for side in (-1,1):
        x=side*.93
        cylinder(B['black'],(x,1.35,.76),(x,1.35,1.12),.105,16)
        cylinder(B['steel'],(x,1.35,.68),(x,1.35,.78),.17,20)
        cylinder(B['brass'],(x,1.72,1.24),(x,1.72,1.49),.12,16)
        disc(B['lamp'],(x,1.72,1.225),(0,0,-1),.095,16)
    cylinder(B['black'],(0,1.31,.80),(0,1.31,1.18),.11,12)
    box(B['black'],-.13,.13,1.14,1.49,.75,.99)
    # Angled pilot: transverse front edge and eleven metal slats.
    box(B['rim'],-1.20,1.20,.12,.20,0,.10)
    box(B['rim'],-1.20,1.20,1.08,1.16,1.00,1.10)
    for x in np.linspace(-1.10,1.10,11):
        beam(B['rim'],(x,.16,.055),(x,1.12,1.04),.055,.055)
    for side in (-1,1):beam(B['steel'],(side*1.20,.17,.05),(side*1.20,1.13,1.05),.055,.055)
    # Cab floor, lower side plates, window posts, dark glazing, and gold trim.
    box(B['iron'],-1.14,1.14,1.49,1.65,9.10,12.34)
    for side in (-1,1):
        lo,hi=sorted((side*1.10,side*1.18)); x=side*1.19
        box(B['iron'],lo,hi,1.65,2.67,9.12,12.32)
        box(B['iron'],lo,hi,3.54,3.82,9.12,12.32)
        for z in (9.12,10.63,12.20):box(B['iron'],lo,hi,2.65,3.55,z,z+.12)
        for za,zb in ((9.24,10.63),(10.75,12.20)):
            box(B['glass'],lo,hi,2.70,3.50,za,zb)
            for y in (2.69,3.51):beam(B['brass'],(x,y,za),(x,y,zb),.022,.022)
            for z in (za,zb):beam(B['brass'],(x,2.69,z),(x,3.51,z),.022,.022)
        # Large outlined lower cab panel, made from fine actual strips.
        for y in (1.86,2.51):beam(B['brass'],(x,y,9.55),(x,y,11.97),.018,.018)
        for z in (9.55,11.97):beam(B['brass'],(x,1.86,z),(x,2.51,z),.018,.018)
        # Steps and vertical rear grab iron.
        box(B['black'],side*1.04 if side>0 else -1.28,side*1.28 if side>0 else -1.04,.62,.70,11.55,12.20)
        cylinder(B['brass'],(side*1.20,.74,12.23),(side*1.20,2.35,12.23),.024,8)
    # Rear wall frame, cab roof, rear beam and coupling.
    # The front bulkhead has framed windows on either side of the boiler.
    box(B['iron'],-1.10,1.10,1.65,2.69,9.10,9.18)
    box(B['iron'],-1.10,1.10,3.52,3.83,9.10,9.18)
    for x in (-1.10,-.08,.98):box(B['iron'],x,x+.12,2.69,3.52,9.10,9.18)
    for xa,xb in ((-.98,-.08),(.04,.98)):
        box(B['glass'],xa,xb,2.72,3.49,9.08,9.10)
    box(B['iron'],-1.10,1.10,1.65,2.55,12.25,12.34)
    for x in (-1.10,-.12,.98):box(B['iron'],x,x+.12,2.55,3.80,12.25,12.34)
    box(B['iron'],-1.10,1.10,3.53,3.83,12.25,12.34)
    roof(B['iron'])
    box(B['red'],-1.15,1.15,1.18,1.43,12.30,12.55)
    cylinder(B['black'],(0,1.30,12.52),(0,1.30,12.84),.09,12)
    box(B['black'],-.12,.12,1.20,1.40,12.80,12.95)
    # A simple brass headlight centered above the smokebox face.
    cylinder(B['brass'],(0,3.53,1.35),(0,3.53,1.62),.14,20)
    disc(B['lamp'],(0,3.53,1.34),(0,0,-1),.11,20)
    # Export separate PBR primitives with descriptive names.
    labels={'boiler':'Boiler_Riveted_Shell','iron':'Cab_And_Aged_Iron','door':'Smokebox_Door','red':'Red_Frame_And_Spokes','rim':'Wheel_Rims_And_Pilot','steel':'Linkage_And_Buffers','black':'Chassis_And_Axles','brass':'Brass_Trim_And_Fittings','glass':'Cab_Window_Glazing','lamp':'Headlight_Lenses'}
    scene=trimesh.Scene();stats={}
    for key,b in B.items():
        m=b.mesh(mat[key]);scene.add_geometry(m,geom_name=labels[key],node_name=labels[key]);stats[labels[key]]=len(m.faces)
    out=OUT/'steam_locomotive.glb';out.write_bytes(scene.export(file_type='glb'))
    data={'units':'meters','up_axis':'Y','forward':'-Z','front_z':0,'bounds':scene.bounds.tolist(),'triangles':sum(stats.values()),'triangles_by_mesh':stats,'driving_wheel_centers_z':list(driver_z),'driving_wheel_radius_m':.8,'wheel_centers_x':[-.7515,.7515],'leading_axle_center_z':2.1,'trailing_axle_center_z':10.9,'small_wheel_radius_m':.42,'rail_head_placement_y':.24}
    (OUT/'mesh_stats.json').write_text(json.dumps(data,indent=2)+'\n')
    print('GLB:',out,'bounds:',scene.bounds,'triangles:',data['triangles'],flush=True)

if __name__=='__main__':make_textures();build()
