"""Arched Workshop — deterministic, private Blender 4.5 asset authoring.

Run with Blender --background --factory-startup --threads 4 --python build.py.
All scene and deliverable paths stay in this script's asset directory.
The supplied reference is interpreted as modeled geometry, never a billboard.
"""
import bpy
import bmesh
import math
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
ROOT.joinpath('renders').mkdir(exist_ok=True)
START = datetime.now(timezone.utc)
WORK_STARTED = '2026-10-23T09:37:09Z'
PI = math.pi

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for collection in list(bpy.data.collections):
    if collection.name != 'Collection':
        bpy.data.collections.remove(collection)
base = bpy.data.collections.get('Collection')
base.name = 'ASSET'
ASSET = base
STUDIO = bpy.data.collections.new('STUDIO')
bpy.context.scene.collection.children.link(STUDIO)

def assign_collection(obj, collection=ASSET):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)
    return obj

def material(name, color, roughness=.55, metallic=0.0, emission=None, transmission=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = roughness
    bs.inputs['Metallic'].default_value = metallic
    bs.inputs['Transmission Weight'].default_value = transmission
    if transmission:
        bs.inputs['IOR'].default_value = 1.46
        bs.inputs['Coat Weight'].default_value = .24
        bs.inputs['Coat Roughness'].default_value = .19
    if emission:
        bs.inputs['Emission Color'].default_value = (*emission[0], 1)
        bs.inputs['Emission Strength'].default_value = emission[1]
    return mat

M = {}
M['ivory'] = material('Ivory | warm mineral wall', (.63, .60, .50), .79)
M['ivory_l'] = material('Ivory | light panel variation', (.68, .65, .55), .80)
M['ivory_d'] = material('Ivory | shadow panel variation', (.585, .561, .475), .79)
M['arch'] = material('Ivory | cut arch fascia', (.76, .72, .60), .67)
M['joint'] = material('Masonry | recessed joint', (.31, .30, .26), .88)
M['sage'] = material('Sage | curved standing seam metal', (.125, .185, .151), .54, .18)
M['sage_l'] = material('Sage | raised seam edges', (.19, .255, .211), .50, .22)
M['sage_d'] = material('Sage | folded panel variation', (.112, .168, .137), .56, .18)
M['door'] = material('Sage | service door and utility casing', (.244, .301, .263), .59, .14)
M['steel'] = material('Graphite | painted steel', (.122, .137, .130), .43, .50)
M['steel_l'] = material('Graphite | trim edge', (.225, .241, .225), .40, .52)
M['shutter'] = material('Graphite | shutter slats', (.165, .181, .169), .53, .45)
M['shutter_alt'] = material('Graphite | alternate shutter slats', (.183, .195, .181), .51, .45)
M['black'] = material('Charcoal | rubber and shadow recess', (.038, .047, .043), .75)
M['orange'] = material('Ochre orange | tool cabinet enamel', (.65, .275, .075), .49, .18)
M['orange_l'] = material('Ochre orange | painted detail', (.82, .382, .115), .42, .14)
M['concrete'] = material('Concrete | cast foundation', (.37, .385, .365), .88)
M['concrete_l'] = material('Concrete | ramp and sill', (.49, .494, .447), .85)
M['floor'] = material('Interior | sealed concrete', (.30, .311, .274), .78)
M['wood'] = material('Interior | worn worktop', (.285, .221, .135), .74)
M['peg'] = material('Interior | tool board', (.235, .219, .157), .78)
M['glass'] = material('Glazing | smoked green inset glass', (.105, .151, .129), .18, .0, transmission=.68)
M['silver'] = material('Metal | fasteners and handles', (.38, .405, .38), .31, .74)
M['lamp'] = material('Light | warm practical lens', (.98, .76, .38), .33, emission=((1, .69, .30), 3.5))
M['strip'] = material('Light | interior strip diffuser', (.96, .81, .55), .37, emission=((1, .73, .40), 4.0))
M['mark'] = material('Floor | muted safety paint', (.60, .409, .095), .69)
M['label'] = material('Label | warm paper enamel', (.68, .658, .558), .66)

def activate(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def bevel(obj, amount=.025, segments=3):
    if amount > 0:
        # Stay below the collapse point on thin inserts and wedge ramp edges.
        dimensions = [v for v in obj.dimensions if v > 1e-7]
        edges = [(obj.data.vertices[e.vertices[0]].co-obj.data.vertices[e.vertices[1]].co).length for e in obj.data.edges]
        positive_edges = [v for v in edges if v > 1e-7]
        limits = [amount]
        if dimensions:
            limits.append(min(dimensions)*.42)
        if positive_edges:
            limits.append(min(positive_edges)*.42)
        mod = obj.modifiers.new('Real rounded edge', 'BEVEL')
        mod.width = min(limits)
        mod.segments = segments
        mod.limit_method = 'ANGLE'
        mod.angle_limit = math.radians(26)
    for face in obj.data.polygons:
        face.use_smooth = True
    normal = obj.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
    normal.keep_sharp = True
    normal.weight = 45
    return obj

def mesh_obj(name, vertices, faces, mat, rounded=0):
    mesh = bpy.data.meshes.new(name + ' mesh')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-7)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-8, edges=list(bm.edges))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    ASSET.objects.link(obj)
    obj.data.materials.append(mat)
    if rounded:
        bevel(obj, rounded)
    return obj

def box(name, loc, dim, mat, rounded=.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dim
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign_collection(obj)
    obj.data.materials.append(mat)
    if rounded:
        bevel(obj, rounded)
    return obj

def cyl(name, loc, radius, depth, mat, axis='Z', vertices=24, rounded=.008):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    if axis == 'X':
        obj.rotation_euler[1] = PI / 2
    elif axis == 'Y':
        obj.rotation_euler[0] = PI / 2
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign_collection(obj)
    obj.data.materials.append(mat)
    if rounded:
        bevel(obj, rounded, 2)
    return obj

def ball(name, loc, radius, mat, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=radius, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign_collection(obj)
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj

def tube(name, points, radius, mat, smooth=True):
    curve = bpy.data.curves.new(name + ' swept path', 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 10
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    curve.use_fill_caps = True
    if smooth:
        spline = curve.splines.new('BEZIER')
        spline.bezier_points.add(len(points)-1)
        for p, co in zip(spline.bezier_points, points):
            p.co = co
            p.handle_left_type = 'AUTO'
            p.handle_right_type = 'AUTO'
    else:
        spline = curve.splines.new('POLY')
        spline.points.add(len(points)-1)
        for p, co in zip(spline.points, points):
            p.co = (*co, 1)
    obj = bpy.data.objects.new(name, curve)
    ASSET.objects.link(obj)
    obj.data.materials.append(mat)
    activate(obj)
    bpy.ops.object.convert(target='MESH')
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj

def torus(name, loc, major, minor, mat, axis='Z'):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=24, minor_segments=8, location=loc)
    obj = bpy.context.object
    obj.name = name
    if axis == 'X':
        obj.rotation_euler[1] = PI / 2
    elif axis == 'Y':
        obj.rotation_euler[0] = PI / 2
    assign_collection(obj)
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj

def rounded_rect(x0, x1, z0, z1, radius, steps=7):
    if isinstance(radius, (int, float)):
        radius = [radius] * 4
    points = []
    corners = [(x1-radius[0], z0+radius[0], -90, radius[0]),
               (x1-radius[1], z1-radius[1], 0, radius[1]),
               (x0+radius[2], z1-radius[2], 90, radius[2]),
               (x0+radius[3], z0+radius[3], 180, radius[3])]
    for cx, cz, ang, r in corners:
        for i in range(steps+1):
            a = math.radians(ang + 90*i/steps)
            points.append((cx + r*math.cos(a), cz + r*math.sin(a)))
    return points

def ring(name, outer, inner, front, back, mat, plane='XZ', rounded=.012):
    n = len(outer)
    assert len(inner) == n
    def xyz(p, depth):
        return (p[0], depth, p[1]) if plane == 'XZ' else (depth, p[0], p[1])
    vertices = [xyz(p, d) for d in (front, back) for outline in (outer, inner) for p in outline]
    faces = []
    for i in range(n):
        j = (i+1) % n
        faces += [(i, j, n+j, n+i), (2*n+i, 3*n+i, 3*n+j, 2*n+j),
                  (i, 2*n+i, 2*n+j, j), (n+i, n+j, 3*n+j, 3*n+i)]
    return mesh_obj(name, vertices, faces, mat, rounded)

def extruded_profile(name, points, front, back, mat, rounded=0):
    n = len(points)
    vertices = [(x, y, z) for y in (front, back) for x, z in points]
    faces = [tuple(range(n-1, -1, -1)), tuple(range(n, 2*n))]
    faces.extend((i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n))
    return mesh_obj(name, vertices, faces, mat, rounded)

HALF = 3.35
EAVE = 3.27
RISE = 1.06
R = (HALF*HALF + RISE*RISE)/(2*RISE)
ZC = EAVE+RISE-R
TH = math.asin(HALF/R)
YF, YB = -2.5, 2.5

def roof_z(x, offset=0):
    return ZC + math.sqrt((R+offset)**2 - x*x)

def arch_band(name, y0, y1, rout, rin, a0, a1, mat, segments=64, rounded=.009):
    angles = [a0 + (a1-a0)*i/segments for i in range(segments+1)]
    n = len(angles)
    vertices = [(r*math.sin(a), y, ZC+r*math.cos(a)) for y in (y0, y1) for r in (rout, rin) for a in angles]
    faces = []
    for i in range(n-1):
        j = i+1
        faces += [(i, j, 2*n+j, 2*n+i), (n+i, 3*n+i, 3*n+j, n+j),
                  (i, n+i, n+j, j), (2*n+i, 2*n+j, 3*n+j, 3*n+i)]
    faces += [(0, 2*n, 3*n, n), (n-1, 2*n-1, 4*n-1, 3*n-1)]
    return mesh_obj(name, vertices, faces, mat, rounded)

def panel_span(name, xr, yr, zr, orient, grid=1.0):
    a, b = (xr if orient == 'front' else yr)
    count = max(1, math.ceil((b-a)/grid))
    mats = [M['ivory'], M['ivory_l'], M['ivory'], M['ivory_d']]
    for i in range(count):
        u0 = a+(b-a)*i/count+.003
        u1 = a+(b-a)*(i+1)/count-.003
        if orient == 'front':
            loc = ((u0+u1)/2, sum(yr)/2, sum(zr)/2)
            dim = (u1-u0, yr[1]-yr[0], zr[1]-zr[0]-.006)
        else:
            loc = (sum(xr)/2, (u0+u1)/2, sum(zr)/2)
            dim = (xr[1]-xr[0], u1-u0, zr[1]-zr[0]-.006)
        box(name+' panel %02d' % i, loc, dim, mats[i%len(mats)], .014)

# Cast foundation, structural floor and actual sloping ramp.
box('Foundation | rounded cast slab', (0, 0, .14), (7.12, 5.43, .28), M['concrete'], .065)
box('Interior | continuous floor slab', (0, 0, .291), (6.48, 4.84, .065), M['floor'], .025)
for x in (-2.55, -1.1, .55, 2.2):
    box('Foundation | front panel joint', (x, -2.719, .145), (.009, .009, .22), M['joint'], .002)
for y in (-1.5, 0, 1.5):
    box('Foundation | left panel joint', (-3.564, y, .145), (.009, .009, .22), M['joint'], .002)
    box('Foundation | right panel joint', (3.564, y, .145), (.009, .009, .22), M['joint'], .002)
rampverts = [(-2.20,-2.71,.285),(1.72,-2.71,.285),(1.88,-3.68,.025),(-2.36,-3.68,.025),
             (-2.20,-2.71,.015),(1.72,-2.71,.015),(1.88,-3.68,.015),(-2.36,-3.68,.015)]
mesh_obj('Entry | poured tapered concrete ramp', rampverts, [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)], M['concrete_l'], .012)
for t in (.12,.29,.46,.63,.80):
    y = -2.71-.97*t
    z = .285-.26*t+.003
    box('Ramp | transverse traction groove', (-.24, y, z), (3.90+.20*t,.009,.006), M['concrete'], .002)

# Front wall has a true garage aperture and separate personnel-door aperture.
for z0,z1 in ((.28,1.20),(1.20,2.20),(2.20,3.22)):
    panel_span('Front left masonry', (-3.35,-2.18), (-2.5,-2.27),(z0,z1),'front')
    panel_span('Front central masonry', (1.61,1.99),(-2.5,-2.27),(z0,z1),'front')
    panel_span('Front right masonry',(2.91,3.35),(-2.5,-2.27),(z0,z1),'front')
panel_span('Garage lintel',(-2.18,1.61),(-2.5,-2.27),(2.97,3.22),'front',1.2)
panel_span('Personnel door head',(1.99,2.91),(-2.5,-2.27),(2.35,3.22),'front',1)

# The left wall is split around the long, genuinely inset window opening.
for z0,z1 in ((.28,1.09),(1.09,1.57),(2.61,3.22)):
    panel_span('Left masonry band',(-3.35,-3.12),(-2.27,2.5),(z0,z1),'side',1.2)
for ya,yb in ((-2.27,-1.91),(1.91,2.5)):
    panel_span('Left window pier',(-3.35,-3.12),(ya,yb),(1.57,2.61),'side',1.0)

# Right-side service windows have their own through-opening.
for z0,z1 in ((.28,1.15),(1.15,1.95),(2.68,3.22)):
    panel_span('Right masonry band',(3.12,3.35),(-2.27,2.5),(z0,z1),'side',1.18)
for ya,yb in ((-2.27,-.7),(1.85,2.5)):
    panel_span('Right window pier',(3.12,3.35),(ya,yb),(1.95,2.68),'side',1.15)

# Back wall and a functional rear service door.
for z0,z1 in ((.28,1.20),(1.20,2.25),(2.25,3.22)):
    panel_span('Rear masonry',(-3.35,1.96),(2.27,2.5),(z0,z1),'front',1.18)
    panel_span('Rear door right pier',(2.84,3.35),(2.27,2.5),(z0,z1),'front',1)
panel_span('Rear door head',(1.96,2.84),(2.27,2.5),(2.30,3.22),'front',1)

# Reinforced rounded building corners and low durable skirting stones.
for x in (-3.29,3.29):
    for y in (-2.44,2.44):
        box('Masonry | rounded corner return', (x,y,1.755),(.18,.19,2.95),M['ivory_l'],.07)
for x0,x1 in ((-3.35,-2.18),(1.61,1.99),(2.91,3.35)):
    box('Front | foundation plinth block',((x0+x1)/2,-2.532,.42),(x1-x0,.1,.28),M['concrete_l'],.022)
for side in (-1,1):
    box('Side | protective plinth course',(side*3.382,.015,.42),(.105,4.98,.28),M['concrete_l'],.025)

# Real curved metal roof sheet and standing seams, each following the barrel.
arch_band('Roof | continuous thick barrel vault', -2.59,2.59,R,R-.075,-TH,TH,M['sage'],64,.008)
for i in range(17):
    y = -2.50+i*(5/16)
    arch_band('Roof | standing seam %02d' % (i+1), y-.016,y+.016,R+.035,R-.005,-TH,TH,M['sage_l'],64,.006)
    if i % 4 == 1:
        arch_band('Roof | subtle adjacent sheet fold %02d' % i,y+.026,y+.108,R+.004,R-.002,-TH,TH,M['sage_d'],48,.002)

# Front and back thick segmented arch fascia, with actual tiny joints.
for end,y0,y1 in (('front',-2.73,-2.48),('rear',2.48,2.72)):
    for i in range(11):
        gap = .0008
        a0 = -TH+2*TH*i/11+gap
        a1 = -TH+2*TH*(i+1)/11-gap
        arch_band('Fascia | %s ivory arch stone %02d' % (end,i+1),y0,y1,R+.07,R-.225,a0,a1,M['arch'],8,.017)

gable_half = math.sqrt((R-.205)**2-(3.20-ZC)**2)
frontgable = [(-gable_half,3.175),(gable_half,3.175)]
frontgable += [(x,roof_z(x,-.205)) for x in [gable_half-i*(2*gable_half/48) for i in range(49)]]
extruded_profile('Front | sage vaulted gable infill',frontgable,-2.535,-2.33,M['sage_d'],.005)
extruded_profile('Rear | ivory vaulted masonry gable',frontgable,2.30,2.515,M['ivory'],.006)
for i in range(15):
    x = -3.12+i*(6.24/14)
    top = roof_z(x,-.215)
    if top > 3.20:
        box('Front gable | vertical folded seam %02d' % i,(x,-2.555,(3.18+top)/2),(.018,.021,top-3.18),M['sage_l'],.004)
box('Front gable | metal drip flashing',(0,-2.56,3.19),(6.58,.085,.07),M['steel'],.016)
box('Rear gable | stone sill joint',(0,2.527,3.195),(6.58,.016,.012),M['joint'],.002)
for x in (-2.36,-1.18,0,1.18,2.36):
    top = roof_z(x,-.23)
    box('Rear gable | vertical block joint',(x,2.525,(3.22+top)/2),(.006,.008,top-3.22),M['joint'],.001)

# Garage reveal and rounded frame. Nothing spans the open lower aperture.
garage_outer = rounded_rect(-2.31,1.76,.275,3.08,[.045,.27,.27,.045])
garage_inner = rounded_rect(-2.135,1.585,.303,2.905,[.025,.17,.17,.025])
ring('Garage | sculpted graphite surround',garage_outer,garage_inner,-2.635,-2.37,M['steel_l'],rounded=.016)
ring('Garage | inner weather seal',rounded_rect(-2.137,1.587,.30,2.91,[.025,.17,.17,.025]),rounded_rect(-2.094,1.544,.308,2.865,[.02,.15,.15,.02]),-2.59,-2.35,M['black'],rounded=.004)
for x in (-2.075,1.525):
    box('Shutter | recessed vertical guide channel',(x,-2.30,1.57),(.065,.10,2.52),M['steel'],.012)
    for z in (.46,1.48,2.48):
        cyl('Guide | mounting bolt',(x,-2.374,z),.018,.018,M['silver'],'Y',12,.003)

SHUTTER_BOTTOM = 1.78
top = 2.87
pitch = .0865
n = math.ceil((top-SHUTTER_BOTTOM)/pitch)
for i in range(n):
    z = SHUTTER_BOTTOM+(i+.5)*(top-SHUTTER_BOTTOM)/n
    box('Shutter | articulated horizontal slat %02d'%i,(-.275,-2.398,z),(3.58,.080,(top-SHUTTER_BOTTOM)/n-.010),M['shutter_alt' if i%4==0 else 'shutter'],.012)
    box('Shutter | slat folded lower lip %02d'%i,(-.275,-2.446,z-.028),(3.54,.011,.011),M['steel'],.004)
box('Shutter | heavy bottom rail',(-.275,-2.403,SHUTTER_BOTTOM),(3.61,.104,.095),M['steel_l'],.018)
for x in (-1.95,1.40):
    box('Shutter | amber corner marker',(x,-2.461,SHUTTER_BOTTOM),(.12,.012,.031),M['orange_l'],.004)
for x in (-1.88,-.83,.28,1.34):
    cyl('Shutter | bottom rail rivet',(x,-2.465,SHUTTER_BOTTOM-.02),.009,.009,M['silver'],'Y',12,.002)
cyl('Shutter | concealed roll drum',(-.275,-2.08,2.96),.16,3.66,M['steel'],'X',32,.01)

def service_door(name, x, y, rear=False):
    sign = 1 if rear else -1
    ring(name+' | rounded steel jamb',rounded_rect(x-.47,x+.47,.28,2.37,.06),rounded_rect(x-.405,x+.405,.303,2.303,.03),y+sign*.08,y-sign*.10,M['steel'],rounded=.012)
    box(name+' | sage slab',(x,y,1.302),(.792,.08,1.998),M['door'],.025)
    fy = y+sign*.049
    box(name+' | recessed lower field',(x,fy,1.20),(.66,.016,1.60),M['sage_d'],.017)
    box(name+' | inner field',(x,fy+sign*.009,1.20),(.615,.012,1.55),M['door'],.012)
    if not rear:
        ring(name+' | narrow vision-light frame',rounded_rect(x-.11,x+.11,1.35,2.02,.025),rounded_rect(x-.074,x+.074,1.389,1.982,.015),fy+sign*.035,fy,M['steel_l'],rounded=.006)
        box(name+' | inset narrow glazing',(x,fy+sign*.012,1.685),(.147,.017,.593),M['glass'],.008)
    hx = x-.267
    box(name+' | handle escutcheon',(hx,fy+sign*.03,1.10),(.075,.035,.19),M['steel'],.016)
    tube(name+' | lever handle',[(hx,fy+sign*.07,1.16),(hx,fy+sign*.11,1.16),(hx+.12,fy+sign*.11,1.16)],.016,M['silver'])
    cyl(name+' | lock cylinder',(hx,fy+sign*.055,1.04),.019,.015,M['silver'],'Y',16,.002)
    for z in (.66,1.95):
        cyl(name+' | barrel hinge',(x+.375,fy,z),.025,.14,M['steel_l'],'Z',16,.004)
    box(name+' | brushed kick plate',(x,fy+sign*.014,.43),(.70,.015,.16),M['steel_l'],.009)

service_door('Front personnel door',2.45,-2.515)
service_door('Rear maintenance door',2.40,2.515,True)

def side_window(name, side, ua, ub, z0, z1, panes):
    outer = rounded_rect(ua,ub,z0,z1,.14)
    inner = rounded_rect(ua+.075,ub-.075,z0+.075,z1-.075,.085)
    x = side*3.36
    ring(name+' | ivory recess surround',rounded_rect(ua-.07,ub+.07,z0-.07,z1+.07,.18),outer,x+side*.018,x-side*.11,M['ivory_l'],'YZ',.013)
    ring(name+' | rounded graphite glazing frame',outer,inner,x+side*.047,x-side*.13,M['steel'],'YZ',.013)
    usable = (ub-ua-.15)/panes
    for i in range(panes):
        u = ua+.075+usable*(i+.5)
        box(name+' | inset glass pane %02d'%i,(x-side*.05,u,(z0+z1)/2),(.022,usable-.038,z1-z0-.165),M['glass'],.009)
        if i < panes-1:
            box(name+' | metal mullion %02d'%i,(x+side*.026,ua+.075+usable*(i+1),(z0+z1)/2),(.085,.049,z1-z0-.11),M['steel_l'],.009)
    box(name+' | deep stone sill',(x+side*.025,(ua+ub)/2,z0-.07),(.23,ub-ua+.12,.075),M['arch'],.02)

side_window('Left long window band',-1,-1.91,1.91,1.57,2.61,5)
side_window('Right service window band',1,-.7,1.85,1.95,2.68,3)

# Side-mounted ventilated service unit; slats are separate angled solids.
box('HVAC | wall-mounted sage service casing',(-3.525,.95,.965),(.32,1.16,1.31),M['door'],.055)
box('HVAC | dark grille recess',(-3.696,.95,1.03),(.025,.94,1.02),M['black'],.025)
for i in range(9):
    z = .60+i*.103
    slat = box('HVAC | angled louver %02d'%i,(-3.729,.95,z),(.067,.92,.054),M['steel_l'],.008)
    slat.rotation_euler[1] = math.radians(-23)
for y in (.46,1.44):
    for z in (.39,1.52):
        cyl('HVAC | casing fastener',(-3.701,y,z),.018,.014,M['silver'],'X',12,.003)
box('HVAC | lower access panel',(-3.704,.95,.425),(.022,.94,.16),M['door'],.015)

# Orange/graphite exterior tool storage matches the reference's side placement.
box('Exterior tools | rounded steel body',(-3.56,-1.05,.94),(.44,.97,1.27),M['steel'],.045)
box('Exterior tools | dark drawer bank',(-3.794,-1.30,.96),(.027,.415,1.15),M['black'],.008)
for i in range(5):
    z = .59+i*.17
    box('Exterior tools | drawer %02d'%i,(-3.817,-1.30,z),(.031,.385,.143),M['shutter'],.011)
    box('Exterior tools | orange pull %02d'%i,(-3.841,-1.30,z+.043),(.035,.31,.023),M['orange_l'],.008)
box('Exterior tools | orange full-height cabinet door',(-3.813,-.835,.96),(.045,.45,1.18),M['orange'],.019)
box('Exterior tools | door handle',(-3.851,-1.008,1.05),(.035,.024,.16),M['silver'],.006)
for z in (.47,.52,.57,.62):
    box('Exterior tools | door lower ventilation slot',(-3.840,-.80,z),(.008,.18,.013),M['black'],.004)
box('Exterior tools | small enamel label',(-3.842,-.84,1.45),(.012,.20,.052),M['label'],.007)
for y in (-1.39,-.72):
    for z in (.40,1.49):
        cyl('Exterior tools | panel screw',(-3.844,y,z),.009,.008,M['silver'],'X',12,.002)
for y in (-1.36,-.74):
    box('Exterior tools | raised foot',(-3.55,y,.33),(.30,.10,.10),M['black'],.014)

# Gutter half-tubes with real hollow trough profile.
def gutter(name,x,y0,y1,z):
    n = 20
    angles = [PI+i*PI/n for i in range(n+1)]
    pts = [(x+.112*math.cos(a),z+.112*math.sin(a)) for a in angles]
    pts += [(x+.083*math.cos(a),z+.083*math.sin(a)) for a in reversed(angles)]
    return extruded_profile(name,pts,y0,y1,M['steel_l'],.005)

for side in (-1,1):
    gx = side*3.39
    gutter('Drainage | %s hollow eave gutter'%side,gx,-2.62,2.61,3.285)
    for y in (-2.57,-1.75,-.85,.05,.95,1.85,2.57):
        box('Gutter | external retention strap',(gx,y,3.228),(.255,.032,.145),M['steel'],.022)
    for y in (-2.43,2.43):
        px = side*3.44
        tube('Drainage | downpipe and curved shoe',[(gx,y,3.25),(gx,y,3.06),(px,y,2.92),(px,y,.62),(px,y,.43),(px+side*.12,y,.32),(px+side*.12,y,.225)],.054,M['steel_l'])
        for z in (.66,1.87,2.83):
            cyl('Downpipe | clamping collar',(px,y,z),.072,.065,M['steel'],'Z',20,.006)
            box('Downpipe | masonry saddle',(side*3.385,y,z),(.12,.12,.075),M['steel'],.01)
        if y < 0:
            tube('Drainage | ochre protective guard',[(px-side*.20,y-.04,.38),(px-side*.20,y-.04,1.33)],.041,M['orange'])
            for z in (.54,1.22):
                cyl('Guard | dark restraint collar',(px-side*.20,y-.04,z),.048,.045,M['steel'],'Z',20,.005)

# Rear ventilation grille with a genuine raised frame and inclined blades.
box('Rear vent | deep dark recess',(0,2.557,3.32),(1.52,.13,.76),M['black'],.038)
ring('Rear vent | steel outer bezel',rounded_rect(-.80,.80,2.90,3.74,.035),rounded_rect(-.70,.70,2.99,3.65,.02),2.655,2.54,M['steel_l'],rounded=.012)
for i in range(7):
    blade = box('Rear vent | angled louver %02d'%i,(0,2.65,3.035+i*.091),(1.39,.09,.046),M['steel'],.008)
    blade.rotation_euler[0] = math.radians(21)

# A compact roof exhaust monitor, seated on the curved sheet.
vx,vy = -1.93,1.39
vz = roof_z(vx)
box('Roof exhaust | flashed curb',(vx,vy,vz+.035),(.88,.80,.11),M['steel_l'],.035)
box('Roof exhaust | dark plenum',(vx,vy,vz+.245),(.69,.61,.37),M['black'],.03)
for side in (-1,1):
    for i in range(4):
        z = vz+.12+i*.077
        box('Roof exhaust | end louver',(vx,vy+side*.33,z),(.68,.09,.039),M['steel_l'],.006)
        box('Roof exhaust | side louver',(vx+side*.37,vy,z),(.09,.60,.039),M['steel_l'],.006)
for sx in (-1,1):
    for sy in (-1,1):
        box('Roof exhaust | corner post',(vx+sx*.37,vy+sy*.32,vz+.247),(.061,.062,.37),M['steel_l'],.008)
box('Roof exhaust | folded cap',(vx,vy,vz+.451),(.86,.77,.095),M['steel_l'],.028)

# Practical gooseneck lamps, with modeled bell reflectors and emissive lenses.
def bell(name,x,y,z):
    profile = [(0,.095),(.049,.095),(.058,.058),(.083,.025),(.127,-.032),(.153,-.041),(.153,-.060),(.139,-.064),(.108,-.014),(.061,.047),(0,.047)]
    verts=[]
    segments=32
    for r,h in profile:
        verts.extend((x+r*math.cos(2*PI*i/segments),y+r*math.sin(2*PI*i/segments),z+h) for i in range(segments))
    faces=[]
    for row in range(len(profile)-1):
        for i in range(segments):
            faces.append((row*segments+i,row*segments+(i+1)%segments,(row+1)*segments+(i+1)%segments,(row+1)*segments+i))
    obj=mesh_obj(name,verts,faces,M['steel'],.003)
    cyl(name+' | warm recessed lens',(x,y,z-.045),.121,.013,M['lamp'],'Z',32,.003)
    return obj

def add_area(name,loc,target,energy,size,color):
    light=bpy.data.lights.new(name,'AREA')
    light.energy=energy
    light.shape='DISK'
    light.size=size
    light.color=color
    obj=bpy.data.objects.new(name,light)
    STUDIO.objects.link(obj)
    obj.location=loc
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    return obj

for x in (-2.79,2.45):
    cyl('Lamp | wall mounting rosette',(x,-2.545,2.99),.074,.055,M['steel'],'Y',24,.01)
    tube('Lamp | curved gooseneck arm',[(x,-2.575,2.995),(x,-2.61,3.12),(x,-2.75,3.13),(x,-2.86,3.035)],.024,M['steel'])
    bell('Lamp | spun metal bell shade',x,-2.86,2.97)
    add_area('Practical lamp warm wash', (x,-2.87,2.88),(x,-2.48,1.85),26,.20,(1,.68,.35))

box('Front sign | dark rounded lightbox',(2.45,-2.57,2.62),(1.04,.17,.36),M['steel_l'],.055)
box('Front sign | ivory illuminated face',(2.45,-2.665,2.62),(.91,.025,.25),M['lamp'],.035)

def text_mesh(name,body,loc,size,mat,rotation=(PI/2,0,0),extrude=.0008):
    font=bpy.data.curves.new(name+' letters','FONT')
    font.body=body
    font.align_x='CENTER'
    font.align_y='CENTER'
    font.size=size
    font.extrude=extrude
    font.bevel_depth=.0004
    font.resolution_u=4
    obj=bpy.data.objects.new(name,font)
    ASSET.objects.link(obj)
    obj.location=loc
    obj.rotation_euler=rotation
    obj.data.materials.append(mat)
    activate(obj)
    bpy.ops.object.convert(target='MESH')
    return obj

text_mesh('Front sign | raised SERVICE letters','SERVICE',(2.45,-2.682,2.617),.112,M['steel'])
box('Front | small workshop number plaque',(-2.81,-2.535,2.39),(.24,.027,.16),M['steel'],.018)
text_mesh('Front | unit number 07','07',(-2.81,-2.551,2.39),.105,M['label'])

# Rear electrical service box, conduits and realistic mounting hardware.
box('Rear electrical | cast junction enclosure',(3.045,2.588,.97),(.29,.20,.57),M['steel_l'],.032)
box('Rear electrical | inset meter window',(3.045,2.701,1.10),(.19,.022,.16),M['glass'],.017)
box('Rear electrical | fuse access panel',(3.045,2.701,.855),(.20,.021,.19),M['steel'],.012)
for z in (.44,1.38):
    tube('Rear electrical | rigid wall conduit',[(3.045,2.56,z),(3.045,2.56,z+.29)],.018,M['steel_l'],False)
for z in (.49,1.55):
    box('Rear electrical | conduit clamp',(3.045,2.585,z),(.08,.035,.027),M['steel'],.006)
for x in (-2.5,-1.35,-.2,.95):
    for z in (.72,2.71):
        cyl('Rear masonry | inset anchor',(x,2.514,z),.014,.009,M['ivory_d'],'Y',12,.002)
for y in (-1.7,-.3,1.15,2.2):
    for z in (.82,2.9):
        cyl('Side masonry | inset fixing',(-3.363,y,z),.013,.009,M['ivory_d'],'X',12,.002)

# Interior: a visible near-side tool bank, rear workbench, shelves and tools.
box('Interior | rear workbench cabinet carcass',(-.40,1.72,.70),(3.52,.67,.78),M['steel'],.025)
box('Interior | rear workbench timber top',(-.40,1.71,1.12),(3.66,.78,.10),M['wood'],.035)
box('Interior | metal worktop edge',(-.40,1.305,1.11),(3.66,.04,.085),M['steel_l'],.01)
for j,x in enumerate((-1.68,-.82,.04,.90)):
    for k in range(4):
        z=.45+k*.17
        box('Interior workbench | drawer %d-%d'%(j,k),(x,1.367,z),(.77,.035,.142),M['orange' if j==3 else 'shutter'],.014)
        box('Interior workbench | horizontal pull %d-%d'%(j,k),(x,1.331,z+.03),(.40,.035,.025),M['silver'],.006)
box('Interior | wall tool board',(-.42,2.24,1.70),(3.60,.075,1.02),M['peg'],.018)
box('Interior | pegboard top ledge',(-.42,2.16,2.25),(3.72,.18,.065),M['steel'],.016)
for col in range(12):
    for row in range(3):
        cyl('Tool board | recessed peg point',(-2.0+col*.28,2.197,1.37+row*.27),.010,.008,M['black'],'Y',8,.001)
for i in range(5):
    x=-1.62+i*.36
    z=1.71+(i%2)*.10
    box('Tool board | hanging spanner shaft',(x,2.155,z),(.035,.03,.32),M['silver'],.007)
    torus('Tool board | ring spanner head',(x,2.153,z+.18),.047,.013,M['silver'],'Y')
    box('Tool board | spanner lower jaw',(x,2.152,z-.18),(.075,.032,.064),M['silver'],.01)
for i in range(3):
    x=.37+i*.24
    cyl('Tool board | screwdriver handle',(x,2.14,1.53),.032,.14,M['orange'],'Z',16,.005)
    cyl('Tool board | screwdriver steel shaft',(x,2.14,1.71),.008,.22,M['silver'],'Z',12,.002)

# Near-left bench is intentionally within the shutter sightline.
box('Interior | left tool cabinet',(-1.40,-.34,.77),(1.10,.62,.89),M['steel'],.028)
box('Interior | left tool cabinet worktop',(-1.40,-.34,1.25),(1.16,.69,.085),M['wood'],.025)
for i in range(5):
    z=.43+i*.164
    box('Interior | left cabinet drawer %02d'%i,(-1.40,-.665,z),(1.01,.04,.14),M['orange' if i==0 else 'shutter'],.013)
    box('Interior | left cabinet drawer handle %02d'%i,(-1.40,-.70,z+.025),(.61,.035,.026),M['silver'],.005)
box('Interior | right orange tool chest',(.99,.10,.78),(.71,.66,.94),M['orange'],.033)
box('Interior | right chest top',(.99,.10,1.28),(.78,.72,.065),M['steel'],.022)
for i in range(4):
    z=.49+i*.20
    box('Interior | right chest drawer',(.99,-.248,z),(.62,.033,.16),M['orange_l'],.012)
    box('Interior | right chest pull',(.99,-.278,z+.028),(.31,.032,.025),M['steel'],.007)

# Bench vice, small bottles and a storage rack add readable interior depth.
box('Interior | vice base',(-1.39,-.31,1.34),(.28,.23,.09),M['steel_l'],.017)
box('Interior | vice fixed jaw',(-1.39,-.24,1.45),(.25,.06,.18),M['steel_l'],.014)
box('Interior | vice movable jaw',(-1.39,-.43,1.45),(.25,.06,.15),M['steel_l'],.014)
cyl('Interior | vice screw',(-1.39,-.49,1.37),.024,.23,M['silver'],'Y',16,.004)
cyl('Interior | vice sliding handle',(-1.39,-.62,1.37),.010,.25,M['silver'],'Z',12,.002)
for i in range(3):
    cyl('Interior | worktop consumable tin',(-.94+i*.17,1.62,1.25),.054,.16,M['orange' if i==1 else 'steel_l'],'Z',20,.007)
    cyl('Interior | tin lid',(-.94+i*.17,1.62,1.34),.058,.02,M['steel'],'Z',20,.003)
for x in (-2.86,-2.30):
    for y in (.58,1.55):
        box('Interior | shelving upright',(x,y,1.36),(.045,.045,2.02),M['steel'],.008)
for z in (.55,1.18,1.82,2.34):
    box('Interior | storage rack shelf',(-2.58,1.065,z),(.65,1.10,.06),M['steel_l'],.012)
for z in (.77,1.39):
    for y in (.78,1.25):
        box('Interior | shelf parts bin',(-2.58,y,z),(.46,.35,.32),M['door'],.02)
        box('Interior | bin label',(-2.338,y,z+.01),(.012,.12,.055),M['label'],.005)

# Factory-style interior lighting and restrained floor markings.
for y in (-.45,1.5):
    box('Interior light | steel strip housing',(-.25,y,3.13),(2.75,.18,.10),M['steel'],.025)
    box('Interior light | luminous diffuser',(-.25,y,3.075),(2.58,.13,.018),M['strip'],.008)
    add_area('Interior overhead strip illumination',(-.25,y,3.045),(-.25,y,.4),38,1.4 if y>1 else 2.1,(1,.78,.48))
box('Interior light | low task fixture',(-.43,2.095,2.13),(2.15,.12,.07),M['steel'],.015)
box('Interior light | low task diffuser',(-.43,2.015,2.122),(2.02,.028,.038),M['strip'],.008)
add_area('Interior workbench task illumination',(-.42,1.90,2.11),(-.42,1.4,.8),50,.60,(1,.76,.42))
for x in (-1.94,1.39):
    box('Interior floor | garage guide stripe',(x,-.80,.328),(.045,3.09,.005),M['mark'],.001)
box('Interior floor | rear stopping line',(-.275,.74,.328),(3.37,.044,.005),M['mark'],.001)

# Place the near tool bank within the raised-shutter hero sightline.
for obj in ASSET.objects:
    if obj.name.startswith('Interior | left') or obj.name.startswith('Interior | vice'):
        obj.location.x += .20
        obj.location.y -= .55

# Apply true geometry rounding and create a nondegenerate UV atlas per component.
print('ASSET_BUILD_GEOMETRY_COMPLETE', len(ASSET.objects), flush=True)
for index,obj in enumerate(list(ASSET.objects)):
    if obj.type != 'MESH':
        continue
    activate(obj)
    for mod in list(obj.modifiers):
        if mod.type != 'WEIGHTED_NORMAL':
            bpy.ops.object.modifier_apply(modifier=mod.name)
    # Weld duplicate lathe poles and dissolve numerical bevel remnants.
    bm=bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.set_sharp_from_angle(angle=math.radians(42))
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    if obj.data.uv_layers:
        for layer in list(obj.data.uv_layers):
            obj.data.uv_layers.remove(layer)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.015,area_weight=.45,correct_aspect=True,scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.uv_layers.active.name = 'UV0_ComponentAtlas'
    obj['asset_part'] = 'ARCHED_WORKSHOP'
    obj['uv_method'] = 'Applied geometry; angle-unwrapped component atlas; 0.015 normalized island margin'
    if index % 100 == 0:
        print('FINALIZE_MESH',index,flush=True)

# Warm, pale photography studio, excluded from all geometry exports.
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.length_unit='METERS'
scene.unit_settings.scale_length=1.0
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=32
scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED'
scene.render.threads=4
scene.render.resolution_x=1440
scene.render.resolution_y=1080
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.render.film_transparent=False
scene.world.color=(.18,.18,.18)
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.69,.70,.66,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.30
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'

studio_mat=material('STUDIO | pale warm seamless',(.63,.615,.572),.85)
floor=box('STUDIO | ground',(0,0,-.067),(200,200,.10),studio_mat,.005)
assign_collection(floor,STUDIO)
add_area('STUDIO | large soft key',(-5.5,-6.8,10.7),(0,0,1.6),1450,7.0,(1,.88,.73))
add_area('STUDIO | broad cool fill',(5,-3.0,7),(0,0,1.8),850,6,(.79,.88,1))
add_area('STUDIO | roof rim',(-1.5,6.5,9),(0,0,2.2),1350,5,(1,.94,.82))

def camera(name,loc,target,scale):
    data=bpy.data.cameras.new(name)
    data.type='ORTHO'
    data.ortho_scale=scale
    data.lens=50
    obj=bpy.data.objects.new(name,data)
    STUDIO.objects.link(obj)
    obj.location=loc
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    return obj

hero=camera('CAMERA | hero front left',(-9.8,-13.2,7.1),(0,-.22,2.1),11.4)
rear=camera('CAMERA | rear right',(10.2,12.2,7.6),(0,0,2.12),11.0)
detail=camera('CAMERA | low front opening',(-4.9,-15.7,4.15),(-.05,-.15,1.88),9.25)
scene.camera=hero

# Custom asset metadata kept with the editable native project.
scene['asset_name']='Arched Workshop'
scene['reference']='D:/github/AstraEffort/REF/Set01/arched_workshop.png'
scene['front_axis']='-Y'
scene['up_axis']='Z'
scene['authorship']='Independent Set01 arched_workshop assignment; geometry authored by script'
scene['material_limitations']='Solid named PBR materials; no baked textures. Smoked glazing is intentionally restrained.'

def select_asset():
    bpy.ops.object.select_all(action='DESELECT')
    for obj in ASSET.objects:
        if obj.type=='MESH':
            obj.select_set(True)
    bpy.context.view_layer.objects.active=next(obj for obj in ASSET.objects if obj.type=='MESH')

select_asset()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'arched_workshop.blend'))
print('NATIVE_SAVED',flush=True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'arched_workshop.glb'),export_format='GLB',use_selection=True,export_apply=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_cameras=False,export_lights=False)
print('GLB_EXPORTED',flush=True)
bpy.ops.export_scene.fbx(filepath=str(ROOT/'arched_workshop.fbx'),use_selection=True,object_types={'MESH'},use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,bake_anim=False,path_mode='AUTO')
print('FBX_EXPORTED',flush=True)

manifest={'asset':'arched_workshop','reference':str(Path('D:/github/AstraEffort/REF/Set01/arched_workshop.png')),'work_started_at_utc':WORK_STARTED,'build_started_at_utc':START.isoformat(),'engine':'Blender Cycles CPU','blender_version':bpy.app.version_string,'samples':32,'denoising':True,'resolution':[1440,1080],'threads':4,'color_management':'AgX / Medium High Contrast','units':'meters','up_axis':'Z','front_axis':'-Y','exports_geometry_only':True,'views':[]}
for view,cam in [('hero',hero),('rear',rear),('front_detail',detail)]:
    scene.camera=cam
    scene.render.filepath=str(ROOT/'renders'/f'{view}.png')
    started=datetime.now(timezone.utc)
    render_start=time.monotonic()
    bpy.ops.render.render(write_still=True)
    finished=datetime.now(timezone.utc)
    manifest['views'].append({'view':view,'path':f'renders/{view}.png','camera_location':list(cam.location),'camera_rotation_euler':list(cam.rotation_euler),'orthographic_scale':cam.data.ortho_scale,'started_at_utc':started.isoformat(),'finished_at_utc':finished.isoformat(),'render_seconds':time.monotonic()-render_start})
    ROOT.joinpath('capture_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print('RENDER_DONE',view,flush=True)

scene.camera=hero
select_asset()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'arched_workshop.blend'))
manifest['build_finished_at_utc']=datetime.now(timezone.utc).isoformat()
manifest['build_elapsed_seconds']=(datetime.now(timezone.utc)-START).total_seconds()
ROOT.joinpath('capture_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print('BUILD_FINISHED',manifest['build_finished_at_utc'],flush=True)
