import bpy, math, random, json, os
from mathutils import Vector
random.seed(82)
ROOT=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/high'
OUT=ROOT+'/Source/FBX'
os.makedirs(OUT,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
palette={
 'Grass':(.29,.40,.25),'Hill':(.35,.44,.28),'Earth':(.24,.21,.16),
 'Stone':(.44,.47,.43),'StoneLight':(.61,.61,.52),'Gravel':(.36,.39,.37),
 'Plaster':(.79,.72,.54),'Trim':(.38,.25,.15),'Wood':(.48,.34,.20),
 'Roof':(.13,.29,.28),'RoofEdge':(.22,.39,.36),'Metal':(.16,.20,.20),
 'Rail':(.43,.49,.48),'Glass':(.17,.34,.38),'Cream':(.9,.84,.65),
 'Ochre':(.70,.48,.22),'Path':(.61,.54,.39),'Leaf':(.21,.34,.24),
 'LeafLight':(.38,.47,.28),'Dark':(.035,.055,.052),'Lamp':(1,.76,.38),
 'Brick':(.51,.31,.23),'Flower':(.68,.55,.40)}
mats={}
for n,c in palette.items():
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1); mats[n]=m
groups={}; current='Terrain';cache={}
def finish(o,n,mat):
 o.name=n
 if not o.data.materials:o.data.materials.append(mats[mat])
 groups.setdefault(current,[]).append(o);return o
def mesh(n,v,f,mat):
 m=bpy.data.meshes.new(n);m.from_pydata(v,[],f);m.update();o=bpy.data.objects.new(n,m);bpy.context.collection.objects.link(o);return finish(o,n,mat)
def box(n,loc,size,mat,bev=.04,rot=0):
 key=('box',mat,bool(bev))
 if key not in cache:
  bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object
  if bev:
   mod=o.modifiers.new('soft crafted edges','BEVEL');mod.width=.035;mod.segments=3;bpy.ops.object.modifier_apply(modifier=mod.name)
   mod=o.modifiers.new('corner normals','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=mod.name)
  cache[key]=o.data;bpy.data.objects.remove(o,do_unlink=True)
 o=bpy.data.objects.new(n,cache[key]);bpy.context.collection.objects.link(o);o.location=loc;o.scale=size;o.rotation_euler[2]=rot
 return finish(o,n,mat)
def sphere(n,loc,scale,mat,sub=2):
 key=('sphere',mat,sub)
 if key not in cache:
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1);o=bpy.context.object
  for p in o.data.polygons:p.use_smooth=True
  cache[key]=o.data;bpy.data.objects.remove(o,do_unlink=True)
 o=bpy.data.objects.new(n,cache[key]);bpy.context.collection.objects.link(o);o.location=loc;o.scale=scale
 return finish(o,n,mat)
def cyl(n,loc,r,depth,mat,vertices=12):
 key=('cyl',mat,vertices)
 if key not in cache:
  vv=[(math.cos(i*math.tau/vertices),math.sin(i*math.tau/vertices),z) for z in [-.5,.5] for i in range(vertices)]
  ff=[tuple(range(vertices-1,-1,-1)),tuple(range(vertices,vertices*2))]+[(i,(i+1)%vertices,(i+1)%vertices+vertices,i+vertices) for i in range(vertices)]
  me=bpy.data.meshes.new(n);me.from_pydata(vv,[],ff);me.materials.append(mats[mat]);cache[key]=me
 o=bpy.data.objects.new(n,cache[key]);bpy.context.collection.objects.link(o);o.location=loc;o.scale=(r,r,depth);groups.setdefault(current,[]).append(o);return o
def beam(n,a,b,r,mat):
 a,b=Vector(a),Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,mat);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def text(n,txt,loc,size,mat,rotation=(math.pi/2,0,0)):
 cu=bpy.data.curves.new(n,'FONT');cu.body=txt;cu.align_x='CENTER';cu.align_y='CENTER';cu.size=size;cu.extrude=.006;cu.bevel_depth=.002
 o=bpy.data.objects.new(n,cu);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=rotation
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False);return finish(o,n,mat)
def ty(x):return 5+.004*x*x
def height(x,y):
 # Clear southern station terrace and a flattened rail cutting through the northern hills.
 h=12*math.exp(-((x-27)/20)**2-((y-29)/16)**2)+8*math.exp(-((x+31)/20)**2-((y-27)/19)**2)+3*math.exp(-((x+38)/16)**2-((y+27)/15)**2)
 h*=min(1,max(0,(y-ty(x)-4)/9)) if y>0 else min(1,max(0,(-x-22)/15))
 return h
N=100;v=[];f=[]
for j in range(N+1):
 for i in range(N+1):
  x=-50+i;y=-50+j;v.append((x,y,height(x,y)))
for j in range(N):
 for i in range(N):
  a=j*(N+1)+i;f.append((a,a+1,a+N+2,a+N+1))
o=mesh('sculpted 100m mountain meadow',v,f,'Grass')
for p in o.data.polygons:p.use_smooth=True
box('earth cutaway',(0,0,-1.2),(100,100,2.3),'Earth',.7)
def ribbon(n,points,width,mat):
 v=[]
 for i,p in enumerate(points):
  tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)]);normal=Vector((-tangent.y,tangent.x,0)).normalized()
  v.extend([Vector(p)+normal*width/2,Vector(p)-normal*width/2])
 return mesh(n,v,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(points)-1)],mat)
current='Railway'
pts=[(x/2,ty(x/2),.22) for x in range(-100,101)]
ribbon('continuous ballast bed',pts,4.2,'Gravel')
for side in [-1,1]:
 # A four sided swept rail has continuous edges, independent of sleeper spacing.
 vv=[]
 for x,y,z in pts:
  no=Vector((-.008*x,1,0)).normalized();c=Vector((x,y,.48))+no*side*.76
  vv.extend([c+no*dx+Vector((0,0,dz)) for dx,dz in [(-.045,-.06),(.045,-.06),(.045,.06),(-.045,.06)]])
 ff=[]
 for i in range(len(pts)-1):
  for q in range(4):ff.append((i*4+q,i*4+(q+1)%4,(i+1)*4+(q+1)%4,(i+1)*4+q))
 mesh('continuous polished rail',vv,ff,'Rail')
for i in range(145):
 x=-49.5+i*.6875;y=ty(x);ang=math.atan(.008*x)
 box('timber sleeper',(x,y,.29),(.23,2.5,.17),'Wood',.03,ang)
 for s in [-1,1]:
  no=Vector((-math.sin(ang),math.cos(ang),0));p=Vector((x,y,.4))+no*s*.76
  box('rail chair',p,(.32,.25,.08),'Metal',.01,ang)
current='Platform'
# Smooth platform edge follows exactly the same centerline as the rail.
pv=[]
for i in range(85):
 x=-23+i*.5;y=ty(x)-2.05
 pv += [(x,y,.0),(x,y,1.05),(x,-4.5,1.05),(x,-4.5,0)]
pf=[]
for i in range(84):
 for q in range(4):pf.append((4*i+q,4*i+(q+1)%4,4*(i+1)+(q+1)%4,4*(i+1)+q))
pf.extend([(0,3,2,1),(336,337,338,339)])
mesh('curved stone platform',pv,pf,'Stone')
for i in range(84):
 x=-22.75+i*.5;ang=math.atan(.008*x)
 box('edge coping',(x,ty(x)-2.24,1.09),(.49,.42,.12),'Cream',.025,ang)
 box('ochre warning line',(x,ty(x)-2.66,1.115),(.49,.11,.018),'Ochre',.006,ang)
for x in range(-22,19,2):
 for y in [-.8,.45,1.65]:box('paving joints',(x,y,1.055),(1.94,1.15,.035),'StoneLight',.02)
# Low ramp from forecourt to eastern platform end, 1:12 grade.
mesh('accessible arrival ramp',[(14,-13,0),(17,-13,0),(17,0,1.05),(14,0,1.05),(14,-13,-.1),(17,-13,-.1),(17,0,0),(14,0,0)],[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'Path')
for x in [14,17]:
 for j in range(7):
  y=-12+j*2;z=(y+13)/13*1.05;beam('ramp handrail post',(x,y,z),(x,y,z+.9),.035,'Metal')
 beam('continuous ramp handrail',(x,-12,1),(x,0,2),.045,'Metal')
current='Station'
box('raised stone foundation',(-8,-8, .48),(17,9, .95),'Stone',.16)
box('cream station walls',(-8,-8,2.55),(16,8,4),'Plaster',.13)
for x in [-15.8,-.2]:box('corner timber',(x,-12.05,2.65),(.20,.22,4.1),'Trim',.04)
box('front sill beam',(-8,-12.08,1.1),(16,.22,.25),'Trim')
box('front eave beam',(-8,-12.08,4.25),(16,.23,.23),'Trim')
for j in range(4):box('front entry stair',(-6.5,-13.9+j*.35,.12+j*.12),(2.6,1.5-j*.2,.24+j*.24),'StoneLight',.05)
# Gable roof with actual thickness, ridge caps and individual standing seams.
verts=[(-17,-13,4.3),(1,-13,4.3),(1,-8,6.8),(-17,-8,6.8),(-17,-3,4.3),(1,-3,4.3)]
roof=mesh('broad folded roof',verts,[(0,1,2,3),(3,2,5,4)],'Roof')
sol=roof.modifiers.new('thick roof','SOLIDIFY');sol.thickness=.20;bpy.context.view_layer.objects.active=roof;bpy.ops.object.modifier_apply(modifier=sol.name)
for x in [-16.9, .9]:
 beam('roof bargeboard',(x,-13,4.27),(x,-8,6.8),.12,'RoofEdge');beam('roof bargeboard',(x,-8,6.8),(x,-3,4.27),.12,'RoofEdge')
for x in [i*1.2-16.5 for i in range(15)]:
 beam('roof seam',(x,-13,4.35),(x,-8,6.88),.035,'RoofEdge');beam('roof seam',(x,-8,6.88),(x,-3,4.35),.035,'RoofEdge')
beam('ridge cap',(-17,-8,6.86),(1,-8,6.86),.17,'RoofEdge')
for x in [-16,0]:
 mesh('gable infill',[(x,-12,4.2),(x,-8,6.5),(x,-4,4.2)],[(0,1,2)],'Plaster')
for x in [-13.5,-9,-3]:
 box('front window frame',(x,-12.15,2.8),(2.5,.23,1.85),'Cream',.10)
 box('blue window glazing',(x,-12.29,2.8),(2.12,.035,1.50),'Glass',.04)
 box('window vertical mullion',(x,-12.33,2.8),(.10,.08,1.52),'Cream',.015)
 box('window crossbar',(x,-12.33,2.8),(2.15,.08,.10),'Cream',.015)
 box('deep sill',(x,-12.35,1.83),(2.7,.45,.18),'StoneLight',.06)
for x in [-12,-4]:
 box('platform window frame',(x,-3.89,2.7),(2.7,.24,1.8),'Cream',.08)
 box('platform window glass',(x,-3.74,2.7),(2.3,.03,1.45),'Glass',.03)
 box('platform window mullion',(x,-3.69,2.7),(.10,.06,1.45),'Cream',.01)
for y in [-12.18,-3.82]:
 box('door frame',(-6.5,y,2.13),(1.55,.2,3.1),'Trim',.05)
 box('door timber',(-6.5,y+(-.12 if y<-8 else .12),2.1),(1.27,.12,2.85),'Roof',.06)
 box('door glass',(-6.5,y+(-.2 if y<-8 else .2),2.75),(.87,.035,1.15),'Glass',.03)
current='Canopy'
box('platform shelter roof',(-8,-1.35,4.02),(18,4.4,.23),'Roof',.13)
box('canopy fascia',(-8,.9,3.86),(18,.18,.43),'Cream',.045)
for x in [-16,-10,-4,0]:
 box('canopy post',(x,.2,2.45),(.18,.18,2.8),'Trim',.03)
 beam('angled brace',(x,.2,3.0),(x+.6,.2,3.85),.07,'Trim')
 beam('angled brace',(x,.2,3.0),(x-.6,.2,3.85),.07,'Trim')
current='Signs'
for x in [-21,20]:
 for dx in [-1.25,1.25]:box('station signpost',(x+dx,1,2.2),(.13,.13,2.6),'Cream',.025)
 box('station name board',(x,1,2.9),(3,.20,1.05),'Roof',.12)
 text('SOLMARU front','SOLMARU',(x,.87,3.05),.38,'Cream')
 text('station altitude','MOUNTAIN LINE  /  082',(x,.865,2.7),.13,'Cream')
 text('SOLMARU rail side','SOLMARU',(x,1.13,3.05),.38,'Cream',(math.pi/2,0,math.pi))
box('building nameplate',(-8,-12.35,4.55),(6,.15,.75),'Roof',.06)
text('station facade title','SOLMARU',(-8,-12.46,4.55),.55,'Cream')
# Round station clock on front wall, face looks south.
o=cyl('clock rim',(-.4,-12.25,3.4),.6,.14,'Metal',48);o.rotation_euler[0]=math.pi/2
o=cyl('clock face',(-.4,-12.34,3.4),.51,.025,'Cream',48);o.rotation_euler[0]=math.pi/2
for i in range(12):
 a=i*math.tau/12;box('clock hour mark',(-.4+math.sin(a)*.43,-12.37,3.4+math.cos(a)*.43),(.045,.02,.09),'Metal',.01)
beam('clock hour hand',(-.4,-12.39,3.4),(-.65,-12.39,3.57),.025,'Metal')
beam('clock minute hand',(-.4,-12.40,3.4),(-.24,-12.4,3.74),.018,'Metal')
current='Tunnel'
# Tunnel at x=30 follows local rail tangent; segmented arched voussoirs, open throat.
tx=30;origin=Vector((tx,ty(tx),.1));ang=math.atan(.008*tx);T=Vector((math.cos(ang),math.sin(ang),0));S=Vector((-math.sin(ang),math.cos(ang),0))
def tr(u,v,z):return origin+T*u+S*v+Vector((0,0,z))
for side in [-1,1]:
 for h in range(5):
  box('tunnel side ashlar',tr(0,side*2.75,.45+h*.72),(1.25,.9,.68),'StoneLight' if h%2 else 'Stone',.06,ang)
for j in range(15):
 a=j*math.pi/15;b=(j+1)*math.pi/15
 vv=[]
 for u in [-.65,.65]:
  for r,th in [(2.3,a+.012),(3.25,a+.012),(3.25,b-.012),(2.3,b-.012)]:vv.append(tr(u,r*math.cos(th),3.25+r*math.sin(th)))
 mesh('radial arch stone',vv,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'StoneLight' if j%3 else 'Stone')
vv=[]
for u in [.4,10]:
 vv.extend([tr(u,-2.32,0),tr(u,-2.32,3.25)])
 vv.extend([tr(u,2.32*math.cos(math.pi-i*math.pi/24),3.25+2.32*math.sin(math.pi-i*math.pi/24)) for i in range(25)])
 vv.append(tr(u,2.32,0))
nn=len(vv)//2
mesh('continuous tunnel lining',vv,[(i,i+1,i+1+nn,i+nn) for i in range(nn-1)],'Dark')
# Mounded overburden covers tunnel sides, with open front portal.
for u in [2,5,8]:
 for s in [-1,1]:sphere('portal rock shoulder',tr(u,s*4.8,2.8),(3.5,2.7,4.1),'Stone',2)
 sphere('tunnel hill cap',tr(u,0,7.2),(3.7,5.7,2.3),'Hill',3)
box('tunnel keystone plaque',tr(-.71,0,5.85),(.13,1.4,.45),'Cream',.04,ang)
current='GroundPaths'
route=[(-6,-50,0.035),(-6,-35,.035),(-4,-25,.035),(2,-18,.035),(14,-13,.035)]
ribbon('arrival gravel promenade',route,4.0,'Path')
trail=[]
for i in range(81):
 t=i/80;x=-24-14*math.sin(t*math.pi*.8);y=-19+57*t;trail.append((x,y,height(x,y)+.10))
ribbon('winding hill footpath',trail,1.8,'Path')
for i in range(8,75,4):
 x,y,z=trail[i];beam('trail marker',(x-1.1,y,z),(x-1.1,y,z+.75),.065,'Wood')
current='Cargo'
box('cargo apron',(12,-23,.13),(15,10,.25),'Gravel',.4)
box('freight shed',(17,-23,1.8),(6.5,5,3.6),'Wood',.12)
box('freight shed roof',(17,-23,3.75),(7.4,5.9,.3),'Roof',.16)
for x in [14.2+i*.35 for i in range(17)]:box('shed vertical battens',(x,-25.55,1.9),(.06,.09,3.35),'Trim',.01)
box('shed sliding door',(17,-25.62,1.7),(2.8,.13,3.1),'RoofEdge',.05)
beam('shed door diagonal',(15.7,-25.72,.3),(18.3,-25.72,3.1),.065,'Cream')
for x,y,z,s in [(9,-24,.6,1),(11,-24,.6,1),(10,-24,1.75,.85),(9,-21,.55,.9),(12,-21,.6,1)]:
 box('freight crate',(x,y,z),(1.5*s,1.2*s,1.15*s),'Ochre',.08)
 for off in [-.5,.5]:box('crate strap',(x+off*s,y-.61*s,z),(.09, .04,1.1*s),'Trim',.01)
 beam('crate crossbrace',(x-.65*s,y-.64*s,z-.45*s),(x+.65*s,y-.64*s,z+.45*s),.055,'Wood')
for x,y in [(13,-19),(14.3,-19)]:
 cyl('barrel',(x,y,.65),.48,1.25,'Wood',16)
 for z in [.2,1.05]:cyl('barrel hoop',(x,y,z),.493,.095,'Metal',16)
current='Furniture'
def bench(x,y,z,rot=0):
 # Back faces away from rail; slatted seat and comfortable rounded back.
 for j in range(4):box('bench seat slat',(x,y+j*.16,z+.48),(2.25,.13,.09),'Wood',.04)
 for zz in [.80,1.04]:box('bench backrest',(x,y+.58,z+zz),(2.25,.1,.18),'Wood',.045)
 for dx in [-.8,.8]:
  for dy in [.05,.47]:box('bench legs',(x+dx,y+dy,z+.24),(.095,.1,.46),'Metal',.02)
  beam('bench back upright',(x+dx,y+.55,z+.1),(x+dx,y+.55,z+1.1),.045,'Metal')
for x in [-18,-13,-3,7]:bench(x,-.4,1.07)
bench(-34,31,height(-34,31))
for x,y,z in [(-17,-.5,1.1),(7,-1,1.1),(4,-14,0)]:
 box('leather travel trunk',(x,y,z+.35),(.95,.55,.7),'Ochre',.12)
 for dx in [-.3,.3]:box('luggage strap',(x+dx,y-.28,z+.35),(.07,.025,.62),'Trim',.015)
 beam('luggage handle',(x-.13,y,z+.74),(x+.13,y,z+.74),.035,'Trim')
for x,y,z in [(-22,0,1.1),(10,0,1.1),(20,-16,0),(-4,-25,0),(-7,-40,0)]:
 cyl('lamp plinth',(x,y,z+.12),.21,.24,'Stone',16);cyl('lamp post',(x,y,z+1.95),.07,3.7,'Metal',12)
 box('lantern amber panes',(x,y,z+3.9),(.36,.36,.5),'Lamp',.04)
 box('lantern cap',(x,y,z+4.2),(.52,.52,.12),'Roof',.06)
 for dx in [-.19,.19]:
  for dy in [-.19,.19]:beam('lantern frame',(x+dx,y+dy,z+3.65),(x+dx,y+dy,z+4.15),.025,'Metal')
for x in range(-23,22,3):
 box('forecourt fence post',(x,-19,.65),(.16,.16,1.3),'Cream',.04)
 if not -8<x<5:
  for z in [.4,1.0]:box('fence rail',(x+1.4,-19,z),(2.8,.10,.12),'Wood',.025)
for x,y in [(-13,-13.3),(-3,-13.3)]:
 box('window planter',(x,y,.95),(2.4,.6,.55),'Trim',.08)
 for j in range(9):sphere('planter herb',(x-1+j*.25,y,1.38),(.25,.26,.28),'LeafLight',1)
current='Vegetation'
trees=[]
for k in range(60):
 x=random.uniform(-46,46);y=random.uniform(-45,46)
 if abs(y-ty(x))<7 or (-27<x<27 and y<8) or (x>23 and 0<y<20):continue
 if any((x-p[0])**2+(y-p[1])**2<10 for p in trail):continue
 trees.append((x,y))
for x,y in trees:
 z=height(x,y);h=random.uniform(4.8,8.5)
 cyl('pine warm trunk',(x,y,z+h*.35),.18,h*.7,'Wood',10)
 for j in range(3):
  bpy.ops.mesh.primitive_cone_add(vertices=10,radius1=(h*.28)*(1-.22*j),radius2=.15,depth=h*.48,location=(x,y,z+h*(.45+.20*j)))
  o=finish(bpy.context.object,'rounded alpine pine','Leaf' if j%2==0 else 'LeafLight')
  bevel=o.modifiers.new('soft branch skirts','BEVEL');bevel.width=.18;bevel.segments=3;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=bevel.name)
for k in range(65):
 x=random.uniform(-48,48);y=random.uniform(-45,47)
 if abs(y-ty(x))<5 or (-25<x<25 and y<5):continue
 z=height(x,y);s=random.uniform(.45,1.7)
 sphere('weathered hillside boulder',(x,y,z+s*.38),(s,s*.7,s*.65),'Stone',2)
for k in range(100):
 x=random.uniform(-46,46);y=random.uniform(-46,46)
 if abs(y-ty(x))<4 or (-26<x<26 and y<4):continue
 z=height(x,y);sphere('low meadow shrub',(x,y,z+.25),(.5,.45,.45),'LeafLight',1)
# Export one FBX per semantic assembly. All vertex coordinates are original meters.
manifest={ 'site_extent_cm':[-5000,-5000,5000,5000], 'site_center_cm':[0,0,0], 'rail_gauge_cm':152, 'platform_top_cm':105, 'ramp_grade':1.05/13, 'tree_count':len(trees),'palette':palette,'assemblies':[] }
for name,objs in groups.items():
 print('EXPORTING',name,len(objs),flush=True)
 bpy.ops.object.select_all(action='DESELECT')
 for ob in objs:
  ob.data=ob.data.copy();ob.select_set(True)
 bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();ob=bpy.context.object;ob.name='SM_'+name
 ob.data=ob.data.copy()
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 path=OUT+'/'+ob.name+'.fbx'
 bpy.ops.export_scene.fbx(filepath=path,use_selection=True,object_types={'MESH'},apply_unit_scale=True,axis_forward='-Y',axis_up='Z',mesh_smooth_type='FACE',use_mesh_modifiers=True,add_leaf_bones=False)
 manifest['assemblies'].append({'name':ob.name,'file':path,'vertices':len(ob.data.vertices),'polygons':len(ob.data.polygons)})
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/Source/Solmaru.blend')
with open(ROOT+'/Source/source_manifest.json','w') as f:json.dump(manifest,f,indent=2)
print('SOLMARU_SOURCE_COMPLETE',manifest)
