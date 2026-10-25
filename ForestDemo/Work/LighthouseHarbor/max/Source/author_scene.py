"""Original LighthouseHarbor/max art. Blender 5; all dimensions are metres."""
import bpy, bmesh, math, random, json, time
import numpy as np
from mathutils import Vector
from pathlib import Path
R=random.Random(42713)
ROOT=Path('D:/github/AstraEffort/ForestDemo/Work/LighthouseHarbor/max')
ART=ROOT/'SourceArt'; FBX=ART/'FBX'; TEX=ART/'Textures'
for p in [ART,FBX,TEX,ROOT/'Validation']: p.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC'; bpy.context.scene.unit_settings.scale_length=1.0
GROUPS={}; MAT={}; palette={}

def material(name, rgb, rough=0.7, kind='plaster', tile=4.0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*rgb,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=rough
    n=512; y,x=np.mgrid[0:n,0:n].astype(np.float32)/n
    # Analytic periodic harmonics: exact seamless wrapping, fixed seed and no sourced images.
    noise=(np.sin(2*math.pi*(x*7+y*11))+np.sin(2*math.pi*(x*23-y*17))*.35+np.sin(2*math.pi*(x*61+y*43))*.16)/1.51
    if kind=='wood': noise=.55*np.sin(2*math.pi*(y*29+.22*np.sin(x*2*math.pi)))+.25*np.sin(2*math.pi*(y*77+x*2))+.2*noise
    elif kind=='stone': noise=.5*noise+.5*np.sin(2*math.pi*(y*13+.3*np.sin(x*6*math.pi)))
    elif kind=='copper': noise=.6*noise+.4*np.sin(2*math.pi*(x*3+y*4))
    amp=.055 if kind in ['plaster','metal'] else .10
    pixels=np.empty((n,n,4),dtype=np.float32)
    for c in range(3): pixels[:,:,c]=np.clip(rgb[c]*(1+noise*amp),0,1)
    pixels[:,:,3]=1
    img=bpy.data.images.new('T_'+name,width=n,height=n,alpha=True)
    img.pixels.foreach_set(pixels.ravel()); img.filepath_raw=str(TEX/('T_'+name+'.png'));img.file_format='PNG';img.save()
    tex=m.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=img;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
    MAT[name]=m;palette[name]={'color_srgb':rgb,'roughness':rough,'kind':kind,'tile_metres':tile,'image':str(TEX/('T_'+name+'.png'))}
    return m

for args in [
('Chalk',(0.91,.84,.66),.82,'plaster',4),('WarmStone',(.59,.48,.34),.9,'stone',4),
('CliffSand',(.70,.57,.39),.92,'stone',4),('CliffShade',(.43,.38,.31),.95,'stone',4),
('Grass',(.40,.52,.31),.92,'plaster',4),('GrassLight',(.54,.61,.34),.9,'plaster',4),
('Path',(.74,.66,.48),.95,'stone',4),('BrickRed',(.67,.22,.13),.75,'plaster',3),
('RoofClay',(.69,.32,.18),.78,'stone',3),('RoofLight',(.82,.43,.23),.76,'stone',3),
('Copper',(.18,.40,.37),.48,'copper',3),('Timber',(.37,.22,.11),.84,'wood',2),
('TimberLight',(.61,.43,.24),.8,'wood',2),('SeaPaint',(.21,.46,.51),.65,'plaster',2),
('Mustard',(.85,.61,.22),.68,'plaster',2),('Iron',(.12,.19,.20),.45,'metal',2),
('Rope',(.72,.61,.40),.9,'wood',1),('Window',(.10,.24,.28),.25,'metal',2),
('Lamp',(1.0,.70,.28),.35,'plaster',2),('Foam',(.77,.91,.80),.55,'plaster',4),
('Water',(.12,.43,.49),.28,'plaster',8),('DeepWater',(.07,.25,.33),.6,'plaster',8),
('Flower',(.91,.57,.35),.8,'plaster',1)]: material(*args)

def collect(o,g,mat,smooth=False):
    o.name=g+'_'+str(len(GROUPS.get(g,[]))).zfill(4);o.data.materials.append(MAT[mat])
    for p in o.data.polygons:p.use_smooth=smooth
    GROUPS.setdefault(g,[]).append(o);return o
def bevel(o,w=.06,segments=2):
    if w<=0:return o
    mod=o.modifiers.new('Soft hand-shaped edges','BEVEL');mod.width=w;mod.segments=segments
    mod.affect='EDGES'
    bpy.context.view_layer.objects.active=o
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return o
def cube(g,loc,size,mat,bev=.05,rot=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);bevel(o,bev)
    o.rotation_euler.z=rot;return collect(o,g,mat)
def cyl(g,loc,r,depth,mat,verts=24,r2=None):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=r if r2 is None else r2,depth=depth,location=loc)
    o=bpy.context.object;bevel(o,min(.06,r*.12));return collect(o,g,mat,True)
def sphere(g,loc,scale,mat,sub=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=loc);o=bpy.context.object;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return collect(o,g,mat,True)
def mesh(g,verts,faces,mat,smooth=False):
    me=bpy.data.meshes.new(g);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(g,me);bpy.context.collection.objects.link(o)
    return collect(o,g,mat,smooth)
def line(g,pts,r,mat,cyclic=False):
    cu=bpy.data.curves.new('Rounded line','CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=r;cu.bevel_resolution=2
    sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,co in zip(sp.points,pts):p.co=(*co,1)
    sp.use_cyclic_u=cyclic;o=bpy.data.objects.new(g,cu);bpy.context.collection.objects.link(o)
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
    return collect(o,g,mat,True)
def rod(g,a,b,r,mat,verts=12):
    a,b=Vector(a),Vector(b);o=cyl(g,(a+b)/2,r,(b-a).length,mat,verts)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def ring(g,center,r,t,mat,segments=48):
    return line(g,[(center[0]+r*math.cos(i*2*math.pi/segments),center[1]+r*math.sin(i*2*math.pi/segments),center[2]) for i in range(segments)],t,mat,True)
def rock(g,p,s,mat='CliffSand'):
    o=sphere(g,p,s,mat,2);o.rotation_euler=(R.uniform(-.2,.2),R.uniform(-.2,.2),R.uniform(0,6.2));return o

# 100 metre square water foundation, plus a separate dense surface for shader motion.
cube('Water_Base',(0,0,-2.5),(100,100,4.4),'DeepWater',1.1)
n=64;vv=[(-50+100*x/n,-50+100*y/n,-.18) for y in range(n+1) for x in range(n+1)]
ff=[(y*(n+1)+x,y*(n+1)+x+1,(y+1)*(n+1)+x+1,(y+1)*(n+1)+x) for y in range(n) for x in range(n)]
mesh('Water_Surface',vv,ff,'Water',True)

def terrain(g,c,rx,ry,bottom,top,seed):
    rng=random.Random(seed);N=48;ang=[i*2*math.pi/N for i in range(N)]
    radii=[1+.035*math.sin(5*a+seed)+.03*math.cos(9*a+.3) for a in ang]
    rings=[(1.0,bottom),(1.02,bottom+(top-bottom)*.16),(.96,bottom+(top-bottom)*.54),(.91,top-.55),(.90,top)]
    v=[]
    for j,(s,z) in enumerate(rings):
        for i,a in enumerate(ang):v.append((c[0]+rx*radii[i]*s*math.cos(a),c[1]+ry*radii[i]*s*math.sin(a),z+(0 if j in [0,4] else .28*math.sin(7*a+1.4*j))))
    f=[]
    for j in range(4):
        for i in range(N):f.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
    f.append(tuple(reversed(range(N))));o=mesh(g,v,f,'CliffSand')
    o.data.materials.append(MAT['CliffShade']);o.data.materials.append(MAT['WarmStone'])
    for p in o.data.polygons:p.material_index=1 if (p.index//N)==1 else (2 if p.index%7 in [0,1] else 0)
    bevel(o,.20,2)
    topv=[(c[0],c[1],top)]+[(c[0]+rx*radii[i]*.90*math.cos(a),c[1]+ry*radii[i]*.90*math.sin(a),top) for i,a in enumerate(ang)]
    grass=mesh(g+'_Grass',topv,[(0,i+1,(i+1)%N+1) for i in range(N)],'Grass')
    grass.data.materials.append(MAT['GrassLight'])
    for p in grass.data.polygons:p.material_index=1 if p.index%9==0 else 0
    return [(c[0]+rx*radii[i]*.92*math.cos(a),c[1]+ry*radii[i]*.92*math.sin(a),top) for i,a in enumerate(ang)]
edge=terrain('Cliff_Lower',(-7,7),39,34,-1,3.2,14)
mid=terrain('Cliff_Middle',(-15,15),28,22,3.0,13,25)
upper=terrain('Cliff_Upper',(-23,21),17,14,12.8,25,33)

# Rock columns break the uniform tier outlines; fine strata make close cliff views legible.
for i in range(38):
    a=R.uniform(0,2*math.pi);rx,ry=R.uniform(34,38),R.uniform(29,32)
    x,y=-7+rx*math.cos(a),7+ry*math.sin(a)
    if abs(x)<47 and abs(y)<47:rock('Coastal_Rocks',(x,y,R.uniform(-.1,.8)),(R.uniform(1,2.5),R.uniform(1,2),R.uniform(1,2.8)))
for i in range(24):
    a=R.uniform(3.2,6.2);x,y=-23+15.6*math.cos(a),21+12.6*math.sin(a)
    rock('Cliff_Details',(x,y,18.3),(R.uniform(1.1,2.2),R.uniform(.7,1.3),R.uniform(3.5,5.8)),'WarmStone')
for a0,a1,z in [(3.3,6.1,7.0),(3.5,5.8,10.2)]:
    pts=[(-15+27*math.cos(a),15+21*math.sin(a),z+.2*math.sin(a*13)) for a in np.linspace(a0,a1,40)]
    line('Cliff_Details',pts,.13,'Chalk')

# Quay: stone blocks, a boardwalk edge and pier arms with piles, braces and cleats.
cube('Harbor_Quay',(15,-10,1.0),(27,15,3.6),'WarmStone',.8)
cube('Harbor_Quay',(15,-10,2.86),(26.6,14.6,.25),'Path',.25)
for x in np.arange(2.2,28.2,1.9):
    for z in [.1,1.3,2.4]:cube('Harbor_Masonry',(x,-17.46,z),(1.8,.38,.92),'CliffSand',.12)
for y in np.arange(-16.5,-3.5,1.9):
    for z in [.1,1.3,2.4]:cube('Harbor_Masonry',(28.3,y,z),(.4,1.8,.92),'CliffSand',.12)
def pier(cx,cy,length,width):
    for y in np.arange(cy-length/2,cy+length/2,.48):cube('Pier_Deck',(cx,y,2.03),(width,.43,.22),'TimberLight',.045)
    for x in [cx-width*.38,cx+width*.38]:
        cube('Pier_Structure',(x,cy,1.73),(.24,length+.1,.40),'Timber',.04)
        for y in np.arange(cy-length/2+.5,cy+length/2,3.3):
            cyl('Pier_Piles',(x,y,.12),.20,5.0,'Timber',12)
            cyl('Pier_Piles',(x,y,2.72),.25,.18,'Rope',16)
            rod('Pier_Structure',(x,y,1.8),(x,y+1.0,.0),.10,'Timber')
    for y in [cy-length/2+1,cy+length/2-1]:
        for x in [cx-width*.34,cx+width*.34]:
            cyl('Pier_Hardware',(x,y,2.4),.12,.48,'Iron',12);rod('Pier_Hardware',(x-.25,y,2.58),(x+.25,y,2.58),.08,'Iron')
pier(10,-26,21,4.4);pier(25,-24,16,3.6)
# End cross-head and horizontal join make a clear working harbor plan.
for x in np.arange(7.8,27.0,.48):cube('Pier_Deck',(x,-35.6,2.03),(.43,3.4,.22),'TimberLight',.045)
for x in [8,13,18,23,26]:cyl('Pier_Piles',(x,-36.8,.1),.22,5.0,'Timber',12)
for x in [11,20,25]:
    pts=[(x+.5*math.cos(t),-35.6+.5*math.sin(t),2.24+.015*t) for t in np.linspace(0,5*math.pi,80)]
    line('Fishing_Gear',pts,.045,'Rope')

# Switchback stairs. Treads, stone risers, landings and slim timber rails follow the slope.
def stairs(a,b,width=2.3):
    a,b=Vector(a),Vector(b);d=b-a;horizontal=Vector((d.x,d.y,0));dist=horizontal.length;u=horizontal.normalized();side=Vector((-u.y,u.x,0))
    steps=max(2,math.ceil(abs(d.z)/.22),math.ceil(dist/.48));theta=math.atan2(u.y,u.x)
    for i in range(steps):
        t=(i+.5)/steps;p=a+d*t
        cube('Stairs',(p.x,p.y,p.z-.15),(dist/steps+.06,width,.30),'Path',.06,theta)
    for s in [-1,1]:
        rail=[]
        for i in range(0,steps+1,max(1,steps//7)):
            p=a+d*(i/steps)+side*s*(width/2+.10)
            rod('Stair_Rails',p,p+Vector((0,0,1.0)),.075,'Timber');rail.append(tuple(p+Vector((0,0,1.02))))
        p=b+side*s*(width/2+.1);rail.append(tuple(p+Vector((0,0,1.02))))
        line('Stair_Rails',rail,.065,'TimberLight')
    for p in [a,b]:cube('Stairs',(p.x,p.y,p.z-.17),(2.7,2.7,.32),'Path',.12)
for a,b in [((8,-10,3.2),(1,-5,3.2)),((1,-5,3.2),(-10,-1,13)),((-10,-1,13),(-18,2,13)),((-18,2,13),(-30,7,19)),((-30,7,19),(-32,13,25)),((-32,13,25),(-25,16,25))]:stairs(a,b)
# Path stepping stones and flowering verges.
for i in range(22):
    x=-22+R.uniform(-7,7);y=18+R.uniform(-4,6)
    if (x+22)**2+(y-19)**2>27:rock('Garden_Stones',(x,y,25.05),(.6,.5,.12),'Path')

# Lighthouse profile: broad taper, cream/red bands, rounded cornices and a lantern gallery.
LX,LY=-22,19
cyl('Lighthouse_Foundation',(LX,LY,25.25),4.7,.55,'Chalk',64)
cyl('Lighthouse_Foundation',(LX,LY,25.64),4.1,.35,'WarmStone',64)
levels=[(25.8,29.0,'Chalk'),(29,32,'BrickRed'),(32,36.2,'Chalk'),(36.2,39.0,'BrickRed'),(39,43,'Chalk')]
for za,zb,ma in levels:
    ra=3.35-(za-25.8)*.055;rb=3.35-(zb-25.8)*.055
    cyl('Lighthouse_Tower',(LX,LY,(za+zb)/2),ra,zb-za,ma,64,rb)
for z,r in [(25.94,3.50),(28.95,3.25),(32,3.02),(39,2.69),(42.9,2.56)]:cyl('Lighthouse_Tower',(LX,LY,z),r,.17,'Chalk',64)
cyl('Lighthouse_Gallery',(LX,LY,43.27),3.6,.40,'WarmStone',64)
cyl('Lighthouse_Gallery',(LX,LY,43.51),3.68,.15,'Chalk',64)
for a in np.linspace(0,2*math.pi,32,endpoint=False):
    x,y=LX+3.3*math.cos(a),LY+3.3*math.sin(a);rod('Lighthouse_Gallery',(x,y,43.6),(x,y,44.65),.055,'Iron')
ring('Lighthouse_Gallery',(LX,LY,44.65),3.3,.075,'Iron');ring('Lighthouse_Gallery',(LX,LY,44.2),3.3,.035,'Iron')
cyl('Lighthouse_Lantern',(LX,LY,44.0),2.25,.65,'Copper',32)
# Open lantern has narrow glass panes and an emissive optic, without a solid opaque cylinder hiding it.
for i in range(12):
    a=i*math.pi/6;x,y=LX+2.15*math.cos(a),LY+2.15*math.sin(a)
    rod('Lighthouse_Lantern',(x,y,44.2),(x,y,46.8),.075,'Iron')
ring('Lighthouse_Lantern',(LX,LY,46.8),2.22,.1,'Copper')
for z in [44.6,45.0,45.4,45.8,46.2]:cyl('Lighthouse_Optic',(LX,LY,z),.68,.22,'Lamp',48)
cyl('Lighthouse_Lantern',(LX,LY,47.55),2.9,1.55,'Copper',48,.18)
cyl('Lighthouse_Lantern',(LX,LY,48.50),.15,.85,'Iron',16,.08)
sphere('Lighthouse_Lantern',(LX,LY,49.05),(.23,.23,.23),'Mustard')
# Door, arched crown, hinges, portholes and plaque.
cube('Lighthouse_Details',(LX,LY-3.25,27.15),(1.35,.18,2.5),'Copper',.14)
for x in [LX-.83,LX+.83]:cube('Lighthouse_Details',(x,LY-3.3,27.1),(.22,.3,2.9),'Chalk',.08)
pts=[(LX+.82*math.cos(a),LY-3.32,28.45+.82*math.sin(a)) for a in np.linspace(0,math.pi,20)]
line('Lighthouse_Details',pts,.14,'Chalk')
for z in [26.6,27.7]:cube('Lighthouse_Details',(LX-.42,LY-3.38,z),(.6,.08,.1),'Iron',.025)
sphere('Lighthouse_Details',(LX+.4,LY-3.4,27.1),(.10,.07,.10),'Mustard')
for z in [33.7,40.6]:
    r=3.35-(z-25.8)*.055
    o=cyl('Lighthouse_Details',(LX,LY-r-.03,z),.47,.13,'Window',32);o.rotation_euler.x=math.pi/2
    pts=[(LX+.52*math.cos(a),LY-r-.11,z+.52*math.sin(a)) for a in np.linspace(0,2*math.pi,40,endpoint=False)]
    line('Lighthouse_Details',pts,.10,'Chalk',True)
    rod('Lighthouse_Details',(LX-.42,LY-r-.15,z),(LX+.42,LY-r-.15,z),.035,'Copper')

def house(g,cx,cy,z,w,d,h,roof='RoofClay',wall='Chalk'):
    cube(g,(cx,cy,z+.24),(w+.5,d+.5,.48),'WarmStone',.18)
    cube(g,(cx,cy,z+h/2+.4),(w,d,h),wall,.22)
    # Gable and roof slopes, each tile is slightly crowned with rounded exposed edges.
    ridge=z+h+2.2;eave=z+h+.2
    v=[(cx-w/2,cy-d/2,z+h+.2),(cx+w/2,cy-d/2,z+h+.2),(cx,cy-d/2,ridge),
       (cx-w/2,cy+d/2,z+h+.2),(cx+w/2,cy+d/2,z+h+.2),(cx,cy+d/2,ridge)]
    mesh(g,v,[(0,1,2),(5,4,3),(0,3,4,1),(0,2,5,3),(1,4,5,2)],wall)
    for s in [-1,1]:
        dx=s*(w/2+.45);dz=eave-ridge;slope=math.sqrt(dx*dx+dz*dz)
        roofob=cube(g,(cx+dx/2,cy,(eave+ridge)/2),(slope,d+.9,.22),roof,.08)
        roofob.rotation_euler.y=-math.atan2(dz,dx) if s==1 else math.atan2(dz,-dx)
        # Explicit roof quad avoids depending on Euler sign for visible roof plane.
        mesh(g,[(cx,cy-d/2-.45,ridge+.08),(cx+dx,cy-d/2-.45,eave+.08),(cx+dx,cy+d/2+.45,eave+.08),(cx,cy+d/2+.45,ridge+.08)],[(0,1,2,3)],roof)
        for row in range(7):
            t=(row+.5)/7;x=cx+dx*t;zz=ridge+dz*t+.12
            for col in range(max(5,int(d/.55))):
                yy=cy-d/2+(col+.5)*(d/max(5,int(d/.55)))
                ob=cube(g,(x,yy,zz),(slope/7+.08,.52,.13),'RoofLight' if (col+row)%7==0 else roof,.07)
                ob.rotation_euler.y=-math.atan2(dz,abs(dx))*s
    rod(g,(cx,cy-d/2-.55,ridge+.2),(cx,cy+d/2+.55,ridge+.2),.15,roof)
    # Front facade trim, windows with muntins and shutters.
    for x in [cx-w*.28,cx+w*.28]:
        wz=z+h*.61
        cube(g,(x,cy-d/2-.06,wz),(1.14,.13,1.3),'Window',.10)
        for sx in [-.66,.66]:cube(g,(x+sx,cy-d/2-.14,wz),(.16,.15,1.6),'TimberLight',.035)
        for sz in [-.75,.75]:cube(g,(x,cy-d/2-.15,wz+sz),(1.45,.21,.15),'Chalk',.04)
        for sx in [-.96,.96]:
            cube(g,(x+sx,cy-d/2-.15,wz),(.45,.11,1.4),'Copper',.04)
            for sz in [-.4,0,.4]:cube(g,(x+sx,cy-d/2-.23,wz+sz),(.41,.06,.065),'SeaPaint',.02)
        rod(g,(x,cy-d/2-.15,wz-.58),(x,cy-d/2-.15,wz+.58),.035,'Chalk')
        rod(g,(x-.5,cy-d/2-.15,wz),(x+.5,cy-d/2-.15,wz),.035,'Chalk')
    cube(g,(cx,cy-d/2-.13,z+1.5),(1.1,.17,2.35),'SeaPaint',.12)
    cube(g,(cx,cy-d/2-.55,z+.22),(1.7,1.2,.35),'Path',.12)
    sphere(g,(cx+.32,cy-d/2-.27,z+1.5),(.07,.07,.07),'Mustard')
    cube(g,(cx+w*.27,cy+d*.22,z+h+1.3),(.85,.8,2.0),'WarmStone',.12)
    cube(g,(cx+w*.27,cy+d*.22,z+h+2.35),(1.05,.95,.18),'Chalk',.04)
    # Half round gutter and side wall little porthole.
    rod(g,(cx+w/2+.25,cy-d/2-.3,eave),(cx+w/2+.25,cy+d/2+.3,eave),.08,'Copper')
    rod(g,(cx+w/2+.25,cy+d/2,eave),(cx+w/2+.25,cy+d/2,z+.3),.07,'Copper')
house('Keeper_House_A',-12,5.0,13,7.7,6.2,4.0)
house('Keeper_House_B',-.8,15.2,13,6.5,5.2,3.6,'Copper')
house('Harbor_Boathouse',21.0,-7.2,3.1,7.0,5.7,3.7,'RoofClay','SeaPaint')
# Low workshop doors, awning and signboard evoke an active fishing place.
cube('Harbor_Details',(21,-10.25,4.75),(2.7,.18,2.9),'Timber',.12)
for x in np.linspace(19.8,22.2,9):cube('Harbor_Details',(x,-10.37,4.75),(.08,.08,2.65),'TimberLight',.02)
cube('Harbor_Details',(21,-10.5,6.6),(3.8,.22,.75),'Chalk',.12)
for x in [18.9,23.1]:rod('Harbor_Details',(x,-13,3.1),(x,-13,6.1),.09,'Timber')
mesh('Harbor_Details',[(18.7,-10.2,6.4),(23.3,-10.2,6.4),(23.3,-13.3,6.0),(18.7,-13.3,6.0)],[(0,1,2,3)],'Mustard')
for x in np.arange(18.9,23.2,.65):cube('Harbor_Details',(x,-13.3,5.9),(.28,.12,.35),'Chalk',.035)

# Garden fences, trellises, salt-shaped shrubs and flower pots.
def fence(points,z):
    for x,y in points:rod('Garden_Fences',(x,y,z),(x,y,z+1.05),.075,'Chalk')
    for dz in [.4,.85]:line('Garden_Fences',[(x,y,z+dz) for x,y in points],.055,'Chalk')
fence([(-18+i*.8,8.7) for i in range(17)],13)
fence([(-5,10+i*.8) for i in range(10)],13)
for cx,cy,z in [(-17,1.3,13),(-7,1.3,13),(-3,11.9,13),(2,11.9,13),(-28,18,25),(-17,18,25),(17,-11,3.1),(25,-11,3.1)]:
    cyl('Garden_Pots',(cx,cy,z+.35),.45,.65,'RoofClay',20,.55)
    for k in range(5):
        xx,yy=cx+R.uniform(-.35,.35),cy+R.uniform(-.35,.35)
        sphere('Garden_Pots',(xx,yy,z+.8),(.35,.3,.35),'GrassLight')
        sphere('Garden_Pots',(xx,yy,z+1.06),(.10,.10,.10),'Flower')
for i in range(40):
    a=R.uniform(.1,3.1);x,y=-7+R.uniform(24,33)*math.cos(a),7+R.uniform(23,29)*math.sin(a)
    for k in range(3):sphere('Coastal_Vegetation',(x+R.uniform(-.5,.5),y+R.uniform(-.5,.5),3.6),(R.uniform(.6,1.2),R.uniform(.5,1),R.uniform(.5,1)),'GrassLight' if k==0 else 'Grass')
# Four windswept pines, clustered canopies with characteristic sideways lean.
for x,y,z,sz in [(-35,26,25,1),(-30,30,25,.85),(-3,27,13,1),(7,12,3.2,1.25),(-26,-8,3.2,.9),(-31,-2,3.2,.8)]:
    rod('Coastal_Trees',(x,y,z),(x+.65*sz,y,z+4.3*sz),.20*sz,'Timber')
    for k in range(4):
        p=(x+(k*.5-.4)*sz,y+(k%2-.5)*sz,z+(3.5+.4*(k%2))*sz)
        rod('Coastal_Trees',(x+.4*sz,y,z+2.8*sz),p,.09*sz,'Timber')
        sphere('Coastal_Trees',p,(1.8*sz,1.3*sz,.85*sz),'Grass' if k%2 else 'GrassLight')

# Hull with separate curved sheer, inner bulwark, ribs, seats, oars and painted waterline.
def boat(g,cx,cy,ang,length=7.3,width=2.5,color='BrickRed',cabin=False):
    co,si=math.cos(ang),math.sin(ang)
    def tr(p):return (cx+p[0]*co-p[1]*si,cy+p[0]*si+p[1]*co,p[2])
    N=32;outline=[]
    for i in range(N):
        a=i*2*math.pi/N
        # pointed bow, rounded stern, full middle
        xx=length*.5*math.cos(a); yy=width*.5*math.sin(a)*(1-.23*math.cos(a))
        outline.append((xx,yy))
    v=[]
    for scale,z in [(.55,.00),(.91,.36),(1,1.2),(.91,1.13),(.70,.28)]:
        for x,y in outline:v.append(tr((x*scale,y*scale,z+.20*(x/(length*.5))**4)))
    f=[]
    for j in range(4):
        for i in range(N):f.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
    f.append(tuple(range(4*N,5*N)));ob=mesh(g,v,f,color,True);bevel(ob,.035)
    for scale,z,ma,r in [(1.0,1.22,'Chalk',.10),(.92,.42,'Mustard',.055),(.82,.25,'Timber',.055)]:
        line(g,[tr((x*scale,y*scale,z+.20*(x/(length*.5))**4)) for x,y in outline],r,ma,True)
    for x in [-length*.25,0,length*.25]:
        o=cube(g,tr((x,0,.77)),(.40,width*.79,.15),'TimberLight',.06);o.rotation_euler.z=ang
    for s in [-1,1]:
        for x in [-length*.3,-length*.12,length*.1,length*.27]:
            line(g,[tr((x,s*width*.28,.35)),tr((x,s*width*.40,.65)),tr((x,s*width*.46,1.12))],.055,'TimberLight')
    if cabin:
        o=cube(g,tr((-1,0,1.65)),(2,1.7,1.8),'Chalk',.15);o.rotation_euler.z=ang
        o=cube(g,tr((-1,0,2.63)),(2.35,2.0,.25),'SeaPaint',.12);o.rotation_euler.z=ang
        for s in [-1,1]:
            o=cube(g,tr((-1,s*.86,1.95)),(1.3,.06,.65),'Window',.04);o.rotation_euler.z=ang
        rod(g,tr((.9,0,1)),tr((.9,0,4.1)),.07,'Timber')
        rod(g,tr((.9,-1,3.65)),tr((.9,1,3.65)),.045,'Timber')
        line(g,[tr((.9,-1,3.65)),tr((1.7,-.6,2.7)),tr((1.9,-.5,1.1))],.025,'Rope')
        mesh(g,[tr((.92,0,4.1)),tr((1.75,0,3.85)),tr((.92,0,3.65))],[(0,1,2)],'Mustard')
    else:
        rod(g,tr((-1.8,-.6,1.3)),tr((1.3,.8,1.35)),.05,'TimberLight')
        o=cube(g,tr((1.45,.86,1.36)),(.55,.22,.06),'TimberLight',.03);o.rotation_euler.z=ang+.42
    # Fender rope and buoy on outward side.
    line(g,[tr((0,width*.48,1.22)),tr((.1,width*.60,.85))],.025,'Rope')
    sphere(g,tr((.1,width*.6,.65)),(.16,.18,.4),'Foam')
boat('Boat_Fishing',17,-26,.95,7.6,2.6,'BrickRed',True)
boat('Boat_Blue',4.5,-26,1.6,6.7,2.3,'SeaPaint')
boat('Boat_Dinghy',31,-26,1.35,5.4,2,'Mustard')
boat('Boat_At_Sea',35,10,-.65,7.2,2.5,'SeaPaint',True)
# Mooring lines visibly connect boats and pier cleats.
for p,q in [((17.8,-23,1.4),(11.5,-22.5,2.6)),((16,-28.7,1.4),(11.5,-29.5,2.6)),((4.5,-23.3,1.3),(8.5,-23,2.6)),((30.4,-23.5,1.3),(26,-23,2.6))]:
    midp=((p[0]+q[0])/2,(p[1]+q[1])/2,(p[2]+q[2])/2-.35);line('Mooring_Ropes',[p,midp,q],.035,'Rope')

def crate(x,y,z,scale=1):
    cube('Fishing_Crates',(x,y,z+.45*scale),(.95*scale,.85*scale,.9*scale),'Timber',.06)
    for side in [-1,1]:
        for zz in [.12,.45,.78]:cube('Fishing_Crates',(x,y+side*.44*scale,z+zz*scale),(1.0*scale,.08*scale,.21*scale),'TimberLight',.025)
        for xx in [-.38,.38]:cube('Fishing_Crates',(x+xx*scale,y+side*.46*scale,z+.45*scale),(.10*scale,.08*scale,.95*scale),'TimberLight',.025)
    for xx in [-.36,0,.36]:cube('Fishing_Crates',(x+xx*scale,y,z+.94*scale),(.30*scale,.84*scale,.07*scale),'TimberLight',.02)
for x,y,z in [(13,-12,3.1),(14.1,-12,3.1),(13.2,-12,4.05),(26,-8,3.1),(26,-9.1,3.1),(10,-32,2.2),(24.7,-18,2.2),(7.4,-16,3.1)]:crate(x,y,z)
for x,y,z in [(16,-12,3.1),(17,-12.5,3.1),(24.5,-12,3.1),(11,-17,2.2)]:
    cyl('Fishing_Barrels',(x,y,z+.55),.44,1.10,'Timber',20,.38)
    for zz in [.18,.85]:ring('Fishing_Barrels',(x,y,z+zz),.44,.045,'Iron')
    cyl('Fishing_Barrels',(x,y,z+1.12),.38,.055,'TimberLight',20)
# Lobster pots: thin hoop cages and square knotted net draped over the drying frame.
for x,y,z in [(13,-15,3.1),(14.5,-15,3.1),(9,-30,2.2)]:
    for yy in np.linspace(y-.45,y+.45,6):
        line('Fishing_Gear',[(x+.55*math.cos(a),yy,z+.55*math.sin(a)) for a in np.linspace(0,math.pi,16)],.025,'Rope')
    for a in np.linspace(0,math.pi,10):rod('Fishing_Gear',(x+.55*math.cos(a),y-.45,z+.55*math.sin(a)),(x+.55*math.cos(a),y+.45,z+.55*math.sin(a)),.018,'Rope')
for x in [3.5,7.0]:rod('Fishing_Net',(x,-9,3.2),(x,-9,5.5),.09,'Timber')
rod('Fishing_Net',(3.4,-9,5.5),(7.1,-9,5.5),.075,'TimberLight')
for x in np.linspace(3.55,6.95,16):line('Fishing_Net',[(x,-9,5.45),(x,-9.2,4.6),(x,-9.5,3.4)],.013,'Rope')
for z in np.linspace(3.5,5.4,10):line('Fishing_Net',[(x,-9-(5.45-z)*.25,z-.12*math.sin((x-3.5)*math.pi/3.5)) for x in np.linspace(3.55,6.95,20)],.013,'Rope')
for x,y,z in [(8,-17,3.1),(27,-14,3.1),(9,-31,2.2),(24,-21,2.2)]:
    rod('Harbor_Buoys',(x,y,z),(x,y,z+1.1),.03,'Rope')
    sphere('Harbor_Buoys',(x,y,z+.42),(.26,.26,.38),'BrickRed');sphere('Harbor_Buoys',(x,y,z+.8),(.20,.20,.20),'Foam')
for x,y in [(38,-8),(36,-36),(-19,-32)]:
    cyl('Channel_Buoys',(x,y,.05),.55,.50,'BrickRed',20,.34)
    rod('Channel_Buoys',(x,y,.2),(x,y,1.3),.06,'Iron')
    cyl('Channel_Buoys',(x,y,1.25),.23,.32,'Mustard',20,.12)

# Harbor lanterns: physical small glass lamps, crooked-arm posts and base collars.
for x,y,z in [(3,-15,3.1),(27,-16,3.1),(10,-34,2.2),(-17,2,13),(-31,14,25)]:
    rod('Harbor_Lamps',(x,y,z),(x,y,z+3.2),.085,'Iron')
    line('Harbor_Lamps',[(x,y,z+3.2),(x+.2,y,z+3.55),(x+.65,y,z+3.55),(x+.8,y,z+3.25)],.075,'Iron')
    cube('Harbor_Lamps',(x+.8,y,z+3.05),(.35,.35,.5),'Lamp',.04)
    cyl('Harbor_Lamps',(x+.8,y,z+3.38),.30,.2,'Copper',8,.12)
    for sx in [-.2,.2]:rod('Harbor_Lamps',(x+.8+sx,y-.2,z+2.75),(x+.8+sx,y-.2,z+3.3),.025,'Iron')

# White foam curls, broken wake dashes and faint elongated swells are authored geometry.
for i in range(14):
    a0=3.4+i*.18;pts=[]
    for a in np.linspace(a0,a0+.13,12):pts.append((-7+40*math.cos(a),7+35*math.sin(a),.11+.02*math.sin(a*20)))
    if all(abs(x)<49 and abs(y)<49 for x,y,z in pts):line('Shore_Foam',pts,.14,'Foam')
for i in range(35):
    x=R.uniform(-44,44);y=R.uniform(-44,42)
    if ((x+7)/41)**2+((y-7)/36)**2<1.08:continue
    pts=[(x+t,y+.15*math.sin(t*1.2),.08) for t in np.linspace(-R.uniform(.4,1.7),R.uniform(.4,1.5),10)]
    if all(abs(xx)<49 for xx,yy,zz in pts):line('Sea_Ripples',pts,R.uniform(.025,.06),'Foam')
for s in [-1,1]:
    line('Boat_Wake',[(34+s*(.9+i*.22),12+i*.5,.1) for i in range(13)],.08,'Foam')
# Warm seagull silhouettes over the side water, away from the lighthouse focal point.
for x,y,z in [(16,22,23),(20,24,24.3),(26,20,22.6)]:
    line('Seabirds',[(x-.85,y,z+.1),(x-.45,y,z+.36),(x,y,z),(x+.45,y,z+.35),(x+.9,y,z+.05)],.07,'Chalk')

# Join semantic modules, recalculate normals, project repeat UVs at material-specific metre scale.
records=[]
for g,objs in GROUPS.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object;o.name=g
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free()
    uv=o.data.uv_layers.new(name='Surface_metres')
    density=[]
    for p in o.data.polygons:
        ma=o.data.materials[p.material_index].name;tile=palette[ma]['tile_metres'];n=p.normal;axis=max(range(3),key=lambda k:abs(n[k]));axes=[k for k in range(3) if k!=axis]
        for li in p.loop_indices:
            co=o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv=(co[axes[0]]/tile,co[axes[1]]/tile)
        density.append(512/tile*math.sqrt(abs(n[axis])))
    pts=[v.co for v in o.data.vertices];low=[min(p[i] for p in pts) for i in range(3)];high=[max(p[i] for p in pts) for i in range(3)]
    records.append({'name':g,'bounds_m':[low,high],'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),
      'materials':[m.name for m in o.data.materials],'uv_density_px_per_m_min':min(density),'uv_density_px_per_m_max':max(density)})
    bpy.ops.export_scene.fbx(filepath=str(FBX/(g+'.fbx')),use_selection=True,apply_unit_scale=True,global_scale=1.0,
        axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,
        object_types={'MESH'},path_mode='STRIP')

# Saved original is inspectable and self-contained; images also remain as separate PNG originals.
bpy.ops.object.select_all(action='DESELECT')
bpy.context.scene.world.color=(.22,.26,.31)
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'harbor.blend'))
(ART/'palette.json').write_text(json.dumps(palette,indent=2),encoding='utf-8')
(ART/'mesh_manifest.json').write_text(json.dumps({'seed':42713,'unit':'metre','meshes':records,
  'textures':'512x512 analytic periodic sine harmonics, authored here with NumPy and saved by Blender; no external imagery',
  'uv':'dominant plane per polygon, scaled by material tile metres. Repeat overlaps intentional; not atlas unwrap. No unique bake UV.',
  'padding':'tileable full-image surfaces; island padding not applicable. Projection seams and curved-face density loss documented.',
  'beacon_origin_m':[LX,LY,45.5]},indent=2),encoding='utf-8')
print('AUTHOR_SCENE_COMPLETE',len(records),'meshes',sum(r['polygons'] for r in records),'polygons')
