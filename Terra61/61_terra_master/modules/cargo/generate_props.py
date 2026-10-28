#!/usr/bin/env python3
"""Build three independent low-poly Victorian platform props, Y up, metres."""
from pathlib import Path
import json,math,struct
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageEnhance
P=Path(__file__).resolve().parent;P.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(110213)

# Original procedural wood with painted plank joints and subtle knots.
def wood_texture(name,planks=0,base=(126,86,56),size=512):
 w=h=size
 ys=np.arange(h)[:,None];xs=np.arange(w)[None,:]
 coarse=rng.normal(0,6,(h//4,w//4))
 coarse=np.asarray(Image.fromarray(np.uint8(np.clip(coarse+128,0,255))).resize((w,h),Image.Resampling.BICUBIC),float)-128
 fine=rng.normal(0,3,(h,w));grain=np.repeat(rng.normal(0,5,(1,w)),h,axis=0)
 data=np.stack([np.clip(c+coarse+fine+grain,0,255) for c in base],axis=2).astype('uint8');im=Image.fromarray(data,'RGB');d=ImageDraw.Draw(im)
 for _ in range(250):
  x=int(rng.integers(w));y=int(rng.integers(h));length=int(rng.integers(3,110));bright=int(rng.integers(-23,19));color=tuple(int(np.clip(c+bright,0,255)) for c in base)
  d.line((x,y,x+int(rng.integers(-2,3)),min(h-1,y+length)),fill=color,width=1)
 if planks:
  for k in range(planks):
   x=round(k*w/planks);d.line((x,0,x,h),fill=(48,34,25),width=3);d.line((x+3,0,x+3,h),fill=(171,123,79),width=1)
 for _ in range(5):
  x=int(rng.integers(25,w-25));y=int(rng.integers(25,h-25));rx=int(rng.integers(3,8));ry=int(rng.integers(7,16));d.ellipse((x-rx,y-ry,x+rx,y+ry),outline=(70,48,32),width=1);d.ellipse((x-rx//2,y-ry//2,x+rx//2,y+ry//2),outline=(72,48,32),width=1)
 im.save(P/name)
wood_texture('crate_planks.png',6)
wood_texture('wood_beam.png',0,base=(139,95,60))
wood_texture('barrel_staves.png',16,base=(121,79,49))
wood_texture('barrel_lid.png',6,base=(127,86,55))

# Downsize the project-supplied generated iron for compact prop assets. Rivets
# on the crate plates and hoops are drawn into the texture, not modeled spheres.
source=P.parent.parent/'materials'/'ai_aged_cast_iron.png'
if source.exists():
 metal=Image.open(source).convert('RGB').resize((512,512),Image.Resampling.LANCZOS)
elif (P/'iron_ai_small.png').exists():
 metal=Image.open(P/'iron_ai_small.png').convert('RGB')
else:
 raise FileNotFoundError('Need project ai_aged_cast_iron.png or local iron_ai_small.png')
metal.save(P/'iron_ai_small.png',optimize=True)
metal.resize((512,128),Image.Resampling.LANCZOS).save(P/'iron_plain.png',optimize=True)
rivet=metal.resize((512,128),Image.Resampling.LANCZOS);d=ImageDraw.Draw(rivet)
for x in (128,384):
 y=64;d.ellipse((x-12,y-12,x+12,y+12),fill=(25,26,25));d.ellipse((x-9,y-10,x+8,y+7),fill=(91,91,81));d.ellipse((x-6,y-7,x-2,y-3),fill=(153,149,130))
rivet.save(P/'iron_riveted.png',optimize=True)
plate=metal.resize((128,256),Image.Resampling.LANCZOS);d=ImageDraw.Draw(plate)
for y in (65,190):
 x=64;d.ellipse((x-11,y-11,x+11,y+11),fill=(23,24,23));d.ellipse((x-8,y-9,x+8,y+7),fill=(100,98,86));d.ellipse((x-5,y-6,x-2,y-3),fill=(171,166,143))
plate.save(P/'rivet_plate.png',optimize=True)
Image.new('RGB',(16,16),(175,131,64)).save(P/'aged_gold.png')

# Cream numeral and brass keyline are baked into the front/back sign texture.
sign=Image.new('RGB',(512,640),(28,36,40));d=ImageDraw.Draw(sign)
d.rectangle((8,8,503,631),outline=(102,73,43),width=12);d.rectangle((24,24,487,615),outline=(202,158,93),width=7)
for x in (40,472):
 for y in (40,600):
  d.ellipse((x-11,y-11,x+11,y+11),fill=(68,47,28));d.ellipse((x-8,y-8,x+7,y+7),fill=(205,160,85));d.ellipse((x-5,y-5,x-2,y-2),fill=(244,219,151))
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',435)
b=d.textbbox((0,0),'3',font=font);d.text(((512-(b[2]-b[0]))/2,(640-(b[3]-b[1]))/2-b[1]-3),'3',font=font,fill=(233,211,165))
sign.save(P/'platform_3.png')

class Mesh:
 def __init__(self,name):self.name=name;self.p=[];self.n=[];self.uv=[];self.idx=[]
 def face(self,pts,uv=None):
  pts=np.asarray(pts,float);n=np.cross(pts[1]-pts[0],pts[2]-pts[0]);size=np.linalg.norm(n)
  if size<1e-10:return
  n/=size;start=len(self.p);self.p.extend(pts.tolist());self.n.extend([n.tolist()]*len(pts))
  if uv is None:uv=[[0,0],[1,0],[1,1],[0,1]] if len(pts)==4 else [[0,0],[1,0],[.5,1]]
  self.uv.extend(uv);self.idx.extend([start,start+1,start+2]);
  if len(pts)==4:self.idx.extend([start,start+2,start+3])
 def beam(self,p0,p1,w,depth,ref=(0,0,1)):
  p0=np.asarray(p0,float);p1=np.asarray(p1,float);axis=p1-p0;length=np.linalg.norm(axis)
  if length<1e-10:return
  axis/=length;ref=np.asarray(ref,float)
  if abs(np.dot(axis,ref))>.96:ref=np.array((0,1,0),float)
  a=np.cross(ref,axis);a/=np.linalg.norm(a);b=np.cross(axis,a);a*=w/2;b*=depth/2
  q=[p0-a-b,p0+a-b,p0+a+b,p0-a+b,p1-a-b,p1+a-b,p1+a+b,p1-a+b]
  for j,f in enumerate(((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))):
   uv=[[0,0],[1,0],[1,1],[0,1]] if j<2 else [[0,0],[0,1],[length/.8,1],[length/.8,0]]
   self.face([q[k] for k in f],uv)
 def box(self,x,y,z,sx,sy,sz):self.beam((x,y-sy/2,z),(x,y+sy/2,z),sx,sz)
 def textured_box(self,x0,x1,y0,y1,z0,z1):
  # Each face takes the complete texture so the planks remain readily visible.
  for f in (((x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)),
            ((x1,y0,z0),(x0,y0,z0),(x0,y1,z0),(x1,y1,z0)),
            ((x1,y0,z1),(x1,y0,z0),(x1,y1,z0),(x1,y1,z1)),
            ((x0,y0,z0),(x0,y0,z1),(x0,y1,z1),(x0,y1,z0)),
            ((x0,y1,z1),(x1,y1,z1),(x1,y1,z0),(x0,y1,z0)),
            ((x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1))):
   self.face(f,[[0,1],[1,1],[1,0],[0,0]])
 def cylinder(self,p0,p1,r,segments=10):
  p0=np.asarray(p0,float);p1=np.asarray(p1,float);axis=p1-p0;axis/=np.linalg.norm(axis);ref=np.array((0,0,1),float)
  if abs(np.dot(axis,ref))>.96:ref=np.array((0,1,0),float)
  a=np.cross(ref,axis);a/=np.linalg.norm(a);b=np.cross(axis,a)
  for i in range(segments):
   aa=2*math.pi*i/segments;bb=2*math.pi*(i+1)/segments;r0=r*(a*math.cos(aa)+b*math.sin(aa));r1=r*(a*math.cos(bb)+b*math.sin(bb))
   self.face([p0+r0,p0+r1,p1+r1,p1+r0]);self.face([p0,p0+r1,p0+r0]);self.face([p1,p1+r0,p1+r1])

# A freestanding cast-iron sign. Decorative scroll is actual slim geometry;
# numeral, its lining and round pin heads are on the image map.
sign_m={x:Mesh(x) for x in ('iron_plain','aged_gold','platform_3')};I=sign_m['iron_plain'];G=sign_m['aged_gold'];S=sign_m['platform_3']
I.box(0,.06,0,.40,.12,.38);I.box(0,.16,0,.33,.08,.32);I.box(0,.31,0,.27,.22,.26)
for y,w in ((.22,.30),(.43,.31),(.51,.25)):
 I.box(0,y,0,w,.065,w)
for y,r,h in ((.55,.15,.10),(.65,.12,.10),(2.73,.10,.08),(2.82,.12,.08),(2.91,.09,.10)):
 I.cylinder((0,y-h/2,0),(0,y+h/2,0),r,12)
I.cylinder((0,.68,0),(0,2.74,0),.065,12)
for theta in np.linspace(0,2*math.pi,7,endpoint=False):
 x=.066*math.cos(theta);z=.066*math.sin(theta);I.cylinder((x,.74,z),(x,2.62,z),.012,6)
for y,r in ((.57,.15),(.68,.115),(2.71,.102),(2.85,.10)):
 G.cylinder((0,y-.015,0),(0,y+.015,0),r,12)
I.cylinder((0,2.96,0),(0,3.01,0),.06,10)
# a small conical tip
for i in range(10):
 a=2*math.pi*i/10;b=2*math.pi*(i+1)/10
 I.face([(0,3.11,0),(.07*math.cos(a),3.01,.07*math.sin(a)),(.07*math.cos(b),3.01,.07*math.sin(b))])
I.beam((.08,2.77,0),(1.02,2.77,0),.065,.07)
G.cylinder((.96,2.77,-.045),(.96,2.77,.045),.045,10)
# cast curved bracket and scroll
curve=[(.07,2.28,0),(.15,2.39,0),(.24,2.48,0),(.36,2.55,0),(.49,2.63,0),(.65,2.71,0)]
for a,b in zip(curve,curve[1:]):I.beam(a,b,.045,.045)
for i in range(12):
 a=2*math.pi*i/12;b=2*math.pi*(i+1)/12
 I.beam((.22+.10*math.cos(a),2.58+.10*math.sin(a),0),(.22+.10*math.cos(b),2.58+.10*math.sin(b),0),.028,.035)
for x in (.53,.91):I.beam((x,2.77,0),(x,2.57,0),.03,.03)
# A thin backing board plus separate, correctly oriented front and rear images.
I.box(.72,2.25,0,.54,.68,.06)
x0,x1=.46,.98;y0,y1=1.92,2.58
S.face([(x0,y0,.032),(x1,y0,.032),(x1,y1,.032),(x0,y1,.032)],[[0,1],[1,1],[1,0],[0,0]])
S.face([(x1,y0,-.032),(x0,y0,-.032),(x0,y1,-.032),(x1,y1,-.032)],[[0,1],[1,1],[1,0],[0,0]])

# Crate: shared texture on planks, modeled outlines and diagonal framing;
# the metal corner plates carry painted rivets.
crate_m={x:Mesh(x) for x in ('crate_planks','wood_beam','iron_plain','rivet_plate')};W=crate_m['crate_planks'];B=crate_m['wood_beam'];I=crate_m['iron_plain'];R=crate_m['rivet_plate']
W.textured_box(-.50,.50,.08,1.08,-.50,.50)
for x in (-.40,.40):
 for z in (-.40,.40):B.box(x,.04,z,.20,.08,.20)
for signside in (-1,1):
 z=signside*.525
 for x in (-.44,.44):B.box(x,.58,z,.105,1.00,.05)
 for y in (.14,1.02):B.beam((-.50,y,z),(.50,y,z),.10,.05)
 B.beam((-.39,.21,z),(.39,.95,z),.10,.045)
 x=signside*.525
 for z in (-.44,.44):B.box(x,.58,z,.05,1.00,.105)
 for y in (.14,1.02):B.beam((x,y,-.50),(x,y,.50),.10,.05,ref=(1,0,0))
 B.beam((x,.21,-.39),(x,.95,.39),.10,.045,ref=(1,0,0))
# Two protective slats on the crate lid.
for x in (-.37,.37):B.beam((x,1.10,-.50),(x,1.10,.50),.045,.10,ref=(1,0,0))
# Actual thin corner armor, with two rivets drawn on each outward face.
for sx in (-1,1):
 for sz in (-1,1):
  for y in (.17,.99):
   x=sx*.46;z=sz*.553;I.box(x,y,z,.13,.18,.025)
   face=z+sz*.014
   points=[(x-.055,y-.08,face),(x+.055,y-.08,face),(x+.055,y+.08,face),(x-.055,y+.08,face)];uv=[[0,1],[1,1],[1,0],[0,0]]
   R.face(points if sz>0 else points[::-1],uv if sz>0 else uv[::-1])
   x=sx*.553;z=sz*.46;I.box(x,y,z,.025,.18,.13)
   face=x+sx*.014
   points=[(face,y-.08,z-.055),(face,y+.08,z-.055),(face,y+.08,z+.055),(face,y-.08,z+.055)];uv=[[0,1],[0,0],[1,0],[1,1]]
   R.face(points if sx>0 else points[::-1],uv if sx>0 else uv[::-1])

# Barrel: sixteen facets and five contour rings, with four thin iron hoops.
barrel_m={x:Mesh(x) for x in ('barrel_staves','barrel_lid','iron_riveted')};W=barrel_m['barrel_staves'];T=barrel_m['barrel_lid'];I=barrel_m['iron_riveted']
N=16; levels=[(0,.36),(.22,.405),(.52,.43),(.82,.405),(1.04,.36)]
def radius(y):
 for (y0,r0),(y1,r1) in zip(levels,levels[1:]):
  if y0<=y<=y1:return r0+(r1-r0)*(y-y0)/(y1-y0)
 return levels[-1][1]
def p(r,y,a):return (r*math.cos(a),y,r*math.sin(a))
for j,((y0,r0),(y1,r1)) in enumerate(zip(levels,levels[1:])):
 for i in range(N):
  a=2*math.pi*i/N;b=2*math.pi*(i+1)/N
  W.face([p(r0,y0,a),p(r1,y1,a),p(r1,y1,b),p(r0,y0,b)],[[i/N,1-y0/1.04],[i/N,1-y1/1.04],[(i+1)/N,1-y1/1.04],[(i+1)/N,1-y0/1.04]])
for y,r,up in ((0,.36,False),(1.04,.36,True)):
 for i in range(N):
  a=2*math.pi*i/N;b=2*math.pi*(i+1)/N;pa=p(r,y,a);pb=p(r,y,b);pc=(0,y,0)
  uv0=[.5,.5];uva=[.5+math.cos(a)*.5,.5+math.sin(a)*.5];uvb=[.5+math.cos(b)*.5,.5+math.sin(b)*.5]
  T.face([pc,pb,pa] if up else [pc,pa,pb],[uv0,uvb,uva] if up else [uv0,uva,uvb])
for cy in (.075,.27,.77,.97):
 y0=cy-.035;y1=cy+.035;r0=radius(y0)+.012;r1=radius(y1)+.012
 for i in range(N):
  a=2*math.pi*i/N;b=2*math.pi*(i+1)/N
  I.face([p(r0,y0,a),p(r1,y1,a),p(r1,y1,b),p(r0,y0,b)],[[2*i/N,1],[2*i/N,0],[2*(i+1)/N,0],[2*(i+1)/N,1]])

files={'iron_plain':'iron_plain.png','aged_gold':'aged_gold.png','platform_3':'platform_3.png','crate_planks':'crate_planks.png','wood_beam':'wood_beam.png','rivet_plate':'rivet_plate.png','barrel_staves':'barrel_staves.png','barrel_lid':'barrel_lid.png','iron_riveted':'iron_riveted.png'}
def write(name,meshes):
 blob=bytearray();views=[];access=[];images=[];textures=[];materials=[];prim=[]
 def add(data,target=None):
  while len(blob)%4:blob.append(0)
  off=len(blob);blob.extend(data);v={'buffer':0,'byteOffset':off,'byteLength':len(data)}
  if target:v['target']=target
  views.append(v);return len(views)-1
 def ac(arr,typ,component,target,bounds=False):
  arr=np.ascontiguousarray(arr);view=add(arr.tobytes(),target);obj={'bufferView':view,'componentType':component,'count':len(arr),'type':typ}
  if bounds:obj.update(min=arr.min(axis=0).astype(float).tolist(),max=arr.max(axis=0).astype(float).tolist())
  access.append(obj);return len(access)-1
 for key,m in meshes.items():
  view=add((P/files[key]).read_bytes());images.append({'name':key,'bufferView':view,'mimeType':'image/png'});textures.append({'name':key,'sampler':0,'source':len(images)-1})
  metal=.7 if key in ('iron_plain','iron_riveted','aged_gold','rivet_plate') else 0
  materials.append({'name':key,'pbrMetallicRoughness':{'baseColorTexture':{'index':len(textures)-1},'baseColorFactor':[1,1,1,1],'metallicFactor':metal,'roughnessFactor':.58}})
  pos=np.asarray(m.p,dtype='<f4');nor=np.asarray(m.n,dtype='<f4');uv=np.asarray(m.uv,dtype='<f4');idx=np.asarray(m.idx,dtype='<u4')
  pa=ac(pos,'VEC3',5126,34962,True);na=ac(nor,'VEC3',5126,34962);ua=ac(uv,'VEC2',5126,34962);ia=ac(idx,'SCALAR',5125,34963)
  prim.append({'attributes':{'POSITION':pa,'NORMAL':na,'TEXCOORD_0':ua},'indices':ia,'material':len(materials)-1,'mode':4})
 while len(blob)%4:blob.append(0)
 gltf={'asset':{'version':'2.0','generator':'Victorian prop generator, NumPy + Pillow'},'scene':0,'scenes':[{'nodes':[0],'name':name}],
 'nodes':[{'name':name+'_ground_pivot_y_up','mesh':0}],'meshes':[{'name':name,'primitives':prim}],
 'materials':materials,'textures':textures,'images':images,'samplers':[{'wrapS':10497,'wrapT':10497,'magFilter':9729,'minFilter':9987}],
 'buffers':[{'byteLength':len(blob)}],'bufferViews':views,'accessors':access}
 js=json.dumps(gltf,separators=(',',':')).encode();js+=b' '*((-len(js))%4)
 raw=struct.pack('<4sII',b'glTF',2,12+8+len(js)+8+len(blob))+struct.pack('<I4s',len(js),b'JSON')+js+struct.pack('<I4s',len(blob),b'BIN\0')+blob;(P/(name+'.glb')).write_bytes(raw)
 points=np.array([p for m in meshes.values() for p in m.p]);return {'file':name+'.glb','bounds_min':points.min(axis=0).tolist(),'bounds_max':points.max(axis=0).tolist(),
 'triangles_by_material':{k:len(m.idx)//3 for k,m in meshes.items()},'triangles':sum(len(m.idx)//3 for m in meshes.values()),'bytes':len(raw)}

if __name__=='__main__':
 assets=[write('platform_sign',sign_m),write('cargo_crate',crate_m),write('cargo_barrel',barrel_m)]
 manifest={'units':'metres','axis':'Y up','pivot':'local origin at ground level','assets':assets,
  'texture_sources':'Procedural wood, painted numeral, gold, and rivets; iron textures are resized or decorated derivatives of the supplied AI cast iron image.'}
 (P/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
