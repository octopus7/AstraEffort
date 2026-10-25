"""Original WindmillFarm geometry. Run only in a separate Blender background process."""
import bpy, math, random, json
from mathutils import Vector, Matrix
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Source/Models'
OUT.mkdir(parents=True,exist_ok=True)
random.seed(23076)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=1.0

# Base colors are sRGB. UE conversion is performed explicitly during material authoring.
PALETTE={
 'Grass':('#80974b','Grass',.92), 'GrassLight':('#9ca75e','Grass',.9), 'GrassDark':('#647d44','Grass',.95),
 'Earth':('#92704c','Earth',.96), 'Soil':('#67503c','Earth',.95), 'Path':('#c9aa72','Earth',.91),
 'Stone':('#9b9e8b','Stone',.86), 'StoneLight':('#bab9a0','Stone',.85), 'Plaster':('#eee1bd','Plaster',.85),
 'Wood':('#775039','Wood',.82), 'WoodLight':('#b28a5a','Wood',.78), 'WoodDark':('#493c30','Wood',.88),
 'BarnRed':('#aa5941','Wood',.85), 'Terracotta':('#c57850','Clay',.82), 'TileLight':('#dd986a','Clay',.78),
 'Slate':('#50767a','Stone',.76), 'SlateLight':('#6b9190','Stone',.76), 'Trim':('#efe7cc','Plaster',.8),
 'Glass':('#254c54','',.2), 'WarmGlass':('#e6bc69','',.38), 'Iron':('#3f4842','',.48),
 'Wheat':('#d8b254','Straw',.88), 'WheatLight':('#efcf77','Straw',.86), 'WheatDark':('#b48f3f','Straw',.9),
 'Leaf':('#567d46','Grass',.9), 'LeafLight':('#78934e','Grass',.9), 'LeafDark':('#3d6542','Grass',.94),
 'Apple':('#bd5e43','',.65), 'Pumpkin':('#d88a3d','',.8), 'FlowerRed':('#cb6252','',.8),
 'FlowerBlue':('#8d9abb','',.8), 'FlowerCream':('#f1dfa4','',.8), 'Canvas':('#f4e4b7','Canvas',.95),
 'RotorWood':('#896241','Wood',.8), 'RotorIron':('#454a43','',.48), 'RotorCanvas':('#f4e4b7','Canvas',.95), 'Water':('#6b9b9a','',.27)
}
MAT={}
for name,(hexcolor,texture,roughness) in PALETTE.items():
    mat=bpy.data.materials.new(name)
    rgb=tuple(int(hexcolor[i:i+2],16)/255 for i in (1,3,5))
    mat.diffuse_color=(*rgb,1)
    MAT[name]=mat

class Mesh:
    def __init__(self,name,category,bevel=0):
        self.name=name;self.category=category;self.bevel=bevel
        self.v=[];self.f=[];self.m=[];self.s=[]
    def add(self,vs,fs,mat,smooth=False):
        offset=len(self.v);self.v.extend([tuple(v) for v in vs])
        self.f.extend([tuple(offset+i for i in f) for f in fs]);self.m.extend([mat]*len(fs));self.s.extend([smooth]*len(fs))
    def box(self,c,size,mat,rot=0):
        sx,sy,sz=[q/2 for q in size];ca,sa=math.cos(rot),math.sin(rot)
        vs=[]
        for z in [-sz,sz]:
            for x,y in [(-sx,-sy),(sx,-sy),(sx,sy),(-sx,sy)]:
                vs.append((c[0]+x*ca-y*sa,c[1]+x*sa+y*ca,c[2]+z))
        self.add(vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
    def beam(self,a,b,width,mat,depth=None):
        a,b=Vector(a),Vector(b);d=(b-a).normalized()
        q=Vector((0,0,1)) if abs(d.z)<.95 else Vector((1,0,0))
        u=d.cross(q).normalized()*width/2;v=d.cross(u).normalized()*(depth or width)/2
        vs=[p+u*su+v*sv for p in [a,b] for su,sv in [(-1,-1),(1,-1),(1,1),(-1,1)]]
        self.add(vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
    def cone(self,c,r0,r1,height,mat,n=12,smooth=True):
        vs=[(c[0]+r*math.cos(i*math.tau/n),c[1]+r*math.sin(i*math.tau/n),c[2]+z) for z,r in [(0,r0),(height,r1)] for i in range(n)]
        fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        self.add(vs,fs,mat,smooth)
    def tube(self,a,b,r,mat,n=8):
        a,b=Vector(a),Vector(b);d=(b-a).normalized();q=Vector((0,0,1)) if abs(d.z)<.9 else Vector((1,0,0))
        u=d.cross(q).normalized();v=d.cross(u).normalized()
        vs=[p+r*(math.cos(i*math.tau/n)*u+math.sin(i*math.tau/n)*v) for p in [a,b] for i in range(n)]
        self.add(vs,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat,True)
    def ellipsoid(self,c,s,mat,n=10,rings=6,rough=0):
        vs=[]
        for j in range(rings+1):
            phi=math.pi*j/rings
            for i in range(n):
                theta=math.tau*i/n
                wobble=1+rough*math.sin(3*theta+1.7*j)*math.sin(phi)
                vs.append((c[0]+s[0]*math.sin(phi)*math.cos(theta)*wobble,c[1]+s[1]*math.sin(phi)*math.sin(theta)*wobble,c[2]+s[2]*math.cos(phi)))
        fs=[]
        for j in range(rings):
            for i in range(n):
                q=(i+1)%n
                if j==0:fs.append((j*n+i,(j+1)*n+i,(j+1)*n+q))
                elif j==rings-1:fs.append((j*n+i,(j+1)*n+i,j*n+q))
                else:fs.append((j*n+i,(j+1)*n+i,(j+1)*n+q,j*n+q))
        self.add(vs,fs,mat,True)
    def torus(self,c,major,minor,mat,n=24,k=6,axis='Z'):
        vs=[]
        for i in range(n):
            a=i*math.tau/n
            for j in range(k):
                b=j*math.tau/k;q=((major+minor*math.cos(b))*math.cos(a),(major+minor*math.cos(b))*math.sin(a),minor*math.sin(b))
                if axis=='Y':q=(q[0],q[2],q[1])
                vs.append(tuple(c[t]+q[t] for t in range(3)))
        fs=[(i*k+j,((i+1)%n)*k+j,((i+1)%n)*k+(j+1)%k,i*k+(j+1)%k) for i in range(n) for j in range(k)]
        if axis=='Y':fs=[tuple(reversed(f)) for f in fs]
        self.add(vs,fs,mat,True)

def ground(x,y):
    return .14+.1*math.sin(x*.13)*math.cos(y*.12)+2.4*max(0,(y-29)/21)**2*(.65+.35*math.sin(x*.12)**2)

meshes=[]
def group(name,category,bevel=0):
    m=Mesh(name,category,bevel);meshes.append(m);return m

# Rounded square terrain, with a visible earth section and soft perimeter.
terrain=group('SM_Terrain','Terrain')
def perimeter(half,r=5,steps=12):
    pts=[]
    for cx,cy,start in [(half-r,half-r,0),(-half+r,half-r,90),(-half+r,-half+r,180),(half-r,-half+r,270)]:
        for i in range(steps):
            a=math.radians(start+i*90/steps)
            pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    dense=[]
    for i,a in enumerate(pts):
        b=pts[(i+1)%len(pts)]
        count=max(1,math.ceil(math.dist(a,b)/1.5))
        dense.extend([(a[0]+(b[0]-a[0])*j/count,a[1]+(b[1]-a[1])*j/count) for j in range(count)])
    return dense
edge=perimeter(50);N=len(edge)
for scale,z,mat in [(1,-1.7,'Earth'),(.998,-.7,'Earth'),(.996,-.08,'GrassDark')]:
    terrain.add([(x*scale,y*scale,z) for x,y in edge]+[(x*scale,y*scale,z+.65) for x,y in edge],[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)],mat)
terrain.add([(x,y,-1.7) for x,y in edge],[tuple(reversed(range(N)))],'Earth')
vs=[(0,0,ground(0,0))]
for ring in range(1,61):
    scale=ring/60
    vs.extend([(x*scale,y*scale,ground(x*scale,y*scale)) for x,y in edge])
fs=[(0,1+i,1+(i+1)%N) for i in range(N)]
for j in range(59):
    a=1+j*N;b=a+N
    fs.extend([(a+i,b+i,b+(i+1)%N,a+(i+1)%N) for i in range(N)])
terrain.add(vs,fs,'Grass',True)

paths=group('SM_Paths','Paths')
def ribbon(points,width,mat='Path'):
    # Catmull-Rom spline makes smoothly connected farm tracks.
    p=[Vector((x,y,0)) for x,y in points];p=[p[0]]+p+[p[-1]]
    samples=[]
    for i in range(1,len(p)-2):
        for k in range(14):
            t=k/14
            q=.5*((2*p[i])+(-p[i-1]+p[i+1])*t+(2*p[i-1]-5*p[i]+4*p[i+1]-p[i+2])*t*t+(-p[i-1]+3*p[i]-3*p[i+1]+p[i+2])*t*t*t)
            samples.append(q)
    samples.append(p[-2]);vs=[]
    for i,q in enumerate(samples):
        d=(samples[min(i+1,len(samples)-1)]-samples[max(0,i-1)]).normalized();n=Vector((-d.y,d.x,0))
        for side in [-1,1]:
            v=q+n*side*width/2;vs.append((v.x,v.y,ground(v.x,v.y)+.04))
    paths.add(vs,[(2*i,2*i+2,2*i+3,2*i+1) for i in range(len(samples)-1)],mat)
ribbon([(0,-49),(-1,-36),(0,-23),(-4,-9),(-9,1),(-16,12),(-23,17)],4.0)
ribbon([(-8,1),(2,5),(14,7),(26,10),(34,17)],3.5)
ribbon([(0,-24),(15,-19),(30,-12),(36,0),(34,18)],2.4)
ribbon([(-24,16),(-23,26),(-10,31),(5,29),(19,24),(30,18)],2.3)

mill=group('SM_WindmillTower','WindmillTower',.045)
mx,my=-23,17;mz=ground(mx,my)
mill.cone((mx,my,mz),5.0,4.8,.55,'Stone',16)
mill.cone((mx,my,mz+.55),3.8,2.45,11.5,'Plaster',12)
mill.cone((mx,my,mz+.6),3.83,3.55,2.0,'Stone',12)
# Individual masonry blocks at the base and pale horizontal courses.
for row in range(4):
    for i in range(20):
        a=(i+(row%2)*.5)*math.tau/20;r=3.84-row*.045
        mill.box((mx+r*math.cos(a),my+r*math.sin(a),mz+.85+row*.43),(.94,.12,.34),'StoneLight' if (i+row)%4==0 else 'Stone',a+math.pi/2)
for z,r in [(2.65,3.62),(6.3,3.2),(10.8,2.65)]:mill.cone((mx,my,mz+z),r,r,.14,'Trim',12)
# Timber octagonal upper faces, visible framing and small windows.
for i in range(8):
    a=i*math.tau/8
    mill.beam((mx+3.48*math.cos(a),my+3.48*math.sin(a),mz+3),(mx+2.6*math.cos(a),my+2.6*math.sin(a),mz+11.5),.18,'WoodDark')
for x,z in [(-1.2,4.5),(1.2,7.8),(-1,9.6)]:
    yy=my-math.sqrt(max(1,(3.7-.1*z)**2-x*x))-.03
    mill.box((mx+x,yy,mz+z),(.68,.13,1.03),'WoodDark')
    mill.box((mx+x,yy-.08,mz+z),(.48,.06,.8),'Glass')
    mill.box((mx+x,yy-.13,mz+z),(.07,.06,.8),'Trim')
    mill.box((mx+x,yy-.13,mz+z),(.5,.06,.07),'Trim')
mill.box((mx,my-3.8,mz+1.2),(1.5,.22,2.25),'WoodDark')
for i in range(7):mill.box((mx-.61+i*.2,my-3.94,mz+1.2),(.17,.1,2.0),'Wood')
mill.box((mx,my-4.04,mz+1.65),(1.35,.09,.12),'WoodLight')
mill.box((mx,my-4.04,mz+.7),(1.35,.09,.12),'WoodLight')
mill.ellipsoid((mx+.45,my-4.12,mz+1.1),(.08,.06,.08),'Iron',8,4)
# Gallery at 5.2 m and braces.
mill.cone((mx,my,mz+5.05),5.1,5.1,.24,'Wood',24)
for i in range(32):
    a=i*math.tau/32
    mill.box((mx+4.15*math.cos(a),my+4.15*math.sin(a),mz+5.32),(.65,1.8,.12),'WoodLight',a+math.pi/2)
for i in range(24):
    a=i*math.tau/24;b=(i+1)*math.tau/24
    p=(mx+4.92*math.cos(a),my+4.92*math.sin(a),mz+5.38)
    mill.beam(p,(p[0],p[1],mz+6.4),.13,'WoodDark')
    for z in [5.68,6.36]:mill.beam((p[0],p[1],mz+z),(mx+4.92*math.cos(b),my+4.92*math.sin(b),mz+z),.13,'Wood')
    if i%3==0:mill.beam((mx+3.3*math.cos(a),my+3.3*math.sin(a),mz+3.3),(p[0],p[1],mz+5.12),.23,'WoodDark')
# Steep blue cap, overlapped scalloped shingle bands and finial.
mill.cone((mx,my,mz+11.9),3.35,.3,4.1,'Slate',16)
for row in range(6):
    z=12+row*.58;r=3.4-row*.44
    for i in range(24):
        a=(i+(row%2)*.5)*math.tau/24
        mill.ellipsoid((mx+r*math.cos(a),my+r*math.sin(a),mz+z),(.35,.35,.12),'SlateLight' if (i+row)%5==0 else 'Slate',8,4)
mill.cone((mx,my,mz+15.9),.22,.06,1.0,'Iron',10)
mill.ellipsoid((mx,my,mz+16.75),(.25,.25,.25),'WoodLight',12,6)

rotor=group('SM_WindmillRotor','WindmillRotor',.025)
rotor_pivot=(mx,my-6.0,mz+11.15)
rotor.tube((0,-.35,0),(0,3.5,0),.34,'RotorIron',12)
rotor.ellipsoid((0,-.45,0),(.48,.28,.48),'RotorWood',12,6)
def rotor_pt(x,z,a,y=0):return (x*math.cos(a)+z*math.sin(a),y,-x*math.sin(a)+z*math.cos(a))
for k in range(4):
    a=math.pi/4+k*math.pi/2
    rotor.beam(rotor_pt(0,.2,a),rotor_pt(0,7.4,a),.2,'RotorWood',.24)
    for side in [.08,1.48]:rotor.beam(rotor_pt(side,1.8,a),rotor_pt(side,7.2,a),.1,'RotorWood')
    for i in range(11):
        z=1.8+i*.54
        rotor.beam(rotor_pt(-.16,z,a,-.035),rotor_pt(1.56,z,a,-.035),.095,'RotorWood')
    # Canvas panels with gaps retain the visible timber lattice.
    for j in range(8):
        z=2.7+j*.52
        verts=[rotor_pt(x,zz,a,.04) for x,zz in [(.14,z),(1.4,z), (1.4,z+.44),(.14,z+.44)]]
        rotor.add(verts,[(0,1,2,3),(3,2,1,0)],'RotorCanvas')
rotor.torus((0,-.5,0),.48,.065,'RotorIron',20,6,'Y')

house=group('SM_Farmhouse','Farmhouse',.055)
barn=group('SM_Barn','Barn',.04)
def building(m,c,size,wall,roof):
    x,y=c;w,d,height=size;z=ground(x,y)
    m.box((x,y,z+.26),(w+.5,d+.5,.52),'Stone')
    m.box((x,y,z+height/2+.5),(w,d,height),wall)
    # Gabled end walls and thick roof planes.
    peak=height+.5+w*.34;eave=height+.5
    m.add([(x-w/2,y-d/2,z+eave),(x+w/2,y-d/2,z+eave),(x,y-d/2,z+peak),(x-w/2,y+d/2,z+eave),(x+w/2,y+d/2,z+eave),(x,y+d/2,z+peak)],[(0,1,2),(5,4,3)],wall)
    for side in [-1,1]:
        vs=[(x,y-d/2-.6,z+peak+.15),(x+side*(w/2+.65),y-d/2-.6,z+eave-.05),(x+side*(w/2+.65),y+d/2+.6,z+eave-.05),(x,y+d/2+.6,z+peak+.15)]
        m.add(vs,[(0,1,2,3),(3,2,1,0)],roof)
        for j in range(8):
            t=(j+.5)/8
            for k in range(round(d/.62)+2):
                yy=y-d/2-.4+k*.62+(j%2)*.15
                if yy>y+d/2+.5:continue
                xx=x+side*(w/2+.55)*t;zz=z+peak+.17-(peak-eave+.2)*t
                m.ellipsoid((xx,yy,zz),(.38,.36,.065),('TileLight' if (j+k)%7==0 else roof) if roof=='Terracotta' else ('SlateLight' if (j+k)%7==0 else roof),8,4)
    m.beam((x,y-d/2-.67,z+peak+.2),(x,y+d/2+.67,z+peak+.2),.24,roof)
    for yy in [y-d/2-.63,y+d/2+.63]:
        for side in [-1,1]:m.beam((x,yy,z+peak+.16),(x+side*(w/2+.68),yy,z+eave-.1),.21,'Trim' if wall=='Plaster' else 'WoodDark')
    return z,eave,peak

hx,hy=23,18;hz,he,hp=building(house,(hx,hy),(10.5,13,4.2),'Plaster','Terracotta')
building(house,(hx+7.2,hy+1),(5.5,9,3.1),'Plaster','Terracotta')
# Exposed corner timbers, shutters, mullions and flower boxes.
for x in [hx-5.2,hx+5.2]:
    for y in [hy-6.4,hy+6.4]:house.box((x,y,hz+2.6),(.25,.25,4.4),'WoodDark')
def window(m,x,y,z,w=1.4,h=1.6):
    m.box((x,y,z),(w+.25,.18,h+.25),'Trim');m.box((x,y-.12,z),(w,.09,h),'Glass')
    m.box((x,y-.19,z),(.08,.08,h),'Trim');m.box((x,y-.19,z),(w,.08,.08),'Trim')
    for s in [-1,1]:
        m.box((x+s*(w/2+.43),y-.06,z),(.52,.13,h+.14),'Slate')
        for j in range(5):m.box((x+s*(w/2+.43),y-.145,z-h/2+.16+j*h/5),(.43,.045,.055),'SlateLight')
    m.box((x,y-.27,z-h/2-.12),(w+.4,.45,.19),'WoodLight')
for x in [hx-3.1,hx+3.1]:window(house,x,hy-6.57,hz+2.8)
window(house,hx,hy-6.57,hz+6.2,1.1,1.2)
house.box((hx,hy-6.6,hz+1.6),(1.65,.25,2.6),'WoodDark')
house.box((hx,hy-6.78,hz+1.6),(1.4,.12,2.35),'Slate')
house.box((hx,hy-6.87,hz+2.05),(1.1,.05,.9),'WarmGlass')
house.box((hx,hy-7.6,hz+.2),(4,2.3,.4),'StoneLight')
for x in [hx-2,hx+2]:house.beam((x,hy-8.5,hz+.4),(x,hy-8.5,hz+3.4),.16,'Wood')
house.box((hx,hy-7.75,hz+3.35),(4.6,2.9,.18),'Terracotta')
# Chimney with cap and varied courses.
house.box((hx+2.7,hy+3.2,hz+7.3),(1.0,1.1,3.0),'Plaster')
house.box((hx+2.7,hy+3.2,hz+8.86),(1.2,1.28,.23),'Terracotta')
for yy in [hy+2.95,hy+3.48]:house.cone((hx+2.7,yy,hz+8.95),.22,.2,.45,'Terracotta',10)

bx,by=33,0;bz,be,bp=building(barn,(bx,by),(10,12,4.8),'BarnRed','Slate')
for side in [-1,1]:
    for i in range(20):
        xx=bx-4.75+i*.5
        barn.box((xx,by+side*6.03,bz+2.9),(.07,.09,4.6),'WoodLight' if i%5==0 else 'Wood')
barn.box((bx,by-6.15,bz+2.5),(4.7,.2,4.3),'WoodDark')
for i in range(10):barn.box((bx-2.12+i*.47,by-6.29,bz+2.5),(.42,.1,4.05),'Wood')
for side in [-1,1]:
    cx=bx+side*1.14
    barn.beam((cx-1.0,by-6.4,bz+.55),(cx+1.0,by-6.4,bz+4.35),.18,'WoodLight')
    barn.beam((cx+1.0,by-6.4,bz+.55),(cx-1.0,by-6.4,bz+4.35),.18,'WoodLight')
barn.box((bx,by-6.4,bz+4.65),(5.3,.2,.25),'Trim')
window(barn,bx,by-6.08,bz+6.1,1.15,1.0)

fields=[]
def field(name,x0,x1,y0,y1,harvest=False):
    m=group(name,'Wheat');fields.append((x0,x1,y0,y1))
    # Soil boundary follows the rolling surface.
    rows=round((y1-y0)/.7);cols=round((x1-x0)/.7)
    for j in range(rows):
        y=y0+(j+.5)*(y1-y0)/rows
        m.beam((x0,y,ground(x0,y)+.03),(x1,y,ground(x1,y)+.03),.22,'Soil',.08)
        for i in range(cols):
            x=x0+(i+.5)*(x1-x0)/cols+random.uniform(-.13,.13);yy=y+random.uniform(-.12,.12)
            if harvest and i>cols*.3:continue
            z=ground(x,yy);height=random.uniform(.68,1.05)
            for dx,dy in [(-.12,-.08),(.1,.09),(0,.17)]:
                top=(x+dx+.07,yy+dy,z+height)
                m.tube((x+dx,yy+dy,z+.04),top,.016,'WheatDark',4)
                m.ellipsoid((top[0],top[1],top[2]+.14),(.067,.065,.23),random.choice(['Wheat','WheatLight','Wheat']),6,4)
                for s in [-1,1]:
                    m.add([(x+dx,yy+dy,z+height*.5),(x+dx+s*.22,yy+dy+.035,z+height*.75),(x+dx+s*.05,yy+dy+.05,z+height*.44)],[(0,1,2),(2,1,0)],'Wheat')
    return m
field('SM_Wheat_West',-41,-13,-36,-7)
field('SM_Wheat_East',7,28,-39,-23)
field('SM_Harvest',-39,-14,27,37,True)

fences=group('SM_Fences','Fences',.035)
def fence(points,step=2.8):
    for a,b in zip(points,points[1:]):
        a=Vector(a);b=Vector(b);d=b-a;n=max(1,round(d.length/step));prev=None
        for i in range(n+1):
            p=a+d*i/n;z=ground(p.x,p.y)
            fences.box((p.x,p.y,z+.72),(.18,.18,1.45),'Wood')
            fences.cone((p.x,p.y,z+1.445),.13,0,.12,'WoodLight',4)
            if prev:
                for h in [.5,1.12]:fences.beam((prev.x,prev.y,ground(prev.x,prev.y)+h),(p.x,p.y,z+h),.12,'WoodLight')
            prev=p
fence([(-43,-38),(-43,-4),(-13,-4),(-11,-20)])
fence([(-43,-38),(-13,-38),(-11,-31)])
fence([(5,-41),(30,-41),(30,-23)])
fence([(7,-21),(21,-21)])
fence([(-43,25),(-43,40),(-12,40),(-12,29)])
fence([(40,-17),(44,1),(43,28),(36,37),(12,39)])
# Welcoming gate at the approach.
for x in [-3.2,3.2]:
    fences.box((x,-44,ground(x,-44)+1.05),(.35,.35,2.1),'WoodDark')
    fences.ellipsoid((x,-44,ground(x,-44)+2.18),(.25,.25,.2),'WoodLight',10,5)
fences.beam((-3.2,-44,2.1),(-7,-43,2.1),.16,'WoodLight')
fences.beam((3.2,-44,2.1),(7,-43,2.1),.16,'WoodLight')

orchard=group('SM_Orchard','Orchard')
trees=group('SM_BoundaryTrees','Orchard')
def tree(m,x,y,s=1,fruit=False):
    z=ground(x,y)
    m.cone((x,y,z),.28*s,.12*s,2.7*s,'Wood',9)
    for a in [.4,2.5,4.4]:
        end=(x+math.cos(a)*1.1*s,y+math.sin(a)*1.1*s,z+3.3*s)
        m.tube((x,y,z+1.8*s),end,.13*s,'Wood',7)
    for dx,dy,dz,ss in [(-.85,0,3.4,1.45),(.8,.1,3.7,1.5),(0,.8,4.3,1.4),(0,-.65,4.4,1.35),(.15,.05,5.0,1.2)]:
        m.ellipsoid((x+dx*s,y+dy*s,z+dz*s),(ss*s,ss*.92*s,ss*.9*s),random.choice(['Leaf','LeafLight','LeafDark']),12,8,.06)
    if fruit:
        for i in range(16):
            a=random.random()*math.tau;r=random.uniform(.8,1.55)*s
            m.ellipsoid((x+r*math.cos(a),y+r*math.sin(a),z+random.uniform(2.8,4.4)*s),(.12*s,.12*s,.13*s),'Apple',8,5)
for x,y in [(4,18),(4,26),(10,21),(11,30),(1,34)]:tree(orchard,x,y,1.0,True)
for x,y,s in [(-44,16,1.45),(-43,5,1.2),(-41,43,1.2),(-29,44,1.1),(-4,44,1.4),(15,43,1.2),(39,40,1.35),(45,19,1.3),(45,-9,1.2),(-47,-26,.8)]:tree(trees,x,y,s)

props=group('SM_FarmProps','Props',.03)
garden=group('SM_KitchenGarden','Props')
# Stone well, timber roof, spindle, and pail.
wx,wy=10,4;wz=ground(wx,wy)
props.cone((wx,wy,wz),1.0,1.0,1.1,'Stone',16)
props.cone((wx,wy,wz+1.08),.78,.78,.03,'Water',16)
props.torus((wx,wy,wz+1.15),.98,.16,'StoneLight',24,8)
for x in [wx-1.15,wx+1.15]:props.beam((x,wy,wz),(x,wy,wz+3),.19,'Wood')
props.tube((wx-1.2,wy,wz+2.0),(wx+1.2,wy,wz+2.0),.13,'WoodDark')
props.tube((wx,wy,wz+2),(wx,wy,wz+.9),.025,'WoodLight',6)
for side in [-1,1]:props.add([(wx-1.5,wy,wz+3.5),(wx+1.5,wy,wz+3.5),(wx+1.5,wy+side*1.4,wz+2.9),(wx-1.5,wy+side*1.4,wz+2.9)],[(0,1,2,3),(3,2,1,0)],'Slate')

def barrel(x,y,s=1):
    z=ground(x,y);props.cone((x,y,z),.42*s,.5*s,.6*s,'Wood',12);props.cone((x,y,z+.6*s),.5*s,.4*s,.6*s,'WoodLight',12)
    for h,r in [(.15,.45),(.6,.51),(1.05,.45)]:props.torus((x,y,z+h*s),r*s,.045*s,'Iron',16,5)
    props.cone((x,y,z+1.2*s),.4*s,.4*s,.04*s,'Wood',12)
for x,y,s in [(17,10,1),(16.3,11,.85),(38,-7,1),(39,-6,.9),(-19,11,.8)]:barrel(x,y,s)

def bale(x,y,r=.8):
    z=ground(x,y)
    props.tube((x,y-.65,z+r),(x,y+.65,z+r),r,'Wheat',16)
    for yy in [y-.45,y+.45]:props.torus((x,yy,z+r),r+.015,.045,'WoodDark',20,5,'Y')
    for yy in [y-.67,y+.67]:
        for rr in [.2,.4,.6]:props.torus((x,yy,z+r),rr,.018,'WheatDark',20,4,'Y')
for x,y in [(-29,33),(-22,31),(-35,30),(29,-15),(32,-16)]:bale(x,y)

# Farm cart with spoked wooden wheels and a stack of sacks.
cx,cy=18,-2;cz=ground(cx,cy)
props.box((cx,cy,cz+1.0),(2.3,3.5,.23),'WoodDark')
for i in range(9):props.box((cx,cy-1.5+i*.36,cz+1.15),(2.2,.32,.12),'WoodLight')
for side in [-1,1]:
    for h in [1.42,1.8]:props.box((cx+side*1.15,cy,cz+h),(.12,3.5,.25),'Wood')
    for yy in [cy-1.2,cy+1.2]:
        # wheel planes parallel to YZ, made with spokes in that plane
        xx=cx+side*1.38
        for i in range(16):
            a=i*math.tau/16;b=(i+1)*math.tau/16
            props.tube((xx,yy+.72*math.cos(a),cz+.75+.72*math.sin(a)),(xx,yy+.72*math.cos(b),cz+.75+.72*math.sin(b)),.075,'WoodDark',6)
        for i in range(10):
            a=i*math.tau/10;props.beam((xx,yy,cz+.75),(xx,yy+.68*math.cos(a),cz+.75+.68*math.sin(a)),.075,'WoodLight')
    props.beam((cx+side*.7,cy-1.5,cz+1),(cx+side*.5,cy-4.2,cz+.6),.13,'Wood')
for x,y in [(cx-.5,cy-.8),(cx+.4,cy),(cx-.4,cy+.8)]:props.ellipsoid((x,y,cz+1.7),(.52,.6,.6),'Canvas',10,7)

# Garden beds, cabbage rosettes, pumpkins and trellises near the house.
for i in range(4):
    gx=34+i*2.1;gy=26;gz=ground(gx,gy)
    garden.box((gx,gy,gz+.17),(1.65,7,.34),'Soil')
    for sx in [-.9,.9]:garden.box((gx+sx,gy,gz+.2),(.15,7.2,.35),'Wood')
    for yy in [gy-3.5,gy+3.5]:garden.box((gx,yy,gz+.2),(1.8,.15,.35),'Wood')
    for j in range(8):
        yy=gy-3+j*.8
        if i%2==0:
            for a in range(6):
                t=a*math.tau/6;garden.ellipsoid((gx+.19*math.cos(t),yy+.19*math.sin(t),gz+.43),(.31,.29,.18),'LeafLight' if a%2 else 'Leaf',8,5)
        else:
            garden.ellipsoid((gx,yy,gz+.48),(.33,.34,.29),'Pumpkin',10,6)
            garden.cone((gx,yy,gz+.73),.045,.035,.12,'Wood',6)

# A practical firewood stack beside the barn.
for row in range(4):
    for k in range(7-row):
        x=39.3+k*.25+row*.12;y=2.0;z=ground(x,y)+.2+row*.3
        props.tube((x,y-1,z),(x,y+1,z),.16,'Wood',9)
        props.tube((x,y-1.02,z),(x,y-.99,z),.13,'WoodLight',9)
# Stepping stones around doors.
stones=group('SM_Stones','Props')
for x,y in [(23,9),(23,7.8),(23,6.6),(-23,12),(-23,10.7),(-23,9.5),(33,-7.5),(33,-8.8)]:
    stones.ellipsoid((x,y,ground(x,y)+.1),(.65,.46,.15),'StoneLight',10,5,.08)
for i in range(45):
    a=random.random()*math.tau;x=46*math.cos(a);y=44*math.sin(a)
    stones.ellipsoid((x,y,ground(x,y)+.16),(.35+random.random()*.5,.35+random.random()*.4,.2+random.random()*.25),'Stone',9,5,.12)

flora=group('SM_Wildflowers','Props')
def tuft(x,y,s=1,flower=False):
    z=ground(x,y)
    for k in range(5):
        a=k*2.4;dx=math.cos(a)*.25*s;dy=math.sin(a)*.25*s
        flora.add([(x-.025,y,z),(x+dx,y+dy,z+.38*s),(x+.025,y,z)],[(0,1,2),(2,1,0)],'GrassDark' if k%2 else 'LeafLight')
    if flower:
        top=z+.6*s;flora.tube((x,y,z),(x,y,top),.012,'Leaf',4)
        mat=random.choice(['FlowerRed','FlowerBlue','FlowerCream'])
        for k in range(5):
            a=k*math.tau/5;flora.ellipsoid((x+.08*s*math.cos(a),y+.08*s*math.sin(a),top),(.09*s,.09*s,.035*s),mat,6,3)
for i in range(650):
    x=random.uniform(-47,47);y=random.uniform(-46,45)
    if any(a-1<x<b+1 and c-1<y<d+1 for a,b,c,d in fields):continue
    if (-30<x<-16 and 9<y<25) or (16<x<43 and -8<y<32):continue
    # Keep the main path visibly clear.
    if abs(x)<4 and y<0:continue
    tuft(x,y,random.uniform(.7,1.3),random.random()<.3)
for x in [hx-3.1,hx+3.1]:
    for j in range(5):
        xx=x-.5+j*.25;yy=hy-6.9;zz=hz+1.85
        flora.ellipsoid((xx,yy,zz),(.15,.17,.12),'Leaf',8,4)
        flora.ellipsoid((xx,yy-.04,zz+.13),(.1,.1,.06),'FlowerRed',8,4)

manifest={'site_dimensions_m':[100,100],'created_at_utc':datetime.now(timezone.utc).isoformat(),'coordinate_units':'meters in Blender; FBX applies its built-in x100 centimeter transform once; global_scale=1',
 'rotor_pivot_m':rotor_pivot,'rotor_axis':[0,1,0],'meshes':[],'palette':{n:{'srgb_hex':p[0],'texture':p[1]+'.png' if p[1] else None,'roughness':p[2]} for n,p in PALETTE.items()},
 'textures':[p.name for p in sorted((ROOT/'Source/Textures').glob('*.png'))], 'seed':23076,
 'uv_policy':'Dominant-face planar UVs in meters divided by two. Repeating surface textures, intentional tiling/overlap. No unique bake atlas.'}

for m in meshes:
    data=bpy.data.meshes.new(m.name);data.from_pydata(m.v,[],m.f);data.update()
    ob=bpy.data.objects.new(m.name,data);bpy.context.collection.objects.link(ob)
    used=list(dict.fromkeys(m.m))
    for n in used:data.materials.append(MAT[n])
    for poly,n,smooth in zip(data.polygons,m.m,m.s):poly.material_index=used.index(n);poly.use_smooth=smooth
    uv=data.uv_layers.new(name='SurfaceUV')
    for poly in data.polygons:
        axis=max(range(3),key=lambda a:abs(poly.normal[a]));axes=[a for a in range(3) if a!=axis]
        for li in poly.loop_indices:
            co=data.vertices[data.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]]/2,co[axes[1]]/2)
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    if m.bevel:
        bevel=ob.modifiers.new('Soft crafted edges','BEVEL');bevel.width=m.bevel;bevel.segments=2;bevel.limit_method='ANGLE';bevel.angle_limit=.6
        bpy.ops.object.modifier_apply(modifier=bevel.name)
        normals=ob.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');normals.keep_sharp=True
        bpy.ops.object.modifier_apply(modifier=normals.name)
    data=ob.data
    bbox=[ob.matrix_world@Vector(c) for c in ob.bound_box]
    item={'name':m.name,'category':m.category,'vertices':len(data.vertices),'polygons':len(data.polygons),'loops':len(data.loops),'uv_loops':len(data.uv_layers.active.data),
      'bounds_min':[min(v[a] for v in bbox) for a in range(3)],'bounds_max':[max(v[a] for v in bbox) for a in range(3)],'materials':used}
    manifest['meshes'].append(item)
    bpy.ops.export_scene.fbx(filepath=str(OUT/(m.name+'.fbx')),use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=False,
      apply_scale_options='FBX_SCALE_NONE',axis_forward='Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,path_mode='STRIP')
    print('EXPORTED',m.name,len(data.vertices),flush=True)

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Source/WindmillFarm_max.blend'))
(ROOT/'Source/scene_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('SOURCE_COMPLETE',json.dumps({'meshes':len(meshes),'vertices':sum(x['vertices'] for x in manifest['meshes'])}),flush=True)
