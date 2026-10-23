"""Original SnowyOnsen/max source artwork; Blender 5.0 background only."""
import bpy, bmesh, math, random, json, time, os, statistics
from mathutils import Vector
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max')
OUT=ROOT/'Source'; OUT.mkdir(parents=True,exist_ok=True)
T0=time.time(); random.seed(231023)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC'; bpy.context.scene.unit_settings.scale_length=1
MATS={
 'Snow':((0.78,0.88,0.94),.88,16), 'Wood':((.26,.115,.053),.75,8),
 'DarkWood':((.10,.045,.025),.8,8),'Plaster':((.74,.62,.43),.9,8),
 'Stone':((.22,.30,.34),.83,8),'Roof':((.12,.22,.25),.8,8),
 'Water':((.025,.48,.46),.22,8),'Window':((1,.51,.12),.4,8),
 'Pine':((.065,.19,.16),.9,8),'Red':((.48,.085,.055),.8,8),
 'Brass':((.56,.34,.10),.45,8),'Steam':((.78,.93,.92),1,8),
 'Path':((.30,.32,.32),.9,8),'Towel':((.87,.77,.57),.95,8),
}
mats={}
for n,(col,rough,tile) in MATS.items():
 m=bpy.data.materials.new(n); m.diffuse_color=(*col,1); mats[n]=m

# Original seamless analytic texture source. Pixel generation is vectorized.
import numpy as np
texmeta={}
N=1024
u,v=np.meshgrid(np.arange(N,dtype=np.float32)/N,np.arange(N,dtype=np.float32)/N)
rng=np.random.default_rng(231023)
for name in ['Wood','DarkWood','Snow','Stone','Path','Plaster','Roof','Pine','Red','Towel','Steam','Water']:
 base=np.array(MATS[name][0],dtype=np.float32)
 grain=np.sin(2*np.pi*(32*v+1.6*np.sin(2*np.pi*u)+.4*np.sin(12*np.pi*u)))
 cloud=(np.sin(2*np.pi*u)*np.cos(4*np.pi*v)+np.sin(10*np.pi*u+8*np.pi*v)*.25+np.sin(26*np.pi*u-18*np.pi*v)*.12)
 noise=rng.random((N,N),dtype=np.float32)-.5
 if name in ['Wood','DarkWood']:
  tone=.91+.085*grain+.04*noise
  seams=np.abs(np.sin(16*np.pi*v))<.026; tone[seams]*=.5
 elif name=='Steam':
  tone=np.clip(.55+.24*cloud+.10*np.sin(18*np.pi*u+6*np.pi*v),0,1)
 elif name=='Water': tone=.91+.055*np.sin(24*np.pi*u+8*np.sin(4*np.pi*v))+.035*cloud
 elif name in ['Stone','Path']: tone=.9+.07*cloud+.1*noise
 elif name=='Snow': tone=.97+.018*cloud+.017*noise
 else: tone=.94+.035*cloud+.04*noise
 rgb=np.clip(base[None,None,:]*tone[:,:,None],0,1)
 rgba=np.concatenate([rgb,np.ones((N,N,1),dtype=np.float32)],axis=2)
 if name=='Steam':
  rgba[:,:,:3]=tone[:,:,None]
  rgba[:,:,3]=(np.exp(-((u-.5)/.31)**2)*np.maximum(0,np.sin(np.pi*v))**1.8*np.maximum(0,np.sin(np.pi*u))**1.3).astype(np.float32)
 im=bpy.data.images.new('T_'+name,width=N,height=N,alpha=True)
 im.pixels.foreach_set(rgba.ravel()); im.filepath_raw=str(OUT/('T_'+name+'.png')); im.file_format='PNG'; im.save()
 texmeta[name]={'file':'T_'+name+'.png','resolution':[N,N],'tile_m':MATS[name][2],'target_px_per_m':N/MATS[name][2],'source':'original analytic periodic grain/cloud + seeded noise','alpha':1}
print('SOURCE textures complete',flush=True)

class Builder:
 def __init__(self,name): self.name=name; self.v=[];self.f=[];self.mi=[];self.sm=[];self.components=[]
 def add(self,verts,faces,mat='Snow',smooth=False,closed=True):
  k=len(self.v); self.v.extend(verts); self.f.extend([tuple(k+i for i in f) for f in faces]); self.mi.extend([list(MATS).index(mat)]*len(faces));self.sm.extend([smooth]*len(faces))
  self.components.append({'first_face':len(self.f)-len(faces),'faces':len(faces),'closed':closed,'material':mat})
 def box(self,c,s,mat='Wood',rot=0):
  x,y,z=c; a,b,h=[q/2 for q in s]; co=math.cos(rot);si=math.sin(rot)
  verts=[(x+dx*co-dy*si,y+dx*si+dy*co,z+dz) for dx,dy,dz in [(-a,-b,-h),(a,-b,-h),(a,b,-h),(-a,b,-h),(-a,-b,h),(a,-b,h),(a,b,h),(-a,b,h)]]
  self.add(verts,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],mat)
 def ellipsoid(self,c,r,mat='Snow',n=16,rings=8):
  # Two poles, no zero-area quads; winding is outward for every component.
  verts=[(c[0],c[1],c[2]-r[2])]
  for j in range(1,rings):
   p=-math.pi/2+math.pi*j/rings
   for i in range(n):
    t=2*math.pi*i/n; verts.append((c[0]+r[0]*math.cos(p)*math.cos(t),c[1]+r[1]*math.cos(p)*math.sin(t),c[2]+r[2]*math.sin(p)))
  top=len(verts);verts.append((c[0],c[1],c[2]+r[2]));faces=[]
  for i in range(n):faces.append((0,1+(i+1)%n,1+i))
  for j in range(rings-2):
   for i in range(n):
    a=1+j*n+i;b=1+j*n+(i+1)%n;faces.append((a,b,b+n,a+n))
  for i in range(n):faces.append((1+(rings-2)*n+i,1+(rings-2)*n+(i+1)%n,top))
  self.add(verts,faces,mat,True)
 def cylinder(self,a,b,r,mat='Wood',n=12,r2=None):
  av=Vector(a);bv=Vector(b);d=(bv-av).normalized();basis=d.cross(Vector((0,0,1)))
  if basis.length<.001:basis=d.cross(Vector((0,1,0)))
  basis.normalize();up=d.cross(basis);r2=r if r2 is None else r2
  verts=[tuple(c+rr*(basis*math.cos(2*math.pi*i/n)+up*math.sin(2*math.pi*i/n))) for c,rr in [(av,r),(bv,r2)] for i in range(n)]
  faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
  self.add(verts,faces,mat,True)
 def roof(self,c,w,d,eave,rise,mat='Snow',thick=.28):
  x,y,z=c
  # Gabled solid roof with six-face cross-section extruded along X.
  sec=[(-d/2,eave),(0,eave+rise),(d/2,eave),(d/2,eave-thick),(0,eave+rise-thick),(-d/2,eave-thick)]
  verts=[(x+sx*w/2,y+yy,z+zz) for sx in [-1,1] for yy,zz in sec]
  faces=[tuple(reversed(range(6))),tuple(range(6,12))]+[(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)]
  self.add(verts,faces,mat)
 def surface_ellipse(self,c,rx,ry,mat='Water',n=64):
  verts=[c]+[(c[0]+rx*math.cos(2*math.pi*i/n),c[1]+ry*math.sin(2*math.pi*i/n),c[2]) for i in range(n)]
  self.add(verts,[(0,1+i,1+(i+1)%n) for i in range(n)],mat,False,False)
 def vertical_card(self,c,w,h,angle=0):
  dx=math.cos(angle)*w/2;dy=math.sin(angle)*w/2;x,y,z=c
  self.add([(x-dx,y-dy,z),(x+dx,y+dy,z),(x+dx,y+dy,z+h),(x-dx,y-dy,z+h)],[(0,1,2,3)],'Steam',False,False)

B={name:Builder('SM_'+name) for name in ['Terrain','Ridges','InnMain','Bathhouse','GuestEast','GuestWest','Pools','Water','Bridges','Paths','Pines','Rocks','Lanterns','Furnishings','Steam','Entrance']}
terr=B['Terrain']
# Rounded-square 100m footprint; layered island with continuous snowy cap.
def round_square(builder,z0,z1,half,r,mat):
 xy=[]
 for cx,cy,a in [(half-r,half-r,0),(-half+r,half-r,90),(-half+r,-half+r,180),(half-r,-half+r,270)]:
  for i in range(9):
   th=math.radians(a+i*90/8);xy.append((cx+r*math.cos(th),cy+r*math.sin(th)))
 n=len(xy);vv=[(x,y,z) for z in[z0,z1] for x,y in xy];ff=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 builder.add(vv,ff,mat)
round_square(terr,-3.5,-.45,50,9,'Stone');round_square(terr,-.45,.45,49.8,9,'Snow')
# Snowy mountain ridge encloses northern half without exceeding footprint.
rid=B['Ridges']
for x,y,rx,ry,h in [(-32,34,14,12,15),(-13,39,15,10,18),(6,39,17,10,22),(28,35,16,13,17),(39,23,9,15,10)]:
 rid.ellipsoid((x,y,.45+h/2),(rx,ry,h/2),'Stone',20,10)
 rid.ellipsoid((x,y,.70+h/2),(rx*.985,ry*.985,h/2),'Snow',20,10)
 # A few exposed rounded slanted crags.
 for k in range(4):
  rid.ellipsoid((x-rx*.7+k*rx*.42,y-ry*.73,2+h*(.1+.08*k)),(rx*.22,ry*.19,h*.22),'Stone',12,7)

def building(group,x,y,z,w,d,h,balcony=False):
 b=B[group];b.box((x,y,z-.05),(w+1,d+1,1),'Stone');b.box((x,y,z+h/2),(w,d,h),'Plaster')
 # Framing and horizontal timber cladding.
 for yy in [-d/2-.09,d/2+.09]:
  for zz in [.35,1.05,h*.53,h-.2]:b.box((x,y+yy,z+zz),(w+.25,.2,.22),'DarkWood')
  for xx in [-w/2,-w/4,0,w/4,w/2]:b.box((x+xx,y+yy,z+h/2),(.23,.23,h+.1),'Wood')
 for xx in[-w/2-.08,w/2+.08]:
  for zz in [.35,h*.53,h-.2]:b.box((x+xx,y,z+zz),(.22,d+.3,.22),'DarkWood')
  for yy in[-d/2,0,d/2]:b.box((x+xx,y+yy,z+h/2),(.23,.23,h),'Wood')
 # Front windows with visible depth, sill, frame and small shoji mullions.
 floors=[1.8,h-1.65] if h>6 else [h*.57]
 for zz in floors:
  for xx in [-w*.32,0,w*.32]:
   ww=w*.21;hh=1.65 if h>6 else 1.8;front=y-d/2-.15
   b.box((x+xx,front,z+zz),(ww,.12,hh),'DarkWood');b.box((x+xx,front-.08,z+zz),(ww-.19,.1,hh-.18),'Window')
   for off in[-.5,0,.5]:b.box((x+xx+off*ww*.76,front-.17,z+zz),(.065,.12,hh),'Wood')
   b.box((x+xx,front-.17,z+zz),(ww,.12,.07),'Wood');b.box((x+xx,front-.23,z+zz-hh/2),(ww+.3,.45,.13),'Wood')
 # Side windows repeat warm screens.
 for xx in[-w/2-.15,w/2+.15]:
  for yy in[-d*.25,d*.25]:
   b.box((x+xx,y+yy,z+2),(.11,1.65,1.7),'DarkWood');b.box((x+xx+(.07 if xx>0 else -.07),y+yy,z+2),(.08,1.45,1.5),'Window')
   for o in[-.5,0,.5]:b.box((x+xx*1.002,y+yy+o,z+2),(.22,.06,1.7),'Wood')
 # Deep entrance, little curtain, raised porch and canopy.
 b.box((x,y-d/2-.25,z+1.35),(1.65,.45,2.7),'DarkWood')
 b.box((x,y-d/2-.50,z+1.25),(1.4,.08,2.3),'Wood')
 for o in[-.48,0,.48]:b.box((x+o,y-d/2-.59,z+2.1),(.43,.06,.8),'Red')
 b.box((x,y-d/2-.8,z+.05),(w+1,1.9,.30),'Wood')
 b.roof((x,y-d/2-.6,z),4.0,2.9,3.1,.55,'Roof',.22);b.roof((x,y-d/2-.6,z+.20),4.2,3.05,3.1,.55,'Snow',.25)
 for off in[-1.6,1.6]:b.box((x+off,y-d/2-1.35,z+1.5),(.18,.18,3),'Wood')
 # Snow roof and visible layered fascia. Actual geometry for gable triangular fill.
 b.roof((x,y,z),w+1.9,d+2.0,h+.22,d*.29,'Roof',.38)
 b.roof((x,y,z+.34),w+2.1,d+2.1,h+.22,d*.29,'Snow',.42)
 # Ridge beam, overhanging curled corners and eave rail.
 b.cylinder((x-w/2-1.15,y,z+h+d*.29+.48),(x+w/2+1.15,y,z+h+d*.29+.48),.18,'Snow')
 for yy in[-d/2-1.0,d/2+1.0]:b.box((x,y+yy,z+h),(w+2.15,.25,.26),'DarkWood')
 for xx in[-w/2-.4,w/2+.4]:
  b.cylinder((x+xx,y-d/2-.8,z+h+.15),(x+xx,y,z+h+d*.29+.1),.12,'Wood')
  b.cylinder((x+xx,y,z+h+d*.29+.1),(x+xx,y+d/2+.8,z+h+.15),.12,'Wood')
 # Repeated snow clumps and ice needles along front roof edge.
 for i in range(int(w/.8)):
  xx=x-w/2+i*.8
  b.ellipsoid((xx,y-d/2-.94,z+h+.36),(.55,.35,.2),'Snow',8,4)
  if i%3==0:b.cylinder((xx,y-d/2-.97,z+h+.1),(xx,y-d/2-.97,z+h-.37-random.random()*.3),.075,'Snow',7,.012)
 if balcony:
  bz=z+h*.52;b.box((x,y-d/2-1.0,bz),(w+1,2.0,.23),'Wood')
  for xx in range(15):
   px=x-w/2+xx*w/14;b.box((px,y-d/2-1.85,bz+.65),(.09,.1,1.25),'Wood')
  for zz in[.25,1.25]:b.box((x,y-d/2-1.85,bz+zz),(w+.8,.13,.15),'Wood')
  b.box((x,y-d/2-1.85,bz+1.36),(w+.9,.25,.10),'Snow')
 # Chimney with wood/stone stack and snowy cap.
 b.box((x+w*.25,y+d*.15,z+h+d*.27+.5),(.9,.85,1.8),'Stone');b.box((x+w*.25,y+d*.15,z+h+d*.27+1.43),(1.2,1.1,.18),'Snow')
 # Front steps.
 for i in range(4):b.box((x,y-d/2-1.3-i*.38,z-.1-i*.18),(2.8,.52,.25),'Wood')

building('InnMain',-17,13,1.1,18,11,7.5,True)
building('Bathhouse',20,13,3.6,10,8,4.8)
building('GuestEast',29,-15,.8,10,8,5.2)
building('GuestWest',-31,-15,.8,10,8,5.0)
print('SOURCE buildings complete',flush=True)

def pool(x,y,rx,ry,z):
 p=B['Pools'];w=B['Water']
 # Closed flat-topped support solids sit entirely below the water surface.
 def support(ax,ay,low,high,mat):
  n=64;vs=[(x+ax*math.cos(2*math.pi*i/n),y+ay*math.sin(2*math.pi*i/n),zz) for zz in[low,high] for i in range(n)]
  fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
  p.add(vs,fs,mat)
 support(rx+1.5,ry+1.35,.44,z-.18,'Snow')
 support(rx+1.05,ry+.95,z-.20,z-.04,'Stone')
 w.surface_ellipse((x,y,z+.08),rx,ry,'Water',72)
 for i in range(42):
  t=2*math.pi*i/42;rr=.4+random.random()*.25
  p.ellipsoid((x+(rx+.18)*math.cos(t),y+(ry+.18)*math.sin(t),z+.12),(rr*1.4,rr,rr*.80),'Stone',10,5)
  if i%4!=0:p.ellipsoid((x+(rx+.35)*math.cos(t),y+(ry+.35)*math.sin(t),z+.4),(rr*1.2,rr*.80,.14),'Snow',10,4)
 # Pale graphic ripple rings, intentionally non-physical art.
 for rr in[.55,1.0,1.65]:
  for j in range(10):
   t=2*math.pi*j/10
   B['Pools'].cylinder((x-rx*.33+rr*math.cos(t),y+ry*.20+rr*.44*math.sin(t),z+.10),(x-rx*.33+rr*math.cos(t+.30),y+ry*.20+rr*.44*math.sin(t+.30),z+.10),.025,'Snow',6)
pool(-4,-13,10,6.2,1.0);pool(4,1,7.7,5.2,2.35);pool(16,8,4.5,3.7,3.65)

# Small waterfall lips feeding each terrace; material scrolling adds motion.
for x,y,z,w,h in [(1,-4.1,2.4,1.5,1.35),(12.3,5.8,3.72,1.0,1.2)]:
 B['Water'].box((x,y,z-h/2),(w,.20,h),'Water');B['Pools'].box((x,y+.3,z+.1),(w+.45,.7,.25),'Wood')

path=B['Paths']
def path_segment(a,b,width=2.3):
 av=Vector(a);bv=Vector(b);d=bv-av;length=d.length;ang=math.atan2(d.y,d.x)
 path.box(tuple((av+bv)/2),(length,width,.18),'Path',ang)
 for k in range(max(2,int(length/.9))):
  t=(k+.5)/max(2,int(length/.9));p=av.lerp(bv,t)
  path.box(tuple(p+Vector((random.uniform(-.12,.12),random.uniform(-.10,.10),.12))),(.72,width*.84,.12),'Stone',ang+random.uniform(-.1,.1))
route=[(0,-47,.53),(-7,-34,.53),(-15,-27,.53),(-20,-17,.60),(-18,-5,.68),(-17,5,.85)]
for a,b in zip(route,route[1:]):path_segment(a,b)
for a,b in [((-15,-27,.53),(12,-27,.53)),((12,-27,.53),(28,-23,.58)),((-20,-17,.60),(-31,-21,.65)),((13,-22,.60),(21,-5,.65)),((21,-5,.65),(22,4,3.4))]:path_segment(a,b,2.0)
# Terrace steps with clear tread/riser profile.
for i in range(12):B['Bridges'].box((21,1.0+i*.45,.8+i*.23),(3.0,.55,.28),'Wood')

def bridge(x,y,z,length,width,rot=0):
 b=B['Bridges'];co=math.cos(rot);si=math.sin(rot)
 def p(dx,dy,dz):return(x+dx*co-dy*si,y+dx*si+dy*co,z+dz)
 steps=22
 for i in range(steps):
  t=(i+.5)/steps;dx=(t-.5)*length;arch=.8*math.sin(math.pi*t)
  b.box(p(dx,0,arch),(length/steps-.035,width,.18),'Wood',rot)
 for side in[-1,1]:
  for i in range(7):
   t=i/6;dx=(t-.5)*length;arch=.8*math.sin(math.pi*t)
   b.cylinder(p(dx,side*width*.48,arch-.10),p(dx,side*width*.48,arch+1.10),.075,'DarkWood')
  for i in range(18):
   t=i/18;t2=(i+1)/18
   for h in[.38,1.08]:b.cylinder(p((t-.5)*length,side*width*.48,.8*math.sin(math.pi*t)+h),p((t2-.5)*length,side*width*.48,.8*math.sin(math.pi*t2)+h),.065,'Wood')
bridge(-3,-22,.65,8.5,2.1,0)
bridge(1,-5.3,1.3,5.3,1.5,math.pi/2)

def pine(x,y,z,s):
 b=B['Pines'];b.cylinder((x,y,z),(x,y,z+s*6.7),.23*s,'Wood',10,.10*s)
 for i,(hh,rr) in enumerate([(1.8,2.05),(3.2,1.7),(4.5,1.3),(5.7,.87)]):
  b.cylinder((x,y,z+s*hh),(x,y,z+s*(hh+2.3)),s*rr,'Pine',12,.02*s)
  b.cylinder((x,y,z+s*(hh+.45)),(x,y,z+s*(hh+2.43)),s*rr*.86,'Snow',12,.03*s)
  for k in range(6):
   t=k*math.pi/3+i*.3;b.ellipsoid((x+rr*s*.65*math.cos(t),y+rr*s*.65*math.sin(t),z+s*(hh+.65)),(.65*s,.52*s,.26*s),'Snow',8,4)
for x,y,s in[(-43,29,1.5),(-41,15,1.35),(-44,1,1.35),(-42,-11,1.2),(-43,-28,1.3),(-32,-37,1.0),(-22,-43,.85),(-13,29,1.15),(-3,30,1.1),(14,28,1.0),(33,24,1.2),(41,14,1.3),(43,-1,1.25),(44,-21,1.2),(39,-33,.95),(27,-39,.9),(13,-42,.85)]:pine(x,y,.6,s)
# Small scattered snow stone gardens, kept clear of major circulation.
for x,y,s in[(-22,-32,2.1),(-11,-37,1.3),(9,-35,1.8),(20,-32,1.1),(34,-6,1.6),(-32,0,1.8),(-35,24,2.2),(29,30,2.1),(5,24,2.4),(24,-3,1.5)]:
 for k in range(3):
  xx=x+random.uniform(-s,s);yy=y+random.uniform(-s,s);rr=s*random.uniform(.5,.8)
  B['Rocks'].ellipsoid((xx,yy,.45+rr*.35),(rr,rr*.8,rr*.75),'Stone',12,6)
  B['Rocks'].ellipsoid((xx,yy,.45+rr*.9),(rr*.86,rr*.68,rr*.28),'Snow',12,5)

lights=[]
def lantern(x,y,z=0.6,standing=True):
 b=B['Lanterns']
 if standing:
  b.box((x,y,z+.12),(.72,.72,.28),'Stone');b.cylinder((x,y,z+.25),(x,y,z+2.3),.105,'DarkWood');zz=z+2.3
 else:zz=z
 b.box((x,y,zz),(.57,.57,.83),'Window')
 for xx in[-.31,.31]:
  for yy in[-.31,.31]:b.box((x+xx,y+yy,zz),(.055,.055,.94),'DarkWood')
 for dz in[-.46,.46]:b.box((x,y,zz+dz),(.73,.73,.10),'DarkWood')
 b.roof((x,y,zz),1.0,.95,.52,.24,'Roof',.12);b.roof((x,y,zz+.1),1.05,1.0,.52,.24,'Snow',.13)
 lights.append([x,y,zz])
for x,y in[(-2,-42),(-11,-32),(-18,-25),(-22,-10),(-14,3),(12,-28),(25,-24),(23,-6),(23,6),(-30,-23),(6,-20),(7,-3)]:lantern(x,y)
for x,y,z in[(-24,6.4,3.1),(-10,6.4,3.1),(17,8.3,6),(25,-19.5,3),(33,-19.5,3),(-35,-19.6,3),(-27,-19.6,3)]:lantern(x,y,z,False)

f=B['Furnishings']
def bench(x,y,z,rot=0):
 f.box((x,y,z+.7),(2.7,.8,.18),'Wood',rot)
 for xx in[-.95,.95]:f.box((x+xx,y,z+.35),(.22,.60,.7),'DarkWood',rot)
 f.box((x,y+.32,z+1.2),(2.7,.15,.6),'Wood',rot)
for x,y,z in[(-17,-21,.6),(11,-21,.6),(-12,1,.7),(25,-8,.6),(-28,-26,.6)]:bench(x,y,z)
# Buckets, washing stools, towels and stone water spouts around pools.
for x,y,z in[(-12,-15,1.3),(5,-17,1.3),(-1,5,2.65),(19,8,3.95)]:
 f.cylinder((x,y,z),(x,y,z+.48),.30,'Wood',14,.36);f.cylinder((x,y,z+.49),(x,y,z+.51),.27,'DarkWood',14)
 for zz in[.12,.40]:
  # thin metal hoops as polygonal torus-like segments
  for k in range(14):
   a=k*2*math.pi/14;bb=(k+1)*2*math.pi/14;f.cylinder((x+.33*math.cos(a),y+.33*math.sin(a),z+zz),(x+.33*math.cos(bb),y+.33*math.sin(bb),z+zz),.022,'Brass',6)
 f.box((x+.7,y,z+.2),(.55,.42,.34),'Wood');f.box((x+.7,y,z+.40),(.62,.48,.08),'Towel')
for x,y,z in[(-9,-8,1.0),(5,4,2.35)]:
 f.cylinder((x,y,z+.2),(x,y,z+1.5),.16,'Wood');f.cylinder((x,y,z+1.4),(x+.9,y,z+1.4),.11,'Wood')
 B['Water'].cylinder((x+.85,y,z+1.35),(x+.85,y,z+.1),.055,'Water',8)
# Snow fences and low boundary of terraces.
for x0,y0,x1,y1 in[(-39,-32,-25,-32),(26,-33,37,-33),(-28,0,-28,6),(28,3,28,19)]:
 length=math.hypot(x1-x0,y1-y0);n=max(2,int(length/2))
 for i in range(n+1):
  t=i/n;x=x0+(x1-x0)*t;y=y0+(y1-y0)*t
  f.box((x,y,1.25),(.16,.16,1.5),'Wood');f.ellipsoid((x,y,2.04),(.18,.18,.1),'Snow',8,4)
 for zz in[1,1.7]:f.cylinder((x0,y0,zz),(x1,y1,zz),.075,'Wood')

entr=B['Entrance']
for xx in[-2.4,2.4]:entr.cylinder((xx,-42,.5),(xx,-42,4.2),.20,'Wood')
entr.box((0,-42,4.2),(5.8,.35,.32),'DarkWood');entr.roof((0,-42,4.2),6.5,1.8,.45,.5,'Roof',.2);entr.roof((0,-42,4.4),6.7,1.9,.45,.5,'Snow',.24)
entr.box((0,-42.18,3.7),(2.8,.16,.8),'Wood')
# Three raised onsen steam symbols on the gateway plaque.
for xx in[-.65,0,.65]:
 for k in range(6):
  t=k/6;t2=(k+1)/6
  entr.cylinder((xx+.10*math.sin(t*6),-42.29,3.44+t*.46),(xx+.10*math.sin(t2*6),-42.29,3.44+t2*.46),.028,'Brass',7)

# Steam cards have explicit outward normals; crossed planes use two-sided material.
for x,y,z,w,h,ang in[(-7,-12,1.18,4.0,3.4,.1),(-1,-14,1.18,3.7,3.0,.55),(2,0,2.5,3.6,3.8,.25),(7,1,2.5,2.8,3.1,.9),(15,8,3.8,2.6,2.8,.15)]:
 B['Steam'].vertical_card((x,y,z),w,h,ang);B['Steam'].vertical_card((x,y,z+.15),w*.85,h*.9,ang+math.pi/2)

# Convert data to meshes. Each disconnected closed component's signed volume is
# checked and corrected before normals/UVs are authored. Open surfaces preserve
# explicit top/front direction and are audited separately.
validation={'started_at_utc':datetime.fromtimestamp(T0,timezone.utc).isoformat(),'textures':texmeta,'meshes':[],'coordinate_bake':'Blender source Y is mirrored and winding reversed before export; FBX UE conversion mirrors it back to authored UE world coordinates. Actors remain unit scale.','uv_policy':{'mapping':'dominant-axis planar metres / tile_metres, recomputed after applied bevel; Steam normalized per card','overlap':'intentional repeating tile coordinates shared across disconnected primitive surfaces; no packed lightmap UV','padding':'not applicable to wrap/repeating texture coordinates','density_tolerance':'dominant-axis projection has cosine contraction on curved faces; measured per triangle'}}
manifest={'meshes':[],'materials':{n:{'color':c,'roughness':r,'tile_m':t,'texture':('T_'+n+'.png') if n in texmeta else None} for n,(c,r,t) in MATS.items()},'lights_m':lights,'footprint_m':100}
for name,bu in B.items():
 if not bu.v:continue
 flipped=0;closedvol=[];open_normals=[]
 for comp in bu.components:
  fs=bu.f[comp['first_face']:comp['first_face']+comp['faces']]
  if comp['closed']:
   volume=0
   for face in fs:
    a=Vector(bu.v[face[0]])
    for j in range(1,len(face)-1):volume+=a.dot(Vector(bu.v[face[j]]).cross(Vector(bu.v[face[j+1]])))/6
   if volume<0:
    for ii in range(comp['first_face'],comp['first_face']+comp['faces']):bu.f[ii]=tuple(reversed(bu.f[ii]))
    volume=-volume;flipped+=1
   assert volume>1e-10,(name,comp,volume)
   closedvol.append(volume)
 mesh=bpy.data.meshes.new(bu.name);mesh.from_pydata([(x,-y,z) for x,y,z in bu.v],[],[tuple(reversed(f)) for f in bu.f]);mesh.update();ob=bpy.data.objects.new(bu.name,mesh);bpy.context.collection.objects.link(ob)
 for ma in mats.values():mesh.materials.append(ma)
 uv=mesh.uv_layers.new(name='UVMap');density=[];degenerate=0
 for poly,mi,sm in zip(mesh.polygons,bu.mi,bu.sm):
  poly.material_index=mi;poly.use_smooth=sm;normal=poly.normal;axis=max(range(3),key=lambda i:abs(normal[i]));indices=([1,2] if axis==0 else [0,2] if axis==1 else [0,1]);tile=list(MATS.values())[mi][2]
  for corner,li in enumerate(poly.loop_indices):
   co=mesh.vertices[mesh.loops[li].vertex_index].co
   uv.data[li].uv=([(0,0),(1,0),(1,1),(0,1)][corner] if list(MATS)[mi]=='Steam' else (co[indices[0]]/tile,co[indices[1]]/tile))
 mesh.calc_loop_triangles()
 for tri in mesh.loop_triangles:
  a,b,c=[mesh.vertices[i].co for i in tri.vertices];area=(b-a).cross(c-a).length/2
  uvv=[uv.data[i].uv for i in tri.loops];ua=abs((uvv[1].x-uvv[0].x)*(uvv[2].y-uvv[0].y)-(uvv[1].y-uvv[0].y)*(uvv[2].x-uvv[0].x))/2
  if area<1e-12:degenerate+=1
  else:density.append(1024*math.sqrt(ua/area))
 assert degenerate==0,(name,'degenerate faces',degenerate)
 assert all(math.isfinite(k) for d in uv.data for k in d.uv)
 for comp in bu.components:
  if not comp['closed']:
   ns=[tuple(mesh.polygons[i].normal) for i in range(comp['first_face'],comp['first_face']+comp['faces'])];open_normals.append({'material':comp['material'],'normal_sample':ns[0],'front_up_positive':all(n[2]>.99 for n in ns) if comp['material']=='Water' else None,'two_sided':comp['material']=='Steam'})
 # Bevel selected angular architecture edges; bounded one pass per semantic mesh.
 if name in ['InnMain','Bathhouse','GuestEast','GuestWest','Bridges','Entrance']:
  mod=ob.modifiers.new('Soft crafted corners','BEVEL');mod.width=.035;mod.segments=2;mod.limit_method='ANGLE';mod.angle_limit=.7
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
  bpy.ops.object.modifier_apply(modifier=mod.name);mesh=ob.data
  bm=bmesh.new();bm.from_mesh(mesh)
  bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0.00001)
  bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=0.00001)
  bmesh.ops.triangulate(bm,faces=list(bm.faces))
  bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=0.00001)
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
  bm.to_mesh(mesh);bm.free();mesh.update();uv=mesh.uv_layers.active
  # Bevel UV interpolation collapses strips at projected face boundaries;
  # author actual final face UVs instead, with the same physical density.
  for poly in mesh.polygons:
   axis=max(range(3),key=lambda i:abs(poly.normal[i]));indices=([1,2] if axis==0 else [0,2] if axis==1 else [0,1]);tile=list(MATS.values())[poly.material_index][2]
   for li in poly.loop_indices:
    co=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=(co[indices[0]]/tile,co[indices[1]]/tile)
  mesh.calc_loop_triangles()
 mn=[min(v[i] for v in bu.v) for i in range(3)];mx=[max(v[i] for v in bu.v) for i in range(3)]
 rec={'name':bu.name,'vertices':len(mesh.vertices),'faces':len(mesh.polygons),'triangles':len(mesh.loop_triangles),'components':len(bu.components),'closed_components':len(closedvol),'closed_min_volume_m3':min(closedvol) if closedvol else None,'corrected_inward_components':flipped,'open_surface_checks':open_normals,'uv_all_finite':True,'degenerate_triangles':degenerate,'density_px_per_m':{'min':min(density),'median':statistics.median(density),'max':max(density)},'bounds_m':{'min':mn,'max':mx}}
 validation['meshes'].append(rec);manifest['meshes'].append({'name':bu.name,'fbx':bu.name+'.fbx','bounds_m':rec['bounds_m'],'materials':list(MATS)})
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.export_scene.fbx(filepath=str(OUT/(bu.name+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,global_scale=1,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,path_mode='STRIP')
 print('SOURCE exported',bu.name,len(mesh.loop_triangles),'triangles',flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SnowyOnsen_original.blend'))
validation['finished_at_utc']=datetime.now(timezone.utc).isoformat();validation['elapsed_seconds']=time.time()-T0
(ROOT/'Validation'/'source_validation.json').write_text(json.dumps(validation,indent=2),encoding='utf8')
(OUT/'scene_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print('SOURCE COMPLETE',json.dumps({'seconds':validation['elapsed_seconds'],'meshes':len(manifest['meshes']),'triangles':sum(m['triangles'] for m in validation['meshes'])}),flush=True)
