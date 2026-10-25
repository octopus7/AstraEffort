import bpy, math, random, json, os, time, struct, zlib
from pathlib import Path
from mathutils import Vector, Matrix
from datetime import datetime, timezone
import numpy as np

ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/DesertVillage/max')
ART=ROOT/'SourceArt'; FBX=ART/'FBX'; TEX=ART/'Textures'
for p in (ART,FBX,TEX): p.mkdir(parents=True,exist_ok=True)
START=time.time(); random.seed(37191)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for unused in list(bpy.data.materials):
    if unused.users==0:bpy.data.materials.remove(unused)
scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1.0

def png(name, a):
    a=np.uint8(np.clip(a,0,255)); h,w=a.shape[:2]
    if a.shape[2]==3: a=np.dstack([a,np.full((h,w),255,dtype=np.uint8)])
    def chunk(t,d): return struct.pack('!I',len(d))+t+d+struct.pack('!I',zlib.crc32(t+d)&0xffffffff)
    raw=b''.join(b'\0'+a[y].tobytes() for y in range(h))
    (TEX/(name+'.png')).write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,6))+chunk(b'IEND',b''))

N=512; yy,xx=np.mgrid[0:N,0:N]; u=xx/N; v=yy/N; rng=np.random.default_rng(37191)
noise=rng.random((N,N)); fine=rng.random((N,N))
pl=239+2*np.sin((u+.08*np.sin(v*math.tau*3))*math.tau*7)+4*(noise-.5)+np.sin((u+v)*math.tau*17)
png('T_Plaster',np.dstack([pl,pl,pl]))
sand=230+7*np.sin((v+.018*np.sin(u*math.tau*3))*math.tau*18)+5*(noise-.5)
png('T_Sand',np.dstack([sand,sand,sand]))
wood=219+15*np.sin((u+.03*np.sin(v*math.tau*3))*math.tau*13)+8*np.sin(u*math.tau*47)+5*(noise-.5)
png('T_Wood',np.dstack([wood,wood,wood]))
weave=231+7*np.sin(u*math.tau*128)*np.sin(v*math.tau*128)+3*(noise-.5)
png('T_Weave',np.dstack([weave,weave,weave]))
stone=229+7*np.sin(u*math.tau*4)*np.cos(v*math.tau*6)+10*(noise-.5)
png('T_Stone',np.dstack([stone,stone,stone]))
water=0.5+0.25*np.sin((u+.07*np.sin(v*math.tau*3))*math.tau*6)+.15*np.cos((v+.05*np.sin(u*math.tau*2))*math.tau*9)
png('T_WaterRipples',np.dstack([water*255,water*255,water*255]))
dx=.22*np.cos((u+.07*np.sin(v*math.tau*3))*math.tau*6); dy=.18*np.sin((v+.05*np.sin(u*math.tau*2))*math.tau*9)
png('T_WaterNormal',np.dstack([(dx*.5+.5)*255,(dy*.5+.5)*255,np.sqrt(np.maximum(0,1-dx*dx-dy*dy))*255]))
for name,base,accent in [('T_Rug_Rust',(135,48,37),(240,189,105)),('T_Rug_Teal',(29,101,106),(239,199,127)),('T_Rug_Gold',(202,133,44),(80,68,58))]:
    a=np.zeros((N,N,3)); a[:]=base
    edge=np.minimum.reduce([u,v,1-u,1-v]); border=(edge>.04)&(edge<.11); a[border]=accent
    bands=(edge>.125)&(edge<.14); a[bands]=accent
    diamond=np.abs((u-.5)*2)+np.abs((v-.5)*1.4)
    a[(diamond<.53)&(diamond>.43)]=accent
    a[diamond<.20]=accent
    repeat=(np.abs(((u*8)%1)-.5)+np.abs(((v*12)%1)-.5))<.14
    a[repeat&(edge>.17)&(diamond>.6)]=accent
    a+=((noise-.5)*10+np.sin(u*math.tau*180)*2)[...,None]
    png(name,a)

MAT={}
def mat(name,color,texture=None,rough=.75,metal=0,uv=1.0,two=False):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=rough
    MAT[name]={'color':color,'texture':texture,'roughness':rough,'metallic':metal,'uv_meters_per_repeat':uv,'two_sided':two}; return name

mat('Sand',(0.78,.57,.31),'T_Sand',.9,uv=3)
mat('DuneLight',(.86,.66,.39),'T_Sand',.92,uv=3)
mat('Sandstone',(.72,.43,.24),'T_Stone',.82,uv=1.5)
mat('Limestone',(.88,.72,.47),'T_Stone',.8,uv=1.5)
mat('PlasterWarm',(.78,.48,.27),'T_Plaster',.88,uv=2)
mat('PlasterPeach',(.87,.59,.36),'T_Plaster',.87,uv=2)
mat('PlasterCream',(.9,.74,.5),'T_Plaster',.85,uv=2)
mat('PlasterRose',(.7,.35,.24),'T_Plaster',.86,uv=2)
mat('TrimCream',(.95,.79,.53),'T_Plaster',.85,uv=1)
mat('Recess',(.16,.13,.10),None,.95)
mat('Wood',(.34,.18,.085),'T_Wood',.85,uv=.7)
mat('WoodLight',(.58,.35,.16),'T_Wood',.88,uv=.7)
mat('DoorTeal',(.1,.33,.32),'T_Wood',.82,uv=.7)
mat('PalmTrunk',(.42,.27,.13),'T_Wood',.9,uv=.65)
mat('PalmLeaf',(.20,.37,.115),None,.8,two=True)
mat('PalmLeafLight',(.36,.48,.16),None,.82,two=True)
mat('ClothCream',(.95,.82,.58),'T_Weave',.9,uv=.5,two=True)
mat('ClothTerracotta',(.74,.25,.13),'T_Weave',.9,uv=.5,two=True)
mat('ClothTeal',(.10,.43,.43),'T_Weave',.9,uv=.5,two=True)
mat('ClothGold',(.94,.59,.20),'T_Weave',.9,uv=.5,two=True)
mat('RugRust',(1,1,1),'T_Rug_Rust',.95,uv=0,two=True)
mat('RugTeal',(1,1,1),'T_Rug_Teal',.95,uv=0,two=True)
mat('RugGold',(1,1,1),'T_Rug_Gold',.95,uv=0,two=True)
mat('Terracotta',(.64,.25,.13),'T_Stone',.8,uv=.7)
mat('CeramicTeal',(.075,.40,.41),None,.28)
mat('CeramicCream',(.9,.73,.45),None,.36)
mat('Basket',(.64,.42,.19),'T_Weave',.92,uv=.25)
mat('Metal',(.19,.16,.105),None,.5,.65)
mat('LanternGlass',(1,.65,.21),None,.32)
mat('Dates',(.25,.105,.045),None,.65)
mat('Orange',(.91,.39,.075),None,.62)
mat('Olive',(.34,.43,.10),None,.7)
mat('Water',(.035,.44,.48),'T_WaterRipples',.36,uv=6,two=True)
mat('WaterEdge',(.34,.72,.66),None,.42,two=True)
mat('Rock',(.68,.49,.29),'T_Stone',.86,uv=1)
mat('Reed',(.37,.44,.15),None,.85,two=True)

class Group:
    def __init__(self,name,bevel=0,smooth=False): self.name=name;self.v=[];self.f=[];self.mi=[];self.uv=[];self.mats=[];self.bevel=bevel;self.smooth=smooth
    def add(self,verts,faces,material,uv=None):
        off=len(self.v);self.v.extend(verts)
        if material not in self.mats:self.mats.append(material)
        idx=self.mats.index(material)
        for k,f in enumerate(faces):self.f.append(tuple(off+i for i in f));self.mi.append(idx);self.uv.append(uv[k] if uv else None)
    def finish(self):
        mesh=bpy.data.meshes.new(self.name);mesh.from_pydata(self.v,[],self.f);mesh.update();o=bpy.data.objects.new(self.name,mesh);scene.collection.objects.link(o)
        for m in self.mats:mesh.materials.append(bpy.data.materials[m])
        for p,i in zip(mesh.polygons,self.mi):p.material_index=i;p.use_smooth=self.smooth
        layer=mesh.uv_layers.new(name='UVMap')
        for p,special in zip(mesh.polygons,self.uv):
            normal=p.normal;axis=max(range(3),key=lambda i:abs(normal[i])); axes=([1,2],[0,2],[0,1])[axis];scale=MAT[self.mats[p.material_index]]['uv_meters_per_repeat'] or 1
            for j,li in enumerate(p.loop_indices):
                co=mesh.vertices[mesh.loops[li].vertex_index].co;layer.data[li].uv=special[j] if special else (co[axes[0]]/scale,co[axes[1]]/scale)
        bpy.context.view_layer.objects.active=o;o.select_set(True)
        if self.bevel:
            mod=o.modifiers.new('Soft handcrafted edges','BEVEL');mod.width=self.bevel;mod.segments=3;mod.limit_method='ANGLE';mod.angle_limit=.52
            bpy.ops.object.modifier_apply(modifier=mod.name)
        # Project AFTER beveling so newly-created edge faces also have nondegenerate UVs.
        mesh=o.data;mesh.update();layer=mesh.uv_layers.active
        for p in mesh.polygons:
            scale=MAT[mesh.materials[p.material_index].name]['uv_meters_per_repeat']
            if not scale:continue
            axis=max(range(3),key=lambda i:abs(p.normal[i]));axes=([1,2],[0,2],[0,1])[axis]
            for li in p.loop_indices:
                co=mesh.vertices[mesh.loops[li].vertex_index].co;layer.data[li].uv=(co[axes[0]]/scale,co[axes[1]]/scale)
        o.select_set(False);return o

G={}
def group(n,bevel=0,smooth=False):G[n]=Group(n,bevel,smooth);return G[n]
def box(g,c,s,m,rz=0):
    x,y,z=c;a,b,h=[i/2 for i in s];co=math.cos(rz);si=math.sin(rz)
    verts=[(x+vx*co-vy*si,y+vx*si+vy*co,z+vz) for vx,vy,vz in [(-a,-b,-h),(a,-b,-h),(a,b,-h),(-a,b,-h),(-a,-b,h),(a,-b,h),(a,b,h),(-a,b,h)]]
    g.add(verts,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],m)
def cyl(g,c,r,depth,m,n=16,r2=None):
    if r2 is None:r2=r
    x,y,z=c;verts=[(x+(r if k==0 else r2)*math.cos(i*math.tau/n),y+(r if k==0 else r2)*math.sin(i*math.tau/n),z+(-.5 if k==0 else .5)*depth) for k in range(2) for i in range(n)]
    fs=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    g.add(verts,fs,m)
def uv_sphere(g,c,s,m,n=16,lat=8):
    x,y,z=c; a,b,d=s;verts=[(x,y,z+d)]
    for j in range(1,lat):
        t=math.pi*j/lat
        for i in range(n):p=math.tau*i/n;verts.append((x+a*math.sin(t)*math.cos(p),y+b*math.sin(t)*math.sin(p),z+d*math.cos(t)))
    bottom=len(verts);verts.append((x,y,z-d))
    fs=[(0,1+i,1+(i+1)%n) for i in range(n)]
    for j in range(lat-2):
        row=1+j*n
        fs.extend([(row+i,row+n+i,row+n+(i+1)%n,row+(i+1)%n) for i in range(n)])
    row=1+(lat-2)*n
    fs.extend([(row+i,bottom,row+(i+1)%n) for i in range(n)])
    g.add(verts,fs,m)
def beam(g,a,b,r,m,n=8):
    a=Vector(a);b=Vector(b);d=(b-a).normalized();e=d.cross(Vector((0,0,1)))
    if e.length<.01:e=d.cross(Vector((0,1,0)))
    e.normalize();f=d.cross(e).normalized();verts=[]
    for p in (a,b):
        for i in range(n):q=p+r*(math.cos(i*math.tau/n)*e+math.sin(i*math.tau/n)*f);verts.append(tuple(q))
    g.add(verts,[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],m)
def torus(g,c,major,minor,m,n=32,k=8,vertical=False):
    x,y,z=c;vs=[]
    for i in range(n):
        a=math.tau*i/n
        for j in range(k):b=math.tau*j/k; q=((major+minor*math.cos(b))*math.cos(a),(major+minor*math.cos(b))*math.sin(a),minor*math.sin(b));vs.append((x+q[0],y+(q[2] if vertical else q[1]),z+(q[1] if vertical else q[2])))
    fs=[(i*k+j,i*k+(j+1)%k,((i+1)%n)*k+(j+1)%k,((i+1)%n)*k+j) for i in range(n) for j in range(k)]
    g.add(vs,fs if vertical else [tuple(reversed(f)) for f in fs],m)
def arch(g,x,y,z,width,height,depth,m,thick=.32):
    r=width/2;spring=height-r
    box(g,(x-r-thick/2,y,z+spring/2),(thick,depth,spring),m);box(g,(x+r+thick/2,y,z+spring/2),(thick,depth,spring),m)
    vs=[]
    for side in [-depth/2,depth/2]:
        for rad in [r,r+thick]:
            for i in range(17):a=math.pi*i/16;vs.append((x+rad*math.cos(a),y+side,z+spring+rad*math.sin(a)))
    fs=[]
    for i in range(16):fs.extend([(i,i+1,17+i+1,17+i),(34+i,51+i,51+i+1,34+i+1),(i,34+i,34+i+1,i+1),(17+i,17+i+1,51+i+1,51+i)])
    fs.extend([(0,17,51,34),(16,50,67,33)]);g.add(vs,[tuple(reversed(f)) for f in fs],m)
def arch_fill(g,x,y,z,w,h,m,depth=.08):
    r=w/2;spring=h-r;poly=[(x-r,y,z),(x+r,y,z)]+[(x+r*math.cos(i*math.pi/16),y,z+spring+r*math.sin(i*math.pi/16)) for i in range(17)]
    # Front face points toward south; reverse to obtain -Y outward.
    g.add(poly,[tuple(range(len(poly)))],m)
def lathe(g,c,profile,m,n=24):
    x,y,z=c;vs=[(x+r*math.cos(math.tau*i/n),y+r*math.sin(math.tau*i/n),z+h) for r,h in profile for i in range(n)]
    fs=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(profile)-1) for i in range(n)]
    g.add(vs,fs,m)

def terrain_height(x,y):
    d=math.sqrt(((x+20)/14.2)**2+((y+20)/10.5)**2)
    basin=-.85*math.exp(-(d/.89)**8)
    inner=.12+.05*math.sin(x*.28)*math.cos(y*.21)
    dunes=0
    for cx,cy,sx,sy,h in [(-41,-29,12,22,3.2),(-42,24,14,25,4.2),(1,43,31,9,4.8),(36,34,16,17,5.7),(44,-4,9,25,3.9),(25,-43,23,8,2.8),(-18,-44,26,8,2.5)]:
        dunes+=h*math.exp(-(((x-cx)/sx)**2+((y-cy)/sy)**2)*1.5)
    return inner+basin+dunes

t=group('SM_SculptedSandTerrain',smooth=True)
nn=150;vs=[]
for j in range(nn+1):
    y=-50+100*j/nn
    for i in range(nn+1):x=-50+100*i/nn;vs.append((x,y,terrain_height(x,y)))
fs=[]
for j in range(nn):
    for i in range(nn):a=j*(nn+1)+i;fs.extend([(a,a+1,a+nn+2),(a,a+nn+2,a+nn+1)])
t.add(vs,fs,'Sand')
# Ground thickness and smooth beveled 100 m footprint.
base=group('SM_DioramaEarth',.35);box(base,(0,0,-1.45),(100,100,1.5),'Sandstone')
dunes=group('SM_WindSculptedDuneCrests',smooth=True)
for k,(cx,cy,length,angle) in enumerate([(-40,-7,30,.18),(-29,39,33,-.2),(24,40,25,.4),(42,-25,24,.8),(-5,-43,28,.05)]):
    verts=[]
    for i in range(65):
        a=(i/64-.5)*length;xx=cx+a*math.cos(angle);yy=cy+a*math.sin(angle)
        for side in [-1,1]:
            ox=xx-side*.13*math.sin(angle);oy=yy+side*.13*math.cos(angle);verts.append((ox,oy,terrain_height(ox,oy)+.025))
    dunes.add(verts,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(64)],'DuneLight')

terr=group('SM_TerracedVillageFoundation',.10)
box(terr,(1,17,.66),(55,27,1.35),'Sandstone')
box(terr,(1,17,1.38),(55.4,27.4,.22),'Limestone')
box(terr,(-24,8,.46),(14,18,.95),'Sandstone');box(terr,(-24,8,1.02),(14.4,18.4,.18),'Limestone')
for x in range(-26,29,2):box(terr,(x,3.28,.72),(1.88,.36,1.1),'Sandstone')
plaza=group('SM_TradingPlazaPaving',.035)
box(plaza,(5,-8,.20),(30,21,.30),'Sandstone')
for ix in range(20):
    for iy in range(14):
        x=-9.3+ix*1.49;y=-17.7+iy*1.48
        m='Limestone' if (ix*3+iy)%8<3 else 'PlasterCream'
        box(plaza,(x,y,.39+random.uniform(-.008,.008)),(1.42,1.41,.12),m)
for x,y in [(16,-22),(18,-24),(21,-26),(24,-28),(26,-30),(-10,-22),(-10,-25),(-13,-27),(-16,-29),(-19,-31),(-25,-31),(-28,-29)]:
    box(plaza,(x,y,terrain_height(x,y)+.12),(1.7,1.15,.20),'Limestone',random.uniform(-.25,.25))

archs=group('SM_CaravanseraiArcades',.055)
house=group('SM_CaravanseraiArchitecture',.05)
# Broad rear caravan lodging with five genuine open vaulted bays.
cx,cy,z,w,d,h=0,16,1.5,21,12,7.1
box(house,(cx,cy+2.3,z+h/2),(w,d-4.6,h),'PlasterWarm')
box(house,(-10.2,12,z+h/2),(.6,4.5,h),'PlasterWarm');box(house,(10.2,12,z+h/2),(.6,4.5,h),'PlasterWarm')
box(house,(0,11.2,z+5.5),(21,3.8,3.2),'PlasterWarm')
for x in [-8,-4,0,4,8]:arch(archs,x,9.2,z,3.25,4.05,.85,'TrimCream',.36)
box(house,(0,16,z+h+.13),(21.6,12.6,.32),'TrimCream')
for yy in [9.8,22.2]:box(house,(0,yy,z+h+.64),(21.6,.42,.85),'PlasterPeach')
for xx in [-10.6,10.6]:box(house,(xx,16,z+h+.64),(.42,12.2,.85),'PlasterPeach')
box(house,(1.4,18,z+h+2.0),(8.5,6.8,3.7),'PlasterPeach')
box(house,(1.4,18,z+h+3.98),(9.0,7.25,.3),'TrimCream')
for x in [-7.6,-3.8,0,3.8,7.6]:
    arch_fill(house,x,9.19,z+4.9,.92,1.45,'Recess');arch(archs,x,9.1,z+4.9,.92,1.45,.16,'TrimCream',.14)
    for k in range(3):box(archs,(x-.27+k*.27,9.0,z+5.46),(.055,.075,.8),'Wood')
# roof wooden drainage scuppers.
for x in [-8,-4,0,4,8]:box(house,(x,9.3,8.35),(.20,1.1,.22),'Wood')

homes=group('SM_AdobeHomes',.09); details=group('SM_DoorsWindowsAndBeams',.01)
def building(x,y,z,w,d,h,col,door='DoorTeal',upper=False):
    box(homes,(x,y,z+h/2),(w,d,h),col)
    box(homes,(x,y,z+h+.05),(w+.45,d+.45,.24),'TrimCream')
    for yy in [y-d/2,y+d/2]:box(homes,(x,yy,z+h+.50),(w+.35,.38,.82),col)
    for xx in [x-w/2,x+w/2]:box(homes,(xx,y,z+h+.50),(.38,d,.82),col)
    fy=y-d/2-.021
    arch_fill(details,x,fy-.02,z+.04,1.25,2.35,'Recess');arch_fill(details,x,fy-.05,z+.04,1.10,2.18,door)
    arch(details,x,fy-.12,z,1.30,2.4,.20,'TrimCream',.22)
    for dx in [-w*.29,w*.29]:
        arch_fill(details,x+dx,fy-.025,z+2.25,.85,1.28,'Recess');arch(details,x+dx,fy-.08,z+2.20,.90,1.37,.16,'TrimCream',.13)
        box(details,(x+dx,fy-.15,z+2.2),(1.20,.45,.17),'Wood')
        if (int(x*2+dx)%3)!=0:
            for b in [-.25,0,.25]:box(details,(x+dx+b,fy-.16,z+2.82),(.055,.07,.75),'Wood')
    for dx in np.arange(-w/2+.65,w/2,.95):box(details,(x+dx,fy-.28,z+h-.36),(.16,.8,.18),'Wood')
    box(details,(x,fy-.19,z+.10),(1.70,.8,.18),'Limestone')
    if upper:
        building(x+w*.12,y+d*.1,z+h+.18,w*.55,d*.58,2.9,'PlasterCream',door,False)
    return z+h+.19

roof=[]
for spec in [(-20,15,1.5,8,8,5.4,'PlasterPeach',True),(-22,25,1.5,9,7,6.1,'PlasterRose',False),(-15,25,1.5,5.4,6.8,4.7,'PlasterCream',False),(-24,3.5,1.13,8,7,4.5,'PlasterCream',False),(-30,11,1.13,6,8,5.7,'PlasterWarm',False),(17,20,1.5,8.5,10,5.2,'PlasterPeach',True),(24,23,1.5,6,7,7.5,'PlasterWarm',False),(23,11,1.5,9,8.5,4.6,'PlasterRose',False),(17,6.5,1.5,6,6,3.9,'PlasterCream',False),(29,0,.5,8,8,5.1,'PlasterPeach',True),(30,-10,.35,6.5,6,4.3,'PlasterWarm',False),(-4,27,1.5,8,6,4.8,'PlasterCream',False)]:
    x,y,z,w,d,h,col,upper=spec; roof.append((x,y,building(x,y,z,w,d,h,col,upper=upper),w,d))

tower=group('SM_WindcatcherTower',.08)
box(tower,(-11,19,6.7),(4.3,5.0,10.4),'PlasterRose');box(tower,(-11,19,12.05),(4.9,5.5,.35),'TrimCream')
for xx in [-12.55,-9.45]:
    for yy in [17.25,20.75]:box(tower,(xx,yy,13.25),(.65,.65,2.4),'PlasterPeach')
box(tower,(-11,19,14.65),(5.1,5.7,.5),'TrimCream')
for xx in [-12.0,-11,-10]:beam(tower,(xx,17.2,12.4),(xx,17.2,14.3),.065,'Wood')
box(tower,(-11,19,15.13),(4.45,5.05,.4),'PlasterPeach')

stairs=group('SM_ExteriorStairsAndRoutes',.055)
def stair(x,y,z,w,steps,rise,run,direction=1):
    for i in range(steps):box(stairs,(x,y+direction*(i+.5)*run,z+(i+1)*rise/2),(w,run+.02,(i+1)*rise),'Limestone')
    for side in [-1,1]:
        for i in range(steps):box(stairs,(x+side*(w/2+.15),y+direction*(i+.5)*run,z+(i+1)*rise+.22),(.28,run+.03,.44),'PlasterWarm')
stair(0,1.0,.45,5.4,6,.175,.40)
stair(-15.5,5.3,1.5,1.9,18,.29,.38)
stair(26.9,7.3,1.5,1.6,16,.29,.38)
stair(33.8,-3.6,.40,1.5,18,.29,.38)
stair(-28.4,-1.5,.2,2.7,5,.18,.42)

gate=group('SM_EasternCaravanGateway',.095)
for x in [20.7,28.5]:
    box(gate,(x,-19.8,2.85),(2.4,2.7,5.2),'PlasterWarm');box(gate,(x,-19.8,5.65),(2.75,3.05,.4),'TrimCream')
    for dx in [-.83,0,.83]:box(gate,(x+dx,-20.9,6.03),(.45,.6,.5),'PlasterPeach')
arch(gate,24.6,-19.8,.3,5.4,5.0,1.15,'PlasterPeach',.65)
box(gate,(24.6,-19.8,5.54),(5.5,1.45,.43),'TrimCream')
for x in [17.4,31.4]:box(gate,(x,-19.8,1.0),(4.2,.7,1.4),'PlasterWarm')

market=group('SM_MarketTimberAndStalls',.012);cloth=group('SM_ShadeClothCanopies',smooth=True)
def canopy(x,y,z,w,d,color,phase=0):
    nx,ny=24,14;verts=[]
    for j in range(ny+1):
        vv=j/ny
        for i in range(nx+1):
            uu=i/nx; sag=.45*math.sin(math.pi*uu)*math.sin(math.pi*vv)
            verts.append((x+(uu-.5)*w,y+(vv-.5)*d,z-sag+.07*math.sin(uu*math.tau*5+phase)*math.sin(math.pi*vv)))
    for j in range(ny):
        for i in range(nx):
            a=j*(nx+1)+i;m='ClothCream' if i//4%2==0 else color
            cloth.add([verts[a],verts[a+1],verts[a+nx+2],verts[a+nx+1]],[(0,1,2,3)],m,uv=[[(i/nx*4,j/ny*3),((i+1)/nx*4,j/ny*3),((i+1)/nx*4,(j+1)/ny*3),(i/nx*4,(j+1)/ny*3)]])
    # Scalloped valance along visible edge.
    for i in range(32):
        xa=x-w/2+i*w/32;xb=xa+w/32;za=z-.25-.08*math.sin((i+.5)/32*math.tau*8)
        cloth.add([(xa,y-d/2,z),(xb,y-d/2,z),(xb,y-d/2,za),(xa,y-d/2,za)],[(0,1,2,3)],color if i//5%2 else 'ClothCream')
    for dx in [-w/2,w/2]:
        for dy in [-d/2,d/2]:beam(market,(x+dx,y+dy,.5),(x+dx,y+dy,z+.12),.09,'Wood')
    beam(market,(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),.075,'Wood')
def stall(x,y,w,d,color):
    box(market,(x,y,.95),(w,d,1.05),'WoodLight');box(market,(x,y,1.53),(w+.15,d+.12,.14),'Wood')
    for dx in np.arange(-w/2+.15,w/2,.31):box(market,(x+dx,y-d/2-.03,.97),(.055,.08,.95),'Wood')
    canopy(x,y,3.65,w+.65,d+1.55,color)
    return (x,y,1.65)
stalls=[]
for x,y,w,d,col in [(-5,-4,4.0,1.5,'ClothTerracotta'),(1,-3.2,4.1,1.6,'ClothTeal'),(9,-2.8,4.0,1.5,'ClothGold'),(17,-8.5,3.8,1.5,'ClothTerracotta'),(-5,-12,4.0,1.6,'ClothGold'),(6,-13,4.4,1.5,'ClothTeal')]:stalls.append(stall(x,y,w,d,col))
canopy(6,-7.5,5.4,13.5,8.3,'ClothTerracotta',.8)
canopy(-20,15,7.2,5.6,4.9,'ClothTeal',.4)
canopy(18.2,21,7.5,4.7,5.2,'ClothGold',.2)

rugs=group('SM_HandPatternedRugs')
def rug(x,y,z,w,d,material,angle=0):
    vs=[];nx,ny=12,16
    for j in range(ny+1):
        for i in range(nx+1):
            a=(i/nx-.5)*w;b=(j/ny-.5)*d;zz=z+.018*math.sin(i*.65+j*.4)
            vs.append((x+a*math.cos(angle)-b*math.sin(angle),y+a*math.sin(angle)+b*math.cos(angle),zz))
    fs=[];uv=[]
    for j in range(ny):
        for i in range(nx):
            a=j*(nx+1)+i;fs.append((a,a+1,a+nx+2,a+nx+1));uv.append([(i/nx,j/ny),((i+1)/nx,j/ny),((i+1)/nx,(j+1)/ny),(i/nx,(j+1)/ny)])
    rugs.add(vs,fs,material,uv)
    for i in range(28):
        a=(i/27-.5)*w
        for s in [-1,1]:
            b=s*d/2; end=s*(d/2+.13)
            beam(rugs,(x+a*math.cos(angle)-b*math.sin(angle),y+a*math.sin(angle)+b*math.cos(angle),z),(x+a*math.cos(angle)-end*math.sin(angle),y+a*math.sin(angle)+end*math.cos(angle),z),.012,'ClothCream',4)
for spec in [(-5,-8.2,.50,3.6,2.9,'RugRust',.05),(3.3,-8.4,.50,3.8,2.7,'RugTeal',-.11),(12,-12,.50,2.4,3.4,'RugGold',.20),(-19,10.1,1.58,2.6,3.0,'RugRust',0),(0,12.8,1.57,3.3,2.4,'RugTeal',.12),(-24,2,5.85,3.3,2.4,'RugGold',0)]:rug(*spec)

pots=group('SM_HandThrownPottery',smooth=True); baskets=group('SM_WovenBaskets',smooth=True);produce=group('SM_MarketProduce',smooth=True)
def pot(x,y,z,s=1,m='Terracotta'):
    profile=[(0,0),(.25,0),(.34,.1),(.48,.40),(.45,.68),(.27,.89),(.25,1.05),(.30,1.10),(.30,1.16),(.22,1.16),(.20,1.07),(.20,.93),(.28,.80),(.30,.43)]
    lathe(pots,(x,y,z),[(a*s,b*s) for a,b in profile],m)
    torus(pots,(x,y,z+1.13*s),.26*s,.035*s,'CeramicCream',24,6)
    if s>.8:
        for side in [-1,1]:
            for i in range(9):
                a=i*math.pi/8;b=(i+1)*math.pi/8
                beam(pots,(x+side*(.30+.18*math.sin(a))*s,y,z+(.85-.32*i/8)*s),(x+side*(.30+.18*math.sin(b))*s,y,z+(.85-.32*(i+1)/8)*s),.045*s,m,6)
def basket(x,y,z,s=1,kind=None):
    lathe(baskets,(x,y,z),[(.25*s,0),(.38*s,.10*s),(.47*s,.45*s),(.50*s,.54*s),(.44*s,.54*s),(.39*s,.20*s),(.28*s,.09*s)],'Basket')
    for i in range(6):torus(baskets,(x,y,z+(.1+i*.08)*s),(.37+i*.021)*s,.022*s,'WoodLight',24,5)
    if kind:
        for i in range(18):
            a=random.random()*math.tau;r=random.random()*.32*s;uv_sphere(produce,(x+math.cos(a)*r,y+math.sin(a)*r,z+.45*s+random.random()*.15*s),(.07*s,.07*s,.07*s),kind,8,4)

for i,(x,y,z) in enumerate(stalls):
    for j in range(4):
        if i%2==0:basket(x-1.4+j*.9,y,z,.75,['Orange','Olive','Dates'][j%3])
        else:pot(x-1.4+j*.9,y,z,.48+.12*(j%2),['Terracotta','CeramicTeal','CeramicCream'][j%3])
for x,y,z,s,m in [(-9,-3,.4,1.25,'Terracotta'),(-8,-3.5,.4,.8,'CeramicCream'),(12,1,1.5,1.3,'CeramicTeal'),(13,1,1.5,.8,'Terracotta'),(-19,9.8,1.5,1.3,'CeramicTeal'),(-18,10,1.5,.75,'Terracotta'),(26,-3,.45,1.2,'Terracotta'),(27,-3,.45,.8,'CeramicCream'),(23,-16,.35,1.0,'Terracotta'),(29,-18,.5,1.1,'CeramicTeal'),(-3,10.8,1.5,.9,'Terracotta'),(7,10.7,1.5,1.1,'CeramicTeal'),(-23,4,5.85,.8,'Terracotta')]:pot(x,y,z,s,m)
for x,y,z,s in [(-8,-11,.45,1.2),(-8.9,-11,.45,1),(9,-14.8,.45,1.3),(10.1,-14.7,.45,1.1),(19,-11,.35,1.1),(-21,9.6,1.5,1.1)]:basket(x,y,z,s,'Dates')

crates=group('SM_CratesAndCaravanCargo',.003)
def crate(x,y,z,w=1.1,d=.85,h=.9):
    box(crates,(x,y,z+h/2),(w,d,h),'WoodLight')
    for zz in [z+.12,z+h-.12]:
        for yy in [y-d/2-.03,y+d/2+.03]:box(crates,(x,yy,zz),(w+.05,.075,.13),'Wood')
    for xx in [x-w/2+.10,x+w/2-.10]:
        for yy in [y-d/2-.06,y+d/2+.06]:box(crates,(xx,yy,z+h/2),(.12,.10,h),'Wood')
    for dx in [-.3,0,.3]:box(crates,(x+dx,y,z+h+.016),(.015,d,.025),'Wood')
for x,y,z in [(20,-15,.3),(21.15,-15,.3),(20.4,-15,1.22),(-15,5,1.5),(-16.2,5,1.5),(14,-.5,1.5),(15.1,-.5,1.5),(14.5,-.5,2.4),(-30,6,1.1),(-29,6,1.1)]:crate(x,y,z)
carts=group('SM_WoodenTradingCarts')
for cx,cy in [(19,-23),(-14,-7)]:
    box(carts,(cx,cy,1.0),(2.8,1.6,.22),'WoodLight')
    for dx in [-1.4,1.4]:
        for zz in [1.25,1.57]:box(carts,(cx+dx,cy,zz),(.10,1.7,.18),'Wood')
    for dy in [-.8,.8]:
        for zz in [1.25,1.57]:box(carts,(cx,cy+dy,zz),(2.8,.10,.18),'Wood')
    beam(carts,(cx,cy-1.2,.75),(cx,cy+1.2,.75),.085,'Metal')
    for dy in [-1.02,1.02]:
        torus(carts,(cx,cy+dy,.75),.64,.085,'Wood',24,6,True)
        for i in range(8):a=i*math.tau/8;beam(carts,(cx,cy+dy,.75),(cx+.60*math.cos(a),cy+dy,.75+.60*math.sin(a)),.037,'WoodLight',6)
    for dy in [-.62,.62]:beam(carts,(cx+1.3,cy+dy,1.0),(cx+3.4,cy+dy,.65),.075,'Wood')
    crate(cx-.4,cy,1.12,1,.8,.8);pot(cx+.8,cy,1.12,.63,'Terracotta')

well=group('SM_CommunityWell',.004)
wx,wy=12,-18
lathe(well,(wx,wy,.4),[(1.35,0),(1.35,.90),(1.47,.9),(1.47,1.12),(1.05,1.12),(1.05,.20)],'Limestone',32)
for i in range(12):
    a=i*math.tau/12;box(well,(wx+1.28*math.cos(a),wy+1.28*math.sin(a),1.15),(.1,.12,.75),'Sandstone',a)
for dx in [-1.8,1.8]:beam(well,(wx+dx,wy,.35),(wx+dx,wy,3.75),.14,'Wood')
beam(well,(wx-2,wy,3.6),(wx+2,wy,3.6),.18,'Wood')
beam(well,(wx,wy,3.5),(wx,wy,1.6),.022,'Basket');basket(wx,wy,1.38,.65)
channel=group('SM_OasisIrrigationChannel',.035)
for x in np.arange(-7,11,1.3):
    for dy in [-.46,.46]:box(channel,(x,-20+dy,.3),(1.26,.23,.35),'Limestone')
box(channel,(2,-20,.20),(19,.65,.08),'Water')

waterg=group('SM_TurquoiseOasisWater',smooth=True)
cx,cy=-20,-20;nr,ns=16,112;vs=[(cx,cy,-.02)]
for j in range(1,nr+1):
    q=j/nr
    for i in range(ns):a=i*math.tau/ns;r=q*(1+.045*math.sin(a*5)+.025*math.sin(a*9+.7));vs.append((cx+13.2*r*math.cos(a),cy+9.35*r*math.sin(a),-.02))
fs=[(0,1+i,1+(i+1)%ns) for i in range(ns)]
for j in range(nr-1):
    off=1+j*ns
    for i in range(ns):fs.append((off+i,off+ns+i,off+ns+(i+1)%ns,off+(i+1)%ns))
waterg.add(vs,fs,'Water')
shore=group('SM_OasisShoreStones',smooth=True);ripples=group('SM_SubtleOasisShoreHighlights',smooth=True)
for i in range(66):
    a=i*math.tau/66+.06*random.random();r=1+.03*random.random();x=cx+14.1*r*math.cos(a);y=cy+10.25*r*math.sin(a)
    if -1.1<a<.25:continue
    z=terrain_height(x,y);uv_sphere(shore,(x,y,z+.12),(random.uniform(.30,.70),random.uniform(.25,.55),random.uniform(.20,.42)),'Rock',12,6)
for k in range(7):
    a0=.2+k*.78;verts=[]
    for i in range(28):
        a=a0+i/27*.36;r=.93+.014*math.sin(a*11)
        for dr in [-.003,.003]:verts.append((cx+13.0*(r+dr)*math.cos(a),cy+9.0*(r+dr)*math.sin(a),.006))
    ripples.add(verts,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(27)],'WaterEdge')

trunks=group('SM_CurvedPalmTrunks',smooth=True);leaves=group('SM_PalmFronds',smooth=True);reeds=group('SM_OasisReeds',smooth=True)
def palm(x,y,h,lean,seed):
    rr=random.Random(seed);z=terrain_height(x,y);angle=rr.random()*math.tau;points=[]
    for j in range(15):
        t=j/14;points.append((x+math.cos(angle)*lean*t*t,y+math.sin(angle)*lean*t*t,z+h*t))
    for j in range(14):
        beam(trunks,points[j],points[j+1],.24-(j/14)*.095,'PalmTrunk',12)
        px,py,pz=points[j];torus(trunks,(px,py,pz),.24-(j/14)*.095,.035,'WoodLight',12,5)
    tx,ty,tz=points[-1]
    uv_sphere(trunks,(tx,ty,tz-.1),(.36,.36,.45),'PalmLeaf',12,6)
    for f in range(12):
        a=f*math.tau/12+rr.uniform(-.13,.13);length=rr.uniform(3.0,4.4);up=rr.uniform(.5,1.5);vs=[]
        for j in range(15):
            t=j/14;px=tx+math.cos(a)*length*t;py=ty+math.sin(a)*length*t;pz=tz+up*math.sin(math.pi*t)-1.40*t*t;wid=.50*math.sin(math.pi*t)**.7
            for side in [-1,0,1]:vs.append((px-side*math.sin(a)*wid,py+side*math.cos(a)*wid,pz-(abs(side)*.12*math.sin(math.pi*t))))
        leaves.add(vs,[(j*3,j*3+3,j*3+4,j*3+1) for j in range(14)]+[(j*3+1,j*3+4,j*3+5,j*3+2) for j in range(14)],'PalmLeafLight' if f%3==0 else 'PalmLeaf')
        # The folded leaf surface carries the form; omit tiny rib cylinders that caused contact-shadow speckle.
    for i in range(5):a=i*math.tau/5;uv_sphere(trunks,(tx+.25*math.cos(a),ty+.25*math.sin(a),tz-.35),(.16,.16,.22),'Dates',8,4)
for i,(x,y,h,l) in enumerate([(-31,-23,8.4,1),(-28,-11,9.2,1.1),(-18,-8.7,8.1,.8),(-9,-15,7.1,.6),(-19,-32,7.6,.9),(-33,-13,6.5,1.0),(-8,-26,8.0,.65),(7,-25,7.2,.8),(34,11,8.5,.7),(-34,23,7.6,.6),(14,30,7.9,.8)]):palm(x,y,h,l,470+i)
for x,y in [(-31,-18),(-28,-28),(-14,-28),(-8.5,-21),(-25,-10)]:
    for i in range(13):
        px=x+random.uniform(-.6,.6);py=y+random.uniform(-.6,.6);z=terrain_height(px,py);h=random.uniform(.5,1.25)
        beam(reeds,(px,py,z),(px+random.uniform(-.15,.15),py+random.uniform(-.15,.15),z+h),.025,'Reed',5)

props=group('SM_LanternsBenchesAndSigns',.0075)
for x,y,z in [(-8,8.7,4.6),(8,8.7,4.6),(21,-20.9,4.7),(28.1,-20.9,4.7),(-24,-.2,3.3),(29,-14,3.0)]:
    beam(props,(x,y+.4,z+.4),(x,y-.3,z+.4),.035,'Metal');beam(props,(x,y-.3,z+.4),(x,y-.3,z+.13),.02,'Metal')
    box(props,(x,y-.3,z-.12),(.22,.22,.38),'LanternGlass')
    for zz in [z-.34,z+.12]:box(props,(x,y-.3,zz),(.30,.30,.08),'Metal')
for x,y,z in [(-2,8.5,1.5),(6,8.5,1.5),(-21,7.4,1.13),(25,-5,.4)]:
    box(props,(x,y,z+.62),(2.2,.65,.15),'WoodLight')
    for dx in [-.8,.8]:box(props,(x+dx,y,z+.3),(.16,.44,.6),'Wood')
for x,y,z in [(-5,-4.85,2.5),(1,-4.15,2.5),(9,-3.7,2.5)]:
    box(props,(x,y,z),(1.1,.12,.38),'WoodLight')
    # Purpose-built geometric shop symbols, no borrowed lettering.
    for dx in [-.30,0,.30]:uv_sphere(props,(x+dx,y-.08,z),(.08,.025,.08),'TrimCream',8,4)

# Export per semantic assembly, preserving authored material slot names.
objects=[];source_manifest={'started_at_utc':datetime.fromtimestamp(START,timezone.utc).isoformat(),'unit':'meters','export_unit':'centimeters via FBX unit metadata','seed':37191,'materials':MAT,'meshes':[],'design_scope_m':[100,100],'uv_method':'Dominant-normal box projection in world meters for repeating textures. Rugs use dedicated full 0-1 islands; frond and solid color meshes retain planar coordinates. Repeating UV overlap intentional, no lightmap UV requirement with fully dynamic lighting.'}
for name,g in G.items():
    o=g.finish();objects.append(o)
    # Calibration imports Blender Y with reversed sign in UE. Preconvert only the FBX copy.
    exp=o.copy();exp.data=o.data.copy();scene.collection.objects.link(exp);exp.name=name+'_Export'
    exp.data.transform(Matrix.Diagonal((1,-1,1,1)));exp.data.flip_normals()
    bpy.context.view_layer.objects.active=exp;exp.select_set(True)
    fpath=FBX/(name+'.fbx')
    bpy.ops.export_scene.fbx(filepath=str(fpath),use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,path_mode='STRIP')
    exp.select_set(False);bpy.data.objects.remove(exp,do_unlink=True)
    bounds=[[min(v.co[a] for v in o.data.vertices),max(v.co[a] for v in o.data.vertices)] for a in range(3)]
    source_manifest['meshes'].append({'name':name,'fbx':str(fpath),'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'bounds_m':bounds,'materials':[m.name for m in o.data.materials],'uv_layers':len(o.data.uv_layers),'zero_area_faces':sum(p.area<1e-10 for p in o.data.polygons)})
    print('EXPORTED',name,len(o.data.polygons),flush=True)

# Deliberately asymmetric axis/scale probe, never part of delivered level.
probe=Group('SM_AxisProbe');box(probe,(3,7,1),(2,4,2),'PlasterWarm');o=probe.finish();o.data.transform(Matrix.Diagonal((1,-1,1,1)));o.data.flip_normals();o.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.export_scene.fbx(filepath=str(FBX/'SM_AxisProbe.fbx'),use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',add_leaf_bones=False,bake_anim=False)
bpy.data.objects.remove(o,do_unlink=True)
source_manifest['axis_probe_bounds_m']=[[2,4],[5,9],[0,2]]
source_manifest['fbx_axis_correction']='Original UE probe imported X unchanged, Y reversed, Z unchanged, meters to centimeters x100. Export copies mirror Y and reverse winding so imported UE scene matches intended author coordinates.'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'DesertVillage_Original.blend'))
source_manifest['finished_at_utc']=datetime.now(timezone.utc).isoformat();source_manifest['elapsed_seconds']=time.time()-START
source_manifest['total_triangles']=sum(x['triangles'] for x in source_manifest['meshes'])
source_manifest['texture_files']=[p.name for p in sorted(TEX.glob('*.png'))]
(ART/'source_manifest.json').write_text(json.dumps(source_manifest,indent=2),encoding='utf-8')
print('COMPLETE',len(objects),source_manifest['total_triangles'],'triangles',time.time()-START,flush=True)
