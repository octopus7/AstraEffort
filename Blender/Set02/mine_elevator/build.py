import bpy, bmesh, math, json, os, time, hashlib
from mathutils import Vector
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
STARTED = '2026-10-23T12:15:19.695345+00:00'
RUN_START = time.time()
os.makedirs(os.path.join(ROOT, 'renders'), exist_ok=True)
def utc(): return datetime.now(timezone.utc).isoformat()

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
asset = bpy.data.collections.get('Collection'); asset.name = 'ASSET'
studio = bpy.data.collections.new('STUDIO'); bpy.context.scene.collection.children.link(studio)
scene = bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1.0
scene['asset_brief']='Mine elevator headhouse; metres; front -Y; Z up; static asset.'
scene['design_decision']='Paired load ropes cross the crown sheave to a visible roof winding drum; full service stair descends behind annex.'

def material(name, rgb, roughness=.5, metallic=0, emission=None):
    m=bpy.data.materials.new(name); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*rgb,1)
    p.inputs['Roughness'].default_value=roughness
    p.inputs['Metallic'].default_value=metallic
    if emission:
        p.inputs['Emission Color'].default_value=(*rgb,1)
        p.inputs['Emission Strength'].default_value=emission
    m.diffuse_color=(*rgb,1)
    return m

M={
 'ivory':material('Ivory | cast mineral housing',(.68,.65,.55),.73),
 'edge':material('Limestone | plinth edges',(.51,.50,.44),.8),
 'sage':material('Sage | enamel structure',(.27,.35,.30),.43,.32),
 'sage_dark':material('Deep sage | frames',(.16,.23,.20),.5,.38),
 'sage_light':material('Pale sage | collars',(.40,.46,.38),.49,.3),
 'graphite':material('Graphite | steel',(.075,.085,.078),.4,.65),
 'steel':material('Warm galvanized steel',(.42,.44,.40),.35,.72),
 'rope':material('Woven steel rope',(.105,.115,.105),.42,.8),
 'orange':material('Ochre orange | operational accents',(.77,.28,.065),.42,.3),
 'rubber':material('Rubber | seals and rollers',(.045,.055,.049),.75),
 'screen':material('Control display glass',(.075,.18,.17),.2,.15),
 'light':material('Warm task lighting',(.98,.80,.44),.3,.08,2.5),
 'mark':material('Ivory | instrument markings',(.79,.78,.65),.55),
}

def move_collection(o, coll=asset):
    for c in list(o.users_collection): c.objects.unlink(o)
    coll.objects.link(o)

def activate(o):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.context.view_layer.objects.active=o

def wind(o):
    bm=bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(o.data); bm.free(); o.data.update()

def bevel(o, amount=.03, segments=3, angle=.38):
    if amount <= 0: return
    wind(o)
    mod=o.modifiers.new('Soft manufactured edges','BEVEL')
    mod.width=amount; mod.segments=segments; mod.limit_method='ANGLE'; mod.angle_limit=angle
    activate(o); bpy.ops.object.modifier_apply(modifier=mod.name)

def finish(o,name,mat='sage',smooth=True):
    o.name=name; o.data.name=name+' mesh'; move_collection(o)
    o.data.materials.append(M[mat])
    for p in o.data.polygons: p.use_smooth=smooth
    return o

def box(name, loc, dims, mat='sage', radius=.04, segments=3, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o=bpy.context.object; o.dimensions=dims
    activate(o); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    finish(o,name,mat)
    bevel(o,min(radius,min(dims)*.39),segments)
    if rot: o.rotation_euler=rot
    mod=o.modifiers.new('Face weighted normals','WEIGHTED_NORMAL'); mod.keep_sharp=True; mod.weight=40
    activate(o); bpy.ops.object.modifier_apply(modifier=mod.name)
    return o

def cyl(name, a, b, radius, mat='sage', vertices=32, bevel_size=.012, radius2=None):
    a,b=Vector(a),Vector(b); d=b-a
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius, radius2=radius if radius2 is None else radius2, depth=d.length, location=(a+b)/2)
    o=bpy.context.object; o.rotation_mode='QUATERNION'; o.rotation_quaternion=d.to_track_quat('Z','Y')
    activate(o); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    finish(o,name,mat)
    bevel(o,min(bevel_size,radius*.35,d.length*.35),3)
    mod=o.modifiers.new('Cylinder weighted normals','WEIGHTED_NORMAL'); mod.keep_sharp=True
    activate(o); bpy.ops.object.modifier_apply(modifier=mod.name)
    return o

def beam(name,a,b,width,depth,mat='sage',radius=.025):
    a,b=Vector(a),Vector(b)
    o=box(name,(a+b)/2,(width,depth,(b-a).length),mat,radius)
    o.rotation_mode='QUATERNION'; o.rotation_quaternion=(b-a).to_track_quat('Z','Y')
    return o

def mesh_obj(name, verts, faces, mat='sage', rounding=0, smooth=True):
    me=bpy.data.meshes.new(name+' mesh'); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); asset.objects.link(o); me.materials.append(M[mat]); wind(o)
    for p in me.polygons:p.use_smooth=smooth
    if rounding: bevel(o,rounding,3)
    return o

def tube(name, points, radius=.025, mat='sage', sides=10):
    points=[Vector(p) for p in points]
    points=[p for i,p in enumerate(points) if i==0 or (p-points[i-1]).length>1e-7]
    vv=[]; ff=[]; prev=None
    for j,p in enumerate(points):
        t=(points[min(j+1,len(points)-1)]-points[max(j-1,0)]).normalized()
        if prev is None:
            ref=Vector((0,1,0)) if abs(t.y)<.9 else Vector((1,0,0))
            u=(ref-t*ref.dot(t)).normalized()
        else: u=(prev-t*prev.dot(t)).normalized()
        v=t.cross(u).normalized();prev=u
        for k in range(sides):
            q=p+radius*(u*math.cos(k*2*math.pi/sides)+v*math.sin(k*2*math.pi/sides));vv.append(tuple(q))
    for j in range(len(points)-1):
        for k in range(sides):
            a=j*sides+k;b=j*sides+(k+1)%sides;c=(j+1)*sides+(k+1)%sides;d=(j+1)*sides+k
            ff.append((a,b,c,d))
    for j in (0,len(points)-1):
        ci=len(vv);vv.append(tuple(points[j]))
        for k in range(sides):ff.append((ci,j*sides+k,j*sides+(k+1)%sides))
    return mesh_obj(name,vv,ff,mat,smooth=True)

def rounded_path(points, r=.12, steps=6):
    p=[Vector(x) for x in points]; out=[p[0]]
    for i in range(1,len(p)-1):
        a=(p[i-1]-p[i]);b=(p[i+1]-p[i]);d=min(r,a.length*.4,b.length*.4)
        q=p[i]+a.normalized()*d; s=p[i]+b.normalized()*d
        out.append(q)
        for j in range(1,steps+1):
            t=j/steps;out.append((1-t)**2*q+2*(1-t)*t*p[i]+t*t*s)
    out.append(p[-1]);return out

def ring(name, center, profile, mat='steel', segments=80):
    # Closed radial cross-section revolved about Y, with no pole or duplicated seam vertices.
    x,y,z=center;vv=[];ff=[]
    for dy,r in profile:
        for i in range(segments):
            a=2*math.pi*i/segments;vv.append((x+r*math.cos(a),y+dy,z+r*math.sin(a)))
    for j in range(len(profile)):
        for i in range(segments):ff.append((j*segments+i,j*segments+(i+1)%segments,((j+1)%len(profile))*segments+(i+1)%segments,((j+1)%len(profile))*segments+i))
    return mesh_obj(name,vv,ff,mat,smooth=True)

def bolt(name,loc,axis='Y',r=.035,mat='steel'):
    v=Vector((0,-.025,0)) if axis=='Y' else Vector((.025,0,0)) if axis=='X' else Vector((0,0,.025))
    return cyl(name,Vector(loc)-v,Vector(loc)+v,r,mat,6,.003)

def arch_housing():
    p=[(-1.72,.22),(-1.72,2.77)]
    for i in range(1,13):
        a=math.pi-i*math.pi/24;p.append((-1.44+.28*math.cos(a),2.77+.28*math.sin(a)))
    p.append((1.44,3.05))
    for i in range(1,13):
        a=math.pi/2-i*math.pi/24;p.append((1.44+.28*math.cos(a),2.77+.28*math.sin(a)))
    p.extend([(1.72,.22),(1.05,.22),(1.05,2.46)])
    for i in range(1,10):
        a=i*math.pi/18;p.append((.87+.18*math.cos(a),2.46+.18*math.sin(a)))
    p.append((-.87,2.64))
    for i in range(1,10):
        a=math.pi/2+i*math.pi/18;p.append((-.87+.18*math.cos(a),2.46+.18*math.sin(a)))
    p.append((-1.05,.22))
    n=len(p);vv=[(x,y,z) for y in (-1.45,1.30) for x,z in p]
    ff=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    ff += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o=mesh_obj('01 Housing | rounded open portal',vv,ff,'ivory',.045,True)
    mod=o.modifiers.new('Mineral weighted normals','WEIGHTED_NORMAL');mod.keep_sharp=True;activate(o);bpy.ops.object.modifier_apply(modifier=mod.name)

def canopy(name,span,depth,zbase,thickness,mat):
    vv=[];ff=[];N=40;r=.31
    for i in range(N+1):
        x=-span/2+span*i/N
        q=max(0,abs(x)-(span/2-r)); y=depth/2-r+math.sqrt(max(0,r*r-q*q))
        h=zbase+.25*(1-(x/(span/2))**2)
        vv.extend([(x,-y,h),(x,y,h),(x,-y,h+thickness),(x,y,h+thickness)])
    for i in range(N):
        a=i*4;b=(i+1)*4
        ff.extend([(a,b,b+1,a+1),(a+2,a+3,b+3,b+2),(a,a+2,b+2,b),(a+1,b+1,b+3,a+3)])
    ff.extend([(0,1,3,2),(N*4,N*4+2,N*4+3,N*4+1)])
    o=mesh_obj(name,vv,ff,mat,min(.06,thickness*.3),True)
    mod=o.modifiers.new('Canopy weighted normals','WEIGHTED_NORMAL');mod.keep_sharp=True;activate(o);bpy.ops.object.modifier_apply(modifier=mod.name)
    return o

# Foundation and an actual U-shaped portal rather than a dark painted door.
box('01 Main mineral footing',(0,-.02,.11),(3.80,3.16,.22),'edge',.07)
box('01 Annex mineral footing',(2.42,-.88,.11),(1.72,1.96,.22),'edge',.07)
arch_housing()
box('01 Shaft rear wall',(0,1.15,1.40),(2.12,.20,2.37),'edge',.04)
for x in (-.65,0,.65):
    box('01 Rear shaft liner panel',(x,1.025,1.42),(.60,.035,2.24),'ivory',.01)
for side in (-1,1):
    box('01 Interior jamb seal', (side*1.032,-1.465,1.40),(.065,.07,2.32),'sage_dark',.025)
    box('01 Corner impact pedestal',(side*1.49,-1.28,.53),(.58,.57,.67),'sage_light',.085)
    box('01 Corner pedestal shoe',(side*1.49,-1.28,.22),(.69,.69,.17),'ivory',.045)
    for z in (.42,.72): bolt('01 Pedestal hex fixing',(side*1.49,-1.58,z),r=.024)
    # Recessed vertical task lamp, inset in each jamb.
    box('01 Portal lamp bezel',(side*.985,-1.474,1.91),(.095,.10,.40),'sage_dark',.036)
    box('01 Portal warm lamp',(side*.985,-1.535,1.91),(.043,.025,.30),'light',.015)
box('01 Threshold tread',(0,-1.39,.255),(2.00,.40,.07),'steel',.015)
for i in range(16):
    box('01 Threshold anti-slip rib',(-.90+i*.12,-1.40,.296),(.025,.33,.012),'graphite',.004)

# Perimeter deck; the central aperture remains open for cage suspension and ropes.
for name,loc,dims in [
 ('front',(0,-1.20,3.14),(3.72,.58,.18)),
 ('rear',(0,1.09,3.14),(3.72,.77,.18)),
 ('left',(-1.50,-.10,3.14),(.72,1.62,.18)),
 ('right',(1.50,-.10,3.14),(.72,1.62,.18))]:
    box('02 Service deck | '+name,loc,dims,'sage_dark',.035)
for i in range(25):
    box('02 Front deck traction strip',(-1.68+i*.14,-1.21,3.236),(.022,.38,.012),'steel',.004,rot=(0,0,.32))
for x in (-1.50,1.50):
    for i in range(10):box('02 Side deck traction strip',(x,-.73+i*.16,3.236),(.43,.023,.012),'steel',.004)

# Four load-bearing slightly tapered posts, collars, sockets and bracing.
for x in (-1.43,1.43):
    for y in (-1.04,1.04):
        key=('L' if x<0 else 'R')+('F' if y<0 else 'B')
        box('03 Post '+key+' base socket',(x,y,3.29),(.54,.53,.22),'sage',.045)
        cyl('03 Headframe post '+key,(x,y,3.31),(x,y,7.55),.224,'sage',40,.022,.195)
        for z in (3.45,5.12,7.39):
            cyl('03 Post '+key+' ivory collar',(x,y,z-.058),(x,y,z+.058),.238,'ivory',40,.017)
        for dx in (-.17,.17):
            bolt('03 Foot anchor bolt',(x+dx,y-.18,3.407),'Z',.026)
        # Thick cap saddles meet the roof underside.
        box('03 Post '+key+' cap saddle',(x,y,7.50),(.47,.50,.22),'sage_dark',.07)
        cyl('03 Cap pin',(x,y-.28,7.50),(x,y+.28,7.50),.064,'steel',24,.008)
for y in (-1.04,1.04):
    box('03 Main axle carrier beam',(0,y,6.13),(3.08,.34,.34),'sage',.075)
    for x in (-1.42,1.42):
        cyl('03 Carrier orange pin',(x,y-.205,6.13),(x,y-.235,6.13),.073,'orange',28,.008)
    box('03 Pedestal lower block',(0,y,6.35),(.40,.31,.29),'sage_dark',.055)
    cyl('03 Axle bearing block',(0,y-.20,6.56),(0,y+.20,6.56),.185,'sage_light',40,.028)
    for x in (-.15,.15):bolt('03 Bearing hold-down',(x,y-.17,6.33),'Z',.026)
for x in (-1.43,1.43):
    tube('03 Side compression brace',[(x,-.93,3.67),(x,.94,5.96)],.075,'sage',14)
    for y,z in [(-.93,3.67),(.94,5.96)]:
        cyl('03 Side brace eye',(x-.13,y,z),(x+.13,y,z),.106,'sage_dark',24,.015)
        bolt('03 Side brace pin',(x+.145,y,z),'X',.044)
for a,b in [((-1.31,1.10,3.58),(1.31,1.10,6.02)),((1.31,1.13,3.58),(-1.31,1.13,6.02))]:
    tube('03 Rear structural cross brace',[a,b],.068,'sage',14)
box('03 Rear brace centre clamp',(0,1.16,4.80),(.23,.15,.30),'sage_dark',.04)
bolt('03 Rear brace centre bolt',(0,1.26,4.80),r=.041)
canopy('04 Canopy | sage underside',3.70,2.99,7.49,.10,'sage_dark')
canopy('04 Canopy | softly arched ivory shell',3.88,3.19,7.57,.24,'ivory')
for x in (-1.36,1.36):
    box('04 Canopy underside cross joist',(x,0,7.55),(.16,2.65,.16),'sage_dark',.055)

# A truly grooved annular sheave, two spoke faces and a through axle.
C=(0,-.25,6.56)
outer=[(-.46,1.065),(-.42,1.065),(-.34,1.025),(-.28,1.002),(-.20,1.002),(-.14,1.025),(-.08,1.065),(.08,1.065),(.14,1.025),(.20,1.002),(.28,1.002),(.34,1.025),(.42,1.065),(.46,1.065)]
ring('05 Hoist sheave | two machined cable grooves',C,outer+[(.46,.845),(-.46,.845)],'graphite',112)
for side in (-1,1):
    y=C[1]+side*.49
    ring('05 Sheave flange '+('front' if side<0 else 'rear'),(0,y,6.56),[(-.04,1.083),(.04,1.083),(.04,.89),(-.04,.89)],'ivory',96)
    for k in range(6):
        a=2*math.pi*k/6+.15
        p=(.20*math.cos(a),y,6.56+.20*math.sin(a));q=(.95*math.cos(a),y,6.56+.95*math.sin(a))
        beam('05 Sheave '+('front' if side<0 else 'rear')+' spoke %02d'%(k+1),p,q,.145,.09,'ivory',.035)
    cyl('05 Sheave central hub',(0,y-.07,6.56),(0,y+.07,6.56),.235,'sage_light',48,.025)
cyl('05 Through axle',(0,-1.34,6.56),(0,1.34,6.56),.088,'steel',40,.01)
cyl('05 Front bearing cap',(0,-1.36,6.56),(0,-1.30,6.56),.132,'orange',40,.012)
cyl('05 Front cap central inset',(0,-1.378,6.56),(0,-1.363,6.56),.086,'steel',32,.004)
cyl('05 Rear bearing cap',(0,1.29,6.56),(0,1.36,6.56),.127,'orange',40,.012)

# Two separate guide rails with actual flanges and four guided carriage stations.
for side in (-1,1):
    x=side*.985
    box('06 Guide rail web',(x,-.57,3.20),(.045,.15,5.94),'steel',.006)
    for y in (-.67,-.47):box('06 Guide rail flange',(x,y,3.20),(.135,.04,5.94),'graphite',.008)
    for z in (.35,3.13,6.15):
        box('06 Rail wall shoe',(x,-.46,z),(.22,.38,.15),'sage_dark',.02)
        for dx in (-.075,.075):bolt('06 Rail shoe bolt',(x+dx,-.68,z),r=.021)

# Editable lift cage, near the ground landing, with a full floor and two safety gate leaves.
box('07 Cage floor tray',(0,-.28,.35),(1.87,1.68,.17),'sage_dark',.035)
box('07 Cage floor tread',(0,-.28,.444),(1.72,1.52,.025),'steel',.008)
for j in range(11):
    for k in range(2):box('07 Cage floor grip',( -.42+k*.84,-.94+j*.13,.462),(.66,.019,.012),'graphite',.004,rot=(0,0,.12 if j%2==0 else -.12))
for x in (-.865,.865):
    for y in (-1.06,.50):
        box('07 Cage corner upright',(x,y,1.47),(.075,.075,2.08),'graphite',.018)
        box('07 Cage upper corner gusset',(x,y,2.43),(.15,.15,.16),'sage_dark',.024)
    for z in (.72,1.48,2.47):box('07 Cage side tie',(x,-.28,z),(.055,1.57,.065),'steel',.015)
    for i in range(9):box('07 Cage side safety bar',(x,-.96+i*.17,1.10),(.023,.023,.69),'steel',.008)
box('07 Cage rear upper beam',(0,.50,2.47),(1.80,.07,.08),'graphite',.02)
box('07 Cage rear waist beam',(0,.50,1.48),(1.80,.055,.06),'steel',.015)
box('07 Cage rear low beam',(0,.50,.65),(1.80,.055,.06),'steel',.015)
for i in range(11):box('07 Cage rear safety bar',(-.80+i*.16,.50,1.06),(.025,.025,.78),'steel',.008)
box('07 Cage front header',(0,-1.06,2.47),(1.80,.08,.08),'graphite',.02)
for y in (-.49,-.01):
    box('07 Cage suspension spreader',(0,y,2.53),(1.92,.11,.14),'sage_dark',.024)
    box('07 Cable termination clevis',(0,y,2.652),(.15,.10,.18),'orange',.024)
    cyl('07 Cable clevis cross pin',(-.10,y,2.655),(.10,y,2.655),.027,'steel',20,.004)
for side in (-1,1):
    x=side*.436
    for xx in (x-.404,x+.404):box('08 Gate leaf vertical',(xx,-1.105,.997),(.045,.055,1.10),'steel',.012)
    for zz in (.46,1.04,1.54):box('08 Gate leaf horizontal',(x,-1.105,zz),(.847,.055,.045),'steel',.012)
    box('08 Gate leaf kick panel',(x,-1.106,.61),(.77,.026,.25),'sage_dark',.012)
    box('08 Gate orange hand bar',(x,-1.14,1.555),(.86,.042,.045),'orange',.016)
    # Diamond safety mesh clipped into each leaf aperture. Each wire is a real closed tube.
    xmin,xmax=x-.375,x+.375; zmin,zmax=.765,1.495
    for slope in (-1,1):
        for k in range(-9,10):
            c=1.13+k*.105-slope*x
            pts=[]
            for xx in (xmin,xmax):
                zz=slope*xx+c
                if zmin-1e-6<=zz<=zmax+1e-6:pts.append((xx,-1.108,zz))
            for zz in (zmin,zmax):
                xx=(zz-c)/slope
                if xmin+1e-6<xx<xmax-1e-6:pts.append((xx,-1.108,zz))
            if len(pts)==2:tube('08 Gate diamond wire',pts,.0052,'steel',6)
    for z in (.60,1.40):
        box('08 Gate orange hinge bracket',(side*.881,-1.11,z),(.115,.11,.16),'orange',.024)
        cyl('08 Gate hinge pin',(side*.89,-1.17,z-.10),(side*.89,-1.17,z+.10),.022,'steel',16,.005)
box('08 Gate centre latch',(0,-1.162,1.37),(.15,.08,.12),'orange',.024)
for x in (-.047,.047):bolt('08 Gate latch screws',(x,-1.209,1.37),r=.014)
for side in (-1,1):
    for z in (.65,2.25):
        box('07 Rail carriage bracket',(side*.92,-.58,z),(.24,.28,.23),'orange',.028)
        cyl('07 Guide roller',(side*.985,-.72,z),(side*.985,-.77,z),.072,'rubber',28,.01)
        cyl('07 Guide roller axle',(side*.985,-.785,z),(side*.985,-.768,z),.026,'steel',20,.003)

# Machinery annex: rounded body, front door, louvers and side maintenance panel.
box('09 Annex rounded housing',(2.40,-.87,1.14),(1.55,1.78,1.88),'ivory',.15,5)
box('09 Annex roof seam',(2.40,-.87,2.035),(1.57,1.80,.09),'edge',.034)
box('09 Annex rounded roof cap',(2.40,-.87,2.12),(1.59,1.82,.18),'ivory',.065,5)
box('09 Annex lower sage skirting',(2.40,-.87,.26),(1.57,1.80,.12),'sage_light',.04)
box('09 Annex door rubber gasket',(2.05,-1.782,.93),(.62,.058,1.36),'sage_dark',.065)
box('09 Annex inset service door',(2.05,-1.818,.93),(.535,.055,1.285),'sage',.048)
box('09 Annex door inset panel',(2.05,-1.852,.96),(.42,.02,1.06),'sage_dark',.032)
box('09 Annex door inner face',(2.05,-1.867,.97),(.37,.018,1.00),'sage',.026)
for z in (.48,1.36):box('09 Annex door hinge',(1.79,-1.86,z),(.06,.065,.12),'steel',.014)
box('09 Door handle backplate',(2.22,-1.87,.90),(.07,.035,.24),'sage_dark',.015)
tube('09 Orange pull handle',rounded_path([(2.22,-1.89,.82),(2.22,-1.96,.82),(2.22,-1.96,.99),(2.22,-1.89,.99)],.035),.015,'orange',10)
box('09 Door task lamp housing',(2.05,-1.81,1.77),(.38,.10,.13),'sage_dark',.045)
box('09 Door task lamp diffuser',(2.05,-1.871,1.77),(.285,.025,.065),'light',.024)
box('09 Louver dark cavity',(2.73,-1.796,1.01),(.57,.07,1.04),'graphite',.04)
for x in (2.425,3.035):box('09 Louver vertical trim',(x,-1.846,1.01),(.052,.08,1.12),'sage',.022)
for z in (.45,1.57):box('09 Louver horizontal trim',(2.73,-1.846,z),(.66,.08,.055),'sage',.022)
for j in range(12):box('09 Louver blade %02d'%(j+1),(2.73,-1.858,.52+j*.087),(.54,.095,.037),'sage_dark',.010,rot=(math.radians(22),0,0))
box('09 Outer maintenance gasket',(3.183,-.85,1.02),(.028,1.20,1.31),'sage_dark',.01)
box('09 Outer maintenance door',(3.205,-.85,1.02),(.045,1.11,1.23),'sage',.016)
for y in (-1.30,-.40):
    for z in (.51,1.53):bolt('09 Side service door fixing',(3.241,y,z),'X',.022)
box('09 Side service latch',(3.252,-.48,1.02),(.055,.055,.19),'steel',.016)
# Two bent service conduits attach to the annex and lower portal.
for dy in (0,.12):
    path=[(1.58,-1.52,.40),(1.58,-1.67,.40),(1.58,-1.67,1.98),(1.80,-1.67,2.02)]
    tube('09 Exterior rounded conduit',rounded_path([(x,y+dy,z) for x,y,z in path],.14),.036,'sage_dark',12)
    for z in (.63,1.47):box('09 Conduit saddle',(1.58,-1.68+dy,z),(.12,.09,.075),'sage',.02)
box('09 Orange isolator box',(1.57,-1.76,1.10),(.25,.15,.47),'orange',.04)
box('09 Isolator label plate',(1.57,-1.845,1.19),(.12,.015,.075),'ivory',.008)
box('09 Isolator switch',(1.57,-1.87,1.02),(.055,.04,.13),'graphite',.01)

# Visible powered winding drum and motor mounted securely on the annex roof.
D=(2.45,-.25,2.49)
for y in (-.70,.20):
    box('10 Winch mounting foot',(2.45,y,2.23),(.58,.21,.08),'sage_dark',.025)
    box('10 Winch bearing pedestal',(2.45,y,2.37),(.27,.16,.28),'sage',.04)
    cyl('10 Winch bearing',(2.45,y-.09,2.49),(2.45,y+.09,2.49),.105,'steel',32,.015)
    for x in (2.23,2.67):bolt('10 Winch foot bolt',(x,y,2.282),'Z',.026)
cyl('10 Winding drum axle',(2.45,-1.32,2.49),(2.45,.32,2.49),.055,'steel',32,.006)
cyl('10 Winding drum core',(2.45,-.62,2.49),(2.45,.12,2.49),.16,'graphite',64,.012)
for y in (-.63,-.25,.13):
    ring('10 Winding drum cheek',(2.45,y,2.49),[(-.027,.222),(.027,.222),(.027,.064),(-.027,.064)],'sage_light',64)
cyl('10 Rounded motor housing',(2.45,-1.35,2.49),(2.45,-.80,2.49),.223,'orange',48,.055)
cyl('10 Motor end cap',(2.45,-1.39,2.49),(2.45,-1.35,2.49),.185,'sage_dark',48,.014)
for i in range(5):box('10 Motor end cooling slot',(2.45,-1.419,2.39+i*.047),(.25,.015,.014),'graphite',.004)
box('10 Motor foot',(2.45,-1.08,2.23),(.49,.46,.08),'sage_dark',.024)
box('10 Motor terminal box',(2.45,-1.05,2.735),(.23,.25,.12),'sage',.028)
tube('10 Motor electrical conduit',rounded_path([(2.45,-1.05,2.77),(2.15,-1.05,2.77),(2.15,-.91,2.22)],.07),.018,'graphite',10)

# Rope paths are analytical tangents to the crown sheave and winch drum.
R=1.025;r=.184;cx,cz=0,6.56;dx,dz=2.45,2.49
A=Vector((0,2.74)); rel=A-Vector((cx,cz))
phi=math.atan2(rel.y,rel.x); alpha=math.acos(R/rel.length)
theta_a=phi-alpha
while theta_a<0:theta_a+=2*math.pi
delta=Vector((dx-cx,dz-cz));theta_d=math.atan2(delta.y,delta.x)+math.acos((R-r)/delta.length)
rope_paths=[]
for i,y in enumerate((-.49,-.01)):
    p=[(0,y,2.74)]
    for k in range(65):
        a=theta_a+(theta_d-theta_a)*k/64;p.append((cx+R*math.cos(a),y,cz+R*math.sin(a)))
    p.append((dx+r*math.cos(theta_d),y,dz+r*math.sin(theta_d)))
    for k in range(1,61):
        a=theta_d-k*(1.5*math.pi)/60;p.append((dx+r*math.cos(a),y,dz+r*math.sin(a)))
    tube('11 Continuous load rope %d | cage to sheave to winch'%(i+1),p,.018,'rope',10)
    rope_paths.append(p)
    cyl('11 Cage rope ferrule',(0,y,2.70),(0,y,2.82),.030,'steel',20,.006)
    # Small anchor clamps are attached at the drum end of each rope.
    end=Vector(p[-1]);box('11 Winch cable end clamp',end,(.07,.06,.07),'steel',.014)

# Tube rails around the service deck. The right opening leads directly to the stair.
def rail_run(name, pts, height=.85, orange=True, posts=True):
    low=[(x,y,z+.12) for x,y,z in pts];mid=[(x,y,z+.44) for x,y,z in pts];top=[(x,y,z+height) for x,y,z in pts]
    tube(name+' mid rail',rounded_path(mid,.12),.021,'sage_light',10)
    tube(name+' handrail',rounded_path(top,.12),.027,'orange' if orange else 'sage',12)
    if posts:
        for j,p in enumerate(pts):
            tube(name+' upright '+str(j),[p,(p[0],p[1],p[2]+height)],.027,'sage',10)
            box(name+' foot '+str(j),(p[0],p[1],p[2]+.028),(.12,.12,.045),'sage_dark',.012)
rail_run('12 Front platform',[(x,-1.465,3.23) for x in (-1.73,-.87,0,.87,1.73)])
rail_run('12 Rear platform',[(x,1.45,3.23) for x in (-1.73,-.86,0,.86,1.73)])
rail_run('12 Left platform',[(-1.73,y,3.23) for y in (-1.465,-.49,.48,1.45)])
rail_run('12 Right front platform',[(1.73,y,3.23) for y in (-1.465,-.50)])
rail_run('12 Right rear platform',[(1.73,y,3.23) for y in (.45,1.45)])

# Fourteen equal-rise industrial treads; continuous stringers, handrails and ground pads.
box('13 Stair upper landing',(2.25,-.08,3.14),(1.10,.58,.18),'sage_dark',.035)
rail_run('13 Landing front',[(1.78,-.37,3.23),(2.78,-.37,3.23),(2.78,.15,3.23)])
for x in (1.88,2.74):
    beam('13 Stair stringer',(x,2.79,.22),(x,.12,3.11),.115,.18,'sage',.025)
    box('13 Stair ground shoe',(x,2.73,.10),(.28,.35,.20),'ivory',.045)
    for y in (2.64,2.82):bolt('13 Stair ground anchor',(x,y,.215),'Z',.023)
for k in range(14):
    z=.20+(k+1)*(3.03/14);y=2.70-(k+.5)*(.18)
    box('13 Stair tread %02d'%(k+1),(2.31,y,z-.045),(.89,.24,.09),'steel',.021)
    box('13 Stair tread nosing %02d'%(k+1),(2.31,y+.107,z+.004),(.85,.022,.014),'graphite',.004)
    for dx in (-.25,0,.25):box('13 Stair tread grip',(2.31+dx,y,z+.008),(.15,.11,.009),'sage_dark',.003)
for x in (1.86,2.77):
    pts=[]
    for k in (0,3,6,9,13):
        z=.20+(k+1)*3.03/14;y=2.70-(k+.5)*.18
        pts.append((x,y,z))
    rail_run('13 Stair '+('inner' if x<2 else 'outer'),pts,.86)
    tube('13 Stair top return',rounded_path([(x,.27,4.09),(x,.13,4.09),(x,-.30,4.09)],.08),.027,'orange',12)

# Operational control panel on the upper deck, placed clear of the rope and access route.
box('14 Control cabinet pedestal',(1.35,-.64,3.31),(.43,.40,.16),'sage_dark',.025)
box('14 Orange control cabinet',(1.35,-.64,3.78),(.43,.37,.86),'orange',.065)
box('14 Cabinet front inset',(1.35,-.842,3.80),(.335,.035,.65),'sage_dark',.025)
box('14 Control display surround',(1.35,-.872,3.98),(.265,.025,.205),'steel',.023)
box('14 Control display',(1.35,-.890,3.98),(.215,.018,.153),'screen',.015)
for i in range(3):box('14 Display meter marking',(1.29+i*.06,-.903,3.965),(.017,.006,.05+i*.015),'mark',.002)
for x in (1.27,1.43):cyl('14 Control selector',(x,-.90,3.71),(x,-.934,3.71),.037,'steel',24,.006)
cyl('14 Emergency stop bezel',(1.35,-.901,3.56),(1.35,-.927,3.56),.054,'ivory',24,.006)
cyl('14 Emergency stop button',(1.35,-.929,3.56),(1.35,-.956,3.56),.034,'orange',24,.006)
for z in (3.50,4.07):box('14 Cabinet side hinge',(1.58,-.66,z),(.048,.10,.08),'steel',.014)
tube('14 Cabinet power feed',rounded_path([(1.34,-.59,3.31),(1.34,-.39,3.01),(1.70,-.39,2.85),(2.15,-.91,2.77)],.08),.021,'graphite',10)

# Final geometry is baked and triangulated before either export, with per-component UV islands.
print('MODEL_BUILT',len(asset.objects),flush=True)
uv_repairs=[]
for idx,o in enumerate(list(asset.objects)):
    if o.type!='MESH':continue
    activate(o)
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    wind(o)
    # Face winding is established before all bevels. Welding only removes coincident generated vertices.
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.025,area_weight=0.0,correct_aspect=True,scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    mod=o.modifiers.new('Baked export triangulation','TRIANGULATE');mod.quad_method='BEAUTY';mod.ngon_method='BEAUTY'
    bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.calc_loop_triangles()
    uv=o.data.uv_layers.active.data
    for t in o.data.loop_triangles:
        a,b,c=[uv[i].uv.copy() for i in t.loops]
        ar=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5
        if ar<1e-12:
            # A microscopic bevel triangle may collapse during float32 UV packing; give it a true local island.
            p=[o.data.vertices[i].co for i in t.vertices]
            e1=p[1]-p[0];e2=p[2]-p[0];u=e1.normalized();n=e1.cross(e2).normalized();v=n.cross(u)
            scale=max(e1.length,e2.length,1e-7)
            values=[(.01,.01),(.01+.02*e1.length/scale,.01),(.01+.02*e2.dot(u)/scale,.01+.02*e2.dot(v)/scale)]
            for li,value in zip(t.loops,values):uv[li].uv=value
            uv_repairs.append({'object':o.name,'triangle':t.index})
    o['part_category']=o.name.split(' ')[0]
    o['uv_layout']='Per-component smart-projected islands; seam-aware, no shared image atlas.'
    if idx%100==0:print('FINALIZED',idx,flush=True)

def asset_stats():
    vv=[];tris=0
    for o in asset.objects:
        if o.type=='MESH':
            o.data.calc_loop_triangles();tris+=len(o.data.loop_triangles)
            vv.extend([o.matrix_world@v.co for v in o.data.vertices])
    lo=[min(v[i] for v in vv) for i in range(3)];hi=[max(v[i] for v in vv) for i in range(3)]
    return {'mesh_objects':len(asset.objects),'triangles':tris,'bounds_min':lo,'bounds_max':hi,'dimensions':[hi[i]-lo[i] for i in range(3)]}
stats=asset_stats();print('ASSET_STATS',json.dumps(stats),flush=True)

# Asset-only files, no studio or hidden helpers.
bpy.ops.object.select_all(action='DESELECT')
for o in asset.objects:o.select_set(True)
bpy.context.view_layer.objects.active=next(iter(asset.objects))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'mine_elevator.glb'),export_format='GLB',use_selection=True,export_apply=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_cameras=False,export_lights=False)
bpy.ops.export_scene.fbx(filepath=os.path.join(ROOT,'mine_elevator.fbx'),use_selection=True,object_types={'MESH'},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',path_mode='AUTO')

# Separate soft studio, excluded by selection in the asset exports.
groundmat=material('STUDIO | warm pale gray',(.63,.61,.57),.84)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.018));floor=bpy.context.object
floor.name='STUDIO | floor';move_collection(floor,studio);floor.data.materials.append(groundmat)
scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.67,.69,.66,1)
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.5
def area(name,loc,power,size,target):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
area('STUDIO | broad key',(-6,-8,12),2000,7,(0,0,3.5))
area('STUDIO | fill',(7,-5,9),1400,6,(0,0,4))
area('STUDIO | high rim',(3,7,12),2300,6,(0,0,4))
camera_data=bpy.data.cameras.new('STUDIO | orthographic camera');camera=bpy.data.objects.new('STUDIO | orthographic camera',camera_data);studio.objects.link(camera)
camera_data.type='ORTHO';camera_data.ortho_scale=10.65;camera_data.lens=50;scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=1440;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.3;scene.view_settings.gamma=1
scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
def frame_asset(cam):
    bpy.context.view_layer.update()
    inv=cam.matrix_world.inverted()
    projected=[inv@(o.matrix_world@v.co) for o in asset.objects if o.type=='MESH' for v in o.data.vertices]
    lo=[min(p[i] for p in projected) for i in (0,1)];hi=[max(p[i] for p in projected) for i in (0,1)]
    cam.location+=cam.rotation_euler.to_quaternion()@Vector(((lo[0]+hi[0])*.5,(lo[1]+hi[1])*.5,0))
    cam.data.ortho_scale=max((hi[0]-lo[0])/.80,(hi[1]-lo[1])*(1440/1080)/.80)
    bpy.context.view_layer.update()
captures=[]
for name,loc,target in [('hero',(11,-18,11.3),(.54,.15,3.95)),('rear',(11,18,11.7),(.54,.25,3.95))]:
    camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    frame_asset(camera)
    scene.render.filepath=os.path.join(ROOT,'renders',name+'.png')
    begin=utc();t=time.time();bpy.ops.render.render(write_still=True)
    captures.append({'view':name,'path':'renders/'+name+'.png','started_at_utc':begin,'finished_at_utc':utc(),'elapsed_seconds':time.time()-t,'camera_location':list(camera.location),'initial_look_at':list(target),'projection':'orthographic','ortho_scale':camera.data.ortho_scale,'framing':'Transformed asset vertices centered at 80 percent maximum image dimension','engine':'Cycles','device':'CPU','threads':4,'samples':32,'denoising':True,'resolution':[1440,1080],'color_management':'AgX / Medium High Contrast / exposure -0.3','authenticity':'Actual Blender render of delivered model; no generated image compositing.'})
camera.location=(11,-18,11.3);camera.rotation_euler=(Vector((.54,.15,3.95))-camera.location).to_track_quat('-Z','Y').to_euler()
frame_asset(camera)
scene.render.filepath=os.path.join(ROOT,'renders','hero.png')
bpy.ops.object.select_all(action='DESELECT')
scene['mechanical_inventory']='4 headframe posts; 1 crown sheave; 12 spokes; 1 through axle; 2 continuous load ropes; 1 powered winding drum; 1 motor; 2 guide rails; 4 carriage stations; 1 cage; 2 gate leaves; 14 stair treads.'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'mine_elevator.blend'))
with open(os.path.join(ROOT,'capture_manifest.json'),'w',encoding='utf-8') as f:json.dump({'asset':'mine_elevator','captures':captures,'lighting':'Three large disk area lights with world fill; warm pale gray studio. Studio is separate and excluded from exports.'},f,indent=2)
with open(os.path.join(ROOT,'build_record.json'),'w',encoding='utf-8') as f:json.dump({'started_at_utc':STARTED,'build_started_at_utc':datetime.fromtimestamp(RUN_START,timezone.utc).isoformat(),'build_finished_at_utc':utc(),'build_elapsed_seconds':time.time()-RUN_START,'stats':stats,'uv_microtriangle_repairs':uv_repairs,'mechanical_inventory':scene['mechanical_inventory']},f,indent=2)
print('BUILD_FINISHED',utc(),flush=True)

