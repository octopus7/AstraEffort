#!/usr/bin/env python3
"""Build the Victorian entrance building as a Y-up, metre-scale textured GLB.

Brick source is a separately supplied AI-generated base-color image. Other
maps, meshes and the clock face are generated procedurally by this script.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import trimesh
import math, shutil, json

ROOT = Path(__file__).resolve().parent
TEX = ROOT / 'textures'
TEX.mkdir(exist_ok=True)
BRICK_SRC = ROOT.parents[1] / 'materials' / 'ai_victorian_brick.png'
STONE_SRC = ROOT.parents[1] / 'materials' / 'ai_victorian_stone.png'
for src in (BRICK_SRC, STONE_SRC):
    target=TEX/src.name
    if src.exists() and src.resolve()!=target.resolve():shutil.copy2(src,target)
    elif not target.exists():raise FileNotFoundError(f'Missing material: {src.name}')
RNG = np.random.default_rng(63827)

# Deterministic procedural base-color maps, all created by this file.
def grain_image(color, amount=9, size=512):
    noise = RNG.normal(0, amount, (size,size,1))
    v=np.clip(np.asarray(color)[None,None,:] + noise + RNG.normal(0,2,(size,size,3)),0,255).astype(np.uint8)
    return Image.fromarray(v,'RGB')

im=grain_image((188,174,149),5)
d=ImageDraw.Draw(im,'RGBA')
# Seven courses of ashlar with alternate staggered vertical joints.
for row in range(8):
    y=row*64
    d.line((0,y,511,y),fill=(92,81,68,130),width=3)
    d.line((0,y+3,511,y+3),fill=(243,229,201,105),width=1)
    for x in range(-128+(row%2)*128,640,256):
        d.line((x,y,x,y+63),fill=(94,82,67,105),width=2)
        d.line((x+3,y+2,x+3,y+62),fill=(240,226,199,65),width=1)
for _ in range(1100):
    x,y=RNG.integers(0,512,2); c=int(RNG.integers(30,75))
    d.point((int(x),int(y)),fill=(86,76,65,c))
im.save(TEX/'cut_stone.png')
im=grain_image((220,208,184),3)
d=ImageDraw.Draw(im,'RGBA')
for _ in range(250):
    x,y=RNG.integers(0,512,2)
    d.line((int(x),int(y),int(x)+int(RNG.integers(3,18)),int(y)),fill=(111,99,80,24),width=1)
im.save(TEX/'limestone_trim.png')

im=grain_image((58,64,69),7)
d=ImageDraw.Draw(im,'RGBA')
for y in range(0,512,128):
    d.line((0,y,511,y),fill=(25,28,32,100),width=3)
for row in range(4):
    for x in range((row%2)*128,512,256):d.line((x,row*128,x,row*128+127),fill=(30,33,36,100),width=2)
im.save(TEX/'slate_roof.png')

im=grain_image((42,49,48),3);im.save(TEX/'iron.png')
im=grain_image((115,83,47),4);im.save(TEX/'brass.png')
im=grain_image((101,56,33),5)
d=ImageDraw.Draw(im,'RGBA')
for x in range(0,512,64):
    d.line((x,0,x,511),fill=(52,28,16,110),width=2)
for _ in range(140):
    x=int(RNG.integers(0,512)); yy=int(RNG.integers(0,512))
    d.line((x,yy,x,yy+int(RNG.integers(15,110))),fill=(47,22,12,25),width=1)
im.save(TEX/'wood.png')

# Opaque glass deliberately retains a warm interior impression when viewed in
# engines that do not enable transmission; geometry is still physically recessed.
a=np.zeros((512,512,3),dtype=np.uint8)
for y in range(512):
    for x in range(512):
        n=float(RNG.normal(0,2)); glow=max(0,1-abs(x/512-.64)*2.2)*max(0,1-abs(y/512-.57)*2)
        a[y,x]=np.clip([93+56*glow+n,91+34*glow+n,72+15*glow+n],0,255)
im=Image.fromarray(a,'RGB');d=ImageDraw.Draw(im,'RGBA')
d.polygon([(80,0),(160,0),(40,512),(0,512)],fill=(179,194,188,22))
d.polygon([(310,0),(350,0),(240,512),(206,512)],fill=(220,218,195,20))
im.save(TEX/'glass.png')

im=Image.new('RGB',(512,512),(229,217,184));d=ImageDraw.Draw(im,'RGBA')
d.ellipse((5,5,507,507),fill=(229,217,184,255),outline=(59,52,43,255),width=12)
d.ellipse((20,20,492,492),outline=(135,113,76,255),width=3)
font_path='/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
font=ImageFont.truetype(font_path,31)
roman=['XII','I','II','III','IV','V','VI','VII','VIII','IX','X','XI']
for k,label in enumerate(roman):
    angle=math.radians(k*30-90);x=256+190*math.cos(angle);y=256+190*math.sin(angle)
    bbox=d.textbbox((0,0),label,font=font)
    d.text((x-(bbox[2]-bbox[0])/2,y-(bbox[3]-bbox[1])/2-bbox[1]),label,font=font,fill=(47,45,39,255))
for k in range(60):
    angle=math.radians(k*6-90);r0=151 if k%5==0 else 164;r1=176
    d.line((256+r0*math.cos(angle),256+r0*math.sin(angle),256+r1*math.cos(angle),256+r1*math.sin(angle)),fill=(70,59,43,255),width=4 if k%5==0 else 2)
# clock at about ten past ten
d.line((256,256,179,204),fill=(35,35,31,255),width=10)
d.line((256,256,337,138),fill=(35,35,31,255),width=7)
d.ellipse((247,247,265,265),fill=(59,48,32,255))
im.save(TEX/'clock_face.png')

class Builder:
    def __init__(self): self.v={};self.f={};self.uv={}
    def geom(self, mat, pts, faces, uv):
        if mat not in self.v:self.v[mat]=[];self.f[mat]=[];self.uv[mat]=[]
        offset=len(self.v[mat]);self.v[mat].extend(pts);self.uv[mat].extend(uv)
        self.f[mat].extend([[offset+i for i in face] for face in faces])
    def quad(self,mat,p,uv): self.geom(mat,p,[(0,1,2),(0,2,3)],uv)
    def tri(self,mat,p,uv): self.geom(mat,p,[(0,1,2)],uv)
B=Builder()
SCALE={'brick':(1.95,1.11),'stone':(2.4,2.0),'trim':(2,2),'slate':(2,2),'iron':(2,2),'wood':(1,2),'glass':(1.5,2.5),'brass':(2,2)}

def uv(mat, coords):
    a,b=SCALE.get(mat,(1,1))
    return [(u/a,v/b) for u,v in coords]

def transform(p, side):
    u,y,d=p
    if side=='front': return (u,y,d)
    if side=='right': return (10-d,y,u)
    if side=='left': return (-10+d,y,8-u)
    if side=='back': return (-u,y,8-d)
    raise ValueError(side)

def quad(mat, ps, side='front', coords=None):
    if coords is None: coords=[(p[0],p[1]) for p in ps]
    B.quad(mat,[transform(p,side) for p in ps],uv(mat,coords))

def box(mat,u0,u1,y0,y1,d0,d1,side='front'):
    if u1-u0<1e-5 or y1-y0<1e-5 or d1-d0<1e-5:return
    quad(mat,[(u0,y0,d0),(u0,y1,d0),(u1,y1,d0),(u1,y0,d0)],side)
    quad(mat,[(u1,y0,d1),(u1,y1,d1),(u0,y1,d1),(u0,y0,d1)],side)
    quad(mat,[(u0,y0,d1),(u0,y1,d1),(u0,y1,d0),(u0,y0,d0)],side,[(d1,y0),(d1,y1),(d0,y1),(d0,y0)])
    quad(mat,[(u1,y0,d0),(u1,y1,d0),(u1,y1,d1),(u1,y0,d1)],side,[(d0,y0),(d0,y1),(d1,y1),(d1,y0)])
    quad(mat,[(u0,y1,d0),(u0,y1,d1),(u1,y1,d1),(u1,y1,d0)],side,[(u0,d0),(u0,d1),(u1,d1),(u1,d0)])
    quad(mat,[(u0,y0,d1),(u0,y0,d0),(u1,y0,d0),(u1,y0,d1)],side,[(u0,d1),(u0,d0),(u1,d0),(u1,d1)])

def arch_wall(mat,u0,u1,y0,y1,d0,d1,holes,side='front',n=12):
    """Extruded wall with actual arched voids, not painted recesses."""
    last=u0
    for cx,r,bottom,spring in sorted(holes):
        left,right=cx-r,cx+r
        assert left>=last-1e-6 and right<=u1+1e-6 and spring+r<=y1+1e-6
        box(mat,last,left,y0,y1,d0,d1,side)
        box(mat,left,right,y0,bottom,d0,d1,side)
        # Each solid trapezoid starts exactly at the arch and rises to the wall top.
        xs=np.linspace(left,right,n+1)
        for a,b in zip(xs[:-1],xs[1:]):
            ya=spring+math.sqrt(max(0,r*r-(a-cx)**2));yb=spring+math.sqrt(max(0,r*r-(b-cx)**2))
            quad(mat,[(a,ya,d0),(a,y1,d0),(b,y1,d0),(b,yb,d0)],side)
            quad(mat,[(b,yb,d1),(b,y1,d1),(a,y1,d1),(a,ya,d1)],side)
            quad(mat,[(a,ya,d0),(b,yb,d0),(b,yb,d1),(a,ya,d1)],side,[(a,d0),(b,d0),(b,d1),(a,d1)])
            quad(mat,[(a,y1,d0),(a,y1,d1),(b,y1,d1),(b,y1,d0)],side,[(a,d0),(a,d1),(b,d1),(b,d0)])
        last=right
    box(mat,last,u1,y0,y1,d0,d1,side)

def ring(mat,cx,cy,ri,ro,d0,d1,side='front',n=20):
    angles=np.linspace(0,math.pi,n+1)
    for a,b in zip(angles[:-1],angles[1:]):
        ip=(cx+ri*math.cos(a),cy+ri*math.sin(a));jp=(cx+ri*math.cos(b),cy+ri*math.sin(b))
        op=(cx+ro*math.cos(a),cy+ro*math.sin(a));oq=(cx+ro*math.cos(b),cy+ro*math.sin(b))
        quad(mat,[(ip[0],ip[1],d0),(jp[0],jp[1],d0),(oq[0],oq[1],d0),(op[0],op[1],d0)],side)
        quad(mat,[(op[0],op[1],d0),(oq[0],oq[1],d0),(oq[0],oq[1],d1),(op[0],op[1],d1)],side)
        quad(mat,[(jp[0],jp[1],d0),(ip[0],ip[1],d0),(ip[0],ip[1],d1),(jp[0],jp[1],d1)],side)

def arched_plane(mat,cx,r,bottom,spring,d,side='front',n=20):
    # convex polygon; triangle fan begins at the lower-left corner
    poly=[(cx-r,bottom),(cx+r,bottom)]
    poly.extend((cx+r*math.cos(a),spring+r*math.sin(a)) for a in np.linspace(0,math.pi,n+1))
    for i in range(1,len(poly)-1):
        ps=[poly[0],poly[i+1],poly[i]]
        B.tri(mat,[transform((x,y,d),side) for x,y in ps],uv(mat,ps))

def bar(mat,a,b,width,d0,d1,side='front'):
    ax,ay=a;bx,by=b;dx=bx-ax;dy=by-ay;l=math.hypot(dx,dy)
    if l<1e-6:return
    ox=-dy/l*width/2;oy=dx/l*width/2
    q=[(ax-ox,ay-oy),(ax+ox,ay+oy),(bx+ox,by+oy),(bx-ox,by-oy)]
    quad(mat,[(x,y,d0) for x,y in q],side)
    for i in range(4):
        a=q[i];b=q[(i+1)%4]
        quad(mat,[(a[0],a[1],d0),(b[0],b[1],d0),(b[0],b[1],d1),(a[0],a[1],d1)],side)

def trim_arch(cx,r,bottom,spring,side='front',thick=.13):
    # Each surround is actual projecting limestone with an arched inner edge.
    ring('trim',cx,spring,r,r+thick,.04,.18,side,n=18)
    for s in [-1,1]:
        x=cx+s*(r+thick/2)
        box('trim',x-thick/2,x+thick/2,bottom,spring,.04,.20,side)
        box('trim',x-thick*.72,x+thick*.72,bottom,bottom+.13,.025,.21,side)
        box('trim',x-thick*.72,x+thick*.72,spring-.08,spring+.06,.025,.21,side)
    # Keystone at apex; individual voussoir joints are texture.
    box('trim',cx-.09,cx+.09,spring+r-.03,spring+r+thick+.08,.015,.18,side)

def window(cx,r,bottom,spring,side='front',door=False,small=False):
    arched_plane('glass',cx,r-.035,bottom+.04,spring,.49,side)
    # Frame, crossbars and fanlight ribs are real iron geometry.
    for s in [-1,1]:box('iron',cx+s*(r-.04)-.035,cx+s*(r-.04)+.035,bottom+.04,spring,.39,.47,side)
    ring('iron',cx,spring,r-.075,r-.005,.38,.47,side,n=18)
    box('iron',cx-r+.035,cx+r-.035,spring-.035,spring+.035,.37,.47,side)
    box('iron',cx-r+.035,cx+r-.035,bottom+.06,bottom+.12,.37,.47,side)
    for dx in ([-.5,0,.5] if not small else [0]):
        x=cx+r*dx
        box('iron',x-.023,x+.023,bottom+.1,spring,.37,.47,side)
    if not door:
        for h in [bottom+(spring-bottom)*.34,bottom+(spring-bottom)*.67]:
            box('iron',cx-r+.06,cx+r-.06,h-.022,h+.022,.37,.47,side)
    for a in np.linspace(.25*math.pi,.75*math.pi,3):
        bar('iron',(cx,spring),(cx+(r-.08)*math.cos(a),spring+(r-.08)*math.sin(a)),.035,.36,.46,side)
    if door:
        # Closed double doors have actual wood slabs and small glass lites.
        box('wood',cx-r+.075,cx+r-.075,bottom+.12,spring-.12,.30,.38,side)
        box('iron',cx-.025,cx+.025,bottom+.12,spring-.12,.26,.32,side)
        for s in [-1,1]:
            x=cx+s*r*.48
            box('glass',x-r*.29,x+r*.29,bottom+1.12,spring-.22,.26,.30,side)
            box('brass',x-.018,x+.018,bottom+.77,bottom+.88,.24,.29,side)
            # Shallow inset door panels are separate framed meshes.
            for yy in [bottom+.28,bottom+.70]:
                box('iron',x-r*.28,x+r*.28,yy,yy+.035,.26,.30,side)
                box('iron',x-r*.28,x-r*.28+.03,yy,yy+.30,.26,.30,side)
                box('iron',x+r*.28-.03,x+r*.28,yy,yy+.30,.26,.30,side)
                box('iron',x-r*.28,x+r*.28,yy+.27,yy+.30,.26,.30,side)

def lathe(mat,cx,cz,rings,segments=16):
    # axis Y, rings ordered bottom to top
    for (y0,r0),(y1,r1) in zip(rings[:-1],rings[1:]):
        for i in range(segments):
            a=i*2*math.pi/segments;b=(i+1)*2*math.pi/segments
            ps=[(cx+r0*math.cos(a),y0,cz+r0*math.sin(a)),(cx+r1*math.cos(a),y1,cz+r1*math.sin(a)),(cx+r1*math.cos(b),y1,cz+r1*math.sin(b)),(cx+r0*math.cos(b),y0,cz+r0*math.sin(b))]
            B.quad(mat,ps,uv(mat,[(i/segments,y0),(i/segments,y1),((i+1)/segments,y1),((i+1)/segments,y0)]))

def disk(mat,cx,cy,cz,radius,depth,segments=48,face_texture=False):
    # Front circular face points towards -Z; rear remains capped.
    for i in range(segments):
        a=2*math.pi*i/segments;b=2*math.pi*(i+1)/segments
        p=(cx+radius*math.cos(a),cy+radius*math.sin(a));q=(cx+radius*math.cos(b),cy+radius*math.sin(b))
        if face_texture:
            # Images are top-left-origin; UV v=1 at +Y.
            # The clock faces toward -Z: +X is screen-left from its front.
            uvs=[(.5,.5),(.5-.5*math.cos(b),.5+.5*math.sin(b)),(.5-.5*math.cos(a),.5+.5*math.sin(a))]
        else:uvs=uv(mat,[(cx,cy),q,p])
        B.tri(mat,[(cx,cy,cz),(q[0],q[1],cz),(p[0],p[1],cz)],uvs)
        quad(mat,[(p[0],p[1],cz),(q[0],q[1],cz),(q[0],q[1],cz+depth),(p[0],p[1],cz+depth)],'front')

def annular_disk(mat,cx,cy,cz,inner,outer,depth,segments=48):
    """A real open-centered bezel, avoiding overlapping coplanar clock faces."""
    for i in range(segments):
        a=2*math.pi*i/segments;b=2*math.pi*(i+1)/segments
        def p(r,t,z):return (cx+r*math.cos(t),cy+r*math.sin(t),z)
        ia,ib=p(inner,a,cz),p(inner,b,cz)
        oa,ob=p(outer,a,cz),p(outer,b,cz)
        iab,ibb=p(inner,a,cz+depth),p(inner,b,cz+depth)
        oab,obb=p(outer,a,cz+depth),p(outer,b,cz+depth)
        quad(mat,[ia,ib,ob,oa])
        quad(mat,[oab,obb,ibb,iab])
        quad(mat,[oa,ob,obb,oab])
        quad(mat,[ib,ia,iab,ibb])

# Ground level: nine front openings, with closed double doors in the three middle bays.
front_centers=[-8.8,-6.6,-4.4,-2.2,0,2.2,4.4,6.6,8.8]
holes=[(x,.66,.05,2.35) for x in front_centers]
arch_wall('stone',-10,10,0,4.05,.18,.67,holes)
for i,x in enumerate(front_centers):
    trim_arch(x,.66,.05,2.35,thick=.15)
    window(x,.66,.05,2.35,door=i in (3,4,5))
# Plinth and intermediate cornice are profiled physical masonry.
for x in [-10,-7.7,-5.5,-3.3,-1.1,1.1,3.3,5.5,7.7,10]:
    x0=max(-10,x-.17);x1=min(10,x+.17)
    box('trim',x0,x1,.03,.37,.02,.20)
    box('trim',x0+.045,x1-.045,.37,3.57,.055,.20)
    box('trim',x0,x1,3.57,3.75,.025,.22)
box('trim',-10,10,3.83,4.08,.03,.24)
box('trim',-10,10,4.08,4.22,.00,.26)
box('trim',-10,10,4.22,4.34,.045,.24)
# Repeating courses of small corbels beneath the cornice.
for x in np.linspace(-9.7,9.7,35):box('trim',x-.07,x+.07,3.69,3.84,.035,.22)

# Both return walls: physical openings continue along the station's depth.
for side in ['left','right']:
    hs=[(x,.61,.05,2.35) for x in [1.35,3.95,6.55]]
    arch_wall('stone',0,8,0,4.05,.18,.65,hs,side)
    for x in [1.35,3.95,6.55]:
        trim_arch(x,.61,.05,2.35,side,thick=.13);window(x,.61,.05,2.35,side)
    box('trim',0,8,3.83,4.10,.03,.25,side)
    box('trim',0,8,4.10,4.32,.0,.26,side)
    for x in np.linspace(.2,7.8,14):box('trim',x-.06,x+.06,3.7,3.84,.035,.2,side)
    # Upper return: tower end and two brick window bays.
    arch_wall('stone',0,2.1,4.34,8.95,.18,.65,[(1.0,.48,5.05,7.10)],side)
    trim_arch(1.0,.48,5.05,7.10,side);window(1.0,.48,5.05,7.10,side,small=True)
    arch_wall('brick',2.1,8,4.34,8.95,.18,.65,[(3.2,.48,5.05,7.10),(5.5,.48,5.05,7.10),(7.1,.42,5.05,7.10)],side)
    for x,r in [(3.2,.48),(5.5,.48),(7.1,.42)]:
        trim_arch(x,r,5.05,7.10,side);window(x,r,5.05,7.10,side,small=True)
    box('trim',0,8,8.70,8.91,.03,.25,side)
    box('trim',0,8,8.91,9.08,.0,.28,side)

# Upper brick wings with arched recesses. Every black line inside is physical iron.
for lo,hi,centers in [(-8,-3.45,[-6.8,-4.6]),(3.45,8,[4.6,6.8])]:
    hs=[(x,.49,5.05,7.10) for x in centers]
    arch_wall('brick',lo,hi,4.34,8.83,.18,.65,hs)
    for x in centers:
        trim_arch(x,.49,5.05,7.10,thick=.12);window(x,.49,5.05,7.10,small=True)
        box('trim',x-.66,x+.66,4.90,5.06,.02,.23)
    box('trim',lo,hi,8.51,8.68,.05,.24)
    box('trim',lo,hi,8.68,8.88,.00,.26)
    # a delicate, solid balustrade silhouette along the roofline
    box('trim',lo,hi,9.08,9.16,.03,.20)
    for x in np.arange(lo+.13,hi,.30):box('trim',x,x+.07,8.87,9.08,.05,.16)
    for x in [lo+.12,(lo+hi)*.5,hi-.12]:
        box('trim',x-.09,x+.09,5.0,8.50,.055,.20)
        box('trim',x-.13,x+.13,4.84,5.03,.025,.22)
        box('trim',x-.13,x+.13,8.34,8.52,.025,.22)

# Front tower bases, square corner masonry, and arched upper windows.
for lo,hi,cx in [(-10,-8,-9),(8,10,9)]:
    arch_wall('stone',lo,hi,4.34,8.8,.18,2.45,[(cx,.48,5.05,7.10)])
    trim_arch(cx,.48,5.05,7.10,thick=.12);window(cx,.48,5.05,7.10,small=True)
    box('trim',lo,hi,8.55,8.75,.02,.27)
    box('trim',lo,hi,8.75,8.96,0,.30)
    arch_wall('stone',lo,hi,8.96,10.43,.18,2.40,[(cx,.38,9.15,9.73)])
    trim_arch(cx,.38,9.15,9.73,thick=.10);window(cx,.38,9.15,9.73,small=True)
    box('trim',lo,hi,10.30,10.49,.02,.32)
    box('trim',lo,hi,10.49,10.66,0,.33)
    for x in [lo+.16,hi-.16]:
        box('trim',x-.13,x+.13,4.34,10.32,.025,.22)
        for y in np.arange(4.40,10.30,.55):box('stone',x-.16,x+.16,y,y+.06,.01,.20)
    # Slate dome is a low-poly surface of revolution with modeled ribs.
    box('stone',lo+.12,hi-.12,10.65,10.84,.18,2.3)
    dome_cx=cx;dome_cz=1.24
    rings=[(10.80,.90),(10.93,.94),(11.17,.90),(11.40,.81),(11.62,.68),(11.80,.50),(11.92,.31),(11.98,.19)]
    lathe('slate',dome_cx,dome_cz,rings,segments=20)
    for j in range(10):
        a=2*math.pi*j/10
        # dark standing seams actually rise above the dome rather than being painted.
        for (y0,r0),(y1,r1) in zip(rings[:-1],rings[1:]):
            x0=dome_cx+r0*math.cos(a);z0=dome_cz+r0*math.sin(a)
            x1=dome_cx+r1*math.cos(a);z1=dome_cz+r1*math.sin(a)
            tang=(-math.sin(a)*.016,math.cos(a)*.016)
            pts=[(x0+tang[0],y0+.01,z0+tang[1]),(x0-tang[0],y0+.01,z0-tang[1]),(x1-tang[0],y1+.01,z1-tang[1]),(x1+tang[0],y1+.01,z1+tang[1])]
            B.quad('iron',pts,uv('iron',[(0,y0),(.04,y0),(.04,y1),(0,y1)]))
    lathe('iron',dome_cx,dome_cz,[(11.94,.22),(12.02,.22),(12.08,.14)],segments=12)
    lathe('brass',dome_cx,dome_cz,[(12.08,.11),(12.14,.11),(12.22,.045),(12.43,.02),(12.50,.0)],segments=10)
    # Round dormer on each front dome: actual nested circular meshes.
    disk('brass',dome_cx,11.23,.285,.19,.10,segments=20)
    disk('iron',dome_cx,11.23,.27,.14,.025,segments=20)
    disk('glass',dome_cx,11.23,.26,.105,.018,segments=20)

# Central vaulted brick tympanum and great semicircular glazed opening.
# Piers and an annular arch leave an actual aperture through the front wall.
box('brick',-3.45,-2.45,4.34,7.55,.18,.68)
box('brick',2.45,3.45,4.34,7.55,.18,.68)
ring('brick',0,7.55,2.45,3.45,.18,.68,n=32)
ring('trim',0,7.55,3.26,3.52,.02,.20,n=32)
ring('trim',0,7.55,2.43,2.56,.04,.20,n=32)
ring('trim',0,7.55,3.48,3.60,.00,.12,n=32)
# Archway uprights and stone courses.
for s in [-1,1]:
    x=s*3.37
    box('trim',x-.16,x+.16,4.34,7.56,.01,.24)
    box('trim',x-.22,x+.22,4.34,4.62,0,.26)
    box('trim',x-.21,x+.21,7.39,7.62,0,.25)
    x=s*2.50
    box('trim',x-.08,x+.08,4.66,7.55,.04,.20)
# Great window, opaque tinted glass in a physically recessed arched plane.
arched_plane('glass',0,2.40,4.66,7.55,.50,n=40)
ring('iron',0,7.55,2.32,2.40,.35,.49,n=36)
for x in np.arange(-2.4,2.401,.60):
    if abs(x)<2.4:
        top=7.55+math.sqrt(max(0,2.32**2-x**2))
        box('iron',x-.035,x+.035,4.70,top,.34,.47)
for y in [4.73,5.35,5.97,6.59,7.21,7.56,8.12,8.65,9.18]:
    r=2.30 if y<=7.55 else math.sqrt(max(0,2.30**2-(y-7.55)**2))
    if r>.1:box('iron',-r,r,y-.028,y+.028,.33,.46)
# Small framing edge where glazing meets lower horizontal sill.
box('trim',-2.60,2.60,4.50,4.70,.01,.29)
box('iron',-2.40,2.40,4.70,4.77,.12,.24)

# Center clock: modeled circular casings with a generated clock-face texture.
annular_disk('iron',0,9.35,.005,.73,.82,.13)
annular_disk('brass',0,9.35,.001,.655,.73,.03)
disk('clock',0,9.35,0,.655,.012,face_texture=True)
# Crown above the arch, and four carved-looking corner finials.
box('trim',-.60,.60,11.02,11.22,.02,.45)
box('trim',-.42,.42,11.22,11.42,.04,.38)
box('trim',-.27,.27,11.42,11.58,.06,.32)
lathe('trim',0,.19,[(11.58,.17),(11.68,.17),(11.80,.085)],segments=10)
lathe('brass',0,.19,[(11.80,.08),(11.86,.05),(12.10,0)],segments=10)
for x in [-3.55,3.55]:
    box('trim',x-.22,x+.22,8.38,9.13,.02,.34)
    box('trim',x-.25,x+.25,9.13,9.28,0,.36)
    lathe('trim',x,.18,[(9.28,.15),(9.38,.15),(9.54,.08),(9.64,0)],segments=10)

# Rest of the building body: a restrained roof and rear elevation, providing a
# complete module rather than an unbacked front card.
box('slate',-9.92,9.92,8.82,8.98,.30,7.92)
backholes=[(x,.64,.05,2.35) for x in [-8,-4,0,4,8]]
arch_wall('stone',-10,10,0,4.05,.18,.67,backholes,'back')
for x in [-8,-4,0,4,8]:
    trim_arch(x,.64,.05,2.35,'back',thick=.13);window(x,.64,.05,2.35,'back')
box('trim',-10,10,4.05,4.34,.00,.26,'back')
arch_wall('brick',-10,10,4.34,8.83,.18,.65,[(x,.47,5.05,7.10) for x in [-8,-4,0,4,8]],'back')
for x in [-8,-4,0,4,8]:
    trim_arch(x,.47,5.05,7.10,'back',thick=.12);window(x,.47,5.05,7.10,'back',small=True)
box('trim',-10,10,8.70,8.90,.03,.25,'back')
box('trim',-10,10,8.90,9.05,.0,.26,'back')

images={'brick':'ai_victorian_brick.png','stone':'ai_victorian_stone.png','trim':'limestone_trim.png','slate':'slate_roof.png','iron':'iron.png','wood':'wood.png','glass':'glass.png','brass':'brass.png','clock':'clock_face.png'}
scene=trimesh.Scene(base_frame='world')
for name in images:
    # The outward-facing clock dial has correct -Z normals. Keeping it
    # single-sided prevents its front from self-shadowing in Three.js's
    # standard back-face shadow pass; other building surfaces stay double-sided.
    mat=trimesh.visual.material.PBRMaterial(name=name,baseColorTexture=Image.open(TEX/images[name]),metallicFactor=.5 if name in ('iron','brass') else 0,roughnessFactor=.38 if name=='glass' else .82,doubleSided=name!='clock')
    mesh=trimesh.Trimesh(vertices=np.asarray(B.v[name],dtype=np.float32),faces=np.asarray(B.f[name],dtype=np.int64),process=False)
    mesh.visual=trimesh.visual.TextureVisuals(uv=np.asarray(B.uv[name],dtype=np.float32),material=mat)
    # Pointed finial tips naturally create zero-area fan triangles; discard
    # them and their unreferenced vertices before calculating explicit normals.
    mesh.update_faces(mesh.area_faces > 1e-10)
    mesh.remove_unreferenced_vertices()
    _=mesh.vertex_normals
    scene.add_geometry(mesh,geom_name=name,node_name=name)
path=ROOT/'station_facade.glb'
path.write_bytes(scene.export(file_type='glb'))
loaded=trimesh.load(path,force='scene',process=False)
summary={'file':str(path),'bounds_m':loaded.bounds.tolist(),'geometry_meshes':len(loaded.geometry),'materials':[g.visual.material.name for g in loaded.geometry.values()],'triangles':sum(len(g.faces) for g in loaded.geometry.values()),'vertices':sum(len(g.vertices) for g in loaded.geometry.values())}
(ROOT/'model_stats.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
