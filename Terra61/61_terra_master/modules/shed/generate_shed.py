#!/usr/bin/env python3
"""Generate a repeatable Y-up Victorian train-shed bay, in metres.

Uses only numpy and Pillow. glTF 2.0 is assembled directly to make the images,
alpha mode, double-sided glass and PBR factors unambiguous to importing engines.
"""
from pathlib import Path
import json, math, shutil, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(8126)


def noise_texture(filename, base, size=(512, 128), rivets=False):
    w, h = size
    coarse = rng.normal(0, 6.5, (h//4, w//4))
    coarse = np.asarray(Image.fromarray(np.uint8(np.clip(coarse+128,0,255))).resize((w,h),Image.Resampling.BICUBIC), dtype=float)-128
    fine = rng.normal(0, 2.2, (h,w))
    streak = np.tile(rng.normal(0, 1.8, (1,w)),(h,1))
    arr = np.stack([np.clip(v+coarse+fine+streak, 0, 255) for v in base],axis=2).astype('uint8')
    im = Image.fromarray(arr,'RGB'); d=ImageDraw.Draw(im, 'RGB')
    for _ in range(65):
        x=int(rng.integers(w)); y=int(rng.integers(h)); l=int(rng.integers(3,32))
        d.line((x,y,min(w-1,x+l),y), fill=(75,73,64), width=1)
    if rivets:
        for x in (64,192,320,448):
            y=h//2
            d.ellipse((x-5,y-4,x+5,y+5),fill=(20,23,24))
            d.ellipse((x-4,y-4,x+3,y+3),fill=(76,79,75))
            d.ellipse((x-3,y-3,x,y-1),fill=(125,125,111))
    im.save(OUT/filename)


def glass_texture(filename):
    w=h=512
    base = rng.normal(0, 4.2, (h,w))
    sm = np.asarray(Image.fromarray(np.uint8(np.clip(base+128,0,255))).resize((128,128),Image.Resampling.BICUBIC).resize((w,h),Image.Resampling.BICUBIC),dtype=float)-128
    vals = [np.clip(c+sm,0,255).astype('uint8') for c in (143,175,181)]
    alpha = np.clip(66+sm*.8,52,78).astype('uint8')
    im=Image.fromarray(np.stack(vals+[alpha],axis=2),'RGBA')
    im.save(OUT/filename)

noise_texture('iron_plain.png',(58,65,65))
noise_texture('iron_riveted.png',(58,65,65),rivets=True)
noise_texture('aged_brass.png',(132,104,68))
glass_texture('roof_glass.png')
Image.new('RGB',(4,4),(255,177,74)).save(OUT/'lantern_glass.png')
# Preserve and embed the supplied AI-generated surface itself, without baking
# the roof, glazing or openings into this image.
source_cast=OUT.parent.parent/'materials'/'ai_aged_cast_iron.png'
local_cast=OUT/'ai_aged_cast_iron.png'
if source_cast.exists() and source_cast.resolve()!=local_cast.resolve(): shutil.copy2(source_cast,local_cast)
if not local_cast.exists(): raise FileNotFoundError('Missing ai_aged_cast_iron.png')

class Mesh:
    def __init__(self,name):
        self.name=name; self.p=[]; self.n=[]; self.uv=[]; self.idx=[]
    def quad(self,pts,uv):
        pts=np.asarray(pts,float)
        n=np.cross(pts[1]-pts[0],pts[2]-pts[0]); l=np.linalg.norm(n)
        if l < 1e-8: return
        n=n/l; start=len(self.p)
        self.p.extend(pts.tolist()); self.n.extend([n.tolist()]*4); self.uv.extend(uv)
        self.idx.extend((start,start+1,start+2,start,start+2,start+3))
    def triangle(self,pts,uv):
        pts=np.asarray(pts,float)
        n=np.cross(pts[1]-pts[0],pts[2]-pts[0]); l=np.linalg.norm(n)
        if l < 1e-8: return
        n=n/l; start=len(self.p)
        self.p.extend(pts.tolist()); self.n.extend([n.tolist()]*3); self.uv.extend(uv)
        self.idx.extend((start,start+1,start+2))
    def beam(self,p0,p1,w,d,ref=(0,0,1)):
        p0=np.asarray(p0,float);p1=np.asarray(p1,float); axis=p1-p0; length=np.linalg.norm(axis)
        if length<1e-7: return
        axis=axis/length; ref=np.asarray(ref,float)
        if abs(np.dot(axis,ref))>0.96: ref=np.array((0,1,0),float)
        a=np.cross(ref,axis);a/=np.linalg.norm(a); b=np.cross(axis,a)
        a=a*w/2;b=b*d/2
        q=[p0-a-b,p0+a-b,p0+a+b,p0-a+b,p1-a-b,p1+a-b,p1+a+b,p1-a+b]
        faces=((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))
        for j,face in enumerate(faces):
            if j<2: uv=[[0,0],[1,0],[1,1],[0,1]]
            else: uv=[[0,0],[0,1],[length/.80,1],[length/.80,0]]
            self.quad([q[k] for k in face],uv)
    def box(self,cx,cy,cz,sx,sy,sz):
        self.beam((cx,cy-sy/2,cz),(cx,cy+sy/2,cz),sx,sz)
    def disk_y(self,cx,cy,cz,r,height,segments=10):
        y0=cy-height/2;y1=cy+height/2
        for i in range(segments):
            a=2*math.pi*i/segments;b=2*math.pi*(i+1)/segments
            p0=(cx+r*math.cos(a),y0,cz+r*math.sin(a));p1=(cx+r*math.cos(b),y0,cz+r*math.sin(b))
            p2=(p1[0],y1,p1[2]);p3=(p0[0],y1,p0[2]);self.quad((p0,p3,p2,p1),[[0,0],[0,1],[1,1],[1,0]])
        # Solid end caps are triangles, rather than degenerate quad wedges.
        for i in range(segments):
            a=2*math.pi*i/segments;b=2*math.pi*(i+1)/segments
            for y, reverse in ((y0,False),(y1,True)):
                p0=(cx+r*math.cos(a),y,cz+r*math.sin(a));p1=(cx+r*math.cos(b),y,cz+r*math.sin(b));pc=(cx,y,cz)
                self.triangle((pc,p1,p0) if reverse else (pc,p0,p1),[[.5,.5],[0,0],[1,0]])

M={k:Mesh(k) for k in ['iron_plain','iron_riveted','iron_cast_ai','aged_brass','roof_glass','lantern_glass']}
I=M['iron_plain']; R=M['iron_riveted']; C=M['iron_cast_ai']; B=M['aged_brass']; G=M['roof_glass']; L=M['lantern_glass']

def snapshot():
    return {k:(len(m.p),len(m.idx)) for k,m in M.items()}
end_ranges=[]

SPAN=9.72
N=32
XS=np.linspace(-SPAN,SPAN,N+1)
def roof_y(x): return 7.70+4.30*(1.0-(x/SPAN)**2)

def arch(z,top_drop,lower_drop,band_depth,main=True):
    # Two parallel chords and diagonal lattice; all iron is real geometry.
    for i in range(N):
        x0,x1=XS[i],XS[i+1]
        y0,y1=roof_y(x0),roof_y(x1)
        for drop in (top_drop,lower_drop):
            C.beam((x0,y0-drop,z),(x1,y1-drop,z),.105 if main else .075,band_depth)
        # X braces in every second panel, single diagonal in the remainder.
        I.beam((x0,y0-lower_drop+.04,z),(x1,y1-top_drop-.04,z),.045 if main else .032,band_depth*.62)
        if i%2==0:
            I.beam((x0,y0-top_drop-.04,z),(x1,y1-lower_drop+.04,z),.045 if main else .032,band_depth*.62)
    # Small joint plates along lower chord help catch highlights.
    if main:
        for i in range(2,N,4):
            x=XS[i];y=roof_y(x)-lower_drop
            R.box(x,y,z,.19,.16,band_depth+.025)

start=snapshot()
arch(.28,.09,.95,.26,True)
end_ranges.append((start,snapshot()))
arch(3.13,.13,.62,.14,False)

# Roof sheet, a doubly sided, alpha-blended continuous curved glass surface.
for i in range(N):
    x0,x1=XS[i],XS[i+1]; y0,y1=roof_y(x0)+.035,roof_y(x1)+.035
    G.quad(((x0,y0,0),(x0,y0,6),(x1,y1,6),(x1,y1,0)),
           [[i/2,0],[i/2,3],[(i+1)/2,3],[(i+1)/2,0]])
# Longitudinal glazing bars; narrow enough to read as mullions, not planks.
for x in XS:
    yy=roof_y(x)+.052
    I.beam((x,yy,0),(x,yy,6),.038,.038)
# The transverse glazing bars track the curve as short coplanar chords.
for z in (.9,1.8,2.7,3.6,4.5,5.4):
    for i in range(N):
        x0,x1=XS[i],XS[i+1]
        I.beam((x0,roof_y(x0)+.05,z),(x1,roof_y(x1)+.05,z),.036,.036)

# Built-up square, fluted cast-iron columns and their concrete-free footplates.
start=snapshot()
for side in (-1,1):
    x=side*9.70; z=.29
    C.box(x,.10,z,.58,.20,.52)
    C.box(x,.29,z,.49,.18,.44)
    C.box(x,.58,z,.40,.40,.38)
    R.box(x,.86,z,.45,.13,.42)
    C.box(x,3.80,z,.30,5.80,.30)
    # Raised long flutes on visible faces.
    for xx in (-.105,0,.105):
        I.box(x+xx,3.80,z-.16,.030,5.54,.028)
        I.box(x+xx,3.80,z+.16,.030,5.54,.028)
    for zz in (-.105,0,.105):
        I.box(x-.16,3.80,z+zz,.028,5.54,.030)
        I.box(x+.16,3.80,z+zz,.028,5.54,.030)
    # Brass is restrained to thin edge lines and collar separators.
    for xx in (-.17,.17): B.box(x+xx,3.83,z-.176,.017,5.25,.016)
    for h,w,d,sy in ((1.02,.38,.38,.08),(1.18,.35,.35,.09),(6.47,.40,.37,.12),(6.66,.46,.41,.12),(6.90,.53,.45,.12),(7.18,.50,.43,.16),(7.47,.43,.39,.14)):
        R.box(x,h,z,w,sy,d)
    B.box(x,6.73,z,.46,.035,.42)
    # Ornamental diamond relief on the front of the broad base.
    xf=x; zz=z-.232
    I.beam((xf-.14,.48,zz),(xf+.14,.72,zz),.035,.025)
    I.beam((xf-.14,.72,zz),(xf+.14,.48,zz),.035,.025)
    # Curved knee brace hugging the spring of the arch.
    p=[(x,6.72,.28),(x-side*.20,7.10,.28),(x-side*.45,7.42,.28),(x-side*.82,7.75,.28),(x-side*1.18,8.02,.28)]
    for a,b in zip(p,p[1:]): R.beam(a,b,.09,.13)
    I.beam(p[0],p[3],.045,.075)
    # Vertical finial (low-profile, aligned at the eave).
    R.box(x,7.72,z,.32,.12,.33)
    B.disk_y(x,7.82,z,.095,.12,segments=10)
end_ranges.append((start,snapshot()))

# Open-sided iron lattice eaves with spandrel diagonal braces.
for side in (-1,1):
    x=side*9.70
    for y in (7.02,7.65): R.beam((x,y,.36),(x,y,6),.10,.12,ref=(1,0,0))
    # Stop the angled infill just short of the join so its end caps do not
    # protrude into the following module.
    zz=np.linspace(.36,5.97,9)
    for i,(z0,z1) in enumerate(zip(zz,zz[1:])):
        I.beam((x,7.06,z0),(x,7.60,z1),.045,.065,ref=(1,0,0))
        I.beam((x,7.60,z0),(x,7.06,z1),.045,.065,ref=(1,0,0))

# Decorative circular bosses at the haunches of the front arch.
start=snapshot()
for side in (-1,1):
    for xmag in (7.7,8.75):
        x=side*xmag;y=roof_y(x)-.52; z=.125
        rr=.19
        for i in range(12):
            a=math.tau*i/12;b=math.tau*(i+1)/12
            I.beam((x+rr*math.cos(a),y+rr*math.sin(a),z),(x+rr*math.cos(b),y+rr*math.sin(b),z),.029,.025)
        B.beam((x-.09,y,z-.015),(x+.09,y,z-.015),.018,.018)
        B.beam((x,y-.09,z-.015),(x,y+.09,z-.015),.018,.018)
end_ranges.append((start,snapshot()))

# Four suspended lanterns, high above both tracks, attached to roof structure.
def lamp(x,z):
    top=roof_y(x)-.16; upper=top-.55; lower=upper-.43
    I.beam((x,top,z),(x,upper,z),.035,.035)
    R.box(x,upper+.03,z,.38,.07,.34)
    L.box(x,(upper+lower)/2,z,.27,upper-lower,.25)
    for dx in (-.15,.15):
        for dz in (-.14,.14): R.beam((x+dx,lower,z+dz),(x+dx,upper,z+dz),.028,.028)
    R.box(x,lower-.03,z,.38,.06,.34)
    B.disk_y(x,lower-.085,z,.06,.10,segments=8)
for x in (-7.35,7.35):
    for z in (1.55,4.55): lamp(x,z)

# Minimal direct GLB writer with embedded textures and grouped draw calls.
def glb_write(meshes, filename):
    blob=bytearray(); views=[]; accessors=[]; prim=[]; materials=[]; images=[]; textures=[]
    def append(raw,target=None):
        while len(blob)%4: blob.append(0)
        offset=len(blob);blob.extend(raw);view={'buffer':0,'byteOffset':offset,'byteLength':len(raw)}
        if target:view['target']=target
        views.append(view);return len(views)-1
    def accessor(arr,kind,component,target,with_range=False):
        arr=np.ascontiguousarray(arr); view=append(arr.tobytes(),target)
        a={'bufferView':view,'componentType':component,'count':len(arr),'type':kind}
        if with_range: a.update(min=np.min(arr,axis=0).astype(float).tolist(),max=np.max(arr,axis=0).astype(float).tolist())
        accessors.append(a);return len(accessors)-1
    material_parameters={
      'iron_plain':('iron_plain.png',.72,.58),
      'iron_riveted':('iron_riveted.png',.72,.58),
      'iron_cast_ai':('ai_aged_cast_iron.png',.72,.64),
      'aged_brass':('aged_brass.png',.76,.53),
      'roof_glass':('roof_glass.png',0,.24),
      'lantern_glass':('lantern_glass.png',0,.4),
    }
    for name,mesh in meshes.items():
        if not mesh.idx: continue
        texture_filename,metal,rough=material_parameters[name]
        iv=append((OUT/texture_filename).read_bytes());images.append({'name':name,'bufferView':iv,'mimeType':'image/png'})
        textures.append({'name':name,'sampler':0,'source':len(images)-1})
        mat={'name':name,'pbrMetallicRoughness':{'baseColorTexture':{'index':len(textures)-1},'baseColorFactor':[1,1,1,1],'metallicFactor':metal,'roughnessFactor':rough}}
        if name=='roof_glass':mat.update(alphaMode='BLEND',doubleSided=True)
        if name=='lantern_glass':mat.update(emissiveFactor=[0.95,0.38,0.06])
        materials.append(mat)
        pos=np.array(mesh.p,dtype='<f4');nor=np.array(mesh.n,dtype='<f4');uv=np.array(mesh.uv,dtype='<f4');idx=np.array(mesh.idx,dtype='<u4')
        pa=accessor(pos,'VEC3',5126,34962,True);na=accessor(nor,'VEC3',5126,34962);ua=accessor(uv,'VEC2',5126,34962);ia=accessor(idx,'SCALAR',5125,34963)
        prim.append({'attributes':{'POSITION':pa,'NORMAL':na,'TEXCOORD_0':ua},'indices':ia,'material':len(materials)-1,'mode':4})
    while len(blob)%4:blob.append(0)
    name=Path(filename).stem
    gltf={'asset':{'version':'2.0','generator':'Victorian shed generator, numpy + Pillow'},'scene':0,'scenes':[{'nodes':[0],'name':name}],
          'nodes':[{'name':name+'_y_up','mesh':0}],'meshes':[{'name':'shed_geometry','primitives':prim}],
          'materials':materials,'textures':textures,'images':images,'samplers':[{'wrapS':10497,'wrapT':10497,'magFilter':9729,'minFilter':9987}],
          'buffers':[{'byteLength':len(blob)}],'bufferViews':views,'accessors':accessors}
    js=json.dumps(gltf,separators=(',',':')).encode();js+=b' '*((-len(js))%4)
    raw=struct.pack('<4sII',b'glTF',2,12+8+len(js)+8+len(blob))+struct.pack('<I4s',len(js),b'JSON')+js+struct.pack('<I4s',len(blob),b'BIN\0')+blob
    (OUT/filename).write_bytes(raw)
    allpoints=np.array([p for m in meshes.values() for p in m.p]);
    stats={'bounds_min':allpoints.min(axis=0).tolist(),'bounds_max':allpoints.max(axis=0).tolist(),
           'vertices':{k:len(m.p) for k,m in meshes.items() if m.idx},
           'triangles':{k:len(m.idx)//3 for k,m in meshes.items() if m.idx},
           'total_triangles':sum(len(m.idx)//3 for m in meshes.values()),'bytes':len(raw)}
    return stats

def build_end_mesh():
    end={k:Mesh(k) for k in M}
    for start,finish in end_ranges:
        for k,src in M.items():
            v0,i0=start[k];v1,i1=finish[k]; dst=end[k];base=len(dst.p)
            dst.p.extend(src.p[v0:v1]);dst.n.extend(src.n[v0:v1]);dst.uv.extend(src.uv[v0:v1])
            selection=src.idx[i0:i1]
            assert all(v0<=i<v1 for i in selection)
            dst.idx.extend([base+i-v0 for i in selection])
    return end

def main():
    bay=glb_write(M,'train_shed_bay.glb')
    end=glb_write(build_end_mesh(),'train_shed_end_frame.glb')
    manifest={'axis':'Y up','units':'meters','repeat_offset':[0,0,6],
              'bay':bay,'end_frame':end,'glass':'BLEND, double sided',
              'texture_sources':'AI-generated aged cast iron supplied by assembly lead, embedded and UV-applied to arch chords and column cores; other textures procedurally generated with deterministic seed 8126',
              'notes':'Repeat the bay every 6m. To support the final roof edge, add the separate end frame at z=(6*number_of_bays)-0.28m.'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
