import bpy, math, random, json, time, struct, zlib
from pathlib import Path
from mathutils import Vector, Matrix

START=time.time()
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max')
ART=ROOT/'SourceArt'; ART.mkdir(exist_ok=True)
FBX=ART/'Meshes'; FBX.mkdir(exist_ok=True)
TEX=ART/'Textures'; TEX.mkdir(exist_ok=True)
random.seed(741903)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC'; bpy.context.scene.unit_settings.scale_length=1.0
PALETTE={
 'Limestone':((0.60,0.66,0.68),0.90,0.0,'stone'),
 'StoneDark':((0.22,0.29,0.38),0.94,0.0,'stone'),
 'RockBlue':((0.20,0.28,0.37),0.96,0.0,'rock'),
 'RockPale':((0.30,0.39,0.46),0.96,0.0,'rock'),
 'Grass':((0.25,0.43,0.38),0.96,0.0,'grass'),
 'Moss':((0.41,0.55,0.43),0.96,0.0,'grass'),
 'Path':((0.67,0.63,0.50),0.94,0.0,'stone'),
 'RoofTeal':((0.10,0.33,0.38),0.44,0.35,'metal'),
 'RoofLight':((0.17,0.44,0.46),0.48,0.30,'metal'),
 'Brass':((0.64,0.40,0.14),0.30,0.72,'metal'),
 'BrassLight':((0.86,0.64,0.28),0.27,0.68,'metal'),
 'Iron':((0.10,0.17,0.22),0.48,0.65,'metal'),
 'Timber':((0.35,0.22,0.15),0.82,0.0,'wood'),
 'WoodLight':((0.55,0.37,0.21),0.82,0.0,'wood'),
 'Leaf':((0.13,0.35,0.35),0.96,0.0,'grass'),
 'LeafLight':((0.30,0.48,0.40),0.96,0.0,'grass'),
 'Lavender':((0.47,0.44,0.62),0.88,0.0,'grass'),
 'Cloud':((0.48,0.59,0.73),1.0,0.0,'cloud'),
 'Window':((1.0,0.50,0.15),0.42,0.0,'glow'),
 'Lens':((0.04,0.35,0.48),0.18,0.55,'lens'),
 'Star':((0.85,0.68,0.31),0.38,0.15,'glow'),
}
MATS={}
for name,(rgb,rough,metal,kind) in PALETTE.items():
 m=bpy.data.materials.new(name); m.diffuse_color=(*rgb,1); MATS[name]=m

def png(path,w,h,data):
 def chunk(t,b): return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
 scan=b''.join(b'\0'+data[y*w*3:(y+1)*w*3] for y in range(h))
 path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(scan,6))+chunk(b'IEND',b''))

def textures():
 import numpy as np
 n=1024; yy,xx=np.mgrid[0:n,0:n]/n
 for index,(name,(rgb,rough,metal,kind)) in enumerate(PALETTE.items()):
  # Periodic procedural hand-painted-like variation: all images original to this task.
  phase=index*.73
  f=.045*np.sin(2*math.pi*(xx*3+yy*2)+phase)+.025*np.sin(2*math.pi*(xx*13-yy*7)+phase)
  f+=.012*np.sin(2*math.pi*(xx*67+yy*37))
  if kind=='wood': f+=.09*np.sin(2*math.pi*(yy*22+.18*np.sin(xx*2*math.pi)))**9
  if kind=='stone': f+=.025*np.cos(2*math.pi*xx*16)*np.cos(2*math.pi*yy*16)
  if kind=='rock': f+=.035*np.sin(2*math.pi*(yy*8+xx*2))
  if kind=='metal': f*=.38
  if kind in ('cloud','glow','lens'): f*=.15
  a=np.stack([np.clip((c+f)*255,0,255).astype(np.uint8) for c in rgb],axis=2)
  png(TEX/f'T_{name}.png',n,n,a.tobytes())
 print('TEXTURES_DONE',flush=True)

class MeshGroup:
 def __init__(self,name): self.name=name; self.v=[];self.f=[];self.mi=[];self.smooth=[];self.parts=[]
 def add(self,verts,faces,mat,smooth=False):
  off=len(self.v); verts=[tuple(v) for v in verts]
  # Propagate winding across the closed primitive before orienting its signed volume.
  # This handles dome cut caps and extruded star caps whose initial winding differs.
  edge_faces={}
  for fi,f in enumerate(faces):
   for a,b in zip(f,f[1:]+f[:1]):edge_faces.setdefault(tuple(sorted((a,b))),[]).append((fi,a,b))
  assert all(len(e)==2 for e in edge_faces.values()),'Primitive must be closed'
  adjacent={i:[] for i in range(len(faces))}
  for e in edge_faces.values():
   (fi,a,b),(fj,c,d)=e;relation=-1 if (a,b)==(c,d) else 1
   adjacent[fi].append((fj,relation));adjacent[fj].append((fi,relation))
  signs={0:1};todo=[0]
  while todo:
   fi=todo.pop()
   for fj,rel in adjacent[fi]:
    expected=signs[fi]*rel
    if fj in signs:assert signs[fj]==expected,'Non-orientable primitive'
    else:signs[fj]=expected;todo.append(fj)
  assert len(signs)==len(faces),'Primitive has disconnected topology'
  faces=[f if signs[i]>0 else tuple(reversed(f)) for i,f in enumerate(faces)]
  # Every authored primitive is now a closed, consistently oriented component.
  vol=sum(Vector(verts[f[0]]).dot(Vector(verts[f[i]]).cross(Vector(verts[f[i+1]])))/6 for f in faces for i in range(1,len(f)-1))
  if vol<0: faces=[tuple(reversed(f)) for f in faces];vol=-vol
  self.v.extend(verts)
  for f in faces:
   for i in range(1,len(f)-1): self.f.append((off+f[0],off+f[i],off+f[i+1]));self.mi.append(mat);self.smooth.append(smooth)
  self.parts.append({'first_vertex':off,'vertices':len(verts),'triangles':sum(len(f)-2 for f in faces),'volume_m3':vol,'material':mat})
G={}
def grp(name):
 if name not in G:G[name]=MeshGroup(name)
 return G[name]
def box(g,c,size,mat,rot=0,bevel=0):
 # Bevels are modeled explicitly with chamfered XY corners; no expensive operators.
 x,y,z=c; sx,sy,sz=[s/2 for s in size]; b=min(bevel,sx*.45,sy*.45)
 outline=[(-sx+b,-sy),(sx-b,-sy),(sx,-sy+b),(sx,sy-b),(sx-b,sy),(-sx+b,sy),(-sx,sy-b),(-sx,-sy+b)] if b else [(-sx,-sy),(sx,-sy),(sx,sy),(-sx,sy)]
 pts=[]
 for zz in [-sz,sz]:
  for xx,yy in outline:pts.append((x+xx*math.cos(rot)-yy*math.sin(rot),y+xx*math.sin(rot)+yy*math.cos(rot),z+zz))
 n=len(outline);faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 g.add(pts,faces,mat)
def axis_basis(a,b):
 z=(Vector(b)-Vector(a)).normalized();ref=Vector((0,0,1)) if abs(z.z)<.95 else Vector((1,0,0)); x=ref.cross(z).normalized();y=z.cross(x);return x,y,z
def cylinder(g,a,b,r,mat,n=20,r2=None,smooth=True):
 r2=r if r2 is None else r2;x,y,z=axis_basis(a,b);vs=[]
 for c,rr in [(Vector(a),r),(Vector(b),r2)]:
  vs += [tuple(c+rr*(math.cos(i*math.tau/n)*x+math.sin(i*math.tau/n)*y)) for i in range(n)]
 faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 g.add(vs,faces,mat,smooth)
def sphere(g,c,r,mat,n=20,rings=10,smooth=True):
 if isinstance(r,(float,int)):r=(r,r,r)
 vs=[(c[0],c[1],c[2]-r[2])]
 for j in range(1,rings):
  p=-math.pi/2+math.pi*j/rings
  vs.extend([(c[0]+r[0]*math.cos(p)*math.cos(i*math.tau/n),c[1]+r[1]*math.cos(p)*math.sin(i*math.tau/n),c[2]+r[2]*math.sin(p)) for i in range(n)])
 top=len(vs);vs.append((c[0],c[1],c[2]+r[2]));fs=[]
 for i in range(n):fs.append((0,1+(i+1)%n,1+i))
 for j in range(rings-2):
  a=1+j*n;b=a+n
  for i in range(n):fs.append((a+i,a+(i+1)%n,b+(i+1)%n,b+i))
 for i in range(n):fs.append((top,1+(rings-2)*n+i,1+(rings-2)*n+(i+1)%n))
 g.add(vs,fs,mat,smooth)
def torus(g,c,major,minor,mat,normal=(0,0,1),n=48,m=8):
 x,y,z=axis_basis(c,Vector(c)+Vector(normal));vs=[]
 for i in range(n):
  radial=math.cos(i*math.tau/n)*x+math.sin(i*math.tau/n)*y
  for j in range(m):vs.append(tuple(Vector(c)+(major+minor*math.cos(j*math.tau/m))*radial+minor*math.sin(j*math.tau/m)*z))
 fs=[(i*m+j,((i+1)%n)*m+j,((i+1)%n)*m+(j+1)%m,i*m+(j+1)%m) for i in range(n) for j in range(m)]
 g.add(vs,fs,mat,True)
def arch(g,c,width,height,depth,mat,yaw):
 r=width/2;spring=height-r;out=[(-r,0),(r,0),(r,spring)]+[(r*math.cos(i*math.pi/16),spring+r*math.sin(i*math.pi/16)) for i in range(1,17)]
 vs=[]
 for dd in [-depth/2,depth/2]:
  for xx,zz in out:vs.append((c[0]+xx*math.cos(yaw)-dd*math.sin(yaw),c[1]+xx*math.sin(yaw)+dd*math.cos(yaw),c[2]+zz))
 n=len(out);fs=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)];g.add(vs,fs,mat)
def star(g,c,r,mat,normal=(0,0,1)):
 x,y,z=axis_basis(c,Vector(c)+Vector(normal));out=[Vector(c)+(r if i%2==0 else r*.26)*(math.cos(i*math.pi/4)*x+math.sin(i*math.pi/4)*y) for i in range(8)]
 vs=[tuple(p+z*.04) for p in out]+[tuple(p-z*.04) for p in out]
 fs=[tuple(range(8)),tuple(reversed(range(8,16)))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)];g.add(vs,fs,mat)

ISLANDS=[('Central',(-5,8,4.5),(23,20),19),('Arrival',(15,-31,2.8),(16,13),14),('Cottages',(-32,-16,3.8),(14,13),13),('Garden',(33,14,6.0),(12,12),15),('Beacon',(-27,35,7.0),(9,9),13)]
def island(name,c,r,drop):
 g=grp('Island_'+name);n=40
 radii=[1+random.uniform(-.09,.09) for _ in range(n)];v=[]
 levels=[(1.0,c[2]-.65),(.97,c[2]-2.6),(.70,c[2]-drop*.61),(.38,c[2]-drop*.88),(.05,c[2]-drop)]
 for lev,(scale,z) in enumerate(levels):
  for i in range(n):
   a=i*math.tau/n;rr=radii[i]*(1+(.04*math.sin(i*2.3+lev)))
   v.append((c[0]+r[0]*scale*rr*math.cos(a),c[1]+r[1]*scale*rr*math.sin(a),z+(.0 if lev==0 else random.uniform(-.5,.5))))
 fs=[tuple(reversed(range(n)))]+[(l*n+i,l*n+(i+1)%n,(l+1)*n+(i+1)%n,(l+1)*n+i) for l in range(len(levels)-1) for i in range(n)]+[tuple(range((len(levels)-1)*n,len(levels)*n))]
 g.add(v,fs,'RockBlue')
 # Rounded turf slab with pale weathered stone ledge.
 sphere(g,(c[0],c[1],c[2]-.3),(r[0]*.98,r[1]*.98,1.15),'Limestone',40,8)
 sphere(g,(c[0],c[1],c[2]+.05),(r[0]*.965,r[1]*.965,.72),'Grass',40,8)
 for i in range(10):
  a=i*math.tau/10+.12;rr=.85
  sphere(g,(c[0]+r[0]*rr*math.cos(a),c[1]+r[1]*rr*math.sin(a),c[2]-drop*.38),(2,1.2,3),'RockPale',7,5,False)
 # Golden mineral seams on the underside, clearly sculptural.
 for i in [1,4,8]:
  a=i*math.tau/10;p=(c[0]+r[0]*.5*math.cos(a),c[1]+r[1]*.5*math.sin(a),c[2]-drop*.72)
  cylinder(g,p,(p[0]+.6,p[1]-.4,p[2]-2),.28,'Brass',6,r2=.05, smooth=False)

def walkway(g,a,b,width=2.5,mat='Path',n=16):
 a=Vector(a);b=Vector(b);d=b-a;yaw=math.atan2(d.y,d.x)
 for i in range(n):
  p=a+d*((i+.5)/n);box(g,p,(d.xy.length/n*.94,width,.18),mat,yaw,.13)

def bridge(name,a,b,width=3.3):
 g=grp('Bridge_'+name);a=Vector(a);b=Vector(b);d=b-a;side=Vector((-d.y,d.x,0)).normalized();yaw=math.atan2(d.y,d.x);N=24
 def point(t):return a+d*t+Vector((0,0,1.8*math.sin(math.pi*t)))
 for i in range(N):
  p=point((i+.5)/N);box(g,p,(d.xy.length/N*1.01,width,.36),'WoodLight',yaw,.08)
 for s in [-1,1]:
  for i in range(13):
   t=i/12;p=point(t)+side*(s*width*.48)
   cylinder(g,p,p+Vector((0,0,1.55)),.12,'Iron',10)
   sphere(g,p+Vector((0,0,1.58)),.17,'BrassLight',10,6)
  for j in range(N):
   p=point(j/N)+side*(s*width*.48);q=point((j+1)/N)+side*(s*width*.48)
   for z in [.75,1.5]:cylinder(g,p+Vector((0,0,z)),q+Vector((0,0,z)),.075,'Brass',8)
   cylinder(g,p+Vector((0,0,-.7)),q+Vector((0,0,-.7)),.22,'Iron',10)
   # Descending structural arch and vertical spandrels, joined to deck.
   lowp=p+Vector((0,0,-.7-2.0*math.sin(math.pi*j/N)));lowq=q+Vector((0,0,-.7-2.0*math.sin(math.pi*(j+1)/N)))
   cylinder(g,lowp,lowq,.26,'Limestone',10)
   if j%3==0:cylinder(g,lowp,p,.11,'Iron',8)
 for p in [a,b]:
  cylinder(g,(p.x,p.y,p.z-1.8),(p.x,p.y,p.z-.35),width*.7,'Limestone',12)
 for t in [.0,1.]:
  p=point(t)
  for s in [-1,1]:lantern(g,p+side*(s*(width/2+.35)),height=2.6)

def lantern(g,p,height=2.8):
 p=Vector(p);cylinder(g,p,p+Vector((0,0,.32)),.34,'Limestone',12)
 cylinder(g,p,p+Vector((0,0,height)),.08,'Iron',10)
 c=p+Vector((0,0,height));sphere(g,c,(.26,.26,.42),'Window',12,8)
 cylinder(g,c+Vector((0,0,.36)),c+Vector((0,0,.56)),.39,'RoofTeal',12,r2=.06)
 for aa in [0,math.pi/2,math.pi,3*math.pi/2]:
  off=Vector((.24*math.cos(aa),.24*math.sin(aa),0));cylinder(g,c+off-Vector((0,0,.4)),c+off+Vector((0,0,.38)),.035,'Iron',6)

def dome(g,c,r):
 # Double-shell dome with a 42-degree open observing slit oriented toward foreground.
 az0=math.radians(-24);az1=math.radians(294);na=53;np=12;vs=[]
 for rad in [r,r-.22]:
  for j in range(np+1):
   phi=(math.pi/2-.018)*j/np
   for i in range(na+1):
    az=az0+(az1-az0)*i/na;vs.append((c[0]+rad*math.cos(phi)*math.cos(az),c[1]+rad*math.cos(phi)*math.sin(az),c[2]+rad*math.sin(phi)))
 stride=na+1;layer=(np+1)*stride;fs=[]
 for k in [0,1]:
  for j in range(np):
   for i in range(na):
    a=k*layer+j*stride+i;f=(a,a+1,a+stride+1,a+stride);fs.append(f if k==0 else tuple(reversed(f)))
 for j in range(np):
  for i in [0,na]:
   a=j*stride+i;b=(j+1)*stride+i;fs.append((a,b,b+layer,a+layer))
 for i in range(na):
  for j in [0,np]:a=j*stride+i;fs.append((a,a+1,a+1+layer,a+layer))
 g.add(vs,fs,'RoofTeal',True)
 # Slit edge brass rails and panel ribs follow the actual dome curve.
 for az in [az0,az1]+[az0+(az1-az0)*i/12 for i in range(1,12)]:
  for j in range(12):
   pp=[]
   for k in [j,j+1]:
    phi=(math.pi/2-.035)*k/12;pp.append((c[0]+(r+.025)*math.cos(phi)*math.cos(az),c[1]+(r+.025)*math.cos(phi)*math.sin(az),c[2]+(r+.025)*math.sin(phi)))
   cylinder(g,pp[0],pp[1],.095 if az in [az0,az1] else .048,'Brass',8)
 torus(g,c,r,.17,'Brass',n=72)

def observatory():
 g=grp('Observatory');cx,cy=-5,8;z=5.2
 for rr,zz,hh,ma in [(12,z,.6,'StoneDark'),(11.5,z+.45,.55,'Limestone'),(10.9,z+.9,.35,'Path'),(9.7,z+1.25,6.4,'Limestone')]:
  cylinder(g,(cx,cy,zz),(cx,cy,zz+hh),rr,ma,64)
 floor=z+1.25;roof=floor+6.4
 for zz in [floor+.32,roof-.35,roof+.05]:torus(g,(cx,cy,zz),9.76,.20,'Brass',n=72)
 for i in range(14):
  az=i*math.tau/14;nx,ny=math.cos(az),math.sin(az);yaw=az+math.pi/2
  p=(cx+9.75*nx,cy+9.75*ny,floor+.95)
  arch(g,p,1.65,3.25,.24,'StoneDark',yaw)
  p2=(cx+9.91*nx,cy+9.91*ny,floor+1.1);arch(g,p2,1.22,2.86,.12,'Window',yaw)
  # Visible mullions and stone sill.
  cylinder(g,(p2[0]+.09*nx,p2[1]+.09*ny,p2[2]),(p2[0]+.09*nx,p2[1]+.09*ny,p2[2]+2.8),.05,'Brass',8)
  box(g,(cx+10.03*nx,cy+10.03*ny,floor+.97),(1.9,.45,.2),'Limestone',yaw,.07)
 for i in range(14):
  az=(i+.5)*math.tau/14;nx,ny=math.cos(az),math.sin(az)
  cylinder(g,(cx+9.8*nx,cy+9.8*ny,floor+.4),(cx+9.8*nx,cy+9.8*ny,roof-.4),.29,'Path',12)
 dome(g,(cx,cy,roof+.2),9.65)
 # Entry portico faces the arrival island; real raised steps join the plaza.
 az=-math.pi/2;yaw=0
 arch(g,(cx,cy-9.99,floor),2.8,4.6,.30,'Brass',yaw)
 arch(g,(cx,cy-10.18,floor+.1),2.35,4.2,.25,'Timber',yaw)
 for s in [-1,1]:cylinder(g,(cx+s*2.1,cy-11.5,floor-.1),(cx+s*2.1,cy-11.5,floor+4.0),.30,'Limestone',16)
 box(g,(cx,cy-11.1,floor+4.3),(5.3,3.2,.4),'RoofTeal',0,.3)
 for i in range(5):box(g,(cx,cy-12.3-i*.48,z+.15+i*.16),(4.5,.55,.3),'Limestone',0,.08)
 # Roof finial and small navigation band.
 cylinder(g,(cx,cy,roof+9.7),(cx,cy,roof+11.4),.10,'Brass',12)
 sphere(g,(cx,cy,roof+10.1),.35,'BrassLight',16,8)
 star(g,(cx,cy,roof+11.6),.9,'Star',(1,-1,0))
 # Telescope deck, offset from dome so its mechanical structure reads in overview.
 cylinder(g,(7,-6,5.1),(7,-6,5.9),6.0,'Limestone',48)
 cylinder(g,(7,-6,5.9),(7,-6,6.05),5.65,'Path',48)
 for i in range(22):
  aa=i*math.tau/22
  if -2.8<aa-math.pi<-.4:continue
  p=Vector((7+5.75*math.cos(aa),-6+5.75*math.sin(aa),6.05));cylinder(g,p,p+Vector((0,0,1.05)),.065,'Brass',8)
 walkway(g,(-5,-7,5.3),(4,-6,5.7),3.7,n=14)

def telescope():
 g=grp('GrandTelescope');pivot=Vector((7,-6,10.9));d=Vector((.73,-.48,.48)).normalized()
 cylinder(g,(7,-6,6.05),(7,-6,6.5),2.2,'StoneDark',32)
 cylinder(g,(7,-6,6.5),(7,-6,9.1),1.18,'Brass',24,r2=.9)
 for zz,rr in [(6.7,1.3),(8.6,1.1),(9.1,1.6)]:torus(g,(7,-6,zz),rr,.15,'BrassLight')
 # Fork trunnions, axle, large altitude gears, handwheel and counterweight.
 side=Vector((-d.y,d.x,0)).normalized()
 for s in [-1,1]:
  a=Vector((7,-6,8.8))+side*s*1.8;b=pivot+side*s*1.8
  cylinder(g,a,b,.35,'Brass',12)
  cylinder(g,pivot+side*s*1.2,pivot+side*s*2.2,.6,'Iron',20)
  torus(g,pivot+side*s*2.18,1.02,.16,'BrassLight',normal=side)
  for k in range(24):
   xx,yy,zz=axis_basis(pivot,pivot+side);rad=xx*math.cos(k*math.tau/24)+yy*math.sin(k*math.tau/24)
   sphere(g,pivot+side*s*2.18+rad*1.06,.14,'Brass',8,4)
 a=pivot-d*4.2;b=pivot+d*6.7
 cylinder(g,a,b,1.22,'Brass',40,r2=1.48)
 for t,rr in [(-4.2,1.27),(-3.3,1.32),(-.8,1.42),(1.5,1.48),(5.7,1.56),(6.65,1.60)]:
  torus(g,pivot+d*t,rr,.16,'BrassLight',normal=d)
 # Objective hood rim and visibly inset glass. No black open-back faces.
 cylinder(g,b+d*.01,b+d*.18,1.38,'Iron',40)
 cylinder(g,b+d*.19,b+d*.23,1.22,'Lens',40)
 torus(g,b+d*.25,1.35,.13,'BrassLight',normal=d)
 cylinder(g,a-d*1.0,a,.45,'Iron',24,r2=.65)
 cylinder(g,a-d*1.55,a-d*.95,.28,'BrassLight',20)
 # Finder scope and mounting saddles.
 off=Vector((0,0,1.65))
 cylinder(g,pivot-d*.8+off,pivot+d*3+off,.23,'RoofTeal',16,r2=.3)
 for t in [-.5,2.5]:cylinder(g,pivot+d*t+Vector((0,0,1.0)),pivot+d*t+off,.12,'Iron',8)
 cylinder(g,pivot-Vector((0,0,1.3)),pivot-Vector((0,0,3.3)),.12,'Iron',10)
 cylinder(g,pivot-Vector((0,0,3.2)),pivot-Vector((0,0,3.8)),.75,'Iron',16)
 wheel=pivot-side*2.6-Vector((0,0,.9));torus(g,wheel,.72,.10,'BrassLight',normal=side,n=32)
 xx,yy,_=axis_basis(wheel,wheel+side)
 for i in range(6):cylinder(g,wheel,wheel+.67*(math.cos(i*math.tau/6)*xx+math.sin(i*math.tau/6)*yy),.045,'Brass',8)
 for s in [-1,1]:
  box(g,(3+s*1.2,-8,6.6),(.3,1.0,1.1),'Timber',0,.05)
 box(g,(3,-8,7.2),(3.1,1.5,.18),'WoodLight',0,.12)

def armillary(g,c):
 c=Vector(c);cylinder(g,c,c+Vector((0,0,.35)),2.4,'Limestone',32)
 cylinder(g,c+Vector((0,0,.35)),c+Vector((0,0,2.6)),.7,'Brass',20,r2=.35)
 o=c+Vector((0,0,4.0))
 for r,norm in [(2.2,(0,0,1)),(2.15,(1,0,.4)),(2.05,(0,1,.25)),(1.7,(1,1,.7))]:torus(g,o,r,.085,'BrassLight',normal=norm,n=64)
 sphere(g,o,.48,'Lens',24,12)
 cylinder(g,o-Vector((.6,.2,2.5)),o+Vector((.6,.2,2.5)),.075,'Brass',12)
 star(g,o+Vector((.6,.2,2.7)),.5,'Star',(1,-1,0))

def gardens():
 g=grp('ConstellationGarden');c=(33,14,6.8)
 cylinder(g,(33,14,6.55),(33,14,6.75),9.3,'StoneDark',64)
 torus(g,c,8.8,.12,'Brass',n=72);torus(g,c,6.8,.07,'Brass',n=72)
 armillary(g,(33,14,6.8))
 # A seven-star inlaid constellation, each disk connected by brass lines.
 points=[(27,11),(26,15),(28,19),(31,21),(35,21),(39,18),(40,13)]
 for a,b in zip(points,points[1:]):cylinder(g,(*a,6.87),(*b,6.87),.055,'BrassLight',8)
 for x,y in points:star(g,(x,y,6.9),.55,'Star')
 for i in range(12):
  a=i*math.tau/12;star(g,(33+8*math.cos(a),14+8*math.sin(a),6.9),.26,'BrassLight')
 # Sundial on its own south terrace.
 cylinder(g,(33,6,6.9),(33,6,8.0),.55,'Limestone',16)
 cylinder(g,(33,6,8.0),(33,6,8.18),1.15,'Brass',32)
 g.add([(32.95,5.4,8.2),(32.95,6.7,8.2),(32.95,6.2,9.1),(33.05,5.4,8.2),(33.05,6.7,8.2),(33.05,6.2,9.1)],[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],'Iron')
 for i in range(6):
  a=i*math.tau/6;lantern(g,(33+10.5*math.cos(a),14+10.5*math.sin(a),6.6),2)

def cottage(g,c,yaw=0,scale=1):
 # Small scholars' houses: round corners, steep hipped teal roofs and brass vents.
 x,y,z=c;s=scale
 box(g,(x,y,z+.30),(7*s,5.8*s,.7),'StoneDark',yaw,.65)
 box(g,(x,y,z+2.4*s),(6.4*s,5.2*s,4.3*s),'Limestone',yaw,.65)
 # Closed truncated hipped roof, transformed in XY.
 vs=[]
 for zz,rx,ry in [(z+4.6*s,3.9*s,3.2*s),(z+7.0*s,2.7*s,.22*s)]:
  for xx,yy in [(-rx,-ry),(rx,-ry),(rx,ry),(-rx,ry)]:vs.append((x+xx*math.cos(yaw)-yy*math.sin(yaw),y+xx*math.sin(yaw)+yy*math.cos(yaw),zz))
 g.add(vs,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'RoofTeal')
 def trans(xx,yy,zz):return (x+xx*math.cos(yaw)-yy*math.sin(yaw),y+xx*math.sin(yaw)+yy*math.cos(yaw),zz)
 for xx in [-1.8*s,1.8*s]:
  arch(g,trans(xx,-2.64*s,z+1.1*s),1.3*s,2.2*s,.18,'Brass',yaw)
  arch(g,trans(xx,-2.76*s,z+1.2*s),1.05*s,1.92*s,.12,'Window',yaw)
 arch(g,trans(0,-2.71*s,z+.4),1.4*s,2.8*s,.2,'Timber',yaw)
 for i in range(3):box(g,trans(0,-3.1*s-i*.35,z+.2-i*.07),(2*s,.6,.2),'Limestone',yaw,.05)
 p=trans(2*s,1*s,z+5*s);cylinder(g,p,(p[0],p[1],z+7.4*s),.35,'Brass',16)
 sphere(g,(p[0],p[1],z+7.5*s),(.5,.5,.17),'RoofTeal',16,6)
 for xx in [-3.0*s,3.0*s]:
  for yy in [-2.3*s,2.3*s]:cylinder(g,trans(xx,yy,z+.5),trans(xx,yy,z+4.5*s),.14,'Timber',10)

def village_and_arrival():
 g=grp('ScholarsVillage');cottage(g,(-34,-12,4.8),.30,1.0);cottage(g,(-29,-23,4.7),-.4,.78)
 walkway(g,(-28,-5,4.8),(-32,-19,4.8),2.2,n=20)
 for p in [(-37,-17,4.7),(-25,-18,4.7),(-32,-26,4.6)]:lantern(g,p)
 # Books, crates, stools and a rolled chart station beside the cottage.
 box(g,(-31,-17,5.9),(2.5,1.3,.15),'WoodLight',.3,.08)
 for xx in [-1,1]:
  for yy in [-.45,.45]:box(g,(-31+xx,-17+yy,5.3),(.12,.12,1.2),'Timber')
 for i in range(5):box(g,(-31.5+i*.15,-17,6.05+i*.045),(.6,.8,.10),'RoofLight' if i%2 else 'Brass',.2+i*.1,.02)
 for p in [(-38,-13,5.2),(-36,-21,5.1)]:
  box(g,p,(1.1,1.1,.9),'Timber',.1,.08)
  for dz in [-.25,.25]:box(g,(p[0],p[1]-.57,p[2]+dz),(1.15,.08,.09),'Brass')
 a=grp('ArrivalCourt');cylinder(a,(15,-31,3.1),(15,-31,3.5),9.0,'Limestone',48)
 cylinder(a,(15,-31,3.5),(15,-31,3.6),8.5,'Path',48)
 torus(a,(15,-31,3.65),7.5,.11,'Brass',n=72)
 for i in range(8):
  angle=i*math.tau/8;end=(15+6.7*math.cos(angle),-31+6.7*math.sin(angle),3.68)
  cylinder(a,(15,-31,3.68),end,.065,'Brass',8)
  star(a,end,.65 if i%2==0 else .4,'BrassLight')
 star(a,(15,-31,3.72),2.3,'RoofTeal')
 # Welcome arch and hanging celestial emblem at the front edge.
 for x in [10.3,19.7]:
  cylinder(a,(x,-37.5,3.5),(x,-37.5,7.4),.4,'Limestone',16)
  sphere(a,(x,-37.5,7.7),.48,'BrassLight',16,8)
 cylinder(a,(10.3,-37.5,7.6),(19.7,-37.5,7.6),.24,'Timber',16)
 torus(a,(15,-37.5,6.7),.8,.08,'BrassLight',normal=(0,1,0))
 star(a,(15,-37.5,6.7),.65,'Star',(0,-1,0))
 for x in [8,22]:
  box(a,(x,-32,4.3),(1.4,3.2,.25),'WoodLight',0,.2)
  for y in [-33,-31]:box(a,(x,y,3.8),(.9,.35,.8),'StoneDark',0,.1)
 for p in [(5,-28,3.7),(25,-28,3.7),(6,-36,3.7),(24,-36,3.7)]:lantern(a,p)
 # Rear small beacon tower.
 b=grp('Beacon');cylinder(b,(-27,35,7.7),(-27,35,8.2),4.7,'Limestone',32)
 cylinder(b,(-27,35,8.2),(-27,35,13.0),2.5,'Limestone',32,r2=2.2)
 cylinder(b,(-27,35,13),(-27,35,15.1),1.9,'Window',24)
 for i in range(8):
  aa=i*math.tau/8;p=(-27+1.95*math.cos(aa),35+1.95*math.sin(aa),13)
  cylinder(b,p,(p[0],p[1],15.25),.10,'Brass',8)
 cylinder(b,(-27,35,15.25),(-27,35,18),3.0,'RoofTeal',32,r2=.2)
 sphere(b,(-27,35,18.2),.4,'BrassLight',16,8)

def tree(g,p,scale=1):
 x,y,z=p;s=scale;cylinder(g,(x,y,z),(x,y,z+3.7*s),.28*s,'Timber',10,r2=.16*s)
 for angle in [0,2.3,4.5]:
  e=(x+1.1*s*math.cos(angle),y+1.1*s*math.sin(angle),z+3.3*s);cylinder(g,(x,y,z+2*s),e,.15*s,'Timber',8,r2=.06*s)
 sphere(g,(x,y,z+4*s),(1.8*s,1.6*s,2.3*s),'Leaf',16,10)
 sphere(g,(x+.85*s,y-.4*s,z+3.8*s),(1.3*s,1.3*s,1.6*s),'LeafLight',16,8)
def vegetation():
 g=grp('Vegetation')
 trees=[(-18,15,5.2,1.1),(-17,2,5.2,.9),(-12,22,5.0,1), (8,20,5.2,.9),(12,11,5.2,.85),(-39,-8,4.6,.85),(-40,-19,4.6,1),(-24,-24,4.6,.85),(4,-34,3.5,.8),(23,-34,3.5,.85),(24,-23,3.6,.65),(38,21,6.8,.85),(41,10,6.8,.7),(-31,39,7.7,.7)]
 for x,y,z,s in trees:tree(g,(x,y,z),s)
 for name,c,r,drop in ISLANDS:
  for i in range(22):
   aa=random.random()*math.tau;rr=random.uniform(.76,.90);x=c[0]+r[0]*rr*math.cos(aa);y=c[1]+r[1]*rr*math.sin(aa);z=c[2]+.6
   sphere(g,(x,y,z+.22),(random.uniform(.35,.8),random.uniform(.35,.8),.5),'Moss',10,6)
   if i%3==0:
    for j in range(3):
     xx=x+random.uniform(-.4,.4);yy=y+random.uniform(-.4,.4)
     cylinder(g,(xx,yy,z),(xx,yy,z+.65),.035,'Leaf',5)
     sphere(g,(xx,yy,z+.7),(.16,.16,.22),'Lavender',8,5)

def clouds():
 g=grp('CloudLayer')
 # Bounded static soft ellipsoids. Their upper surface stays below island tips.
 for x,y,z,rx,ry,rz in [(-28,-29,-20,17,12,3.2),(-4,-34,-22,16,11,3.0),(24,-24,-21,20,15,3.7),(30,7,-22,17,19,3.8),(-34,12,-22,12,22,3.2),(-8,31,-23,24,15,3.5)]:
  rz*=1.6
  sphere(g,(x,y,z),(rx,ry,rz),'Cloud',32,12)
  for j in range(5):
   xx=x+random.uniform(-rx*.50,rx*.50);yy=y+random.uniform(-ry*.45,ry*.45)
   sphere(g,(xx,yy,z+1.4),(rx*.34,ry*.36,rz*.8),'Cloud',24,10)

def export_and_validate():
 report={'generated_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'units':'metres in Blender; FBX metadata converts to centimetres','uv_texture_resolution':1024,'texel_density_target_px_per_m':64,'uv_method':'Each geometric triangle is a separate planar UV island at exact area scale. Islands are shelf-packed into disjoint rectangles with 4px padding on every side. Periodic textures deliberately repeat outside 0..1. No atlas baking/lightmaps. Shared tiling patterns are intentional, never mirrored UVs.','groups':[],'material_parameters':{k:{'rgb':v[0],'roughness':v[1],'metallic':v[2],'kind':v[3]} for k,v in PALETTE.items()}}
 globalmin=[1e9]*3;globalmax=[-1e9]*3
 for name,g in G.items():
  mesh=bpy.data.meshes.new('SM_'+name);mesh.from_pydata(g.v,[],g.f);mesh.update()
  ob=bpy.data.objects.new('SM_'+name,mesh);bpy.context.collection.objects.link(ob)
  used=list(dict.fromkeys(g.mi));index={ma:i for i,ma in enumerate(used)}
  for ma in used:mesh.materials.append(MATS[ma])
  uv=mesh.uv_layers.new(name='SurfaceUV');density=[];degenerate=0
  # Unique UV islands in an integer grid preserve periodic texture scale and prevent unintended overlaps.
  shelf_x=0.;shelf_y=0.;shelf_height=0.;uv_rects=[]
  for p,ma,sm in zip(mesh.polygons,g.mi,g.smooth):
   p.material_index=index[ma];p.use_smooth=sm
   aa,bb,cc=[Vector(mesh.vertices[i].co) for i in p.vertices];ab=bb-aa;ac=cc-aa;cross=ab.cross(ac);area=cross.length*.5
   if area<1e-10:degenerate+=1;coords=[(0,0)]*3
   else:
    tangent=ab.normalized();bitangent=cross.normalized().cross(tangent);raw=[(0.,0.),(ab.length/16,0.),(ac.dot(tangent)/16,ac.dot(bitangent)/16)]
    minx=min(v[0] for v in raw);miny=min(v[1] for v in raw);maxx=max(v[0] for v in raw);maxy=max(v[1] for v in raw)
    # 4px padding, separate integer cells; UV outside 0..1 is intentionally wrapped.
    pad=4/1024;cellw=maxx-minx+2*pad;cellh=maxy-miny+2*pad
    if shelf_x+cellw>16:shelf_x=0.;shelf_y+=shelf_height;shelf_height=0.
    coords=[(u-minx+shelf_x+pad,v-miny+shelf_y+pad) for u,v in raw]
    uv_rects.append((shelf_x+pad,shelf_y+pad,shelf_x+pad+maxx-minx,shelf_y+pad+maxy-miny))
    shelf_x+=cellw;shelf_height=max(shelf_height,cellh)
    uvarea=abs((coords[1][0]-coords[0][0])*(coords[2][1]-coords[0][1])-(coords[2][0]-coords[0][0])*(coords[1][1]-coords[0][1]))*.5
    density.append(1024*math.sqrt(uvarea/area))
   for li,co in zip(p.loop_indices,coords):uv.data[li].uv=co
   if area>=1e-10:
    stored=[uv.data[li].uv.copy() for li in p.loop_indices]
    measured=abs((stored[1].x-stored[0].x)*(stored[2].y-stored[0].y)-(stored[2].x-stored[0].x)*(stored[1].y-stored[0].y))*.5
    density[-1]=1024*math.sqrt(measured/area)
  # Component topology and orientation are checked independently, not only aggregate volume.
  edges={}
  for f in g.f:
   for a,b in zip(f,f[1:]+f[:1]):edges.setdefault(tuple(sorted((a,b))),[]).append((a,b))
  bad=sum(len(e)!=2 or e[0]!=tuple(reversed(e[1])) for e in edges.values())
  bounds=[[min(v[k] for v in g.v),max(v[k] for v in g.v)] for k in range(3)]
  for k in range(3):globalmin[k]=min(globalmin[k],bounds[k][0]);globalmax[k]=max(globalmax[k],bounds[k][1])
  item={'name':'SM_'+name,'vertices':len(g.v),'triangles':len(g.f),'closed_components':len(g.parts),'all_component_signed_volumes_positive':all(p['volume_m3']>1e-9 for p in g.parts),'nonmanifold_or_inconsistent_edges':bad,'degenerate_triangles':degenerate,'bounds_m':bounds,'materials':used,'uv_finite':all(math.isfinite(v) for u in uv.data for v in u.uv),'density_min':min(density),'density_max':max(density),'density_average':sum(density)/len(density),'uv_island_count':len(g.f),'padding_px':4,'uv_overlap_check':'monotonic shelves and nonoverlapping per-face rectangles with 4px padding; periodic wrap is intentional','open_faces':0}
  assert bad==0 and degenerate==0 and item['all_component_signed_volumes_positive'] and item['uv_finite'],item
  report['groups'].append(item)
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
  bpy.ops.export_scene.fbx(filepath=str(FBX/(ob.name+'.fbx')),use_selection=True,object_types={'MESH'},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,global_scale=1.0,mesh_smooth_type='FACE',path_mode='AUTO')
  print('EXPORT',name,len(g.f),'faces',flush=True)
 report['bounds_m']=[globalmin,globalmax];report['xy_footprint_m']=[globalmax[k]-globalmin[k] for k in [0,1]]
 assert all(globalmin[k]>=-50 and globalmax[k]<=50 for k in [0,1]),report['bounds_m']
 report['source_generation_seconds']=time.time()-START
 (ROOT/'Evidence/source_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 (ART/'materials.json').write_text(json.dumps(report['material_parameters'],indent=2),encoding='utf-8')
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/'SkyObservatory_Master.blend'))
 print('SOURCE_VALIDATION_PASS',report['bounds_m'],report['source_generation_seconds'],flush=True)

textures()
for args in ISLANDS:island(*args)
observatory();telescope();gardens();village_and_arrival();vegetation()
bridge('Arrival',(13,-18,3.8),(7,-11,5.6),3.8)
bridge('Village',(-22,-1,5.3),(-27,-6,4.7),3.0)
bridge('Garden',(15,12,5.2),(23,13,6.7),3.1)
bridge('Beacon',(-17,22,5.1),(-22,29,7.7),2.6)
clouds();export_and_validate()
