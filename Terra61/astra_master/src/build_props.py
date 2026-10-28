#!/usr/bin/env python3
"""Low-poly textured station furnishings. Authored Z-up, exported glTF Y-up."""
from __future__ import annotations

import json
import math
from pathlib import Path
import numpy as np
from PIL import Image
from pygltflib import Material, PbrMetallicRoughness, TextureInfo, NormalMaterialTexture
from build_architecture import Geometry, GLBWriter, write_png_atomic

STATION=Path(__file__).resolve().parents[1]
OUT=STATION/'modules'/'props'


def maps():
    OUT.mkdir(parents=True,exist_ok=True)
    result={}
    for material in ('iron','wood','brass','ornament'):
        result[material]={key:STATION/'textures'/f'{material}_{suffix}.png'
                          for key,suffix in (('base','basecolor'),('normal','normal'),('orm','orm'))}
        if not all(path.exists() for path in result[material].values()):
            raise FileNotFoundError(f'missing source maps for {material}')
    # Isolated flame and amber glazing, cropped from the generated lamp reference.
    # Each image is a complete UV chart, rather than an uncropped source atlas.
    crop=(390,180,455,310)
    src=STATION/'references'/'08_gaslamp_reference.png'
    out=OUT/'gaslight_basecolor.png'
    write_png_atomic(Image.open(src).convert('RGB').crop(crop).resize((260,520),Image.Resampling.LANCZOS),out)
    result['lantern']={'base':out}
    result['clock']={}
    for key,suffix in (('base','basecolor'),('normal','normal'),('orm','orm')):
        path=STATION/'textures'/f'clock_{suffix}.png'
        target=OUT/f'clock_{suffix}.png'
        write_png_atomic(Image.open(path).convert('RGB').crop((16,25,613,628)),target)
        result['clock'][key]=target
    sign=OUT/'platform_3_basecolor.png'
    source=STATION/'references'/'12_station_clock_sign_reference.png'
    write_png_atomic(Image.open(source).convert('RGB').crop((806,464,923,578)).resize((468,456),Image.Resampling.LANCZOS),sign)
    result['sign3']={'base':sign}
    return result


class Writer(GLBWriter):
    def add_material(self,name,record):
        base=self.texture(record['base'])
        metal,rough=(1.,1.) if 'orm' in record else ((0.,.4) if name=='lantern' else (.2,.6))
        pbr=PbrMetallicRoughness(baseColorFactor=[1,1,1,1],baseColorTexture=TextureInfo(index=base),
                                 metallicFactor=metal,roughnessFactor=rough)
        normal=None
        if 'normal' in record:
            normal=NormalMaterialTexture(index=self.texture(record['normal']),scale=.55)
        if 'orm' in record:
            pbr.metallicRoughnessTexture=TextureInfo(index=self.texture(record['orm']))
        kw={}
        if name=='lantern':
            kw={'emissiveTexture':TextureInfo(index=base),'emissiveFactor':[1,.75,.38], 'doubleSided':True}
        idx=len(self.gltf.materials)
        self.gltf.materials.append(Material(name=name,pbrMetallicRoughness=pbr,normalTexture=normal,**kw))
        return idx


def beam(g,material,a,b,r,segments=6):
    """Straight compact round beam with end caps and oriented normals."""
    a=np.array(a,dtype=float); b=np.array(b,dtype=float); axis=b-a; axis/=np.linalg.norm(axis)
    ref=np.array([0.,0.,1.]) if abs(axis[2])<.9 else np.array([1.,0.,0.])
    u=np.cross(ref,axis); u/=np.linalg.norm(u); v=np.cross(axis,u)
    for i in range(segments):
        t0=2*math.pi*i/segments; t1=2*math.pi*(i+1)/segments
        f=lambda p,t:p+r*(u*math.cos(t)+v*math.sin(t))
        p0,p1,p2,p3=f(a,t0),f(a,t1),f(b,t1),f(b,t0)
        g.quad(material,[p0,p1,p2,p3])
        g.triangle(material,[a,p1,p0],[(.5,.5),(0,0),(1,0)])
        g.triangle(material,[b,p3,p2],[(.5,.5),(0,0),(1,0)])


def frustum(g,mat,z0,z1,half0,half1,cx=0,cy=0):
    """Square tapered plinth or hipped cap, real silhouette not a painted box."""
    p0=[(cx-half0,cy-half0,z0),(cx+half0,cy-half0,z0),(cx+half0,cy+half0,z0),(cx-half0,cy+half0,z0)]
    p1=[(cx-half1,cy-half1,z1),(cx+half1,cy-half1,z1),(cx+half1,cy+half1,z1),(cx-half1,cy+half1,z1)]
    for i in range(4):
        j=(i+1)%4
        g.quad(mat,[p0[i],p0[j],p1[j],p1[i]])
    if half1>0:
        g.quad(mat,[p1[0],p1[1],p1[2],p1[3]])


def gaslamp():
    g=Geometry('station_gaslamp')
    g.box('iron',-.225,.225,-.225,.225,0,.09)
    frustum(g,'iron',.09,.16,.225,.19)
    g.box('iron',-.19,.19,-.19,.19,.16,.57)
    g.box('brass',-.196,.196,-.196,.196,.17,.19)
    g.box('brass',-.196,.196,-.196,.196,.53,.55)
    # A single decorative panel on each of the four plinth faces.
    x=.192
    uv=[(.1,.9),(.9,.9),(.9,.1),(.1,.1)]
    g.quad('ornament',[(-.13,-x,.22),(.13,-x,.22),(.13,-x,.50),(-.13,-x,.50)],uv)
    g.quad('ornament',[(.13,x,.22),(-.13,x,.22),(-.13,x,.50),(.13,x,.50)],uv)
    g.quad('ornament',[(x,-.13,.22),(x,.13,.22),(x,.13,.50),(x,-.13,.50)],uv)
    g.quad('ornament',[(-x,.13,.22),(-x,-.13,.22),(-x,-.13,.50),(-x,.13,.50)],uv)
    frustum(g,'iron',.57,.67,.20,.145)
    g.lathe('iron',0,0,[(.67,.145),(.72,.15),(.76,.11),(.82,.09),(.87,.12),(.94,.12),
                       (1.02,.085),(1.12,.066),(2.65,.066),(2.72,.09),(2.79,.09),
                       (2.85,.13),(2.92,.10),(2.98,.085)],segments=10)
    for z0,z1,radius in ((.74,.77,.115),(1.02,1.05,.095),(2.69,2.72,.095),(2.80,2.83,.10)):
        g.lathe('brass',0,0,[(z0,radius),(z1,radius)],segments=10)
    g.box('iron',-.22,.22,-.22,.22,2.94,3.00)
    g.box('brass',-.24,.24,-.24,.24,2.99,3.035)
    z0,z1=3.035,3.62; b,t=.205,.27
    uv=[(0,1),(1,1),(1,0),(0,0)]
    g.quad('lantern',[(-b,-b,z0),(b,-b,z0),(t,-t,z1),(-t,-t,z1)],uv)
    g.quad('lantern',[(b,b,z0),(-b,b,z0),(-t,t,z1),(t,t,z1)],uv)
    g.quad('lantern',[(b,-b,z0),(b,b,z0),(t,t,z1),(t,-t,z1)],uv)
    g.quad('lantern',[(-b,b,z0),(-b,-b,z0),(-t,-t,z1),(-t,t,z1)],uv)
    for sx in (-1,1):
        for sy in (-1,1):
            beam(g,'iron',(sx*b,sy*b,z0),(sx*t,sy*t,z1),.018,6)
    g.box('iron',-.29,.29,-.29,.29,3.61,3.66)
    g.box('brass',-.29,.29,-.29,.29,3.66,3.68)
    frustum(g,'iron',3.68,3.80,.29,.12)
    g.lathe('iron',0,0,[(3.80,.12),(3.83,.12),(3.83,.085),(3.90,.085),(3.92,.115),(3.94,.06)],segments=8)
    g.lathe('brass',0,0,[(3.94,.06),(3.97,.04),(4.0,.006)],segments=8)
    return g


def ribbon(g,mat,x,width,points,thickness):
    """Thin solid curved side support in the YZ plane."""
    points=np.asarray(points,dtype=float)
    for a,b in zip(points[:-1],points[1:]):
        tangent=b-a; tangent/=np.linalg.norm(tangent)
        n=np.array([-tangent[1],tangent[0]])*thickness/2
        al=a-n; ah=a+n; bl=b-n; bh=b+n
        def p(x0,yz): return (x0,float(yz[0]),float(yz[1]))
        xl=x-width/2; xh=x+width/2
        g.quad(mat,[p(xh,al),p(xh,bl),p(xh,bh),p(xh,ah)])
        g.quad(mat,[p(xl,bl),p(xl,al),p(xl,ah),p(xl,bh)])
        g.quad(mat,[p(xl,al),p(xl,bl),p(xh,bl),p(xh,al)])
        g.quad(mat,[p(xh,ah),p(xh,bh),p(xl,bh),p(xl,ah)])


def slanted_slat(g,z0,z1):
    x0,x1=-.965,.965
    y0=.235+(z0-.50)*.22; y1=.235+(z1-.50)*.22
    d=.04
    a=(x0,y0,z0);b=(x1,y0,z0);c=(x1,y1,z1);e=(x0,y1,z1)
    A=(x0,y0+d,z0);B=(x1,y0+d,z0);C=(x1,y1+d,z1);E=(x0,y1+d,z1)
    g.quad('wood',[a,b,c,e]);g.quad('wood',[B,A,E,C])
    g.quad('wood',[A,a,e,E]);g.quad('wood',[b,B,C,c])
    g.quad('wood',[e,c,C,E]);g.quad('wood',[A,B,b,a])


def bench():
    g=Geometry('station_bench')
    for i in range(5):
        y=-.29+i*.105
        g.box('wood',-.995,.995,y,y+.087,.435,.475)
    for i in range(5):
        z=.505+i*.096
        slanted_slat(g,z,z+.079)
    for x in (-1.01,1.01):
        g.box('iron',x-.04,x+.04,-.34,-.23,0,.045)
        g.box('iron',x-.04,x+.04,.24,.35,0,.045)
        ribbon(g,'iron',x,.055,[(-.285,.035),(-.28,.17),(-.28,.32),(-.25,.47)],.045)
        ribbon(g,'iron',x,.055,[(.29,.035),(.29,.25),(.31,.45),(.34,.68),(.37,.99)],.047)
        curve=[]
        for i in range(7):
            y=-.285+i*.575/6
            z=.06+.27*math.sin(math.pi*i/6)
            curve.append((y,z))
        ribbon(g,'iron',x,.055,curve,.043)
        ribbon(g,'iron',x,.06,[(.37,.98),(.32,.88),(.26,.76),(.17,.72),(.05,.72),(-.12,.75),(-.22,.75),(-.27,.70)],.06)
        beam(g,'iron',(x,-.25,.47),(x,-.25,.72),.025,6)
        # The central decorative panel is painted relief; no scrollwork microgeometry.
        xl=x-.030 if x<0 else x+.030
        if x<0:
            points=[(xl,.12,.22),(xl,-.12,.22),(xl,-.12,.41),(xl,.12,.41)]
        else:
            points=[(xl,-.12,.22),(xl,.12,.22),(xl,.12,.41),(xl,-.12,.41)]
        g.quad('ornament',points,[(.18,.82),(.82,.82),(.82,.18),(.18,.18)])
    return g


def ribbon_xz(g,mat,y,depth,points,thickness):
    """Solid curved bracket on the facade-facing XZ plane."""
    points=np.asarray(points,dtype=float)
    for a,b in zip(points[:-1],points[1:]):
        tangent=b-a; tangent/=np.linalg.norm(tangent)
        n=np.array([-tangent[1],tangent[0]])*thickness/2
        al=a-n; ah=a+n; bl=b-n; bh=b+n
        def p(y0,xz): return (float(xz[0]),y0,float(xz[1]))
        yf=y-depth/2; yb=y+depth/2
        g.quad(mat,[p(yf,al),p(yf,bl),p(yf,bh),p(yf,ah)])
        g.quad(mat,[p(yb,bl),p(yb,al),p(yb,ah),p(yb,bh)])
        g.quad(mat,[p(yf,al),p(yb,al),p(yb,bl),p(yf,bl)])
        g.quad(mat,[p(yb,ah),p(yf,ah),p(yf,bh),p(yb,bh)])


def reverse_clock_face(g,cx,y,cz,r,segments=32):
    """A readable rear face: reverse winding and mirror UVs for rear viewers."""
    for i in range(segments):
        a=2*math.pi*i/segments; b=2*math.pi*(i+1)/segments
        def p(t): return (cx+r*math.cos(t),y,cz+r*math.sin(t))
        def uv(t): return (.5-.5*math.cos(t),.5-.5*math.sin(t))
        g.triangle('clock',[(cx,y,cz),p(b),p(a)],[(.5,.5),uv(b),uv(a)])


def station_clock_sign():
    g=Geometry('station_clock_sign')
    post=-.51
    g.box('iron',post-.22,post+.22,-.22,.22,0,.10)
    frustum(g,'iron',.10,.18,.22,.17,cx=post)
    g.box('iron',post-.17,post+.17,-.17,.17,.18,.55)
    for z in (.19,.53):
        g.box('brass',post-.175,post+.175,-.175,.175,z,z+.025)
    g.quad('ornament',[(post-.125,-.172,.23),(post+.125,-.172,.23),
                       (post+.125,-.172,.49),(post-.125,-.172,.49)],
           [(.15,.85),(.85,.85),(.85,.15),(.15,.15)])
    frustum(g,'iron',.55,.66,.18,.115,cx=post)
    g.lathe('iron',post,0,[(.66,.115),(.72,.12),(.77,.085),(.84,.075),
                          (3.25,.075),(3.31,.10),(3.39,.10),(3.45,.15),
                          (3.52,.12)],segments=10)
    for z0,z1,r in ((.73,.76,.12),(1.05,1.08,.083),(2.00,2.03,.083),(3.30,3.33,.105)):
        g.lathe('brass',post,0,[(z0,r),(z1,r)],segments=10)
    g.lathe('brass',post,0,[(3.52,.12),(3.57,.15),(3.62,.10),(3.70,.08),(3.78,.012)],segments=10)
    # Broad cast-iron sweep holds the clock above its side-mounted sign.
    ribbon_xz(g,'iron',0,.075,[(post,2.03),(-.44,2.35),(-.34,2.72),(-.21,3.08),
                                (-.08,3.36),(.08,3.52),(.22,3.55)],.065)
    ribbon_xz(g,'brass',-.041,.012,[(post,2.03),(-.44,2.35),(-.34,2.72),(-.21,3.08),
                                    (-.08,3.36),(.08,3.52),(.22,3.55)],.015)
    x,z=.22,2.92
    beam(g,'iron',(x,-.12,z),(x,.12,z),.50,segments=24)
    g.circle('clock',x,-.126,z,.464,segments=32)
    reverse_clock_face(g,x,.126,z,.464,segments=32)
    g.ring('brass',x,-.14,z,.463,.500,0,2*math.pi,segments=24,depth=.035)
    for dx in (-.13,.13):
        beam(g,'iron',(x+dx,0,2.42),(x+dx,0,2.29),.012,segments=6)
    g.box('iron',x-.205,x+.205,-.055,.055,1.88,2.29)
    g.image_panel('sign3',x-.20,x+.20,-.058,1.885,2.285)
    g.quad('sign3',[(x+.20,.058,1.885),(x-.20,.058,1.885),
                    (x-.20,.058,2.285),(x+.20,.058,2.285)],
           [(0,1),(1,1),(1,0),(0,0)])
    return g


def export(name,geo,tex):
    writer=Writer()
    mats={n:writer.add_material(n,tex[n]) for n in sorted(geo.parts)}
    idx=writer.add_mesh(geo,mats)
    writer.instance(idx,name,0)
    writer.save(OUT/f'{name}.glb')


def main():
    tex=maps()
    modules={'station_gaslamp':gaslamp(),'station_bench':bench(),
             'station_clock_sign':station_clock_sign()}
    for name,geo in modules.items(): export(name,geo,tex)
    manifest={'coordinate_system':{'units':'meters','authored_up':'Z','front':'-Y',
                 'origin':'centered X/Y and on ground Z=0',
                 'gltf_root_rotation_xyzw':[-math.sqrt(.5),0,0,math.sqrt(.5)]},'modules':{}}
    for name,geo in modules.items():
        manifest['modules'][name]={'file':name+'.glb','bounds_author_z_up':geo.bounds(),
                                   'triangles':geo.triangles(),'materials':list(geo.parts),
                                   'uv_coverage':'all triangles'}
    manifest['modules']['station_gaslamp']['emission']='emissive amber lantern texture, no external light required'
    manifest['source_textures']={n:{k:str(p.relative_to(STATION)) for k,p in rec.items()} for n,rec in tex.items()}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest['modules'],indent=2))

if __name__=='__main__': main()
