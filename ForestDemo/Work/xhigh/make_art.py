"""Quiet Cove original geometry. Run with Blender --background --python."""
import bpy, bmesh, math, random, json, os
from mathutils import Vector
from math import sin, cos, pi, exp, sqrt

ROOT = r'D:/github/AstraEffort/ForestDemo/Work/xhigh'
OUT = ROOT + '/SourceArt'
os.makedirs(OUT, exist_ok=True)
random.seed(82161)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1.0

PALETTE = {
 'Bark': (.22,.14,.085), 'BarkLight': (.33,.23,.14),
 'LeafSage': (.27,.39,.20), 'LeafMoss': (.19,.30,.14),
 'LeafLight': (.37,.46,.24), 'Pine': (.14,.28,.23), 'PineTips': (.23,.36,.27),
 'Stone': (.39,.42,.38), 'StoneLight': (.51,.52,.44), 'StoneDark': (.27,.32,.30),
 'Grass': (.32,.42,.21), 'Reed': (.43,.44,.23), 'RushTip': (.25,.21,.13),
 'Petal': (.70,.65,.40), 'Wood': (.39,.28,.16), 'EndGrain': (.55,.41,.25),
 'WaterLake': (.095,.30,.31), 'WaterSea': (.12,.35,.39), 'Foam': (.53,.66,.61),
 'Terrain': (.35,.44,.25), 'Sand': (.64,.57,.40), 'Path': (.50,.43,.30),
}
mats = {}
for name, col in PALETTE.items():
 m = bpy.data.materials.new(name); m.diffuse_color = (*col,1); mats[name]=m

parts=[]
def add(obj, mat, smooth=True):
 obj.data.materials.clear(); obj.data.materials.append(mats[mat])
 if smooth:
  for p in obj.data.polygons: p.use_smooth=True
 parts.append(obj); return obj
def ico(loc, scale, mat, sub=2, rough=.07):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=1, location=loc)
 o=bpy.context.object
 for v in o.data.vertices:
  v.co *= 1+random.uniform(-rough,rough)
 o.scale=scale
 bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
 return add(o,mat)
def tube(points,radii,mat, sides=10):
 verts=[]; faces=[]
 for i,p in enumerate(points):
  tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
  tangent.normalize(); side=tangent.cross(Vector((0,1,0))).normalized(); other=tangent.cross(side).normalized()
  for k in range(sides):
   a=k*2*pi/sides; verts.append(Vector(p)+radii[i]*(cos(a)*side+sin(a)*other))
 for i in range(len(points)-1):
  for k in range(sides):
   a=i*sides+k; b=i*sides+(k+1)%sides; faces.append((a,b,b+sides,a+sides))
 faces.extend([tuple(reversed(range(sides))), tuple((len(points)-1)*sides+k for k in range(sides))])
 me=bpy.data.meshes.new('OrganicTube');me.from_pydata(verts,[],faces);me.update()
 o=bpy.data.objects.new('OrganicTube',me);bpy.context.collection.objects.link(o);return add(o,mat)
def box(loc,scale,mat,bevel=.06,rot=0):
 bpy.ops.mesh.primitive_cube_add(size=1, location=loc);o=bpy.context.object;o.scale=scale;o.rotation_euler.z=rot
 bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
 mod=o.modifiers.new('Soft crafted edges','BEVEL');mod.width=bevel;mod.segments=3
 bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 return add(o,mat)
manifest={'palette':PALETTE,'meshes':{},'instances':[],'regions':{}}
def export(name, collision=True):
 global parts
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0]
 bpy.ops.object.join();obj=bpy.context.object;obj.name=name
 # Every prototype keeps its true origin at zero.
 bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
 # UE FBX importer changes handedness by reflecting Y. Compensate source export
 # so scene_manifest coordinates and sampled terrain remain identical in UE.
 for v in obj.data.vertices:v.co.y=-v.co.y
 bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update()
 bpy.ops.export_scene.fbx(filepath=OUT+'/'+name+'.fbx',use_selection=True,object_types={'MESH'},
   add_leaf_bones=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,
   bake_anim=False,use_mesh_modifiers=True,mesh_smooth_type='FACE',colors_type='LINEAR')
 manifest['meshes'][name]={'materials':[m.name for m in obj.data.materials], 'collision':collision,
  'vertices':len(obj.data.vertices),'polygons':len(obj.data.polygons)}
 obj.hide_set(True); parts=[]
 return obj

# Sculpted broadleaf variants: bent trunk, branching forks and interlocking rounded crown.
for variant in range(3):
 h=[7.8,9.3,6.4][variant]
 tube([(0,0,0),(.12,-.08,h*.24),(-.1,.1,h*.51),(.22,0,h*.76)], [.44,.34,.24,.12],'Bark',12)
 for a in [0.3,2.3,4.4]:
  d=Vector((cos(a),sin(a),0)); p=d*1.5
  tube([(.02,0,h*.38),tuple(d*.7+Vector((0,0,h*.57))),tuple(p+Vector((0,0,h*.70)))],[.22,.15,.06],'BarkLight',8)
 for i,(x,y,z,s) in enumerate([(-1.35,.5,.74,1.0),(1.3,.4,.76,1.05),(.0,-1.25,.80,1.12),(-.1,.4,.96,1.15),(-1.1,-.9,.87,.88),(1.0,1.1,.86,.9)]):
  ico((x*h/8,y*h/8,z*h),(2.0*s*h/8,1.9*s*h/8,1.65*s*h/8),['LeafMoss','LeafSage','LeafLight'][(i+variant)%3],3,.055)
 for a in [0,1.5,3,4.5]:
  tube([(cos(a)*.95,sin(a)*.95,.02),(cos(a)*.35,sin(a)*.35,.22),(0,0,.8)],[.07,.18,.23],'Bark',8)
 export('SM_Broadleaf_'+str(variant))

for variant in range(2):
 h=[10.3,7.9][variant]
 tube([(0,0,0),(.1,.02,h*.5),(0,0,h)],[.35,.22,.025],'Bark',10)
 for tier,(z,rad,height) in enumerate([(h*.27,2.35,h*.45),(h*.49,1.9,h*.38),(h*.68,1.35,h*.32)]):
  vs=[];fs=[];n=24
  for t,r in [(0,.72),(.09,1),(.25,.95),(.51,.68),(.78,.34),(1,.02)]:
   for k in range(n):
    a=k*2*pi/n; rr=rad*r*(1+.045*sin(k*3+variant)); vs.append((cos(a)*rr,sin(a)*rr,z+height*t+.035*sin(k*2)))
  for q in range(5):
   for k in range(n):a=q*n+k;b=q*n+(k+1)%n;fs.append((a,b,b+n,a+n))
  fs.append(tuple(reversed(range(n))))
  me=bpy.data.meshes.new('WhorledPine');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('WhorledPine',me);bpy.context.collection.objects.link(o);add(o,'Pine' if tier<2 else 'PineTips')
 export('SM_Pine_'+str(variant))

for variant in range(4):
 ico((0,0,.65), (1.4+variant*.18,1.05+variant*.1,.94+variant*.12),'Stone',2,.18)
 if variant%2==0:ico((-.55,.15,1.18),(1.12,.91,.4),'StoneLight',2,.08)
 export('SM_Boulder_'+str(variant))
for variant in range(2):
 for k in range(5):
  a=k*2.4;r=.2+.35*random.random();ico((cos(a)*r,sin(a)*r,.12),(.22+random.random()*.2,.18+random.random()*.2,.12+random.random()*.16),'StoneLight',2,.1)
 export('SM_Pebbles_'+str(variant))

# Ribbon blades have thickness and curled tips; ferns have paired leaflets.
def leaf(start, direction, length, width, mat):
 d=Vector(direction).normalized();s=Vector(start);side=Vector((-d.y,d.x,0)).normalized()
 if side.length<.1:side=Vector((1,0,0))
 v=[]
 for t,w in [(0,0),(.22,.8),(.55,1),(.82,.64),(1,0)]:
  p=s+d*length*t+Vector((0,0,sin(t*pi)*length*.17));v.extend([p-side*width*w,p+Vector((0,0,.018))*sin(t*pi),p+side*width*w])
 f=[]
 for k in range(4):
  a=k*3;b=a+3;f.extend([(a,b,b+1,a+1),(a+1,b+1,b+2,a+2)])
 me=bpy.data.meshes.new('Leaf');me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new('Leaf',me);bpy.context.collection.objects.link(o);add(o,mat)
for variant in range(3):
 for k in range(12):
  a=k*2.399; r=random.uniform(.04,.3)
  leaf((r*cos(a),r*sin(a),0),(cos(a)*.6,sin(a)*.6,1),random.uniform(.4,.85),.045,'Grass' if k%3 else 'LeafLight')
 export('SM_Grass_'+str(variant),False)
for k in range(8):
 a=k*pi/4;d=Vector((cos(a),sin(a),.4));
 tube([(0,0,0),tuple(d*.4+Vector((0,0,.25))),tuple(d*.95)], [.018,.014,.003],'Grass',5)
 for j in range(1,7):
  p=d*(j/7)*.95+Vector((0,0,.18*sin(j*pi/7)));length=.25*(1-j/9)
  for sign in [-1,1]:leaf(p,(cos(a+sign*.8),sin(a+sign*.8),.16),length,.045,'LeafSage')
export('SM_Fern',False)
for k in range(8):
 a=k*2.4; p=Vector((cos(a)*.3,sin(a)*.3,0));h=random.uniform(1.1,1.7)
 tube([tuple(p),tuple(p+Vector((.04,.03,h*.65))),tuple(p+Vector((.14,.07,h)))],[.025,.02,.012],'Reed',6)
 if k%2==0:ico(tuple(p+Vector((.12,.06,h*.91))),(.065,.065,.22),'RushTip',2,.02)
 leaf(tuple(p),(cos(a)*.45,sin(a)*.45,1),h*.75,.045,'Reed')
export('SM_Reeds',False)
for k in range(5):
 a=k*2.4;p=(cos(a)*.2,sin(a)*.2,.28+random.random()*.15)
 tube([(p[0],p[1],0),p],[.012,.008],'Grass',5)
 for j in range(5):
  b=j*2*pi/5;ico((p[0]+cos(b)*.05,p[1]+sin(b)*.05,p[2]),(.055,.035,.022),'Petal',1,.01)
export('SM_Wildflowers',False)
for k in range(5):ico((cos(k*2.4)*.6,sin(k*2.4)*.6,.5+random.random()*.3),(.8,.7,.7),'LeafMoss' if k%2 else 'LeafSage',2,.06)
export('SM_Shrub',False)

# Hollow fallen log, old stump, restrained wooden trail details.
tube([(-2,0,.4),(-.9,.07,.38),(.6,-.03,.4),(2,0,.35)],[.42,.46,.43,.36],'Bark',14)
tube([(-2.01,0,.4),(-2.03,0,.4)],[.33,.33],'EndGrain',14)
tube([(.2,0,.65),(.5,.12,1.1),(.72,.15,1.18)],[.16,.12,.09],'BarkLight',8)
export('SM_FallenLog')
tube([(0,0,0),(.04,0,.6),(0,0,.85)],[.55,.46,.4],'Bark',12)
tube([(0,0,.855),(0,0,.87)],[.34,.34],'EndGrain',16)
export('SM_Stump')
for x in [-.9,.9]:
 for y in [-.3,.3]:box((x,y,.33),(.15,.15,.66),'BarkLight',.035)
for y in [-.29,0,.29]:box((0,y,.72),(2.35,.26,.12),'Wood',.04)
export('SM_Bench')
for y in [-.85,.85]:
 for x in [-1.25,1.25]:tube([(x,y,-.5),(x,y,.2)],[.1,.09],'Bark',8)
for i in range(11):box((-1.3+i*.26,0,.1),(.24,2.05,.16),'Wood' if i%3 else 'EndGrain',.025)
export('SM_Dock')

def coast(x):return -27+3.0*sin(x*.085)+1.8*sin(x*.19+.8)
def lake_r(x,y):
 dx=x+18;dy=y-14;angle=math.atan2(dy/10.3,dx/14.2)
 return sqrt((dx/14.2)**2+(dy/10.3)**2)/(1+.065*sin(3*angle)+.04*cos(5*angle))
def height(x,y):
 c=coast(x);t=max(0,min(1,(y-c)/12));t=t*t*(3-2*t)
 land=2.9+3.9*exp(-((x-25)/21)**2-((y-24)/26)**2)+2.0*exp(-((x+36)/18)**2-((y-38)/19)**2)
 land+=.32*sin(x*.16)*sin(y*.19)+.2*cos(x*.31+y*.12)
 z=(-1.8+(y-c)*.055)*(1-t)+land*t
 lr=lake_r(x,y)
 if lr<1.32:
  blend=max(0,min(1,(lr-.82)/.50));blend=blend*blend*(3-2*blend)
  z=.65*(1-blend)+z*blend
 return z
def trail_x(y):return 6+6*sin((y+22)*.073)+2*sin(y*.17)
def colors(x,y,z):
 d=y-coast(x); t=max(0,min(1,(d-6)/6));t=t*t*(3-2*t)
 sand=Vector(PALETTE['Sand']);grass=Vector(PALETTE['Terrain']);c=sand.lerp(grass,t)
 lr=lake_r(x,y)
 if .97<lr<1.2:c=c.lerp(Vector((.44,.43,.28)),max(0,1-abs(lr-1.07)/.13)*.6)
 dist=abs(x-trail_x(y));path=max(0,1-dist/1.9)*max(0,min(1,(y+18)/5))*max(0,min(1,(43-y)/5))
 c=c.lerp(Vector(PALETTE['Path']),path*.9)
 variation=.97+.05*sin(x*.3+y*.2)+.025*cos(y*.8-x*.5)
 return (*(c*variation),1)

N=160;vs=[];fs=[]
for j in range(N+1):
 y=-50+100*j/N
 for i in range(N+1):x=-50+100*i/N;vs.append((x,y,height(x,y)))
for j in range(N):
 for i in range(N):
  a=j*(N+1)+i;fs.extend([(a,a+1,a+N+2),(a,a+N+2,a+N+1)])
me=bpy.data.meshes.new('ContinuousTerrain');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('Terrain',me);bpy.context.collection.objects.link(o);add(o,'Terrain')
attr=me.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
for poly in me.polygons:
 for li in poly.loop_indices:
  p=me.vertices[me.loops[li].vertex_index].co;attr.data[li].color=colors(*p)
export('SM_Terrain')

def surface(name, verts, faces, mat):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);add(o,mat);export(name,False)
# Both water bodies are contained inside the 100 m footprint.
surface('SM_Sea',[(-50,-50,0),(50,-50,0),(50,-15,0),(-50,-15,0)],[(0,1,2,3)],'WaterSea')
vs=[(-18,14,2.0)]
for k in range(128):
 a=k*2*pi/128;rr=1.22*(1+.065*sin(3*a)+.04*cos(5*a))
 vs.append((-18+14.2*rr*cos(a),14+10.3*rr*sin(a),2.0))
surface('SM_Lake',vs,[(0,k+1,(k+1)%128+1) for k in range(128)],'WaterLake')

# Narrow, irregular shore lines are authored mesh ribbons rather than decals.
for band in range(3):
 vs=[];fs=[]
 for i in range(161):
  x=-49.7+99.4*i/160;y=coast(x)-.3-band*3.5+.20*sin(x*.6+band)
  width=.08+.07*(.5+.5*sin(x*.31+band))
  vs.extend([(x,y, .025+band*.005),(x,y+width,.025+band*.005)])
 for i in range(160):fs.append((i*2,i*2+2,i*2+3,i*2+1))
 surface('SM_Surf_'+str(band),vs,fs,'Foam')

# Distribution deliberately leaves a winding traversable glade and vistas over water.
instances=manifest['instances']
def put(mesh,x,y,scale=1,rz=0,z=None,role='prop'):
 instances.append({'mesh':mesh,'location':[x,y,height(x,y) if z is None else z],
 'scale':[scale]*3 if isinstance(scale,(int,float)) else scale,'yaw':rz,'role':role})
occupied=[]
for j in range(14):
 for i in range(19):
  x=-46+i*5.05+random.uniform(-1.6,1.6);y=-9+j*4.25+random.uniform(-1.5,1.5)
  if abs(x)>46 or y>46 or lake_r(x,y)<1.30 or abs(x-trail_x(y))<3.5:continue
  # Opening from the beach towards the central path.
  if y<1 and -4<x<21:continue
  if random.random()<.12:continue
  conifer=(x>20 or y>34) and random.random()<.7
  mesh='SM_Pine_'+str(random.randrange(2)) if conifer else 'SM_Broadleaf_'+str(random.randrange(3))
  scale=random.uniform(.78,1.18);put(mesh,x,y,scale,random.uniform(0,360),role='tree');occupied.append((x,y))
# Art-directed rock outcrops frame beach and overlook, not a uniform scatter.
for cx,cy in [(-41,-19),(36,-16),(35,15),(-36,34),(0,33),(44,39),(-31,0)]:
 for k in range(6):
  x=cx+random.uniform(-3.3,3.3);y=cy+random.uniform(-2.5,2.5)
  put('SM_Boulder_'+str(k%4),x,y,random.uniform(.85,1.8),random.uniform(0,360),role='rock')
for k in range(26):
 a=k*2*pi/26;r=1.12
 x=-18+14.2*r*cos(a);y=14+10.3*r*sin(a)
 if k%3==0:put('SM_Boulder_'+str(k%4),x,y,random.uniform(.35,.65),random.uniform(0,360),role='lake_rock')
 put('SM_Reeds',x,y,random.uniform(.8,1.1),random.uniform(0,360),role='lake_reeds')
for k in range(700):
 x=random.uniform(-47,47);y=random.uniform(-18,47)
 if y<coast(x)+10 or lake_r(x,y)<1.17 or abs(x-trail_x(y))<2.2:continue
 typ=random.random()
 mesh='SM_Grass_'+str(k%3) if typ<.57 else 'SM_Fern' if typ<.78 else 'SM_Shrub' if typ<.93 else 'SM_Wildflowers'
 put(mesh,x,y,random.uniform(.65,1.3),random.uniform(0,360),role='understory')
for k in range(65):
 x=random.uniform(-46,46);y=coast(x)+random.uniform(4.8,10)
 if k%4==0:put('SM_Grass_'+str(k%3),x,y,random.uniform(.65,1),random.uniform(0,360),role='beach_grass')
 else:put('SM_Pebbles_'+str(k%2),x,y,random.uniform(.5,1.2),random.uniform(0,360),role='beach_stones')
for x,y,rz in [(-37,6,30),(29,31,-32),(-12,36,68)]:put('SM_FallenLog',x,y,1,rz)
for x,y in [(16,21),(-37,9),(26,34)]:put('SM_Stump',x,y,.9,0)
put('SM_Bench',2,12,1,90,role='rest_bench')
put('SM_Dock',-4.9,13,1,0,z=2.35,role='lake_dock')
for x,y,rz in [(-23,-20,12),(24,-20,-25)]:put('SM_FallenLog',x,y,.8,rz,role='driftwood')

manifest['regions']={'footprint_cm':[-5000,-5000,5000,5000], 'lake_center_m':[-18,14], 'lake_water_z_m':2.0,
 'sea_water_z_m':0,'beach_band':'south coast, y roughly -25 to -15 m',
 'player_m':[8,-9,height(8,-9)+1.1], 'overview_location_cm':[12500,-16000,13500], 'overview_target_cm':[0,0,150]}
manifest['terrain_samples']=[{'x_m':x,'y_m':y,'height_m':height(x,y)} for x,y in [(8,-9),(8,0),(12,15),(6,28),(-18,14),(30,-19),(-30,-19)]]
with open(ROOT+'/scene_manifest.json','w') as f:json.dump(manifest,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/QuietCove_Source.blend')
print('XHIGH_ART_COMPLETE',len(manifest['meshes']),len(instances))
