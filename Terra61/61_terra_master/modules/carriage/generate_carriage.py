#!/usr/bin/env python3
"""Generate an original Victorian passenger carriage GLB, Y up, meters."""
from pathlib import Path
import json,math,struct,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;P.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(40617)

def textured(name,base,kind='metal',size=(512,512)):
    w,h=size
    basea=np.zeros((h,w,3),dtype=float);basea[:]=base
    coarse=rng.normal(0,3,(h//4,w//4));coarse=np.asarray(Image.fromarray(np.uint8(np.clip(coarse+128,0,255))).resize((w,h),Image.Resampling.BICUBIC),dtype=float)-128
    fine=rng.normal(0,1.9,(h,w))
    if kind=='wood':
        grain=np.asarray(Image.fromarray(np.uint8(np.clip(rng.normal(128,13,(h,1)),0,255))).resize((w,h)),dtype=float)-128
        grain=grain*.31
        for channel in range(3):basea[:,:,channel]+=coarse+fine+grain
    else:
        for channel in range(3):basea[:,:,channel]+=coarse+fine
    img=Image.fromarray(np.clip(basea,0,255).astype('uint8'),'RGB');d=ImageDraw.Draw(img)
    for i in range(45):
        x=int(rng.integers(w));y=int(rng.integers(h));length=int(rng.integers(3,35))
        c=(min(255,base[0]+13),min(255,base[1]+9),min(255,base[2]+7))
        d.line((x,y,min(w-1,x+length),y),fill=c,width=1)
    img.save(P/name)

textured('burgundy_wood.png',(119,37,33),'wood')
textured('dark_wood.png',(71,35,28),'wood')
textured('upholstery.png',(104,37,36),'wood')
textured('aged_gold.png',(169,124,55),'metal',size=(256,256))
textured('roof_metal.png',(55,61,65),'metal')
textured('wheel_steel.png',(62,65,62),'metal',size=(256,256))
Image.new('RGBA',(128,128),(147,181,187,54)).save(P/'window_glass.png')
label=Image.new('RGBA',(1024,128),(0,0,0,0));draw=ImageDraw.Draw(label)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',72)
s='RIVERDALE RAILWAY';box=draw.textbbox((0,0),s,font=font);x=(1024-(box[2]-box[0]))/2; y=(128-(box[3]-box[1]))/2-box[1]
draw.text((x,y),s,font=font,fill=(214,169,85,255),stroke_width=0);label.save(P/'lettering.png')
source=P.parent.parent/'materials'/'ai_aged_cast_iron.png';local=P/'ai_aged_cast_iron.png'
if source.exists() and source.resolve()!=local.resolve():shutil.copy2(source,local)
if not local.exists():raise FileNotFoundError('Missing ai_aged_cast_iron.png')

class Mesh:
 def __init__(self,name):self.name=name;self.p=[];self.n=[];self.uv=[];self.idx=[]
 def face(self,pts,uv=None):
  pts=np.asarray(pts,dtype=float);normal=np.cross(pts[1]-pts[0],pts[2]-pts[0]);l=np.linalg.norm(normal)
  if l<1e-9:return
  normal=normal/l;start=len(self.p);self.p.extend(pts.tolist());self.n.extend([normal.tolist()]*len(pts))
  if uv is None:uv=[[0,0],[1,0],[1,1],[0,1]] if len(pts)==4 else [[0,0],[1,0],[.5,1]]
  self.uv.extend(uv);self.idx.extend([start,start+1,start+2]);
  if len(pts)==4:self.idx.extend([start,start+2,start+3])
 def beam(self,p0,p1,w,d,ref=(0,0,1)):
  p0=np.asarray(p0,float);p1=np.asarray(p1,float);axis=p1-p0;length=np.linalg.norm(axis)
  if length<1e-8:return
  axis/=length;ref=np.asarray(ref,float)
  if abs(np.dot(axis,ref))>.96:ref=np.array((0,1,0),float)
  a=np.cross(ref,axis);a/=np.linalg.norm(a);b=np.cross(axis,a);a*=w/2;b*=d/2
  q=[p0-a-b,p0+a-b,p0+a+b,p0-a+b,p1-a-b,p1+a-b,p1+a+b,p1-a+b]
  for j,face in enumerate(((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))):
   uv=[[0,0],[1,0],[1,1],[0,1]] if j<2 else [[0,0],[0,1],[length/.8,1],[length/.8,0]]
   self.face([q[k] for k in face],uv)
 def box(self,x,y,z,sx,sy,sz):self.beam((x,y-sy/2,z),(x,y+sy/2,z),sx,sz)
 def ring_x(self,x,y,z,outer,inner,thickness,segments=16):
  x0=x-thickness/2;x1=x+thickness/2
  def pt(xx,r,a):return (xx,y+r*math.cos(a),z+r*math.sin(a))
  for i in range(segments):
   a=2*math.pi*i/segments;b=2*math.pi*(i+1)/segments
   self.face([pt(x1,inner,a),pt(x1,outer,a),pt(x1,outer,b),pt(x1,inner,b)])
   self.face([pt(x0,inner,b),pt(x0,outer,b),pt(x0,outer,a),pt(x0,inner,a)])
   self.face([pt(x0,outer,a),pt(x0,outer,b),pt(x1,outer,b),pt(x1,outer,a)])
   self.face([pt(x0,inner,b),pt(x0,inner,a),pt(x1,inner,a),pt(x1,inner,b)])
 def cylinder(self,p0,p1,r,segments=12):
  p0=np.asarray(p0,float);p1=np.asarray(p1,float);axis=(p1-p0);axis/=np.linalg.norm(axis)
  ref=np.array((0,0,1),float)
  if abs(np.dot(axis,ref))>.96:ref=np.array((0,1,0),float)
  a=np.cross(ref,axis);a/=np.linalg.norm(a);b=np.cross(axis,a)
  for i in range(segments):
   t=2*math.pi*i/segments;u=2*math.pi*(i+1)/segments
   r0=r*(a*math.cos(t)+b*math.sin(t));r1=r*(a*math.cos(u)+b*math.sin(u))
   self.face([p0+r0,p0+r1,p1+r1,p1+r0]);self.face([p0,p0+r1,p0+r0]);self.face([p1,p1+r0,p1+r1])

materials=['burgundy_wood','dark_wood','upholstery','aged_gold','roof_metal','wheel_steel','iron_cast_ai','window_glass','lettering']
M={k:Mesh(k) for k in materials}
W=M['burgundy_wood'];D=M['dark_wood'];U=M['upholstery'];G=M['aged_gold'];R=M['roof_metal'];S=M['wheel_steel'];I=M['iron_cast_ai'];V=M['window_glass'];T=M['lettering']

# Dimensions: 15.2m over couplers, 2.8m over the trim, wheels on y=0.
body_z0=.55;body_z1=14.65;body_len=body_z1-body_z0
# Floor and lower/upper shell, deliberately discontinuous around windows.
D.box(0,1.22,7.6,2.57,.18,body_len)
I.box(0,1.10,7.6,2.56,.13,body_len+.10)
for side in (-1,1):
 x=side*1.30
 W.box(x,1.65,7.6,.10,.80,body_len)
 W.box(x,3.33,7.6,.10,.38,body_len)
 # Repeated uprights between windows.
 posts=np.linspace(.65,14.55,12)
 centers=(posts[:-1]+posts[1:])/2
 for z in posts:W.box(x,2.56,z,.105,1.05,.23)
 # Outer hardwood and gold horizontal sill bands.
 for y in (1.23,1.99,3.10,3.50):D.box(side*1.365,y,7.6,.05,.06,body_len)
 for y in (1.30,1.93,3.17,3.44):G.box(side*1.394,y,7.6,.014,.014,body_len-.18)
 # True translucent window planes and built-up trim.
 for z in centers:
  zl,zr=z-.49,z+.49;y0,y1=2.02,3.12;xx=side*1.362
  # Reverse the surface for the opposite side; material is double sided.
  V.face([(xx,y0,zl),(xx,y1,zl),(xx,y1,zr),(xx,y0,zr)],[[0,1],[0,0],[1,0],[1,1]])
  for yy in (2.02,2.91,3.12):D.box(side*1.38,yy,z,.04,.055,.98)
  for zz in (zl,zr):D.box(side*1.38,2.57,zz,.04,1.12,.055)
  for yy in (2.07,3.07):G.box(side*1.404,yy,z,.012,.014,.90)
  for zz in (zl+.045,zr-.045):G.box(side*1.404,2.57,zz,.012,1.0,.014)
  # Gold paint on the lower inset panel, small enough to read as a single frame.
  for yy in (1.36,1.83):G.box(side*1.388,yy,z,.012,.013,1.02)
  for zz in (z-.51,z+.51):G.box(side*1.388,1.595,zz,.012,.48,.013)
 # Decorative board carrying a thin opaque side strip, not a solid window wall.
 # Mirroring UV for the opposite flank keeps lettering legible from each side.
 x=side*1.403;y0,y1=3.245,3.425;z0,z1=4.85,10.35
 if side==1: uv=[[1,1],[1,0],[0,0],[0,1]]
 else: uv=[[0,1],[0,0],[1,0],[1,1]]
 T.face([(x,y0,z0),(x,y1,z0),(x,y1,z1),(x,y0,z1)],uv)

# End walls with an actual inset glazed centre door, not a painted fake window.
for z in (body_z0,body_z1):
 W.box(0,1.66,z,2.62,.82,.10);W.box(0,3.34,z,2.62,.38,.10)
 for x in (-1.22,-.65,.65,1.22):W.box(x,2.56,z,.13,1.08,.10)
 for xa,xb in ((-1.15,-.70),(-.58,.58),(.70,1.15)):
  V.face([(xa,2.02,z),(xb,2.02,z),(xb,3.12,z),(xa,3.12,z)],[[0,1],[1,1],[1,0],[0,0]])
 # Broad centre door bottom and clearly framed centre door glazing.
 W.box(0,1.74,z-(.065 if z<7 else -.065),1.13,.58,.055)
 for x in (-.61,.61):D.box(x,2.58,z,.075,1.84,.15)
 for y in (1.25,2.02,3.11,3.51):D.box(0,y,z,1.31,.065,.15)
 facez=z+(-.085 if z<7 else .085)
 for x in (-.54,.54):G.box(x,2.58,facez,.015,1.72,.015)
 for y in (1.30,1.95,3.04):G.box(0,y,facez,1.08,.015,.015)
 for x in (-1.02,1.02):
  # Hand rails and little exterior step below each end.
  G.beam((x,1.40,facez),(x,2.14,facez),.026,.026)
  I.box(x,.96,z,.43,.07,.47)

# Simplified interior: wooden aisle floor and two rows of seat cushions / backs.
D.box(0,1.33,7.6,2.40,.07,13.7)
for z in np.linspace(1.55,13.65,9):
 for side in (-1,1):
  x=side*.73
  U.box(x,1.67,z,.83,.22,.68)
  U.box(x,2.05,z+.26,.83,.82,.15)
  D.box(x,1.47,z,.76,.26,.56)

# Rounded roof, dark on both outside and inside, with shallow standing seams.
segments=20;xs=np.linspace(-1.38,1.38,segments+1)
def top(x):return 3.55+.45*(1-(x/1.38)**2)
for i in range(segments):
 a,b=xs[i],xs[i+1];ya,yb=top(a),top(b)
 R.face([(a,ya,.50),(a,ya,14.70),(b,yb,14.70),(b,yb,.50)],[[i/4,0],[i/4,9],[(i+1)/4,9],[(i+1)/4,0]])
 R.face([(a,ya-.065,14.70),(a,ya-.065,.50),(b,yb-.065,.50),(b,yb-.065,14.70)],[[i/4,0],[i/4,9],[(i+1)/4,9],[(i+1)/4,0]])
 for z in (.50,14.70):R.face([(a,ya-.065,z),(a,ya,z),(b,yb,z),(b,yb-.065,z)])
for x in (-1.38,1.38):R.box(x,3.53,7.60,.06,.12,14.2)
for z in np.linspace(1.0,14.2,10):
 for i in range(segments):
  a,b=xs[i],xs[i+1];R.beam((a,top(a)+.017,z),(b,top(b)+.017,z),.025,.035)
for z in np.linspace(1.5,13.7,7):
 R.cylinder((0,4.00,z),(0,4.08,z),.085,12)
 R.cylinder((0,4.08,z),(0,4.12,z),.13,12)

# Two two-axle bogies. Spoked wheel rims are visible from the outside.
axles=[2.60,4.20,11.00,12.60]
for z in axles:
 I.cylinder((-.94,.46,z),(.94,.46,z),.075,10)
 for side in (-1,1):
  x=side*.78;I.ring_x(x,.46,z,.46,.325,.15,16)
  # A thin steel wheel tread catches a highlight at the perimeter.
  S.ring_x(x,.46,z,.46,.435,.16,16)
  for j in range(7):
   a=2*math.pi*j/7
   I.beam((x,.46,z),(x,.46+.345*math.cos(a),z+.345*math.sin(a)),.065,.075,ref=(1,0,0))
  I.cylinder((x-side*.11,.46,z),(x+side*.11,.46,z),.12,12)
  S.cylinder((x+side*.11,.46,z),(x+side*.14,.46,z),.07,10)
# Side frames, diagonal equaliser arms, end leaf springs and central chassis box.
for bogie in (3.40,11.80):
 for side in (-1,1):
  x=side*.96
  I.beam((x,.88,bogie-1.17),(x,.88,bogie+1.17),.17,.15,ref=(1,0,0))
  I.beam((x,.87,bogie-1.06),(x,.58,bogie-.80),.11,.12,ref=(1,0,0))
  I.beam((x,.87,bogie+1.06),(x,.58,bogie+.80),.11,.12,ref=(1,0,0))
  for dz in (-.80,.80):
   I.box(x,.69,bogie+dz,.20,.28,.29)
   for k in range(3):S.box(x+side*.11,.67+k*.075,bogie+dz,.025,.022,.27)
  I.box(x,.81,bogie,.20,.24,.55)
 I.beam((-.96,.91,bogie),(.96,.91,bogie),.16,.16)
I.box(0,.82,7.6,1.55,.46,2.3)
for side in (-1,1):
 I.beam((side*.98,.92,4.58),(side*.98,.61,6.50),.09,.09)
 I.beam((side*.98,.61,8.70),(side*.98,.92,10.62),.09,.09)

# Buffer beams, two disc buffers and a central coupler on each end.
for end in (0,1):
 z=body_z0 if end==0 else body_z1;sign=-1 if end==0 else 1
 I.box(0,1.09,z,2.45,.22,.18)
 for x in (-.91,.91):
  I.cylinder((x,1.07,z),(x,1.07,z+sign*.32),.09,12)
  S.cylinder((x,1.07,z+sign*.30),(x,1.07,z+sign*.38),.185,16)
 # Main hook / link projects to the declared z endpoints.
 I.beam((0,.95,z),(0,.95,z+sign*.47),.13,.15)
 I.cylinder((-.08,.95,z+sign*.42),(.08,.95,z+sign*.42),.13,10)
 # Flexible hoses rendered as simple descending iron links.
 for x in (-.35,.35):
  I.beam((x,.98,z+sign*.12),(x,.56,z+sign*.31),.04,.04)
  I.cylinder((x-.04,.53,z+sign*.31),(x+.04,.53,z+sign*.31),.045,8)

# glTF writer groups by material, embeds each PNG in one binary GLB.
def write():
 blob=bytearray();views=[];acc=[];images=[];textures=[];materials_json=[];primitives=[]
 def add(raw,target=None):
  while len(blob)%4:blob.append(0)
  offset=len(blob);blob.extend(raw);v={'buffer':0,'byteOffset':offset,'byteLength':len(raw)}
  if target:v['target']=target
  views.append(v);return len(views)-1
 def accessor(a,kind,comp,target,bounds=False):
  a=np.ascontiguousarray(a);v=add(a.tobytes(),target);obj={'bufferView':v,'componentType':comp,'count':len(a),'type':kind}
  if bounds:obj.update(min=a.min(axis=0).astype(float).tolist(),max=a.max(axis=0).astype(float).tolist())
  acc.append(obj);return len(acc)-1
 specs={
  'burgundy_wood':('burgundy_wood.png',0,.48),'dark_wood':('dark_wood.png',0,.57),
  'upholstery':('upholstery.png',0,.9),'aged_gold':('aged_gold.png',.77,.4),
  'roof_metal':('roof_metal.png',.65,.56),'wheel_steel':('wheel_steel.png',.8,.47),
  'iron_cast_ai':('ai_aged_cast_iron.png',.7,.62),'window_glass':('window_glass.png',0,.15),
  'lettering':('lettering.png',0,.58)}
 for name,m in M.items():
  filename,metal,rough=specs[name];view=add((P/filename).read_bytes());images.append({'name':name,'bufferView':view,'mimeType':'image/png'})
  textures.append({'name':name,'sampler':0,'source':len(images)-1});mat={'name':name,'pbrMetallicRoughness':{'baseColorTexture':{'index':len(textures)-1},'baseColorFactor':[1,1,1,1],'metallicFactor':metal,'roughnessFactor':rough}}
  if name in ('window_glass','lettering'):mat.update(alphaMode='BLEND',doubleSided=True)
  materials_json.append(mat)
  pos=np.asarray(m.p,dtype='<f4');nor=np.asarray(m.n,dtype='<f4');uv=np.asarray(m.uv,dtype='<f4');ind=np.asarray(m.idx,dtype='<u4')
  pa=accessor(pos,'VEC3',5126,34962,True);na=accessor(nor,'VEC3',5126,34962);ua=accessor(uv,'VEC2',5126,34962);ia=accessor(ind,'SCALAR',5125,34963)
  primitives.append({'attributes':{'POSITION':pa,'NORMAL':na,'TEXCOORD_0':ua},'indices':ia,'material':len(materials_json)-1,'mode':4})
 while len(blob)%4:blob.append(0)
 gltf={'asset':{'version':'2.0','generator':'Victorian passenger carriage generator, NumPy + Pillow'},'scene':0,'scenes':[{'name':'Victorian passenger carriage','nodes':[0]}],
       'nodes':[{'name':'carriage_y_up','mesh':0}],'meshes':[{'name':'carriage_geometry','primitives':primitives}],
       'materials':materials_json,'images':images,'textures':textures,'samplers':[{'wrapS':10497,'wrapT':10497,'magFilter':9729,'minFilter':9987}],
       'buffers':[{'byteLength':len(blob)}],'bufferViews':views,'accessors':acc}
 js=json.dumps(gltf,separators=(',',':')).encode();js+=b' '*((-len(js))%4)
 out=struct.pack('<4sII',b'glTF',2,12+8+len(js)+8+len(blob))+struct.pack('<I4s',len(js),b'JSON')+js+struct.pack('<I4s',len(blob),b'BIN\0')+blob
 (P/'victorian_carriage.glb').write_bytes(out)
 verts=np.array([p for m in M.values() for p in m.p]);manifest={'axis':'Y up','units':'meters','placement_above_track_ground':.24,'bounds_min':verts.min(axis=0).tolist(),'bounds_max':verts.max(axis=0).tolist(),
 'vertices':{k:len(m.p) for k,m in M.items()},'triangles':{k:len(m.idx)//3 for k,m in M.items()},'total_triangles':sum(len(m.idx)//3 for m in M.values()),'bytes':len(out),
 'interior':'Simple aisle floor and two rows of seat cushions/backs visible through translucent windows; no detailed full interior.',
 'materials':'Procedural wood, metal, glass, lettering and upholstery; supplied AI-generated cast-iron texture on bogies/undercarriage.'}
 (P/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
if __name__=='__main__':write()
