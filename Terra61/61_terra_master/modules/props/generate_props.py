#!/usr/bin/env python3
"""Create five Y-up metre-scale Victorian station prop modules as embedded GLBs."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import trimesh, math, json, shutil

ROOT=Path(__file__).resolve().parent
TEX=ROOT/'textures';TEX.mkdir(exist_ok=True)
IRON_SRC=ROOT.parents[1]/'materials'/'ai_aged_cast_iron.png'
if IRON_SRC.exists():
    # Optimized, visibly equivalent copy of the supplied generated base-color texture.
    Image.open(IRON_SRC).convert('RGB').resize((768,576),Image.Resampling.LANCZOS).save(TEX/'ai_aged_cast_iron_768.png')
elif not (TEX/'ai_aged_cast_iron_768.png').exists():raise FileNotFoundError('ai_aged_cast_iron.png')
RNG=np.random.default_rng(345179)
def noisy(color,noise=5,size=512):
    a=RNG.normal(0,noise,(size,size,1))+RNG.normal(0,2,(size,size,3))+np.array(color)[None,None,:]
    return Image.fromarray(np.clip(a,0,255).astype('uint8'),'RGB')

# Wood: low-frequency directional grain over warm plank color.
im=noisy((123,78,45),5); d=ImageDraw.Draw(im,'RGBA')
for _ in range(600):
    y=int(RNG.integers(0,512));x=int(RNG.integers(-100,512));w=int(RNG.integers(15,140))
    shade=int(RNG.integers(20,75));d.line((x,y,x+w,y+int(RNG.integers(-1,2))),fill=(55,26,12,shade),width=int(RNG.integers(1,3)))
for _ in range(15):
    x,y=RNG.integers(0,512,2);d.ellipse((int(x)-8,int(y)-2,int(x)+8,int(y)+2),outline=(57,28,13,90),width=1)
im.save(TEX/'wood_grain.png')
im=noisy((91,47,27),7);d=ImageDraw.Draw(im,'RGBA')
for _ in range(160):
    x,y=RNG.integers(0,512,2);d.line((int(x),int(y),int(x)+int(RNG.integers(2,15)),int(y)+int(RNG.integers(-5,6))),fill=(201,136,88,28),width=1)
im.save(TEX/'worn_leather.png')
im=noisy((159,121,65),4);im.save(TEX/'aged_brass.png')
im=noisy((193,175,138),4);im.save(TEX/'stone.png')
im=noisy((60,69,71),4);im.save(TEX/'dark_roof.png')
# warm frosted pane with a flame painted into each physical lantern pane
im=Image.new('RGB',(256,256));a=np.zeros((256,256,3),dtype='uint8')
for y in range(256):
 for x in range(256):
    glow=max(0,1-math.sqrt(((x-128)/125)**2+((y-130)/150)**2));n=RNG.normal(0,1.8)
    a[y,x]=np.clip([162+85*glow+n,116+106*glow+n,56+96*glow+n],0,255)
im=Image.fromarray(a);d=ImageDraw.Draw(im,'RGBA')
d.polygon([(128,34),(113,91),(111,120),(118,137),(127,141),(139,133),(145,112),(140,91)],fill=(255,245,193,220))
d.polygon([(128,69),(122,103),(123,123),(128,132),(134,122),(135,104)],fill=(255,255,235,235))
im.save(TEX/'lantern_glow.png')
# Painted iron canopy frieze: graphic ornament is intentionally texture, not geometry.
im=Image.new('RGB',(512,128),(37,43,43));d=ImageDraw.Draw(im,'RGBA')
d.line((0,7,511,7),fill=(187,140,73,210),width=3);d.line((0,119,511,119),fill=(187,140,73,180),width=3)
for x in range(0,513,128):
    d.arc((x-65,18,x+65,109),190,350,fill=(181,136,74,200),width=3)
    d.arc((x-34,29,x+34,94),10,250,fill=(181,136,74,200),width=3)
    d.ellipse((x-4,59,x+4,67),fill=(214,173,102,220))
    d.line((x+63,12,x+63,115),fill=(132,111,76,130),width=2)
im.save(TEX/'canopy_frieze.png')
# Supplied façade generator made this Roman-numeral face procedurally.
clock_src=ROOT.parent/'facade'/'textures'/'clock_face.png'
if clock_src.exists():shutil.copy2(clock_src,TEX/'clock_face.png')
else:
    im=Image.new('RGB',(512,512),(224,213,185));d=ImageDraw.Draw(im)
    d.ellipse((5,5,507,507),outline=(55,50,41),width=12)
    f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',32)
    for k,s in enumerate(['XII','I','II','III','IV','V','VI','VII','VIII','IX','X','XI']):
        a=math.radians(k*30-90);p=(256+190*math.cos(a),256+190*math.sin(a));d.text(p,s,font=f,fill=(40,38,33),anchor='mm')
    d.line((256,256,177,198),fill=(35,35,31),width=10);d.line((256,256,333,138),fill=(35,35,31),width=7)
    im.save(TEX/'clock_face.png')

SCALES={'iron':(.8,.8),'brass':(.6,.6),'wood':(1.1,.55),'leather':(.6,.6),'stone':(1,1),'roof':(1.5,1.5),'glow':(1,1),'frieze':(2,.2),'clock':(1,1)}
FILES={'iron':'ai_aged_cast_iron_768.png','wood':'wood_grain.png','leather':'worn_leather.png','brass':'aged_brass.png','stone':'stone.png','roof':'dark_roof.png','glow':'lantern_glow.png','frieze':'canopy_frieze.png','clock':'clock_face.png'}

def norm(v):
    v=np.array(v,dtype=float);return v/np.linalg.norm(v)
class Bank:
    def __init__(self):self.v={};self.f={};self.uv={}
    def add(self,mat,pts,faces,uvs):
        self.v.setdefault(mat,[]);self.f.setdefault(mat,[]);self.uv.setdefault(mat,[]);i=len(self.v[mat]);self.v[mat].extend(pts);self.uv[mat].extend(uvs);self.f[mat].extend([[i+x for x in face] for face in faces])
    def quad(self,mat,pts,uvs=None):
        if uvs is None:
            n=np.cross(np.subtract(pts[1],pts[0]),np.subtract(pts[2],pts[0]));axis=int(np.argmax(np.abs(n)));indices=[(2,1),(0,2),(0,1)][axis]
            sc=SCALES.get(mat,(1,1));uvs=[(p[indices[0]]/sc[0],p[indices[1]]/sc[1]) for p in pts]
        self.add(mat,pts,[(0,1,2),(0,2,3)],uvs)
    def tri(self,mat,pts,uvs):self.add(mat,pts,[(0,1,2)],uvs)
    def box(self,mat,x0,x1,y0,y1,z0,z1):
        if min(x1-x0,y1-y0,z1-z0)<1e-6:return
        self.quad(mat,[(x0,y0,z0),(x0,y1,z0),(x1,y1,z0),(x1,y0,z0)])
        self.quad(mat,[(x1,y0,z1),(x1,y1,z1),(x0,y1,z1),(x0,y0,z1)])
        self.quad(mat,[(x0,y0,z1),(x0,y1,z1),(x0,y1,z0),(x0,y0,z0)])
        self.quad(mat,[(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)])
        self.quad(mat,[(x0,y1,z0),(x0,y1,z1),(x1,y1,z1),(x1,y1,z0)])
        self.quad(mat,[(x0,y0,z1),(x0,y0,z0),(x1,y0,z0),(x1,y0,z1)])
    def lathe(self,mat,cx,cz,rings,n=12):
        for (y0,r0),(y1,r1) in zip(rings[:-1],rings[1:]):
            for i in range(n):
                a=2*math.pi*i/n;b=2*math.pi*(i+1)/n
                ps=[(cx+r0*math.cos(a),y0,cz+r0*math.sin(a)),(cx+r1*math.cos(a),y1,cz+r1*math.sin(a)),(cx+r1*math.cos(b),y1,cz+r1*math.sin(b)),(cx+r0*math.cos(b),y0,cz+r0*math.sin(b))]
                self.quad(mat,ps,[(i/n,y0), (i/n,y1),((i+1)/n,y1),((i+1)/n,y0)])
    def rod(self,mat,p0,p1,r=.02,n=8):
        p0=np.array(p0,float);p1=np.array(p1,float);d=norm(p1-p0);ref=np.array([0.,1.,0.]) if abs(d[1])<.9 else np.array([1.,0.,0.]);e1=norm(np.cross(d,ref));e2=norm(np.cross(d,e1))
        for i in range(n):
            a=2*math.pi*i/n;b=2*math.pi*(i+1)/n;v0=r*(math.cos(a)*e1+math.sin(a)*e2);v1=r*(math.cos(b)*e1+math.sin(b)*e2)
            self.quad(mat,[p0+v0,p1+v0,p1+v1,p0+v1],[(i/n,0),(i/n,1),((i+1)/n,1),((i+1)/n,0)])
    def ring_z(self,mat,cx,cy,z0,z1,ri,ro,n=20):
        for i in range(n):
            a=2*math.pi*i/n;b=2*math.pi*(i+1)/n
            def p(r,t,z):return (cx+r*math.cos(t),cy+r*math.sin(t),z)
            self.quad(mat,[p(ri,a,z0),p(ri,b,z0),p(ro,b,z0),p(ro,a,z0)])
            self.quad(mat,[p(ro,a,z1),p(ro,b,z1),p(ri,b,z1),p(ri,a,z1)])
            self.quad(mat,[p(ro,a,z0),p(ro,b,z0),p(ro,b,z1),p(ro,a,z1)])
            self.quad(mat,[p(ri,b,z0),p(ri,a,z0),p(ri,a,z1),p(ri,b,z1)])
    def face_z(self,mat,cx,cy,z,r,n=32,faceuv=True):
        for i in range(n):
            a=2*math.pi*i/n;b=2*math.pi*(i+1)/n
            p=(cx+r*math.cos(a),cy+r*math.sin(a),z);q=(cx+r*math.cos(b),cy+r*math.sin(b),z)
            # A front clock face points toward -Z. Reverse U so its numerals
            # are legible from that side; the rear face keeps the other hand.
            flip=-1 if mat=='clock' and z<0 else 1
            self.tri(mat,[(cx,cy,z),q,p],[(.5,.5),(.5+flip*.5*math.cos(b),.5+.5*math.sin(b)),(.5+flip*.5*math.cos(a),.5+.5*math.sin(a))] if faceuv else [(0,0),(1,0),(0,1)])
    def ring_x(self,mat,x0,x1,cy,cz,ri,ro,n=20):
        for i in range(n):
            a=2*math.pi*i/n;b=2*math.pi*(i+1)/n
            def p(r,t,x):return (x,cy+r*math.sin(t),cz+r*math.cos(t))
            self.quad(mat,[p(ri,a,x0),p(ri,b,x0),p(ro,b,x0),p(ro,a,x0)])
            self.quad(mat,[p(ro,a,x1),p(ro,b,x1),p(ri,b,x1),p(ri,a,x1)])
            self.quad(mat,[p(ro,a,x0),p(ro,b,x0),p(ro,b,x1),p(ro,a,x1)])
            self.quad(mat,[p(ri,b,x0),p(ri,a,x0),p(ri,a,x1),p(ri,b,x1)])
    def polyline(self,mat,pts,r=.02,n=6):
        for a,b in zip(pts[:-1],pts[1:]):self.rod(mat,a,b,r,n)
    def export(self,name):
        scene=trimesh.Scene(base_frame='world')
        for mat in self.v:
            material=trimesh.visual.material.PBRMaterial(name=mat,baseColorTexture=Image.open(TEX/FILES[mat]),metallicFactor=.6 if mat in ['iron','brass','frieze'] else 0,roughnessFactor=.85,doubleSided=True,emissiveFactor=np.array([.28,.13,.025]) if mat=='glow' else None)
            mesh=trimesh.Trimesh(vertices=np.asarray(self.v[mat],np.float32),faces=np.asarray(self.f[mat],np.int64),process=False)
            mesh.visual=trimesh.visual.TextureVisuals(uv=np.asarray(self.uv[mat],np.float32),material=material)
            mesh.update_faces(mesh.area_faces>1e-10);mesh.remove_unreferenced_vertices();_=mesh.vertex_normals
            scene.add_geometry(mesh,geom_name=mat,node_name=mat)
        path=ROOT/(name+'.glb');path.write_bytes(scene.export(file_type='glb'))
        loaded=trimesh.load(path,force='scene',process=False)
        summary={'file':name+'.glb','bounds_m':np.round(loaded.bounds,5).tolist(),'triangles':sum(len(m.faces) for m in loaded.geometry.values()),'vertices':sum(len(m.vertices) for m in loaded.geometry.values()),'materials':list(loaded.geometry)}
        print(json.dumps(summary),flush=True)
        return summary

stats={}
# 1. Free-standing gas lamp: square pedestal, fluted pole, tapered 4-sided lantern.
b=Bank()
b.box('iron',-.25,.25,0,.08,-.25,.25);b.box('iron',-.21,.21,.08,.16,-.21,.21)
b.box('iron',-.17,.17,.16,.52,-.17,.17);b.box('iron',-.20,.20,.52,.60,-.20,.20)
for z in [-.174,.174]:b.box('brass',-.115,.115,.22,.24,z-.003,z+.003)
b.lathe('iron',0,0,[(.60,.16),(.66,.17),(.73,.11),(.83,.105),(2.26,.075),(2.37,.11),(2.44,.14),(2.52,.10),(2.58,.08)],12)
for j in range(8):
 a=2*math.pi*j/8;b.rod('iron',(.086*math.cos(a),.82,.086*math.sin(a)),(.062*math.cos(a),2.27,.062*math.sin(a)),.009,6)
b.lathe('brass',0,0,[(.66,.14),(.69,.14),(.72,.11)],12)
b.lathe('iron',0,0,[(2.56,.09),(2.61,.14),(2.66,.14)],12)
# Lantern sides taper toward the lower platform. The glowing pane is opaque and textured.
y0,y1=2.64,3.15;bottom=.19;top=.30
for side in range(4):
 a=side*math.pi/2+math.pi/4;c=(side+1)*math.pi/2+math.pi/4
 def corner(rad,ang,y):return (rad*math.cos(ang),y,rad*math.sin(ang))
 p0=corner(bottom,a,y0);p1=corner(top,a,y1);p2=corner(top,c,y1);p3=corner(bottom,c,y0)
 b.quad('glow',[p0,p1,p2,p3],[(0,0),(0,1),(1,1),(1,0)])
 b.rod('iron',p0,p1,.018,6);b.rod('iron',p0,p3,.016,6);b.rod('iron',p1,p2,.018,6)
b.lathe('iron',0,0,[(3.15,.33),(3.20,.33),(3.24,.27),(3.34,.10),(3.38,.08)],4)
b.lathe('brass',0,0,[(3.38,.09),(3.43,.09),(3.49,.045),(3.56,0)],10)
stats['station_lamp']=b.export('station_lamp')

# 2. Park/station bench: slatted wood over two cast-iron side frames.
b=Bank()
for z in [-.30,-.15,0,.15]:b.box('wood',-.94,.94,.43,.48,z-.065,z+.065)
for i in range(5):
 y=.53+i*.115;b.box('wood',-.94,.94,y,y+.09,.285,.33)
for x in [-.91,.91]:
 # decorative side silhouette and actual feet
 for z in [-.28,.27]:
  b.box('iron',x-.07,x+.07,0,.045,z-.08,z+.08)
  b.rod('iron',(x,.04,z),(x,.43,z),.035,8)
 b.rod('iron',(x,.43,-.31),(x,.43,.32),.026,8)
 b.rod('iron',(x,.43,.29),(x,1.08,.30),.035,8)
 b.polyline('iron',[(x,.60,-.31),(x,.66,-.35),(x,.71,-.30),(x,.72,-.18),(x,.72,.04),(x,.78,.22),(x,1.09,.30)],.026,8)
 b.polyline('iron',[(x,.08,-.25),(x,.22,-.14),(x,.29,0),(x,.22,.14),(x,.08,.24)],.022,8)
 b.ring_x('iron',x-.025,x+.025,.62,-.03,.085,.105,16)
 for j in range(6):
  a=j*math.pi/3;b.rod('iron',(x,.62,-.03),(x,.62+.08*math.sin(a),-.03+.08*math.cos(a)),.01,6)
 b.rod('brass',(x-.04,.62,-.03),(x+.04,.62,-.03),.027,8)
stats['station_bench']=b.export('station_bench')

# 3. Four-wheeled wooden luggage trolley with three separate-looking fixed trunks.
b=Bank()
b.box('iron',-.98,.98,.36,.42,-.39,.39)
for z in [-.31,-.15,.01,.17,.33]:b.box('wood',-.98,.98,.42,.49,z-.07,z+.07)
for x in [-.73,.73]:
 for z in [-.36,.36]:
  b.ring_z('iron',x,.235,z-.038,z+.038,.19,.235,16)
  b.face_z('brass',x,.235,z-.042,.045,12)
  for j in range(6):
   a=j*math.pi/3;b.rod('iron',(x,.235,z),(x+.19*math.cos(a),.235+.19*math.sin(a),z),.016,6)
  b.rod('iron',(x,.235,z),(x,.40,z),.035,8)
for x in [-.93,.93]:
 for z in [-.34,.34]:b.rod('iron',(x,.43,z),(x,1.02,z),.032,8)
 b.rod('wood',(x,1.02,-.34),(x,1.02,.34),.035,10)
 b.rod('iron',(x,.67,-.34),(x,.67,.34),.022,6)
def trunk(x0,x1,z0,z1,y0,y1):
 b.box('leather',x0,x1,y0,y1,z0,z1)
 # iron/brass binding uses simple strips and physically protruding corner caps
 for x in [x0+.12,x1-.12]:
  b.box('wood',x-.025,x+.025,y0,y1+.008,z0-.006,z1+.006)
  b.box('brass',x-.032,x+.032,(y0+y1)/2-.03,(y0+y1)/2+.03,z0-.012,z0-.006)
 for x in [x0,x1-.055]:
  for z in [z0,z1-.055]:b.box('brass',x,x+.055,y1-.055,y1+.006,z,z+.055)
 # front latch and top seam
 b.box('brass',(x0+x1)/2-.045,(x0+x1)/2+.045,(y0+y1)/2-.04,(y0+y1)/2+.04,z0-.015,z0-.005)
 b.box('iron',x0+.02,x1-.02,y1-.13,y1-.115,z0-.008,z0-.001)
 c=(x0+x1)*.5;h=y0+(y1-y0)*.34
 b.polyline('iron',[(c-.09,h+.04,z0-.016),(c-.09,h,z0-.035),(c+.09,h,z0-.035),(c+.09,h+.04,z0-.016)],.012,6)
trunk(-.78,-.05,-.26,.23,.50,1.00)
trunk(-.30,.48,-.34,.02,.50,.82)
trunk(.53,.85,-.18,.22,.50,.88)
stats['luggage_trolley']=b.export('luggage_trolley')

# 4. Ornamental wall clock. Pivot y=0 at the lowest finial; hanging height is up to the assembler.
b=Bank();cx=.20;cy=.88
b.box('iron',-.67,-.58,.12,1.66,-.05,.05)
b.box('brass',-.69,-.56,.12,.16,-.07,.07);b.box('brass',-.69,-.56,1.61,1.66,-.07,.07)
b.rod('iron',(-.62,1.50,0),(.2,1.50,0),.025,8)
b.rod('iron',(-.62,.25,0),(.2,.25,0),.025,8)
for y,sign in [(1.25,1),(.49,-1)]:
 pts=[]
 for a in np.linspace(math.pi,math.pi+1.45*math.pi,14):
  r=.22*(1-(a-math.pi)/(1.45*math.pi)*.6);pts.append((-.40+r*math.cos(a),y+sign*r*math.sin(a),0))
 b.polyline('iron',pts,.018,6)
b.ring_z('iron',cx,cy,-.13,.13,.50,.59,32)
b.ring_z('brass',cx,cy,-.145,-.125,.485,.53,32)
b.face_z('clock',cx,cy,-.15,.487,48)
b.face_z('clock',cx,cy,.135,.487,48)
for j in range(8):
 a=j*math.pi/4;x=cx+.55*math.cos(a);y=cy+.55*math.sin(a)
 b.face_z('brass',x,y,-.15,.025,8)
b.lathe('brass',cx,0,[(.15,.06),(.10,.07),(.04,.03),(0,0)],10)
b.rod('iron',(cx,.14,0),(cx,.31,0),.035,8)
b.lathe('brass',cx,0,[(1.46,.05),(1.54,.08),(1.61,.05),(1.68,0)],10)
stats['wall_clock']=b.export('wall_clock')

# 5. Front canopy: origin matches facade, full X width, projects toward -Z.
b=Bank()
# canopy roof 4.00 m at front to 4.09 m against the façade
roof=[(-10,4.00,-2.5),(-10,4.09,0),(10,4.09,0),(10,4.00,-2.5)]
b.quad('roof',roof,[(-5,0),(-5,1.67),(5,1.67),(5,0)])
b.quad('roof',[(-10,3.97,-2.5),(10,3.97,-2.5),(10,4.06,0),(-10,4.06,0)])
b.box('iron',-10,10,3.80,4.00,-2.49,-2.39)
b.box('iron',-10,10,3.90,4.09,-.12,0)
b.box('iron',-10,10,3.78,3.84,-2.49,-2.37)
# Decorative flat frieze on front fascia; repeated scrolls are texture.
b.quad('frieze',[(-10,3.81,-2.495),(-10,3.98,-2.495),(10,3.98,-2.495),(10,3.81,-2.495)],[(0,0),(0,1),(10,1),(10,0)])
posts=[-9.4,-7.7,-5.5,-3.3,-1.1,1.1,3.3,5.5,7.7,9.4]
for x in posts:
 z=-2.21
 b.box('iron',x-.14,x+.14,0,.08,z-.14,z+.14)
 b.box('iron',x-.11,x+.11,.08,.23,z-.11,z+.11)
 b.lathe('iron',x,z,[(.23,.10),(.30,.10),(.35,.072),(3.28,.055),(3.36,.09),(3.44,.095),(3.52,.06)],10)
 b.box('brass',x-.10,x+.10,.29,.32,z-.10,z+.10)
 b.box('iron',x-.15,x+.15,3.48,3.58,z-.15,z+.15)
 b.box('iron',x-.065,x+.065,3.58,3.94,-2.40,-.05)
 # Curved braces on the front elevation and front-to-wall return.
 for sign in [-1,1]:
  pts=[]
  for t in np.linspace(0,1,7):pts.append((x+sign*.54*t,3.05+.68*(1-(1-t)**2),z))
  b.polyline('iron',pts,.018,6)
  for t in [.38,.68]:
   xx=x+sign*.54*t;yy=3.05+.68*(1-(1-t)**2)
   b.rod('iron',(xx,yy,z),(xx,3.80,z),.010,6)
 pts=[]
 for t in np.linspace(0,1,7):pts.append((x,3.10+.68*(1-(1-t)**2),z+1.45*t))
 b.polyline('iron',pts,.018,6)
 # Rear braces continue into the facade anchor line.
 b.rod('iron',(x,3.78,-.75),(x,4.02,-.10),.018,6)
# Additional roof crossbeams and restrained accent rivets.
for z in [-1.7,-.9]:b.box('iron',-10,10,3.97,4.01,z-.025,z+.025)
for x in [-8.55,-6.6,-4.4,-2.2,0,2.2,4.4,6.6,8.55]:
 # Low-poly hanging gas pendants. The glow is an emissive opaque texture,
 # not a source of real light; an engine light can be added if desired.
 z=-1.35
 b.rod('iron',(x,3.96,z),(x,3.68,z),.012,6)
 b.lathe('iron',x,z,[(3.64,.075),(3.68,.075)],8)
 b.lathe('glow',x,z,[(3.48,.045),(3.52,.085),(3.62,.085),(3.66,.055)],8)
 b.lathe('iron',x,z,[(3.47,.035),(3.49,.055),(3.51,.065)],8)
for x in np.arange(-9.5,9.6,.5):
 b.face_z('brass',x,3.895,-2.498,.018,6)
stats['facade_canopy']=b.export('facade_canopy')
(ROOT/'model_stats.json').write_text(json.dumps(stats,indent=2)+'\n')
