import bpy, math, random, json, time, os
from pathlib import Path
from mathutils import Vector

ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/NightMarket/max')
OUT=ROOT/'Source'/'Exports'; OUT.mkdir(parents=True,exist_ok=True)
TEX=ROOT/'Source'/'Textures'; TEX.mkdir(parents=True,exist_ok=True)
random.seed(231023)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC'; bpy.context.scene.unit_settings.scale_length=1.0
materials={}; groups={}; current='Ground'; semantic={}; lights=[]
palette={
 'Plinth':((0.13,0.19,0.24),0.65,0,'stone'),
 'Coping':((0.32,0.41,0.43),0.65,0,'stone'),
 'Paving':((0.16,0.23,0.27),0.28,0,'cobble'),
 'Court':((0.30,0.33,0.32),0.32,0,'cobble'),
 'Clay':((0.43,0.21,0.13),0.62,0,'plaster'),
 'Cream':((0.73,0.61,0.40),0.63,0,'plaster'),
 'Teal':((0.10,0.35,0.35),0.56,0,'plaster'),
 'Blue':((0.16,0.25,0.41),0.59,0,'plaster'),
 'Peach':((0.65,0.36,0.25),0.62,0,'plaster'),
 'Deep':((0.055,0.12,0.17),0.55,0,'plaster'),
 'Wood':((0.29,0.14,0.067),0.58,0,'wood'),
 'LightWood':((0.58,0.34,0.14),0.51,0,'wood'),
 'Roof':((0.13,0.25,0.29),0.46,0,'roof'),
 'RedRoof':((0.42,0.20,0.16),0.50,0,'roof'),
 'RedFabric':((0.66,0.17,0.12),0.68,0,'fabric'),
 'CreamFabric':((0.83,0.65,0.39),0.7,0,'fabric'),
 'TealFabric':((0.08,0.46,0.40),0.67,0,'fabric'),
 'DarkMetal':((0.08,0.12,0.14),0.3,0.7,None),
 'Brass':((0.48,0.28,0.085),0.3,0.75,None),
 'Steel':((0.40,0.49,0.51),0.25,0.85,None),
 'White':((0.86,0.78,0.60),0.31,0,None),
 'Porcelain':((0.58,0.76,0.70),0.22,0,None),
 'Red':((0.72,0.14,0.075),0.4,0,None),
 'Orange':((0.92,0.42,0.055),0.43,0,None),
 'Green':((0.19,0.49,0.17),0.45,0,None),
 'Leaf':((0.10,0.29,0.20),0.61,0,None),
 'Dough':((0.84,0.64,0.37),0.6,0,None),
 'Water':((0.055,0.14,0.20),0.065,0.45,None),
 'GlowGold':((1.0,0.38,0.09),0.35,0,None),
 'GlowCream':((1.0,0.73,0.34),0.35,0,None),
 'GlowMint':((0.10,0.8,0.72),0.3,0,None),
 'GlowCoral':((1.0,0.18,0.10),0.35,0,None),
 'GlassDark':((0.07,0.21,0.26),0.15,0.2,None),
}
for n,(color,rough,metal,tex) in palette.items():
 m=bpy.data.materials.new(n);m.diffuse_color=(*color,1);materials[n]=m

def add(o,mat='Wood'):
 o.data.materials.clear();o.data.materials.append(materials[mat]);groups.setdefault(current,[]).append(o)
 return o
def bevel(o,r=0.06):
 mod=o.modifiers.new('Soft edges','BEVEL');mod.width=r;mod.segments=2
 bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 return o
def box(name,loc,scale,mat='Wood',r=0.05,rot=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if r:bevel(o,min(r,min(scale)*.24))
 o.rotation_euler[2]=math.radians(rot);return add(o,mat)
def cylinder(name,loc,radius,depth,mat='Wood',vertices=16,rotation=None):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc,rotation=rotation or (0,0,0))
 o=bpy.context.object;o.name=name;bevel(o,min(radius*.16,.035));return add(o,mat)
def sphere(name,loc,scale,mat='Red',segments=12,rings=8):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for p in o.data.polygons:p.use_smooth=True
 return add(o,mat)
def mesh(name,verts,faces,mat):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);return add(o,mat)
def beam(name,a,b,r,mat='DarkMetal',verts=10):
 d=Vector(b)-Vector(a);o=cylinder(name,(Vector(a)+Vector(b))/2,r,d.length,mat,verts);o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return o
def tube(name,points,r,mat='DarkMetal'):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=1;sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
 for p,v in zip(sp.points,points):p.co=(*v,1)
 o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False);return add(o,mat)
def torus(name,loc,major,minor,mat='DarkMetal',rot=(0,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=20,minor_segments=6,location=loc,rotation=rot);o=bpy.context.object;o.name=name;return add(o,mat)
def text(name,label,loc,size,mat='GlowCream',rot=(90,0,0)):
 cu=bpy.data.curves.new(name,'FONT');cu.body=label;cu.align_x='CENTER';cu.align_y='CENTER';cu.size=size;cu.extrude=.012;cu.bevel_depth=.006;cu.bevel_resolution=1
 o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=tuple(math.radians(a) for a in rot)
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');o.select_set(False);return add(o,mat)
def roundrect(name,cx,cy,z,w,d,mat):
 return box(name,(cx,cy,z),(w,d,.05),mat,.2)

def lantern(x,y,z,r=.40,color='GlowGold',drop=.4):
 beam('lantern hanger',(x,y,z+drop),(x,y,z),.025)
 sphere('silk lantern',(x,y,z-r*.85),(r,r,r*1.05),color)
 cylinder('upper cap',(x,y,z),r*.55,.10,'Brass',12)
 cylinder('lower cap',(x,y,z-r*1.85),r*.5,.1,'Brass',12)
 for i in range(8):
  a=2*math.pi*i/8
  pts=[(x+math.sin(a)*r*math.sin(math.pi*t/10),y+math.cos(a)*r*math.sin(math.pi*t/10),z-.03-1.75*r*t/10) for t in range(11)]
  tube('lantern silk rib',pts,.009,'Brass')
 beam('tassel',(x,y,z-r*1.90),(x,y,z-r*2.35),.025,'RedFabric')

def crate(x,y,z=0.4,w=1.15,d=.85,produce=None):
 box('crate base',(x,y,z+.06),(w,d,.12),'Wood',.025)
 for s in [-1,1]:
  for h in [.18,.43]:box('crate slat',(x,y+s*d/2,z+h),(w,.08,.19),'LightWood',.018)
  for h in [.18,.43]:box('crate end',(x+s*w/2,y,z+h),(.08,d,.19),'LightWood',.018)
  for v in [-1,1]:box('crate corner',(x+s*w*.46,y+v*d*.44,z+.28),(.09,.09,.58),'Wood',.015)
 if produce:
  for a in range(4):
   for b in range(3):
    xx=x+(a-1.5)*w*.21;yy=y+(b-1)*d*.25
    sphere('fresh '+produce,(xx,yy,z+.52),(.13,.13,.13),produce,10,6)
    if produce=='Orange':beam('stem',(xx,yy,z+.63),(xx,yy,z+.69),.014,'Leaf',6)

def stool(x,y,z=.35):
 cylinder('stool seat',(x,y,z+.55),.36,.14,'LightWood',16)
 for a in range(4):
  t=a*math.pi/2+math.pi/4;beam('stool leg',(x+math.cos(t)*.28,y+math.sin(t)*.28,z),(x+math.cos(t)*.21,y+math.sin(t)*.21,z+.52),.055,'Wood')
def bowl(x,y,z,r=.23):
 sphere('bowl',(x,y,z), (r,r,r*.52),'Porcelain')
 cylinder('soup',(x,y,z+r*.27),r*.83,.015,'Clay',18)
 torus('bowl lip',(x,y,z+r*.23),r*.87,.027,'White')
 for q in [-1,1]:beam('chopstick',(x-.28,y+q*.07,z+.13),(x+.23,y+q*.07,z+.19),.012,'LightWood',6)

def pot(x,y,z):
 cylinder('stockpot',(x,y,z+.30),.43,.60,'Steel',20);torus('pot lip',(x,y,z+.61),.43,.035,'Steel')
 cylinder('broth',(x,y,z+.59),.37,.01,'Clay',20)
 for s in [-1,1]:torus('pot handle',(x+s*.46,y,z+.40),.12,.035,'DarkMetal',(math.pi/2,0,0))
 beam('ladle',(x+.15,y,z+.45),(x+.36,y,z+.95),.022,'LightWood')

def bike(x,y,z=.35,rot=0):
 start=len(groups.setdefault(current,[]))
 for xx in [-.75,.75]:
  torus('bicycle tyre',(x+xx,y,z+.51),.49,.052,'DarkMetal',(math.pi/2,0,0))
  torus('wheel rim',(x+xx,y,z+.51),.42,.022,'Steel',(math.pi/2,0,0))
  for i in range(10):
   a=i*math.pi/5;beam('spoke',(x+xx,y,z+.51),(x+xx+.42*math.cos(a),y,z+.51+.42*math.sin(a)),.009,'Steel',6)
 a=(x-.75,y,z+.51);b=(x-.25,y,z+1.14);c=(x,y,z+.52);d=(x+.50,y,z+1.15);e=(x+.75,y,z+.51)
 for aa,bb in [(a,b),(b,c),(c,a),(b,d),(d,c),(d,e)]:beam('bike frame',aa,bb,.043,'TealFabric')
 box('saddle',(x-.25,y,z+1.25),(.38,.24,.09),'Wood',.04)
 beam('handlebar neck',d,(x+.49,y,z+1.40),.035,'Steel');beam('handlebar',(x+.49,y-.25,z+1.40),(x+.49,y+.25,z+1.40),.035,'Steel')
 box('front basket',(x+.83,y,z+1.12),(.42,.47,.35),'LightWood',.04)
 if rot:
  for ob in groups[current][start:]:
   v=ob.location-Vector((x,y,z));a=math.radians(rot);ob.location=Vector((x+v.x*math.cos(a)-v.y*math.sin(a),y+v.x*math.sin(a)+v.y*math.cos(a),z+v.z));ob.rotation_euler[2]+=a

def building(name,x,y,w,d,h,wall='Cream',roof='Roof',sign='TEA HOUSE'):
 global current
 current='Building_'+name;semantic[current]={'type':'shopfront','label':sign,'footprint_m':[x,y,w,d],'height_m':h}
 box('raised shop base',(x,y,.55),(w+.65,d+.65,.5),'Coping',.15)
 box('plaster building',(x,y,.9+h/2),(w,d,h),wall,.25)
 # Horizontal color-band and deep inset facade on south side.
 for zz in [1.05,4.5, h+.85]:box('continuous timber cornice',(x,y,zz),(w+.30,d+.30,.23),'Wood',.05)
 fy=y-d/2-.10
 for xx in [x-w/2+.35,x+w/2-.35]:box('corner post',(xx,fy,(h+.9)/2),(.27,.35,h+.6),'Wood',.05)
 for xx in [x-w*.28,x+w*.28]:
  box('shop window surround',(xx,fy-.10,2.6),(w*.33,.30,2.75),'Wood',.06)
  box('shop luminous window',(xx,fy-.28,2.6),(w*.30,.045,2.45),'GlowCream',.03)
  for j in [-1,0,1]:box('window mullion',(xx+j*w*.09,fy-.33,2.6),(.075,.10,2.45),'Wood',.02)
  for zz in [1.95,2.75]:box('window bar',(xx,fy-.34,zz),(w*.31,.10,.07),'Wood',.015)
 box('door frame',(x,fy-.18,2.3),(1.7,.31,3.0),'Wood',.06)
 box('door pane',(x,fy-.36,2.25),(1.4,.06,2.7),'GlassDark',.03)
 beam('door handle',(x+.45,fy-.46,2.05),(x+.45,fy-.46,2.45),.04,'Brass')
 # Upper bays, balconies, drain pipes and rooftop details.
 for floor in range(1,max(2,int(h/3.5))):
  zz=5.7+(floor-1)*3.25
  if zz>h-.3:continue
  for xx in [x-w*.30,x,x+w*.30]:
   box('upper window surround',(xx,fy-.1,zz),(1.85,.22,2.05),'Wood',.06)
   box('upper window',(xx,fy-.24,zz),(1.60,.035,1.78),'GlowGold' if (floor+int(xx))%3 else 'GlassDark',.03)
   box('window cross',(xx,fy-.30,zz),(.07,.09,1.8),'Wood',.02);box('window cross',(xx,fy-.30,zz),(1.65,.09,.07),'Wood',.02)
   box('window ledge',(xx,fy-.4,zz-1.02),(2.1,.70,.15),'Coping',.04)
  if floor==1:
   box('balcony',(x,fy-.80,zz-1.10),(w*.78,1.50,.20),'Wood',.07)
   for q in range(13):box('balcony spindle',(x-w*.36+q*w*.06,fy-1.5,zz-.55),(.07,.07,1.0),'Wood',.02)
   box('balcony railing',(x,fy-1.5,zz-.02),(w*.80,.15,.15),'LightWood',.04)
 # Pitched low hip roof in two faces, solid wedge; ridge ornaments.
 z=h+1.05;over=.7
 verts=[(x-w/2-over,y-d/2-over,z),(x+w/2+over,y-d/2-over,z),(x+w/2+over,y+d/2+over,z),(x-w/2-over,y+d/2+over,z),
        (x-w*.44,y,z+1.7),(x+w*.44,y,z+1.7)]
 ob=mesh('hip roof',verts,[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4),(3,2,1,0)],roof);bevel(ob,.10)
 beam('roof ridge',(x-w*.47,y,z+1.72),(x+w*.47,y,z+1.72),.13,'Coping',12)
 for q in range(int(w/.58)):
  xx=x-w/2+q*.58
  beam('roof tile seam',(xx,y-d/2-.55,z+.08),(xx,y,z+1.75),.045,roof,6)
  beam('roof tile seam',(xx,y,z+1.75),(xx,y+d/2+.55,z+.08),.045,roof,6)
 box('chimney',(x+w*.3,y+d*.18,z+1.3),(.9,.9,2),'Clay',.10);box('chimney cap',(x+w*.3,y+d*.18,z+2.35),(1.25,1.25,.22),'Coping',.07)
 # Individual canvas shop awning, face aligned readable signage.
 awning(x,fy-1.0,4.4,w*.88,2.3,'TealFabric' if wall in ['Cream','Peach'] else 'RedFabric')
 box('main sign',(x,fy-.38,4.52),(w*.87,.27,.94),'Deep',.10)
 text('shop name',sign,(x,fy-.54,4.53),min(.62,w*.8/max(len(sign),1)*1.55),'GlowCream')
 # side sign projects into pedestrian lane
 sx=x+w/2+.18
 box('vertical sign',(sx,fy+.4,6.4),(.24,1.8,3.2),'Deep',.08)
 for i,word in enumerate(['N','I','G','H','T']):text('vertical letter',word,(sx+.15,fy+.4,7.45-i*.48),.43,'GlowMint',(90,0,90))
 for xx in [x-w*.38,x+w*.38]:lantern(xx,fy-2.0,4.05,.38)
 lights.append({'name':'shop_'+name,'location':[x,fy-2,3.3],'color':[1,.59,.30],'intensity':650,'radius':7.5})
 # Side paneling prevents empty box silhouettes.
 for side in [-1,1]:
  for q in range(3):
   yy=y-d*.28+q*d*.28
   box('side frame',(x+side*(w/2+.08),yy,6.5),(.20,1.65,2.3),'Wood',.06)
   box('side lit window',(x+side*(w/2+.20),yy,6.5),(.025,1.42,2.05),'GlowGold' if q%2 else 'GlassDark',.02)
  tube('drain pipe',[(x+side*w*.45,y+d*.51,h+.7),(x+side*w*.45,y+d*.51,1.0),(x+side*w*.48,y+d*.56,.65)],.065,'DarkMetal')

def awning(x,y,z,w,d,color):
 # Flat-topped fabric slopes toward customer, made of alternating tailored strips.
 stripes=max(4,int(w/.6))
 for q in range(stripes):
  xa=x-w/2+q*w/stripes;xb=xa+w/stripes
  verts=[(xa,y+d/2,z+.45),(xb,y+d/2,z+.45),(xb,y-d/2,z),(xa,y-d/2,z),
         (xa,y+d/2,z+.39),(xb,y+d/2,z+.39),(xb,y-d/2,z-.06),(xa,y-d/2,z-.06)]
  mesh('canvas stripe',verts,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],color if q%3 else 'CreamFabric')
  box('scalloped valance',(xa+w/stripes/2,y-d/2-.02,z-.18),(w/stripes-.015,.10,.35),color if q%3 else 'CreamFabric',.10)
 for xx in [x-w/2+.08,x+w/2-.08]:beam('canopy support',(xx,y-d/2,z),(xx,y-d/2,.40),.075,'Wood')
 beam('canopy edge',(x-w/2,y-d/2,z+.03),(x+w/2,y-d/2,z+.03),.055,'Brass')

def stall(name,x,y,kind,color='RedFabric',rot=0):
 global current
 current='Stall_'+name;semantic[current]={'type':'food_cart','kind':kind,'position_m':[x,y]}
 # Components are built facing -Y then optionally rotated as a group.
 box('cart body',(x,y,1.15),(4.7,2.5,1.5),'Teal' if color=='TealFabric' else 'Clay',.14)
 box('serving counter',(x,y-.18,1.98),(5.1,2.9,.22),'LightWood',.08)
 for xx in [-1.7,1.7]:
  for yy in [-.83,.83]:cylinder('cart wheel',(x+xx,y+yy,.67),.40,.18,'DarkMetal',16,(math.pi/2,0,0))
 for q in range(12):box('counter slat',(x-2.2+q*.4,y-1.30,1.16),(.32,.08,1.30),'Wood',.035)
 awning(x,y,4.1,5.8,3.7,color)
 box('stall signboard',(x,y-1.90,3.55),(4.45,.18,.66),'Deep',.07)
 text('stall sign',kind,(x,y-2.01,3.55),.47,'GlowCream')
 for xx in [-2.2,2.2]:lantern(x+xx,y-1.93,3.4,.29,color='GlowCoral' if color=='TealFabric' else 'GlowGold')
 # Back shelf and jars create complete inhabited silhouette.
 box('back shelf',(x,y+1.07,2.62),(4.6,.35,.12),'LightWood',.03)
 for q in range(9):
  xx=x-1.9+q*.47
  cylinder('spice jar',(xx,y+1.06,2.87),.14,.40,'Porcelain' if q%2 else 'Clay',10)
  cylinder('jar lid',(xx,y+1.06,3.09),.16,.07,'Wood',10)
 if 'NOODLE' in kind or 'SOUP' in kind:
  pot(x-.9,y,2.10);pot(x+.2,y+.2,2.1)
  for q in range(4):bowl(x-1.6+q*.9,y-1.05,2.12)
  # Distinct curved stylized static steam, deliberately documented, no simulation.
  for q in [-1,0,1]:tube('curl of steam',[(x-.9+q*.2+.10*math.sin(i*.8),y+.08*math.cos(i),2.8+i*.13) for i in range(12)],.025,'White')
 elif 'TEA' in kind:
  for q in range(5):
   cylinder('tea tin',(x-1.5+q*.75,y+.3,2.32),.22,.45,'Porcelain',16)
   cylinder('tea tin lid',(x-1.5+q*.75,y+.3,2.57),.24,.05,'Brass',16)
   bowl(x-1.5+q*.75,y-.75,2.15,.15)
  sphere('teapot',(x,y-.1,2.37),(.35,.30,.27),'Clay');tube('teapot spout',[(x+.24,y-.1,2.4),(x+.45,y-.1,2.57)],.065,'Clay')
 elif 'FRUIT' in kind or 'GREENS' in kind:
  for q,pr in enumerate(['Orange','Red','Green']):crate(x-1.55+q*1.55,y-.25,2.1,1.35,1.7,pr)
 else:
  for q in range(3):
   xx=x-1.55+q*1.55
   box('display tray',(xx,y-.25,2.13),(1.3,1.5,.08),'Steel',.08)
   for i in range(3):
    for j in range(3):
     sphere('steamed bun' if 'BUN' in kind else 'golden pastry',(xx+(i-1)*.35,y-.25+(j-1)*.40,2.31),(.15,.16,.12),'Dough',10,6)
   if 'BUN' in kind:torus('bamboo steamer',(xx,y-.25,2.26),.60,.055,'LightWood')
 box('menu board',(x+3.1,y-.6,1.45),(.1,1.0,1.6),'Deep',.05,rot=0)
 crate(x-3.0,y+.4,.4,1.0,.8,'Green' if 'GREENS' in kind else None)
 if rot:
  a=math.radians(rot)
  for ob in groups[current]:
   vx,vy=ob.location.x-x,ob.location.y-y;ob.location.x=x+vx*math.cos(a)-vy*math.sin(a);ob.location.y=y+vx*math.sin(a)+vy*math.cos(a);ob.rotation_euler.z+=a
 lights.append({'name':'stall_'+name,'location':[x,y-1.8,3.1],'color':[1,.47,.19],'intensity':420,'radius':6})

# Terrain: exact 100 m square rounded diorama, no scene resource outside footprint.
current='Ground'
box('100m rounded foundation',(0,0,-1.15),(100,100,2.3),'Plinth',1.2)
box('foundation upper trim',(0,0,-.05),(99,99,.38),'Coping',.35)
box('wet pavement',(0,0,.18),(97.7,97.7,.28),'Paving',.35)
box('central lantern court',(0,-1,.36),(30,30,.18),'Court',.8)
# Broad irregular inset lanes and curb strips.
for x,y,w,d in [(-26,-1,2,74),(25,-2,2,75),(0,26,70,1.1),(0,-29,71,1.1)]:box('drainage border',(x,y,.37),(w,d,.12),'Coping',.08)
for y in [-39,-32,-25,25,32,39]:
 for x in [-19,-15,-11,-7,-3,1,5,9,13,17,21]:box('lane setts',(x,y,.355),(3.3,.13,.025),'Coping',.01)
for x in [-47,47]:box('edge curb',(x,0,.53),(1.0,92,.36),'Coping',.18)
for y in [-47,47]:box('edge curb',(0,y,.53),(92,1.0,.36),'Coping',.18)
# Puddle silhouettes are shallow irregular solids, independent from walkable base.
current='Puddles'
for x,y,w,d in [(-9,-25,5,2), (12,-20,4,2.2),(-22,-5,2.5,4.2),(19,7,3,2), (2,20,4,2.1), (32,-17,4.3,1.5),(-5,-38,5,1.4),(-18,30,3,1.4),(37,18,3,2),(-36,-24,3,1.8)]:
 verts=[];n=28
 for i in range(n):
  a=i*2*math.pi/n;rr=1+.10*math.sin(a*5)+.07*math.cos(a*3);verts.append((x+math.cos(a)*w*rr,y+math.sin(a)*d*rr,.386))
 o=mesh('rain puddle',verts,[tuple(range(n))],'Water')
 # Hand-placed tiny edge highlights remain clearly an art approximation.
 for k in range(2):tube('puddle rim',[(x+math.cos(a)*w*.72,y+math.sin(a)*d*.72,.405) for a in [k*2+.2+j*.10 for j in range(11)]],.017,'Coping')

# Perimeter architecture, kept low towards the overview camera foreground.
building('MoonTea',-32,31,17,13,12,'Teal','Roof','MOON TEA')
building('NoodleHouse',-12,35,17,12,16,'Cream','RedRoof','NOODLE HOUSE')
building('BlueInn',10,35,20,14,18,'Blue','Roof','THE BLUE INN')
building('LanternSupply',33,31,17,13,12,'Peach','Roof','LANTERN & CO')
building('EastGrocer',36,9,15,14,10,'Teal','RedRoof','DAILY GREENS')
building('EastBakery',37,-13,14,13,8,'Cream','Roof','WARM BUNS')
building('WestKitchen',-36,8,14,15,11,'Peach','Roof','STEAM KITCHEN')
building('WestBooks',-36,-13,14,14,8,'Blue','RedRoof','AFTER HOURS')
building('CornerCafe',-34,-34,15,13,7,'Teal','Roof','LITTLE CAFE')
building('NightFlorist',35,-35,14,12,6.5,'Peach','Roof','NIGHT BLOOM')

# Central circulation encircles a small social court; front-facing hero carts.
stall('Noodles',-9,-9,'MIDNIGHT NOODLES','RedFabric')
stall('Tea',8,-8,'MOONLIGHT TEA','TealFabric')
stall('Buns',-10,8,'STEAMED BUNS','CreamFabric')
stall('Fruit',9,9,'FRESH FRUIT','RedFabric')
stall('Soup',-20,18,'SOUP & RICE','TealFabric',-12)
stall('Greens',20,19,'GARDEN GREENS','TealFabric',10)
stall('Pastry',-19,-21,'HONEY CAKES','CreamFabric',-8)
stall('Dumplings',19,-23,'DUMPLINGS','RedFabric',8)
stall('LateTea',-2,23,'LATE NIGHT TEA','TealFabric')
stall('BunsSouth',0,-34,'BAO & BUNS','RedFabric')

current='CourtFurniture';semantic[current]={'type':'social_court'}
for x,y in [(-2,-2),(6,0),(-8,0),(14,-3),(-13,-15),(10,-15),(4,14)]:
 cylinder('round table top',(x,y,1.35),.85,.16,'LightWood',20)
 cylinder('table pedestal',(x,y,.89),.13,.85,'DarkMetal',12)
 cylinder('table foot',(x,y,.45),.48,.10,'DarkMetal',16)
 for a in [20,150,270]:stool(x+1.35*math.cos(math.radians(a)),y+1.35*math.sin(math.radians(a)))
 bowl(x-.30,y,1.48);bowl(x+.30,y+.1,1.48,.19)
for x,y in [(-23,-12),(23,-10),(-29,-24),(27,26)]:bike(x,y,rot=20 if x<0 else -15)
# Crates, sacks, barrels and a handcart around service edges.
current='StreetProps'
for x,y in [(-26,25),(25,26),(-28,-3),(29,-3),(-28,-21),(27,-22),(-17,29)]:
 crate(x,y,.4,1.5,1.05,'Orange');crate(x+1.6,y+.3,.4,1.3,.9)
 cylinder('barrel',(x,y+1.5,1.04),.55,1.25,'Wood',16)
 for zz in [.55,1.05,1.55]:torus('barrel hoop',(x,y+1.5,zz),.55,.035,'DarkMetal')
 sphere('rice sack',(x+1.4,y+1.5,.92),(.42,.35,.60),'CreamFabric')
# handcart
box('handcart bed',(27,-32,.94),(2.8,1.6,.17),'LightWood',.07)
for y in [-32.9,-31.1]:cylinder('handcart wheel',(27,y,.85),.65,.16,'DarkMetal',20,(math.pi/2,0,0))
for yy in [-32.6,-31.4]:beam('handcart handle',(28,yy,1.0),(30,yy,1.4),.09,'Wood')
crate(26.4,-32,1.05,1.2,1.1,'Green');crate(27.7,-32,1.05,1.15,1.1,'Orange')

# Central lantern web: hand-authored drooping strings preserve sky and sight lines.
current='LanternCanopy';semantic[current]={'type':'overhead_lantern_network'}
for x in [-23,23]:
 for y in [-25,23]:
  cylinder('lantern post',(x,y,4.1),.15,7.5,'Wood',14)
  cylinder('post foot',(x,y,.70),.38,.60,'Coping',14)
  sphere('post finial',(x,y,7.94),(.24,.24,.30),'Brass')
for y in [-24,-12,1,14,23]:
 z=7.5+(y%3)*.25;points=[(-23+46*t/48,y,z-1.55*math.sin(math.pi*t/48)) for t in range(49)]
 tube('sagging lantern wire',points,.026,'DarkMetal')
 for k in range(10):
  x=-21+k*4.67;h=z-1.55*math.sin(math.pi*(x+23)/46)
  lantern(x,y,h-.22,.33 if k%3 else .44,'GlowGold' if k%3 else 'GlowCoral',.22)
for x in [-22,22]:
 tube('longitudinal wire',[(x,-25+48*t/36,7.5-.8*math.sin(math.pi*t/36)) for t in range(37)],.027,'DarkMetal')
for x,y in [(-16,-18),(0,-17),(16,-17),(-16,3),(0,4),(16,4),(-14,18),(14,18)]:lights.append({'name':'court_lantern','location':[x,y,6.0],'color':[1,.50,.24],'intensity':650,'radius':10})

# Front welcome gate, side information boards and perimeter planters.
current='EntryGate';semantic[current]={'type':'entrance','label':'LANTERN MARKET'}
for x in [-9,9]:box('gate post',(x,-43,3.9),(.55,.55,7.2),'Wood',.12)
box('gate lintel',(0,-43,7.40),(19.5,.65,.55),'Wood',.14)
box('welcome sign',(0,-43,6.6),(13.8,.38,1.20),'Deep',.18)
text('welcome lettering','LANTERN MARKET',(0,-43.24,6.62),.87,'GlowCream')
text('entry small type','OPEN AFTER SUNSET',(0,-43.25,5.90),.30,'GlowMint')
for x in [-8,8]:lantern(x,-43,6.65,.58,'GlowGold')
lights.append({'name':'entry','location':[0,-42,6],'color':[1,.55,.28],'intensity':1600,'radius':14})
current='Gardens'
for x,y in [(-44,-43),(44,-43),(-44,-23),(44,25),(-44,22),(-22,43),(29,44),(23,-38),(-24,-38)]:
 box('stone planter',(x,y,.98),(2.5,2.5,1.3),'Coping',.22)
 box('planter soil',(x,y,1.63),(2.10,2.10,.08),'Wood',.14)
 beam('small tree trunk',(x,y,1.6),(x+.1,y,4.3),.14,'Wood')
 for q in range(7):
  a=q*math.pi*2/7;xx=x+math.cos(a)*.85;yy=y+math.sin(a)*.85
  beam('branch',(x,y,3.1),(xx,yy,4.1),.075,'Wood')
  sphere('rounded tree foliage',(xx,yy,4.2+(q%2)*.4),(.92,.82,.80),'Leaf',12,8)
 sphere('tree crown',(x,y,4.95),(1.20,1.13,1.10),'Green',12,8)
for x in [-44,44]:
 for y in [-8,10,39]:
  cylinder('streetlight base',(x,y,.70),.40,.55,'Coping')
  cylinder('streetlight pole',(x,y,3.1),.10,4.8,'DarkMetal')
  cylinder('lamp roof',(x,y,5.65),.53,.16,'DarkMetal',8)
  box('street lantern',(x,y,5.32),(.60,.60,.55),'GlowCream',.10)
  lights.append({'name':'perimeter_lamp','location':[x,y,5.1],'color':[.55,.74,1.0],'intensity':1100,'radius':10})

# Source textures: deterministic and entirely authored here, authored in linear RGB.
import numpy as np
for style in ['stone','cobble','plaster','wood','roof','fabric']:
 n=1024 if style=='cobble' else 512
 yy,xx=np.mgrid[0:n,0:n].astype(np.float32);u=xx/n;v=yy/n
 rng=np.random.default_rng(231023+len(style));noise=rng.random((n,n),dtype=np.float32)
 field=.84+.10*noise+.035*np.sin(u*61+np.sin(v*31))+.02*np.cos(v*47)
 if style=='cobble':
  row=np.floor(v*8);ux=(u*8+(row%2)*.5)%1;vy=(v*8)%1
  seam=np.minimum(np.minimum(ux,1-ux),np.minimum(vy,1-vy));field*=np.where(seam<.035,.56,1.0)
  field+=.035*np.sin(np.floor(u*8+(row%2)*.5)*2.1+row*1.7)
 elif style=='wood':field+=.075*np.sin(u*160+np.sin(v*11)*1.5)+.025*np.sin(u*380+v*8)
 elif style=='fabric':field+=.023*np.sin(u*804)+.023*np.sin(v*804)
 elif style=='roof':field*=np.where(((u*10)%1<.055)|((v*10)%1<.055),.69,1.0)
 elif style=='plaster':field+=.03*np.sin(u*11)*np.cos(v*17)
 pix=np.empty((n,n,4),dtype=np.float32);pix[:,:,:3]=np.clip(field[:,:,None],0,1);pix[:,:,3]=1
 image=bpy.data.images.new('T_'+style,width=n,height=n,alpha=True);image.pixels.foreach_set(pix.reshape(-1));image.filepath_raw=str(TEX/('T_'+style+'.png'));image.file_format='PNG';image.save();bpy.data.images.remove(image)

# Join each scene assembly, transform to world-space, ensure outward winding and metric UVs.
report={'source':'Original deterministic Blender authoring; no external geometry or textures','uv':{'method':'Dominant-normal planar tiling per face after transforms','world_tile_m':4.0,'texture_size_px':{'cobble':1024,'other':512},'density_px_per_m':{'cobble':256,'other':128},'overlap':'Intentional repeating planar UV overlap, not a unique lightmap atlas','padding':'Not applicable to tileable UVs; no atlas borders','exceptions':'Curved/beveled surfaces and text use dominant-axis projections and therefore local distortion; all mesh loops have finite UV coordinates'},'meshes':[],'materials':{},'semantic_groups':semantic,'lights':lights,'footprint_m':[100,100]}
for name,(rgb,rough,metal,style) in palette.items():report['materials'][name]={'color':rgb,'roughness':rough,'metallic':metal,'texture':('T_'+style) if style else None,'emissive':3.5 if name.startswith('Glow') else 0.0}
for key,obs in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for ob in obs:ob.select_set(True)
 bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();ob=bpy.context.object;ob.name='SM_NM_'+key
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
 me=ob.data
 while len(me.uv_layers):me.uv_layers.remove(me.uv_layers[0])
 uv=me.uv_layers.new(name='UV_Metric4m')
 for face in me.polygons:
  no=face.normal;axis=max(range(3),key=lambda i:abs(no[i]))
  axes=[i for i in range(3) if i!=axis]
  for li in face.loop_indices:
   co=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]]/4,co[axes[1]]/4)
 verts=[v.co for v in me.vertices];mins=[min(v[i] for v in verts) for i in range(3)];maxs=[max(v[i] for v in verts) for i in range(3)]
 # Signed volume is a practical orientation check for closed source components.
 me.calc_loop_triangles();signed_volume=sum(me.vertices[t.vertices[0]].co.dot(me.vertices[t.vertices[1]].co.cross(me.vertices[t.vertices[2]].co))/6 for t in me.loop_triangles)
 uv_count=len(uv.data);finite=all(math.isfinite(c) for d in uv.data for c in d.uv)
 report['meshes'].append({'name':ob.name,'file':ob.name+'.fbx','vertices':len(me.vertices),'triangles':len(me.loop_triangles),'bounds_min_m':mins,'bounds_max_m':maxs,'uv_loops':uv_count,'uv_finite':finite,'signed_volume_m3':signed_volume,'materials':[m.name for m in me.materials]})
 bpy.ops.export_scene.fbx(filepath=str(OUT/(ob.name+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Y',axis_up='Z',bake_space_transform=False,use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=True,path_mode='AUTO',add_leaf_bones=False)
 print('EXPORTED',ob.name,len(me.loop_triangles),flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Source'/'NightMarket_Source.blend'))
(ROOT/'Source'/'source_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('NIGHT_MARKET_SOURCE_COMPLETE',len(report['meshes']),sum(m['triangles'] for m in report['meshes']),flush=True)
