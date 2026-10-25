"""Water station / Set01. Run in a private Blender 4.5 process.

Authoring coordinates: meters, Z up, front -Y. All design is owned by this asset.
No external assets, images, packages, or shared scene state are loaded.
"""
import bpy
import math
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parent
START = datetime.now(timezone.utc)
START_T = time.perf_counter()
OUT = ROOT / 'renders'
OUT.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene.unit_settings.length_unit = 'METERS'
asset = bpy.data.collections.new('ASSET')
studio = bpy.data.collections.new('STUDIO')
scene.collection.children.link(asset)
scene.collection.children.link(studio)


def stamp():
    return datetime.now(timezone.utc).isoformat()


def linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def mat(name, hexcode, rough=.45, metal=0.0, emission=0.0):
    rgb = [linear(int(hexcode[i:i+2], 16) / 255.0) for i in (0, 2, 4)]
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*rgb, 1)
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = metal
    if emission:
        bs.inputs['Emission Color'].default_value = (*rgb, 1)
        bs.inputs['Emission Strength'].default_value = emission
    return m


IVORY = mat('Paint | warm porcelain ivory', 'D8D0BA', .42, .10)
IVORY_EDGE = mat('Paint | ivory seams', 'BEB7A3', .47, .12)
SAGE = mat('Paint | muted sage green', '7D9585', .40, .18)
SAGE_EDGE = mat('Paint | deep sage bands', '647C6D', .43, .20)
GRAPHITE = mat('Metal | graphite cast iron', '414A43', .46, .62)
STEEL = mat('Metal | satin nickel bolts', 'A6AAA0', .32, .76)
ORANGE = mat('Paint | safety orange valves', 'D98639', .36, .23)
CONCRETE = mat('Foundation | warm concrete', 'ACA99C', .83, 0)
CONCRETE_EDGE = mat('Foundation | stair tread nosing', 'C0BBAC', .78, 0)
DARK = mat('Inserts | deep recess', '222C28', .58, .12)
FACE = mat('Gauge | ivory dial', 'ECE6D6', .52, .0)
GLASS = mat('Gauge | smoked window', '30463E', .18, .35)
AMBER = mat('Lamp | amber lens', 'F4B967', .30, .05, .25)
GROUND = mat('Studio | pale warm backdrop', 'D8D4CA', .92, 0)


def move_to(obj, coll=asset):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)
    return obj


def finish(obj, name, material, smooth=False):
    obj.name = name
    move_to(obj)
    if material:
        obj.data.materials.append(material)
    if obj.type == 'MESH':
        for p in obj.data.polygons:
            p.use_smooth = smooth
    obj['asset'] = 'water_station'
    return obj


def bevel(obj, width=.025, segments=3):
    mod = obj.modifiers.new('Manufactured edge radius', 'BEVEL')
    mod.width = width
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    mod.angle_limit = math.radians(35)
    mod.harden_normals = True
    norm = obj.modifiers.new('Face-weighted normals', 'WEIGHTED_NORMAL')
    norm.keep_sharp = True
    norm.weight = 40
    return obj


def box(name, loc, dims, material, radius=.025, rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = finish(bpy.context.object, name, material)
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if rotation:
        o.rotation_euler = rotation
    if radius:
        # A radius at half the thin depth collapses parallel bevel bands.
        # Keep a planar strip between them, including on door plates and windows.
        bevel(o, min(radius, min(dims)*.40), 3)
    return o


def cylinder(name, loc, radius, depth, material, axis=(0,0,1), vertices=64, edge=.01):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, end_fill_type='NGON', location=loc)
    o = finish(bpy.context.object, name, material, True)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector(axis).normalized().to_track_quat('Z', 'Y')
    for p in o.data.polygons:
        if len(p.vertices) > 4:
            p.use_smooth = False
    if edge:
        bevel(o, edge, 3)
    return o


def rod(name, a, b, radius, material, vertices=16):
    a, b = Vector(a), Vector(b)
    return cylinder(name, (a+b)*.5, radius, (b-a).length, material, (b-a), vertices, min(radius*.25, .006))


def torus(name, center, major, minor, material, axis=(0,0,1), major_segments=64, minor_segments=10):
    bpy.ops.mesh.primitive_torus_add(major_segments=major_segments, minor_segments=minor_segments,
        location=center, major_radius=major, minor_radius=minor)
    o = finish(bpy.context.object, name, material, True)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector(axis).normalized().to_track_quat('Z', 'Y')
    return o


def mesh_obj(name, verts, faces, material, smooth=False):
    data = bpy.data.meshes.new(name + ' | mesh')
    data.from_pydata(verts, [], faces)
    data.update()
    o = bpy.data.objects.new(name, data)
    asset.objects.link(o)
    data.materials.append(material)
    for p in data.polygons:
        p.use_smooth = smooth
    o['asset'] = 'water_station'
    return o


def lathe(name, center, profile, material, segments=96):
    # profile runs around cross-section; caps are closed with planar end ngons.
    verts = []
    for r, z in profile:
        for j in range(segments):
            a = math.tau*j/segments
            verts.append((center[0]+r*math.cos(a), center[1]+r*math.sin(a), z))
    faces = []
    for i in range(len(profile)-1):
        for j in range(segments):
            n = (j+1) % segments
            faces.append((i*segments+j, i*segments+n, (i+1)*segments+n, (i+1)*segments+j))
    faces.append(tuple(range(segments-1, -1, -1)))
    faces.append(tuple((len(profile)-1)*segments+j for j in range(segments)))
    o = mesh_obj(name, verts, faces, material, True)
    o.data.polygons[-1].use_smooth = False
    o.data.polygons[-2].use_smooth = False
    return o


def rounded_path(points, radius=.25, subdivisions=10):
    pts = [Vector(p) for p in points]
    result = [pts[0]]
    for i in range(1, len(pts)-1):
        p, prev, nxt = pts[i], pts[i-1], pts[i+1]
        va, vb = (prev-p).normalized(), (nxt-p).normalized()
        angle = va.angle(vb)
        if abs(angle-math.pi) < 1e-5:
            result.append(p)
            continue
        t = min(radius / math.tan(angle/2), (prev-p).length*.44, (nxt-p).length*.44)
        rr = t*math.tan(angle/2)
        center = p + (va+vb).normalized() * rr/math.sin(angle/2)
        start, end = p+va*t, p+vb*t
        a = start-center
        b = end-center
        rotation = a.rotation_difference(b)
        result.append(start)
        from mathutils import Quaternion
        identity = Quaternion((1,0,0,0))
        for j in range(1, subdivisions+1):
            result.append(center + identity.slerp(rotation, j/subdivisions) @ a)
    result.append(pts[-1])
    return result


def tube(name, points, radius, material, fillet=.25, sides=20):
    pts = rounded_path(points, fillet, 10) if fillet else [Vector(p) for p in points]
    verts = []
    # All authored paths are planar or sufficiently gradual for this transported frame.
    old_u = None
    for i, p in enumerate(pts):
        tangent = (pts[min(i+1, len(pts)-1)]-pts[max(i-1, 0)]).normalized()
        if old_u is None:
            ref = Vector((0,1,0)) if abs(tangent.y) < .85 else Vector((1,0,0))
            u = tangent.cross(ref).normalized()
        else:
            u = (old_u - tangent*old_u.dot(tangent)).normalized()
        v = tangent.cross(u).normalized()
        old_u = u
        for j in range(sides):
            a = math.tau*j/sides
            verts.append(tuple(p + radius*(u*math.cos(a)+v*math.sin(a))))
    faces = []
    for i in range(len(pts)-1):
        for j in range(sides):
            k = (j+1) % sides
            faces.append((i*sides+j, i*sides+k, (i+1)*sides+k, (i+1)*sides+j))
    faces.extend([tuple(range(sides-1,-1,-1)), tuple((len(pts)-1)*sides+j for j in range(sides))])
    o = mesh_obj(name, verts, faces, material, True)
    for p in o.data.polygons[-2:]:
        p.use_smooth = False
    return o


def axis_frame(axis):
    n = Vector(axis).normalized()
    ref = Vector((0,0,1)) if abs(n.z)<.8 else Vector((0,1,0))
    u = n.cross(ref).normalized()
    v = n.cross(u).normalized()
    return n,u,v


def flange(name, center, axis, pipe_r=.15, bolts=8, pair=True):
    c = Vector(center)
    n,u,v = axis_frame(axis)
    offsets = [-.045,.045] if pair else [0]
    outer = pipe_r*1.54
    for k, offset in enumerate(offsets):
        pos = c+n*offset
        cylinder(name+f' | flange {k+1}', pos, outer, .063, GRAPHITE, n, 48, .008)
        torus(name+f' | rim {k+1}', pos+n*.033, outer-.012, .009, STEEL, n, 48, 6)
    if pair:
        cylinder(name+' | dark gasket', c, outer-.013, .021, DARK, n, 48, .002)
    for j in range(bolts):
        a = math.tau*(j+.5)/bolts
        radial = (u*math.cos(a)+v*math.sin(a))*(outer-.038)
        for side in [-1,1]:
            z = .085 if pair else .044
            pos = c+radial+n*(z*side)
            cylinder(name+f' | bolt {j+1:02d} {side:+d}', pos, .021, .027, STEEL, n, 6, .002)


def wheel(name, center, radius=.15, axis=(0,-1,0)):
    c = Vector(center)
    n,u,v = axis_frame(axis)
    torus(name+' | orange handwheel rim', c, radius, .019, ORANGE, n, 48, 10)
    cylinder(name+' | hub', c, .042, .052, ORANGE, n, 24, .005)
    for i in range(4):
        a = math.tau*i/4 + math.pi/4
        edge = c + radius*(u*math.cos(a)+v*math.sin(a))
        rod(name+f' | spoke {i+1}', c, edge, .013, ORANGE, 12)
    cylinder(name+' | stem fastener', c+n*.034, .017, .014, STEEL, n, 6, .002)


def valve(name, center, flow_axis=(1,0,0), wheel_axis=(0,-1,0), radius=.15):
    c = Vector(center)
    n = Vector(flow_axis).normalized()
    w = Vector(wheel_axis).normalized()
    cylinder(name+' | valve body', c, radius*1.23, .25, GRAPHITE, n, 32, .025)
    flange(name+' | upstream', c-n*.18, n, radius, 8, False)
    flange(name+' | downstream', c+n*.18, n, radius, 8, False)
    rod(name+' | bonnet', c+w*.05, c+w*.25, .055, GRAPHITE, 20)
    rod(name+' | stem', c+w*.23, c+w*.37, .021, STEEL, 12)
    wheel(name, c+w*.36, .155, w)


# Rounded U-shaped concrete pad with a real stair recess.
outline = [(-3.25,-2.17)]
for a in range(180,271,15):
    outline.append((-3.02+.23*math.cos(math.radians(a)), -2.17+.23*math.sin(math.radians(a))))
outline.extend([(-1.035,-2.4),(-1.035,-1.04),(1.035,-1.04),(1.035,-2.4),(3.02,-2.4)])
for a in range(270,361,15):
    outline.append((3.02+.23*math.cos(math.radians(a)), -2.17+.23*math.sin(math.radians(a))))
outline.append((3.25,2.17))
for a in range(0,91,15):
    outline.append((3.02+.23*math.cos(math.radians(a)), 2.17+.23*math.sin(math.radians(a))))
outline.append((-3.02,2.4))
for a in range(90,181,15):
    outline.append((-3.02+.23*math.cos(math.radians(a)), 2.17+.23*math.sin(math.radians(a))))
# Remove repeated end points before extrusion.
outline = [p for i,p in enumerate(outline) if i==0 or (Vector(p)-Vector(outline[i-1])).length>1e-6]
n = len(outline)
verts = [(x,y,z) for z in (.0,.42) for x,y in outline]
faces = [tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]
faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
foundation = mesh_obj('Foundation | rounded concrete pad with stair recess', verts, faces, CONCRETE)
bevel(foundation, .045, 3)

# Four actual small foot-level utility slots cut into the foundation edge.
for idx,(x,y) in enumerate([(-2.46,-2.39),(2.46,-2.39),(-2.46,2.39),(2.46,2.39)]):
    cut = box('temporary foundation cutter', (x,y,.045), (.34,.24,.18), None, .025)
    bpy.context.view_layer.objects.active = cut
    for mod in list(cut.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    mod = foundation.modifiers.new('Foot utility clearance', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cut
    bpy.context.view_layer.objects.active = foundation
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cut, do_unlink=True)

# Five clean solid treads and protected sloping cheeks.
for i in range(5):
    h = .18*(i+1)
    y = -2.4 + .252*(i+.5)
    box(f'Stair | step {i+1:02d} of 05', (0,y,h*.5), (1.75,.265,h), CONCRETE, .023)
    box(f'Stair | tread nosing {i+1:02d}', (0,y-.115,h-.019), (1.70,.045,.035), CONCRETE_EDGE, .009)
box('Stair | top landing', (0,-.995,.66), (2.05,.34,.48), CONCRETE, .04)
for side in [-1,1]:
    x = side*.955
    profile = [(-2.4,.0),(-1.04,.0),(-1.04,.98),(-2.4,.20)]
    vv = [(xx,y,z) for xx in [x-.095,x+.095] for y,z in profile]
    ff = [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    bevel(mesh_obj(f'Stair | side cheek {side:+d}', vv,ff,CONCRETE), .025,3)
    tube(f'Handrail {side:+d} | continuous upper rail',[(x,-2.30,.22),(x,-2.30,1.10),(x,-1.09,1.97),(x,-.81,1.97)],.031,SAGE_EDGE,.08,16)
    rod(f'Handrail {side:+d} | upper upright',(x,-.89,.90),(x,-.89,1.97),.031,SAGE_EDGE)
    tube(f'Handrail {side:+d} | middle rail',[(x,-2.30,.68),(x,-1.09,1.55),(x,-.89,1.55)],.024,SAGE_EDGE,.06,16)
    for y,z in [(-2.30,.21),(-.89,.90)]:
        box(f'Handrail {side:+d} | mounting shoe {y}',(x,y,z+.021),(.14,.14,.042),GRAPHITE,.015)
        for dx in [-.043,.043]:
            cylinder(f'Handrail {side:+d} | anchor',(x+dx,y,z+.047),.015,.016,STEEL,vertices=6,edge=.002)


def build_tank(prefix, x, y, radius, top, dome_h, body_mat, cap_mat, band_mat):
    body = cylinder(prefix+' | cylindrical pressure vessel', (x,y,(.70+top)*.5),radius,top-.70,body_mat,vertices=96,edge=.035)
    body['component_role'] = 'primary_tank'
    body['tank_radius_m'] = radius
    body['tank_body_height_m'] = top-.70
    cylinder(prefix+' | bottom skirt',(x,y,.71),radius+.027,.17,cap_mat,vertices=96,edge=.025)
    torus(prefix+' | rolled lower edge',(x,y,.65),radius-.009,.036,cap_mat,major_segments=96)
    heights = [.88,1.92,3.10,top-.045] if top>4 else [.86,1.67,2.62,top-.045]
    for i,z in enumerate(heights):
        lathe(prefix+f' | raised circumferential band {i+1}',(x,y),[(radius-.006,z-.026),(radius+.014,z-.025),(radius+.022,z-.013),(radius+.022,z+.013),(radius+.014,z+.025),(radius-.006,z+.026)],band_mat)
    # The shallow elliptical cap is real surface geometry, with a gently rolled edge.
    profile = [(radius+.03,top-.015),(radius+.037,top+.025)]
    for i in range(17):
        t = (math.pi/2-.025)*i/16
        profile.append(((radius+.035)*math.cos(t),top+.055+dome_h*math.sin(t)))
    profile.append((.005,top+.055+dome_h))
    lathe(prefix+' | shallow domed cap',(x,y),profile,cap_mat)
    torus(prefix+' | cap seam lip',(x,y,top+.035),radius+.023,.018,band_mat,major_segments=96)
    # Quiet raised panel seams make the large surfaces readable without graphics.
    for j in range(8):
        a = math.tau*j/8
        rod(prefix+f' | body panel weld {j+1}',(x+(radius+.001)*math.cos(a),y+(radius+.001)*math.sin(a),.83),
            (x+(radius+.001)*math.cos(a),y+(radius+.001)*math.sin(a),top-.06),.0045,band_mat,8)
        path=[]
        for k in range(15):
            t = .04+(math.pi/2-.20)*k/14
            rr = (radius+.037)*math.cos(t)
            path.append((x+rr*math.cos(a),y+rr*math.sin(a),top+.058+dome_h*math.sin(t)))
        tube(prefix+f' | cap panel weld {j+1}',path,.0045,band_mat,0,6)
    cap_z=top+.055+dome_h
    cylinder(prefix+' | vent neck',(x,y,cap_z+.055),.18,.15,cap_mat,vertices=48,edge=.015)
    cylinder(prefix+' | vent shadow gap',(x,y,cap_z+.143),.17,.036,DARK,vertices=48,edge=.006)
    cylinder(prefix+' | mushroom vent cover',(x,y,cap_z+.183),.235,.066,GRAPHITE if top>4 else cap_mat,vertices=48,edge=.025)
    torus(prefix+' | vent rim',(x,y,cap_z+.198),.214,.010,STEEL if top>4 else band_mat,major_segments=48,minor_segments=8)
    for j,a in enumerate([math.radians(25),math.radians(155),math.radians(260)]):
        rr = radius*.84
        z = top+.055+dome_h*math.sqrt(max(0,1-(rr/(radius+.035))**2))+.045
        p = Vector((x+rr*math.cos(a),y+rr*math.sin(a),z))
        torus(prefix+f' | lifting eye {j+1}',p,.060,.020,band_mat,(math.cos(a),math.sin(a),0),32,8)
        box(prefix+f' | lifting eye foot {j+1}',(p.x,p.y,p.z-.05),(.11,.10,.06),band_mat,.015)
    # Four isolated feet carry the vessel clear of the foundation.
    for j in range(4):
        a = math.pi/4+j*math.pi/2
        xx,yy=x+radius*.76*math.cos(a),y+radius*.76*math.sin(a)
        box(prefix+f' | concrete support {j+1}',(xx,yy,.53),(.30,.32,.22),CONCRETE,.025)
        box(prefix+f' | support saddle {j+1}',(xx,yy,.66),(.23,.25,.08),GRAPHITE,.02)
        for d in [-.09,.09]:
            cylinder(prefix+f' | foot anchor {j+1} {d}',(xx+d,yy-.11,.655),.018,.026,STEEL,vertices=6,edge=.002)


build_tank('Tank A tall ivory',-1.55,.66,1.16,4.66,.50,IVORY,SAGE,IVORY_EDGE)
build_tank('Tank B short sage',1.55,.66,1.06,3.44,.37,SAGE,IVORY,SAGE_EDGE)


def inspection(prefix, x, y, z, radius):
    axis=(0,-1,0)
    cylinder(prefix+' | reinforced mounting boss',(x,y+.045,z),radius+.055,.10,GRAPHITE,axis,64,.018)
    cylinder(prefix+' | bolted inspection cover',(x,y-.014,z),radius,.065,SAGE,axis,64,.018)
    torus(prefix+' | cover raised rim',(x,y-.05,z),radius-.025,.012,STEEL,axis,64,8)
    for j in range(10):
        a=math.tau*j/10
        cylinder(prefix+f' | cover bolt {j+1:02d}',(x+(radius-.035)*math.cos(a),y-.062,z+(radius-.035)*math.sin(a)),.022,.022,STEEL,axis,6,.002)
    box(prefix+' | cover hinge tab',(x-radius-.012,y-.01,z),(.065,.08,.14),GRAPHITE,.012)


inspection('Tank A',-1.55,-.525,1.30,.33)
inspection('Tank B',1.55,-.425,1.28,.30)


def ladder(prefix, center, radius, top, normal):
    center=Vector((center[0],center[1],0)); n=Vector((normal[0],normal[1],0)).normalized(); t=Vector((-n.y,n.x,0))
    base=center+n*(radius+.13)
    for side in [-1,1]:
        p=base+t*(side*.21)
        points=[(p.x,p.y,.46),(p.x,p.y,top+.18),tuple(p-n*.26+Vector((0,0,top+.18))),tuple(p-n*.26+Vector((0,0,top-.12)))]
        # The point vectors above are planar offsets whose base z is zero.
        tube(prefix+f' | curved side rail {side:+d}',points,.027,GRAPHITE,.11,14)
    count=int((top-.55)/.29)+1
    for j in range(count):
        z=.58+j*.29
        a=base-t*.21+Vector((0,0,z)); b=base+t*.21+Vector((0,0,z))
        rod(prefix+f' | rung {j+1:02d}',a,b,.021,GRAPHITE,12)
    for j,z in enumerate([.70,1.75,2.8]+([3.85,4.58] if top>4 else [3.38])):
        for side in [-1,1]:
            p=base+t*(side*.21)+Vector((0,0,z))
            rod(prefix+f' | wall stand-off {j+1} {side}',p,p-n*.17,.021,GRAPHITE,12)
            cylinder(prefix+f' | bracket pad {j+1} {side}',p-n*.17,.054,.022,GRAPHITE,n,24,.005)
    for side in [-1,1]:
        p=base+t*(side*.21)
        box(prefix+f' | ladder foot {side}',(p.x,p.y,.443),(.16,.16,.045),GRAPHITE,.015)


ladder('Tank A service ladder',(-1.55,.66),1.16,5.12,(-.90,-.44))
ladder('Tank B service ladder',(1.55,.66),1.06,3.81,(.99,.10))

# Pump house body, cap roof and coherent front service details.
box('Pump house | rounded ivory enclosure',(0,-.48,1.75),(2.02,1.44,1.82),IVORY,.105)
box('Pump house | footing plinth',(0,-.48,.86),(2.07,1.48,.13),SAGE_EDGE,.045)
box('Pump house | sage roof fascia',(0,-.48,2.635),(2.10,1.51,.12),SAGE_EDGE,.045)
box('Pump house | shallow rounded ivory roof',(0,-.48,2.72),(2.08,1.49,.18),IVORY,.075)
for x in [-.88,.88]:
    box('Pump house | front corner seam',(x,-1.203,1.74),(.014,.012,1.57),IVORY_EDGE,.004)
box('Door | dark seal surround',(.34,-1.226,1.665),(.79,.055,1.56),GRAPHITE,.055)
box('Door | sage rounded service leaf',(.34,-1.266,1.665),(.71,.065,1.48),SAGE,.045)
box('Door | recessed window border',(.43,-1.307,1.87),(.115,.020,.395),STEEL,.012)
box('Door | narrow smoked window',(.43,-1.321,1.87),(.075,.014,.35),GLASS,.008)
for z in [1.18,2.17]:
    cylinder('Door | hinge barrel',(.709,-1.29,z),.026,.16,GRAPHITE,vertices=20,edge=.006)
box('Door | handle escutcheon',(.09,-1.31,1.40),(.07,.018,.15),GRAPHITE,.015)
tube('Door | cast L handle',[(.09,-1.33,1.43),(.09,-1.38,1.43),(.20,-1.38,1.43)],.016,STEEL,.025,12)
cylinder('Door | lock cylinder',(.09,-1.33,1.355),.014,.012,STEEL,(0,-1,0),16,.002)
box('Louver | sage outer frame',(-.53,-1.24,1.66),(.49,.08,1.14),SAGE_EDGE,.025)
box('Louver | dark ventilation recess',(-.53,-1.286,1.66),(.403,.018,1.025),DARK,.008)
for j in range(10):
    box(f'Louver | angled blade {j+1:02d}',(-.53,-1.305,1.20+j*.102),(.39,.076,.041),SAGE,.011,(math.radians(24),0,0))
for x in [-.735,-.325]:
    for z in [1.15,2.17]:
        cylinder('Louver | frame screw',(x,-1.289,z),.012,.015,STEEL,(0,-1,0),12,.002)

# Gauge: modeled bezel, dial, scale, spindle and needle, with no texture dependency.
gx,gy,gz=.825,-1.245,2.05
cylinder('Gauge | graphite housing',(gx,gy,gz),.118,.08,GRAPHITE,(0,-1,0),64,.013)
cylinder('Gauge | ivory dial',(gx,gy-.047,gz),.094,.012,FACE,(0,-1,0),64,.003)
torus('Gauge | polished bezel',(gx,gy-.051,gz),.101,.011,STEEL,(0,-1,0),64,10)
for j in range(11):
    a=math.radians(-40+j*26)
    r1=.062 if j%5==0 else .070
    a1=(gx+r1*math.cos(a),gy-.058,gz+r1*math.sin(a)); a2=(gx+.083*math.cos(a),gy-.058,gz+.083*math.sin(a))
    rod(f'Gauge | engraved scale {j+1:02d}',a1,a2,.0027,DARK,8)
rod('Gauge | orange pressure needle',(gx,gy-.063,gz),(gx-.042,gy-.063,gz+.05),.0035,ORANGE,8)
cylinder('Gauge | needle spindle',(gx,gy-.065,gz),.009,.01,GRAPHITE,(0,-1,0),16,.001)

# A small identification plate and modeled text remain simple mesh geometry.
box('Pump house | identification plate',(-.53,-1.231,2.34),(.30,.024,.095),GRAPHITE,.012)
bpy.ops.object.text_add(location=(-.53,-1.247,2.315), rotation=(math.pi/2,0,0))
text_obj=bpy.context.object
text_obj.data.body='P-02'
text_obj.data.align_x='CENTER'
text_obj.data.size=.065
text_obj.data.extrude=.0008
text_obj.data.bevel_depth=.0003
text_obj.data.materials.append(IVORY)
bpy.ops.object.convert(target='MESH')
finish(bpy.context.object,'Pump house | P-02 embossed identification',None)

# Warm enclosed entry beacon with actual cage bars.
box('Entry lamp | wall backplate',(.12,-1.235,2.59),(.17,.06,.25),GRAPHITE,.032)
cylinder('Entry lamp | amber lens',(.12,-1.31,2.59),.062,.18,AMBER,vertices=32,edge=.023)
for z in [2.50,2.68]:
    cylinder('Entry lamp | cap',(.12,-1.31,z),.076,.025,GRAPHITE,vertices=32,edge=.007)
for i in range(6):
    a=math.tau*i/6
    rod('Entry lamp | guard bar',(.12+.069*math.cos(a),-1.31+.069*math.sin(a),2.51),(.12+.069*math.cos(a),-1.31+.069*math.sin(a),2.67),.006,GRAPHITE,8)

# Continuous thick loop with rounded elbows around the pump house.
main_points=[(-2.48,-1.12,.47),(-2.48,-1.12,.94),(-1.25,-1.12,.94),(-1.25,-1.12,2.99),(1.25,-1.12,2.99),(1.25,-1.12,.94),(2.48,-1.12,.94),(2.48,-1.12,.47)]
main=tube('Pipe | continuous front pump manifold',main_points,.151,SAGE,.285,24)
main['route']='Left foundation inlet -> left riser -> overhead header -> right riser -> right foundation outlet'
tube('Pipe | tall tank supply to overhead tee',[(-.88,-.305,3.83),(-.88,-1.12,3.83),(-.88,-1.12,2.99)],.15,SAGE,.285,24)
cylinder('Pipe | tall tank outlet welded nozzle',(-.88,-.342,3.83),.215,.14,SAGE_EDGE,(0,-1,0),48,.018)
flange('Pipe | tall tank outlet',(-.88,-.47,3.83),(0,-1,0),.15)
valve('Valve | tall tank isolation',(-.88,-1.12,3.39),(0,0,1),(0,-1,0),.15)
cylinder('Pipe | overhead tee collar',(-.88,-1.12,3.055),.171,.12,SAGE_EDGE,(0,0,1),40,.012)
flange('Pipe | overhead coupling',(.36,-1.12,2.99),(1,0,0),.151)
for side in [-1,1]:
    valve('Valve | '+('left intake' if side<0 else 'right discharge'),(side*1.88,-1.12,.94),(1,0,0),(0,-1,0),.151)
    flange(f'Pipe | riser service coupling {side:+d}',(side*1.25,-1.12,2.18),(0,0,1),.151,6,False)
    flange(f'Pipe | ground socket {side:+d}',(side*2.48,-1.12,.52),(0,0,1),.151,8,False)
    box(f'Pipe | socket concrete plinth {side:+d}',(side*2.48,-1.12,.46),(.45,.46,.08),CONCRETE,.035)
    box(f'Pipe | valve support block {side:+d}',(side*1.88,-1.12,.53),(.30,.31,.22),CONCRETE,.025)
    rod(f'Pipe | valve support leg {side:+d}',(side*1.88,-1.12,.64),(side*1.88,-1.12,.77),.055,GRAPHITE,16)

# Rear balance connection has a complete intelligible route on the reverse view.
tube('Pipe | rear tank balance line',[(-1.55,1.77,1.03),(-1.55,2.07,1.03),(1.55,2.07,1.03),(1.55,1.66,1.03)],.125,SAGE,.17,24)
for x,y in [(-1.55,1.85),(1.55,1.79)]:
    flange('Pipe | rear vessel coupling '+str(x),(x,y,1.03),(0,1,0),.125,8,False)
valve('Valve | rear balance isolation',(0,2.07,1.03),(1,0,0),(0,1,0),.125)
for x in [-.75,.75]:
    box('Rear pipe | concrete saddle',(x,2.07,.53),(.25,.30,.22),CONCRETE,.025)
    rod('Rear pipe | support stem',(x,2.07,.64),(x,2.07,.90),.045,GRAPHITE,16)

# Separate slim level/overflow line follows the outside of the short vessel.
tube('Tank B | overflow return pipe',[(2.31,-.02,3.57),(2.56,-.02,3.57),(2.56,-.02,.76),(2.34,-.02,.76)],.055,GRAPHITE,.11,16)
for z in [.91,1.89,3.22]:
    cylinder('Tank B | overflow clamp',(2.56,-.02,z),.077,.055,STEEL,vertices=32,edge=.006)
    rod('Tank B | overflow wall bracket',(2.56,-.02,z),(2.40,.05,z),.025,GRAPHITE,12)

# House right-side access panel, hinges and fasteners provide useful reverse detail.
box('Pump house | side maintenance panel',(1.024,-.44,1.77),(.035,.63,.84),SAGE_EDGE,.035)
box('Pump house | side panel recessed center',(1.046,-.44,1.77),(.024,.52,.71),SAGE,.026)
rod('Pump house | side panel pull',(1.076,-.33,1.68),(1.076,-.33,1.88),.016,GRAPHITE,12)
for y in [-.69,-.19]:
    for z in [1.43,2.11]:
        cylinder('Pump house | side panel screw',(1.065,y,z),.015,.015,STEEL,(1,0,0),12,.002)


# Bake manufactured bevels, retain useful separate components, and create UVs
# directly on the final mesh surfaces, including newly generated bevel faces.
print('GEOMETRY_COMPLETE', len(asset.objects), flush=True)
bpy.ops.object.select_all(action='DESELECT')
for o in list(asset.objects):
    if o.type!='MESH':
        raise RuntimeError('Non-mesh in ASSET: '+o.name)
    bpy.context.view_layer.objects.active=o
    o.select_set(True)
    for mod in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.validate(verbose=False)
    o.data.update()
    o.select_set(False)

# Each part gets an independent non-overlapping smart atlas. This is deliberate:
# material-driven game prop with individually editable mechanical components.
uv_start=time.perf_counter()
for i,o in enumerate(asset.objects):
    bpy.context.view_layer.objects.active=o
    o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.025,area_weight=.0,correct_aspect=True,scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    o.data.uv_layers.active.name='UVMap'
    o.select_set(False)
    if i%100==0:
        print('UV_PART', i, flush=True)
print('UV_COMPLETE_SECONDS',time.perf_counter()-uv_start,flush=True)

# Asset metadata in the saved scene is explicit and easy to inspect.
scene['asset_name']='water_station'
scene['authoring_front']='-Y'
scene['authoring_up']='Z'
scene['units']='meters'
scene['reference']='D:/github/AstraEffort/REF/Set01/water_station.png'
scene['primary_tank_count']=2
scene['service_stair_treads']=5
scene['uv_method']='Per-component smart projected unique islands, 0.025 normalized island margin.'
scene['materials']='Named solid PBR materials; no image textures or external files.'

# Studio is a separate non-exported collection.
floor=box('Studio floor',(0,0,-.055),(200,200,.10),GROUND,.0)
move_to(floor,studio)
floor['asset']='studio_only'
world=bpy.data.worlds.new('Warm studio world')
scene.world=world
world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.62,.65,.68,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.32


def area(name,loc,power,size,color,target):
    data=bpy.data.lights.new(name,'AREA')
    data.energy=power; data.shape='DISK'; data.size=size; data.color=color
    o=bpy.data.objects.new(name,data); studio.objects.link(o); o.location=loc
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    return o


area('Key | large warm softbox',(-5,-7,10),1500,6.0,(1.0,.91,.78),(0,0,2))
area('Fill | broad cool softbox',(6,-3,7),1050,5.0,(.82,.91,1.0),(0,0,2))
area('Rim | upper back softbox',(3,6,10),1900,5.0,(1,.94,.83),(0,0,2.5))

cam_data=bpy.data.cameras.new('Presentation orthographic camera')
cam=bpy.data.objects.new('Presentation orthographic camera',cam_data)
studio.objects.link(cam)
scene.camera=cam
cam_data.type='ORTHO'
cam_data.lens=48
cam_data.clip_start=.1; cam_data.clip_end=300
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=32
scene.cycles.use_denoising=True
scene.cycles.max_bounces=6
scene.cycles.diffuse_bounces=3
scene.cycles.glossy_bounces=3
scene.render.threads_mode='FIXED'
scene.render.threads=4
scene.render.resolution_x=1440
scene.render.resolution_y=1080
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGB'
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=.5
scene.view_settings.gamma=1.0


def all_bounds():
    return [o.matrix_world@Vector(p) for o in asset.objects for p in o.bound_box]


def setup_camera(location):
    cam.location=location
    cam.rotation_euler=(Vector((0,0,2.55))-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=10
    bpy.context.view_layer.update()
    local=[cam.matrix_world.inverted()@p for p in all_bounds()]
    mid=Vector(((min(p.x for p in local)+max(p.x for p in local))*.5,(min(p.y for p in local)+max(p.y for p in local))*.5,0))
    cam.location+=cam.rotation_euler.to_quaternion()@mid
    bpy.context.view_layer.update()
    proj=[world_to_camera_view(scene,cam,p) for p in all_bounds()]
    spanx=max(p.x for p in proj)-min(p.x for p in proj)
    spany=max(p.y for p in proj)-min(p.y for p in proj)
    cam.data.ortho_scale*=max(spanx,spany)/.82
    bpy.context.view_layer.update()


# Export only the ASSET collection's selected geometry, using native format axes.
setup_camera((-9.0,-14.0,8.2))
bpy.ops.object.select_all(action='DESELECT')
for o in asset.objects: o.select_set(True)
bpy.context.view_layer.objects.active=next(iter(asset.objects))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'water_station.glb'),export_format='GLB',use_selection=True,export_apply=True,
    export_yup=True,export_animations=False,export_cameras=False,export_lights=False,export_materials='EXPORT',export_texcoords=True,export_normals=True)
bpy.ops.export_scene.fbx(filepath=str(ROOT/'water_station.fbx'),use_selection=True,object_types={'MESH'},use_mesh_modifiers=True,
    apply_unit_scale=True,global_scale=1.0,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Y',axis_up='Z',
    add_leaf_bones=False,bake_anim=False,path_mode='AUTO',use_custom_props=True)

# Preserve a clean studio preview and editable component geometry in the blend.
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active=None
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'water_station.blend'))
render_manifest=[]
for name,location in [('hero',(-9,-14,8.2)),('rear',(9.8,14,8.3))]:
    setup_camera(location)
    scene.render.filepath=str(OUT/(name+'.png'))
    before=stamp(); rt=time.perf_counter()
    bpy.ops.render.render(write_still=True)
    render_manifest.append({'view':name,'file':'renders/'+name+'.png','started_at_utc':before,'finished_at_utc':stamp(),
        'render_seconds':time.perf_counter()-rt,'camera_location':list(cam.location),'camera_rotation_euler':list(cam.rotation_euler),
        'orthographic_scale':cam.data.ortho_scale,'resolution':[1440,1080],'engine':'Cycles CPU','samples':32,'denoising':True,'threads':4})
setup_camera((-9,-14,8.2))
scene.render.filepath=str(OUT/'hero.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'water_station.blend'))
(ROOT/'capture_manifest.json').write_text(json.dumps(render_manifest,indent=2),encoding='utf-8')
(ROOT/'build_record.json').write_text(json.dumps({'started_at_utc':START.isoformat(),'finished_at_utc':stamp(),'elapsed_seconds':time.perf_counter()-START_T,
    'blender_version':bpy.app.version_string,'asset_objects':len(asset.objects),'script':'build.py','renders':render_manifest},indent=2),encoding='utf-8')
print('BUILD_AND_RENDERS_COMPLETE',stamp(),flush=True)
