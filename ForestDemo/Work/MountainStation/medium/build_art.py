import bpy, math, random, json, os
from mathutils import Vector
random.seed(117)
OUT=os.path.dirname(__file__)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
palette={'grass':(.28,.39,.26),'edge':(.23,.28,.24),'stone':(.47,.51,.47),'rock':(.37,.43,.41),'cream':(.78,.72,.56),'roof':(.13,.31,.32),'wood':(.36,.23,.14),'woodlight':(.58,.40,.24),'metal':(.15,.19,.20),'rail':(.46,.51,.51),'glass':(.20,.38,.41),'gold':(.85,.66,.30),'gravel':(.40,.43,.39),'path':(.65,.59,.45),'leaf':(.19,.34,.27),'leaf2':(.30,.43,.29),'white':(.88,.84,.70),'dark':(.035,.047,.045),'brick':(.54,.37,.27)}
mats={}
for n,c in palette.items():
 m=bpy.data.materials.new(n); m.diffuse_color=(*c,1); mats[n]=m
def finish(o,n,m):
 o.name=n; o.data.materials.append(mats[m]); return o
def box(n,loc,sc,m,bev=.08,rot=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.scale=sc; o.rotation_euler[2]=rot
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bev:
  mod=o.modifiers.new('Soft edges','BEVEL'); mod.width=bev; mod.segments=2; bpy.ops.object.modifier_apply(modifier=mod.name)
 return finish(o,n,m)
def mesh(n,v,f,m):
 me=bpy.data.meshes.new(n); me.from_pydata(v,[],f); me.update(); o=bpy.data.objects.new(n,me); bpy.context.collection.objects.link(o); return finish(o,n,m)
def cyl(n,loc,r,depth,m,vertices=12):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc); return finish(bpy.context.object,n,m)
def beam(n,a,b,w,m):
 mid=(Vector(a)+Vector(b))/2; o=box(n,mid,(w,w,(Vector(b)-Vector(a)).length),m,w*.12); o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler(); return o
def ball(n,loc,sc,m):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=loc); o=bpy.context.object; o.scale=sc; return finish(o,n,m)
def text(n,string,loc,size,m,rot=(math.pi/2,0,0)):
 bpy.ops.object.text_add(location=loc,rotation=rot); o=bpy.context.object; o.data.body=string; o.data.align_x='CENTER'; o.data.size=size; o.data.extrude=.008; o.data.materials.append(mats[m]); o.name=n; bpy.ops.object.convert(target='MESH'); return o
def zground(x,y):
 # A level rail/station terrace, rising into a low mountain wall behind.
 return max(0,(y-18)/32)**1.25*8 + 2.3*math.exp(-((x+39)/12)**2-((y+26)/15)**2)
N=60; vs=[]
for j in range(N+1):
 y=-50+j*100/N
 for i in range(N+1):
  x=-50+i*100/N; vs.append((x,y,zground(x,y)))
fs=[]
for j in range(N):
 for i in range(N):
  a=j*(N+1)+i; fs.extend([(a,a+1,a+N+2),(a,a+N+2,a+N+1)])
mesh('100m sculpted hillside',vs,fs,'grass')
box('Earth plinth',(0,0,-2),(100,100,4),'edge',1.5)
# Continuous curved ballast ribbon, rails and evenly spaced sleepers.
def route(x): return 8+.0025*x*x
def ribbon(n,offset,width,z,m):
 v=[]
 for k in range(201):
  x=-50+k*.5; y=route(x); a=math.atan(.005*x); nx=-math.sin(a); ny=math.cos(a)
  for side in [-1,1]: v.append((x+nx*(offset+side*width/2),y+ny*(offset+side*width/2),z))
 f=[(i,i+1,i+3,i+2) for i in range(0,400,2)]; return mesh(n,v,f,m)
ribbon('Shaped ballast bed',0,4.3,.12,'gravel')
for side in [-.78,.78]:
 ribbon('Steel running rail',side,.10,.40,'rail')
 ribbon('Rail foot',side,.20,.30,'metal')
for i in range(132):
 x=-49.5+i*.75; y=route(x); a=math.atan(.005*x)
 box('Timber sleeper',(x,y,.23),(.24,2.7,.18),'wood',.035,a)
 for side in [-.78,.78]:
  box('Tie plate',(x-math.sin(a)*side,y+math.cos(a)*side,.335),(.28,.27,.035),'metal',.01,a)
# Curved platform edge follows rail exactly, with generous station area.
v=[]
for i in range(65):
 x=-26+i*.625
 v.extend([(x,route(x)-2.25,.72),(x,route(x)-8,.72),(x,route(x)-2.25,0),(x,route(x)-8,0)])
f=[]
for i in range(64):
 a=i*4; f.extend([(a,a+4,a+5,a+1),(a+2,a+6,a+4,a),(a+1,a+5,a+7,a+3)])
mesh('Curving accessible platform',v,f,'stone')
for i in range(64):
 x=-25.7+i*.625; y=route(x)-2.45
 box('Ivory coping',(x,y,.76),(.61,.40,.10),'white',.025,math.atan(.005*x))
 if i%2==0: box('Safety line',(x,y-.44,.775),(.50,.09,.025),'gold',.005)
# Long south approach ramps to platform height without a step.
mesh('Accessible approach ramp',[(-21,-13,0),(-16,-13,0),(-16,1,.73),(-21,1,.73),(-21,1,0),(-16,1,0)],[(0,1,2,3),(0,3,4),(1,5,2)],'path')
box('Forecourt',(0,-17,.03),(29,13,.12),'path',1.2)
# Station house with a deep pitched roof and separate porch.
box('Station foundation',(-7,-3,.44),(14,8,.88),'stone',.15)
box('Warm plaster walls',(-7,-3,2.85),(13,7.2,4.1),'cream',.20)
for x in [-13.4,-.6]:
 for y in [-6.5,.5]: box('Timber corner',(x,y,2.9),(.24,.24,4.2),'wood',.04)
for y in [-6.6,.6]:
 box('Lower wall band',(-7,y,1.10),(13,.15,.30),'woodlight',.03)
 box('Upper wall band',(-7,y,4.60),(13,.15,.20),'woodlight',.025)
# roof ridge along X; thick gable shape
mesh('Pitched teal roof',[(-14.3,-7.4,4.7),(.3,-7.4,4.7),(-14.3,-3,7),(.3,-3,7),(-14.3,1.4,4.7),(.3,1.4,4.7)],[(0,1,3,2),(2,3,5,4),(0,2,4),(1,5,3)],'roof')
for x in [i*.72-14 for i in range(20)]:
 beam('Standing roof seam',(x,-7.4,4.75),(x,-3,7.05),.07,'roof'); beam('Standing roof seam',(x,-3,7.05),(x,1.4,4.75),.07,'roof')
beam('Ridge cap',(-14.5,-3,7.05),(.5,-3,7.05),.22,'roof')
for x in [-11,-6, -2]:
 for y in [-6.66,.66]:
  box('Window frame',(x,y,2.85),(1.9,.17,1.9),'woodlight',.08)
  box('Blue glass',(x,y+(-.10 if y<0 else .10),2.85),(1.62,.04,1.58),'glass',.025)
  box('Window mullion',(x,y+(-.14 if y<0 else .14),2.85),(.08,.08,1.6),'cream',.01)
  box('Window sill',(x,y,1.86),(2.1,.42,.14),'cream',.04)
box('Entrance door',(-8.4,-6.73,2.15),(1.25,.20,2.8),'roof',.08)
box('Door glazing',(-8.4,-6.86,2.65),(.86,.05,1.35),'glass',.02)
ball('Door handle',(-7.99,-6.93,1.9),(.08,.08,.08),'gold')
box('Entrance step',(-8.4,-7.45,.35),(2.5,1.2,.7),'stone',.12)
box('Chimney',(-10,-3.8,6.9),(.9,.9,2.4),'brick',.08)
box('Chimney cap',(-10,-3.8,8.15),(1.16,1.16,.25),'stone',.07)
# platform canopy
for x in [-20,-14,-8,2,8]:
 cyl('Canopy post',(x,2.0,2.45),.12,3.5,'roof')
 beam('Canopy diagonal',(x,2,3.1),(x,3.1,4.1),.13,'woodlight')
box('Platform canopy',(-6,2.5,4.35),(30,4.2,.28),'roof',.14)
box('Canopy fascia',(-6,4.6,4.1),(30,.15,.4),'woodlight',.035)
text('Station name','ALDER PASS',(-7,-6.78,4.03),.50,'roof')
# Round analog clock on south face
o=cyl('Clock brass surround',(-3.1,-6.85,4.0),.47,.12,'gold',32); o.rotation_euler[0]=math.pi/2
o=cyl('Clock dial',(-3.1,-6.93,4),.405,.04,'white',32); o.rotation_euler[0]=math.pi/2
beam('Clock minute',(-3.1,-6.97,4),(-3.1,-6.97,4.31),.035,'dark'); beam('Clock hour',(-3.1,-6.98,4),(-3.32,-6.98,3.92),.05,'dark')
for a in range(12):
 t=a*math.tau/12; ball('Hour marker',(-3.1+.34*math.sin(t),-6.98,4+.34*math.cos(t)),(.024,.02,.024),'dark')
# Tunnel arch aligned to the local rail tangent, x=30 entry.
angle=math.atan(.005*33); origin=Vector((31,route(31),0))
def tunnelpt(x,y,z): return tuple(origin+Vector((x*math.cos(angle)-y*math.sin(angle),x*math.sin(angle)+y*math.cos(angle),z)))
for k in range(17):
 a=k*math.pi/17; b=(k+1)*math.pi/17
 v=[]
 for d in [0,1.1]:
  for r,t in [(2.5,a),(3.45,a),(3.45,b),(2.5,b)]: v.append(tunnelpt(d,r*math.cos(t),2.1+r*math.sin(t)))
 mesh('Arch voussoir',v,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(3,2,6,7),(0,3,7,4),(1,5,6,2)],'cream' if k%3==0 else 'stone')
for side in [-1,1]:
 for j in range(4): box('Tunnel pier',tunnelpt(.55,side*2.97,.25+j*.54),(1.1,.94,.52),'stone',.04,angle)
# Dark interior horseshoe shell, no obstructing black plane.
for k in range(24):
 a=k*math.pi/24; b=(k+1)*math.pi/24
 mesh('Tunnel lining',[tunnelpt(x,2.48*math.cos(t),2.1+2.48*math.sin(t)) for x,t in [(1,a),(13,a),(13,b),(1,b)]],[(0,1,2,3)],'dark')
for side in [-1,1]:
 mesh('Tunnel side lining',[tunnelpt(x,side*2.48,z) for x,z in [(1,0),(13,0),(13,2.1),(1,2.1)]],[(0,1,2,3)],'dark')
# Rock mass above bore, with flanking masses left clear of the rail corridor.
for x,y,z,sc in [(39,19,5,(11,6,8)),(42,5,5,(8,4,7)),(40,13,8,(10,5,3.4)),(27,28,5,(9,8,8)),(8,36,7,(12,10,9)),(-18,39,6,(12,9,8)),(-39,33,5,(8,11,7))]:
 ball('Weathered mountain outcrop',(x,y,z),sc,'rock')
# benches, bags and station furniture
def bench(x,y):
 for dx in [-1,.95]:
  for dy in [-.28,.28]: box('Bench feet',(x+dx,y+dy,1.04),(.12,.12,.6),'metal',.025)
 for dy in [-.28,0,.28]: box('Bench seat slat',(x,y+dy,1.38),(2.5,.22,.13),'woodlight',.04)
 for z in [1.7,1.96]: box('Bench back slat',(x,y-.37,z),(2.5,.12,.21),'woodlight',.04)
 for dx in [-1,.95]: box('Bench back support',(x+dx,y-.38,1.65),(.10,.10,.85),'metal',.02)
for x in [-19,4,10]: bench(x,2.8)
for x in [-23,14]:
 cyl('Nameboard post',(x,3.3,1.85),.09,2.2,'roof')
 box('Nameboard',(x,3.3,2.7),(3.2,.16,.7),'roof',.09)
 text('Platform station name','ALDER PASS',(x,3.19,2.52),.33,'white')
for x,y in [(-23,4.5),(-1,4.5),(13,4.5),(-12,-14),(8,-16)]:
 z=.72 if y>0 else 0
 cyl('Lamp base',(x,y,z+.16),.26,.32,'metal'); cyl('Lamp pole',(x,y,z+1.85),.07,3.5,'roof')
 box('Lantern',(x,y,z+3.6),(.45,.45,.66),'gold',.1); box('Lantern cap',(x,y,z+3.98),(.65,.65,.15),'roof',.08)
for x,y in [(1,2.4),(1.8,2.4),(-18,2.3)]:
 box('Travel case',(x,y,1.13),(.62,.32,.78),'brick',.09)
 box('Case handle',(x,y,1.58),(.22,.08,.10),'metal',.03)
# Freight shelter and detailed strapped crates.
box('Freight deck',(19,-1,.35),(10,9,.7),'wood',.12)
for x in [14.5,23.5]:
 for y in [-5,3]: box('Freight shed post',(x,y,2.2),(.22,.22,3.7),'wood',.04)
box('Freight shed roof',(19,-1,4.2),(11,10,.32),'roof',.15)
for x,y,z in [(16,-3,1.4),(18,-3,1.4),(17,-3,2.8),(21,0,1.3),(21,-2,1.3)]:
 box('Shipping crate',(x,y,z),(1.6,1.5,1.3),'woodlight',.08)
 for dx in [-.6,.6]: box('Crate strap',(x+dx,y,z),(.10,1.54,1.35),'wood',.015)
 beam('Crate brace',(x-.66,y-.78,z-.50),(x+.66,y-.78,z+.50),.10,'wood')
text('Freight label','FREIGHT',(19,-5.99,3.52),.42,'white')
# Hill walking trail, curved through western slope.
trail=[(-18,-13),(-27,-18),(-34,-13),(-38,-4),(-36,8),(-31,18),(-22,25),(-10,28)]
for i in range(len(trail)-1):
 a=Vector((*trail[i],0)); b=Vector((*trail[i+1],0)); d=b-a; l=d.length
 for j in range(max(1,int(l*2))):
  p=a+d*(j/max(1,int(l*2))); box('Walking trail',(p.x,p.y,zground(p.x,p.y)+.06),(1.0,2.0,.10),'path',.25,math.atan2(d.y,d.x))
for i in range(16):
 x=-28+i*2.5; y=-22
 box('Forecourt fence post',(x,y,.8),(.18,.18,1.6),'wood',.05)
 if i<15:
  for z in [.65,1.2]: box('Fence rail',(x+1.25,y,z),(2.6,.13,.15),'woodlight',.025)
# Stylised conifers with tiered soft silhouettes and varied height.
def tree(x,y,h):
 z=zground(x,y); cyl('Pine trunk',(x,y,z+h*.29),.22,h*.58,'wood')
 for j,(r,d) in enumerate([(h*.28,h*.38),(h*.23,h*.57),(h*.17,h*.75)]):
  bpy.ops.mesh.primitive_cone_add(vertices=10,radius1=r,radius2=.12,depth=h*.43,location=(x,y,z+d)); finish(bpy.context.object,'Rounded pine tier','leaf' if j%2==0 else 'leaf2')
for i in range(100):
 x=random.uniform(-47,47); y=random.uniform(-45,46)
 if abs(y-route(x))<6 or (-29<x<28 and -25<y<8) or (x>25 and 0<y<25): continue
 if min(math.hypot(x-a,y-b) for a,b in trail)<3: continue
 tree(x,y,random.uniform(4,8))
for i in range(48):
 x=random.uniform(-47,47); y=random.uniform(-45,45)
 if abs(y-route(x))<5 or (-30<x<28 and -25<y<8): continue
 ball('Small hillside stone',(x,y,zground(x,y)+.3),(random.uniform(.5,1.3),.65,.65),'stone')
# Join by material for efficient imported geometry while preserving original objects in blend.
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'AlderPass.blend'))
bpy.ops.object.select_all(action='SELECT')
bpy.context.view_layer.objects.active=next(o for o in bpy.context.scene.objects if o.type=='MESH')
bpy.ops.object.join()
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'AlderPass.fbx'),use_selection=True,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',add_leaf_bones=False,bake_anim=False)
json.dump({'palette':palette,'site_cm':10000,'center':[0,0,0],'rail_curve_m':'y=8+0.0025*x*x','station':'Alder Pass','seed':117},open(os.path.join(OUT,'art_manifest.json'),'w'),indent=2)

