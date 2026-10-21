import bpy, math, random, json
from pathlib import Path
from mathutils import Vector
random.seed(3821)
OUT=Path('D:/github/AstraEffort/ForestDemo/Work/high')
FBX=OUT/'Source/FBX';FBX.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.01
palette={
 'Earth':(.26,.32,.18), 'Grass':(.36,.46,.26), 'Meadow':(.46,.53,.30),
 'Sand':(.72,.64,.45), 'Path':(.58,.50,.34),'Cliff':(.30,.32,.27),
 'Bark':(.25,.19,.13),'BarkLight':(.42,.32,.21),'Leaf':(.22,.37,.24),
 'LeafLight':(.35,.48,.29),'LeafDark':(.15,.28,.23),'Pine':(.18,.33,.28),
 'Rock':(.40,.44,.40),'RockLight':(.54,.55,.45),'Moss':(.34,.43,.24),
 'Wood':(.49,.36,.22),'WoodEnd':(.65,.51,.32),'Reed':(.53,.48,.27),
 'Flower':(.69,.62,.44),'WaterLake':(.23,.46,.44),'WaterSea':(.23,.40,.45),
 'Foam':(.62,.73,.65),'Metal':(.24,.30,.29)
}
mats={}
for n,c in palette.items():
 m=bpy.data.materials.new('M_'+n);m.diffuse_color=(*c,1);mats[n]=m
def material(obj,name):obj.data.materials.append(mats[name]);return obj
def ellipsoid(name,loc,scale,mat,seed=1):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=1,location=loc)
 o=bpy.context.object;o.name=name
 rng=random.Random(seed)
 for v in o.data.vertices:
  p=v.co; wobble=1+.065*math.sin(p.x*6+seed)*math.cos(p.z*4+seed)
  p.x*=scale[0]*wobble;p.y*=scale[1]*wobble;p.z*=scale[2]*wobble
 for p in o.data.polygons:p.use_smooth=True
 return material(o,mat)
def branch(a,b,r1,r2,mat='Bark',verts=9):
 d=Vector(b)-Vector(a);mid=(Vector(a)+Vector(b))*.5
 bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r1,radius2=r2,depth=d.length,location=mid)
 o=bpy.context.object;o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
 bevel=o.modifiers.new('Soft edges','BEVEL');bevel.width=min(r1*.2,7);bevel.segments=2
 o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return material(o,mat)
def box(loc,scale,mat,bevel=8):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 m=o.modifiers.new('Rounded corners','BEVEL');m.width=bevel;m.segments=3
 o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return material(o,mat)
def mesh(name,vs,fs,mat):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);material(o,mat);return o
def export(name,objects):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:
  o.select_set(True);bpy.context.view_layer.objects.active=o
  for mod in list(o.modifiers):
   try:bpy.ops.object.modifier_apply(modifier=mod.name)
   except:pass
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
 bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 bpy.ops.export_scene.fbx(filepath=str(FBX/(name+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',axis_forward='-Y',axis_up='Z',bake_anim=False,mesh_smooth_type='FACE',use_mesh_modifiers=True)
 o.hide_render=True;o.hide_set(True)
 return o
def group_begin():return set(bpy.data.objects)
def group_end(name,old):return export(name,list(set(bpy.data.objects)-old))
def coast(x):return -2900+270*math.sin(x/1350)+120*math.sin(x/540)
def pondr(x,y):return math.sqrt(((x+1700)/1370)**2+((y-700)/1030)**2)
trail=[(150,-2800),(500,-1700),(850,-600),(550,400),(250,1700),(-350,2600),(-1000,3800)]
def pathdist(x,y):
 ds=[]
 for a,b in zip(trail[:-1],trail[1:]):
  vx=b[0]-a[0];vy=b[1]-a[1];t=max(0,min(1,((x-a[0])*vx+(y-a[1])*vy)/(vx*vx+vy*vy)))
  ds.append(math.hypot(x-a[0]-t*vx,y-a[1]-t*vy))
 return min(ds)
def height(x,y):
 c=coast(x);shore=max(0,min(1,(y-c)/850))
 h=100+220*shore+200*math.exp(-((x-2200)**2+(y-2300)**2)/5500000)+100*math.exp(-((x+3100)**2+(y-3300)**2)/3500000)
 h+=shore*(32*math.sin(x/900)*math.cos(y/1100)+20*math.sin(y/480+x/700))
 if y<c:h=100+(y-c)*.16
 r=pondr(x,y)
 if r<1.3:
  t=max(0,min(1,(r-.76)/.54));t=t*t*(3-2*t);h=45+(h-45)*t
 return h
# 100 m square continuous terrain, with authored sand / path / upland regions.
vs=[];fs=[];inds=[];N=121
for j in range(N):
 y=-5000+j*10000/(N-1)
 for i in range(N):
  x=-5000+i*10000/(N-1);vs.append((x,y,height(x,y)))
for j in range(N-1):
 for i in range(N-1):
  a=j*N+i;fs.append((a,a+1,a+1+N,a+N));x=-5000+(i+.5)*10000/(N-1);y=-5000+(j+.5)*10000/(N-1)
  r=pondr(x,y)
  if y<coast(x)+620 or .84<r<1.17:idx=2
  elif pathdist(x,y)<145:idx=3
  elif math.sin(x/600)+math.cos(y/800)>1:idx=1
  else:idx=0
  inds.append(idx)
o=mesh('Terrain',vs,fs,'Grass')
for n in ['Meadow','Sand','Path']:o.data.materials.append(mats[n])
for p,idx in zip(o.data.polygons,inds):p.material_index=idx;p.use_smooth=True
export('SM_Terrain',[o])
# Terraced soil rim closes the visible block edges.
vs=[];fs=[]
per=[(-5000+i*100, -5000) for i in range(100)]+[(5000,-5000+i*100) for i in range(100)]+[(5000-i*100,5000) for i in range(100)]+[(-5000,5000-i*100) for i in range(100)]
for x,y in per:vs.extend([(x,y,height(x,y)),(x,y,-550)])
for i in range(len(per)):a=2*i;b=2*((i+1)%len(per));fs.append((a,b,b+1,a+1))
export('SM_EarthRim',[mesh('Rim',vs,fs,'Cliff')])
# Lake contour deliberately irregular, with a shallow inlet facing the trail.
def pondpoint(a,r=1):
 rad=r*(1+.055*math.sin(3*a)+.025*math.cos(5*a));return (-1700+1310*rad*math.cos(a),700+980*rad*math.sin(a),162)
vs=[(-1700,700,162)]+[pondpoint(i*2*math.pi/96,.985) for i in range(96)]
export('SM_Lake',[mesh('Lake',vs,[(0,i+1,(i+1)%96+1) for i in range(96)],'WaterLake')])
vs=[];fs=[]
for i in range(101):
 x=-5000+i*100;vs.extend([(x,-5000,78),(x,coast(x)-100,78)])
for i in range(100):a=2*i;fs.append((a,a+2,a+3,a+1))
export('SM_Sea',[mesh('Sea',vs,fs,'WaterSea')])
# Broadleaf silhouettes are branching trunks with asymmetrical overlapping crown masses.
for k in range(3):
 old=group_begin();h=[830,1000,710][k]
 branch((0,0,0),(22,-8,h*.65),42,17)
 for i in range(5):
  a=i*2.4+k;dx=math.cos(a)*160;dy=math.sin(a)*155;z=h*(.48+.07*(i%3))
  branch((12,0,h*.35),(dx,dy,z+80),23,8)
  ellipsoid('Crown',(dx,dy,z+150),(230,210,210),'LeafLight' if i%3==0 else 'Leaf',i+5*k)
 ellipsoid('CrownTop',(20,0,h*.83),(230,210,h*.24),'Leaf',k+30)
 for i in range(5):
  a=i*1.256;branch((math.cos(a)*70,math.sin(a)*70,5),(0,0,135),16,23)
 group_end('SM_Broadleaf_'+str(k),old)
for k in range(2):
 old=group_begin();h=1050+k*190;branch((0,0,0),(0,0,h*.88),36,7)
 for i in range(5):
  z=240+i*h*.13;r=300-i*48
  # Rounded radial tier, soft lobed profile instead of a perfect cone.
  vv=[];ff=[];rings=[(0,0.84),(30,1),(100,.83),(230,.26),(265,.05)]
  for dz,rs in rings:
   for j in range(16):a=j*math.tau/16;rr=r*rs*(1+.07*math.sin(5*a+i));vv.append((rr*math.cos(a),rr*math.sin(a),z+dz))
  for a in range(4):
   for j in range(16):ff.append((a*16+j,a*16+(j+1)%16,(a+1)*16+(j+1)%16,(a+1)*16+j))
  ob=mesh('FirTier',vv,ff,'Pine' if i%2 else 'LeafDark')
  for p in ob.data.polygons:p.use_smooth=True
 group_end('SM_Fir_'+str(k),old)
for k in range(4):
 old=group_begin();ellipsoid('Boulder',(0,0,65),(140+25*k,100+15*k,110+15*k),'Rock' if k%2==0 else 'RockLight',22+k)
 ellipsoid('MossCap',(-25,5,140+16*k),(95+20*k,82+14*k,30),'Moss',44+k)
 group_end('SM_Rock_'+str(k),old)
for k in range(2):
 old=group_begin()
 for j in range(9):
  a=j*2.4;r=20*(j%3);base=Vector((math.cos(a)*r,math.sin(a)*r,0));length=55+random.random()*65
  side=Vector((-math.sin(a)*8,math.cos(a)*8,0));tip=base+Vector((math.cos(a)*length*.5,math.sin(a)*length*.5,length))
  mid=base*.3+tip*.7+Vector((0,0,10));mesh('Blade',[base-side,base+side,mid+side*.5,tip,mid-side*.5],[(0,1,2,3,4)],'Meadow' if k else 'LeafLight')
 group_end('SM_Grass_'+str(k),old)
old=group_begin()
for j in range(7):
 a=j*math.tau/7;end=Vector((math.cos(a)*105,math.sin(a)*105,45));branch((0,0,0),end,2,1,'LeafLight',5)
 for t in [.25,.4,.55,.7,.85]:
  p=end*t+Vector((0,0,35*math.sin(t*math.pi)));side=Vector((-math.sin(a),math.cos(a),.15))*(1-t)*42
  for sign in [-1,1]:mesh('FernLeaf',[p,p+side*sign+end*.07,p+end*.16],[(0,1,2)],'LeafLight')
group_end('SM_Fern',old)
old=group_begin()
for i in range(7):
 x=random.uniform(-35,35);y=random.uniform(-35,35);h=random.uniform(130,220)
 branch((x,y,0),(x+12,y,h),3,2,'Reed',6);ellipsoid('Seed',(x+12,y,h),(8,8,23),'Bark',i)
 mesh('ReedLeaf',[(x,y,10),(x+35,y+15,h*.5),(x+14,y,h*.8),(x-4,y,h*.4)],[(0,1,2,3)],'Meadow')
group_end('SM_Reeds',old)
old=group_begin();branch((-170,0,55),(170,0,55),62,51,'BarkLight',12)
branch((-172,0,55),(-175,0,55),48,48,'WoodEnd',12);branch((172,0,55),(175,0,55),42,42,'WoodEnd',12)
branch((20,0,60),(45,100,130),18,8,'Bark');ellipsoid('Moss',(-30,0,100),(110,43,18),'Moss',88)
group_end('SM_FallenLog',old)
old=group_begin()
for i in range(13):
 x=-360+i*60;z=40+45*math.sin((i/12)*math.pi);box((x,0,z),(56,240,22),'Wood',5)
for y in [-130,130]:
 for x in [-330,0,330]:box((x,y,105),(18,18,210),'BarkLight',4)
 for i in range(6):x=-360+i*120;branch((x,y,160+35*math.sin(i/6*math.pi)),(x+120,y,160+35*math.sin((i+1)/6*math.pi)),8,8,'Wood',8)
group_end('SM_Bridge',old)
old=group_begin();box((0,0,85),(16,20,170),'BarkLight',4);box((12,0,155),(100,24,39),'Wood',9)
group_end('SM_TrailPost',old)
old=group_begin()
for j in range(5):
 a=j*2.4;x=math.cos(a)*25;y=math.sin(a)*25;h=35+j*7;branch((x,y,0),(x,y,h),2,1,'LeafLight',5)
 ellipsoid('Bloom',(x,y,h),(9,9,6),'Flower',j)
group_end('SM_Wildflower',old)
# Narrow water ripple ribbons, placed just above the opaque water surfaces.
old=group_begin()
for rad,a0,span in [(160,0,1.7),(240,.2,1.5),(320,.35,1.3)]:
 vv=[];ff=[]
 for i in range(25):
  a=a0+span*i/24
  for r in [rad,rad+4]:vv.append((r*math.cos(a),r*.4*math.sin(a),0))
 for i in range(24):a=2*i;ff.append((a,a+2,a+3,a+1))
 mesh('Ripple',vv,ff,'Foam')
group_end('SM_Ripple',old)
# Deterministic composition manifest in centimetres.
actors=[]
def put(mesh,x,y,z=None,scale=1,yaw=0,label=None):
 actors.append(dict(mesh=mesh,location=[x,y,height(x,y) if z is None else z],scale=[scale]*3 if isinstance(scale,(float,int)) else scale,yaw=yaw,label=label or mesh))
for n in ['Terrain','EarthRim','Lake','Sea']:put('SM_'+n,0,0,0,label=n)
trees=[]
for j in range(13):
 for i in range(16):
  x=-4600+i*595+random.uniform(-170,170);y=-1700+j*515+random.uniform(-170,170)
  if y>4600 or x>4600 or pondr(x,y)<1.45 or pathdist(x,y)<360:continue
  if (x-1300)**2+(y+850)**2<700**2:continue
  if random.random()<.17:continue
  trees.append((x,y));typ=('SM_Fir_'+str(random.randrange(2))) if y>2100 and random.random()<.6 else ('SM_Broadleaf_'+str(random.randrange(3)))
  put(typ,x,y,scale=random.uniform(.68,1.2),yaw=random.uniform(0,360),label='Forest tree')
for i in range(70):
 if i<25:
  a=random.uniform(0,math.tau);x=-1700+1550*math.cos(a);y=700+1170*math.sin(a)
 else:x=random.uniform(-4600,4600);y=random.uniform(-2900,4550)
 if pondr(x,y)<1.12 or pathdist(x,y)<210:continue
 put('SM_Rock_'+str(i%4),x,y,scale=random.uniform(.45,1.2),yaw=random.uniform(0,360),label='Moss boulder')
for i in range(560):
 x=random.uniform(-4700,4700);y=random.uniform(-2300,4700)
 if pondr(x,y)<1.27 or pathdist(x,y)<190 or y<coast(x)+600:continue
 typ='SM_Fern' if i%5==0 else 'SM_Wildflower' if i%11==0 else 'SM_Grass_'+str(i%2)
 put(typ,x,y,scale=random.uniform(.65,1.4),yaw=random.uniform(0,360),label='Understory')
for i in range(44):
 a=random.uniform(0,math.tau);x=-1700+1370*math.cos(a);y=700+1030*math.sin(a)
 if x>-500 and y<900:continue
 put('SM_Reeds',x,y,scale=random.uniform(.65,1),yaw=random.uniform(0,360),label='Lakeside reeds')
for x,y,yaw in [(-3300,-1100,25),(2500,1100,125),(-2700,2700,65),(3200,-1400,-25)]:put('SM_FallenLog',x,y,yaw=yaw)
put('SM_Bridge',-480,650,180,yaw=90,label='Pond inlet footbridge')
for x,y in [(440,-2200),(1070,-650),(450,1900)]:put('SM_TrailPost',x,y,yaw=15,label='Trail marker')
for x,y,z,sc in [(-2000,700,165,1),(-1500,200,165,.7),(2100,-4100,81,2),(0,-3800,81,1.3),(-2700,-4350,81,1.4)]:put('SM_Ripple',x,y,z,scale=sc)
# Coastal stone outcrops and small pebble clusters give the beach a distinct character.
for x,y,s in [(3500,-2900,1.6),(3900,-3100,1.1),(3200,-3150,.8),(-4000,-3200,1.3),(-3700,-3400,.6)]:put('SM_Rock_1',x,y,scale=s,yaw=random.random()*360)
for i in range(35):
 x=random.uniform(-4400,4300);y=coast(x)+random.uniform(100,500)
 put('SM_Rock_2',x,y,scale=random.uniform(.07,.19),yaw=random.random()*360,label='Beach pebble')
manifest={'palette':palette,'actors':actors,'footprint_cm':[10000,10000],'start':[650,-1900,height(650,-1900)+110],'overview':[12500,-15300,15100],'target':[0,0,200]}
(OUT/'scene.json').write_text(json.dumps(manifest,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Source/QuietwaterGrove.blend'))
print('HIGH_ART_COMPLETE',len(actors),len(list(FBX.glob('*.fbx'))))
