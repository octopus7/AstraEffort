"""Quietwater Grove: independently authored procedural source art (metres)."""
import bpy, math, random, json, os
from mathutils import Vector
from pathlib import Path

ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra')
OUT=ROOT/'SourceArt'; OUT.mkdir(exist_ok=True)
random.seed(43175)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=1.0
PAL={
 'Grass':(0.265,0.37,0.19,1),'Sand':(.66,.55,.36,1),
 'Bark':(.24,.17,.105,1),'BarkLight':(.38,.28,.17,1),
 'LeafSage':(.24,.38,.22,1),'LeafMoss':(.14,.28,.16,1),'LeafLight':(.34,.45,.24,1),
 'Pine':(.12,.29,.23,1),'PineTip':(.24,.38,.27,1),
 'Rock':(.36,.40,.38,1),'RockLight':(.46,.49,.43,1),'RockMoss':(.23,.33,.20,1),
 'Fern':(.24,.39,.22,1),'Stem':(.32,.37,.16,1),'ReedHead':(.32,.23,.12,1),
 'Petal':(.70,.64,.44,1),'PetalBlue':(.36,.42,.53,1),'Wood':(.39,.28,.16,1),
 'Endgrain':(.53,.40,.24,1),'Iron':(.12,.15,.14,1),
 'Lake':(.16,.38,.35,1),'Sea':(.19,.40,.42,1),'Foam':(.65,.73,.62,1),
 'WetSand':(.43,.40,.29,1)
}
MATS={}
for name,c in PAL.items():
 m=bpy.data.materials.new(name); m.diffuse_color=c; MATS[name]=m

def objmesh(name,verts,faces,mat,colors=None):
 me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
 ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob)
 me.materials.append(MATS[mat])
 for p in me.polygons:p.use_smooth=True
 if colors:
  attr=me.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
  for i,c in enumerate(colors): attr.data[i].color=c
 return ob

def blob(name,center,scale,mat,seed,segments=16,rings=10,rough=.10):
 rng=random.Random(seed); phase=[rng.uniform(0,6.28) for _ in range(4)]
 verts=[]
 for j in range(rings+1):
  t=math.pi*(j+.001)/(rings+.002)
  for i in range(segments):
   a=2*math.pi*i/segments
   q=1+rough*(math.sin(3*a+phase[0])*math.sin(t)**2+.45*math.cos(5*a+2*t+phase[1]))
   verts.append((center[0]+scale[0]*q*math.sin(t)*math.cos(a),center[1]+scale[1]*q*math.sin(t)*math.sin(a),center[2]+scale[2]*q*math.cos(t)))
 faces=[]
 for j in range(rings):
  for i in range(segments):faces.append((j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i))
 return objmesh(name,verts,faces,mat)

def tube(name,points,radii,mat,sides=9):
 verts=[]
 for j,p in enumerate(points):
  direction=Vector(points[min(j+1,len(points)-1)])-Vector(points[max(0,j-1)])
  direction.normalize(); axis=direction.cross(Vector((0,1,0)))
  if axis.length<.01:axis=direction.cross(Vector((1,0,0)))
  axis.normalize(); other=direction.cross(axis)
  for i in range(sides):
   a=2*math.pi*i/sides; v=Vector(p)+radii[j]*(math.cos(a)*axis+math.sin(a)*other); verts.append(v)
 faces=[tuple(reversed(range(sides))),tuple((len(points)-1)*sides+i for i in range(sides))]
 for j in range(len(points)-1):
  for i in range(sides):faces.append((j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i))
 return objmesh(name,verts,faces,mat)

def bevelbox(name,center,scale,mat,bevel=.08):
 bpy.ops.mesh.primitive_cube_add(size=1,location=center); ob=bpy.context.object; ob.name=name; ob.dimensions=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 ob.data.materials.append(MATS[mat]); mod=ob.modifiers.new('soft worn corners','BEVEL');mod.width=bevel;mod.segments=3
 bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=mod.name)
 for p in ob.data.polygons:p.use_smooth=True
 return ob

ASSETS={}; PLACEMENTS=[]
def finish(name,parts,collision='simple'):
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();ob=parts[0];ob.name=name
 bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',axis_forward='-Y',axis_up='Z',bake_anim=False,add_leaf_bones=False,use_mesh_modifiers=True)
 ASSETS[name]={'materials':[m.name for m in ob.data.materials],'collision':collision,'vertices':len(ob.data.vertices),'polygons':len(ob.data.polygons)}
 ob.hide_set(True);ob.hide_render=True
 return ob

def place(asset,x,y,z=None,scale=1,yaw=0,label=None):
 if z is None:z=height(x,y)
 if isinstance(scale,(float,int)):scale=[scale]*3
 PLACEMENTS.append(dict(asset=asset,location=[x,y,z],scale=scale,yaw=yaw,label=label or asset))

def coast(x):return -32+2.2*math.sin(x*.075)+1.5*math.cos(x*.13+.5)
def lake_r(x,y):
 dx=(x+15)/12;dy=(y-8)/9.5;a=math.atan2(dy,dx)
 return math.sqrt(dx*dx+dy*dy)/(1+.08*math.sin(3*a)+.035*math.cos(5*a))
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def height(x,y):
 land=1.6+.35*math.sin(x*.11)*math.cos(y*.09)+2.5*math.exp(-((x-31)**2+(y-32)**2)/950)+1.25*math.exp(-((x+34)**2+(y-33)**2)/450)
 land*=smooth(-5,7,y-coast(x));land-=1.8*(1-smooth(-8,1,y-coast(x)))
 r=lake_r(x,y);land=land*(smooth(.67,1.16,r))+.24*(1-smooth(.67,1.16,r))
 return land
PATH=[(-3,-30),(0,-23),(7,-17),(12,-8),(9,1),(3,9),(-1,18),(-11,24),(-20,33),(-23,45)]
def pathdist(x,y):
 best=100
 for (ax,ay),(bx,by) in zip(PATH[:-1],PATH[1:]):
  t=max(0,min(1,((x-ax)*(bx-ax)+(y-ay)*(by-ay))/((bx-ax)**2+(by-ay)**2)))
  best=min(best,math.hypot(x-ax-t*(bx-ax),y-ay-t*(by-ay)))
 return best

# Continuous sculpted landscape with softly blended sand and trail vertex paint.
N=144;verts=[];colors=[];faces=[]
for j in range(N+1):
 y=-50+100*j/N
 for i in range(N+1):
  x=-50+100*i/N;z=height(x,y);verts.append((x,y,z))
  coast_sand=1-smooth(3,9,y-coast(x));trail=1-smooth(.85,2.3,pathdist(x,y))
  lakebank=(1-smooth(1.04,1.23,lake_r(x,y)))*.48
  sand=max(coast_sand,trail*.77,lakebank)
  shade=.94+.06*math.sin(x*.5+y*.7)+.035*math.cos(y*1.1-x*.4)
  c=[(PAL['Grass'][k]*(1-sand)+PAL['Sand'][k]*sand)*shade for k in range(3)]+[1];colors.append(c)
for j in range(N):
 for i in range(N):
  a=j*(N+1)+i;faces.append((a,a+1,a+N+2,a+N+1))
finish('SM_Ground', [objmesh('Ground',verts,faces,'Grass',colors)],'complex');place('SM_Ground',0,0,0)

# Ocean remains within the exact 100m footprint. Inland lake is a separate mesh.
verts=[];faces=[]
for j in range(17):
 for i in range(101):
  x=-50+i;v=j/16;y=-50+(coast(x)+50-1.8)*v;verts.append((x,y,-.34+.025*math.sin(x*.7+y*.8)))
for j in range(16):
 for i in range(100):a=j*101+i;faces.append((a,a+1,a+102,a+101))
finish('SM_Sea',[objmesh('Sea',verts,faces,'Sea')],'none');place('SM_Sea',0,0,0)
verts=[(-15,8,1.04)];count=96
for i in range(count):
 a=2*math.pi*i/count;r=.975*(1+.08*math.sin(3*a)+.035*math.cos(5*a));verts.append((-15+12*r*math.cos(a),8+9.5*r*math.sin(a),1.04))
faces=[(0,i+1,(i+1)%count+1) for i in range(count)]
finish('SM_Lake',[objmesh('Lake',verts,faces,'Lake')],'none');place('SM_Lake',0,0,0)

def ribbon(name,points,width,mat):
 vs=[]
 for i,p in enumerate(points):
  d=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)]);d.z=0;d.normalize();n=Vector((-d.y,d.x,0))*width*.5
  vs.extend([Vector(p)-n,Vector(p)+n])
 return objmesh(name,vs,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(points)-1)],mat)
parts=[]
for line in range(3):
 pts=[]
 for i in range(101):
  x=-50+i;y=coast(x)-2.0-line*1.65+.2*math.sin(x*.6+line);pts.append((x,y,-.285+.015*line))
 parts.append(ribbon('soft surf',pts,.12 if line==0 else .065,'Foam'))
finish('SM_Surf',[*parts],'none');place('SM_Surf',0,0,0)

# Five individual canopy trees: shaped branching trunks and asymmetrical rounded crowns.
for variant in range(5):
 rng=random.Random(100+variant);parts=[];h=7.6+variant*.6
 parts.append(tube('rooted trunk',[(0,0,-.1),(.12,-.06,.8),(-.12,.04,h*.42),(.35,.1,h*.73)],[.48,.37,.23,.12],'Bark',11))
 for k in range(5):
  a=k*6.283/5+.4;end=(math.cos(a)*.95,math.sin(a)*.95,.04)
  parts.append(tube('root',[end,(end[0]*.4,end[1]*.4,.35),(0,0,.85)],[.09,.21,.30],'Bark',7))
 centers=[(-1.4,-.4,h*.71),(1.2,-.2,h*.77),(.3,1.3,h*.76),(-.1,-.1,h*.96)]
 for k,c in enumerate(centers):
  parts.append(tube('branch',[(0,0,h*.43),(c[0]*.55,c[1]*.55,h*.61),c],[.18,.12,.055],'Bark',8))
  parts.append(blob('sculpted crown',c,(2.25+rng.random()*.35,1.9+rng.random()*.35,1.9+rng.random()*.4),['LeafMoss','LeafSage','LeafLight'][(variant+k)%3],300+variant*10+k,20,14,.085))
 finish('SM_Broadleaf_%02d'%variant,parts)

for variant in range(3):
 parts=[];h=9+variant*1.3
 parts.append(tube('pine trunk',[(0,0,0),(.08,0,h*.5),(0,.05,h*.95)],[.36,.21,.04],'Bark',9))
 for tier in range(5):
  z=2.8+tier*(h-3)/5;r=(2.6-tier*.38)*(1+variant*.08);vs=[];fs=[];seg=18
  for j,(q,dz) in enumerate([(1,0),(.98,.4),(.8,.95),(.43,1.65),(.025,2.15)]):
   for i in range(seg):
    a=i*2*math.pi/seg;rr=r*q*(1+.055*math.sin(a*5+tier));vs.append((rr*math.cos(a),rr*math.sin(a),z+dz+.12*math.sin(a*3)*(1-j/4)))
  for j in range(4):
   for i in range(seg):fs.append((j*seg+i,j*seg+(i+1)%seg,(j+1)*seg+(i+1)%seg,(j+1)*seg+i))
  fs.append(tuple(reversed(range(seg))));parts.append(objmesh('rounded pine whorl',vs,fs,'PineTip' if tier%2 else 'Pine'))
 finish('SM_Pine_%02d'%variant,parts)

for variant in range(5):
 parts=[blob('river worn granite',(0,0,.55),(1.4+variant*.12,1.05+variant*.09,.95+variant*.1),'Rock' if variant%2 else 'RockLight',500+variant,16,10,.15)]
 if variant in [1,3]:parts.append(blob('moss shoulder',(-.2,.1,1.21+variant*.07),(.9,.68,.16),'RockMoss',700+variant,14,7,.12))
 finish('SM_Rock_%02d'%variant,parts)

def leaf(name,base,tip,width,mat):
 b=Vector(base);t=Vector(tip);d=t-b;side=Vector((-d.y,d.x,0)).normalized()*width
 mid=b+d*.52+Vector((0,0,.10))
 return objmesh(name,[b,mid-side,mid+Vector((0,0,.035)),mid+side,t],[(0,1,2),(0,2,3),(1,4,2),(2,4,3)],mat)
for variant in range(3):
 parts=[];rng=random.Random(800+variant)
 for k in range(9):
  a=k*2.399;length=rng.uniform(.38,.85);base=(rng.uniform(-.12,.12),rng.uniform(-.12,.12),0)
  parts.append(leaf('bent grass',base,(base[0]+math.cos(a)*length*.5,base[1]+math.sin(a)*length*.5,length),.065,'LeafLight' if k%4==0 else 'Grass'))
 finish('SM_Grass_%02d'%variant,parts,'none')
parts=[]
for k in range(9):
 a=k*2.399;L=.85 if k%2 else 1.15
 pts=[(0,0,.08),(.34*L*math.cos(a),.34*L*math.sin(a),.62*L),(.95*L*math.cos(a),.95*L*math.sin(a),.47*L)]
 parts.append(tube('fern spine',pts,[.018,.015,.006],'Stem',5))
 for n in range(1,8):
  t=n/8;r=t*.95*L;z=(.11+.7*math.sin(t*2))*L
  for s in [-1,1]:
   w=.28*math.sin(math.pi*t)*L;tip=(r*math.cos(a)+s*w*math.cos(a+1.4),r*math.sin(a)+s*w*math.sin(a+1.4),z-.03)
   parts.append(leaf('fern leaflet',(r*math.cos(a),r*math.sin(a),z),tip,.055,'Fern'))
finish('SM_Fern',parts,'none')
parts=[]
for k in range(7):
 a=k*2.4;x=.25*math.cos(a);y=.25*math.sin(a);h=1.4+random.random()*.65
 parts.append(tube('reed',[(x,y,0),(x+.05,y,h*.6),(x+.13,y,h)],[.024,.018,.012],'Stem',6))
 parts.append(blob('seed head',(x+.13,y,h-.04),(.055,.055,.22),'ReedHead',k,8,6,.03))
 parts.append(leaf('reed blade',(x,y,.2),(x+.4*math.cos(a),y+.4*math.sin(a),h*.8),.07,'Fern'))
finish('SM_Reeds',parts,'none')
for var in range(2):
 parts=[]
 for k in range(5):
  a=k*2.4;x=.25*math.cos(a);y=.25*math.sin(a);z=.33+.16*(k%3)
  parts.append(tube('stem',[(x,y,0),(x+.02,y,z)],[.015,.01],'Stem',5))
  for n in range(5):
   b=n*6.28/5;parts.append(blob('petal',(x+.085*math.cos(b),y+.085*math.sin(b),z),(.075,.06,.026),'Petal' if var==0 else 'PetalBlue',k*5+n,8,5,.04))
 finish('SM_Flowers_%02d'%var,parts,'none')

parts=[tube('fallen trunk',[(-1.8,0,.38),(-.5,.08,.4),(1.7,.12,.36)],[.35,.39,.29],'Bark',12),tube('endgrain',[(1.705,.12,.36),(1.72,.12,.36)],[.25,.25],'Endgrain',12),tube('broken branch',[(-.2,.06,.4),(.05,.6,.68),(.1,.85,.8)],[.17,.11,.06],'Bark',8)]
finish('SM_Log',parts)
parts=[]
for i in range(11):parts.append(bevelbox('weathered board',(-1.6+i*.32,0,.4),(.29,2.2,.14),'Wood',.035))
for x in [-1.5,1.5]:
 for y in [-.88,.88]:parts.append(tube('post',[(x,y,-1.2),(x,y,.68)],[.11,.105],'Bark',9))
parts.append(bevelbox('support',(0,-.8,.18),(3.65,.17,.24),'Wood',.03));parts.append(bevelbox('support',(0,.8,.18),(3.65,.17,.24),'Wood',.03))
finish('SM_LakeLanding',parts,'complex')
parts=[bevelbox('seat',(0,0,.65),(1.9,.53,.16),'Wood'),bevelbox('foot',(-.65,0,.28),(.22,.5,.56),'Bark'),bevelbox('foot',(.65,0,.28),(.22,.5,.56),'Bark')]
finish('SM_Bench',parts)

# Intentional spatial composition: forest enclosure and open lake/meadow corridor.
placed=[]
for attempt in range(1800):
 x=random.uniform(-47,47);y=random.uniform(-23,47);r=lake_r(x,y)
 if r<1.48 or pathdist(x,y)<4.3:continue
 if y<8 and x>-12 and x<24 and random.random()<.88:continue
 if y<-10 and random.random()<.65:continue
 if any(math.hypot(x-a,y-b)<5.2 for a,b in placed):continue
 placed.append((x,y));asset=('SM_Pine_%02d'%random.randrange(3)) if (x>18 or y>29) and random.random()<.60 else ('SM_Broadleaf_%02d'%random.randrange(5))
 place(asset,x,y,scale=random.uniform(.74,1.2),yaw=random.uniform(0,360),label='Forest canopy %03d'%len(placed))
 if len(placed)>=104:break

# Rock ridge on east; shoreline and forest groupings.
for group,(cx,cy,n) in enumerate([(32,17,13),(38,31,9),(-34,24,7),(-30,-18,5),(31,-29,7),(-45,-32,5)]):
 for j in range(n):
  x=cx+random.uniform(-4.7,4.7);y=cy+random.uniform(-3.8,3.8)
  s=random.uniform(.7,1.9) if group>1 else random.uniform(1.5,3)
  place('SM_Rock_%02d'%random.randrange(5),x,y,scale=[s,s*random.uniform(.8,1.2),s*.85],yaw=random.uniform(0,360),label='Granite group %d'%group)
for i in range(27):
 a=i*6.283/27;x=-15+13.8*math.cos(a);y=8+10.8*math.sin(a)
 if pathdist(x,y)>2.2 and i%3!=0:place('SM_Rock_%02d'%(i%5),x,y,scale=random.uniform(.35,.72),yaw=i*34,label='Lake edge stone')
for i in range(33):
 a=random.uniform(0,6.283);x=-15+11.7*math.cos(a);y=8+9.3*math.sin(a)
 if x>-5 and y<13:continue
 place('SM_Reeds',x,y,z=.85,scale=random.uniform(.7,1),yaw=random.uniform(0,360),label='Lake reedbed')

for i in range(1450):
 x=random.uniform(-47,47);y=random.uniform(-26,47)
 if lake_r(x,y)<1.23 or pathdist(x,y)<2.0 or y-coast(x)<6:continue
 if random.random()>.56:continue
 asset='SM_Grass_%02d'%random.randrange(3)
 if i%8==0:asset='SM_Fern'
 elif i%13==0:asset='SM_Flowers_%02d'%random.randrange(2)
 place(asset,x,y,scale=random.uniform(.65,1.3),yaw=random.uniform(0,360),label='Understory')
for x,y,yaw in [(-32,1,27),(26,3,-32),(-28,-25,65),(33,-32,15),(-7,32,70)]:place('SM_Log',x,y,scale=random.uniform(.8,1.3),yaw=yaw,label='Weathered fallen timber')
place('SM_LakeLanding',-2.9,7.0,z=1.14,yaw=0,label='Small lake landing')
place('SM_Bench',3.8,12.7,yaw=-52,label='Lake overlook bench')
# A stepping-stone rhythm where the trail approaches the lake.
for i in range(9):
 t=i/8;x=8-4.3*t;y=1+6.7*t;place('SM_Rock_%02d'%(i%5),x,y,z=height(x,y)-.15,scale=[.40,.34,.18],yaw=i*26,label='Trail stepping stone')

manifest={'title':'Quietwater Grove','seed':43175,'dimensions_m':[100,100],'assets':ASSETS,'placements':PLACEMENTS,'palette':PAL,'height_samples':[[x,y,height(x,y)] for x,y in [(0,-20),(15,0),(0,30),(-35,15),(35,35),(-15,8)]],'lake_center_m':[-15,8,1.04],'player_start_m':[1,-23,height(1,-23)+1.1]}
(ROOT/'scene_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Quietwater_Source.blend'))
print('ULTRA_ART_COMPLETE',len(ASSETS),'assets',len(PLACEMENTS),'placements')
