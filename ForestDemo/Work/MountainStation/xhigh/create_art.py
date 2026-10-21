"""Original Alder Pass environmental artwork. Run with a private background Blender."""
import bpy, math, random, json
from pathlib import Path
from mathutils import Vector
random.seed(21743)
OUT=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh/SourceArt')
OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=1.0
M={}; GROUPS={}; group='Terrain'
COLORS={
 'Grass':(.29,.39,.27), 'GrassLight':(.38,.46,.30), 'Earth':(.29,.26,.21),
 'Rock':(.43,.46,.43), 'RockLight':(.54,.55,.49), 'Ballast':(.36,.38,.35),
 'Trail':(.62,.55,.41), 'Paving':(.60,.61,.53), 'EdgeStone':(.76,.72,.60),
 'Plaster':(.79,.72,.56), 'Timber':(.24,.20,.16), 'Wood':(.46,.33,.20),
 'Roof':(.16,.32,.33), 'RoofSeam':(.22,.40,.39), 'Metal':(.17,.22,.23),
 'Rail':(.43,.47,.45), 'Glass':(.23,.42,.45), 'Cream':(.91,.84,.65),
 'Amber':(.94,.60,.22), 'Pine':(.16,.29,.24), 'PineLight':(.24,.37,.28),
 'Bush':(.34,.43,.26), 'Red':(.54,.28,.20), 'Cargo':(.57,.45,.29),
 'Dark':(.065,.09,.09), 'Flowers':(.70,.58,.32)
}
for k,c in COLORS.items():
 m=bpy.data.materials.new(k); m.diffuse_color=(*c,1); m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*c,1); bs.inputs['Roughness'].default_value=.78
 M[k]=m
def add(o,name,mat):
 o.name=name; o.data.materials.append(M[mat]); GROUPS.setdefault(group,[]).append(o); return o
def mesh(name,v,f,mat,smooth=False):
 d=bpy.data.meshes.new(name); d.from_pydata(v,[],f); d.update(); o=bpy.data.objects.new(name,d); bpy.context.collection.objects.link(o); add(o,name,mat)
 for p in d.polygons:p.use_smooth=smooth
 return o
def bevel(o,w=.06,segments=3):
 mod=o.modifiers.new('Soft worked edges','BEVEL');mod.width=w;mod.segments=segments
 mod=o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL');mod.keep_sharp=True
 return o
def box(name,loc,dim,mat,bev=.06,rot=0):
 bpy.ops.mesh.primitive_cube_add(size=1, location=loc);o=bpy.context.object;o.dimensions=dim;o.rotation_euler.z=rot
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);add(o,name,mat)
 if bev:bevel(o,bev)
 return o
def sphere(name,loc,scale,mat):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=loc);o=bpy.context.object;o.scale=scale;add(o,name,mat)
 for p in o.data.polygons:p.use_smooth=True
 return o
def cylinder(name,loc,r,depth,mat,vertices=16):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc);return bevel(add(bpy.context.object,name,mat),min(.035,r*.18),2)
def beam(name,a,b,w,mat,depth=None):
 mid=(Vector(a)+Vector(b))*.5; o=box(name,mid,(w,depth or w,(Vector(b)-Vector(a)).length),mat,.025)
 o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler();return o
def text(name,body,loc,size,mat,rotation=(math.pi/2,0,0),align='CENTER'):
 d=bpy.data.curves.new(name,'FONT');d.body=body;d.size=size;d.extrude=.008;d.bevel_depth=.002;d.align_x=align;d.align_y='CENTER'
 o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=rotation;add(o,name,mat);return o
def line_strip(name,points,width,mat):
 v=[]
 for i,p in enumerate(points):
  t=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)]);n=Vector((-t.y,t.x,0)).normalized()*width*.5
  v.extend([Vector(p)-n,Vector(p)+n])
 return mesh(name,v,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(points)-1)],mat)
def track(x):return -16+.004*(x+10)**2
def tangent(x):return math.atan(.008*(x+10))
def height(x,y):
 # Flat valley and station apron transition into rolling, asymmetric hills.
 h=.18+.10*math.sin(x*.18)*math.cos(y*.17)
 rear=max(0,(y-7)/43)
 h+=rear**1.45*(9+8*math.exp(-((x-19)/21)**2)+4*math.sin(x*.055)**2)
 h+=12*math.exp(-((x-42)/13)**2-((y+1)/15)**2)
 h+=3.4*math.exp(-((x+42)/10)**2-((y-13)/20)**2)
 d=abs(y-track(x));fade=min(1,max(0,(d-4)/9))
 h=.22+(h-.22)*fade
 if -37<x<21 and -15<y<6:h=.22
 if x<-30:
  lane_blend=min(1,max(0,(abs(y+3)-3)/3));h=.22+(h-.22)*lane_blend
 return h
# Precisely bounded 100m site, visible earthen cut with softened strata.
N=100;vs=[(x-50,y-50,height(x-50,y-50)) for y in range(N+1) for x in range(N+1)]
fs=[]
for j in range(N):
 for i in range(N):
  a=j*(N+1)+i;fs.append((a,a+1,a+N+2,a+N+1))
mesh('Terrain_100m',vs,fs,'Grass',True)
perimeter=[(x,-50) for x in range(-50,51)]+[(50,y) for y in range(-49,51)]+[(x,50) for x in range(49,-51,-1)]+[(-50,y) for y in range(49,-50,-1)]
v=[]
for x,y in perimeter:v.extend([(x,y,height(x,y)),(x,y,-2.2)])
mesh('Cut_earth_edge',v,[(2*i,2*i+1,(2*i+3)%len(v),(2*i+2)%len(v)) for i in range(len(perimeter))],'Earth')
box('Diorama_underbase',(0,0,-2.3),(100,100,.35),'Earth',.22)
group='Paths'
trail=[(-36,-3),(-38,4),(-33,11),(-23,15),(-18,22),(-25,28),(-18,34),(-5,37),(8,35),(17,41)]
trail3=[]
for a,b in zip(trail[:-1],trail[1:]):
 for k in range(12):
  t=k/12;x=a[0]*(1-t)+b[0]*t;y=a[1]*(1-t)+b[1]*t;trail3.append((x,y,height(x,y)+.045))
line_strip('Hillside_walking_trail',trail3,2.4,'Trail')
line_strip('Approach_lane',[(-49,-3,.28),(-43,-3,.28),(-36,-3,.28)],5.5,'Trail')
for x in range(-47,-34,2):box('Approach_pavers',(x,-3,.32),(1.65,2.7,.12),'Paving',.1)
group='Railway'
xs=[-50+i*.35 for i in range(287)];xs[-1]=50
line_strip('Ballast_formation',[(x,track(x),.37) for x in xs],4.2,'Ballast')
for i in range(143):
 x=-49.7+i*.7;y=track(x);a=tangent(x)
 box('Timber_sleeper',(x,y,.48),(.24,2.65,.20),'Timber',.045,a)
 if i%2==0:
  for side in [-1,1]:
   bx=x-math.sin(a)*side*.76;by=y+math.cos(a)*side*.76
   box('Rail_chair',(bx,by,.61),(.30,.23,.07),'Metal',.015,a)
for s in [-1,1]:
 for part,w,z in [('foot',.15,.62),('web',.065,.72),('head',.105,.81)]:
  pts=[(x-math.sin(tangent(x))*s*.765,track(x)+math.cos(tangent(x))*s*.765,z) for x in xs]
  # Connected rectangular rail extrusion, following the same sampled curve.
  vv=[]
  for i,p in enumerate(pts):
   a=tangent(xs[i]);nx=-math.sin(a)*w/2;ny=math.cos(a)*w/2
   vv.extend([(p[0]-nx,p[1]-ny,z-.035),(p[0]+nx,p[1]+ny,z-.035),(p[0]+nx,p[1]+ny,z+.035),(p[0]-nx,p[1]-ny,z+.035)])
  ff=[]
  for i in range(len(pts)-1):
   for j in range(4):ff.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
  mesh('Continuous_rail_'+part,vv,ff,'Rail')
for i in range(360):
 x=random.uniform(-49,49);y=track(x)+random.choice([-1,1])*random.uniform(1.45,2.06)
 sphere('Ballast_stone',(x,y,.40),(random.uniform(.07,.16),.1,.08),'Rock')
group='Platform'
# Curved platform edge maintains an offset from the track near the station.
xx=[-28+i*.5 for i in range(87)]
vv=[]
for x in xx:
 y=track(x)+2.10;vv.extend([(x,y,.23),(x,y,1.22),(x,-2.7,1.22),(x,-2.7,.23)])
ff=[]
for i in range(len(xx)-1):
 for j in range(4):ff.append((4*i+j,4*i+(j+1)%4,4*(i+1)+(j+1)%4,4*(i+1)+j))
ff.extend([(3,2,1,0),tuple(range(len(vv)-4,len(vv)))])
mesh('Curved_platform_body',vv,ff,'Paving')
for i in range(57):
 x=-27.6+i*.75;y=track(x)+2.34
 box('Platform_edge_coping',(x,y,1.25),(.71,.46,.18),'EdgeStone',.035,tangent(x))
line_strip('Safety_line',[(x,track(x)+2.75,1.236) for x in xx],.12,'Cream')
for x in range(-27,15,3):
 line_strip('Paving_joint',[(x,track(x)+2.95,1.23),(x,-2.73,1.23)],.025,'Rock')
mesh('Accessible_west_ramp',[(-36,-8,.25),(-36,-4,.25),(-28,-8,1.22),(-28,-4,1.22),(-28,-8,.23),(-28,-4,.23)],[(0,2,3,1),(0,4,2),(1,3,5),(4,5,3,2)],'Paving')
for y in [-8,-4]:
 for x in [-35,-32,-29]:
  z=.25+(x+36)/8*.97;cylinder('Ramp_handrail_post',(x,y,z+.5),.045,1,'Metal')
 beam('Ramp_handrail',(-36,y,1.25),(-28,y,2.22),.07,'Metal')
group='Station'
box('Stone_plinth',(-9,-6,1.38),(14,6.5,.32),'RockLight',.10)
box('Cream_station_walls',(-9,-5.8,3.45),(13.4,5.8,4.1),'Plaster',.16)
for x in [-15.7,-2.3]:
 mesh('Gable_wall',[(x,-8.7,5.5),(x,-2.9,5.5),(x,-5.8,7.5)],[(0,1,2)],'Plaster')
for y in [-8.78,-2.82]:
 box('Sill_band',(-9,y,1.75),(13.6,.13,.35),'Timber',.03)
 box('Eaves_band',(-9,y,5.28),(13.8,.15,.22),'Timber',.03)
for x in [-15.5,-9,-2.5]:
 for y in [-8.78,-2.82]:box('Half_timber_post',(x,y,3.45),(.20,.16,4.1),'Timber',.025)
# Solid roof boards with standing seams and chunky ridge cap.
for side in [-1,1]:
 y0=-5.8;y1=-5.8+side*3.75
 v=[(-16.6,y0,7.72),(-1.4,y0,7.72),(-1.4,y1,5.36),(-16.6,y1,5.36)]
 o=mesh('Teal_pitched_roof',v,[(0,1,2,3)],'Roof');solid=o.modifiers.new('Roof_thickness','SOLIDIFY');solid.thickness=.17;bevel(o,.06)
 for i in range(26):
  x=-16.4+i*.59;beam('Raised_roof_seam',(x,y0,7.78),(x,y1,5.43),.05,'RoofSeam')
 beam('Eave_fascia',(-16.65,y1,5.36),(-1.35,y1,5.36),.17,'Timber')
beam('Roof_ridge',(-16.75,-5.8,7.78),(-1.25,-5.8,7.78),.18,'RoofSeam')
for x in [-16.58,-1.42]:
 for side in [-1,1]:beam('Gable_fascia',(x,-5.8,7.75),(x,-5.8+side*3.78,5.35),.2,'Timber')
box('Chimney',(-13,-4.7,7.4),(.85,.9,2.5),'RockLight',.06);box('Chimney_cap',(-13,-4.7,8.7),(1.05,1.1,.18),'EdgeStone',.06)
# Front door, window recesses, timber mullions and flower boxes.
for x in [-13,-5]:
 box('Window_dark_reveal',(x,-8.75,3.65),(2.05,.18,2.15),'Timber',.07)
 box('Blue_window',(x,-8.87,3.65),(1.75,.06,1.85),'Glass',.035)
 for dx in [-.91,0,.91]:box('Window_mullion',(x+dx,-8.93,3.65),(.075,.08,1.95),'Cream',.012)
 for z in [2.7,3.65,4.6]:box('Window_crossbar',(x,-8.94,z),(1.9,.08,.075),'Cream',.012)
 box('Window_sill',(x,-9,2.62),(2.2,.38,.15),'EdgeStone',.04)
 box('Flower_box',(x,-9.13,2.25),(2.1,.45,.42),'Wood',.06)
 for dx in [-.75,-.45,0,.4,.75]:
  sphere('Planter_foliage',(x+dx,-9.13,2.54),(.3,.23,.25),'Bush')
  sphere('Ochre_flower',(x+dx,-9.22,2.75),(.09,.08,.09),'Flowers')
box('Door_frame',(-9,-8.78,2.75),(1.8,.22,3.05),'Timber',.06)
box('Entrance_door',(-9,-8.94,2.72),(1.5,.10,2.85),'Roof',.045)
box('Door_glazing',(-9,-9.01,3.25),(1.12,.04,1.25),'Glass',.02)
cylinder('Door_handle',(-8.45,-9.13,2.55),.06,.25,'Amber')
# Platform canopy with narrow ribs, diagonal knee braces, timber posts.
box('Canopy_roof',(-8,-10.6,4.75),(20,3.6,.18),'Roof',.08)
for x in [-17,-7,1]:
 for y in [-11.95]:
  box('Canopy_post',(x,y,2.98),(.19,.19,3.5),'Timber',.035)
  beam('Canopy_brace',(x,y,3.9),(x+.8,y,4.64),.13,'Timber')
  beam('Canopy_brace',(x,y,3.9),(x-.8,y,4.64),.13,'Timber')
for x in range(-17,2,1):box('Canopy_roof_rib',(x,-10.6,4.88),(.04,3.55,.06),'RoofSeam',.015)
box('Station_name_board',(-9,-12.44,4.25),(6.8,.12,.7),'Roof',.07)
text('Station_name','ALDER PASS',(-9,-12.515,4.26),.48,'Cream')
text('Station_subtitle','MOUNTAIN RAILWAY  /  1928',(-9,-9.01,4.85),.17,'Timber')
# End gable clock on east end, visible from the approach around the corner.
clock=cylinder('Clock_case',(-1.99,-5.8,5.65),.64,.16,'Timber',48);clock.rotation_euler.y=math.pi/2
clock=cylinder('Clock_face',(-1.89,-5.8,5.65),.54,.03,'Cream',48);clock.rotation_euler.y=math.pi/2
for i in range(12):
 a=i*math.tau/12;box('Clock_hour_mark',(-1.865,-5.8+math.sin(a)*.45,5.65+math.cos(a)*.45),(.025,.045,.09),'Timber',.006)
beam('Clock_long_hand',(-1.84,-5.8,5.65),(-1.84,-5.8+.32,5.65+.19),.035,'Timber')
beam('Clock_short_hand',(-1.83,-5.8,5.65),(-1.83,-5.8-.14,5.65+.2),.045,'Timber')
group='Tunnel'
px=32;py=track(px);ang=tangent(px)
def portal(t,u,z):return (px+math.cos(ang)*t-math.sin(ang)*u,py+math.sin(ang)*t+math.cos(ang)*u,z)
for s in [-1,1]:
 for row in range(5):
  for c in range(2):
   o=box('Portal_pier_block',portal(.0,s*(3.13+c*.52),.65+row*.64),(.85,.50,.60),'RockLight' if row%3 else 'EdgeStone',.045,ang)
for i in range(17):
 a=i*math.pi/17;b=(i+1)*math.pi/17
 v=[]
 for t in [-.48,.48]:
  for r,q in [(2.9,a),(3.75,a),(3.75,b),(2.9,b)]:v.append(portal(t,math.cos(q)*r,3.48+math.sin(q)*r))
 o=mesh('Arch_voussoir',v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'EdgeStone' if i%3 else 'RockLight');bevel(o,.045)
# Continuous vaulted lining; a real open entrance and deep dark end.
v=[]
for t in [.40,13]:
 for i in range(25):
  q=i*math.pi/24;v.append(portal(t,math.cos(q)*2.92,3.48+math.sin(q)*2.92))
mesh('Tunnel_vault',v,[(i,i+1,26+i,25+i) for i in range(24)],'Rock')
for s in [-1,1]:
 v=[portal(t,s*2.92,z) for t,z in [(.4,.2),(13,.2),(13,3.48),(.4,3.48)]];mesh('Tunnel_sidewall',v,[(0,1,2,3)],'Rock')
box('Tunnel_black_depth',portal(13,0,3.3),(.22,5.8,6.6),'Dark',0,ang)
for s in [-1,1]:
 for j in range(4):
  p=portal(-.2-j*.5,s*(4+j*.7),1.4);box('Splayed_wingwall',p,(1.1,1.0,2.6-j*.35),'RockLight',.09,ang)
box('Portal_keystone',portal(-.57,0,7.12),(.16,.65,.65),'Cream',.06,ang)
# Rock crown covers the vault and blends into the hillside, leaving the entrance clear.
for i in range(26):
 t=random.uniform(1,15);u=random.uniform(-7,7);z=6.0+random.uniform(0,2.3)+max(0,2-abs(u))*.5
 p=portal(t,u,z);sphere('Tunnel_rock_crown',p,(random.uniform(2,4),random.uniform(2,4),random.uniform(1.4,3)),'Rock' if i%3 else 'RockLight')
group='Cargo'
box('Cargo_loading_pad',(10,-5,1.39),(7,6,.3),'RockLight',.08)
for x in [7,13]:
 for y in [-7.5,-2.5]:box('Goods_shelter_post',(x,y,3.1),(.22,.22,3.2),'Timber',.04)
roof=box('Goods_shelter_roof',(10,-5,4.9),(7.4,6.1,.23),'Roof',.08);roof.rotation_euler.x=.10
for x in [7,8,9,10,11,12,13]:box('Goods_shed_board',(x,-2.52,2.9),(.9,.14,2.8),'Wood',.025)
def crate(x,y,z,scale=1):
 box('Cargo_crate',(x,y,z+.5*scale),(1.05*scale,.92*scale,scale),'Cargo',.055)
 for yy in [-.47,.47]:
  for dx in [-.39,.39]:box('Crate_batten',(x+dx*scale,y+yy*scale,z+.5*scale),(.10*scale,.055*scale,1.02*scale),'Wood',.015)
  beam('Crate_diagonal',(x-.4*scale,y+yy*scale,z+.12*scale),(x+.4*scale,y+yy*scale,z+.9*scale),.07*scale,'Wood')
 for dz in [.08,.92]:box('Crate_band',(x,y,z+dz*scale),(1.10*scale,.96*scale,.08*scale),'Wood',.015)
for x,y,z,s in [(8,-4,1.55,1.1),(9.3,-4,1.55,1.1),(8.6,-4,2.65,.85),(11,-3.8,1.55,1.2),(12.3,-4,1.55,.85),(12,-6,1.55,.7)]:crate(x,y,z,s)
for x,y in [(7.7,-6.2),(9.2,-6.4)]:
 cylinder('Barrel',(x,y,2.06),.43,1.1,'Wood',16)
 for z in [1.65,2.45]:cylinder('Barrel_hoop',(x,y,z),.447,.08,'Metal',16)
text('Goods_notice','GOODS', (10,-7.94,4.36),.38,'Cream')
group='Props'
def bench(x,y,rot=0):
 for k in range(4):box('Bench_seat_slat',(x,y-.25+k*.16,1.76),(2.4,.13,.10),'Wood',.03,rot)
 for k in range(3):box('Bench_back_slat',(x,y+.35,2.07+k*.16),(2.4,.10,.12),'Wood',.025,rot)
 for dx in [-.86,.86]:
  box('Bench_leg',(x+dx,y,1.48),(.12,.55,.53),'Metal',.035)
  box('Bench_back_support',(x+dx,y+.38,1.99),(.09,.08,1.25),'Metal',.02)
bench(-20,-9.0);bench(-.2,-10.8)
for x in [-24,4,18]:
 y=track(x)+3.8;z=1.22 if x<15 else .25
 cylinder('Lamp_base',(x,y,z+.15),.18,.3,'Metal');cylinder('Lamp_post',(x,y,z+2.1),.075,4.1,'Metal')
 beam('Lamp_arm',(x,y,z+4.12),(x,y-.6,z+4.12),.09,'Metal')
 cylinder('Lamp_glass',(x,y-.6,z+3.87),.20,.38,'Cream');box('Lamp_cap',(x,y-.6,z+4.13),(.55,.55,.15),'Roof',.08)
for x,y in [(-23,-11),(-22.4,-11.1),(-.5,-10.2)]:
 box('Travel_case',(x,y,1.55),(.52,.32,.65),'Red' if x<-1 else 'Roof',.07)
 for dx in [-.16,.16]:box('Luggage_strap',(x+dx,y-.17,1.55),(.055,.03,.64),'Cargo',.015)
 beam('Luggage_handle',(x-.12,y,1.91),(x+.12,y,1.91),.06,'Timber')
for x in [-25,16]:
 y=track(x)+4.1;z=1.22 if x<15 else .25
 for dx in [-1.7,1.7]:cylinder('Nameboard_post',(x+dx,y,z+1.3),.08,2.6,'Metal')
 box('Freestanding_nameboard',(x,y,z+2.25),(3.7,.13,.75),'Roof',.07)
 text('Platform_name','ALDER PASS',(x,y-.085,z+2.25),.32,'Cream')
 text('Platform_number','01',(x,y-.09,z+1.55),.26,'Timber')
box('Timetable_frame',(-18,-8.7,2.6),(1.1,.16,1.35),'Timber',.05)
box('Timetable_paper',(-18,-8.80,2.6),(.92,.03,1.14),'Cream',.01)
text('Departures_title','DEPARTURES',(-18,-8.83,2.99),.12,'Timber')
for i,body in enumerate(['08:10  VALLEY','10:45  SUMMIT','14:20  VALLEY','17:35  SUMMIT']):text('Timetable_row',body,(-18,-8.83,2.77-i*.16),.085,'Timber')
# Station entrance sign and small hillside wayfinding marker.
for x,y,label in [(-36,1,'STATION'),(-29,16,'RIDGE WALK')]:
 z=height(x,y);box('Waymark_post',(x,y,z+.85),(.14,.14,1.7),'Timber',.03)
 box('Waymark_board',(x,y,z+1.5),(1.9,.12,.42),'Wood',.04)
 text('Waymark_text',label,(x,y-.07,z+1.5),.17,'Cream')
def fence(points):
 for a,b in zip(points[:-1],points[1:]):
  dist=math.dist(a,b);n=max(1,int(dist/2.4));prev=None
  for i in range(n+1):
   t=i/n;x=a[0]*(1-t)+b[0]*t;y=a[1]*(1-t)+b[1]*t;z=height(x,y)
   box('Fence_post',(x,y,z+.57),(.14,.14,1.14),'Wood',.03)
   if prev:
    for off in [.4,.87]:beam('Fence_rail',(prev[0],prev[1],prev[2]+off),(x,y,z+off),.10,'Wood')
   prev=(x,y,z)
fence([(-48,2),(-40,2),(-35,8),(-26,10),(-15,10)])
fence([(-29,24),(-28,29),(-19,34),(-8,37),(4,36)])
group='LandscapeDetails'
# Hand-shaped clusters give the hill a layered silhouette instead of a grid.
tree_positions=[]
for i in range(95):
 x=random.uniform(-47,47);y=random.uniform(8,47)
 if min(math.hypot(x-p[0],y-p[1]) for p in trail)<3.5:continue
 if abs(y-track(x))<6:continue
 tree_positions.append((x,y))
for x,y in [(-44,-32),(-39,-27),(-46,-20),(30,-34),(37,-28),(44,-23),(47,-17),(-31,5)]:tree_positions.append((x,y))
for idx,(x,y) in enumerate(tree_positions):
 z=height(x,y);h=random.uniform(4.4,8.3);r=h*.28
 cylinder('Evergreen_trunk',(x,y,z+h*.33),.18,h*.66,'Timber',10)
 for k in range(3):
  cz=z+h*(.4+.19*k);rr=r*(1-.22*k)
  # Rounded conical crowns, with subtly irregular skirt vertices.
  vv=[];rings=[(0,rr*.92),(.16*h,rr*.76),(.36*h,.06)]
  for dz,rad in rings:
   for j in range(12):
    a=j*math.tau/12;rad2=rad*(1+random.uniform(-.07,.07));vv.append((x+math.cos(a)*rad2,y+math.sin(a)*rad2,cz+dz))
  ff=[]
  for ring in range(2):
   for j in range(12):ff.append((ring*12+j,ring*12+(j+1)%12,(ring+1)*12+(j+1)%12,(ring+1)*12+j))
  ff.append(tuple(reversed(range(12))));ff.append(tuple(range(24,36)))
  o=mesh('Tiered_fir_crown',vv,ff,'Pine' if (idx+k)%3 else 'PineLight',True);bevel(o,.08,2)
for i in range(85):
 x=random.uniform(-47,47);y=random.uniform(-40,47)
 if -39<x<22 and -18<y<9:continue
 if abs(y-track(x))<5:continue
 z=height(x,y);s=random.uniform(.35,1.5)
 sphere('Rounded_outcrop',(x,y,z+.35*s),(s,s*.8,s*.65),'Rock' if i%4 else 'RockLight')
 if i%2==0:sphere('Low_scrub',(x+1,y+.6,z+.3),(1,.8,.55),'Bush')
for i in range(180):
 x=random.uniform(-47,47);y=random.uniform(-45,45)
 if -39<x<22 and -18<y<9:continue
 if abs(y-track(x))<4:continue
 z=height(x,y)
 for j in range(3):beam('Grass_blade',(x+j*.08,y,z),(x+j*.08+.06,y+.03,z+random.uniform(.17,.38)),.025,'GrassLight')
# Source provenance and geometry checks before FBX export.
scene_stats={}
bpy.ops.object.select_all(action='DESELECT')
for name,objects in GROUPS.items():
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
 bpy.ops.object.convert(target='MESH')
 # Join each semantic assembly, keeping its material slots and world coordinates.
 bpy.ops.object.join();o=bpy.context.object;o.name=name
 bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 scene_stats[name]={'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'materials':[m.name for m in o.data.materials]}
 bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,global_scale=1.0,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',bake_anim=False,add_leaf_bones=False)
 o.select_set(False)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'AlderPass.blend'))
(OUT/'palette.json').write_text(json.dumps(COLORS,indent=2))
(OUT/'geometry_manifest.json').write_text(json.dumps({'site_bounds_m':[-50,-50,50,50],'track_equation':'y=-16+0.004*(x+10)^2','rail_center_spacing_m':1.53,'platform_height_m':1.22,'ramp_rise_run_m':[.97,8],'portal_position_m':[px,py,.22],'portal_yaw_degrees':math.degrees(ang),'assemblies':scene_stats,'tree_count':len(tree_positions)},indent=2))
print('ALDER_ART_COMPLETE',json.dumps(scene_stats))
