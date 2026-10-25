"""Reference-driven cargo rover. Run with Blender 4.5 --background --factory-startup."""
import bpy, bmesh, math, json, time, os
from pathlib import Path
from mathutils import Vector, Matrix
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent
ROOT.mkdir(parents=True, exist_ok=True)
(ROOT/'renders').mkdir(exist_ok=True)
START=datetime.now(timezone.utc).isoformat()
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
asset=bpy.data.collections.new('ASSET'); bpy.context.scene.collection.children.link(asset)
studio=bpy.data.collections.new('STUDIO'); bpy.context.scene.collection.children.link(studio)

def mat(name, color, rough=.4, metal=.0, emission=0, transmission=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    p.inputs['Transmission Weight'].default_value=transmission
    if emission:
        p.inputs['Emission Color'].default_value=(*color,1)
        p.inputs['Emission Strength'].default_value=emission
    return m
ivory=mat('Rover_Warm_Ivory_Paint',(0.72,.69,.59),.32,.16)
sage=mat('Rover_Sage_Enamel',(.23,.34,.29),.35,.24)
sage_dark=mat('Rover_Sage_Inset',(.15,.235,.195),.4,.2)
sage_light=mat('Rover_Sage_Edge',(.32,.43,.36),.32,.25)
graphite=mat('Rover_Graphite_Metal',(.075,.088,.09),.36,.48)
rubber=mat('Rover_Tyre_Rubber',(.032,.038,.039),.72,.0)
treadmat=mat('Rover_Tread_Rubber',(.047,.053,.053),.67,.0)
steel=mat('Rover_Brushed_Steel',(.30,.33,.32),.28,.75)
orange=mat('Rover_Utility_Orange',(.76,.29,.055),.36,.22)
glass=mat('Rover_Smoky_Blue_Glass',(.085,.145,.175),.16,.08,transmission=.45)
lamp=mat('Rover_Warm_Headlamp',(.91,.78,.49),.2,.08,emission=2)
amber=mat('Rover_Amber_Lens',(.83,.28,.03),.26,.06,emission=.35)
red=mat('Rover_Red_Taillight',(.48,.055,.022),.28,.08,emission=.3)
seatmat=mat('Rover_Charcoal_Upholstery',(.065,.085,.09),.83)

def link(o, collection=asset):
    for c in list(o.users_collection): c.objects.unlink(o)
    collection.objects.link(o); return o
def finish(o,name,m,smooth=True,bevel=0,segments=3):
    o.name=name; link(o)
    if m:o.data.materials.append(m)
    if o.type=='MESH':
        for p in o.data.polygons:p.use_smooth=smooth
    if bevel:
        b=o.modifiers.new('Soft manufactured edges','BEVEL'); b.width=bevel;b.segments=segments
    if o.type=='MESH' and smooth:
        n=o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL');n.keep_sharp=True;n.weight=50
    return o
def box(name,loc,dim,m,bevel=.04,rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if rotation:o.rotation_euler=rotation
    return finish(o,name,m,True,min(bevel,min(dim)*.42),3)
def mesh(name,verts,faces,m,bevel=0,smooth=True):
    me=bpy.data.meshes.new(name+'_mesh');me.from_pydata(verts,[],faces);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new(name,me);asset.objects.link(o)
    return finish(o,name,m,smooth,bevel,2)
def cyl(name,loc,r,depth,m,axis=(0,0,1),vertices=48,bevel=.015):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc)
    o=bpy.context.object;o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
    return finish(o,name,m,True,bevel,3)
def rod(name,a,b,r,m):
    d=Vector(b)-Vector(a);return cyl(name,(Vector(a)+Vector(b))/2,r,d.length,m,d,24,min(.008,r*.2))
def sphere(name,loc,dim,m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=1,location=loc)
    o=bpy.context.object;o.scale=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,m)
def path(name,points,r,m,cyclic=False):
    cu=bpy.data.curves.new(name+'_curve','CURVE');cu.dimensions='3D';cu.resolution_u=12
    cu.bevel_depth=r;cu.bevel_resolution=3;cu.resolution_u=12;cu.use_fill_caps=True
    s=cu.splines.new('POLY');s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    s.use_cyclic_u=cyclic
    o=bpy.data.objects.new(name,cu);asset.objects.link(o);o.data.materials.append(m)
    return o
def rr(w,h,r,n=8):
    pts=[]
    for cx,cy,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for j in range(n):
            a=math.radians(start+j*90/n);pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    return pts
def frame(name,origin,u,v,w,h,r,border,depth,m):
    u,v=Vector(u),Vector(v);normal=u.cross(v).normalized();origin=Vector(origin)
    outer=rr(w,h,r);inner=rr(w-2*border,h-2*border,max(.012,r-border));N=len(outer)
    vv=[]
    for d in [-depth/2,depth/2]:
        for loop in [outer,inner]:
            vv.extend([tuple(origin+u*x+v*y+normal*d) for x,y in loop])
    ff=[]
    for i in range(N):
        j=(i+1)%N
        ff.extend([(i,j,N+j,N+i),(2*N+i,3*N+i,3*N+j,2*N+j),(i,2*N+i,2*N+j,j),(N+i,N+j,3*N+j,3*N+i)])
    return mesh(name,vv,ff,m,min(.008,depth*.35,border*.35))
def pane(name,origin,u,v,w,h,r,depth,m):
    u,v=Vector(u),Vector(v);normal=u.cross(v).normalized();origin=Vector(origin);pts=rr(w,h,r);N=len(pts)
    vv=[tuple(origin+u*x+v*y+normal*d) for d in [-depth/2,depth/2] for x,y in pts]
    ff=[tuple(reversed(range(N))),tuple(range(N,2*N))]
    ff.extend([(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)])
    return mesh(name,vv,ff,m,.004)

# Structural frame and visible running gear.
box('Main chassis',(0,0,.78),(1.63,3.58,.24),graphite,.09)
for x in [-.57,.57]:box('Box section chassis rail',(x,.05,.69),(.16,3.48,.21),graphite,.035)
for y in [-1.24,1.24]:
    rod('Live axle',(-1.06,y,.56),(1.06,y,.56),.075,graphite)
    sphere('Axle differential',(0,y,.56),(.23,.19,.18),graphite)
    cyl('Differential service cover',(0,y-.16,.56),.13,.035,steel,(0,1,0),32)
    for sign in [-1,1]:
        x=sign*.67
        rod('Suspension damper',(x,y+.10,.58),(x,y+.17,1.02),.045,steel)
        coil=[]
        for k in range(97):
            t=k/96;a=t*5.5*2*math.pi
            coil.append((x+.072*math.cos(a),y+.13+.072*math.sin(a),.63+t*.34))
        path('Orange coil spring',coil,.019,orange)
        rod('Suspension link',(sign*.3,y-.2,.64),(sign*.82,y,.55),.031,steel)
rod('Longitudinal driveshaft',(0,-1.24,.58),(0,1.24,.58),.045,steel)

# Four individually built pneumatic tyres with real raised chevron blocks.
wheel_records=[]
for sign in [-1,1]:
  for wy in [-1.24,1.24]:
    wx=sign*1.0; wz=.56; tag=('R' if sign>0 else 'L')+('_F' if wy<0 else '_R')
    profile=[(-.19,.28),(-.20,.39),(-.17,.47),(-.12,.505),(.12,.505),(.17,.47),(.20,.39),(.19,.28)]
    V=[];F=[];N=64
    for ax,rad in profile:
      for j in range(N):
        a=2*math.pi*j/N;V.append((wx+ax,wy+rad*math.sin(a),wz+rad*math.cos(a)))
    for q in range(len(profile)):
      nq=(q+1)%len(profile)
      for j in range(N):F.append((q*N+j,q*N+(j+1)%N,nq*N+(j+1)%N,nq*N+j))
    tire=mesh('Tyre_'+tag,V,F,rubber);wheel_records.append(tire.name)
    # tread vertices combined into one mesh per wheel, with softened exposed edges
    tv=[];tf=[]
    template=[(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]
    faces=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
    for j in range(32):
      for band in [-1,1]:
        a=(j+(0.38 if band>0 else 0))*2*math.pi/32
        R=Matrix.Rotation(-a,3,'X')@Matrix.Rotation(band*.33,3,'Z')
        center=Vector((wx+band*.087,wy+.502*math.sin(a),wz+.502*math.cos(a)))
        base=len(tv)
        for vx,vy,vz in template:tv.append(tuple(center+R@Vector((vx*.092,vy*.055,vz*.024))))
        tf.extend([tuple(base+k for k in face) for face in faces])
    mesh('Chevron tread_'+tag,tv,tf,treadmat,.009)
    for side in [-1,1]:
      xx=wx+side*.184
      cyl('Bead rim_'+tag,(xx,wy,wz),.322,.045,graphite,(1,0,0),64,.012)
      cyl('Wheel rim_'+tag,(xx+side*.017,wy,wz),.282,.055,sage,(1,0,0),64,.015)
      cyl('Wheel center_'+tag,(xx+side*.052,wy,wz),.173,.055,sage_light,(1,0,0),48,.018)
      cyl('Axle cap_'+tag,(xx+side*.083,wy,wz),.084,.035,graphite,(1,0,0),40,.012)
      for k in range(8):
        a=2*math.pi*k/8
        cyl('Rim bolt_'+tag,(xx+side*.05,wy+.228*math.sin(a),wz+.228*math.cos(a)),.018,.017,steel,(1,0,0),8,.003)
    # outer-side orange witness mark on the hub
    box('Hub utility stripe_'+tag,(wx+sign*.28,wy+.13,wz),(.018,.043,.17),orange,.013)

# Wheel arches are hollow curved solid sections, not intersecting full toruses.
for sign in [-1,1]:
  for wy in [-1.24,1.24]:
    vv=[];ff=[];N=37
    for x in [sign*.73,sign*1.27]:
      for r in [.625,.72]:
        for j in range(N):
          a=math.radians(-79+j*158/(N-1));vv.append((x,wy+r*math.sin(a),.56+r*math.cos(a)))
    for j in range(N-1):
      for base,other in [(0,N),(2*N,3*N),(0,2*N),(N,3*N)]:ff.append((base+j,base+j+1,other+j+1,other+j))
    for j in [0,N-1]:ff.append((j,N+j,3*N+j,2*N+j))
    mesh('Rounded fender',vv,ff,graphite,.027)
    box('Fender amber reflector',(sign*1.282,wy-.31,1.12),(.025,.19,.055),amber,.018)

# Cab: real open frame, glazing, cabin interior and separate lower shell.
box('Cab lower ivory shell',(0,-1.03,1.20),(1.78,1.72,.62),ivory,.17)
box('Cab rear structural wall',(0,-.22,1.70),(1.77,.17,1.38),sage,.11)
box('Cab rounded roof',(0,-.99,2.43),(1.82,1.67,.18),ivory,.085)
box('Roof recessed sage panel',(0,-.98,2.53),(1.51,1.35,.055),sage,.025)
wind_up=Vector((0,.205,.979)).normalized()
frame('Ivory windshield surround',(0,-1.84,1.93),(1,0,0),wind_up,1.79,1.10,.22,.11,.11,ivory)
frame('Windshield dark rubber seal',(0,-1.891,1.940),(1,0,0),wind_up,1.58,.89,.15,.031,.028,rubber)
pane('Front windshield',(0,-1.897,1.940),(1,0,0),wind_up,1.515,.828,.125,.015,glass)
for sign in [-1,1]:
    x=sign*.889
    # Solid A pillar joins the sloped windscreen to the side door frame.
    side_profile=[(-1.98,1.45),(-1.765,2.44),(-1.51,2.44),(-1.51,1.45)]
    pv=[(xx,y,z) for xx in [sign*.82,sign*.948] for y,z in side_profile]
    pf=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    mesh('Solid rounded front cab pillar',pv,pf,ivory,.035)
    box('Lower door outer panel',(x,-.98,1.37),(.085,1.24,.45),ivory,.06)
    frame('Door raised soft surround',(x,-.93,1.99),(0,1,0),(0,0,1),1.29,.92,.17,.075,.085,ivory)
    frame('Side window gasket',(x+sign*.05,-.93,1.99),(0,1,0),(0,0,1),1.14,.775,.12,.024,.025,rubber)
    pane('Side door window',(x+sign*.065,-.93,1.99),(0,1,0),(0,0,1),1.092,.727,.10,.016,glass)
    # Door seams traced with intentionally fine physical trim.
    seam=[(x+sign*.047,y,z) for y,z in [(-1.60,1.45),(-1.60,1.12),(-1.46,1.01),(-.36,1.01),(-.28,1.14),(-.28,1.54)]]
    path('Door lower seam',seam,.009,graphite)
    box('Recessed vertical door latch',(x+sign*.059,-.39,1.54),(.042,.09,.23),graphite,.03)
    box('Door latch lever',(x+sign*.085,-.39,1.55),(.024,.033,.14),steel,.01)
    for z in [1.2,1.52]:
        box('Door hinge',(x+sign*.065,-1.55,z),(.062,.10,.14),graphite,.018)
        for zz in [-.04,.04]:cyl('Door hinge fastener',(x+sign*.099,-1.55,z+zz),.012,.009,steel,(1,0,0),8,.002)
    rod('Mirror bracket',(sign*.86,-1.53,1.86),(sign*1.075,-1.53,1.96),.022,graphite)
    box('Side mirror housing',(sign*1.10,-1.55,2.03),(.18,.13,.34),graphite,.06)
    box('Side mirror glass',(sign*1.10,-1.478,2.03),(.13,.014,.26),steel,.025)
    box('Mirror amber strip',(sign*1.155,-1.622,2.03),(.033,.012,.23),amber,.01)
    box('Footstep support',(sign*.95,-.40,.88),(.28,.47,.13),graphite,.045)
    box('Brushed step plate',(sign*1.025,-.40,.956),(.30,.46,.026),steel,.012)
    for k in range(6):box('Footstep anti slip groove',(sign*1.028,-.57+k*.068,.971),(.25,.015,.008),rubber,.002)
    box('Underbed storage locker',(sign*.83,.25,.86),(.22,.58,.31),graphite,.055)
    frame('Locker pressed border',(sign*.958,.25,.86),(0,1,0),(0,0,1),.47,.23,.035,.017,.01,steel)

# Interior is visible through actual smoky glazing.
box('Cab floor',(0,-.98,1.42),(1.48,1.38,.075),graphite,.025)
box('Dashboard',(0,-1.57,1.53),(1.48,.27,.19),graphite,.06)
for sx in [-.42,.42]:
    box('Seat cushion',(sx,-.67,1.56),(.51,.50,.14),seatmat,.06)
    box('Seat back',(sx,-.41,1.83),(.51,.14,.57),seatmat,.065,rotation=(math.radians(-7),0,0))
    box('Seat headrest',(sx,-.37,2.13),(.28,.15,.18),seatmat,.06)
    rod('Seat support',(sx,-.65,1.43),(sx,-.65,1.52),.06,graphite)
steer_center=Vector((.42,-1.39,1.73));su=Vector((1,0,0));sv=Vector((0,.63,.77))
path('Steering wheel',[tuple(steer_center+su*.18*math.cos(i*math.tau/48)+sv*.18*math.sin(i*math.tau/48)) for i in range(48)],.018,graphite,True)
for a in [0,2.1,4.2]:rod('Steering spoke',steer_center,steer_center+su*.16*math.cos(a)+sv*.16*math.sin(a),.013,graphite)
rod('Steering column',(.42,-1.49,1.55),steer_center,.027,graphite)
frame('Rear cab window trim',(0,-.121,1.99),(1,0,0),(0,0,1),1.05,.44,.09,.035,.025,graphite)
pane('Rear cab glass',(0,-.101,1.99),(1,0,0),(0,0,1),.98,.37,.07,.012,glass)
for y in [-1.49,-.45]:
    path('Roof load handle',[(-.68,y,2.51),(-.68,y,2.64),(-.59,y,2.67),(.59,y,2.67),(.68,y,2.64),(.68,y,2.51)],.034,graphite)
box('Roof amber marker',(0,-1.55,2.555),(.25,.12,.027),amber,.025)
# Windshield wipers along its lower edge.
for sx in [-.37,.37]:
    rod('Wiper pivot arm',(sx,-1.987,1.56),(sx+.11,-1.983,1.60),.011,graphite)
    rod('Wiper blade',(sx-.21,-1.99,1.58),(sx+.23,-1.974,1.66),.015,rubber)

# Distinct open cargo bed, pressed side panels, top rails and hardware.
box('Cargo bed floor',(0,1.02,1.07),(1.91,2.08,.14),sage,.045)
box('Cargo bed front wall',(0,.015,1.43),(1.89,.095,.62),sage,.045)
for sign in [-1,1]:
    box('Cargo side wall',(sign*.917,1.03,1.44),(.105,2.03,.63),sage,.037)
    box('Cargo top rolled rail',(sign*.933,1.03,1.78),(.125,2.09,.105),sage_light,.047)
    for y in [.14,.74,1.34,1.93]:
        box('Cargo vertical reinforcement',(sign*.983,y,1.44),(.064,.066,.59),sage_light,.022)
        for z in [1.20,1.67]:cyl('Bed rivet',(sign*1.022,y,z),.014,.008,steel,(1,0,0),12,.003)
    for y in [.44,1.04,1.64]:box('Pressed side panel inset',(sign*.976,y,1.44),(.013,.48,.42),sage_dark,.006)
    for y in [.095,1.99]:
        box('Cargo corner latch',(sign*.994,y,1.61),(.063,.10,.27),graphite,.018)
        cyl('Cargo latch pin',(sign*1.032,y,1.67),.026,.022,steel,(1,0,0),16,.004)
    box('Cargo side amber reflector',(sign*.99,1.77,1.14),(.026,.20,.057),amber,.016)
for x in [-.72,-.48,-.24,0,.24,.48,.72]:box('Bed floor stiffening channel',(x,1.03,1.148),(.035,1.85,.018),sage_dark,.007)
box('Tailgate',(0,2.04,1.44),(1.89,.10,.63),sage,.045)
box('Tailgate top rolled rail',(0,2.045,1.78),(1.94,.13,.105),sage_light,.045)
frame('Tailgate pressed border',(0,2.098,1.44),(1,0,0),(0,0,1),1.59,.43,.04,.025,.016,sage_light)
for x in [-.64,.64]:
    box('Tailgate hinge mounting',(x,2.104,1.17),(.24,.05,.085),graphite,.016)
    cyl('Tailgate hinge barrel',(x,2.14,1.15),.035,.27,steel,(1,0,0),24,.008)
for sign in [-1,1]:
    box('Tailgate latch',(sign*.78,2.118,1.53),(.10,.05,.26),graphite,.018)
    box('Rear lamp housing',(sign*.83,2.105,.99),(.23,.10,.17),graphite,.035)
    box('Rear red brake lens',(sign*.88,2.162,1.01),(.085,.019,.10),red,.012)
    box('Rear amber lens',(sign*.78,2.162,1.01),(.065,.019,.10),amber,.012)
box('Rear bumper',(0,2.15,.82),(1.91,.22,.19),graphite,.055)
box('Rear step grip',(0,2.18,.93),(.65,.20,.035),steel,.015)

# Front service fascia, lamps, grille, bumper and tow fittings.
box('Front sage service panel',(0,-1.925,1.28),(1.23,.13,.38),sage,.055)
box('Front radiator dark recess',(0,-2.001,1.052),(.89,.035,.14),rubber,.035)
for z in [1.025,1.06,1.095]:rod('Radiator grille slat',(-.39,-2.025,z),(.39,-2.025,z),.009,graphite)
for sign in [-1,1]:
    x=sign*.665
    box('Headlight protective housing',(x,-1.977,1.285),(.34,.18,.35),graphite,.07)
    cyl('Headlight steel bezel',(x,-2.083,1.30),.124,.032,steel,(0,-1,0),48,.012)
    cyl('Headlight recessed seal',(x,-2.104,1.30),.105,.019,rubber,(0,-1,0),48,.006)
    sphere('Convex headlight lens',(x,-2.12,1.30),(.086,.023,.086),lamp)
    box('Front indicator',(x,-2.083,1.11),(.18,.037,.051),amber,.017)
box('Broad rounded front bumper',(0,-2.057,.91),(1.96,.23,.24),graphite,.085)
box('Front bumper center inset',(0,-2.186,.92),(.58,.018,.10),rubber,.028)
for x in [-.62,.62]:
    frame('Front orange tow loop',(x,-2.201,.92),(1,0,0),(0,0,1),.17,.19,.05,.033,.039,orange)
    rod('Tow loop dark mounting',(x,-2.16,.92),(x,-2.04,.92),.045,graphite)
for x in [-.48,.48]:
    for z in [1.18,1.4]:cyl('Front panel fastener',(x,-2.00,z),.012,.009,steel,(0,-1,0),8,.002)

# Convert all authoring pieces to UV-bearing mesh and bake final manufacturing edges.
bpy.ops.object.select_all(action='DESELECT')
for o in list(asset.objects):
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    if o.type=='CURVE':bpy.ops.object.convert(target='MESH')
    for mod in list(o.modifiers):
        try:bpy.ops.object.modifier_apply(modifier=mod.name)
        except RuntimeError:pass
    if o.type=='MESH':
        bm=bmesh.new();bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
        bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges))
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
        # Per-component smart UVs preserve useful independently editable surfaces.
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        bm=bmesh.from_edit_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.update_edit_mesh(o.data)
        bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.025)
        bpy.ops.object.mode_set(mode='OBJECT')
    o.select_set(False)
# Global scale maps the reference truck to a compact ~3.9m vehicle.
for o in asset.objects:
    o.location*=.9
    if o.type=='MESH':
        for v in o.data.vertices:v.co*=.9
bpy.context.view_layer.update()
minimum=min((o.matrix_world@Vector(c)).z for o in asset.objects for c in o.bound_box)
for o in asset.objects:o.location.z-=minimum
bpy.context.view_layer.update()

# Geometry-only exports, root hierarchy with deterministic material names.
root=bpy.data.objects.new('CargoRover_ROOT',None);asset.objects.link(root)
root['asset']='cargo_rover';root['reference']='REF/Set01/cargo_rover.png';root['units']='meters'
for o in list(asset.objects):
    if o!=root:
        mw=o.matrix_world.copy();o.parent=root;o.matrix_world=mw
bpy.ops.object.select_all(action='DESELECT')
for o in asset.objects:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(ROOT/'cargo_rover.glb'),export_format='GLB',use_selection=True,export_apply=True)
bpy.ops.export_scene.fbx(filepath=str(ROOT/'cargo_rover.fbx'),use_selection=True,object_types={'MESH','EMPTY'},apply_unit_scale=True,axis_forward='-Z',axis_up='Y',bake_anim=False,mesh_smooth_type='FACE')

# Studio exists only in the editable .blend and rendered evidence.
floor=box('Studio floor',(0,0,-.08),(200,200,.15),mat('Studio warm grey',(.47,.45,.41),.85),.01);link(floor,studio)
world=bpy.data.worlds.new('Studio world');bpy.context.scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.68,.72,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.45
def area(name,loc,power,size,color):
    ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size;ld.color=color
    o=bpy.data.objects.new(name,ld);studio.objects.link(o);o.location=loc
    o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
area('Large softbox',(-3.6,-4.7,7),1000,5,(1,.91,.78))
area('Cool fill',(5,-1,4.0),650,4,(.80,.88,1))
area('Rear rim',(1,5,5.5),1200,3.5,(1,.96,.87))
camd=bpy.data.cameras.new('Hero_Camera');cam=bpy.data.objects.new('Hero_Camera',camd);studio.objects.link(cam)
camd.type='ORTHO';camd.ortho_scale=5.2
scene=bpy.context.scene;scene.camera=cam;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=40;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=1440;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
def camera_at(loc,target=(0,0,1.12)):
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
camera_at((6.4,-8.4,5.1))
bpy.ops.object.select_all(action='DESELECT');root.select_set(True);bpy.context.view_layer.objects.active=root
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'cargo_rover.blend'))
scene.render.filepath=str(ROOT/'renders'/'hero.png');bpy.ops.render.render(write_still=True)
camera_at((-6.2,8.2,4.8));scene.render.filepath=str(ROOT/'renders'/'rear.png');bpy.ops.render.render(write_still=True)
camera_at((6.4,-8.4,5.1));scene.render.filepath=str(ROOT/'renders'/'hero.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'cargo_rover.blend'))
meshes=[o for o in asset.objects if o.type=='MESH']
points=[o.matrix_world@Vector(p) for o in meshes for p in o.bound_box]
mins=[min(p[i] for p in points) for i in range(3)];maxs=[max(p[i] for p in points) for i in range(3)]
tris=0
for o in meshes:o.data.calc_loop_triangles();tris+=len(o.data.loop_triangles)
report={'asset':'cargo_rover','started_at_utc':START,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'blender':bpy.app.version_string,'mesh_objects':len(meshes),'triangles':tris,'dimensions_m':[maxs[i]-mins[i] for i in range(3)],'bounds_min':mins,'bounds_max':maxs,'missing_uv':[o.name for o in meshes if not o.data.uv_layers],'nonfinite_vertices':[o.name for o in meshes if any(not math.isfinite(c) for v in o.data.vertices for c in v.co)],'wheel_count':len(wheel_records),'geometry_only_exports':True,'materials':sorted({m.name for o in meshes for m in o.data.materials}),'renders':['renders/hero.png','renders/rear.png'],'limitations':['Static model; no armature, collision mesh or LOD chain.','UVs are per component and may overlap across different objects; no single atlas or measured uniform texel density was requested.','Solid PBR materials; concept-art micro-weathering is intentionally not baked into texture maps.']}
(ROOT/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('SET01_CARGO_COMPLETE '+json.dumps(report))
