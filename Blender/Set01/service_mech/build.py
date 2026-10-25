"""Build the independent Set01 service mech. Blender 4.5 LTS, no external assets.

Run: blender -b --factory-startup -t 4 --python build.py
Front = negative Y; Z up; meters. All output stays beside this script.
"""
import bpy
import bmesh
import math
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from mathutils import Vector, Quaternion

ROOT = Path(__file__).resolve().parent
ROOT.mkdir(parents=True, exist_ok=True)
(ROOT / 'renders').mkdir(exist_ok=True)
T0 = time.time()
START = datetime.now(timezone.utc).isoformat()

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for coll in list(bpy.data.collections):
    if coll.name != 'Collection':
        bpy.data.collections.remove(coll)
asset = bpy.data.collections.get('Collection')
asset.name = 'ASSET'
studio = bpy.data.collections.new('STUDIO')
bpy.context.scene.collection.children.link(studio)

def material(name, color, metallic=0.0, roughness=0.4, emission=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    p = mat.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = roughness
    if emission:
        p.inputs['Emission Color'].default_value = (*color, 1)
        p.inputs['Emission Strength'].default_value = emission
    mat.diffuse_color = (*color, 1)
    return mat

IVORY = material('Ceramic ivory | powder-coated shell', (0.63, 0.59, 0.47), .10, .43)
SAGE = material('Muted sage | enamel armor', (0.14, 0.22, 0.18), .12, .43)
SAGE_DARK = material('Dark sage | inset service panels', (0.075, 0.125, 0.10), .15, .46)
GRAPHITE = material('Graphite | rotary housings', (0.029, 0.036, 0.032), .32, .42)
RUBBER = material('Rubber | hoses and traction', (0.033, 0.041, 0.039), .04, .58)
STEEL = material('Satin machined steel', (0.34, 0.365, 0.345), .8, .29)
TRIM = material('Warm aluminum | rounded trims', (0.56, 0.55, 0.475), .7, .31)
ORANGE = material('Safety ochre | service accents', (0.65, 0.19, 0.025), .10, .42)
GLASS = material('Sensor glass | smoked ceramic', (0.025, 0.038, 0.039), .38, .19)
AMBER = material('Amber | low-intensity status light', (1.0, .46, .065), .0, .23, 1.2)
FLOOR = material('Studio warm porcelain', (.64, .61, .55), .0, .7)

def move_to(obj, collection):
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    collection.objects.link(obj)

def finish(obj, name, mat, smooth=True, collection=asset):
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    move_to(obj, collection)
    if obj.type == 'MESH':
        for p in obj.data.polygons:
            p.use_smooth = smooth
    return obj

def apply(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)

def bevel(obj, amount=.02, segments=3, weighted=True):
    m = obj.modifiers.new('Real rounded edges', 'BEVEL')
    m.width = amount
    m.segments = segments
    if weighted:
        n = obj.modifiers.new('Area-weighted corner normals', 'WEIGHTED_NORMAL')
        n.keep_sharp = True
        n.weight = 50
    return obj

def box(name, loc, dims, mat, radius=.025, rotation=None, collection=asset):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.object
    ob.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(ob, name, mat, True, collection)
    if radius:
        # Leave an actual side wall: Blender's exact half-thickness clamp creates
        # coincident corner vertices and zero-area triangles on thin badges.
        bevel(ob, min(radius,min(dims)*.45), 4)
    if rotation:
        ob.rotation_euler = rotation
    return ob

def softbox(name, loc, dims, mat, roundness=.22):
    # Bevel a unit block before non-uniform scaling, for a soft cast shell.
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
    ob = bpy.context.object
    finish(ob, name, mat)
    bevel(ob, roundness, 6)
    apply(ob)
    ob.scale = (dims[0]/2, dims[1]/2, dims[2]/2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return ob

def cyl(name, loc, radius, depth, mat, axis=(0,0,1), vertices=48, edge=.012):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, end_fill_type='NGON', location=loc)
    ob = bpy.context.object
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = Vector((0,0,1)).rotation_difference(Vector(axis).normalized())
    finish(ob, name, mat)
    if edge:
        bevel(ob, min(edge,depth*.45,radius*.45), 3)
    return ob

def between(name, a, b, radius, mat, vertices=32, edge=.008):
    a, b = Vector(a), Vector(b)
    return cyl(name, (a+b)*.5, radius, (b-a).length, mat, b-a, vertices, edge)

def beam(name, a, b, width, depth, mat, edge=.018):
    a, b = Vector(a), Vector(b)
    ob = box(name, (a+b)*.5, (width, depth, (b-a).length), mat, edge)
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = Vector((0,0,1)).rotation_difference((b-a).normalized())
    return ob

def torus(name, loc, major, minor, mat, axis=(0,0,1), major_segments=48, minor_segments=8):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
        major_segments=major_segments, minor_segments=minor_segments, location=loc)
    ob = bpy.context.object
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = Vector((0,0,1)).rotation_difference(Vector(axis).normalized())
    return finish(ob, name, mat)

def bolt(name, loc, axis=(0,-1,0), radius=.013, mat=TRIM):
    # Six-sided socket in a separate inset dark cap; small details stay economical.
    d = Vector(axis).normalized()
    cyl(name + ' | fastener', loc, radius, .008, mat, d, 12, .0015)
    cyl(name + ' | recessed hex', Vector(loc)+d*.0045, radius*.40, .0015, GRAPHITE, d, 6, 0)

def sphere_shell(name, center, dims, e1=.72, e2=.8, mat=IVORY):
    def spow(x, exponent):
        return math.copysign(abs(x)**exponent, x)
    a,b,c = (v*.5 for v in dims)
    rings, seg = 28, 64
    verts = [(0,0,-c)]
    for j in range(1,rings):
        u = -math.pi/2 + math.pi*j/rings
        for i in range(seg):
            v = 2*math.pi*i/seg
            verts.append((a*spow(math.cos(u),e1)*spow(math.cos(v),e2),
                          b*spow(math.cos(u),e1)*spow(math.sin(v),e2),
                          c*spow(math.sin(u),e1)))
    verts.append((0,0,c))
    faces=[]
    for i in range(seg):
        faces.append((0, 1+(i+1)%seg, 1+i))
    for j in range(rings-2):
        s=1+j*seg
        for i in range(seg):
            n=(i+1)%seg
            faces.append((s+i,s+n,s+seg+n,s+seg+i))
    top=len(verts)-1
    s=1+(rings-2)*seg
    for i in range(seg):
        faces.append((s+i,s+(i+1)%seg,top))
    mesh=bpy.data.meshes.new(name+' geometry')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    ob=bpy.data.objects.new(name,mesh)
    asset.objects.link(ob)
    ob.location=center
    ob.data.materials.append(mat)
    for p in mesh.polygons: p.use_smooth=True
    return ob

def roundrect(width, height, radius, segments=10):
    pts=[]
    for cx,cz,a in [(width/2-radius,height/2-radius,0),
                    (-width/2+radius,height/2-radius,90),
                    (-width/2+radius,-height/2+radius,180),
                    (width/2-radius,-height/2+radius,270)]:
        for i in range(segments):
            t=math.radians(a+i*90/(segments-1))
            pts.append((cx+radius*math.cos(t),cz+radius*math.sin(t)))
    return pts

def rect_ring(name, center, outer, inner, depth, mat):
    outer_pts=roundrect(*outer)
    inner_pts=roundrect(*inner)
    n=len(outer_pts)
    verts=[]
    for yy, pts in [(-depth/2,outer_pts),(-depth/2,inner_pts),(depth/2,outer_pts),(depth/2,inner_pts)]:
        verts.extend((x,yy,z) for x,z in pts)
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces += [(i,j,n+j,n+i),(i,2*n+i,2*n+j,j),
                  (n+i,n+j,3*n+j,3*n+i),(2*n+i,3*n+i,3*n+j,2*n+j)]
    mesh=bpy.data.meshes.new(name+' geometry');mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh);asset.objects.link(ob);ob.location=center
    ob.data.materials.append(mat)
    bevel(ob,.004,2)
    return ob

def plate_polygon(name, points_xz, y, depth, mat, edge=.01):
    n=len(points_xz)
    vs=[(x,y-depth/2,z) for x,z in points_xz]+[(x,y+depth/2,z) for x,z in points_xz]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    mesh=bpy.data.meshes.new(name+' geometry');mesh.from_pydata(vs,[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh);asset.objects.link(ob);ob.data.materials.append(mat)
    bevel(ob,edge,3)
    return ob

def torso_front_y(x,z):
    sint=min(.99999,(abs(z-2.10)/.48)**(1/.72))
    cost=(1-sint*sint)**(.72/2)
    cp=min(.99999,(abs(x)/(.71*cost))**(1/.8))
    return -.47*cost*(1-cp*cp)**(.8/2)

def curved_lower_bumper():
    nx,nz=16,6;verts=[]
    for offset in [-.016,.006]:
        for j in range(nz+1):
            z=1.665+j/nz*.145;width=.36+j/nz*.07
            for i in range(nx+1):
                x=-width+2*width*i/nx
                verts.append((x,torso_front_y(x,z)+offset,z))
    layer=(nx+1)*(nz+1);faces=[]
    for j in range(nz):
        for i in range(nx):
            k=j*(nx+1)+i
            faces.append((k,k+1,k+nx+2,k+nx+1))
            faces.append((layer+k,layer+k+nx+1,layer+k+nx+2,layer+k+1))
    boundary=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,nz+1)]+[nz*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(nz-1,0,-1)]
    for i,a in enumerate(boundary):
        b=boundary[(i+1)%len(boundary)]
        faces.append((a,layer+a,layer+b,b))
    mesh=bpy.data.meshes.new('Curved lower bumper geometry');mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new('10 | Sage curved lower chest bumper',mesh);asset.objects.link(ob);mesh.materials.append(SAGE)
    for p in mesh.polygons:p.use_smooth=True
    bevel(ob,.003,2,False)
    return ob

def hose(name, points, radius=.032, corrugated=False):
    cu=bpy.data.curves.new(name+' curve','CURVE')
    cu.dimensions='3D';cu.resolution_u=10;cu.bevel_depth=radius;cu.bevel_resolution=3;cu.resolution_u=12
    sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
    for p,co in zip(sp.bezier_points,points):
        p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    ob=bpy.data.objects.new(name,cu);asset.objects.link(ob);ob.data.materials.append(RUBBER)
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.convert(target='MESH')
    ob=bpy.context.object
    for p in ob.data.polygons:p.use_smooth=True
    # Sample actual Bezier centerline for individually oriented rib rings.
    if corrugated:
        # Interpolate Catmull-Rom through the same anchors. Small ring offsets fit rubber tube.
        path=[]
        ps=[Vector(p) for p in points]
        for j in range(len(ps)-1):
            p0,p1,p2,p3=ps[max(0,j-1)],ps[j],ps[j+1],ps[min(len(ps)-1,j+2)]
            for k in range(9):
                t=k/9
                p=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)
                path.append(p)
        path.append(ps[-1])
        for i in range(2,len(path)-2,2):
            torus(name+f' | rib {i:02}',path[i],radius+.0008,.0045,GRAPHITE,
                  path[i+1]-path[i-1],24,6)
    return ob

def label(name, body, loc, size=.043, mat=GRAPHITE, rotation=(math.pi/2,0,0)):
    cu=bpy.data.curves.new(name+' font','FONT');cu.body=body;cu.align_x='CENTER';cu.align_y='CENTER'
    cu.size=size;cu.extrude=.0006;cu.bevel_depth=.0003;cu.bevel_resolution=1
    ob=bpy.data.objects.new(name,cu);asset.objects.link(ob);ob.location=loc;ob.rotation_euler=rotation;ob.data.materials.append(mat)
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.convert(target='MESH')
    return bpy.context.object

# ---- Central cast torso: actual rounded cavity for the single industrial sensor. ----
body=sphere_shell('01 | Torso ivory cast clamshell',(0,0,2.10),(1.42,.94,.96),.72,.8,IVORY)
cut=box('Temporary sensor opening',(0,-.44,2.16),(.825,.50,.185),None,.088)
apply(cut)
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bm=body.modifiers.new('Recessed sensor opening','BOOLEAN');bm.operation='DIFFERENCE';bm.solver='EXACT';bm.object=cut
bpy.ops.object.modifier_apply(modifier=bm.name)
bpy.data.objects.remove(cut,do_unlink=True)
bevel(body,.003,2,False)
rect_ring('02 | Sensor satin bezel',(0,-.478,2.16),(.88,.236,.112),(.792,.151,.071),.037,TRIM)
rect_ring('03 | Sensor rubber seal',(0,-.485,2.16),(.810,.170,.080),(.762,.123,.057),.018,RUBBER)
box('04 | Recessed smoked sensor module',(0,-.441,2.16),(.77,.035,.142),GLASS,.065)
box('05 | Single amber scan aperture',(0,-.466,2.16),(.272,.009,.015),AMBER,.006)
for i in [-3,-2,-1,1,2,3]:
    box(f'05 | Scan aperture divider {i}',(i*.032,-.472,2.16),(.002,.003,.013),ORANGE,.001)
for x in [-.32,.32]:
    box('Sensor inner corner witness',(x,-.462,2.16),(.042,.006,.015),GRAPHITE,.005)

# Sage panels are inset stepped pieces with rounded edges, distinct from the cast shell.
top=softbox('06 | Sage top service hatch',(0,-.012,2.563),(.80,.49,.067),SAGE,.23)
box('07 | Top hatch inset gasket',(0,-.10,2.602),(.36,.21,.013),SAGE_DARK,.027)
box('08 | Top hatch raised latch',(0,-.13,2.617),(.27,.085,.033),SAGE,.025)
box('09 | Ochre top electrical module',(.35,.025,2.60),(.20,.21,.071),ORANGE,.02)
box('09 | Top electrical dark inset',(.35,.025,2.641),(.137,.12,.009),SAGE_DARK,.013)
for x in [-.28,.28]:
    for y in [-.18,.14]:bolt('Top hatch', (x,y,2.604),(0,0,1),.012)
lower=curved_lower_bumper()
for x in [-.34,.34]:bolt('Lower bumper screw',(x,torso_front_y(x,1.76)-.021,1.76),radius=.012)
for s in [-1,1]:
    x=s*.60
    # Tapered service flank panel, aligned to the oval side curvature.
    panel=softbox(f'11 | {s:+} sage side shell',(x,.015,2.09),(.18,.69,.67),SAGE,.32)
    panel.rotation_euler[1]=s*math.radians(-5)
    box(f'12 | {s:+} vertical maintenance door',(s*.656,-.16,2.07),(.053,.245,.35),SAGE,.021)
    for z in [1.91,2.22]:
        bolt('Flank captive screw',(s*.687,-.18,z),(s,0,0),.012)
    for x2,z in [(s*.50,2.40),(s*.49,1.92)]:
        bolt('Chest clamshell screw',(x2,torso_front_y(x2,z)-.004,z),(0,-1,0),.013)
    for z in [2.08,2.12,2.16]:
        box('Side diagnostic slot',(s*.582,-.334,z),(.025,.015,.010),GRAPHITE,.004)

box('Chest identification plaque',(-.32,-.424,2.335),(.228,.036,.083),IVORY,.010)
label('Chest identification | SRV-07','SRV-07',(-.32,-.445,2.342),.032,SAGE_DARK)
box('Chest orange designation underline',(-.32,-.447,2.318),(.137,.006,.007),ORANGE,.002)

# Carry handles and compact amber beacon, never a humanoid head.
for s in [-1,1]:
    hose(f'13 | {s:+} upper carry handle',[(s*.43,.16,2.51),(s*.48,.17,2.68),(s*.57,.09,2.69),(s*.59,-.05,2.57)],.026)
    for x,y in [(s*.43,.16),(s*.59,-.05)]:
        cyl('Carry handle mount',(x,y,2.555),.042,.063,GRAPHITE,vertices=24,edge=.005)
cyl('14 | Beacon insulated foot',(.39,.17,2.65),.041,.09,GRAPHITE,vertices=24,edge=.008)
cyl('14 | Amber short status beacon',(.39,.17,2.727),.026,.10,ORANGE,vertices=24,edge=.008)
cyl('14 | Beacon satin cap',(.39,.17,2.783),.027,.012,TRIM,vertices=24,edge=.003)

# ---- Rear radiator / removable power cassette / paired protected hoses. ----
softbox('20 | Rear sage power-pack housing',(0,.463,2.12),(.91,.267,.75),SAGE,.24)
softbox('21 | Rear ivory protective rim',(0,.590,2.14),(.77,.08,.66),IVORY,.20)
box('22 | Cooling grille recessed dark well',(0,.642,2.275),(.565,.045,.298),RUBBER,.025)
for j in range(7):
    z=2.16+j*.037
    box(f'23 | Radiator louver {j+1}',(0,.671,z),(.51,.028,.018),GRAPHITE,.007)
box('24 | Battery cassette dark socket',(0,.646,1.94),(.57,.08,.25),GRAPHITE,.022)
box('25 | Ochre rear quick-swap battery',(0,.698,1.94),(.48,.10,.205),ORANGE,.02)
for x in [-.18,.18]:
    box('Battery latch vertical strap',(x,.757,1.94),(.035,.016,.175),TRIM,.006)
    bolt('Battery latch screw',(x,.769,2.006),(0,1,0),.009)
    bolt('Battery latch screw',(x,.769,1.878),(0,1,0),.009)
box('Battery center inset plaque',(0,.757,1.94),(.21,.013,.10),ORANGE,.009)
for x in [-.329,.329]:
    for z in [1.87,2.42]:bolt('Rear rim screw',(x,.638,z),(0,1,0),.012)
for s in [-1,1]:
    hose(f'26 | {s:+} power-pack corrugated return',[(s*.43,.49,2.29),(s*.53,.65,2.21),(s*.55,.69,1.94),(s*.42,.64,1.70),(s*.22,.48,1.67),(s*.17,.30,1.75)],.031,True)
    cyl('Rear hose locking ferrule',(s*.43,.505,2.29),.051,.072,STEEL,(0,1,0),24,.005)
    hose(f'27 | {s:+} shoulder hydraulic supply',[(s*.58,.31,2.40),(s*.73,.39,2.42),(s*.77,.36,2.13),(s*.63,.29,1.91)],.026)
    cyl('Shoulder supply lower connector',(s*.63,.305,1.92),.039,.067,GRAPHITE,(0,1,0),24,.006)

# ---- Substantial rotary shoulders, upper links, independent elbow bearings. ----
for s,side in [(-1,'L gripper'),(1,'R tool')]:
    y,z=.012,2.17
    cyl(f'30 | {side} inner shoulder bearing',(s*.70,y,z),.258,.16,GRAPHITE,(1,0,0),64,.015)
    torus(f'31 | {side} inner shoulder seal',(s*.768,y,z),.262,.017,RUBBER,(1,0,0))
    cyl(f'32 | {side} sage shoulder cast drum',(s*.877,y,z),.326,.230,SAGE,(1,0,0),64,.034)
    cyl(f'33 | {side} ivory shoulder face',(s*1.007,y,z),.278,.097,IVORY,(1,0,0),64,.024)
    cyl(f'34 | {side} shoulder inset ring',(s*1.064,y,z),.208,.028,TRIM,(1,0,0),64,.006)
    cyl(f'35 | {side} shoulder graphite rotary cap',(s*1.083,y,z),.179,.031,GRAPHITE,(1,0,0),64,.010)
    torus(f'36 | {side} shoulder cap hairline',(s*1.102,y,z),.144,.006,STEEL,(1,0,0))
    cyl(f'37 | {side} recessed shoulder center',(s*1.101,y,z),.131,.008,GRAPHITE,(1,0,0),48,.004)
    for angle in [45,135,225,315]:
        a=math.radians(angle)
        bolt(f'{side} shoulder face bolt',(s*1.062,y+math.cos(a)*.235,z+math.sin(a)*.235),(s,0,0),.011)
    # Shoulder perimeter seam is physical, not a flat line painted onto the side.
    torus(f'{side} shoulder outer seam',(s*.923,y,z),.318,.005,SAGE_DARK,(1,0,0),64,6)
    a=(s*.987,.005,2.005); b=(s*1.063,-.045,1.685)
    beam(f'38 | {side} upper arm graphite backbone',a,b,.145,.186,GRAPHITE,.022)
    beam(f'39 | {side} upper arm ivory outer guard',(s*1.036,-.056,1.99),(s*1.105,-.095,1.75),.115,.17,IVORY,.026)
    for yy in [-.087,.09]:
        between(f'40 | {side} upper-arm piston', (s*.98,yy,1.99),(s*1.055,yy-.03,1.75),.023,STEEL,24,.004)
        between(f'41 | {side} upper-arm piston sleeve',(s*.99,yy,1.96),(s*1.026,yy-.015,1.845),.035,GRAPHITE,24,.005)
    elbow=(s*1.067,-.045,1.685)
    cyl(f'42 | {side} elbow graphite motor',elbow,.154,.235,GRAPHITE,(1,0,0),48,.013)
    cyl(f'43 | {side} elbow steel race',(s*1.193,-.045,1.685),.141,.026,STEEL,(1,0,0),48,.005)
    cyl(f'44 | {side} elbow inset cap',(s*1.212,-.045,1.685),.112,.025,SAGE_DARK,(1,0,0),48,.007)
    cyl(f'45 | {side} elbow center bolt',(s*1.23,-.045,1.685),.047,.012,GRAPHITE,(1,0,0),24,.004)
    # Forearm cast sleeve follows a common downward / forward axis.
    p=Vector((s*1.075,-.076,1.57)); q=Vector((s*1.10,-.235,1.25));d=(q-p).normalized()
    between(f'46 | {side} forearm inner actuator',p,q,.100,GRAPHITE,40,.010)
    forearm=between(f'47 | {side} sage forearm housing',p+d*.035,q-d*.045,.178,SAGE,48,.025)
    between(f'48 | {side} ivory wrist cuff',q-d*.085,q+d*.025,.166,IVORY,48,.018)
    between(f'49 | {side} forearm upper end seal',p-d*.015,p+d*.032,.143,GRAPHITE,48,.007)
    guard=box(f'50 | {side} ivory forearm service door',(s*1.105,-.315,1.447),(.215,.055,.27),IVORY,.025)
    guard.rotation_euler[0]=math.radians(-24)
    inset=box(f'51 | {side} small sage service inset',(s*1.105,-.346,1.475),(.123,.022,.124),SAGE,.010)
    inset.rotation_euler[0]=math.radians(-24)
    for x in [s*1.105-.077,s*1.105+.077]:
        bolt(f'{side} forearm lid screw',(x,-.389,1.365),radius=.010)
    hose(f'52 | {side} elbow hydraulic flex',[(s*.987,.08,1.84),(s*1.01,.16,1.69),(s*1.04,.10,1.53)],.017)

# ---- Rounded two-finger industrial gripper (left). ----
cyl('60 | Gripper wrist rotary union',(-1.10,-.252,1.21),.108,.125,GRAPHITE,(0,-.35,-1),40,.012)
torus('61 | Gripper wrist satin race',(-1.10,-.275,1.17),.10,.009,STEEL,(0,-.35,-1),40,8)
softbox('62 | Gripper cast palm',(-1.10,-.290,1.106),(.253,.20,.15),IVORY,.33)
box('63 | Gripper front control panel',(-1.10,-.398,1.111),(.088,.019,.101),GRAPHITE,.023)
box('64 | Gripper ochre control surround',(-1.10,-.410,1.112),(.057,.013,.068),ORANGE,.020)
box('65 | Gripper inset control',(-1.10,-.420,1.112),(.034,.009,.045),GRAPHITE,.012)
for s in [-1,1]:
    pts=[(.076,.025),(.142,.025),(.192,-.083),(.178,-.138),(.118,-.123),(.105,-.060)]
    plate_polygon(f'66 | Gripper {s:+} ivory finger link',[(-1.10+s*x,1.047+z) for x,z in pts],-.285,.112,IVORY,.014)
    pts=[(.121,-.098),(.189,-.099),(.203,-.184),(.170,-.263),(.119,-.294),(.083,-.265),(.128,-.212),(.139,-.171)]
    plate_polygon(f'67 | Gripper {s:+} graphite curled fingertip',[(-1.10+s*x,1.047+z) for x,z in pts],-.285,.105,GRAPHITE,.016)
    cyl(f'68 | Gripper {s:+} finger pivot',(-1.10+s*.112,-.351,1.043),.028,.018,STEEL,(0,-1,0),24,.004)
    cyl(f'69 | Gripper {s:+} inner pivot inset',(-1.10+s*.112,-.363,1.043),.011,.005,GRAPHITE,(0,-1,0),12,.002)
    for k in range(3):
        box(f'Gripper pad traction strip {s:+} {k}',(-1.10+s*.143,-.346,.906-k*.025),(.041,.009,.009),RUBBER,.003)

# ---- Right rotary service tool: ochre chuck, cooling flutes, stepped steel bit. ----
tool_root=Vector((1.10,-.253,1.20));td=Vector((.025,-.38,-1)).normalized()
def tc(t):return tool_root+td*t
between('70 | Tool wrist isolator',tc(-.025),tc(.065),.111,GRAPHITE,48,.01)
between('71 | Tool ochre torque collar',tc(.038),tc(.153),.126,ORANGE,48,.014)
torus('72 | Tool torque collar upper rim',tc(.050),.122,.008,TRIM,td,48,8)
torus('73 | Tool torque collar lower rim',tc(.147),.115,.008,GRAPHITE,td,48,8)
between('74 | Tool fluted graphite spindle',tc(.145),tc(.244),.096,GRAPHITE,48,.006)
rot=Vector((0,0,1)).rotation_difference(td)
for i in range(10):
    a=2*math.pi*i/10
    offset=rot@Vector((math.cos(a)*.092,math.sin(a)*.092,0))
    ob=beam(f'75 | Tool cooling flute {i+1}',tc(.155)+offset,tc(.23)+offset,.019,.019,STEEL,.003)
between('76 | Tool front steel collar',tc(.235),tc(.274),.082,STEEL,48,.006)
between('77 | Tool dark collet',tc(.274),tc(.313),.061,GRAPHITE,40,.005)
# Conical service bit, purposefully blunt and mechanical.
bpy.ops.mesh.primitive_cone_add(vertices=40,radius1=.029,radius2=.055,depth=.092,location=tc(.355))
ob=bpy.context.object;ob.rotation_mode='QUATERNION';ob.rotation_quaternion=Vector((0,0,1)).rotation_difference(-td)
finish(ob,'78 | Tool tapered steel nose',STEEL);bevel(ob,.004,2)
between('79 | Tool hexagonal driver bit',tc(.395),tc(.467),.025,STEEL,6,.003)
between('80 | Tool dark driver tip',tc(.460),tc(.483),.020,GRAPHITE,6,.002)
for i in [-1,1]:
    bolt('Tool collar captive screw',tc(.10)+Vector((i*.123,0,0)),(i,0,0),.012)

# ---- Exposed central articulation and wide planted legs. ----
softbox('90 | Central graphite suspension neck',(0,.01,1.535),(.29,.32,.22),GRAPHITE,.2)
softbox('91 | Sage pelvis gearbox',(0,.005,1.365),(.33,.36,.28),SAGE,.26)
box('92 | Pelvis front service plate',(0,-.192,1.38),(.252,.035,.196),SAGE,.018)
for x in [-.09,.09]:
    for z in [1.32,1.44]:bolt('Pelvis fastener',(x,-.214,z),radius=.011)
for s,side in [(-1,'L'),(1,'R')]:
    hip=(s*.365,.01,1.365)
    cyl(f'93 | {side} hip shaft',(s*.255,.01,1.365),.144,.21,GRAPHITE,(1,0,0),48,.012)
    torus(f'94 | {side} hip shaft seal',(s*.285,.01,1.365),.139,.011,STEEL,(1,0,0))
    cyl(f'95 | {side} outer hip motor',hip,.191,.245,GRAPHITE,(1,0,0),48,.016)
    cyl(f'96 | {side} ivory hip bearing cover',(s*.498,.01,1.365),.180,.047,IVORY,(1,0,0),48,.012)
    cyl(f'97 | {side} inset hip cap',(s*.529,.01,1.365),.129,.026,STEEL,(1,0,0),48,.007)
    cyl(f'98 | {side} hip core',(s*.549,.01,1.365),.096,.018,GRAPHITE,(1,0,0),40,.005)
    # Thighs splay gently outward; joints remain legible between their panels.
    a=(s*.385,.014,1.31);b=(s*.46,-.015,.914)
    beam(f'99 | {side} thigh structural link',a,b,.135,.172,GRAPHITE,.019)
    thigh=softbox(f'100 | {side} ivory thigh armor',(s*.442,-.045,1.149),(.278,.325,.403),IVORY,.38)
    thigh.rotation_euler[1]=s*math.radians(-10)
    sideplate=softbox(f'101 | {side} sage thigh side plate',(s*.559,-.005,1.145),(.046,.25,.302),SAGE,.25)
    sideplate.rotation_euler[1]=s*math.radians(-10)
    box(f'102 | {side} thigh front lower recess',(s*.464,-.213,1.005),(.098,.023,.09),GRAPHITE,.017)
    for z in [1.06,1.24]:bolt(f'{side} thigh side screw',(s*.592,-.035,z),(s,0,0),.010)
    knee=(s*.472,-.012,.847)
    cyl(f'103 | {side} knee motor',knee,.153,.250,GRAPHITE,(1,0,0),48,.014)
    cyl(f'104 | {side} sage knee outer cap',(s*.605,-.012,.847),.143,.047,SAGE,(1,0,0),48,.012)
    cyl(f'105 | {side} knee bearing bright race',(s*.636,-.012,.847),.113,.027,TRIM,(1,0,0),48,.007)
    cyl(f'106 | {side} graphite knee center',(s*.655,-.012,.847),.090,.021,GRAPHITE,(1,0,0),40,.005)
    for ang in [0,120,240]:
        ang=math.radians(ang)
        bolt(f'{side} knee cap screw',(s*.671,-.012+math.cos(ang)*.068,.847+math.sin(ang)*.068),(s,0,0),.007)
    shin_a=(s*.475,-.004,.749);shin_b=(s*.510,.035,.354)
    beam(f'107 | {side} shin inner load strut',shin_a,shin_b,.128,.157,GRAPHITE,.018)
    shin=softbox(f'108 | {side} sage lower leg casting',(s*.497,.013,.557),(.266,.276,.364),SAGE,.3)
    shin.rotation_euler[1]=s*math.radians(-5)
    front=softbox(f'109 | {side} ivory shin inspection cover',(s*.497,-.142,.563),(.20,.072,.334),IVORY,.3)
    front.rotation_euler[1]=s*math.radians(-5)
    box(f'110 | {side} shin orange service lock',(s*.506,-.188,.429),(.079,.031,.057),ORANGE,.009)
    box(f'111 | {side} shin lock dark surround',(s*.506,-.167,.424),(.103,.023,.083),GRAPHITE,.012)
    for z in [.49,.68]:bolt(f'{side} shin side screw',(s*.632,.01,z),(s,0,0),.01)
    # A rear polished pushrod clearly connects the lower-leg shell to the ankle.
    between(f'112 | {side} shin rear polished piston',(s*.499,.16,.691),(s*.512,.16,.378),.026,STEEL,24,.004)
    between(f'113 | {side} shin piston collar',(s*.500,.16,.687),(s*.506,.16,.54),.040,GRAPHITE,32,.006)
    ankle=(s*.514,.018,.283)
    cyl(f'114 | {side} ankle load bearing',ankle,.128,.305,GRAPHITE,(1,0,0),48,.011)
    cyl(f'115 | {side} outer ankle steel race',(s*.677,.018,.283),.113,.031,STEEL,(1,0,0),48,.006)
    cyl(f'116 | {side} dark ankle center',(s*.698,.018,.283),.086,.025,GRAPHITE,(1,0,0),40,.007)
    # Foot sole has a stable flat contact plane and real rounded toe/heel forms.
    softbox(f'117 | {side} rubber traction sole',(s*.510,-.154,.066),(.493,.701,.132),RUBBER,.29)
    softbox(f'118 | {side} sage foot bumper',(s*.510,-.168,.152),(.478,.672,.105),SAGE,.33)
    boot=softbox(f'119 | {side} ivory upper foot cast',(s*.510,-.176,.225),(.430,.584,.175),IVORY,.55)
    for v in boot.data.vertices:
        top_factor=max(0,min(1,v.co.z/.175+.5))
        v.co.z+=top_factor*.060*v.co.y/.584
    # Slight rear tongue protecting the foot pitch joint.
    box(f'120 | {side} sage top foot tongue',(s*.510,-.135,.321),(.173,.204,.029),SAGE,.022)
    for xx in [-.183,.183]:
        bolt(f'{side} toe bumper fastener',(s*.510+xx,-.487,.145),radius=.010)
    for i in range(5):
        box(f'121 | {side} front sole molded tread {i+1}',(s*.510+(i-2)*.075,-.503,.057),(.048,.012,.026),GRAPHITE,.006)
    for yy in [-.36,-.22,.04]:
        box(f'{side} sole side tread relief',(s*.756,yy,.058),(.011,.058,.027),GRAPHITE,.005)
    box(f'122 | {side} heel reinforcement',(s*.510,.146,.144),(.270,.123,.145),GRAPHITE,.025)
    bolt(f'{side} foot outer inspection screw',(s*.727,-.25,.236),(s,0,0),.011)

# Finalize evaluated meshes before exporting. UVs are genuine per-component islands.
bpy.ops.object.select_all(action='DESELECT')
for obj in list(asset.objects):
    if obj.type == 'MESH':
        apply(obj)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True);bpy.context.view_layer.objects.active=obj
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
        bm.to_mesh(obj.data);bm.free()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.018,area_weight=.35,scale_to_bounds=True)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj['role']='Service mech geometry'
        obj['uv_note']='Per-component packed smart-projected UV islands; solid PBR materials'

# Set exact 2.8 m maximum height, and ground the model with no transformation helper in exports.
coords=[o.matrix_world@v.co for o in asset.objects if o.type=='MESH' for v in o.data.vertices]
lo=min(p.z for p in coords);hi=max(p.z for p in coords)
factor=2.8/(hi-lo)
for obj in asset.objects:
    if obj.type=='MESH':
        for v in obj.data.vertices:
            world=obj.matrix_world@v.co
            world.z-=lo
            world*=factor
            v.co=obj.matrix_world.inverted()@world
        obj.data.update()

# ---- Quiet photographic studio (never exported). ----
floor=box('Studio floor',(0,0,-.055),(200,200,.10),FLOOR,0,collection=studio)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1.0
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32
scene.cycles.use_denoising=True
scene.cycles.max_bounces=7;scene.cycles.diffuse_bounces=4;scene.cycles.glossy_bounces=4
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=1440;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.render.film_transparent=False
scene.render.image_settings.color_depth='8'
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.world.color=(.25,.25,.25)
scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.70,.72,.70,1)
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.34

def area(name,loc,power,color,size,target):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size
    ob=bpy.data.objects.new(name,data);studio.objects.link(ob);ob.location=loc
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob

area('Large warm key',(-3.5,-4.8,6.3),900,(1.0,.91,.78),4.0,(0,0,1.4))
area('Soft cool fill',(4.5,-2.6,4.0),650,(.82,.90,1.0),3.5,(0,0,1.5))
area('Rear edgebox',(1.0,4.0,5.2),1100,(1.0,.96,.85),3.0,(0,0,1.5))
area('Front sensor lift',(-.5,-4,2.5),100,(1,1,1),3.0,(0,0,1.4))

def camera(name,loc,target,scale):
    data=bpy.data.cameras.new(name);data.type='ORTHO';data.ortho_scale=scale;data.lens=50
    ob=bpy.data.objects.new(name,data);studio.objects.link(ob);ob.location=loc
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob

hero=camera('Camera | hero front right',(4.2,-7.4,4.0),(0,-.02,1.37),4.45)
rear=camera('Camera | rear left',(-4.1,7.0,3.75),(0,.06,1.38),4.45)
scene.camera=hero
scene['asset_name']='Service mech | SRV-07'
scene['front_axis']='-Y';scene['unit']='meters';scene['reference']='D:/github/AstraEffort/REF/Set01/service_mech.png'
scene['build_started_at_utc']=START
scene['notes']='Static rounded service machine. Geometry-only ASSET exports; studio excluded. No external textures.'

# Export only geometry selected from ASSET, modifiers are already applied.
bpy.ops.object.select_all(action='DESELECT')
for ob in asset.objects:
    if ob.type=='MESH':ob.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(ROOT/'service_mech.glb'),export_format='GLB',use_selection=True,
    export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_yup=True)
bpy.ops.export_scene.fbx(filepath=str(ROOT/'service_mech.fbx'),use_selection=True,object_types={'MESH'},
    apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',axis_forward='-Y',axis_up='Z',
    use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,path_mode='AUTO')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'service_mech.blend'))

render_manifest={'engine':'Cycles','device':'CPU','threads':4,'samples':32,'denoise':True,
 'resolution':[1440,1080],'view_transform':'AgX','look':scene.view_settings.look,'cameras':[]}
for cam,file in [(hero,'hero.png'),(rear,'rear.png')]:
    scene.camera=cam
    scene.render.filepath=str(ROOT/'renders'/file)
    ts=datetime.now(timezone.utc).isoformat();rt=time.time()
    bpy.ops.render.render(write_still=True)
    render_manifest['cameras'].append({'name':cam.name,'file':'renders/'+file,'location':list(cam.location),
      'rotation_euler':list(cam.rotation_euler),'orthographic_scale':cam.data.ortho_scale,
      'started_at_utc':ts,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'render_seconds':time.time()-rt})
scene.camera=hero
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'service_mech.blend'))
(ROOT/'capture_manifest.json').write_text(json.dumps(render_manifest,indent=2),encoding='utf-8')
(ROOT/'build_run.json').write_text(json.dumps({'started_at_utc':START,'finished_at_utc':datetime.now(timezone.utc).isoformat(),
  'elapsed_seconds':time.time()-T0,'blender_version':bpy.app.version_string,'asset_mesh_count':len([o for o in asset.objects if o.type=='MESH'])},indent=2),encoding='utf-8')
print('SERVICE_MECH_BUILD_COMPLETE', flush=True)
