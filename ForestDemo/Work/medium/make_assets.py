import bpy, math, random, json, os, bmesh
from mathutils import Vector
random.seed(42)
ROOT='D:/github/AstraEffort/ForestDemo/Work/medium'
OUT=ROOT+'/Source'; os.makedirs(OUT,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
colors={'Grass':(.28,.39,.24,1),'Moss':(.35,.44,.28,1),'Sand':(.65,.57,.40,1),'Path':(.49,.43,.31,1),'Earth':(.24,.25,.18,1),'Bark':(.27,.22,.17,1),'Leaf':(.19,.32,.23,1),'LeafLight':(.32,.43,.27,1),'LeafBlue':(.22,.36,.33,1),'Rock':(.39,.43,.40,1),'RockLight':(.50,.52,.45,1),'Water':(.19,.43,.45,1),'Foam':(.61,.70,.61,1),'Wood':(.43,.33,.21,1),'Flower':(.72,.67,.42,1)}
mats={}
for n,c in colors.items():
 m=bpy.data.materials.new(n); m.diffuse_color=c; mats[n]=m
def mat(o,n): o.data.materials.append(mats[n]); return o
def smooth(o):
 for p in o.data.polygons:p.use_smooth=True
 return o
def uv(name,loc,scale,material,seg=14,rings=8):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;mat(o,material);smooth(o);return o
def tube(name,a,b,r1,r2,material,vertices=10):
 d=Vector(b)-Vector(a); bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=r1,radius2=r2,depth=d.length,location=(Vector(a)+Vector(b))/2);o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();mat(o,material);smooth(o);return o
def export(name):
 obs=list(bpy.context.scene.objects); bpy.ops.object.select_all(action='SELECT'); bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
 bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 if name in ['Ground','Lake','Sea']:
  for v in o.data.vertices:v.co.y=-v.co.y
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 bpy.ops.export_scene.fbx(filepath=OUT+'/'+name+'.fbx',use_selection=True,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',bake_anim=False)
 bpy.ops.object.delete(use_global=False)
def height(x,y):
 h=.8+.7*math.sin(x*.073)*math.sin(y*.09)+1.9*math.exp(-((x-27)**2+(y-31)**2)/500)+1.3*math.exp(-((x+32)**2+(y-33)**2)/400)
 coast=-32+2*math.sin(x*.07)
 if y<coast+8:h=min(h,(y-coast)*.13)
 r=((x+15)/13)**2+((y-13)/10)**2
 h-=2.4*math.exp(-r*1.8)
 return h
def terrain():
 verts=[]; faces=[];N=400
 for j in range(N+1):
  y=-50+j*100/N
  for i in range(N+1):
   x=-50+i*100/N;verts.append((x,y,height(x,y)))
 for j in range(N):
  for i in range(N):
   a=j*(N+1)+i;faces.append((a,a+1,a+N+2,a+N+1))
 me=bpy.data.meshes.new('Ground');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('Ground',me);bpy.context.collection.objects.link(o)
 for n in ['Grass','Moss','Sand','Path']:me.materials.append(mats[n])
 for p in me.polygons:
  x,y,z=p.center; r=((x+15)/13)**2+((y-13)/10)**2
  pathx=11+6*math.sin(y*.06)
  p.material_index=2 if y<-25+2*math.sin(x*.07) or .73<r<1.3 else (3 if abs(x-pathx)<2.1 else (1 if math.sin(x*.19)+math.sin(y*.17)>1.3 else 0));p.use_smooth=True
 attr=me.color_attributes.new(name='TerrainColor',type='FLOAT_COLOR',domain='CORNER')
 def blend(a,b,t):return tuple(a[k]*(1-t)+b[k]*t for k in range(4))
 def sat(x):return max(0,min(1,x))
 for loop in me.loops:
  x,y,z=me.vertices[loop.vertex_index].co;r=math.sqrt(((x+15)/13)**2+((y-13)/10)**2)
  c=blend(colors['Grass'],colors['Moss'],sat((math.sin(x*.19)+math.sin(y*.17)-.5)*.5))
  sand=max(sat((-24.5+2*math.sin(x*.07)-y)/1.2),sat((1.18-r)*9)*sat((r-.65)*9))
  c=blend(c,colors['Sand'],sand);path=sat((2.5-abs(x-(11+6*math.sin(y*.06))))/.9)
  c=blend(c,colors['Path'],path*(1-sand));attr.data[loop.index].color=c
 export('Ground')
terrain()
for k in range(3):
 tube('trunk',(0,0,0),(.12,-.08,3.5),.40,.20,'Bark')
 for a in range(5):
  angle=a*2.4+k*.6;end=(math.cos(angle)*1.3,math.sin(angle)*1.3,3.2+a*.33)
  tube('branch',(0,0,1.8+a*.25),end,.16,.07,'Bark')
  uv('crown',(end[0]*.75,end[1]*.75,end[2]+.8),(1.65,1.5,1.7),['Leaf','LeafLight','LeafBlue'][k])
 uv('top',(0,0,5),(1.4,1.4,1.7),['Leaf','LeafLight','LeafBlue'][k]);export('Tree'+str(k))
for k in range(3):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1);o=bpy.context.object;o.name='Stone'
 for v in o.data.vertices:
  v.co*=1+random.uniform(-.12,.12);v.co.z=max(v.co.z,-.45)
 o.scale=(1.4,1.1,.95);mat(o,'Rock' if k<2 else 'RockLight');smooth(o)
 mod=o.modifiers.new('soft edges','SUBSURF');mod.levels=1;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name);export('Rock'+str(k))
for k in range(2):
 for i in range(5):
  a=i*2.4;uv('shrub',(math.cos(a)*.4,math.sin(a)*.4,.45+random.random()*.25),(.65,.58,.65),['LeafLight','LeafBlue'][k],10,6)
 export('Shrub'+str(k))
for k in range(2):
 for i in range(7):
  a=i*2.4;x=math.cos(a)*.18;y=math.sin(a)*.18;h=random.uniform(.3,.65)
  tube('blade',(x,y,0),(x*1.8,y*1.8,h),.045,.008,'Moss',5)
  if k: uv('seed',(x*1.8,y*1.8,h),(.065,.065,.10),'Flower',8,4)
 export('Tuft'+str(k))
for i in range(5):
 a=i*2.4;tube('reed',(math.cos(a)*.25,math.sin(a)*.25,0),(math.cos(a)*.35,math.sin(a)*.35,1+i*.08),.025,.018,'LeafLight',6)
 tube('reed head',(math.cos(a)*.35,math.sin(a)*.35,.9+i*.08),(math.cos(a)*.35,math.sin(a)*.35,1.2+i*.08),.05,.05,'Bark',8)
export('Reeds')
tube('fallen trunk',(-1.8,0,.35),(1.8,0,.35),.32,.27,'Bark');tube('cut end',(1.8,0,.35),(1.82,0,.35),.24,.24,'Wood');tube('twig',(.4,0,.35),(.7,.65,.7),.12,.05,'Bark');export('Log')
# flat water meshes use an ellipse and coast-following strip
def mesh(name,v,f,material):
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);mat(ob,material);export(name)
v=[(-15,13,-.12)]+[(-15+11.8*math.cos(i*math.tau/96),13+8.6*math.sin(i*math.tau/96),-.12) for i in range(96)]
mesh('Lake',v,[(0,i+1,(i+1)%96+1) for i in range(96)],'Water')
v=[]
for i in range(101):
 x=-50+i;v.extend([(x,-50,-.18),(x,-33.5+2*math.sin(x*.07),-.18)])
mesh('Sea',v,[(i*2,i*2+2,i*2+3,i*2+1) for i in range(100)],'Water')
layout=[]
def add(n,x,y,s=1,rot=0):layout.append(dict(mesh=n,x=x*100,y=y*100,z=height(x,y)*100,scale=s,rot=rot))
for i in range(170):
 x=random.uniform(-47,47);y=random.uniform(-21,47);r=((x+15)/16)**2+((y-13)/13)**2
 if r<1.5 or abs(x-(11+6*math.sin(y*.06)))<5 or (x>0 and x<27 and -13<y<18):continue
 add('Tree'+str(random.randrange(3)),x,y,random.uniform(.8,1.4),random.uniform(0,360))
for i in range(95):
 x=random.uniform(-47,47);y=random.uniform(-29,46);r=((x+15)/15)**2+((y-13)/12)**2
 if r<1.3 or abs(x-(11+6*math.sin(y*.06)))<3:continue
 add('Shrub'+str(i%2),x,y,random.uniform(.7,1.3),random.uniform(0,360))
for i in range(65):
 x=random.uniform(-46,46);y=random.uniform(-30,46)
 if ((x+15)/14)**2+((y-13)/11)**2<1.2:continue
 add('Rock'+str(i%3),x,y,random.uniform(.4,1.8),random.uniform(0,360))
for i in range(460):
 x=random.uniform(-47,47);y=random.uniform(-27,47)
 if ((x+15)/15)**2+((y-13)/12)**2<1.1 or abs(x-(11+6*math.sin(y*.06)))<2.5:continue
 add('Tuft'+str(i%2),x,y,random.uniform(.7,1.3),random.uniform(0,360))
for i in range(22):
 a=i*math.tau/22;x=-15+12.4*math.cos(a);y=13+9.3*math.sin(a);add('Reeds',x,y,.7,random.uniform(0,360))
for x,y,a in [(-27,-20,30),(30,22,70),(-33,21,130)]:add('Log',x,y,1.2,a)
json.dump({'colors':colors,'layout':layout},open(ROOT+'/layout.json','w'),indent=2)
# Editable procedural source is this script; individual FBX files are the mesh interchange masters.
