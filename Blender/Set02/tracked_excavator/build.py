"""Rounded tracked excavator, authored from the assigned Set02 concept sheet."""
import bpy, bmesh, math, json, time
from pathlib import Path
from mathutils import Vector, Matrix
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent;ROOT.mkdir(parents=True,exist_ok=True);(ROOT/'renders').mkdir(exist_ok=True)
START=datetime.now(timezone.utc).isoformat();T0=time.monotonic()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
ASSET=bpy.data.collections.new('ASSET');bpy.context.scene.collection.children.link(ASSET)
STUDIO=bpy.data.collections.new('STUDIO');bpy.context.scene.collection.children.link(STUDIO)
def material(name,color,rough=.4,metal=0,emission=0,transmission=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
 p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Transmission Weight'].default_value=transmission
 if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
 return m
IV=material('Excavator_Ivory_Enamel',(.66,.63,.54),.34,.12)
SG=material('Excavator_Sage_Enamel',(.20,.31,.25),.36,.22)
SL=material('Excavator_Sage_Edge',(.28,.39,.32),.34,.24)
SD=material('Excavator_Sage_Inset',(.14,.22,.18),.43,.20)
GM=material('Excavator_Graphite_Metal',(.062,.073,.076),.35,.55)
RB=material('Excavator_Rubber_Belt',(.026,.032,.033),.75)
TR=material('Excavator_Tread_Rubber',(.047,.054,.054),.69)
ST=material('Excavator_Brushed_Steel',(.29,.33,.34),.26,.78)
CH=material('Excavator_Chrome_Piston',(.53,.59,.62),.16,.92)
OR=material('Excavator_Operational_Orange',(.73,.28,.045),.37,.23)
GL=material('Excavator_Smoke_Glass',(.085,.135,.15),.14,.08,transmission=.7)
SE=material('Excavator_Seat_Cloth',(.045,.063,.066),.83)
EM=material('Excavator_Warm_Lamp',(.94,.80,.48),.21,.05,emission=2)
AM=material('Excavator_Amber_Lens',(.83,.29,.04),.25,.1,emission=.3)

def link(o,col=ASSET):
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);return o
def finish(o,name,mat,smooth=True,bevel=0):
 o.name=name;link(o)
 if mat:o.data.materials.append(mat)
 if o.type=='MESH':
  for p in o.data.polygons:p.use_smooth=smooth
  if bevel:
   b=o.modifiers.new('Manufactured rounded edges','BEVEL');b.width=bevel;b.segments=3
  if smooth:
   n=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');n.keep_sharp=True
 return o
def box(name,loc,dims,mat,bevel=.04,rotation=None):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if rotation is not None:o.rotation_euler=rotation
 return finish(o,name,mat,True,min(bevel,min(dims)*.4))
def mesh(name,verts,faces,mat,bevel=0):
 me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(verts,[],faces);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if bevel:
  lengths=[e.calc_length() for e in bm.edges if e.calc_length()>1e-8]
  bevel=min(bevel,min(lengths)*.35)
 bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);ASSET.objects.link(o)
 return finish(o,name,mat,True,bevel)
def cyl(name,loc,r,depth,mat,axis=(0,0,1),vertices=48,bevel=.015):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc)
 o=bpy.context.object;o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
 return finish(o,name,mat,True,min(bevel,depth*.35,r*.35))
def rod(name,a,b,r,mat):
 d=Vector(b)-Vector(a);return cyl(name,(Vector(a)+Vector(b))*.5,r,d.length,mat,d,24,min(.008,r*.2))
def sphere(name,loc,scale,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=28,ring_count=14,radius=1,location=loc);o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 return finish(o,name,mat)
def tube(name,points,r,mat,bezier=False,cyclic=False):
 cu=bpy.data.curves.new(name+'_Path','CURVE');cu.dimensions='3D';cu.resolution_u=10;cu.bevel_depth=r;cu.bevel_resolution=3;cu.use_fill_caps=True
 if bezier:
  s=cu.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
  for p,co in zip(s.bezier_points,points):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 else:
  s=cu.splines.new('POLY');s.points.add(len(points)-1)
  for p,co in zip(s.points,points):p.co=(*co,1)
 s.use_cyclic_u=cyclic
 o=bpy.data.objects.new(name,cu);ASSET.objects.link(o);o.data.materials.append(mat);return o
def rr(w,h,r,n=8):
 out=[]
 for cx,cy,a in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
  for j in range(n):
   t=math.radians(a+j*90/n);out.append((cx+r*math.cos(t),cy+r*math.sin(t)))
 return out
def frame(name,origin,u,v,w,h,r,border,depth,mat):
 o=Vector(origin);u=Vector(u);v=Vector(v);n=u.cross(v).normalized();outer=rr(w,h,r);inner=rr(w-2*border,h-2*border,max(.01,r-border));N=len(outer)
 vs=[tuple(o+u*x+v*y+n*d) for d in [-depth/2,depth/2] for loop in [outer,inner] for x,y in loop];fs=[]
 for i in range(N):
  j=(i+1)%N;fs.extend([(i,j,N+j,N+i),(2*N+i,3*N+i,3*N+j,2*N+j),(i,2*N+i,2*N+j,j),(N+i,N+j,3*N+j,3*N+i)])
 return mesh(name,vs,fs,mat,min(.012,depth*.35,border*.35))
def pane(name,origin,u,v,w,h,r,depth,mat):
 o=Vector(origin);u=Vector(u);v=Vector(v);n=u.cross(v).normalized();ps=rr(w,h,r);N=len(ps)
 vs=[tuple(o+u*x+v*y+n*d) for d in [-depth/2,depth/2] for x,y in ps];fs=[tuple(reversed(range(N))),tuple(range(N,2*N))]
 fs.extend([(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)])
 return mesh(name,vs,fs,mat,min(.005,depth*.3))
def plate_yz(name,x,profile,width,mat,bevel=.03):
 n=len(profile);v=[(xx,y,z) for xx in [x-width/2,x+width/2] for y,z in profile]
 f=[tuple(reversed(range(n))),tuple(range(n,2*n))];f.extend([(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
 return mesh(name,v,f,mat,min(bevel,width*.35))
def beam(name,a,b,width,depth,mat,bevel=.04):
 d=Vector(b)-Vector(a);o=box(name,(Vector(a)+Vector(b))/2,(width,depth,d.length),mat,bevel);o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return o
def bolt(name,loc,axis=(1,0,0),r=.021,depth=.014,mat=ST):return cyl(name,loc,r,depth,mat,axis,8,min(.003,depth*.2))

# Two real closed rubber track loops with individually articulated pads.
A=1.02;CZ=.48;R=.435
def track_sample(s):
 L=4*A+2*math.pi*R;s=s%L
 if s<2*A:return Vector((0,-A+s,CZ+R)),Vector((0,1,0))
 s-=2*A
 if s<math.pi*R:
  t=s/R;return Vector((0,A+R*math.sin(t),CZ+R*math.cos(t))),Vector((0,math.cos(t),-math.sin(t)))
 s-=math.pi*R
 if s<2*A:return Vector((0,A-s,CZ-R)),Vector((0,-1,0))
 t=(s-2*A)/R;return Vector((0,-A-R*math.sin(t),CZ-R*math.cos(t))),Vector((0,-math.cos(t),math.sin(t)))
def capsule_loop(rad):
 pts=[]
 for i in range(16):pts.append((-A+2*A*i/16,CZ+rad))
 for i in range(32):
  t=math.pi*i/32;pts.append((A+rad*math.sin(t),CZ+rad*math.cos(t)))
 for i in range(16):pts.append((A-2*A*i/16,CZ-rad))
 for i in range(32):
  t=math.pi*i/32;pts.append((-A-rad*math.sin(t),CZ-rad*math.cos(t)))
 return pts
track_names=[]
for side in [-1,1]:
 x=side*.91;N=96;vs=[];fs=[]
 for xx in [x-.285,x+.285]:
  for rad in [.350,.435]:vs.extend([(xx,y,z) for y,z in capsule_loop(rad)])
 for i in range(N):
  j=(i+1)%N
  fs.extend([(i,j,N+j,N+i),(2*N+i,3*N+i,3*N+j,2*N+j),(i,2*N+i,2*N+j,j),(N+i,N+j,3*N+j,3*N+i)])
 name='Left continuous track belt' if side<0 else 'Right continuous track belt'
 belt=mesh(name,vs,fs,RB);belt['primary_track']=True;track_names.append(belt.name)
 L=4*A+2*math.pi*R
 for k in range(44):
  p,t=track_sample(k*L/44);p.x=x;n=Vector((1,0,0)).cross(t);basis=Matrix((Vector((1,0,0)),t,n)).transposed();rot=basis.to_euler()
  box(f'Track {side} pad {k:02d}',p+n*.018,(.59,.142,.064),RB,.018,rot)
  for band in [-1,0,1]:
   q=p+n*.058+Vector((band*.19,0,0))
   box(f'Track {side} grouser {k:02d} {band}',q,(.171,.119,.039),TR,.014,rot)
 # end wheels and smaller rolling gear are visible within the belt.
 for wy in [-A,A]:
  cyl('Drive wheel rubber ring',(x,wy,CZ),.341,.45,RB,(1,0,0),64,.018)
  for out in [-1,1]:
   xx=x+out*.235
   cyl('End wheel rim',(xx,wy,CZ),.301,.045,ST,(1,0,0),64,.012)
   cyl('End wheel recessed disk',(xx+out*.029,wy,CZ),.263,.035,GM,(1,0,0),64,.012)
   cyl('End wheel hub',(xx+out*.052,wy,CZ),.135,.045,GM,(1,0,0),48,.012)
   cyl('End wheel orange cap',(xx+out*.08,wy,CZ),.079,.018,OR,(1,0,0),40,.006)
   for j in range(6):
    a=math.tau*j/6;bolt('End wheel fastener',(xx+out*.055,wy+.213*math.sin(a),CZ+.213*math.cos(a)),r=.016)
 for wy in [-.69,-.23,.23,.69]:
  cyl('Lower road roller',(x,wy,.29),.167,.44,GM,(1,0,0),40,.014)
  for out in [-1,1]:
   cyl('Road roller inset',(x+out*.232,wy,.29),.112,.025,ST,(1,0,0),32,.006)
   cyl('Road roller spindle',(x+out*.25,wy,.29),.045,.03,GM,(1,0,0),24,.006)
 for wy in [-.58,.58]:cyl('Upper return roller',(x,wy,.73),.10,.44,GM,(1,0,0),32,.008)
 box('Track bogie spine',(x,0,.56),(.48,1.80,.28),GM,.07)
 box('Outer bogie cover',(x+side*.278,0,.56),(.055,1.63,.29),GM,.02)
 for yy in [-.64,.64]:
  for zz in [.49,.64]:bolt('Bogie cover bolt',(x+side*.312,yy,zz),r=.025)
 box('Bogie service accent',(x+side*.313,.41,.56),(.02,.18,.11),OR,.007)
 fender_profile=[(-1.31,.98),(-1.08,1.075),(1.07,1.075),(1.31,.98),(1.28,.925),(1.04,1.01),(-1.05,1.01),(-1.28,.925)]
 plate_yz('Rounded track cover',x,fender_profile,.62,GM,.022)
 for yy in [-.70,.70]:box('Track cover stanchion',(x,yy,.94),(.25,.12,.14),GM,.03)

box('Central undercarriage frame',(0,0,.72),(1.47,2.28,.28),GM,.085)
for yy in [-.86,.86]:rod('Structural crossmember',(-.95,yy,.66),(.95,yy,.66),.083,GM)
cyl('Lower swing flange',(0,.02,.985),.70,.115,GM,vertices=80,bevel=.025)
cyl('Rotating slew bearing',(0,.02,1.075),.64,.145,ST,vertices=80,bevel=.021)
cyl('Upper swing flange',(0,.02,1.16),.70,.08,GM,vertices=80,bevel=.02)
for k in range(20):
 a=math.tau*k/20;cyl('Slew bearing bolt',(.665*math.cos(a),.02+.665*math.sin(a),1.181),.023,.03,ST,vertices=8,bevel=.003)
box('Rounded upper deck',(0,.1,1.29),(2.04,2.31,.22),SG,.10)
box('Rear counterweight',(0,1.02,1.71),(2.03,.79,.91),SG,.20)
box('Left engine fairing',(-.58,.39,1.61),(.86,1.48,.62),SG,.15)
box('Engine upper service lid',(-.58,.67,1.97),(.73,.85,.10),SL,.04)
frame('Rear cooling grille border',(0,1.423,1.78),(1,0,0),(0,0,1),1.34,.53,.10,.065,.045,SD)
pane('Rear grille recess',(0,1.450,1.78),(1,0,0),(0,0,1),1.20,.40,.055,.012,RB)
for z in [1.63,1.69,1.75,1.81,1.87,1.93]:box('Rear cooling louver',(0,1.468,z),(1.16,.024,.026),GM,.008)
for sx in [-.81,.81]:box('Rear amber service reflector',(sx,1.437,1.48),(.16,.035,.17),AM,.012)
frame('Side engine ventilation',(-1.027,.75,1.76),(0,1,0),(0,0,1),.60,.43,.065,.04,.025,SD)
pane('Side engine dark recess',(-1.044,.75,1.76),(0,1,0),(0,0,1),.52,.35,.035,.015,RB)
for z in [1.64,1.70,1.76,1.82,1.88]:box('Side engine grille louver',(-1.062,.75,z),(.018,.48,.025),GM,.006)
box('Orange engine service hatch',(-1.03,.68,1.39),(.035,.25,.19),OR,.012)
for yy in [.59,.77]:bolt('Service hatch bolt',(-1.054,yy,1.43),r=.012)

# Rounded operator cab, true glazing frame, pillars and readable interior.
cx=.49
box('Cab ivory lower shell',(cx,-.12,1.48),(1.12,1.60,.36),IV,.12)
box('Cab rear solid wall',(cx,.60,2.00),(1.13,.15,1.38),IV,.07)
box('Cab softly crowned roof',(cx,-.09,2.71),(1.19,1.57,.18),IV,.085)
box('Roof service insert',(cx,-.02,2.81),(.67,.85,.045),SL,.016)
box('Roof orange identification accent',(cx,-.15,2.838),(.46,.22,.025),OR,.01)
up=Vector((0,.185,.983)).normalized()
frame('Windshield ivory frame',(cx,-.925,2.04),(1,0,0),up,1.08,1.37,.23,.09,.10,IV)
frame('Windshield rubber seal',(cx,-.977,2.05),(1,0,0),up,.90,1.19,.17,.025,.025,RB)
pane('Main windshield',(cx,-.985,2.05),(1,0,0),up,.85,1.14,.145,.014,GL)
for side in [-1,1]:
 x=cx+side*.567
 frame('Cab side door ivory frame',(x,-.10,2.065),(0,1,0),(0,0,1),1.35,1.28,.22,.08,.075,IV)
 frame('Cab door window gasket',(x+side*.043,-.10,2.065),(0,1,0),(0,0,1),1.19,1.12,.16,.025,.025,RB)
 pane('Cab door glass',(x+side*.059,-.10,2.065),(0,1,0),(0,0,1),1.14,1.07,.135,.014,GL)
 plate_yz('Continuous sloped A pillar',x,[(-1.12,1.40),(-.835,2.71),(-.64,2.71),(-.64,1.40)],.105,IV,.03)
 box('Cab rear pillar',(x,.565,2.02),(.10,.14,1.31),IV,.04)
 box('Lower door kick panel',(x+side*.02,-.12,1.48),(.065,1.20,.28),IV,.022)
 if side>0:
  box('Door handle recess',(x+.074,.28,1.89),(.043,.085,.22),GM,.017)
  rod('Door grab handle',(x+.10,.28,1.82),(x+.10,.28,1.96),.017,IV)
  for z in [1.68,2.28]:box('Door hinge',(x+.07,-.56,z),(.05,.09,.13),GM,.017)
  rod('Mirror arm',(x,-.50,2.32),(x+.18,-.56,2.38),.018,GM)
  box('Small side mirror',(x+.21,-.56,2.40),(.11,.075,.23),GM,.03)
  box('Mirror reflective face',(x+.21,-.515,2.40),(.082,.012,.17),ST,.004)
box('Entry step support',(1.09,-.30,1.23),(.27,.65,.10),GM,.033)
box('Entry steel footplate',(1.12,-.30,1.291),(.29,.66,.024),ST,.008)
for j in range(8):box('Step tread grip',(1.12,-.565+j*.075,1.308),(.24,.018,.009),RB,.003)
frame('Rear cab window frame',(cx,.688,2.13),(1,0,0),(0,0,1),.84,.94,.17,.04,.025,GM)
pane('Rear cab glazing',(cx,.707,2.13),(1,0,0),(0,0,1),.76,.86,.13,.012,GL)
box('Operator floor',(cx,-.11,1.56),(.91,1.31,.06),GM,.02)
box('Operator seat cushion',(cx,.22,1.79),(.47,.48,.15),SE,.06)
box('Operator seat back',(cx,.41,2.09),(.47,.13,.55),SE,.05,rotation=(math.radians(-6),0,0))
box('Operator headrest',(cx,.43,2.38),(.27,.15,.19),SE,.06)
cyl('Seat base',(cx,.22,1.66),.15,.15,GM,vertices=32,bevel=.02)
for xx in [cx-.34,cx+.34]:
 box('Seat armrest',(xx,.12,1.98),(.11,.44,.08),GM,.03)
 rod('Control joystick',(xx,-.01,2.01),(xx,-.045,2.15),.019,GM)
 sphere('Joystick grip',(xx,-.045,2.15),(.034,.037,.042),SE)
for xx in [cx-.19,cx+.19]:box('Floor control pedal',(xx,-.63,1.62),(.15,.27,.05),GM,.014,rotation=(math.radians(18),0,0))
box('Low cab instrument console',(cx,-.69,1.86),(.68,.21,.20),GM,.055)
box('Instrument display',(cx,-.799,1.91),(.23,.012,.09),GL,.004)
for xx in [cx-.43,cx+.43]:
 box('Roof worklight housing',(xx,-.835,2.78),(.19,.16,.19),GM,.045)
 box('Roof worklight lens',(xx,-.925,2.78),(.135,.024,.13),EM,.009)
rod('Windshield wiper arm',(cx-.32,-1.071,1.58),(cx-.26,-1.022,1.91),.011,GM)
rod('Windshield wiper blade',(cx-.29,-1.04,1.76),(cx-.22,-.99,2.12),.015,RB)

# Protected exhaust stack has actual open slots around a central pipe.
tube('Exhaust pipe',[(-.65,.96,1.95),(-.65,.96,2.49),(-.65,.90,2.68)],.048,GM,True)
for z in [2.09,2.18,2.27,2.36,2.45]:
 tube('Exhaust guard hoop',[(-.65+.095*math.cos(j*math.tau/32),.96+.095*math.sin(j*math.tau/32),z) for j in range(32)],.009,ST,cyclic=True)
for k in range(10):
 a=k*math.tau/10;rod('Exhaust guard rib',(-.65+.095*math.cos(a),.96+.095*math.sin(a),2.08),(-.65+.095*math.cos(a),.96+.095*math.sin(a),2.47),.013,GM)

# Actual articulated boom, stick, pin bosses, hydraulic barrels and piston rods.
BX=-.55
boom_profile=[(-.59,1.28),(-.81,2.03),(-1.24,2.81),(-2.03,3.10),(-2.18,2.84),(-1.47,2.53),(-1.12,1.95),(-.91,1.23)]
plate_yz('Forged curved main boom',BX,boom_profile,.39,SG,.07)
bc=Vector((sum(y for y,z in boom_profile)/len(boom_profile),sum(z for y,z in boom_profile)/len(boom_profile)))
inset=[tuple(bc+(Vector((y,z))-bc)*.83) for y,z in boom_profile]
for side in [-1,1]:plate_yz('Boom side reinforced inset',BX+side*.201,inset,.018,SL,.005)
stick_profile=[(-2.12,3.23),(-2.35,3.10),(-2.94,1.15),(-2.77,.97),(-2.59,1.15),(-1.93,3.01)]
plate_yz('Rounded excavator stick',BX,stick_profile,.32,SG,.065)
sc=Vector((sum(y for y,z in stick_profile)/len(stick_profile),sum(z for y,z in stick_profile)/len(stick_profile)))
for side in [-1,1]:plate_yz('Stick service panel',BX+side*.166,[tuple(sc+(Vector((y,z))-sc)*.79) for y,z in stick_profile],.015,SL,.004)
def pivot(name,y,z,r,width):
 cyl(name+' axle',(BX,y,z),r,width,GM,(1,0,0),48,.015)
 for side in [-1,1]:
  cyl(name+' silver boss',(BX+side*(width/2+.015),y,z),r*.80,.040,ST,(1,0,0),40,.010)
  cyl(name+' orange pin cap',(BX+side*(width/2+.042),y,z),r*.55,.023,OR,(1,0,0),32,.007)
for name,y,z,r,w in [('Boom base',-.76,1.39,.165,.65),('Boom elbow',-2.065,2.98,.15,.56),('Stick bucket pivot',-2.78,1.09,.13,.55),('Stick cylinder attachment',-2.145,3.14,.10,.48)]:pivot(name,y,z,r,w)
box('Boom root pedestal',(BX,-.67,1.31),(.68,.48,.34),SG,.11)
def hydraulic(name,a,b,r):
 a=Vector(a);b=Vector(b);d=b-a;mid=a+d*.63
 rod(name+' barrel',a,mid,r,GM);rod(name+' polished piston',mid,b,r*.48,CH)
 cyl(name+' rod seal',mid,r*1.08,r*.30,ST,d,40,.007)
 cyl(name+' barrel cap',a+d*.07,r*1.06,r*.36,GM,d,40,.008)
 for label,p in [('base',a),('tip',b)]:cyl(name+' '+label+' clevis',p,r*.92,r*1.9,GM,(1,0,0),36,.009)
for side in [-1,1]:
 xx=BX+side*.285
 hydraulic('Paired boom lift cylinder',(xx,-.80,1.39),(xx,-1.19,2.48),.09)
 cyl('Lift pin silver end cap',(BX+side*.411,-1.19,2.48),.078,.042,ST,(1,0,0),40,.008)
 cyl('Lift pin orange witness cap',(BX+side*.438,-1.19,2.48),.049,.018,OR,(1,0,0),32,.005)
rod('Boom cylinder mounting pin',(BX-.39,-1.19,2.48),(BX+.39,-1.19,2.48),.075,GM)
hydraulic('Stick curl cylinder',(BX,-1.03,2.48),(BX,-2.145,3.14),.105)
hydraulic('Bucket tilt cylinder',(BX,-2.30,2.94),(BX,-3.08,1.28),.092)
for side in [-1,1]:
 xx=BX+side*.205
 beam('Bucket rocker link',(xx,-3.08,1.28),(xx,-2.78,1.09),.105,.12,GM,.035)
 beam('Bucket connecting link',(xx,-3.08,1.28),(xx,-2.96,.94),.09,.10,GM,.03)
for name,y,z in [('Bucket rocker pin',-3.08,1.28),('Bucket lower link pin',-2.96,.94)]:pivot(name,y,z,.084,.60)

# Hollow bucket: thick bent shell and independent solid rounded side cheeks.
p0=Vector((-3.62,.30));p1=Vector((-3.28,.02));p2=Vector((-2.57,.12));p3=Vector((-2.73,1.04))
outer=[];inner=[]
for j in range(41):
 t=j/40;p=(1-t)**3*p0+3*(1-t)**2*t*p1+3*(1-t)*t*t*p2+t**3*p3
 tangent=3*(1-t)**2*(p1-p0)+6*(1-t)*t*(p2-p1)+3*t*t*(p3-p2)
 normal=Vector((-tangent.y,tangent.x)).normalized();outer.append(tuple(p));inner.append(tuple(p+normal*.070))
N=len(outer);vs=[]
for xx in [BX-.51,BX+.51]:
 for loop in [outer,inner]:vs.extend([(xx,y,z) for y,z in loop])
fs=[]
for j in range(N-1):fs.extend([(j,j+1,2*N+j+1,2*N+j),(N+j,3*N+j,3*N+j+1,N+j+1),(j,N+j,N+j+1,j+1),(2*N+j,2*N+j+1,3*N+j+1,3*N+j)])
for j in [0,N-1]:fs.append((j,2*N+j,3*N+j,N+j))
bucket=mesh('Hollow rounded digging bucket',vs,fs,GM,.012);bucket['hollow_bucket_shell']=True
for side in [-1,1]:
 xx=BX+side*.522
 plate_yz('Bucket thick side cheek',xx,outer,.075,GM,.018)
 tube('Rounded bucket cheek rim',[(xx+side*.042,y,z) for y,z in outer]+[(xx+side*.042,*outer[0])],.017,ST)
 plate_yz('Bucket mounting ear',BX+side*.30,[(-2.91,.79),(-2.91,1.16),(-2.69,1.16),(-2.67,.93)],.09,GM,.025)
rod('Blunt bucket cutting edge',(BX-.565,-3.59,.33),(BX+.565,-3.59,.33),.042,ST)
for xx in [BX-.31,BX,BX+.31]:tube('Bucket exterior stiffening rib',[(xx,y+.018,z-.023) for y,z in outer],.020,GM)

# Heavy service hoses follow actual linkage routes and terminate at fittings.
for side in [-1,1]:
 xx=BX+side*.245
 pts=[(xx,-.66,1.47),(xx,-.82,1.98),(xx,-1.18,2.67),(xx,-1.58,2.91),(xx,-1.98,3.09),(xx,-2.15,3.03),(xx,-2.27,2.74)]
 tube('Main boom hydraulic hose',pts,.029,RB,True)
 rod('Hose lower ferrule',pts[0],Vector(pts[0])+Vector((0,-.035,.11)),.042,ST)
 rod('Hose orange coupling',pts[-1],Vector(pts[-1])+Vector((0,-.02,-.09)),.039,OR)
 port=(BX+side*.175,-2.29,2.65)
 rod('Hose fitted elbow connection',Vector(pts[-1])+Vector((0,-.02,-.09)),port,.030,ST)
 cyl('Stick hydraulic side port',port,.053,.035,GM,(1,0,0),32,.008)
 for yy,zz in [(-.99,2.28),(-1.37,2.79)]:box('Boom hose strap',(xx,yy,zz),(.09,.10,.06),GM,.02)
tube('Bucket hydraulic flexible return',[(BX-.23,-2.23,2.92),(BX-.30,-2.41,2.69),(BX-.28,-2.57,2.04),(BX-.27,-2.85,1.30),(BX-.22,-2.97,1.15)],.025,RB,True)
for xx in [BX-.11,BX+.11]:tube('Deck hydraulic loop',[(xx,-.70,1.45),(xx,-.45,1.6),(xx,-.12,1.57),(xx,.10,1.42)],.032,RB,True)

# Bake, clean, orient and UV every export mesh.
bpy.ops.object.select_all(action='DESELECT')
for o in list(ASSET.objects):
 bpy.context.view_layer.objects.active=o;o.select_set(True)
 if o.type=='CURVE':bpy.ops.object.convert(target='MESH')
 for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT');o.select_set(False)
bpy.context.view_layer.update();minz=min((o.matrix_world@v.co).z for o in ASSET.objects for v in o.data.vertices)
for o in ASSET.objects:o.location.z-=minz
bpy.context.view_layer.update()
root=bpy.data.objects.new('TrackedExcavator_ROOT',None);ASSET.objects.link(root);root['reference']='REF/Set02/tracked_excavator.png';root['static_asset']=True
for o in list(ASSET.objects):
 if o!=root:
  mw=o.matrix_world.copy();o.parent=root;o.matrix_world=mw
bpy.ops.object.select_all(action='DESELECT')
for o in ASSET.objects:o.select_set(True)
bpy.context.view_layer.objects.active=root
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
bpy.ops.export_scene.gltf(filepath=str(ROOT/'tracked_excavator.glb'),export_format='GLB',use_selection=True,export_apply=True)
bpy.ops.export_scene.fbx(filepath=str(ROOT/'tracked_excavator.fbx'),use_selection=True,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,bake_anim=False,mesh_smooth_type='FACE')

floor=box('Studio floor',(0,0,-.08),(200,200,.15),material('Studio warm gray',(.47,.45,.41),.86),.01);link(floor,STUDIO)
world=bpy.data.worlds.new('Studio World');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.68,.70,.74,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4
target=Vector((-.1,-.9,1.40))
def area(name,loc,power,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);STUDIO.objects.link(o);o.location=loc;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
area('Key softbox',(-3,-5,7.5),1300,5.5,(1,.92,.79));area('Cool fill',(5,-1,5),850,4.5,(.80,.88,1));area('Rim softbox',(1,5,6),1500,4,(1,.97,.86))
camd=bpy.data.cameras.new('Hero_Camera');cam=bpy.data.objects.new('Hero_Camera',camd);STUDIO.objects.link(cam);scene.camera=cam;camd.type='ORTHO';camd.ortho_scale=6.7
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=40;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=1440;scene.render.resolution_y=1080;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
def camera_at(p):cam.location=p;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
camera_at((6.4,-9.5,5.1));scene.render.filepath=str(ROOT/'renders'/'hero.png')
bpy.ops.object.select_all(action='DESELECT');root.select_set(True);bpy.context.view_layer.objects.active=root
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'tracked_excavator.blend'))
captures=[]
for name,position in [('hero',(6.4,-9.5,5.1)),('rear',(-6.8,7.3,4.7))]:
 camera_at(position);scene.render.filepath=str(ROOT/'renders'/f'{name}.png');a=datetime.now(timezone.utc).isoformat();tick=time.monotonic();bpy.ops.render.render(write_still=True)
 captures.append({'name':name,'file':f'renders/{name}.png','camera':list(position),'target':list(target),'started_at_utc':a,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'seconds':time.monotonic()-tick})
camera_at((6.4,-9.5,5.1));scene.render.filepath=str(ROOT/'renders'/'hero.png');bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'tracked_excavator.blend'))
meshes=[o for o in ASSET.objects if o.type=='MESH'];pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices];bounds=[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]];tris=0;zero=0
for o in meshes:o.data.calc_loop_triangles();tris+=len(o.data.loop_triangles);zero+=sum(t.area<1e-12 for t in o.data.loop_triangles)
report={'asset':'tracked_excavator','started_at_utc':START,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'build_wall_seconds':time.monotonic()-T0,'blender':bpy.app.version_string,'mesh_objects':len(meshes),'triangles':tris,'zero_area_triangles':zero,'bounds':bounds,'dimensions_m':[bounds[1][i]-bounds[0][i] for i in range(3)],'tracks':track_names,'primary_track_count':len(track_names),'missing_uv':[o.name for o in meshes if not o.data.uv_layers],'missing_materials':[o.name for o in meshes if not o.data.materials]}
(ROOT/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(ROOT/'capture_manifest.json').write_text(json.dumps({'renderer':'Blender Cycles CPU','threads':4,'samples':40,'denoising':True,'resolution':[1440,1080],'projection':'ORTHO','ortho_scale':6.7,'actual_renders':True,'views':captures},indent=2),encoding='utf-8')
print('SET02_EXCAVATOR_BUILD '+json.dumps(report))
