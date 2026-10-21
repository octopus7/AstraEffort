import bpy, math, random, json, os
from mathutils import Vector
from collections import defaultdict

ROOT=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra'
OUT=ROOT+'/SourceArt'
os.makedirs(OUT,exist_ok=True)
random.seed(87241)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
groups=defaultdict(list)
palette={
'Meadow':('#7F9171',.95),'MeadowLight':('#95A17B',.96),'Earth':('#6E7966',1),
'Stone':('#969D91',.9),'StoneLight':('#B8B6A1',.86),'StoneDark':('#727C76',.94),
'Gravel':('#AFA38B',.98),'Ballast':('#777F78',1),'Timber':('#685749',.9),
'WoodLight':('#A59170',.82),'Sage':('#7F9D91',.84),'SageDark':('#557C74',.85),
'Cream':('#E0D7B9',.78),'Roof':('#B57960',.83),'RoofLight':('#C48A6D',.8),
'Metal':('#435955',.54),'Rail':('#8C9993',.4),'Glass':('#466A73',.26),
'Pine':('#527B6C',.94),'PineLight':('#668873',.95),'PineDark':('#3C665B',.94),
'Mustard':('#CEAE65',.78),'Luggage':('#9B6656',.8),'Ink':('#354D49',.8),
'Lamp':('#F3D99B',.5),'Interior':('#263D39',1),'Flower':('#C4B58A',1)}
mats={}
def srgb(h):
    a=[int(h[i:i+2],16)/255 for i in (1,3,5)]
    return [v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in a]
for name,(col,rough) in palette.items():
    m=bpy.data.materials.new(name); m.diffuse_color=(*srgb(col),1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*srgb(col),1); bs.inputs['Roughness'].default_value=rough
    mats[name]=m
def finish(o,g,mat,bevel=0,smooth=False):
    o.data.materials.append(mats[mat]); groups[g].append(o)
    if bevel:
        b=o.modifiers.new('Soft crafted edges','BEVEL'); b.width=bevel; b.segments=2
        bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=b.name)
        n=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL'); n.keep_sharp=True
        bpy.ops.object.modifier_apply(modifier=n.name)
    if smooth:
        for p in o.data.polygons:p.use_smooth=True
    return o
def box(g,loc,scale,mat,bevel=.04,rot=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.rotation_euler[2]=rot
    return finish(o,g,mat,bevel)
def mesh(g,verts,faces,mat,smooth=False):
    me=bpy.data.meshes.new(g);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(g,me);bpy.context.collection.objects.link(o)
    return finish(o,g,mat,0,smooth)
def uv(g,loc,scale,mat,segments=12,rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1,location=loc);o=bpy.context.object;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,g,mat,0,True)
def cyl(g,loc,radius,depth,mat,vertices=12,rot=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc);o=bpy.context.object
    if rot:o.rotation_euler=rot
    return finish(o,g,mat,min(.035,radius*.15),True)
def beam(g,a,b,width,mat,depth=None):
    d=Vector(b)-Vector(a);o=box(g,(Vector(a)+Vector(b))/2,(width,depth or width,d.length),mat,min(width*.18,.035));o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return o
def text(g,s,loc,size,mat,rotation=(math.pi/2,0,0),align='CENTER'):
    cu=bpy.data.curves.new('Lettering','FONT');cu.body=s;cu.size=size;cu.align_x=align;cu.align_y='CENTER';cu.extrude=.006;cu.bevel_depth=.002;cu.bevel_resolution=1
    o=bpy.data.objects.new('Lettering',cu);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=rotation;o.scale.x=-1
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False);return finish(o,g,mat)
def track_y(x):return -9+.012*(x+3)**2
def track_z(x):return .82+.0015*max(0,abs(x)-18)**2
def ground(x,y):
    h=.3+15*math.exp(-((x+28)/19)**2-((y-32)/20)**2)+12*math.exp(-((x-36)/18)**2-((y-30)/22)**2)+6*math.exp(-((x-42)/12)**2-((y-6)/13)**2)
    h+=.22*math.sin(x*.17)*math.cos(y*.13)
    # Spacious station clearing and carefully graded railway cutting.
    clearing=math.exp(-((x+2)/20)**6-((y-5)/17)**6)
    h=h*(1-clearing)+.38*clearing
    access=math.exp(-((x+23.5)/10)**8-((y-.5)/3.5)**8)
    h=h*(1-access)+.38*access
    approach=math.exp(-((x+23.5)/10)**8-((y-(5-(x+30)*3/13))/3.5)**8)
    h=h*(1-approach)+.38*approach
    d=abs(y-track_y(x));cut=math.exp(-(d/4.6)**6)
    h=h*(1-cut)+(track_z(x)-.55)*cut
    return h
# Heightfield with layered skirt, exactly 100m square.
N=100;vs=[];fs=[]
for j in range(N+1):
    for i in range(N+1):
        x=i-50;y=j-50;vs.append((x,y,ground(x,y)))
for j in range(N):
    for i in range(N):
        a=j*(N+1)+i;fs.append((a,a+1,a+N+2,a+N+1))
terrain=mesh('Terrain',vs,fs,'Meadow',True)
# Sparse surface color variation at terrain polygon level.
terrain.data.materials.append(mats['MeadowLight'])
for p in terrain.data.polygons:
    co=p.center
    if random.random()<.055:p.material_index=1
edge=[]
for i in range(N+1):edge.append((i-50,-50))
for i in range(1,N+1):edge.append((50,i-50))
for i in range(1,N+1):edge.append((50-i,50))
for i in range(1,N):edge.append((-50,50-i))
vv=[]
for x,y in edge:vv.extend([(x,y,ground(x,y)),(x,y,-1.8),(x*.992,y*.992,-2.2)])
ff=[]
for i in range(len(edge)):
    k=(i+1)%len(edge)
    ff.extend([(3*i,3*k,3*k+1,3*i+1),(3*i+1,3*k+1,3*k+2,3*i+2)])
mesh('TerrainSkirt',vv,ff,'Earth')
def ribbon(g,points,width,mat,thickness=.04):
    verts=[];faces=[]
    for i,p in enumerate(points):
        d=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)]);n=Vector((-d.y,d.x,0)).normalized()*width/2
        verts.extend([tuple(Vector(p)-n),tuple(Vector(p)+n)])
    for i in range(len(points)-1):faces.append((i*2,i*2+1,i*2+3,i*2+2))
    o=mesh(g,verts,faces,mat)
    if thickness:
        so=o.modifiers.new('Solid rim','SOLIDIFY');so.thickness=thickness;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=so.name)
    return o
xs=[-50+i*.25 for i in range(401)]
ribbon('Ballast',[(x,track_y(x),track_z(x)-.14) for x in xs],3.5,'Ballast',.22)
for x in [-49.5+i*.68 for i in range(147)]:
    t=math.atan(.024*(x+3));box('Sleepers',(x,track_y(x),track_z(x)),(.23,2.55,.16),'Timber',.035,t)
    if x<30:
        for s in (-1,1):
            n=Vector((-math.sin(t),math.cos(t),0))*s*.76
            box('RailFasteners',(x+n.x,track_y(x)+n.y,track_z(x)+.105),(.30,.23,.035),'Metal',.012,t)
for side in (-1,1):
    pts=[]
    for x in xs:
        t=math.atan(.024*(x+3));pts.append((x-math.sin(t)*.76*side,track_y(x)+math.cos(t)*.76*side,track_z(x)+.20))
    ribbon('Rails',pts,.10,'Rail',.13)
    ribbon('Rails',[(x,y,z-.10) for x,y,z in pts],.17,'Metal',.03)
# Platform: gently bowed edge echoes the rail while a wide apron holds circulation.
px=[-17+i*.5 for i in range(69)]; pv=[]
for x in px:pv.extend([(x,track_y(x)+2.25,1.52),(x,3.9,1.52),(x,track_y(x)+2.25,.35),(x,3.9,.35)])
pf=[]
for i in range(len(px)-1):
    a=i*4;b=a+4;pf.extend([(a,b,b+1,a+1),(a+2,b+2,b,a),(a+1,b+1,b+3,a+3)])
pf.extend([(0,1,3,2),(len(pv)-4,len(pv)-2,len(pv)-1,len(pv)-3)])
mesh('Platform',pv,pf,'Stone')
ribbon('PlatformCoping',[(x,track_y(x)+2.46,1.57) for x in px],.44,'Cream',.13)
ribbon('PlatformCoping',[(x,track_y(x)+2.90,1.59) for x in px],.10,'Mustard',.02)
for x in range(-16,17):
    box('Paving',(x,1.8,1.55),(.97,3.8,.055),'StoneLight',.015)
    if x%2==0:
        for j in range(3):box('Paving',(x,track_y(x)+3.25+j*.15,1.6),(.055,.075,.022),'Mustard',.006)
# Arrival footpath and an accessible 1:12 ramp to the platform at the west.
rv=[(-30,-1,.4),(-30,2,.4),(-17,2,1.52),(-17,-1,1.52),(-30,-1,.25),(-30,2,.25),(-17,2,.25),(-17,-1,.25)]
rv=[(x,y+4.5-(x+30)*3/13,z) for x,y,z in rv]
mesh('AccessRamp',rv,[(3,2,1,0),(1,5,4,0),(2,6,5,1),(7,6,2,3),(4,7,3,0)],'StoneLight')
for y in (-1.08,2.08):
    for x in [-29.5,-26.5,-23.5,-20.5,-17.5]:
        z=.4+(x+30)/13*1.12;yy=y+4.5-(x+30)*3/13;beam('Railings',(x,yy,z),(x,yy,z+1.05),.07,'Metal')
    beam('Railings',(-30,y+4.5,1.45),(-17,y+1.5,2.57),.075,'Metal')
path=[(-45,-33),(-36,-21),(-31,-10),(-26,1),(-23,10),(-16,16),(-7,17),(4,16),(14,19),(20,27),(17,34),(7,37),(-2,32),(-6,25),(-7,17)]
def catmull(points):
    out=[]; pp=[points[0]]+points+[points[-1]]
    for i in range(1,len(pp)-2):
        p0,p1,p2,p3=[Vector(v) for v in pp[i-1:i+3]]
        for j in range(15):
            t=j/15;v=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t);out.append(tuple(v))
    out.append(tuple(points[-1]));return out
walkpts=catmull(path)
ribbon('Footpath',[(x,y,ground(x,y)+.055) for x,y in walkpts],2.1,'Gravel',.025)
# Main station at (-5,7), front looks south.
bx=-5;by=7.3;base=1.55
box('StationStone',(bx,by,base+.30),(12.4,6.5,.6),'StoneLight',.10)
box('StationWalls',(bx,by,3.55),(11.8,5.9,3.4),'Sage',.10)
# Fine horizontal timber weatherboards with continuous corner trims.
for z in [2.0+i*.23 for i in range(14)]:
    box('StationCladding',(bx,4.31,z),(11.8,.07,.055),'SageDark',.012)
    for x in (-10.96,.96):box('StationCladding',(x,by,z),(.07,5.9,.055),'SageDark',.012)
for x in (-10.85,.85):
    for y in (4.3,10.3):box('StationTrim',(x,y,3.65),(.19,.20,3.6),'Cream',.025)
# Gable ends and pitched roof, ridge follows X.
for x in (-10.9,.9):
    mesh('StationWalls',[(x,4.35,5.25),(x,10.25,5.25),(x,7.3,7.0)],[(0,1,2)],'Sage')
angle=math.atan2(1.9,3.75)
for side in (-1,1):
    o=box('StationRoof',(bx,7.3+side*1.875,6.2),(13.1,math.hypot(3.75,1.9),.18),'Roof',.075);o.rotation_euler[0]=-side*angle
    for x in [-11.2+i*.52 for i in range(25)]:beam('RoofSeams',(x,7.3,7.21),(x,7.3+side*3.8,5.29),.038,'RoofLight',.045)
beam('RoofSeams',(-11.65,7.3,7.25),(1.65,7.3,7.25),.19,'RoofLight',.20)
for x in (-11.55,1.55):
    for side in (-1,1):beam('StationTrim',(x,7.3,7.08),(x,7.3+side*3.85,5.13),.19,'Cream',.16)
# Door, windows, mullions, sills.
box('StationDoors',(-5,4.23,2.94),(1.42,.15,2.7),'Cream',.06)
box('StationDoors',(-5,4.13,2.94),(1.19,.10,2.48),'SageDark',.03)
box('StationGlass',(-5,4.065,3.39),(.89,.035,1.25),'Glass',.025)
beam('StationTrim',(-5,4.02,2.77),(-5,4.02,4.0),.05,'Cream')
cyl('StationDoors',(-4.6,4.00,2.65),.055,.12,'Mustard',12,(math.pi/2,0,0))
for x in (-9,-1.2):
    box('StationTrim',(x,4.17,3.55),(2.05,.20,1.9),'Cream',.05)
    box('StationGlass',(x,4.045,3.55),(1.78,.035,1.64),'Glass',.03)
    for dx in (-.43,.43):box('StationTrim',(x+dx,3.995,3.55),(.055,.065,1.7),'Cream',.01)
    box('StationTrim',(x,3.99,3.55),(1.85,.07,.055),'Cream',.01)
    box('StationTrim',(x,3.98,2.59),(2.28,.45,.12),'Cream',.025)
for y in (6,8.7):
    box('StationTrim',(1.02,y,3.55),(.2,1.75,1.9),'Cream',.04)
    box('StationGlass',(1.13,y,3.55),(.035,1.48,1.64),'Glass',.025)
    box('StationTrim',(1.16,y,3.55),(.05,.07,1.7),'Cream',.01)
    box('StationTrim',(1.16,y,3.55),(.05,1.5,.07),'Cream',.01)
# Stone chimney and canopy, structural brackets and posts.
box('StationStone',(-8.6,8.5,6.9),(.85,.85,2),'StoneLight',.07)
box('StationTrim',(-8.6,8.5,7.94),(1.08,1.08,.22),'StoneDark',.05)
o=box('Canopy',(-5,2.3,4.7),(14,3.7,.15),'Roof',.06);o.rotation_euler[0]=.09
for x in (-11.3,-7.1,-2.9,1.3):
    box('Canopy',(x,.75,3.08),(.19,.19,3.05),'Cream',.025)
    beam('Canopy',(x,.75,3.9),(x,1.45,4.58),.13,'SageDark')
    beam('Canopy',(x,.75,4),(x+.65,.75,4.53),.13,'SageDark')
beam('Canopy',(-11.7,.75,4.55),(1.7,.75,4.55),.19,'Cream')
# Station name suspended under canopy edge.
box('Signage',(-5,.57,4.12),(3.4,.16,.58),'SageDark',.07)
text('Lettering','ALDER PASS',(-5,.475,4.11),.34,'Cream')
box('Signage',(1.37,.57,3.6),(.62,.16,.66),'Mustard',.05);text('Lettering','01',(1.37,.47,3.6),.4,'Ink')
# Clock on east gable, visible from platform arrival.
cyl('Clock',(1.17,7.3,5.65),.65,.12,'Metal',48,(0,math.pi/2,0))
cyl('Clock',(1.25,7.3,5.65),.56,.03,'Cream',48,(0,math.pi/2,0))
for i in range(12):
    a=i*math.pi/6;beam('Clock',(1.28,7.3+math.sin(a)*.45,5.65+math.cos(a)*.45),(1.28,7.3+math.sin(a)*.5,5.65+math.cos(a)*.5),.035,'Ink')
beam('Clock',(1.31,7.3,5.65),(1.31,7.05,5.85),.05,'Ink');beam('Clock',(1.31,7.3,5.65),(1.31,7.49,6.03),.04,'Ink')
# Platform freestanding station nameboard.
for x in (8,12):box('Signage',(x,-3.1,2.8),(.13,.13,2.5),'Metal',.025)
box('Signage',(10,-3.1,3.55),(4.5,.19,.9),'Cream',.07)
box('Signage',(10,-3.215,3.55),(4.25,.06,.69),'SageDark',.035)
text('Lettering','ALDER PASS',(10,-3.26,3.60),.37,'Cream');text('Lettering','ELEV. 1280 m',(10,-3.26,3.30),.16,'Cream')
# Benches with shaped back, slatted seat, metal legs.
def bench(x,y,z,rot=0):
    tmp=[];start=set(bpy.data.objects)
    for dx in (-.87,.87):
        for dy in (-.24,.24):box('Benches',(dx,dy,.23),(.10,.10,.46),'Metal',.025)
        beam('Benches',(dx,.27,.1),(dx,.37,1.08),.09,'Metal')
    for dy in (-.25,-.08,.09,.26):box('Benches',(0,dy,.48),(2.15,.13,.11),'WoodLight',.04)
    for zz in (.75,.98):box('Benches',(0,.36,zz),(2.15,.11,.16),'WoodLight',.035)
    for o in set(bpy.data.objects)-start:
        p=o.location.copy();o.location=(x+p.x*math.cos(rot)-p.y*math.sin(rot),y+p.x*math.sin(rot)+p.y*math.cos(rot),z+p.z);o.rotation_euler[2]+=rot
for p in [(-8,-.7,1.6),(0,-.7,1.6),(13,1.5,1.6),(-1,31,ground(-1,31))]:bench(*p)
def lamp(x,y,z):
    cyl('Lamps',(x,y,z+.12),.27,.24,'Metal');cyl('Lamps',(x,y,z+1.9),.07,3.8,'Metal')
    beam('Lamps',(x,y,z+3.7),(x,y-.52,z+3.7),.08,'Metal')
    box('Lamps',(x,y-.52,z+3.42),(.38,.38,.48),'Lamp',.07)
    box('Lamps',(x,y-.52,z+3.73),(.56,.56,.13),'Metal',.07)
    for dx in (-.17,.17):
        for dy in (-.17,.17):beam('Lamps',(x+dx,y-.52+dy,z+3.17),(x+dx,y-.52+dy,z+3.67),.035,'Metal')
    box('Lamps',(x,y-.52,z+3.15),(.44,.44,.1),'Metal',.025)
for p in [(-15,-2.8,1.6),(5,-3.5,1.6),(15,-1.8,1.6),(-26,3,ground(-26,3))]:lamp(*p)
# Luggage clusters and a timetable cabinet.
for x,y,z,s,mat in [(-7.2,-.4,1.65,.72,'Luggage'),(-6.8,-.2,2.13,.5,'Mustard'),(.7,-.6,1.65,.62,'SageDark')]:
    box('Luggage',(x,y,z+s*.34),(s,s*.47,s*.65),mat,.09)
    for dx in (-s*.3,s*.3):box('Luggage',(x+dx,y-.01,z+s*.34),(.045,s*.49,s*.67),'Timber',.01)
    beam('Luggage',(x-s*.14,y,z+s*.70),(x+s*.14,y,z+s*.70),.035,'Metal')
box('Timetable',(-10.05,3.98,3.4),(.8,.15,1.35),'Metal',.035);box('Timetable',(-10.05,3.89,3.4),(.68,.04,1.2),'Cream',.015)
text('Lettering','DEPARTURES',(-10.05,3.86,3.84),.085,'Ink')
for i,s in enumerate(['08:15 NORTH','10:40 RIDGE','14:20 VALLEY','17:05 NORTH']):text('Lettering',s,(-10.05,3.86,3.59-i*.19),.065,'Ink')
# Freight shed with open front, boxed cargo, handcart and sacks.
fx=17;fy=7
box('FreightShed',(fx,fy,.78),(7,5,.75),'Stone',.08)
for x in (13.7,20.3):box('FreightShed',(x,fy,2.5),(.18,4.7,3),'SageDark',.04)
box('FreightShed',(fx,9.3,2.5),(6.6,.18,3),'SageDark',.04)
o=box('FreightShed',(fx,7,4.16),(7.7,5.6,.22),'Roof',.08);o.rotation_euler[0]=.10
for x in (13.7,20.3):box('FreightShed',(x,4.7,2.55),(.18,.18,3.1),'Cream',.035)
box('Signage',(17,4.35,3.73),(2.1,.12,.45),'Cream',.04);text('Lettering','FREIGHT',(17,4.27,3.73),.25,'Ink')
def crate(x,y,z,s=1):
    box('Cargo',(x,y,z+s*.5),(s,s*.85,s),'WoodLight',.055)
    for dz in (.12,.85):
        box('Cargo',(x,y-s*.44,z+s*dz),(s*1.04,.055,.09),'Timber',.015)
        box('Cargo',(x+s*.52,y,z+s*dz),(.055,s*.91,.09),'Timber',.015)
    for dx in (-.32,.32):box('Cargo',(x+dx*s,y-s*.44,z+s*.5),(.07,.06,s*.9),'Timber',.012)
    beam('Cargo',(x-s*.42,y-s*.48,z+s*.17),(x+s*.42,y-s*.48,z+s*.82),.06,'Timber')
for args in [(14.6,7.8,1.17,1.1),(15.8,7.9,1.17,1.0),(14.7,7.8,2.27,.8),(18.5,7.6,1.17,1.2),(20.9,4,.44,.9),(21.8,4.1,.44,.8)]:crate(*args)
for i in range(5):uv('Cargo',(18.8+(i%2)*.65,5.8+(i//2)*.55,1.55),(.4,.32,.5),'Cream')
box('Handcart',(10.8,5.3,.89),(2.1,1.1,.16),'WoodLight',.05)
for x in (10.1,11.5):
    for y in (4.72,5.88):cyl('Handcart',(x,y,.66),.31,.10,'Metal',20,(math.pi/2,0,0))
beam('Handcart',(11.6,5,.92),(12.8,5,1.3),.08,'Timber');beam('Handcart',(11.6,5.6,.92),(12.8,5.6,1.3),.08,'Timber')
crate(10.6,5.3,1.0,.8)
# Tunnel follows the railway curve; radial voussoirs around a real opening.
tx=31;ty=track_y(tx);ta=math.atan(.024*(tx+3));tz=track_z(tx)-.25
forward=Vector((math.cos(ta),math.sin(ta),0));right=Vector((-math.sin(ta),math.cos(ta),0))
def tp(a,b,z):return tuple(Vector((tx,ty,tz))+forward*a+right*b+Vector((0,0,z)))
# Arch aperture 5.6m wide, spring 2.6m high; 8m visible lined tunnel.
vv=[];ff=[]
for a in (0,9):
    for i in range(25):
        t=i*math.pi/24;vv.append(tp(a,2.8*math.cos(t),2.6+2.8*math.sin(t)))
for i in range(24):ff.append((i,i+1,26+i,25+i))
mesh('TunnelInterior',vv,ff,'StoneDark')
for side in (-1,1):
    mesh('TunnelInterior',[tp(0,side*2.8,0),tp(9,side*2.8,0),tp(9,side*2.8,2.6),tp(0,side*2.8,2.6)],[(0,1,2,3)],'StoneDark')
    for row in range(5):
        for j in range(2):
            p=tp(-.2,side*(3.13+j*.61),.28+row*.53);o=box('TunnelMasonry',p,(1.0,.59,.51),'StoneLight' if (row+j)%3 else 'Stone',.045,ta)
    for a in (.8,3.1,5.4,7.7):
        for i in range(18):
            ang=(i+.5)*math.pi/18;p=tp(a,2.8*math.cos(ang),2.6+2.8*math.sin(ang));o=box('TunnelRibs',p,(.19,.48,.10),'Stone',.015,ta);o.rotation_euler.rotate_axis('X',ang)
for i in range(19):
    a0=i*math.pi/19+.01;a1=(i+1)*math.pi/19-.01
    v=[]
    for depth in (-.73,.30):
        for rad,ang in [(2.8,a0),(2.8,a1),(3.55,a1),(3.55,a0)]:v.append(tp(depth,rad*math.cos(ang),2.6+rad*math.sin(ang)))
    mesh('TunnelMasonry',v,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(3,2,6,7),(1,5,6,2),(0,3,7,4)],'StoneLight' if i%4 else 'Stone')
o=box('TunnelMasonry',tp(-.22,0,6.35),(1.13,8.3,.38),'Stone',.09,ta)
o=box('Signage',tp(-.82,0,5.55),(.12,1.35,.48),'Metal',.04,ta)
# portal plaque text plane faces outward along local -X.
text('Lettering','1908',tp(-.90,0,5.55),.3,'Cream',(math.pi/2,0,ta-math.pi/2))
mesh('TunnelDarkness',[tp(9,-2.8,0),tp(9,2.8,0),tp(9,2.8,5.5),tp(9,-2.8,5.5)],[(0,1,2,3)],'Interior')
# Rock overburden makes the short tunnel read as embedded in a ridge.
for a,b,z,s in [(3,0,7,(6,4.8,2.5)),(7,0,7.8,(5,5,3.0)),(2,5,3,(4,2,3)),(3,-5,3.4,(5,2.5,3.4))]:
    p=tp(a,b,z);uv('TunnelHill',p,s,'StoneDark',16,10)
for a,b,z,s in [(3,0,8.4,(5.7,4.5,1.3)),(7,0,9.5,(4.5,4.8,1.6)),(1,4.8,5,(3.1,2.5,1.0))]:uv('TunnelHill',tp(a,b,z),s,'Meadow',16,10)
# Mountain outcrops: softened strata, stones sunk into terrain.
for x,y,s in [(-31,31,7),(-19,36,5),(-40,23,5),(30,30,6),(42,35,5),(29,18,3),(-33,-9,2.8),(8,-30,2.4),(-19,-28,1.8),(25,-20,2)]:
    z=ground(x,y)
    for i in range(3):uv('Outcrops',(x+i*.3,y+i*.2,z+i*s*.22),(s*(1-.17*i),s*.65*(1-.12*i),s*.40),'Stone' if i%2 else 'StoneDark',10,6)
    uv('OutcropMoss',(x+.6,y+.5,z+s*.63),(s*.56,s*.42,s*.13),'MeadowLight',12,6)
# Sculpted alpine conifers, varying tiers and trunk exposure.
def pine(x,y,s):
    z=ground(x,y);cyl('Trunks',(x,y,z+s*.32),s*.045,s*.64,'Timber',9)
    for k,(zz,r,d) in enumerate([(.36,.34,.48),(.57,.28,.43),(.76,.20,.39),(.93,.12,.31)]):
        bpy.ops.mesh.primitive_cone_add(vertices=10,radius1=s*r,radius2=s*r*.06,depth=s*d,location=(x,y,z+s*zz));o=bpy.context.object
        finish(o,'Conifers',['Pine','PineLight','PineDark'][(k+int(x))%3],.10,True)
    return z
trees=[(-43,38,8),(-37,39,9),(-45,29,7),(-36,25,7),(-25,42,8),(-17,43,6),(-9,42,6),(-42,10,8),(-36,13,6),(-29,18,5),(-30,22,7),(-23,26,6),(26,39,7),(33,42,9),(43,43,8),(44,28,7),(28,25,6),(24,31,5),(38,17,5),(45,14,7),(-41,-17,7),(-44,-25,5),(-35,-27,6),(-31,-33,6),(-18,-38,5),(-10,-40,6),(3,-35,4),(29,-32,6),(38,-28,7),(40,-17,6),(28,-11,4),(-21,12,4),(7,12,4),(23,12,4)]
for p in trees:pine(*p)
# Low shrubs and meadow clumps. Keep platform and footpath clear.
for i in range(145):
    x=random.uniform(-46,46);y=random.uniform(-44,45)
    if abs(y-track_y(x))<5 or (-28<x<24 and -5<y<20) or min((x-a)**2+(y-b)**2 for a,b in walkpts)<5:continue
    z=ground(x,y);s=random.uniform(.35,.9)
    uv('Shrubs',(x,y,z+s*.32),(s,s*.7,s*.52),'PineLight',10,6)
    if i%3==0:
        for j in range(3):uv('MeadowDetails',(x+random.uniform(-s,s),y+random.uniform(-s,s),z+.16),(.12,.12,.16),'Flower',8,4)
# Rail-side fence and overlook balustrade.
def fence(points):
    for x,y in points:
        z=ground(x,y);box('Fences',(x,y,z+.65),(.12,.12,1.3),'WoodLight',.035)
    for (x,y),(xx,yy) in zip(points,points[1:]):
        for z in (.47,1.0):beam('Fences',(x,y,ground(x,y)+z),(xx,yy,ground(xx,yy)+z),.10,'WoodLight')
fence([(-32+i*1.8,track_y(-32+i*1.8)+5.7) for i in range(7)])
fence([(6+i*1.6,37.7) for i in range(8)])
fence([(19,37.7-i*1.5) for i in range(5)])
# Trail wayfinding, a water tap, bins, planter boxes and planted edges.
for x,y,label in [(-24,8,'STATION  /  01'),(8,17,'RIDGE WALK')]:
    z=ground(x,y);box('TrailSigns',(x,y,z+1),(.12,.12,2),'Timber',.03);box('TrailSigns',(x,y,z+1.7),(1.9,.12,.32),'Cream',.04);text('Lettering',label,(x,y-.075,z+1.7),.16,'Ink')
for x in (-11.5,2.1):
    box('Planters',(x,3,1.85),(.8,1.1,.52),'WoodLight',.055)
    for j in range(3):uv('Planters',(x+random.uniform(-.2,.2),2.7+j*.3,2.2),(.31,.30,.3),'PineLight')
for x,y in [(-13,2.8),(4,2.9)]:
    cyl('Bins',(x,y,2.05),.31,.9,'SageDark',16);cyl('Bins',(x,y,2.52),.34,.07,'Metal',16)
beam('WaterTap',(22,2,.5),(22,2,1.55),.12,'Metal');beam('WaterTap',(22,2,1.5),(22,1.7,1.5),.10,'Metal')
# Small kilometre marker beside the curve.
box('Signage',(-22,track_y(-22)-2.3,1.16),(.45,.18,.85),'Cream',.05);text('Lettering','08',(-22,track_y(-22)-2.41,1.22),.27,'Ink')
# Join semantic groups, bake positions (origin at common site datum), export one FBX per group.
manifest=[]
for g,objects in groups.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name='SM_'+g
    bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    # Consistent UE axes: FBX transformation preserves authored XY as UE XY.
    path=OUT+'/SM_'+g+'.fbx'
    bpy.ops.export_scene.fbx(filepath=path,use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,axis_forward='Y',axis_up='Z',mesh_smooth_type='FACE',use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False)
    manifest.append({'name':'SM_'+g,'file':path,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'materials':[m.name for m in o.data.materials]})
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/AlderPass.blend')
with open(ROOT+'/art_manifest.json','w') as f:json.dump({'site_metres':[100,100],'palette':palette,'meshes':manifest,'trees':len(trees),'rail_gauge_cm':152,'platform_height_cm':152,'ramp_rise_cm':112,'ramp_run_cm':1300},f,indent=2)
print('ALDER_ART_COMPLETE',len(manifest),sum(m['polygons'] for m in manifest))
