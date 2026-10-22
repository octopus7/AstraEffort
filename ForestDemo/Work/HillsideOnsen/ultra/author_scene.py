"""Original Sansol Springs geometry. Run only in a private background Blender."""
import bpy, bmesh, math, json, random, time
from pathlib import Path
from mathutils import Vector, Matrix
from datetime import datetime, timezone

W = Path('D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra')
A = W / 'SourceArt'
A.mkdir(exist_ok=True)
random.seed(102323)
START = datetime.now(timezone.utc).isoformat()
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1.0
G = {}
SEMANTICS = []
PALETTE = {
 'Terrain': ('grass', (0.31,0.39,0.25),32),
 'Earth': ('limestone',(0.30,0.29,0.22),64),
 'Stone': ('limestone',(0.56,0.54,0.44),96),
 'BathStone': ('limestone',(0.63,0.62,0.53),96),
 'Path': ('gravel',(0.62,0.58,0.46),96),
 'Cedar': ('cedar',(0.35,0.22,0.13),128),
 'DarkWood': ('cedar',(0.19,0.13,0.09),128),
 'Plaster': ('plaster',(0.77,0.74,0.61),128),
 'Roof': ('slate',(0.20,0.29,0.32),128),
 'Metal': ('slate',(0.12,0.16,0.16),128),
 'Glass': ('plaster',(0.70,0.55,0.29),128),
 'Leaves': ('grass',(0.22,0.33,0.22),64),
 'LeavesLight': ('grass',(0.34,0.43,0.24),64),
 'Trunks': ('cedar',(0.30,0.22,0.14),96),
 'Water': ('water',(0.18,0.48,0.46),128),
 'Stream': ('water',(0.30,0.56,0.52),128),
 'Steam': ('steam',(0.82,0.86,0.82),128),
 'Fabric': ('plaster',(0.32,0.44,0.45),128),
 'Foam': ('water',(0.67,0.76,0.68),128),
}

def add(cat, verts, faces):
    g = G.setdefault(cat, [[],[]])
    base = len(g[0]); g[0].extend([tuple(v) for v in verts])
    g[1].extend([tuple(base+i for i in f) for f in faces])

def box(cat, center, size, bevel=0.06, angle=0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm,size=1)
    for v in bm.verts: v.co = Vector((v.co.x*size[0],v.co.y*size[1],v.co.z*size[2]))
    if bevel > 0:
        bmesh.ops.bevel(bm,geom=list(bm.edges),offset=min(bevel,min(size)*0.22),segments=2,affect='EDGES')
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    rot = Matrix.Rotation(angle,3,'Z')
    add(cat,[rot@v.co+Vector(center) for v in bm.verts],[[v.index for v in f.verts] for f in bm.faces])
    bm.free()

def ico(cat, center, scale, subdivisions=1, jitter=0.05):
    bm=bmesh.new(); bmesh.ops.create_icosphere(bm,subdivisions=subdivisions,radius=1)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    vs=[]
    for v in bm.verts:
        k=1+random.uniform(-jitter,jitter)
        vs.append(tuple(center[i]+v.co[i]*scale[i]*k for i in range(3)))
    add(cat,vs,[[v.index for v in f.verts] for f in bm.faces]); bm.free()

def pole(cat,p,q,r=0.08,sides=8,r2=None):
    p,q=Vector(p),Vector(q); d=q-p
    basis=d.normalized().rotation_difference(Vector((0,0,1))).inverted().to_matrix()
    vs=[]
    for c,rad in [(p,r),(q,r if r2 is None else r2)]:
        for i in range(sides):
            a=i*2*math.pi/sides; vs.append(c+basis@Vector((rad*math.cos(a),rad*math.sin(a),0)))
    fs=[tuple(reversed(range(sides))),tuple(range(sides,2*sides))]
    fs += [(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)]
    add(cat,vs,fs)

ROUTE=[(0,-45,2.6),(-26,-34,2.6),(-28,-24,2.6),(27,-13,6.2),(29,4,6.2),(-27,19,10.1),(-26,30,10.1),(-6,34,10.1)]
STAIRS=[(-24,-20,-12,3.6,6.2),(25,11,21,6.2,10.1)]
STAIR_LINK=[(-24,-23.2,2.861818),(-24,-20,3.6)]
STREAM=[(4.9,25,9.88),(1,22,9.88),(-2,18,9.0),(-3,14,8.0),(-5,10,6.9),(-7,6.4,6.02)]
POOLS=[{'name':'central','x':-8,'y':1,'z':6.2,'rx':8.0,'ry':5.8},
       {'name':'upper','x':10,'y':25,'z':10.1,'rx':5.1,'ry':3.8}]
BUILDINGS=[(-14,-30,2.6,8.0,6.2,4.4,'arrival_lodge'),(13,0,6.2,9.0,8.0,4.6,'bathhouse'),
           (-17,29,10.1,8.0,6.2,4.4,'upper_lodge'),(26,28,10.1,6.7,5.8,4.0,'tea_house')]

def nearest(x,y,route=ROUTE):
    best=(1e9,0,None)
    for p,q in zip(route,route[1:]):
        dx,dy=q[0]-p[0],q[1]-p[1]; t=max(0,min(1,((x-p[0])*dx+(y-p[1])*dy)/(dx*dx+dy*dy)))
        xx,yy=p[0]+t*dx,p[1]+t*dy; dd=math.hypot(x-xx,y-yy)
        if dd<best[0]:best=(dd,p[2]+t*(q[2]-p[2]),(xx,yy))
    return best

def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)

def height(x,y):
    # Quiet flat inhabited terraces, with rounded banks and a rising northern hill.
    z=2.6+3.6*smooth(-22,-12,y)+3.9*smooth(11,21,y)+7.5*smooth(35,50,y)
    z += (0.55*math.sin(x*.12)+.3*math.sin(y*.2+x*.06))*smooth(33,47,abs(x))
    d,rz,_=nearest(x,y)
    if d<4.5:z=(z*(1-smooth(4.5,1.8,d)))+(rz-.08)*smooth(4.5,1.8,d)
    for bx,by,bz,bw,bd,bh,name in BUILDINGS:
        d=max(abs(x-bx)-bw/2-1,abs(y-by)-bd/2-1)
        if d<3: f=1-smooth(0,3,d);z=z*(1-f)+bz*f
    # Central entry apron and upper bath access.
    for cx,cy,sx,sy,zz in [(-1,-8,24,2.1,6.2),(9,19.5,7,1.5,10.1)]:
        d=max(abs(x-cx)-sx,abs(y-cy)-sy)
        if d<1.8:f=1-smooth(0,1.8,d);z=z*(1-f)+zz*f
    for p in POOLS:
        r=math.sqrt(((x-p['x'])/p['rx'])**2+((y-p['y'])/p['ry'])**2)
        if r<1.28:
            rim=p['z']; bottom=rim-1.25
            target=bottom+(rim-bottom)*smooth(.7,1.1,r)
            f=1-smooth(1.1,1.28,r);z=z*(1-f)+target*f
    # Reapply the route after architectural grading so foundations' feathered
    # influence cannot leave a ramp suspended over a lower pad.
    d,rz,_=min(nearest(x,y),nearest(x,y,STAIR_LINK),key=lambda v:v[0])
    if d<4.5:
        f=1-smooth(1.8,4.5,d);z=z*(1-f)+(rz-.03)*f
    main_d,main_z,_=nearest(x,y)
    if main_d<2.4:
        cap=main_z-.03
        f=1-smooth(1.8,2.4,main_d)
        z=z*(1-f)+min(z,cap)*f
    for sx,sy0,sy1,sz0,sz1 in STAIRS:
        if abs(x-sx)<2.8 and sy0-1<y<sy1+1:
            t=max(0,min(1,(y-sy0)/(sy1-sy0)));under=sz0+t*(sz1-sz0)-.22
            f=(1-smooth(1.35,2.8,abs(x-sx)))*(1-smooth(0,1,max(sy0-y,y-sy1,0)))*smooth(1.6,2.2,d)
            z=z*(1-f)+min(z,under)*f
    channel_d,channel_z,_=nearest(x,y,STREAM)
    protected_apron=(1<x<17 and 17.5<y<21.5)
    if channel_d<2 and main_d>2.2 and not protected_apron:
        f=1-smooth(.9,2,channel_d)
        z=min(z,z*(1-f)+(channel_z-.20)*f)
    # Route-bank blending must not rise through a building's foundation.
    # Cover adjacent 1m grid vertices too, so interpolated footprint corners stay clear.
    for bx,by,bz,bw,bd,bh,name in BUILDINGS:
        if abs(x-bx)<=bw/2+.55 and abs(y-by)<=bd/2+.55:
            z=min(z,bz)
    return z

def ribbon(cat,pts,width,thickness=0,segments=1,conform=False):
    # Each quad is explicitly triangulated later. Constant width with overlapping rounded joins.
    for p,q in zip(pts,pts[1:]):
        p,q=Vector(p),Vector(q);d=q-p;side=Vector((-d.y,d.x,0)).normalized()*width/2
        n=max(1,math.ceil(d.length/segments));vs=[]
        if conform:
            # Sample the actual 1m triangle surface, not the continuous grading
            # function. Dense cross sections also retain a terrain-cell crease.
            across=math.ceil(width/.1)
            for i in range(n+1):
                c=p+d*i/n
                for j in range(across+1):
                    v=c+side*(2*j/across-1)
                    ix=max(-50,min(49,math.floor(v.x)));iy=max(-50,min(49,math.floor(v.y)))
                    fx,fy=v.x-ix,v.y-iy
                    aa,bb,cc,dd=height(ix,iy),height(ix+1,iy),height(ix,iy+1),height(ix+1,iy+1)
                    surface=aa+(bb-aa)*fx+(dd-bb)*fy if fx>=fy else aa+(dd-cc)*fx+(cc-aa)*fy
                    v.z=surface+.10;vs.append(v)
            fs=[]
            for i in range(n):
                for j in range(across):
                    a=i*(across+1)+j;b=a+across+1
                    fs.extend([(a,b,b+1),(a,b+1,a+1)])
            count=len(vs);vs += [v-Vector((0,0,.16)) for v in vs]
            for i in range(n):
                a=i*(across+1);b=a+across+1
                fs.extend([(a,a+count,b+count,b),(a+across,b+across,b+across+count,a+across+count)])
            add(cat,vs,fs)
            continue
        for i in range(n+1):
            c=p+d*i/n
            for v in [c-side,c+side]:
                vs.append(v)
        fs=[(i*2,i*2+2,i*2+3,i*2+1) for i in range(n)]
        if cat=='Path':
            count=len(vs);vs += [v-Vector((0,0,.12)) for v in vs]
            for i in range(n):
                a=i*2;b=(i+1)*2
                fs.extend([(a,a+count,b+count,b),(a+1,b+1,b+1+count,a+1+count)])
        add(cat,vs,fs)

def rail(p,q,width=3.2,both=True):
    p,q=Vector(p),Vector(q);d=q-p;side=Vector((-d.y,d.x,0)).normalized()*width/2
    for sign in ([-1,1] if both else [1]):
        a=p+side*sign;b=q+side*sign
        count=math.ceil(d.length/2.8)
        for i in range(count+1):
            c=a+(b-a)*i/count;pole('DarkWood',c,c+Vector((0,0,1.02)),.065)
        for z in [.52,1.0]:pole('Cedar',a+Vector((0,0,z)),b+Vector((0,0,z)),.055)

# Terrain: deterministic triangles, not importer-dependent nonplanar quads.
N=100;vs=[]
for j in range(N+1):
    for i in range(N+1):
        x=-50+i;y=-50+j;vs.append((x,y,height(x,y)))
fs=[]
for j in range(N):
    for i in range(N):
        a=j*(N+1)+i;b=a+1;c=a+N+1;d=c+1
        fs.extend([(a,b,d),(a,d,c)])
add('Terrain',vs,fs)
for edge in [[(-50+i,-50) for i in range(101)],[(50,-50+i) for i in range(101)],[(50-i,50) for i in range(101)],[(-50,50-i) for i in range(101)]]:
    vs=[]
    for x,y in edge:vs.extend([(x,y,-1),(x,y,height(x,y))])
    add('Earth',vs,[(i*2,i*2+2,i*2+3,i*2+1) for i in range(100)])

# Continuous accessible route and natural rounded paved aprons.
ribbon('Path',[(x,y,z+.045) for x,y,z in ROUTE],3.2,segments=.6)
ribbon('Path',[(x,y,z+.045) for x,y,z in STAIR_LINK],2.6,segments=.20,conform=True)
for x,y,z in ROUTE[1:-1]:
    n=20;add('Path',[(x,y,z+.048)]+[(x+1.6*math.cos(i*2*math.pi/n),y+1.6*math.sin(i*2*math.pi/n),z+.048) for i in range(n)],[(0,i+1,(i+1)%n+1) for i in range(n)])
box('Path',(-1,-8,6.16),(46,3.8,.16),.22)
box('Path',(9,19.5,10.08),(14,2.7,.15),.16)
rail(ROUTE[2],ROUTE[3]);rail(ROUTE[4],ROUTE[5])

# Retaining walls break banks into inhabited terraces, with gaps at stairs/routes.
for x0,x1,y,zlo,zhi in [(-20,20,-11.4,3.6,6.12),(-21,21,21.3,7.6,10.02)]:
    for row in range(4):
        step=(zhi-zlo)/4
        for x in range(x0,x1,3):
            xx=x+1.45+(1.4 if row%2 else 0)
            if xx>x1:continue
            box('Stone',(xx,y,zlo+(row+.5)*step),(2.85,.8,step-.035),.11)

# Alternate compact stairs, with ground skirts and rails.
stairs=[]
for x,y0,y1,z0,z1 in STAIRS:
    count=math.ceil((z1-z0)/.18);run=(y1-y0)/count;rise=(z1-z0)/count
    for i in range(count):
        yy=y0+(i+.5)*run;top=z0+(i+1)*rise
        bottom=z0-1.0
        box('Stone',(x,yy,(bottom+top)/2),(2.6,run+.03,top-bottom),.025)
    rail((x,y0,z0),(x,y1,z1),2.5)
    stairs.append({'start':[x,y0,z0],'end':[x,y1,z1],'riser_m':rise,'tread_m':run})

# Baths: stone bed, irregular rim stones, water, and timber steps.
for p in POOLS:
    x,y,z,rx,ry=[p[k] for k in ['x','y','z','rx','ry']]
    n=64
    add('BathStone',[(x,y,z-1.12)]+[(x+rx*.95*math.cos(i*2*math.pi/n),y+ry*.95*math.sin(i*2*math.pi/n),z-1.05) for i in range(n)],[(0,i+1,(i+1)%n+1) for i in range(n)])
    # Nested water rings support subtle shader displacement.
    vs=[(x,y,z-.18)];rings=6
    for ring in range(1,rings+1):
        for i in range(n):
            a=i*2*math.pi/n;rr=ring/rings*.965;vs.append((x+rx*rr*math.cos(a),y+ry*rr*math.sin(a),z-.18))
    fs=[(0,1+i,1+(i+1)%n) for i in range(n)]
    for ring in range(rings-1):
        a=1+ring*n;b=a+n
        fs.extend([(a+i,b+i,b+(i+1)%n,a+(i+1)%n) for i in range(n)])
    add('Water',vs,fs)
    for i in range(30 if rx>6 else 22):
        a=i*2*math.pi/(30 if rx>6 else 22);xx=x+rx*math.cos(a);yy=y+ry*math.sin(a)
        ico('BathStone',(xx,yy,z+.10),(random.uniform(.55,.9),random.uniform(.5,.75),random.uniform(.38,.6)),2,.09)
    for i in range(3):box('Cedar',(x,y-ry+1.1+i*.42,z-.14-i*.28),(2.1,.45,.16),.04)
    # Individual wisps are asymmetric soft cards, crossed to remain visible from multiple viewpoints.
    for i in range(8 if rx>6 else 5):
        a=random.random()*2*math.pi;rr=random.uniform(.15,.7)
        xx=x+rx*rr*math.cos(a);yy=y+ry*rr*math.sin(a);h=random.uniform(1.5,2.8);w=random.uniform(1.5,2.5)
        for ang in [0,math.pi/2]:
            dx,dy=math.cos(ang)*w/2,math.sin(ang)*w/2
            add('Steam',[(xx-dx,yy-dy,z-.05),(xx+dx,yy+dy,z-.05),(xx+dx+.2,yy+dy,z+h),(xx-dx+.2,yy-dy,z+h)],[(0,1,2,3)])
    SEMANTICS.append({'type':'bath','name':p['name'],'center':[x,y,z],'water_z':z-.18,'bottom_z':z-1.12,'radii':[rx,ry]})

# Stream descends in visible small stone channels, ending in the large pool.
stream=STREAM
ribbon('Stream',stream,.72,segments=.5)
for p,q in zip(stream,stream[1:]):
    d=Vector(q)-Vector(p);side=Vector((-d.y,d.x,0)).normalized()*.6
    for i in range(max(2,math.ceil(d.length/.8))):
        c=Vector(p)+d*i/max(2,math.ceil(d.length/.8))
        for sign in [-1,1]:ico('BathStone',c+side*sign-Vector((0,0,.12)),(.5,.5,.36),1,.1)
# Small bridge spans the stream along the upper switchback.
p,q=Vector(ROUTE[4]),Vector(ROUTE[5]);d=q-p;unit=d.normalized();center=p+d*.60
angle=math.atan2(d.y,d.x)
for i in range(19):
    c=center+unit*(i-9)*.27
    box('Cedar',(c.x,c.y,c.z+.11),(.25,3.25,.14),.025,angle)

def building(x,y,z,w,dep,h,name):
    box('Stone',(x,y,z-.48),(w+.45,dep+.45,1.12),.12)
    box('Cedar',(x,y-dep/2-.85,z+.16),(w+1,1.8,.25),.07)
    box('Plaster',(x,y,z+h/2+.12),(w,dep,h),.12)
    for xx in [x-w/2+.12,x+w/2-.12]:
        for yy in [y-dep/2-.06,y+dep/2+.06]:box('DarkWood',(xx,yy,z+h/2),(.18,.2,h+.15),.03)
    for zz in [z+.75,z+h-.12]:box('Cedar',(x,y-dep/2-.07,zz),(w+.15,.16,.16),.025)
    # Front recessed dark doorway, slatted panels, paper-glass window pair.
    box('DarkWood',(x,y-dep/2-.11,z+1.3),(1.5,.12,2.6),.025)
    for dx in [-w*.30,w*.30]:
        box('DarkWood',(x+dx,y-dep/2-.12,z+2.05),(1.8,.14,1.65),.04)
        box('Glass',(x+dx,y-dep/2-.205,z+2.05),(1.55,.025,1.4),.02)
        for off in [-.51,0,.51]:box('Cedar',(x+dx+off,y-dep/2-.24,z+2.05),(.045,.055,1.5),.005)
        box('Cedar',(x+dx,y-dep/2-.24,z+2.05),(1.6,.055,.045),.005)
    for xx in [x-w/2+.15,x+w/2-.15]:box('Cedar',(xx,y-dep/2-1.45,z+h*.44),(.16,.16,h*.88),.03)
    # Thin, rounded gable roof with ridge running front-to-back.
    rw=w/2+.8;rd=dep/2+.85;roofz=z+h+.1;rise=w*.22
    for sign in [-1,1]:
        vs=[(x,y-rd,roofz+rise),(x+sign*rw,y-rd,roofz),(x+sign*rw,y+rd,roofz),(x,y+rd,roofz+rise)]
        add('Roof',vs+[(a,b,c-.18) for a,b,c in vs],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)])
        pole('Roof',(x+sign*rw,y-rd,roofz),(x+sign*rw,y+rd,roofz),.16,8)
        pole('DarkWood',(x,y-rd-.015,roofz+rise-.15),(x+sign*rw,y-rd-.015,roofz-.15),.09)
    pole('Roof',(x,y-rd-.12,roofz+rise+.04),(x,y+rd+.12,roofz+rise+.04),.19,10)
    # Gable timber triangle closes the exposed roof end.
    for yy in [y-dep/2,y+dep/2]:add('Cedar',[(x-w/2,yy,roofz),(x+w/2,yy,roofz),(x,yy,roofz+rise)],[(0,1,2)])
    # Restrained entry curtains.
    for dx in [-.38,.38]:box('Fabric',(x+dx,y-dep/2-.33,z+2.45),(.68,.04,.65),.025)
    SEMANTICS.append({'type':'building','name':name,'center':[x,y,z],'footprint':[w,dep],'ground_z':z,'foundation_bottom':z-1.04,'foundation_top':z+.08})

for b in BUILDINGS:building(*b)

# Simple open arrival gate, sign board, lanterns and benches.
for x in [-2.2,2.2]:box('DarkWood',(x,-39,4.25),(.25,.25,3.3),.045)
box('Cedar',(0,-39,5.85),(5.2,.35,.3),.06)
box('Roof',(0,-39,6.15),(5.8,1.3,.25),.1)
box('Cedar',(3.2,-38.8,3.5),(.14,.14,1.8),.03)
box('DarkWood',(3.2,-38.8,4.15),(1.8,.18,.8),.06)

for x,y,z in [(-17,-7,6.2),(4,-7,6.2),(18,-7,6.2),(-24,27,10.1),(19,20,10.1),(-22,-33,2.6),(5,-40,2.6)]:
    box('Stone',(x,y,z+.12),(.65,.65,.24),.08)
    pole('DarkWood',(x,y,z+.2),(x,y,z+2.65),.075)
    box('DarkWood',(x,y,z+2.5),(.55,.55,.64),.065)
    box('Glass',(x,y-.285,z+2.5),(.38,.025,.43),.02)
    box('Glass',(x+.285,y,z+2.5),(.025,.38,.43),.02)
    box('Roof',(x,y,z+2.91),(.8,.8,.16),.06)
    SEMANTICS.append({'type':'lamp','position':[x,y,z+2.5]})
for x,y,z in [(-18,-7,6.2),(-17,8.2,6.2),(18,20,10.1),(-10,-35,2.6)]:
    box('Cedar',(x,y,z+.48),(2.5,.58,.13),.045)
    for dx in [-.8,.8]:box('DarkWood',(x+dx,y,z+.22),(.17,.45,.44),.03)
    box('Cedar',(x,y+.25,z+.93),(2.5,.12,.52),.035)
# Wash station with basins, water spouts and low stools beside main bath.
for i in range(3):
    x=-18.8;y=-1.5+i*1.6;z=6.2
    box('Cedar',(x,y,z+.28),(.8,.7,.55),.08)
    ico('BathStone',(x-.05,y,z+.68),(.55,.55,.2),2,0)
    pole('Metal',(x+.25,y,z+.7),(x+.25,y,z+1.15),.04)
    pole('Metal',(x+.25,y,z+1.15),(x-.1,y,z+1.15),.04)
    box('Cedar',(x-1.3,y,z+.2),(.55,.55,.4),.07)

# Original, sparse rounded trees: layered evergreen crowns and broadleaf clusters.
trees=[(-38,-29,5),(-35,-8,6),(-39,15,7),(-33,33,7),(-25,42,7),(0,42,6),(20,42,7),(38,35,6),(40,14,6),(40,-7,5),(34,-31,5),(23,-38,5),(-40,39,6),(35,44,6),(-5,37,4),(-31,5,4)]
for idx,(x,y,h) in enumerate(trees):
    z=height(x,y);pole('Trunks',(x,y,z-.2),(x,y,z+h*.9),.22,9,.08)
    cat='Leaves' if idx%3 else 'LeavesLight'
    if idx%3:
        for zz,rr in [(h*.38,h*.39),(h*.60,h*.31),(h*.79,h*.22)]:
            # Rounded rings create a soft conifer silhouette without needle noise.
            rings=[(zz-h*.13,.35),(zz-h*.09,rr*.83),(zz,rr),(zz+h*.18,rr*.66),(zz+h*.30,.10)]
            vs=[];n=12
            for hh,r in rings:
                for j in range(n):a=2*math.pi*j/n;vs.append((x+r*math.cos(a),y+r*math.sin(a),z+hh))
            fs=[]
            for k in range(len(rings)-1):fs.extend([(k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j) for j in range(n)])
            fs.extend([tuple(reversed(range(n))),tuple(range((len(rings)-1)*n,len(rings)*n))]);add(cat,vs,fs)
    else:
        for dx,dy,hh,rr in [(-1.1,0,h*.65,2.0),(1.1,.4,h*.73,2.2),(0,-.7,h*.95,2.1)]:ico(cat,(x+dx,y+dy,z+hh),(rr,rr*.9,rr*.86),2,.04)

for i in range(95):
    x=random.uniform(-44,44);y=random.uniform(-42,43)
    if nearest(x,y)[0]<4.5:continue
    if any(abs(x-b[0])<b[3]/2+2 and abs(y-b[1])<b[4]/2+2 for b in BUILDINGS):continue
    if any(((x-p['x'])/(p['rx']+2))**2+((y-p['y'])/(p['ry']+2))**2<1 for p in POOLS):continue
    if -25<x<24 and -11<y<-4:continue
    z=height(x,y);r=random.uniform(.35,1.1)
    ico('LeavesLight' if i%3 else 'Stone',(x,y,z+r*.25),(r,r*.8,r*.55),2,.08)

def pack_uv(obj, density):
    me=obj.data;uv=me.uv_layers.new(name='SurfaceUV');charts=[]
    if obj.name=='SM_Steam':
        for p in me.polygons:
            for li,co in zip(p.loop_indices,[(0,0),(1,0),(1,1),(0,1)]):uv.data[li].uv=co
        return {'kind':'intentional repeated full-card alpha UV','atlas_pixels':512,'target_px_per_m':None,'charts':len(me.polygons),'overlap':'intentional steam sprites'}
    for p in me.polygons:
        vv=[me.vertices[me.loops[i].vertex_index].co for i in p.loop_indices]
        edges=[vv[(i+1)%len(vv)]-vv[i] for i in range(len(vv))]
        u=max(edges,key=lambda v:v.length).normalized();normal=p.normal.normalized();v=normal.cross(u).normalized()
        xy=[(pt.dot(u)*density,pt.dot(v)*density) for pt in vv]
        xmin=min(a for a,b in xy);ymin=min(b for a,b in xy)
        xy=[(a-xmin,b-ymin) for a,b in xy]
        charts.append({'loops':list(p.loop_indices),'xy':xy,'w':max(a for a,b in xy),'h':max(b for a,b in xy),'area':p.area})
    area=sum((c['w']+16)*(c['h']+16) for c in charts)
    side=2**math.ceil(math.log2(max(512,math.sqrt(area)*1.3)))
    while True:
        pad=max(8,side/1024+1);x=y=pad;row=0;ok=True
        for c in sorted(charts,key=lambda c:c['h'],reverse=True):
            if x+c['w']+pad>side:x=pad;y+=row+pad*2;row=0
            if y+c['h']+pad>side:ok=False;break
            c['origin']=(x,y);x+=c['w']+pad*2;row=max(row,c['h'])
        if ok:break
        side*=2
    for c in charts:
        x,y=c['origin']
        for li,(a,b) in zip(c['loops'],c['xy']):uv.data[li].uv=((x+a)/side,(y+b)/side)
    # Projection is an isometry for planar Blender faces; report measured area ratios.
    ds=[]
    for c in charts:
        pts=c['xy'];ar=abs(sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts))))*.5
        if c['area']>1e-8 and ar>1e-8:ds.append(math.sqrt(ar/c['area']))
    return {'kind':'unique planar face charts, shelf packed','atlas_pixels':side,'target_px_per_m':density,'measured_min':min(ds),'measured_max':max(ds),'charts':len(charts),'padding_each_side_px':pad,'overlap':'nonoverlapping bounding rectangles','uv_bounds':[0,1],'material_tile_pixels':512,'uv_to_texture_scale':side/512}

manifest={'authored_at_utc':datetime.now(timezone.utc).isoformat(),'started_at_utc':START,'theme':'HillsideOnsen','effort':'ultra','bounds_m':[-50,50,-50,50], 'meshes':[], 'semantic_objects':SEMANTICS,'route':ROUTE,'stairs':stairs,'pools':POOLS,
 'coordinate_policy':'Blender meters; FBX global_scale=1, axis_forward=Y, up=Z; importer convert_scene=False, convert_scene_unit=True converts meters to cm; actor scale(1,-1,1) corrects handedness',
 'runtime_routes':[{'name':'arrival_flat','points':[ROUTE[0],(-13,-39.5,2.6)]},{'name':'lower_switchback','points':[(-24,-23.2,2.8618),(-5,-19.4,4.10545)]},{'name':'upper_switchback','points':[(24,5.3393,6.5482),(9,9.3571,7.59286)]}],
 'camera_views':{'overview':{'location':[-89,-110,83],'target':[0,0,8],'fov':48},'top_down':{'location':[0,-2,195],'target':[0,0,7],'fov':60},'hot_spring':{'location':[-28,-25,18],'target':[-4,2,7],'fov':53},'village_path':{'location':[25,-22,9.0],'target':[-5,-2,9],'fov':63}}}

for cat,(verts,faces) in G.items():
    me=bpy.data.meshes.new('SM_'+cat);me.from_pydata(verts,[],faces);me.update()
    obj=bpy.data.objects.new('SM_'+cat,me);bpy.context.collection.objects.link(obj)
    uv=pack_uv(obj,PALETTE[cat][2])
    # Triangulate explicitly after chart assignment so validation and import use identical faces.
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
    for p in me.polygons:p.use_smooth=cat in ['Terrain','BathStone','Leaves','LeavesLight','Water','Stream','Trunks']
    mat=bpy.data.materials.new('Preview_'+cat);mat.diffuse_color=(*PALETTE[cat][1],1);me.materials.append(mat)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    path=A/(obj.name+'.fbx')
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,axis_forward='Y',axis_up='Z',add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=True,mesh_smooth_type='FACE')
    bounds=[[min(v[i] for v in verts),max(v[i] for v in verts)] for i in range(3)]
    manifest['meshes'].append({'name':obj.name,'category':cat,'fbx':str(path),'vertices':len(me.vertices),'triangles':len(me.polygons),'bounds_m':bounds,'texture':PALETTE[cat][0],'color':PALETTE[cat][1],'uv':uv,'collision':cat not in ['Water','Stream','Steam','Glass','Foam','Leaves','LeavesLight','Fabric']})

bpy.ops.wm.save_as_mainfile(filepath=str(A/'SansolSprings.blend'))
manifest['finished_at_utc']=datetime.now(timezone.utc).isoformat()
(W/'scene_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
(W/'uv_source_validation.json').write_text(json.dumps({'meshes':{m['name']:m['uv'] for m in manifest['meshes']},'measurement':'sqrt(projected chart pixel area / source face m2); density assessed before triangulation; all chart rectangles shelf-packed without overlap','limitations':['Steam full-card UVs intentionally overlap','Tiling material sample repeats within unique chart atlas; textures are not unique baked artwork per island','Density at curved surfaces is piecewise planar']},indent=2),encoding='utf-8')
print('AUTHOR_COMPLETE',len(manifest['meshes']),sum(m['triangles'] for m in manifest['meshes']))
