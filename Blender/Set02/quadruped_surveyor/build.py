import bpy, math, os, json, time, hashlib
from mathutils import Vector, Matrix
from datetime import datetime, timezone, timedelta
import bmesh

ROOT = os.path.dirname(os.path.abspath(__file__))
SLUG = 'quadruped_surveyor'
STARTED = '2026-10-23T12:15:19.7380146Z'
BUILD_T0 = time.time()
os.makedirs(os.path.join(ROOT, 'renders'), exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials): bpy.data.materials.remove(m)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
asset = bpy.data.collections.get('Collection'); asset.name = 'ASSET'
studio = bpy.data.collections.new('STUDIO'); bpy.context.scene.collection.children.link(studio)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'; scene.unit_settings.scale_length = 1.0
scene['asset_description'] = 'Four-legged terrain survey platform. Front -Y, Z up, metres; static articulated mechanical assembly.'
scene['reference'] = 'REF/Set02/quadruped_surveyor.png'

def material(name, color, roughness=.4, metallic=0.0, transmission=0.0):
    m=bpy.data.materials.new(name); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=roughness
    p.inputs['Metallic'].default_value=metallic
    p.inputs['Transmission Weight'].default_value=transmission
    m.diffuse_color=(*color,1)
    return m

IVORY=material('Ceramic-coated warm ivory',(.68,.66,.57),.36,.12)
SAGE=material('Matte sage equipment enamel',(.265,.325,.285),.42,.18)
SAGELIGHT=material('Sage deck edge enamel',(.335,.39,.345),.44,.14)
GRAPHITE=material('Graphite cast alloy',(.065,.077,.073),.46,.52)
DARK=material('Black vent and joint recess',(.012,.019,.018),.47,.3)
RUBBER=material('Moulded charcoal elastomer',(.028,.033,.030),.68,.05)
STEEL=material('Brushed stainless hardware',(.31,.34,.32),.28,.82)
ORANGE=material('Safety amber release hardware',(.66,.215,.037),.38,.22)
GLASS=material('Coated optical glass',(.006,.027,.023),.10,.3,.28)
LIDAR=material('Lidar smoked optical window',(.009,.026,.027),.2,.42)
BLUE=material('Subtle lidar detector tint',(.02,.09,.08),.28,.5)
FLOOR=material('Studio warm gray',(.56,.535,.50),.76,0)

def move_to(obj, coll):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    coll.objects.link(obj)

def finish(obj,name,mat,bevel=0,segments=4,smooth=True):
    obj.name=name; move_to(obj,asset)
    if mat: obj.data.materials.append(mat)
    if bevel:
        mod=obj.modifiers.new('Machined edge radii','BEVEL'); mod.width=bevel; mod.segments=segments
        mod.limit_method='ANGLE'
    if smooth:
        for p in obj.data.polygons: p.use_smooth=True
        mod=obj.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL'); mod.keep_sharp=True; mod.weight=30
    return obj

def box(name,loc,dim,mat,bevel=.02,quat=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object; o.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if quat: o.rotation_mode='QUATERNION'; o.rotation_quaternion=quat
    return finish(o,name,mat,min(bevel,min(dim)*.4),5)

def cyl(name,loc,r,depth,mat,axis=(0,0,1),bevel=.005,verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,end_fill_type='NGON',location=loc)
    o=bpy.context.object; o.rotation_mode='QUATERNION'; o.rotation_quaternion=Vector((0,0,1)).rotation_difference(Vector(axis))
    return finish(o,name,mat,min(bevel,depth*.4,r*.4),3)

def sphere(name,loc,scale,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=20,radius=1,location=loc)
    o=bpy.context.object; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,mat,0,1)

def mesh_obj(name,verts,faces,mat,bevel=0):
    me=bpy.data.meshes.new(name+' mesh'); me.from_pydata(verts,[],faces); me.update()
    bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); asset.objects.link(o)
    return finish(o,name,mat,bevel,4)

def ring(name,loc,major,minor,mat,axis=(0,0,1),segments=64):
    bpy.ops.mesh.primitive_torus_add(major_segments=segments,minor_segments=10,location=loc,major_radius=major,minor_radius=minor)
    o=bpy.context.object; o.rotation_mode='QUATERNION'; o.rotation_quaternion=Vector((0,0,1)).rotation_difference(Vector(axis))
    return finish(o,name,mat,0)

def lathe(name,profile,mat,loc=(0,0,0),axis=(0,0,1),n=64):
    vs=[]; levels=[]
    for rad,z in profile:
        if rad==0:
            levels.append([len(vs)]); vs.append((0,0,z))
        else:
            levels.append(list(range(len(vs),len(vs)+n)))
            vs.extend([(rad*math.cos(2*math.pi*i/n),rad*math.sin(2*math.pi*i/n),z) for i in range(n)])
    fs=[]
    for a,b in zip(levels,levels[1:]):
        if len(a)==1:
            fs.extend([(a[0],b[(i+1)%n],b[i]) for i in range(n)])
        elif len(b)==1:
            fs.extend([(a[i],a[(i+1)%n],b[0]) for i in range(n)])
        else:
            fs.extend([(a[i],a[(i+1)%n],b[(i+1)%n],b[i]) for i in range(n)])
    o=mesh_obj(name,vs,fs,mat)
    o.location=loc; o.rotation_mode='QUATERNION'; o.rotation_quaternion=Vector((0,0,1)).rotation_difference(Vector(axis))
    return o

def round_rect(w,d,r,n=10):
    out=[]
    for cx,cy,ang in [(w/2-r,d/2-r,0),(-w/2+r,d/2-r,90),(-w/2+r,-d/2+r,180),(w/2-r,-d/2+r,270)]:
        for i in range(n+1):
            t=math.radians(ang+i*90/n); out.append((cx+r*math.cos(t),cy+r*math.sin(t)))
    return out

def hull(name,rings,mat):
    verts=[]
    for z,w,d,r in rings: verts.extend([(x,y,z) for x,y in round_rect(w,d,r)])
    n=len(verts)//len(rings); faces=[]
    faces.append(tuple(range(n-1,-1,-1)))
    for k in range(len(rings)-1):
        faces.extend([(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i) for i in range(n)])
    faces.append(tuple(range((len(rings)-1)*n,len(rings)*n)))
    return mesh_obj(name,verts,faces,mat,.008)

def beam(name,a,b,width,depth,mat,bevel=.015):
    a,b=Vector(a),Vector(b)
    q=Vector((0,0,1)).rotation_difference(b-a)
    return box(name,(a+b)/2,(width,depth,(b-a).length),mat,bevel,q)

def egg_panel(name,loc,depth,width,length,mat,quat,bevel):
    # Rounded tapered outline, broader at the hip and narrow at the knee.
    n=48; vs=[]
    for x in [-depth/2,depth/2]:
        for i in range(n):
            t=2*math.pi*i/n
            vs.append((x,math.sin(t)*width/2*(1+.14*math.cos(t)),math.cos(t)*length/2))
    fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    fs.extend([(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
    o=mesh_obj(name,vs,fs,mat,min(bevel,depth*.4))
    o.location=loc; o.rotation_mode='QUATERNION'; o.rotation_quaternion=quat
    return o

def rod(name,a,b,r,mat):
    a,b=Vector(a),Vector(b)
    return cyl(name,(a+b)/2,r,(b-a).length,mat,(b-a).normalized(),.003,32)

def tube(name,points,r,mat):
    pts=[Vector(p) for p in points]; centers=[]
    # Catmull-Rom interpolated centreline; capped mesh with welded topology.
    for j in range(len(pts)-1):
        p0=pts[max(j-1,0)]; p1=pts[j]; p2=pts[j+1]; p3=pts[min(j+2,len(pts)-1)]
        for i in range(8):
            t=i/8
            centers.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
    centers.append(pts[-1]); vs=[]; fs=[]; n=10
    for j,p in enumerate(centers):
        tangent=(centers[min(j+1,len(centers)-1)]-centers[max(j-1,0)]).normalized()
        hint=Vector((0,0,1)) if abs(tangent.z)<.92 else Vector((0,1,0))
        u=tangent.cross(hint).normalized(); v=tangent.cross(u).normalized()
        for k in range(n):
            t=2*math.pi*k/n; vs.append(tuple(p+r*(math.cos(t)*u+math.sin(t)*v)))
    for j in range(len(centers)-1):
        fs.extend([(j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k) for k in range(n)])
    fs.append(tuple(range(n-1,-1,-1))); fs.append(tuple(range((len(centers)-1)*n,len(centers)*n)))
    return mesh_obj(name,vs,fs,mat)

def bolt(name,loc,axis=(0,0,1),r=.012,mat=STEEL):
    cyl(name+' captive head',loc,r,.006,mat,axis,.0015,12)
    # A small real recessed-looking hex socket overlays the head face.
    p=Vector(loc)+Vector(axis)*.0032
    cyl(name+' hex drive',p,r*.40,.0012,DARK,axis,0,6)

# Rounded continuous shell, gasketed deck and dark sculpted underbody.
hull('Chassis graphite underbelly',[(.615,1.02,1.46,.23),(.64,1.13,1.58,.25),(.73,1.27,1.78,.29),(.88,1.32,1.86,.31)],GRAPHITE)
hull('Ivory rounded main shell',[(.77,1.23,1.77,.27),(.81,1.32,1.88,.28),(.94,1.38,1.94,.31),(1.04,1.36,1.92,.31),(1.105,1.22,1.81,.29)],IVORY)
hull('Deck perimeter gasket',[(1.102,1.225,1.815,.29),(1.118,1.215,1.805,.29)],DARK)
hull('Sage sloped upper deck',[(1.113,1.215,1.805,.29),(1.155,1.13,1.73,.28),(1.166,1.07,1.67,.27)],SAGELIGHT)

# Front service grille: shadow cavity sits inside a proud rounded frame.
box('Front grille graphite bezel',(0,-.962,.94),(.39,.035,.145),GRAPHITE,.03)
box('Front grille black recess',(0,-.983,.94),(.326,.012,.104),DARK,.019)
for z in [.904,.927,.950,.973]: box('Front grille horizontal louvre',(0,-.992,z),(.301,.018,.008),STEEL,.003)
for x in [-.101,0,.101]: box('Front grille vertical support',(x,-.989,.938),(.007,.01,.088),GRAPHITE,.002)
for x in [-.47,.47]:
    box('Front vertical service inset',(x,-.910,.948),(.034,.032,.105),GRAPHITE,.012)
    box('Front inset inner key',(x,-.929,.95),(.012,.005,.064),RUBBER,.003)
    bolt('Front shell fastener',(x*.78,-.936,1.045),(0,-1,0),.009)
    bolt('Front lower fastener',(x*.77,-.920,.827),(0,-1,0),.009)
box('Lower forward belly access',(0,-.769,.695),(.48,.04,.115),RUBBER,.028)
for i in range(4): box('Belly cooling louvre',(0,-.792,.665+i*.018),(.32-i*.02,.012,.006),GRAPHITE,.002)

# Service doors on both sides; the four hips leave the central door clear.
for side in [-1,1]:
    q=Vector((0,0,1)).rotation_difference(Vector((side,0,0)))
    box('Side service door gasket '+str(side),(side*.686,.02,.939),(.027,.63,.277),DARK,.04)
    box('Sage side service door '+str(side),(side*.705,.02,.939),(.035,.598,.251),SAGE,.039)
    box('Door latch inset '+str(side),(side*.729,-.205,.94),(.018,.043,.17),GRAPHITE,.014)
    box('Amber service latch '+str(side),(side*.744,-.207,.941),(.019,.027,.10),ORANGE,.009)
    for zz in [.905,.975]: cyl('Latch hinge '+str(side),(side*.75,-.207,zz),.011,.033,ORANGE,(0,0,1),.003,24)
    box('Side ventilation bezel '+str(side),(side*.728,.197,.987),(.016,.125,.079),GRAPHITE,.012)
    box('Side ventilation cavity '+str(side),(side*.738,.197,.987),(.012,.102,.056),DARK,.008)
    for z in [.97,.987,1.004]: box('Side vent louvre '+str(side),(side*.746,.197,z),(.014,.097,.005),STEEL,.0015)
    box('Door bottom groove '+str(side),(side*.727,.045,.848),(.003,.27,.008),GRAPHITE,.002)
    for yy in [-.22,.26]:
        for zz in [.846,1.031]: bolt('Door captive screw '+str(side),(side*.724,yy,zz),(side,0,0),.007)
    box('Side diagnostic connector '+str(side),(side*.681,-.367,.923),(.035,.082,.13),GRAPHITE,.025)
    box('Diagnostic dust cap '+str(side),(side*.703,-.368,.923),(.018,.058,.095),RUBBER,.016)

# Rear removable battery/power pack, built as a complete mounted volume.
box('Rear power pack graphite cradle',(0,.667,1.174),(.75,.425,.095),GRAPHITE,.032)
box('Rear power pack sage casing',(0,.682,1.278),(.675,.395,.245),SAGE,.065)
box('Power pack top lid',(0,.676,1.405),(.531,.294,.021),SAGELIGHT,.008)
box('Power pack rear rim',(0,.883,1.266),(.59,.025,.185),GRAPHITE,.028)
box('Power pack rear service cover',(0,.901,1.258),(.405,.019,.132),SAGE,.022)
box('Power pack amber release',(0,.919,1.322),(.165,.021,.027),ORANGE,.009)
for s in [-1,1]:
    box('Battery vent housing '+str(s),(s*.249,.903,1.28),(.065,.019,.132),DARK,.007)
    for x in [-.019,0,.019]: box('Battery vent bar '+str(s),(s*.249+x,.916,1.282),(.006,.013,.105),GRAPHITE,.002)
    box('Battery foot '+str(s),(s*.26,.66,1.164),(.08,.26,.062),GRAPHITE,.012)
    bolt('Battery rear screw '+str(s),(s*.159,.912,1.211),(0,1,0),.008)
    box('Battery side black vent '+str(s),(s*.339,.685,1.28),(.017,.19,.10),DARK,.013)
    for yy in [.625,.655,.685,.715,.745]: box('Battery side vent fins '+str(s),(s*.351,yy,1.28),(.014,.01,.085),GRAPHITE,.002)
# Lift handle attached at both ends.
for x in [-.12,.12]: box('Battery carry handle stanchion',(x,.687,1.432),(.06,.075,.05),GRAPHITE,.014)
box('Battery carry handle grip',(0,.687,1.456),(.25,.071,.036),GRAPHITE,.015)

# Four unambiguous articulated legs, rotary hip -> arm -> knee -> lower linkage -> ankle -> pad.
for side in [-1,1]:
    for fore in [-1,1]:
        tag=('L' if side<0 else 'R')+('_Front' if fore<0 else '_Rear')
        H=Vector((side*.638,fore*.603,.885))
        K=Vector((side*.824,fore*.804,.505))
        A=Vector((side*.891,fore*.976,.211))
        F=(side*.891,fore*.976,0)
        # Lateral rotary hip with machined concentric races and orange cable.
        cyl(tag+' hip structural hub',(side*.681,H.y,H.z),.183,.171,GRAPHITE,(side,0,0),.009,64)
        cyl(tag+' hip ivory bearing flange',(side*.738,H.y,H.z),.170,.028,IVORY,(side,0,0),.006,64)
        ring(tag+' hip elastomer seal',(side*.758,H.y,H.z),.145,.016,RUBBER,(side,0,0))
        cyl(tag+' hip rotating drum',(side*.782,H.y,H.z),.135,.077,GRAPHITE,(side,0,0),.008,56)
        ring(tag+' hip outer metal race',(side*.82,H.y,H.z),.116,.008,STEEL,(side,0,0),48)
        cyl(tag+' hip axle',(side*.839,H.y,H.z),.079,.052,STEEL,(side,0,0),.006,40)
        # Broad upper shell inclined along the load path, with separate sage outer armor.
        upper_top=Vector((side*.853,fore*.631,.935))
        upper_bot=Vector((side*.856,fore*.801,.526))
        beam(tag+' upper structural link',H,K,.132,.156,GRAPHITE,.035)
        d=upper_top-upper_bot; q=Vector((0,0,1)).rotation_difference(d)
        midpoint=(upper_top+upper_bot)/2
        egg_panel(tag+' ivory upper leg armor',midpoint,.122,.272,d.length+.105,IVORY,q,.026)
        egg_panel(tag+' sage upper leg access panel',midpoint+Vector((side*.063,0,.013)),.026,.223,d.length+.012,SAGE,q,.009)
        for t in [.12,.86]:
            p=upper_bot+d*t+Vector((side*.076,0,0))
            bolt(tag+' upper armor fastener',p,(side,0,0),.0085)
        # Large rotary knee: link and cover intersect its axle, never float.
        cyl(tag+' knee graphite bearing',K,.125,.194,GRAPHITE,(side,0,0),.007,56)
        cyl(tag+' knee ivory cover',K+Vector((side*.106,0,0)),.106,.029,IVORY,(side,0,0),.008,56)
        ring(tag+' knee retaining band',K+Vector((side*.124,0,0)),.092,.005,STEEL,(side,0,0),48)
        # Paired lower links and an exposed central hydraulic piston.
        for offset in [-.061,.061]:
            pa=K+Vector((offset,fore*.021,-.024)); pb=A+Vector((offset,-fore*.017,.015))
            beam(tag+' lower parallel link '+str(offset),pa,pb,.033,.071,GRAPHITE,.011)
        mid=A.lerp(K,.61)
        rod(tag+' exposed actuator rod',A+Vector((0,0,.022)),K+Vector((0,0,-.02)),.022,STEEL)
        rod(tag+' hydraulic barrel',mid,K+Vector((0,0,-.018)),.033,GRAPHITE)
        ring(tag+' actuator barrel seal',mid,.031,.005,RUBBER,(K-A).normalized(),32)
        # Separate ankle pin and socket firmly mounted to the sole assembly.
        cyl(tag+' ankle rotary pin',A,.060,.181,GRAPHITE,(1,0,0),.005,40)
        cyl(tag+' ankle outer cap',A+Vector((side*.101,0,0)),.040,.019,STEEL,(side,0,0),.004,32)
        for offs in [-.073,.073]:
            box(tag+' foot yoke cheek '+str(offs),(A.x+offs,A.y,.16),(.034,.133,.10),GRAPHITE,.012)
        # Revolved round foot, real rounded shoulders and separate grippy sole.
        lathe(tag+' circular rubber footpad',[(0,0),(.194,0),(.212,.006),(.219,.019),(.219,.057),(.213,.072),(.195,.079),(0,.079)],RUBBER,F)
        lathe(tag+' ivory foot rim',[(0,.07),(.210,.07),(.214,.079),(.209,.094),(.196,.105),(0,.105)],IVORY,F)
        lathe(tag+' graphite ankle plinth',[(0,.10),(.192,.10),(.183,.119),(.131,.148),(.112,.168),(0,.168)],GRAPHITE,F)
        for j in range(16):
            t=2*math.pi*j/16
            o=box(tag+' sole tread cleat %02d'%j,(F[0]+.211*math.cos(t),F[1]+.211*math.sin(t),.036),(.026,.030,.042),RUBBER,.005)
            o.rotation_euler.z=t
        for j in range(4):
            t=math.pi*.25+j*math.pi*.5
            bolt(tag+' foot rim screw',(F[0]+.168*math.cos(t),F[1]+.168*math.sin(t),.119),(0,0,1),.007)
        # Flexible sealed cable returns from chassis to hip and down to the actuator.
        tube(tag+' hip orange power cable',[(side*.621,fore*.48,.82),(side*.745,fore*.48,.72),(side*.824,fore*.55,.738),(side*.843,fore*.61,.855),(side*.776,fore*.676,.98)],.013,ORANGE)
        tube(tag+' black hip loom',[(side*.62,fore*.69,1.012),(side*.73,fore*.72,1.015),(side*.815,fore*.736,.953),(side*.805,fore*.66,.80)],.019,RUBBER)
        tube(tag+' knee sensor cable',[(side*.76,fore*.75,.70),(side*.74,fore*.83,.59),(side*.75,fore*.90,.36),(side*.82,fore*.94,.25)],.011,RUBBER)
        for yy,zz in [(fore*.48,.82),(fore*.69,1.012)]:
            cyl(tag+' cable gland',(side*.63,yy,zz),.029,.045,GRAPHITE,(side,0,0),.005,24)

# Clean deck tie-downs, flush fasteners and power conduits.
for x in [-.43,.43]:
    for y in [-.53,.43]:
        box('Deck tie-down foot',(x,y,1.168),(.125,.07,.023),GRAPHITE,.009)
        for xx in [-.042,.042]: box('Deck tie-down riser',(x+xx,y,1.184),(.022,.049,.028),GRAPHITE,.007)
        box('Deck tie-down bridge',(x,y,1.197),(.098,.044,.018),GRAPHITE,.007)
for x in [-.37,.37]:
    for y in [-.69,-.40,.12,.48]: bolt('Deck captive screw',(x,y,1.166),(0,0,1),.008)
for s in [-1,1]:
    tube('Ivory deck power conduit '+str(s),[(s*.28,.49,1.20),(s*.28,.41,1.232),(s*.33,.14,1.231),(s*.28,.045,1.202)],.018,IVORY)
    for y in [.17,.39]: box('Conduit graphite clip '+str(s),(s*.32,y,1.224),(.057,.028,.043),GRAPHITE,.007)
    for y in [.045,.49]: cyl('Conduit sealed deck gland '+str(s),(s*.28,y,1.184),.029,.054,GRAPHITE,bevel=.006,verts=32)
for x in [-.31,.31]: cyl('Rear deck short connector',(x,.34,1.211),.022,.092,GRAPHITE,(0,0,1),.005,24)

# Low, rotating 360-degree lidar housing.
Y=-.205
cyl('Lidar pedestal sealed base',(0,Y,1.184),.247,.045,GRAPHITE,bevel=.009,verts=80)
cyl('Lidar ivory lower bearing ring',(0,Y,1.220),.289,.036,IVORY,bevel=.008,verts=96)
cyl('Lidar smoked continuous scanner window',(0,Y,1.270),.277,.079,LIDAR,bevel=.005,verts=96)
cyl('Lidar ivory overhanging cap',(0,Y,1.320),.292,.035,IVORY,bevel=.009,verts=96)
for j in range(20):
    t=2*math.pi*j/20
    # Narrow real mullions, aligned to band radius; scanner remains a dark continuous band.
    o=box('Lidar slim window divider %02d'%j,(.278*math.cos(t),Y+.278*math.sin(t),1.27),(.008,.005,.062),GRAPHITE,.0015)
    o.rotation_euler.z=t+math.pi/2
for x in [-.15,.15]: bolt('Lidar top retaining screw',(x,Y-.19,1.339),(0,0,1),.007)
for angle in [-22,22]:
    t=math.radians(angle); axis=(math.cos(t),math.sin(t),0)
    cyl('Lidar side calibration port',(.279*axis[0],Y+.279*axis[1],1.274),.024,.014,GRAPHITE,axis,.003,32)
    cyl('Lidar side calibration center',(.287*axis[0],Y+.287*axis[1],1.274),.013,.008,DARK,axis,.001,24)
cyl('Telescope yaw joint',(0,Y,1.358),.124,.054,GRAPHITE,bevel=.007,verts=64)
ring('Telescope yaw silver bearing',(0,Y,1.378),.106,.006,STEEL)

# The U fork is one continuous solid extruded profile with two physical side bearings.
head_start=set(asset.objects)
outline=[(-.226,1.661),(-.226,1.414),(-.205,1.379),(-.174,1.366),(.174,1.366),(.205,1.379),(.226,1.414),(.226,1.661),(.212,1.698),(.174,1.708),(.146,1.68),(.146,1.451),(.127,1.431),(-.127,1.431),(-.146,1.451),(-.146,1.68),(-.174,1.708),(-.212,1.698)]
vs=[(x,Y+dy,z) for dy in [-.073,.073] for x,z in outline]; n=len(outline)
fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
fs.extend([(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
mesh_obj('Continuous sage two-sided gimbal fork',vs,fs,SAGE,.014)
for s in [-1,1]:
    box('Gimbal ivory outer cheek '+str(s),(s*.232,Y,1.548),(.031,.143,.278),IVORY,.012)
    box('Gimbal sage inset service plate '+str(s),(s*.250,Y,1.535),(.010,.111,.217),SAGE,.003)
    cyl('Gimbal transverse pitch axle '+str(s),(s*.151,Y,1.625),.068,.069,GRAPHITE,(s,0,0),.004,40)
    cyl('Gimbal amber pivot cap '+str(s),(s*.257,Y,1.625),.035,.017,ORANGE,(s,0,0),.004,40)
    ring('Gimbal pivot retaining ring '+str(s),(s*.268,Y,1.625),.036,.003,STEEL,(s,0,0),32)
    bolt('Gimbal lower cover fastener '+str(s),(s*.257,Y,1.448),(s,0,0),.007)

# Single optical telescope: barrel along -Y, blank rear cap, deep single lens aperture.
cyl('Telescope ivory optical barrel',(0,Y-.015,1.625),.139,.281,IVORY,(0,1,0),.011,80)
cyl('Telescope rear graphite retaining ring',(0,Y+.125,1.625),.130,.044,GRAPHITE,(0,1,0),.006,64)
cyl('Telescope rear solid sage cap',(0,Y+.153,1.625),.116,.022,SAGE,(0,1,0),.007,64)
lathe('Telescope open front baffle',[(.104,-.038),(.144,-.038),(.152,-.027),(.154,.006),(.147,.020),(.115,.025),(.104,.012),(.104,-.038)],GRAPHITE,(0,Y-.167,1.625),(0,-1,0),80)
ring('Lens hood silver outer bevel',(0,Y-.189,1.625),.148,.0045,STEEL,(0,1,0),80)
cyl('Lens aperture black backing',(0,Y-.180,1.625),.107,.018,DARK,(0,1,0),.002,64)
sphere('Single convex optical lens',(0,Y-.198,1.625),(.095,.015,.095),GLASS)
ring('Optical lens inner retaining ring',(0,Y-.210,1.625),.099,.004,GRAPHITE,(0,1,0),64)
ring('Optical lens coating rim',(0,Y-.207,1.625),.086,.002,BLUE,(0,1,0),64)
box('Optical barrel top service pad',(0,Y+.015,1.766),(.12,.12,.022),IVORY,.008)
for x in [-.037,.037]: bolt('Optical barrel top screw',(x,Y+.019,1.779),(0,0,1),.006)
# Slight purposeful yaw towards the front-right; head remains mechanically supported.
pivot=Vector((0,Y,0)); rz=Matrix.Rotation(math.radians(12),4,'Z')
for o in set(asset.objects)-head_start:
    o.matrix_world=Matrix.Translation(pivot)@rz@Matrix.Translation(-pivot)@o.matrix_world

# Bake solid production meshes, consistent normals and explicit nondegenerate UV islands.
print('MODELING_DONE',len(asset.objects),flush=True)
bpy.ops.object.select_all(action='DESELECT')
for idx,o in enumerate(list(asset.objects)):
    bpy.context.view_layer.objects.active=o; o.select_set(True)
    for mod in list(o.modifiers):
        try: bpy.ops.object.modifier_apply(modifier=mod.name)
        except Exception as ex: print('MODIFIER_WARNING',o.name,str(ex),flush=True)
    bm=bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=0.0000005)
    bmesh.ops.dissolve_degenerate(bm,edges=bm.edges,dist=0.0000001)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bmesh.ops.triangulate(bm,faces=bm.faces,quad_method='BEAUTY',ngon_method='BEAUTY')
    bm.to_mesh(o.data); bm.free(); o.data.update()
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.02,area_weight=0,correct_aspect=True,scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    o.data.uv_layers.active.name='Component_UV'
    o.select_set(False)
    if idx%80==0: print('BAKED_UV',idx,flush=True)

# Keep floor, lights and cameras completely outside ASSET and all exports.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.004))
o=bpy.context.object; o.name='STUDIO warm gray floor'; move_to(o,studio); o.data.materials.append(FLOOR)
world=bpy.data.worlds.new('Warm gray studio world') if not scene.world else scene.world
scene.world=world; world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.57,.60,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.32
def light(name,loc,power,size,color,target=(0,0,.7)):
    data=bpy.data.lights.new(name,'AREA'); data.energy=power; data.shape='DISK'; data.size=size; data.color=color
    o=bpy.data.objects.new(name,data); studio.objects.link(o); o.location=loc; o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
light('STUDIO large key',(3.7,-4.1,6.3),550,4.2,(1,.91,.79))
light('STUDIO broad fill',(-4.0,-1.0,3.7),360,4.0,(.81,.89,1))
light('STUDIO rear rim',(1.0,4.6,4.9),650,3.6,(1,.94,.84))
data=bpy.data.cameras.new('STUDIO orthographic camera'); cam=bpy.data.objects.new('STUDIO orthographic camera',data); studio.objects.link(cam)
scene.camera=cam; cam.data.type='ORTHO'; cam.data.ortho_scale=3.45; cam.data.lens=50
scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=32; scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED'; scene.render.threads=4
scene.render.resolution_x=1440; scene.render.resolution_y=1080; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGB'; scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'; scene.view_settings.look='AgX - Medium High Contrast'; scene.view_settings.exposure=.25
scene.render.image_settings.color_depth='8'
views=[('hero',(3.7,-5.3,2.15),(0,0,.80),3.65),('rear',(-3.9,5.3,2.15),(0,0,.80),3.65)]

# Exports only the named asset collection; meshes are already triangulated and modifiers baked.
bpy.ops.object.select_all(action='DESELECT')
for o in asset.objects: o.select_set(True)
bpy.context.view_layer.objects.active=next(iter(asset.objects))
export_t0=time.time()
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,SLUG+'.glb'),export_format='GLB',use_selection=True,export_apply=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_cameras=False,export_lights=False)
bpy.ops.export_scene.fbx(filepath=os.path.join(ROOT,SLUG+'.fbx'),use_selection=True,object_types={'MESH'},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,use_space_transform=True,path_mode='AUTO')
print('EXPORTS_DONE',round(time.time()-export_t0,3),flush=True)
manifest={'asset':SLUG,'reference':'REF/Set02/quadruped_surveyor.png','render_engine':'Cycles','device':'CPU','threads':4,'samples':32,'denoising':True,'resolution':[1440,1080],'color_management':{'view_transform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure},'background':'Warm pale gray floor and world; three broad area lights','views':[]}
for name,pos,target,scale in views:
    cam.location=pos; cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.ortho_scale=scale
    path=os.path.join(ROOT,'renders',name+'.png'); scene.render.filepath=path
    t0=time.time(); utc0=datetime.now(timezone.utc).isoformat()
    bpy.ops.render.render(write_still=True)
    manifest['views'].append({'name':name,'path':'renders/'+name+'.png','camera_location_m':pos,'target_m':target,'orthographic_scale_m':scale,'started_at_utc':utc0,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':round(time.time()-t0,3),'sha256':hashlib.sha256(open(path,'rb').read()).hexdigest()})
    print('RENDER_DONE',name,flush=True)
# Save a welcoming hero view in the native file.
name,pos,target,scale=views[0]
cam.location=pos; cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.ortho_scale=scale
scene.render.filepath=os.path.join(ROOT,'renders','hero.png')
bpy.ops.object.select_all(action='DESELECT')
for o in asset.objects: o.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects.get('Ivory rounded main shell')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,SLUG+'.blend'))
with open(os.path.join(ROOT,'capture_manifest.json'),'w',encoding='utf8') as f: json.dump(manifest,f,indent=2)
with open(os.path.join(ROOT,'build_run.json'),'w',encoding='utf8') as f: json.dump({'started_at_utc':STARTED,'build_finished_at_utc':datetime.now(timezone.utc).isoformat(),'build_script_elapsed_seconds':round(time.time()-BUILD_T0,3),'asset_mesh_objects':len(asset.objects)},f,indent=2)
print('BUILD_COMPLETE',round(time.time()-BUILD_T0,3),flush=True)
