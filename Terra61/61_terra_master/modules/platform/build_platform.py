#!/usr/bin/env python3
"""Build a textured, repeatable 20 x 6 m Victorian station platform and track bay.

Paving uses the project-provided AI-generated texture; additional surfaces
are procedural, drawn with Pillow/NumPy unless a project texture is supplied.
Coordinates: metres, Y up, X width, Z longitudinal. See README for interfaces.
"""
from pathlib import Path
import json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter
import trimesh

OUT=Path(__file__).resolve().parent
TEX=OUT/'textures'
TEX.mkdir(parents=True,exist_ok=True)
SEED=731906


def add_noise(img, seed, amount=7):
    """Add tile-periodic multi-scale patina to a hand-drawn texture."""
    rng=np.random.default_rng(seed)
    h,w=img.height,img.width
    out=np.asarray(img.convert('RGB'),dtype=np.float32)
    fine=rng.normal(0,1,(h,w)).astype(np.float32)
    med=gaussian_filter(rng.normal(0,1,(h,w)).astype(np.float32),sigma=6,mode='wrap')
    med/=max(float(med.std()),1e-5)
    broad=gaussian_filter(rng.normal(0,1,(h//4,w//4)).astype(np.float32),sigma=12,mode='wrap')
    broad/=max(float(broad.std()),1e-5)
    broad=np.asarray(Image.fromarray(broad,mode='F').resize((w,h),Image.Resampling.BILINEAR))
    grain=(.32*fine+.38*med+.30*broad)*amount
    out=np.clip(out+grain[...,None],0,255).astype('uint8')
    return Image.fromarray(out,'RGB')


def slab_texture():
    w,h=1024,1536
    rng=np.random.default_rng(SEED+1)
    im=Image.new('RGB',(w,h),(75,72,67)); d=ImageDraw.Draw(im)
    cw,ch=128,192
    for row in range(h//ch):
        off=(row%2)*cw//2
        # Cover the repeating seam using a stable color for wrapped blocks.
        for i in range(-1,9):
            j=i%8
            local=np.random.default_rng(SEED+100+row*13+j)
            x=i*cw+off; y=row*ch
            k=int(local.integers(-13,14)); c=(151+k,146+k,136+k)
            d.rectangle((x+2,y+2,x+cw-3,y+ch-3),fill=c)
            d.line((x+3,y+3,x+cw-4,y+3), fill=(178+k,173+k,162+k),width=2)
            d.line((x+3,y+4,x+3,y+ch-4), fill=(167+k,162+k,151+k),width=1)
            d.line((x+4,y+ch-4,x+cw-4,y+ch-4),fill=(113+k,110+k,103+k),width=2)
            for _ in range(9):
                px=x+int(local.integers(6,cw-6)); py=y+int(local.integers(6,ch-6))
                rad=int(local.integers(1,5)); kk=int(local.integers(-18,10))
                d.ellipse((px-rad,py-rad,px+rad,py+rad),fill=tuple(max(0,min(255,v+kk)) for v in c))
            if local.random()<.22:
                px=x+int(local.integers(15,cw-25)); py=y+int(local.integers(15,ch-30))
                d.line([(px,py),(px+6,py+11),(px+4,py+19),(px+11,py+30)],fill=(111+k,106+k,97+k),width=1)
    return add_noise(im,SEED+2,11)


def wall_texture():
    w,h=1536,256; im=Image.new('RGB',(w,h),(52,50,47)); d=ImageDraw.Draw(im)
    cw=w//8
    for row in range(3):
        ya=round(row*h/3); yb=round((row+1)*h/3)
        off=(row%2)*cw//2
        for i in range(-1,9):
            j=i%8; local=np.random.default_rng(SEED+1000+row*17+j)
            x=i*cw+off; k=int(local.integers(-13,14)); c=(111+k,106+k,96+k)
            d.rectangle((x+2,ya+2,x+cw-3,yb-3),fill=c)
            d.line((x+4,ya+3,x+cw-4,ya+3),fill=(142+k,136+k,122+k),width=2)
            d.line((x+3,ya+4,x+3,yb-4),fill=(127+k,122+k,110+k),width=2)
            d.line((x+3,yb-3,x+cw-4,yb-3),fill=(77+k,74+k,68+k),width=2)
            for _ in range(8):
                xx=x+int(local.integers(8,cw-8)); yy=ya+int(local.integers(8,max(9,yb-ya-8)))
                dx=int(local.integers(4,18)); dy=int(local.integers(1,4))
                d.line((xx,yy,xx+dx,yy+dy),fill=(100+k,94+k,85+k),width=1)
    return add_noise(im,SEED+3,12)


def coping_texture():
    w,h=1536,128; im=Image.new('RGB',(w,h),(82,78,72)); d=ImageDraw.Draw(im)
    for i in range(10):
        x0=round(w*i/10); x1=round(w*(i+1)/10)
        local=np.random.default_rng(SEED+2000+i); k=int(local.integers(-10,11))
        c=(167+k,162+k,150+k)
        d.rectangle((x0+2,1,x1-3,h-2),fill=c)
        d.line((x0+2,2,x1-3,2), fill=(195+k,189+k,176+k),width=2)
        d.line((x0+3,h-3,x1-3,h-3),fill=(125+k,120+k,110+k),width=2)
        for _ in range(14):
            x=x0+int(local.integers(4,max(5,x1-x0-4))); y=int(local.integers(5,h-5))
            d.point((x,y),fill=(111+k,107+k,98+k))
    return add_noise(im,SEED+4,10)


def wood_texture():
    w,h=1024,256; rng=np.random.default_rng(SEED+5)
    im=Image.new('RGB',(w,h),(82,59,43)); d=ImageDraw.Draw(im)
    for j in range(120):
        y=int(rng.integers(0,h)); x=int(rng.integers(0,w)); length=int(rng.integers(35,500))
        k=int(rng.integers(-20,18)); base=(83+k,60+k,43+k)
        points=[(x,y),(x+length//3,y+int(rng.integers(-2,3))),(x+2*length//3,y+int(rng.integers(-2,3))),(x+length,y+int(rng.integers(-2,3)))]
        for shift in (-w,0,w):
            d.line([(px+shift,py) for px,py in points],fill=base,width=int(rng.integers(1,3)))
    for j in range(8):
        x=int(rng.integers(20,w-20)); y=int(rng.integers(15,h-15)); rx=int(rng.integers(9,23)); ry=int(rng.integers(2,6))
        d.ellipse((x-rx,y-ry,x+rx,y+ry),outline=(56,39,29),width=1)
    return add_noise(im,SEED+6,8)


def ballast_texture():
    w,h=1024,1536; rng=np.random.default_rng(SEED+7)
    im=Image.new('RGB',(w,h),(55,52,48)); d=ImageDraw.Draw(im)
    for _ in range(42000):
        x=int(rng.integers(0,w)); y=int(rng.integers(0,h))
        rx=int(rng.integers(2,11)); ry=int(rng.integers(2,8))
        k=int(rng.integers(-24,36)); c=(92+k,87+k,80+k)
        ring=[]
        for i in range(6):
            a=2*math.pi*i/6; f=float(rng.uniform(.7,1.18))
            ring.append((round(math.cos(a)*rx*f),round(math.sin(a)*ry*f)))
        xshifts=[0]; yshifts=[0]
        if x<rx+2: xshifts.append(w)
        if x>w-rx-2: xshifts.append(-w)
        if y<ry+2: yshifts.append(h)
        if y>h-ry-2: yshifts.append(-h)
        for sx in xshifts:
            for sy in yshifts:
                pts=[(x+dx+sx,y+dy+sy) for dx,dy in ring]
                d.polygon(pts,fill=c)
                d.line((pts[2],pts[3]),fill=tuple(max(0,v-22) for v in c),width=1)
                d.line((pts[4],pts[5]),fill=tuple(min(255,v+20) for v in c),width=1)
    return add_noise(im,SEED+8,5)


def make_textures():
    for name,fn in [('paving',slab_texture),('ashlar',wall_texture),('coping',coping_texture),('wood',wood_texture),('ballast',ballast_texture)]:
        p=TEX/(name+'.png')
        ai=OUT.parent.parent/'materials'/('ai_worn_platform_paving.png' if name=='paving' else 'ai_railway_ballast.png')
        if name in ('paving','ballast') and ai.exists():
            # Feather only the two longitudinal edges: Z=0 and Z=6 must match
            # when bays repeat. Keep the original generated image otherwise.
            image=Image.open(ai).convert('RGB')
            pixels=np.asarray(image,dtype=np.float32).copy()
            for k in range(8):
                weight=.5*(1-k/8)
                top=pixels[k].copy(); bottom=pixels[-1-k].copy()
                pixels[k]=(1-weight)*top+weight*bottom
                pixels[-1-k]=(1-weight)*bottom+weight*top
            Image.fromarray(np.clip(pixels,0,255).astype('uint8')).save(p,optimize=True)
        elif name in ('paving','ballast') and p.exists():
            # Keep the packaged, already-baked images when the bay is moved
            # out of the larger project directory.
            pass
        else:
            fn().save(p,optimize=True)
        print('texture',p,flush=True)


def triangulate_ccw(poly):
    """Ear-clip a simple 2D counter-clockwise outline without optional libs."""
    def cross(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def inside(p,a,b,c):
        return cross(a,b,p)>=-1e-12 and cross(b,c,p)>=-1e-12 and cross(c,a,p)>=-1e-12
    remaining=list(range(len(poly))); faces=[]
    while len(remaining)>3:
        for i,b in enumerate(remaining):
            a=remaining[(i-1)%len(remaining)]; c=remaining[(i+1)%len(remaining)]
            if cross(poly[a],poly[b],poly[c])<=1e-12: continue
            if any(inside(poly[v],poly[a],poly[b],poly[c]) for v in remaining if v not in (a,b,c)):
                continue
            faces.append((a,b,c)); remaining.pop(i); break
        else: raise ValueError('Could not triangulate rail profile')
    faces.append(tuple(remaining))
    return faces


class Builder:
    def __init__(self): self.v=[]; self.f=[]; self.uv=[]
    def quad(self,pts,uv):
        n=len(self.v); self.v.extend(pts); self.uv.extend(uv); self.f.extend([(n,n+1,n+2),(n,n+2,n+3)])
    def tri(self,pts,uv=((0,0),(0,0),(0,0))):
        n=len(self.v); self.v.extend(pts); self.uv.extend(uv); self.f.append((n,n+1,n+2))
    def mesh(self, material):
        m=trimesh.Trimesh(vertices=np.array(self.v,dtype=np.float32),faces=np.array(self.f,dtype=np.int64),process=False)
        m.visual=trimesh.visual.texture.TextureVisuals(uv=np.array(self.uv,dtype=np.float32),material=material)
        return m


def quad(builder,pts,uvfn): builder.quad(pts,[uvfn(*p) for p in pts])


def box(b, x0,x1,y0,y1,z0,z1, uvtop=None, uvside=None, uvend=None):
    # Wound outwards in Y-up coordinates. No face merging: each face has UVs.
    uvtop=uvtop or (lambda x,y,z:(0,0)); uvside=uvside or uvtop; uvend=uvend or uvside
    quad(b,[(x0,y1,z0),(x0,y1,z1),(x1,y1,z1),(x1,y1,z0)],uvtop)
    quad(b,[(x1,y0,z0),(x1,y0,z1),(x0,y0,z1),(x0,y0,z0)],uvtop)
    quad(b,[(x0,y0,z0),(x0,y0,z1),(x0,y1,z1),(x0,y1,z0)],uvside)
    quad(b,[(x1,y0,z1),(x1,y0,z0),(x1,y1,z0),(x1,y1,z1)],uvside)
    quad(b,[(x0,y0,z0),(x0,y1,z0),(x1,y1,z0),(x1,y0,z0)],uvend)
    quad(b,[(x1,y0,z1),(x1,y1,z1),(x0,y1,z1),(x0,y0,z1)],uvend)


def build():
    mat={
      'paving':trimesh.visual.material.PBRMaterial(name='Worn limestone paving',baseColorTexture=Image.open(TEX/'paving.png'),metallicFactor=0.0,roughnessFactor=.93),
      'wall':trimesh.visual.material.PBRMaterial(name='Weathered ashlar masonry',baseColorTexture=Image.open(TEX/'ashlar.png'),metallicFactor=0.0,roughnessFactor=.97),
      'coping':trimesh.visual.material.PBRMaterial(name='Limestone coping blocks',baseColorTexture=Image.open(TEX/'coping.png'),metallicFactor=0.0,roughnessFactor=.87),
      'ballast':trimesh.visual.material.PBRMaterial(name='Dark broken stone ballast',baseColorTexture=Image.open(TEX/'ballast.png'),metallicFactor=0.0,roughnessFactor=1.0),
      'wood':trimesh.visual.material.PBRMaterial(name='Weathered hardwood sleepers',baseColorTexture=Image.open(TEX/'wood.png'),metallicFactor=0.0,roughnessFactor=.94),
      'rail':trimesh.visual.material.PBRMaterial(name='Weathered steel rails',baseColorFactor=[.26,.24,.22,1],metallicFactor=.8,roughnessFactor=.38),
      'head':trimesh.visual.material.PBRMaterial(name='Polished rail running surface',baseColorFactor=[.69,.71,.70,1],metallicFactor=.88,roughnessFactor=.25),
      'fasteners':trimesh.visual.material.PBRMaterial(name='Oxidised iron baseplates and clips',baseColorFactor=[.20,.17,.14,1],metallicFactor=.68,roughnessFactor=.67),
      'stone1':trimesh.visual.material.PBRMaterial(name='Ballast geometry warm gray',baseColorFactor=[.38,.35,.31,1],metallicFactor=0,roughnessFactor=1),
      'stone2':trimesh.visual.material.PBRMaterial(name='Ballast geometry charcoal',baseColorFactor=[.25,.24,.22,1],metallicFactor=0,roughnessFactor=1),
      'stone3':trimesh.visual.material.PBRMaterial(name='Ballast geometry pale gray',baseColorFactor=[.48,.46,.42,1],metallicFactor=0,roughnessFactor=1),
    }
    B={k:Builder() for k in mat}
    platforms=[(-10.,-6.),(-2.,2.),(6.,10.)]
    # Three solid masonry plinths. The cap is kept inset between bevels,
    # while adjacent z modules terminate on exact planes at z=0 and z=6.
    for a,b in platforms:
        wall_side=lambda x,y,z:(z/6,y/.72)
        wall_end=lambda x,y,z:((x-a)/6,y/.72)
        box(B['wall'],a,b,0,.72,0,6,uvside=wall_side,uvend=wall_end)
        # Top infill, with distinct edging blocks along both sides.
        paving=lambda x,y,z:((x-a)/4,z/6)
        quad(B['paving'],[(a+.3,.9,0),(a+.3,.9,6),(b-.3,.9,6),(b-.3,.9,0)],paving)
        for edge,sgn in [(a,1),(b,-1)]:
            outer=edge; inner=edge+sgn*.3; shoulder=edge+sgn*.03
            x0,x1=sorted((shoulder,inner));
            edge_uv=lambda x,y,z,e=edge:(z/6,abs(x-e)/.30)
            quad(B['coping'],[(x0,.9,0),(x0,.9,6),(x1,.9,6),(x1,.9,0)],edge_uv)
            # Three-centimetre chamfer along the outer top corner.
            if sgn==1: pts=[(outer,.87,0),(outer,.87,6),(shoulder,.9,6),(shoulder,.9,0)]
            else: pts=[(shoulder,.9,0),(shoulder,.9,6),(outer,.87,6),(outer,.87,0)]
            quad(B['coping'],pts,edge_uv)
            # Long vertical riser beneath the cap, with periodic joint marks.
            if sgn==1: pts=[(outer,.72,0),(outer,.72,6),(outer,.87,6),(outer,.87,0)]
            else: pts=[(outer,.72,6),(outer,.72,0),(outer,.87,0),(outer,.87,6)]
            quad(B['coping'],pts,lambda x,y,z:(z/6,(y-.72)/.15))
        # Fill the two visible end faces; they coincide cleanly when repeated.
        for z in (0,6):
            pts=([(a,.72,z),(a,.9,z),(b,.9,z),(b,.72,z)] if z==0 else [(b,.72,z),(b,.9,z),(a,.9,z),(a,.72,z)])
            quad(B['coping'],pts,lambda x,y,z:((x-a)/4,(y-.72)/.18))
    # Two four-metre trackbeds, flat textured substrate with scattered facets.
    for center in (-4.,4.):
        a,b=center-2,center+2
        ballastuv=lambda x,y,z,a=a:((x-a)/4,z/6)
        box(B['ballast'],a,b,0,.045,0,6,uvtop=ballastuv,uvside=ballastuv,uvend=ballastuv)
        # Each physical hardwood sleeper runs across the tracks.
        for n in range(10):
            z=.3+n*.6; z0=z-.12; z1=z+.12; xa=center-1.3; xb=center+1.3
            woodtop=lambda x,y,z,xa=xa,z0=z0,n=n:((x-xa)/2.6+n*.061,(z-z0)/.24)
            woodside=lambda x,y,z,xa=xa,n=n:((x-xa)/2.6+n*.061,y/.1)
            woodend=lambda x,y,z,z0=z0:((z-z0)/.24,y/.1)
            box(B['wood'],xa,xb,0,.10,z0,z1,woodtop,woodside,woodend)
            for railoff in (-.7515,.7515):
                rail=center+railoff
                box(B['fasteners'],rail-.10,rail+.10,.100,.110,z-.095,z+.095)
                # Two small retaining jaws at each baseplate.
                for s in (-1,1):
                    box(B['fasteners'],rail+s*.078-.018,rail+s*.078+.018,.110,.128,z-.032,z+.032)
                    box(B['head'],rail+s*.090-.012,rail+s*.090+.012,.110,.116,z+.052-.012,z+.052+.012)
        # Steel rail is an extruded prototypical profile, not a thin bar.
        profile=[(-.070,.110),(.070,.110),(.070,.123),(.019,.130),(.012,.198),(.034,.210),(.034,.232),(.026,.240),(-.026,.240),(-.034,.232),(-.034,.210),(-.012,.198),(-.019,.130),(-.070,.123)]
        # Side surfaces and closed, triangulated end caps.
        profile_triangles=triangulate_ccw(profile)
        for railoff in (-.7515,.7515):
            rail=center+railoff
            for i,(x0,y0) in enumerate(profile):
                x1,y1=profile[(i+1)%len(profile)]
                quad(B['rail'],[(rail+x1,y1,0),(rail+x1,y1,6),(rail+x0,y0,6),(rail+x0,y0,0)],lambda x,y,z:(z/6,y/.24))
            for face in profile_triangles:
                coords=[profile[i] for i in face]
                for z in (0,6):
                    pts=[(rail+x,y,z) for x,y in (coords[::-1] if z==0 else coords)]
                    B['rail'].tri(pts)
            # Bright steel witness stripe, sitting just over the running surface.
            quad(B['head'],[(rail-.026,.24015,0),(rail-.026,.24015,6),(rail+.026,.24015,6),(rail+.026,.24015,0)],lambda x,y,z:(z/6,(x-rail)/.052))
        # Discrete angular ballast stones sit on the textured bed.
        rng=np.random.default_rng(SEED+int(center*100))
        for _ in range(320):
            x=float(rng.uniform(a+.08,b-.08)); z=float(rng.uniform(.11,5.89))
            r=float(rng.uniform(.025,.062)); rz=r*float(rng.uniform(.65,1.4)); ht=float(rng.uniform(.012,.035))
            key=['stone1','stone2','stone3'][int(rng.integers(0,3))]
            top=(x+float(rng.uniform(-.2,.2))*r,.045+ht,z+float(rng.uniform(-.2,.2))*rz)
            ring=[]
            for j in range(6):
                ang=2*math.pi*j/6; rf=float(rng.uniform(.7,1.2))
                ring.append((x+math.cos(ang)*r*rf,.045,z+math.sin(ang)*rz*rf))
            for j in range(6): B[key].tri([ring[(j+1)%6],ring[j],top])
    scene=trimesh.Scene()
    labels={'paving':'Platform_Paving','wall':'Platform_Ashlar_Walls','coping':'Platform_Coping','ballast':'Tracks_Ballast_Beds','wood':'Tracks_Hardwood_Sleepers','rail':'Tracks_Steel_Rails','head':'Tracks_Polished_Heads_And_Bolts','fasteners':'Tracks_Baseplates_And_Clips','stone1':'Ballast_Stones_Warm','stone2':'Ballast_Stones_Charcoal','stone3':'Ballast_Stones_Pale'}
    stats={}
    for key,builder in B.items():
        mesh=builder.mesh(mat[key]); scene.add_geometry(mesh,geom_name=labels[key],node_name=labels[key]); stats[labels[key]]=len(mesh.faces)
    out=OUT/'platform_track_bay.glb'; out.write_bytes(scene.export(file_type='glb'))
    print('glb',out,flush=True)
    print('bounds',scene.bounds,'faces',sum(stats.values()),flush=True)
    (OUT/'mesh_stats.json').write_text(json.dumps({'units':'meters','up_axis':'Y','bounds':scene.bounds.tolist(),'triangles':sum(stats.values()),'triangles_by_mesh':stats,'rail_centers_x':[-4.7515,-3.2485,3.2485,4.7515],'rail_gauge_m_measured_between_inner_faces':1.435,'rail_head_top_y':0.24,'platform_top_y':0.9},indent=2)+'\n')

if __name__=='__main__':
    make_textures(); build()
