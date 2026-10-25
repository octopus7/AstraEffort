"""Set05 original marine work assets. Run one slug per isolated Blender process.

Authoring only: no reopen/import, UV/geometry validator, or image review pass.
Coordinates: meters, Z up, front = -Y. All forms authored from primitives here.
"""
import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector, Quaternion

ROOT = Path(__file__).resolve().parent
ASSETS = ["catamaran_workboat", "underwater_service_robot", "docking_lift_platform", "marine_equipment_workshop"]
KST = timezone(timedelta(hours=9))
MATS = {}
COL = None
ASSET = None


def stamp():
    return datetime.now(timezone.utc).isoformat()


def rgb(hexcode):
    s = hexcode.lstrip("#")
    c = [int(s[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in c) + (1,)


def material(name, color, rough=.42, metal=0, emission=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = rgb(color)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = rgb(color)
    p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rough
    if emission:
        p.inputs["Emission Color"].default_value = rgb(color)
        p.inputs["Emission Strength"].default_value = emission
    MATS[name] = m
    return m


def palette():
    material("Hull_Teal", "41656B", .4, .28)
    material("Warm_White_Paint", "DEDACC", .44, .12)
    material("Ochre_Safety_Paint", "D5A844", .42, .18)
    material("Graphite_Mechanisms", "343E43", .4, .45)
    material("Brushed_Steel", "94A5A7", .3, .72)
    material("Rubber_Bumpers", "252D31", .63, .02)
    material("Muted_Glazing", "36545E", .2, .28)
    material("Deck_Nonslip", "677478", .65, .12)
    material("Pale_Concrete", "B6B7AC", .82, 0)
    material("Warm_Task_Lamp", "FFF0C6", .22, .12, 1.4)
    material("Navigation_Red", "A75D50", .3, .12)
    material("Navigation_Green", "76AFA2", .3, .12)


def init_scene(slug):
    global COL, ASSET
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    ASSET = bpy.data.collections.new("ASSET")
    bpy.context.scene.collection.children.link(ASSET)
    COL = ASSET
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1
    scene["asset_slug"] = slug
    scene["review_status"] = "deferred_by_user"
    scene["authoring_notes"] = "Original named-part mesh authoring. All studio geometry excluded from exports."
    palette()


def group(name):
    global COL
    COL = bpy.data.collections.new(name)
    ASSET.children.link(COL)


def assign(o, name, mat):
    o.name = name
    for c in list(o.users_collection):
        c.objects.unlink(o)
    COL.objects.link(o)
    if mat:
        o.data.materials.append(MATS[mat])
    o["part_name"] = name
    return o


def smooth(o, flat=False):
    for p in o.data.polygons:
        p.use_smooth = not flat


def bevel(o, width=.05, segments=3):
    if width <= 0:
        return o
    mod = o.modifiers.new("Soft manufactured edges", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.harden_normals = True
    wn = o.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
    wn.keep_sharp = True
    wn.weight = 50
    return o


def box(name, loc, dims, mat, radius=.05, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = assign(bpy.context.object, name, mat)
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if rot:
        o.rotation_euler = rot
    bevel(o, min(radius, min(dims) * .44))
    return o


def cyl(name, loc, radius, depth, mat, axis=(0, 0, 1), vertices=32, edge=.025):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, end_fill_type="NGON", location=loc)
    o = assign(bpy.context.object, name, mat)
    o.rotation_euler = Vector(axis).to_track_quat("Z", "Y").to_euler()
    for p in o.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    bevel(o, min(edge, depth*.2, radius*.2))
    return o


def sphere(name, loc, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=loc)
    o = assign(bpy.context.object, name, mat)
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    smooth(o)
    return o


def beam(name, a, b, width, depth, mat, radius=.025):
    a, b = Vector(a), Vector(b)
    o = box(name, (a+b)/2, (width, depth, (b-a).length), mat, radius)
    o.rotation_euler = (b-a).to_track_quat("Z", "Y").to_euler()
    return o


def rod(name, a, b, radius, mat, vertices=20):
    a, b = Vector(a), Vector(b)
    return cyl(name, (a+b)/2, radius, (b-a).length, mat, b-a, vertices, min(.018, radius*.25))


def tube(name, points, radius, mat, curved=False):
    cu = bpy.data.curves.new(name + ".Path", "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = 12
    cu.bevel_depth = radius
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER" if curved else "POLY")
    if curved:
        sp.bezier_points.add(len(points)-1)
        for p, co in zip(sp.bezier_points, points):
            p.co = co
            p.handle_left_type = "AUTO"
            p.handle_right_type = "AUTO"
    else:
        sp.points.add(len(points)-1)
        for p, co in zip(sp.points, points):
            p.co = (*co, 1)
    o = bpy.data.objects.new(name, cu)
    COL.objects.link(o)
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.convert(target="MESH")
    o = bpy.context.object
    o.data.materials.append(MATS[mat])
    o["part_name"] = name
    smooth(o)
    return o


def mesh(name, verts, faces, mat, edge=.03, shade=False):
    data = bpy.data.meshes.new(name + ".Mesh")
    data.from_pydata(verts, [], faces)
    # Establish consistent outward face orientation as part of mesh construction.
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    data.update()
    o = bpy.data.objects.new(name, data)
    COL.objects.link(o)
    data.materials.append(MATS[mat])
    o["part_name"] = name
    if shade:
        smooth(o)
    bevel(o, edge)
    return o


def ring(name, loc, outer, inner, length, mat, axis=(0,0,1), n=40):
    verts=[]
    for z,r in [(-length/2,outer),(length/2,outer),(-length/2,inner),(length/2,inner)]:
        verts += [(r*math.cos(2*math.pi*i/n),r*math.sin(2*math.pi*i/n),z) for i in range(n)]
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces += [(i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j),(j,i,2*n+i,2*n+j),(n+i,n+j,3*n+j,3*n+i)]
    o=mesh(name,verts,faces,mat,min(.016,length*.1),True)
    o.location=loc
    o.rotation_euler=Vector(axis).to_track_quat("Z","Y").to_euler()
    return o


def torus(name, loc, major, minor, mat, axis=(0,0,1)):
    bpy.ops.mesh.primitive_torus_add(major_segments=40,minor_segments=10,location=loc,major_radius=major,minor_radius=minor)
    o=assign(bpy.context.object,name,mat)
    o.rotation_euler=Vector(axis).to_track_quat("Z","Y").to_euler()
    smooth(o)
    return o


def bolt(name,loc,axis=(0,0,1),radius=.045):
    return cyl(name,loc,radius,radius*.45,"Brushed_Steel",axis,6,.006)


def round_loop(xhalf,yhalf,z,r=.2):
    points=[]
    for cx,cy,a0 in [(xhalf-r,yhalf-r,0),(-xhalf+r,yhalf-r,90),(-xhalf+r,-yhalf+r,180),(xhalf-r,-yhalf+r,270)]:
        for i in range(7):
            a=math.radians(a0+i*15)
            points.append((cx+r*math.cos(a),cy+r*math.sin(a),z))
    points.append(points[0])
    return points


def rail(name, points, bottom, top, mat="Brushed_Steel", radius=.035):
    for i,p in enumerate(points):
        rod(name+f".Post_{i+1:02}",(p[0],p[1],bottom),(p[0],p[1],top),radius,mat)
    for j,z in enumerate([top, bottom+(top-bottom)*.53]):
        tube(name+f".Rail_{j+1}",[(p[0],p[1],z) for p in points],radius,mat)


def ladder(name,x,y,z0,z1,width=.48,step=.32):
    for s in [-1,1]:
        rod(name+f".Stile_{s}",(x+s*width/2,y,z0),(x+s*width/2,y,z1),.035,"Brushed_Steel")
    count=int((z1-z0)/step)
    for i in range(count+1):
        z=z0+i*step
        rod(name+f".Rung_{i+1:02}",(x-width/2,y,z),(x+width/2,y,z),.026,"Brushed_Steel")


def window_front(name,x,y,z,width,height):
    box(name+".Gasket",(x,y,z),(width,.065,height),"Rubber_Bumpers",.10)
    box(name+".Glass",(x,y-.039,z),(width-.12,.025,height-.12),"Muted_Glazing",.07)


def window_side(name,x,y,z,width,height,sign=1):
    box(name+".Gasket",(x,y,z),(.065,width,height),"Rubber_Bumpers",.08)
    box(name+".Glass",(x+sign*.039,y,z),(.025,width-.10,height-.10),"Muted_Glazing",.06)


def reel(name,loc,radius,width,axis=(1,0,0),rope=True):
    v=Vector(axis).normalized()
    cyl(name+".Core",loc,radius*.67,width,"Graphite_Mechanisms",axis)
    for s in [-1,1]:
        cyl(name+f".Flange_{s}",Vector(loc)+v*(width/2),radius,.065,"Hull_Teal",axis)
        cyl(name+f".AxleCap_{s}",Vector(loc)+v*(width/2+.05),radius*.23,.09,"Brushed_Steel",axis)
    if rope:
        count=max(8,int(width/.055))
        for i in range(count):
            torus(name+f".CableWinding_{i+1:02}",Vector(loc)+v*(-width*.44+.88*width*i/(count-1)),radius*.73,.024,"Deck_Nonslip",axis)


def hook(name,x,y,z,size=.24):
    pts=[]
    for i in range(17):
        a=math.radians(40+i*270/16)
        pts.append((x+size*.55*math.cos(a),y,z+size*.65*math.sin(a)))
    tube(name,pts,size*.12,"Ochre_Safety_Paint")


def catamaran():
    group("01 Twin hulls and deck")
    outline=[(-.48,-4.0),(-.69,-3.77),(-.76,-3.30),(-.76,3.20),(-.64,3.65),(.64,3.65),(.76,3.20),(.76,-3.30),(.69,-3.77),(.48,-4.0),(0,-4.12)]
    def shell(name,cx,z0,z1,s0,s1,mat):
        vs=[(cx+x*s,y*s,z) for z,s in [(z0,s0),(z1,s1)] for x,y in outline]
        n=len(outline)
        fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        return mesh(name,vs,fs,mat,.13)
    for s,label in [(-1,"Port"),(1,"Starboard")]:
        cx=s*1.65
        shell(label+".LowerHull",cx,.08,.63,.84,.98,"Graphite_Mechanisms")
        shell(label+".PaintedHull",cx,.59,1.63,.98,1,"Hull_Teal")
        shell(label+".Gunwale",cx,1.56,1.84,1,1.015,"Warm_White_Paint")
        for y in [-2.9,-1.45,.15,1.75,3.05]:
            box(label+f".Fender.{y}",(s*2.43,y,1.4),(.24,1.15,.29),"Rubber_Bumpers",.12)
            for off in [-.32,.32]:
                box(label+f".FenderBand.{y}.{off}",(s*2.56,y+off,1.4),(.035,.08,.32),"Graphite_Mechanisms",.015)
        box(label+".BowFender",(cx,-4.04,1.39),(1.05,.23,.3),"Rubber_Bumpers",.12)
        box(label+".SternKeel",(cx,3.65,.62),(.13,.65,.55),"Hull_Teal",.06)
        rod(label+".PropShaft",(cx,3.56,.66),(cx,3.98,.66),.07,"Brushed_Steel")
        cyl(label+".PropHub",(cx,4.02,.66),.11,.16,"Graphite_Mechanisms",(0,1,0))
        for j in range(3):
            a=j*math.tau/3
            o=box(label+f".PropellerBlade_{j+1}",(cx+math.sin(a)*.18,4.01,.66+math.cos(a)*.18),(.15,.065,.33),"Brushed_Steel",.065)
            o.rotation_euler[1]=a
        box(label+".Rudder",(cx,4.22,.65),(.07,.32,.56),"Graphite_Mechanisms",.04)
    box("BridgeDeck.StructuralBeam",(0,-.15,1.61),(4.12,7.15,.28),"Graphite_Mechanisms",.12)
    box("BridgeDeck.NonslipSurface",(0,-.15,1.78),(4.15,7.05,.10),"Deck_Nonslip",.04)
    for y in [-3,-1.5,0,1.5,3]:
        box(f"DeckSeam_{y}",(0,y,1.836),(3.7,.025,.008),"Graphite_Mechanisms",.002)
    for x in [-1.55,1.55]:
        for y in [-3.25,2.85]:
            box(f"DeckAccessHatch_{x}_{y}",(x,y,1.853),(.65,.70,.045),"Hull_Teal",.07)
            box(f"HatchHandle_{x}_{y}",(x,y,1.89),(.22,.045,.035),"Brushed_Steel",.012)
    group("02 Pilothouse")
    box("Pilothouse.CreamShell",(0,-.73,2.71),(2.5,2.45,1.76),"Warm_White_Paint",.19)
    box("Pilothouse.BaseSkirt",(0,-.73,1.96),(2.62,2.56,.25),"Hull_Teal",.07)
    for x in [-.61,.61]:
        window_front(f"Windshield_{x}",x,-1.982,2.98,1.08,1.05)
        rod(f"WindshieldWiper_{x}",(x-.29,-2.035,2.58),(x+.10,-2.048,3.24),.012,"Graphite_Mechanisms")
    for s in [-1,1]:
        window_side(f"SideForwardWindow_{s}",s*1.263,-1.22,3.0,.93,1.02,s)
        box(f"Pilothouse.Door_{s}",(s*1.273,.04,2.69),(.055,.86,1.62),"Warm_White_Paint",.075)
        window_side(f"DoorGlazing_{s}",s*1.309,.04,3.0,.63,.92,s)
        rod(f"DoorGrab_{s}",(s*1.34,.34,2.44),(s*1.34,.34,2.66),.023,"Brushed_Steel")
        box(f"RoofNavigation_{s}",(s*1.42,-.93,3.79),(.12,.23,.14),"Navigation_Red" if s<0 else "Navigation_Green",.05)
    for x in [-.62,.62]:
        box(f"RearCabinWindowFrame_{x}",(x,.518,3.0),(1.08,.055,.96),"Rubber_Bumpers",.09)
        box(f"RearCabinGlass_{x}",(x,.552,3.0),(.96,.02,.84),"Muted_Glazing",.07)
    box("Pilothouse.RoundedRoof",(0,-.7,3.67),(2.89,2.82,.23),"Hull_Teal",.16)
    for x in [-.96,.96]:
        tube(f"RoofGrabRail_{x}",[(x,-1.62,3.81),(x,-1.55,3.98),(x,-.48,3.98),(x,-.4,3.81)],.025,"Brushed_Steel",True)
    for x in [-1.0,1.0]:
        box(f"WorkLightBody_{x}",(x,-1.67,3.94),(.28,.19,.29),"Graphite_Mechanisms",.05)
        box(f"WorkLightLens_{x}",(x,-1.773,3.94),(.21,.02,.21),"Warm_Task_Lamp",.025)
    cyl("Radar.Pedestal",(-.65,-.2,3.96),.10,.38,"Brushed_Steel")
    cyl("Radar.Dome",(-.65,-.2,4.16),.32,.24,"Warm_White_Paint",edge=.07)
    rod("Mast.Main",(.36,.18,3.8),(.36,.18,4.97),.055,"Brushed_Steel")
    rod("Mast.Crossbar",(-.03,.18,4.68),(.75,.18,4.68),.035,"Brushed_Steel")
    cyl("Mast.NavigationBeacon",(.36,.18,5.0),.1,.18,"Warm_White_Paint",edge=.025)
    for x,y,h in [(-1.03,.29,4.85),(.89,.28,5.2)]:
        cyl(f"AntennaBase_{x}",(x,y,3.88),.065,.19,"Graphite_Mechanisms")
        rod(f"AntennaWhip_{x}",(x,y,3.98),(x,y,h),.013,"Brushed_Steel",12)
    group("03 Working deck equipment")
    for x in [-.65,.65]:
        box(f"BowWinch.BearingMount_{x}",(x,-2.85,2.02),(.20,.65,.38),"Ochre_Safety_Paint",.07)
    reel("BowWinch",(0,-2.85,2.28),.38,1.22)
    cyl("BowWinch.DriveMotor",(.94,-2.85,2.28),.21,.38,"Graphite_Mechanisms",(1,0,0))
    box("BowWinch.Fairlead",(0,-3.34,1.95),(.55,.18,.22),"Brushed_Steel",.07)
    hook("BowWinch.Hook",0,-3.46,1.94,.22)
    box("DeckLocker.Body",(-1.18,2.30,2.14),(.95,1.1,.61),"Warm_White_Paint",.08)
    box("DeckLocker.Lid",(-1.18,2.30,2.49),(1.01,1.16,.10),"Graphite_Mechanisms",.05)
    for x in [-1.48,-.88]:
        box(f"DeckLocker.Latch_{x}",(x,1.735,2.25),(.09,.04,.18),"Brushed_Steel",.015)
    for j in range(5):
        torus(f"DeckHoseCoil_{j+1}",(-1.15,.96,1.94+j*.028),.31-j*.015,.026,"Rubber_Bumpers")
    cx,cy=.90,2.1
    cyl("Crane.Foundation",(cx,cy,1.99),.47,.27,"Graphite_Mechanisms",edge=.05)
    cyl("Crane.SlewRing",(cx,cy,2.21),.39,.18,"Brushed_Steel")
    cyl("Crane.Pedestal",(cx,cy,2.52),.29,.58,"Ochre_Safety_Paint",edge=.05)
    a=(cx,cy,2.77); b=(cx,1.78,4.02); c=(cx,3.29,4.25)
    beam("Crane.InnerBoom",a,b,.35,.32,"Ochre_Safety_Paint",.07)
    beam("Crane.OuterBoom",b,c,.31,.29,"Ochre_Safety_Paint",.06)
    for i,p in enumerate([a,b,c]):
        cyl(f"Crane.Pivot_{i+1}",p,.20,.47,"Graphite_Mechanisms",(1,0,0))
        for s in [-1,1]:
            cyl(f"Crane.PivotPin_{i+1}_{s}",Vector(p)+Vector((s*.255,0,0)),.10,.055,"Brushed_Steel",(1,0,0))
    rod("Crane.HydraulicBarrel",(cx+.24,cy,2.87),(cx+.24,1.82,3.56),.085,"Graphite_Mechanisms")
    rod("Crane.HydraulicPiston",(cx+.24,1.82,3.56),(cx+.24,1.79,3.91),.05,"Brushed_Steel")
    tube("Crane.HydraulicHose",[(cx-.23,cy,2.45),(cx-.25,2.2,3.2),(cx-.23,1.68,3.93),(cx-.23,2.5,4.15),(cx-.23,3.12,4.2)],.03,"Rubber_Bumpers",True)
    rod("Crane.HoistCable",(cx,3.29,4.1),(cx,3.29,3.37),.018,"Graphite_Mechanisms")
    box("Crane.HookBlock",(cx,3.29,3.43),(.18,.18,.25),"Graphite_Mechanisms",.045)
    hook("Crane.CargoHook",cx,3.29,3.19,.24)
    group("04 Safety rails and fittings")
    for s in [-1,1]:
        rail(f"OuterRail_{s}",[(s*2.24,y) for y in [-3.55,-2.55,-1.3,0,1.25,2.5,3.4]],1.85,2.65)
        rail(f"SternRail_{s}",[(s*2.24,3.4),(s*1.6,3.4),(s*.9,3.4)],1.85,2.65)
        for y in [-3.55,3.25]:
            cyl(f"Bollard_{s}_{y}",(s*1.75,y,2.0),.09,.30,"Ochre_Safety_Paint")
            cyl(f"BollardCap_{s}_{y}",(s*1.75,y,2.16),.15,.055,"Ochre_Safety_Paint")
            box(f"BollardFoot_{s}_{y}",(s*1.75,y,1.87),(.36,.3,.05),"Graphite_Mechanisms",.04)
        for y in [-1.8,1.8]:
            box(f"CleatFoot_{s}_{y}",(s*1.95,y,1.9),(.25,.16,.06),"Brushed_Steel",.025)
            rod(f"Cleat_{s}_{y}",(s*1.95-.16,y,2.03),(s*1.95+.16,y,2.03),.037,"Brushed_Steel")
    ladder("SternSwimLadder",0,3.6,.6,2.4,.5,.28)


def thruster(name,loc,axis,radius=.25):
    v=Vector(axis).normalized()
    q=v.to_track_quat("Z","Y")
    ring(name+".Duct",loc,radius,radius*.75,.24,"Hull_Teal",axis)
    torus(name+".FrontRim",Vector(loc)+v*.13,radius*.88,.027,"Brushed_Steel",axis)
    cyl(name+".MotorHub",loc,radius*.23,.22,"Graphite_Mechanisms",axis)
    for i in range(4):
        a=i*math.tau/4
        local=Vector((math.cos(a)*radius*.43,math.sin(a)*radius*.43,0))
        o=box(name+f".PropellerBlade_{i+1}",Vector(loc)+q@local,(radius*.76,radius*.23,.035),"Brushed_Steel",.035)
        o.rotation_mode="QUATERNION"
        o.rotation_quaternion=q @ Quaternion((0,0,1),a) @ Quaternion((1,0,0),.24)
    for i in [0,1]:
        a=i*math.pi/2
        u=q @ Vector((math.cos(a)*radius*.80,math.sin(a)*radius*.80,.155))
        w=q @ Vector((-math.cos(a)*radius*.80,-math.sin(a)*radius*.80,.155))
        rod(name+f".Guard_{i+1}",Vector(loc)+u,Vector(loc)+w,.011,"Brushed_Steel",12)
    p=Vector(loc)+q@Vector((0,-radius*.92,0))
    o=box(name+".MotorServiceBand",p,(radius*.75,.07,.26),"Ochre_Safety_Paint",.02)
    o.rotation_euler=q.to_euler()


def rov():
    group("01 Protective frame and buoyancy")
    for z in [.24,1.25]:
        tube(f"Cage.RoundedPerimeter_{z}",round_loop(.98,.73,z,.18),.082,"Warm_White_Paint")
    for x in [-.86,.86]:
        for y in [-.61,.61]:
            rod(f"Cage.CornerPost_{x}_{y}",(x,y,.24),(x,y,1.25),.082,"Warm_White_Paint")
            for z in [.32,1.18]:
                box(f"Cage.CornerGuard_{x}_{y}_{z}",(x,y,z),(.21,.21,.24),"Graphite_Mechanisms",.06)
                bolt(f"Cage.Fastener_{x}_{y}_{z}",(x,y-.112,z),(0,-1,0),.026)
    for x in [-.65,.65]:
        tube(f"LandingSkid_{x}",[(x,-.88,.2),(x,-.75,.10),(x,.73,.10),(x,.86,.2)],.068,"Graphite_Mechanisms",True)
        for y in [-.5,.5]:
            rod(f"SkidBrace_{x}_{y}",(x,y,.12),(x,y,.39),.045,"Brushed_Steel")
    box("Buoyancy.FoamShell",(0,0,1.14),(1.58,1.27,.42),"Warm_White_Paint",.19)
    for x in [-.53,.53]:
        box(f"Buoyancy.StrapTop_{x}",(x,0,1.357),(.17,1.13,.052),"Hull_Teal",.025)
        for y in [-.6,.6]:
            box(f"Buoyancy.StrapEnd_{x}_{y}",(x,y,1.18),(.17,.10,.30),"Hull_Teal",.04)
    cyl("Buoyancy.AccessPlate",(0,-.1,1.366),.24,.035,"Hull_Teal")
    cyl("Buoyancy.AccessPlug",(0,-.1,1.39),.05,.03,"Graphite_Mechanisms",vertices=6)
    for i in range(8):
        a=i*math.tau/8
        bolt(f"AccessPlate.Bolt_{i+1}",(.197*math.cos(a),-.1+.197*math.sin(a),1.392),radius=.016)
    tube("LiftHandle",[(-.31,.13,1.36),(-.31,.13,1.53),(.31,.13,1.53),(.31,.13,1.36)],.038,"Brushed_Steel",True)
    group("02 Pressure hull and instruments")
    cyl("PressureHousing.Central",(0,0,.76),.40,1.20,"Graphite_Mechanisms",(0,1,0),40,.06)
    for y in [-.42,.42]:
        ring(f"PressureHousing.Band_{y}",(0,y,.76),.43,.385,.085,"Brushed_Steel",(0,1,0))
    box("Camera.HeadHousing",(0,-.72,.77),(.79,.29,.49),"Graphite_Mechanisms",.10)
    ring("Camera.LensBezel",(0,-.89,.78),.185,.143,.10,"Brushed_Steel",(0,1,0))
    cyl("Camera.Lens",(0,-.953,.78),.14,.036,"Muted_Glazing",(0,1,0),40)
    cyl("Camera.InnerOptic",(0,-.975,.78),.067,.007,"Graphite_Mechanisms",(0,1,0))
    box("Camera.LightBarHousing",(0,-.82,1.045),(.48,.14,.095),"Graphite_Mechanisms",.04)
    box("Camera.LightBarDiffuser",(0,-.898,1.045),(.39,.02,.05),"Warm_Task_Lamp",.02)
    cyl("Sonar.Transducer",(-.40,-.74,.54),.10,.18,"Hull_Teal",(0,1,0))
    box("Electronics.LowerModule",(0,-.14,.40),(.76,.87,.22),"Hull_Teal",.08)
    for x in [-.28,.28]:
        box(f"Electronics.Vent_{x}",(x,-.59,.40),(.16,.025,.075),"Graphite_Mechanisms",.025)
    for x in [-.46,.46]:
        tube(f"InstrumentConduit_{x}",[(x,-.35,.43),(x,.15,.45),(x,.52,.77),(x,.58,1.02)],.027,"Rubber_Bumpers",True)
    group("03 Six ducted thrusters")
    for s in [-1,1]:
        for y in [-.46,.48]:
            rod(f"ThrusterSupport_{s}_{y}",(s*.73,y,.76),(s*1.07,y,.76),.075,"Graphite_Mechanisms")
            thruster(f"HorizontalThruster_{s}_{y}",(s*1.08,y,.79),(s,0,0),.265)
        rod(f"VerticalThrusterSupport_{s}",(s*.72,.4,1.25),(s*.83,.42,1.48),.06,"Graphite_Mechanisms")
        thruster(f"VerticalThruster_{s}",(s*.83,.42,1.53),(0,0,1),.24)
    group("04 Articulated manipulators")
    for s in [-1,1]:
        a=(s*.53,-.50,.48);b=(s*.57,-1.02,.39);c=(s*.62,-1.43,.31)
        cyl(f"Manipulator_{s}.Shoulder",a,.135,.27,"Graphite_Mechanisms",(1,0,0))
        beam(f"Manipulator_{s}.UpperArm",a,b,.18,.20,"Ochre_Safety_Paint",.07)
        cyl(f"Manipulator_{s}.Elbow",b,.14,.28,"Graphite_Mechanisms",(1,0,0))
        beam(f"Manipulator_{s}.Forearm",b,c,.16,.17,"Ochre_Safety_Paint",.055)
        rod(f"Manipulator_{s}.Actuator",(s*.72,-.61,.53),(s*.75,-1.09,.41),.044,"Brushed_Steel")
        tube(f"Manipulator_{s}.Hose",[(s*.39,-.51,.52),(s*.4,-.9,.52),(s*.43,-1.25,.42)],.022,"Rubber_Bumpers",True)
        cyl(f"Manipulator_{s}.Wrist",c,.105,.20,"Graphite_Mechanisms",(0,1,0))
        box(f"Manipulator_{s}.GripperPalm",(s*.62,-1.54,.31),(.32,.22,.15),"Graphite_Mechanisms",.045)
        for finger in [-1,1]:
            points=[(s*.62+finger*.12,-1.56,.31),(s*.62+finger*.21,-1.74,.31),(s*.62+finger*.17,-1.91,.31),(s*.62+finger*.08,-1.96,.31)]
            for i in range(len(points)-1):
                beam(f"Manipulator_{s}.Finger_{finger}.Link_{i+1}",points[i],points[i+1],.085,.09,"Graphite_Mechanisms",.03)
            cyl(f"Manipulator_{s}.FingerPin_{finger}",points[0],.054,.16,"Brushed_Steel")
            box(f"Manipulator_{s}.FingerPad_{finger}",(s*.62+finger*.085,-1.952,.31),(.06,.12,.11),"Rubber_Bumpers",.024)
        for y,z in [(-.50,.48),(-1.02,.39)]:
            cyl(f"Manipulator_{s}.JointCover_{y}",(s*.53+s*.16,y,z),.075,.04,"Brushed_Steel",(1,0,0))
    group("05 Tether and service fittings")
    cyl("Tether.Socket",(0,.67,.98),.15,.18,"Hull_Teal",(0,1,0))
    cyl("Tether.LockingRing",(0,.80,.98),.12,.12,"Brushed_Steel",(0,1,0),12)
    for i in range(5):
        cyl(f"Tether.StrainRelief_{i+1}",(0,.90+i*.045,.98),.095-i*.005,.03,"Rubber_Bumpers",(0,1,0))
    tube("Tether.ShortCable",[(0,1.08,.98),(0,1.34,1.03),(.13,1.52,1.26),(.35,1.65,1.35)],.042,"Ochre_Safety_Paint",True)
    cyl("Tether.EndCap",(.35,1.65,1.35),.05,.07,"Graphite_Mechanisms",(.6,.5,.2))
    for x in [-.5,.5]:
        cyl(f"RearServicePort_{x}",(x,.68,.71),.075,.13,"Brushed_Steel",(0,1,0),12)
        cyl(f"RearServicePortCap_{x}",(x,.755,.71),.06,.035,"Ochre_Safety_Paint",(0,1,0),12)


def saddle(name,y):
    pts=[(-2.90,2.62),(-2.5,2.25),(-1.6,1.72),(0,1.60),(1.6,1.72),(2.5,2.25),(2.90,2.62)]
    verts=[(x,y+dy,z+dz) for dy in [-.24,.24] for dz in [-.26,0] for x,z in pts]
    n=len(pts);faces=[]
    for i in range(n-1):
        faces += [(i,i+1,n+i+1,n+i),(2*n+i,3*n+i,3*n+i+1,2*n+i+1),(n+i,n+i+1,3*n+i+1,3*n+i),(i,2*n+i,2*n+i+1,i+1)]
    faces += [(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)]
    mesh(name+".SteelSaddle",verts,faces,"Hull_Teal",.07)
    for i in range(n-1):
        x1,z1=pts[i];x2,z2=pts[i+1]
        beam(name+f".RubberContactPad_{i+1}",(x1,y,z1+.04),(x2,y,z2+.04),.12,.43,"Rubber_Bumpers",.025)
    for s in [-1,1]:
        box(name+f".EndClevis_{s}",(s*2.87,y,2.55),(.26,.64,.53),"Ochre_Safety_Paint",.07)
        cyl(name+f".EndPin_{s}",(s*2.88,y,2.70),.09,.75,"Brushed_Steel",(0,1,0))


def dock():
    group("01 Four load towers")
    for x in [-3.8,3.8]:
        for y in [-3.3,3.3]:
            tag=f"Tower_{x}_{y}"
            box(tag+".Foundation",(x,y,.24),(1.85,1.8,.48),"Pale_Concrete",.16)
            box(tag+".FootHousing",(x,y,.76),(1.58,1.52,.68),"Hull_Teal",.15)
            box(tag+".MainColumn",(x,y,3.95),(1.15,1.2,6.16),"Warm_White_Paint",.22)
            box(tag+".TealSleeve",(x,y,4.12),(1.20,1.25,3.55),"Hull_Teal",.18)
            box(tag+".SafetyBand",(x,y,5.92),(1.215,1.265,.18),"Ochre_Safety_Paint",.05)
            box(tag+".Headstock",(x,y,7.09),(1.46,1.52,.42),"Hull_Teal",.10)
            for dx in [-.61,.61]:
                for dy in [-.59,.59]:
                    bolt(tag+f".Anchor_{dx}_{dy}",(x+dx,y+dy,.49),radius=.075)
            box(tag+".ServicePanel",(x,y-.639,3.05),(.67,.08,1.0),"Hull_Teal",.08)
            for z in [2.65,3.45]:
                for dx in [-.24,.24]:
                    bolt(tag+f".PanelBolt_{dx}_{z}",(x+dx,y-.69,z),(0,-1,0),.035)
            tube(tag+".HydraulicPipe",[(x+.41,y-.70,.9),(x+.41,y-.70,6.7),(x+.25,y-.70,7.02)],.038,"Brushed_Steel")
            for z in [1.2,2.3,4.1,5.5,6.5]:
                box(tag+f".PipeClip_{z}",(x+.41,y-.70,z),(.17,.09,.06),"Graphite_Mechanisms",.015)
    group("02 Overhead beams and hoists")
    for y in [-3.3,3.3]:
        box(f"Gantry.CrossBeam_{y}",(0,y,7.02),(7.7,.72,.64),"Warm_White_Paint",.13)
        for x in [-2.9,2.9]:
            box(f"Gantry.BeamCollar_{x}_{y}",(x,y,7.02),(.34,.82,.79),"Hull_Teal",.08)
    for x in [-3.8,3.8]:
        box(f"Gantry.LongitudinalBeam_{x}",(x,0,7.09),(.63,6.7,.55),"Warm_White_Paint",.10)
    for s in [-1,1]:
        for y in [-2.58,2.58]:
            x=s*3.16;tag=f"Hoist_{s}_{y}"
            box(tag+".MachineBed",(x,y,7.45),(1.08,1.28,.18),"Hull_Teal",.06)
            for dy in [-.53,.53]:
                box(tag+f".DrumBearing_{dy}",(x,y+dy,7.78),(.61,.18,.61),"Warm_White_Paint",.12)
            reel(tag+".CableDrum",(x,y,7.91),.43,.98,(0,1,0))
            cyl(tag+".DriveMotor",(x,y+.77,7.87),.24,.42,"Hull_Teal",(0,1,0))
            cyl(tag+".TopSheave",(s*2.91,y,6.67),.29,.29,"Graphite_Mechanisms",(0,1,0))
            for dx in [-.105,.105]:
                rod(tag+f".SuspensionCable_{dx}",(s*2.91+dx,y,6.70),(s*2.91+dx,y,3.18),.018,"Graphite_Mechanisms",12)
            cyl(tag+".LowerSheave",(s*2.91,y,3.18),.22,.28,"Hull_Teal",(0,1,0))
            box(tag+".PulleyCheek",(s*2.91,y-.18,3.18),(.39,.09,.43),"Ochre_Safety_Paint",.09)
            bolt(tag+".PulleyAxle",(s*2.91,y-.24,3.18),(0,-1,0),.075)
            beam(tag+".CradleLink",(s*2.91,y,3.02),(s*2.88,y,2.65),.16,.19,"Graphite_Mechanisms",.045)
    group("03 Empty suspended cradle")
    for y in [-2.58,2.58]:
        saddle(f"Cradle.Saddle_{y}",y)
    for x in [-2.45,2.45]:
        box(f"Cradle.LongitudinalTie_{x}",(x,0,2.11),(.22,5.34,.25),"Hull_Teal",.065)
        for y in [-2.58,2.58]:
            box(f"Cradle.CornerGusset_{x}_{y}",(x,y,2.19),(.48,.64,.20),"Graphite_Mechanisms",.04)
    group("04 Side service walkways")
    for s in [-1,1]:
        x=s*3.55
        box(f"Walkway_{s}.Frame",(x,0,1.64),(1.13,5.45,.23),"Hull_Teal",.07)
        for i in range(30):
            box(f"Walkway_{s}.DeckSlat_{i+1:02}",(x,-2.55+i*.176,1.80),(1.07,.13,.07),"Deck_Nonslip",.014)
        rail(f"Walkway_{s}.OuterGuard",[(s*4.11,y) for y in [-2.6,-1.3,0,1.3,2.6]],1.81,2.82,"Ochre_Safety_Paint",.032)
        rail(f"Walkway_{s}.InnerGuard",[(s*3.02,y) for y in [-1.9,-.63,.63,1.9]],1.81,2.70,"Brushed_Steel",.03)
        for y in [-1.8,1.8]:
            beam(f"Walkway_{s}.DiagonalBrace_{y}",(s*3.8,y,1.0),(s*3.1,y,1.55),.13,.14,"Hull_Teal",.035)
        ladder(f"FrontTowerLadder_{s}",s*3.80,-3.99,.53,7.18,.48,.34)
        for z in [2.5,4.3,6.1]:
            for dx in [-.24,.24]:
                rod(f"LadderStandoff_{s}_{z}_{dx}",(s*3.8+dx,-3.92,z),(s*3.8+dx,-3.74,z),.025,"Graphite_Mechanisms")
    group("05 Operator booth and service panels")
    box("OperatorBooth.Support",(-4.40,-2.15,2.67),(1.12,1.28,.20),"Hull_Teal",.07)
    box("OperatorBooth.CreamCab",(-4.40,-2.15,3.37),(1.05,1.21,1.25),"Warm_White_Paint",.11)
    window_front("OperatorBooth.FrontWindow",-4.40,-2.773,3.55,.85,.72)
    window_side("OperatorBooth.SideWindow",-4.947,-2.15,3.55,.99,.72,-1)
    box("OperatorBooth.Roof",(-4.40,-2.15,4.07),(1.22,1.37,.16),"Hull_Teal",.09)
    box("OperatorBooth.LowerDoor",(-3.856,-2.15,3.27),(.04,.68,.85),"Graphite_Mechanisms",.05)
    box("ElectricalCabinet",(4.39,2.9,1.60),(.62,.88,1.22),"Warm_White_Paint",.09)
    box("ElectricalCabinet.Door",(4.721,2.9,1.61),(.055,.73,1.04),"Hull_Teal",.055)
    box("ElectricalCabinet.Handle",(4.76,2.66,1.62),(.045,.045,.27),"Brushed_Steel",.012)
    for y in [-3.3,3.3]:
        for x in [-3.8,3.8]:
            box(f"TowerTaskLamp_{x}_{y}",(x,y,6.8),(.27,.19,.19),"Graphite_Mechanisms",.04)


def roof_shell(name,y0,y1,width,height,zbase,mat,thick=.14,segments=48):
    pts=[]
    for w,h in [(width,height),(width-thick,height-thick)]:
        for y in [y0,y1]:
            pts += [(w*math.cos(i*math.pi/segments),y,zbase+h*math.sin(i*math.pi/segments)) for i in range(segments+1)]
    n=segments+1;fs=[]
    for i in range(segments):
        fs += [(i,i+1,n+i+1,n+i),(2*n+i+1,2*n+i,3*n+i,3*n+i+1),(i,2*n+i,2*n+i+1,i+1),(n+i+1,3*n+i+1,3*n+i,n+i)]
    fs += [(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)]
    return mesh(name,pts,fs,mat,.025,True)


def arch_front_panel(name,y,width,height,zbase,mat):
    n=40
    pts=[(width*math.cos(i*math.pi/n),zbase+height*math.sin(i*math.pi/n)) for i in range(n+1)]
    verts=[(x,y+dy,z) for dy in [-.10,.10] for x,z in pts]
    k=len(pts)
    faces=[tuple(range(k-1,-1,-1)),tuple(range(k,2*k))]
    faces += [(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)]
    return mesh(name,verts,faces,mat,.025)


def vent(name,x,y,z,side=False,w=.9,h=.8):
    if side:
        box(name+".Frame",(x,y,z),(.12,w,h),"Brushed_Steel",.06)
        box(name+".Recess",(x+.07,y,z),(.035,w-.12,h-.12),"Graphite_Mechanisms",.025)
        for i in range(5):
            box(name+f".Louvre_{i+1}",(x+.1,y,z-h*.32+i*h*.16),(.08,w-.17,.065),"Brushed_Steel",.022)
    else:
        box(name+".Frame",(x,y,z),(w,.12,h),"Brushed_Steel",.06)
        box(name+".Recess",(x,y+.07,z),(w-.12,.035,h-.12),"Graphite_Mechanisms",.025)
        for i in range(5):
            box(name+f".Louvre_{i+1}",(x,y+.1,z-h*.32+i*h*.16),(w-.17,.08,.065),"Brushed_Steel",.022)


def workshop():
    group("01 Foundation and walls")
    box("MainBay.Foundation",(0,0,.14),(9.05,9.15,.28),"Pale_Concrete",.10)
    box("Office.Foundation",(5.68,-1.68,.14),(2.97,5.8,.28),"Pale_Concrete",.10)
    box("MainBay.ShopFloor",(0,0,.31),(8.6,8.75,.07),"Deck_Nonslip",.025)
    for x in [-4.28,4.28]:
        box(f"MainBay.SideWall_{x}",(x,0,2.58),(.25,8.8,4.6),"Warm_White_Paint",.07)
    box("MainBay.RearWall",(0,4.32,2.58),(8.6,.25,4.6),"Warm_White_Paint",.07)
    for y in [-4.32,4.32]:
        arch_front_panel(f"MainBay.ArchedGable_{y}",y,4.4,1.94,4.82,"Warm_White_Paint")
    for x in [-4.17,0,4.17]:
        box(f"FrontPortal.Column_{x}",(x,-4.28,2.57),(.35,.48,4.55),"Hull_Teal",.07)
        box(f"FrontPortal.CollisionGuard_{x}",(x,-4.55,1.08),(.24,.12,1.48),"Ochre_Safety_Paint",.05)
    box("FrontPortal.Lintel",(0,-4.3,4.82),(8.65,.50,.33),"Hull_Teal",.07)
    for x in [-2.08,2.08]:
        box(f"BayDoor_{x}.RolledCurtain",(x,-4.24,4.48),(3.78,.24,.27),"Graphite_Mechanisms",.09)
        for dx in [-1.86,1.86]:
            box(f"BayDoor_{x}.Track_{dx}",(x+dx,-4.43,2.52),(.12,.12,4.28),"Graphite_Mechanisms",.025)
        box(f"BayDoor_{x}.ThresholdDrain",(x,-4.34,.36),(3.77,.3,.045),"Graphite_Mechanisms",.02)
        for i in range(24):
            box(f"BayDoor_{x}.DrainBar_{i+1:02}",(x-1.79+i*.155,-4.34,.391),(.035,.27,.018),"Brushed_Steel",.004)
    for x in [-4.43,4.43]:
        box(f"SideWall.FootTrim_{x}",(x,0,.52),(.13,8.7,.32),"Hull_Teal",.035)
        for i,y in enumerate([-3.4,-2.2,-1,.2,1.4,2.6,3.8]):
            box(f"SideWall.PanelSeam_{x}_{i+1}",(x,y,2.74),(.018,.023,3.83),"Pale_Concrete",.006)
    group("02 Barrel roof and rain goods")
    roof_shell("Roof.ContinuousBarrel",-4.52,4.52,4.52,2.03,4.8,"Hull_Teal",.16)
    for y in [-4.43,4.43]:
        roof_shell(f"Roof.CreamEdgeBand_{y}",y-.17,y+.17,4.56,2.07,4.8,"Warm_White_Paint",.12)
    for j,y in enumerate([-4.63,-2.3,0,2.3,4.63]):
        pts=[(4.59*math.cos(i*math.pi/48),y,4.8+2.10*math.sin(i*math.pi/48)) for i in range(49)]
        tube(f"Roof.StructuralRib_{j+1}",pts,.055,"Hull_Teal")
    for x in [-4.56,4.56]:
        box(f"Roof.EaveGutter_{x}",(x,0,4.79),(.18,9.4,.20),"Hull_Teal",.06)
        tube(f"RainDownpipe_{x}",[(x,3.83,4.8),(x+.12,3.83,4.56),(x+.12,3.83,.65),(x+.24,3.83,.45)],.065,"Brushed_Steel",True)
    box("RoofVent.Curb",(1.5,2.7,6.73),(1.07,.79,.22),"Graphite_Mechanisms",.06)
    box("RoofVent.Hood",(1.5,2.7,7.02),(1.1,.84,.50),"Hull_Teal",.20)
    for i in range(5):
        box(f"RoofVent.FrontLouvre_{i+1}",(1.5,2.265,6.90+i*.058),(.84,.04,.025),"Brushed_Steel",.008)
    group("03 Overhead hoist and visible bay fixtures")
    for x in [-3.83,3.83]:
        box(f"Hoist.LongitudinalRail_{x}",(x,0,4.39),(.22,8.0,.27),"Graphite_Mechanisms",.035)
        for y in [-3.5,0,3.5]:
            beam(f"Hoist.RailBracket_{x}_{y}",(x,y,4.32),(math.copysign(4.12,x),y,3.97),.10,.10,"Hull_Teal",.025)
    box("Hoist.CrossBridge",(0,-1.8,4.34),(7.81,.34,.35),"Ochre_Safety_Paint",.06)
    box("Hoist.TravellingTrolley",(1.12,-1.8,4.11),(.66,.55,.34),"Graphite_Mechanisms",.07)
    for x in [.88,1.36]:
        cyl(f"Hoist.TrolleyWheel_{x}",(x,-1.8,4.35),.13,.62,"Brushed_Steel",(0,1,0))
    for dx in [-.045,.045]:
        rod(f"Hoist.LiftingLine_{dx}",(1.12+dx,-1.8,4.0),(1.12+dx,-1.8,3.15),.015,"Graphite_Mechanisms",12)
    cyl("Hoist.HookPulley",(1.12,-1.8,3.16),.18,.15,"Ochre_Safety_Paint",(0,1,0))
    hook("Hoist.CargoHook",1.12,-1.8,2.87,.28)
    for x in [-2.1,2.1]:
        box(f"Interior.Workbench_{x}",(x,3.62,1.10),(2.8,.72,.17),"Brushed_Steel",.04)
        for dx in [-1.2,1.2]:
            box(f"Interior.WorkbenchLeg_{x}_{dx}",(x+dx,3.62,.72),(.12,.56,.72),"Hull_Teal",.03)
        box(f"Interior.ToolCabinet_{x}",(x,3.60,.71),(1.38,.65,.69),"Hull_Teal",.06)
        for z in [.51,.71,.91]:
            box(f"Interior.Drawer_{x}_{z}",(x,3.254,z),(1.23,.035,.16),"Graphite_Mechanisms",.02)
            box(f"Interior.DrawerPull_{x}_{z}",(x,3.217,z),(.43,.03,.03),"Brushed_Steel",.008)
        box(f"Interior.ToolBoard_{x}",(x,4.17,2.05),(2.35,.08,1.12),"Hull_Teal",.055)
        for k in range(5):
            rod(f"Interior.ToolPeg_{x}_{k}",(x-.8+k*.4,4.09,2.22),(x-.8+k*.4,3.97,2.22),.025,"Brushed_Steel")
        tube(f"Interior.HoseLoop_{x}",[(x+.84,4.03,2.25),(x+.55,4.0,1.91),(x+.61,4.0,1.49),(x+1.0,4.0,1.48),(x+1.12,4.0,1.94),(x+.84,4.03,2.25)],.035,"Rubber_Bumpers",True)
    for y in [-2,1.6]:
        box(f"Interior.CeilingLamp_{y}",(0,y,5.9),(1.2,.25,.12),"Graphite_Mechanisms",.04)
        box(f"Interior.CeilingDiffuser_{y}",(0,y,5.825),(1.09,.19,.025),"Warm_Task_Lamp",.025)
    for x in [-3.56,3.56]:
        cyl(f"Interior.ServiceCylinder_{x}",(x,2.65,.87),.21,1.02,"Hull_Teal",edge=.07)
        cyl(f"Interior.CylinderValve_{x}",(x,2.65,1.43),.06,.13,"Brushed_Steel")
    group("04 Side office")
    box("Office.CreamShell",(5.65,-1.75,1.78),(2.64,5.48,2.98),"Warm_White_Paint",.10)
    box("Office.Roof",(5.65,-1.74,3.37),(2.96,5.76,.20),"Hull_Teal",.07,rot=(0,math.radians(-4),0))
    box("Office.FrontDoor",(4.91,-4.509,1.5),(.93,.055,2.25),"Hull_Teal",.06)
    window_front("Office.DoorWindow",4.91,-4.548,1.90,.65,1.10)
    rod("Office.DoorHandle",(5.24,-4.61,1.32),(5.24,-4.61,1.50),.022,"Brushed_Steel")
    window_front("Office.FrontWindow",6.13,-4.514,2.01,1.12,1.34)
    for y in [-3.28,-1.83,-.38]:
        window_side(f"Office.SideWindow_{y}",6.987,y,2.0,1.28,1.35,1)
    box("Office.WindowSill",(7.02,-1.83,1.29),(.15,4.35,.12),"Hull_Teal",.035)
    box("Office.FrontLampHousing",(4.92,-4.57,2.95),(.49,.19,.17),"Graphite_Mechanisms",.05)
    box("Office.FrontLamp",(4.92,-4.676,2.93),(.39,.02,.08),"Warm_Task_Lamp",.025)
    for x in [4.43,6.88]:
        cyl(f"Office.Bollard_{x}",(x,-4.70,.89),.095,1.16,"Ochre_Safety_Paint",edge=.06)
    group("05 Ventilation and rear service details")
    for y in [1.5,3.1]:
        vent(f"SideVent_{y}",4.45,y,3.53,True,.95,.83)
    for x in [-2.6,2.6]:
        vent(f"RearVent_{x}",x,4.49,3.68,False,1.28,.91)
    box("RearServiceDoor.Frame",(0,4.49,1.58),(1.35,.12,2.60),"Hull_Teal",.07)
    box("RearServiceDoor.Leaf",(0,4.57,1.57),(1.13,.055,2.36),"Graphite_Mechanisms",.045)
    box("RearServiceDoor.Window",(0,4.605,2.15),(.77,.025,.77),"Muted_Glazing",.04)
    rod("RearServiceDoor.Handle",(.40,4.65,1.34),(.40,4.65,1.53),.024,"Brushed_Steel")
    tube("Workshop.ExtractPipe",[(4.69,3.18,.55),(4.69,3.18,5.10),(4.40,3.18,5.49),(4.02,3.18,5.55)],.13,"Brushed_Steel",True)
    for z in [1.1,2.4,3.7,4.9]:
        ring(f"ExtractPipe.Clip_{z}",(4.69,3.18,z),.153,.131,.07,"Graphite_Mechanisms")
    for x in [-2.1,2.1]:
        box(f"Bay.TaskLightHousing_{x}",(x,-4.48,5.21),(.65,.23,.22),"Graphite_Mechanisms",.05)
        box(f"Bay.TaskLightDiffuser_{x}",(x,-4.61,5.16),(.55,.025,.09),"Warm_Task_Lamp",.025)


def author_uvs(objects):
    # This is a production operation, deliberately not a UV validator.
    for i,o in enumerate(objects):
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active=o
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.035,area_weight=.1,correct_aspect=True,scale_to_bounds=True)
        bpy.ops.object.mode_set(mode="OBJECT")
        if o.data.uv_layers:
            o.data.uv_layers.active.name="UV_Component"
        o["uv_method"]="Component-local smart projection, 66 degrees, 0.035 island margin. No overlap/density check."
        if i%100==0:
            print(f"AUTHOR_UV {i+1}/{len(objects)}",flush=True)


def bounds(objects):
    bpy.context.view_layer.update()
    coords=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
    low=Vector(tuple(min(v[i] for v in coords) for i in range(3)))
    high=Vector(tuple(max(v[i] for v in coords) for i in range(3)))
    return low,high


def studio(low,high):
    global COL
    COL=bpy.data.collections.new("STUDIO")
    bpy.context.scene.collection.children.link(COL)
    material("Studio_WarmNeutral","D4D5D2",.85,0)
    span=max(high-low)
    center=(low+high)/2
    box("Studio.Ground",(center.x,center.y,low.z-.10),(span*200,span*200,.16),"Studio_WarmNeutral",0)
    world=bpy.data.worlds.new("Neutral_Studio_World")
    world.use_nodes=True
    world.node_tree.nodes.get("Background").inputs["Color"].default_value=(.58,.64,.70,1)
    world.node_tree.nodes.get("Background").inputs["Strength"].default_value=.35
    bpy.context.scene.world=world
    def area(name,rel,power,size,color):
        data=bpy.data.lights.new(name,"AREA")
        data.energy=power*span*span
        data.shape="DISK"
        data.size=size*span
        data.color=color
        ob=bpy.data.objects.new(name,data)
        COL.objects.link(ob)
        ob.location=center+Vector(rel)*span
        ob.rotation_euler=(center-ob.location).to_track_quat("-Z","Y").to_euler()
    area("Studio.Key",(-.65,-.85,1.4),105,1.0,(1,.94,.84))
    area("Studio.Fill",(.9,-.25,.75),65,1.0,(.80,.89,1))
    area("Studio.Rim",(.4,1.1,1.3),135,.8,(1,.98,.91))
    area("Studio.FrontSoft",(0,-1.2,.35),28,.65,(1,1,1))
    data=bpy.data.cameras.new("Studio.OrthographicCamera")
    data.type="ORTHO"
    data.lens=55
    data.clip_end=span*500
    camera=bpy.data.objects.new("Studio.OrthographicCamera",data)
    COL.objects.link(camera)
    bpy.context.scene.camera=camera
    scene=bpy.context.scene
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.samples=32
    scene.cycles.use_denoising=True
    scene.cycles.max_bounces=6
    scene.render.threads_mode="FIXED"
    scene.render.threads=4
    scene.render.resolution_x=960
    scene.render.resolution_y=960
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_mode="RGBA"
    scene.render.film_transparent=False
    scene.view_settings.view_transform="AgX"
    return camera,center,span


def set_camera(camera,center,span,low,high,rear=False):
    direction=Vector((-1.05,1.43,.97) if rear else (1.08,-1.47,1.02)).normalized()
    camera.location=center+direction*span*2.8
    camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
    q=camera.rotation_euler.to_quaternion().inverted()
    corners=[Vector((x,y,z)) for x in [low.x,high.x] for y in [low.y,high.y] for z in [low.z,high.z]]
    p=[q@(v-center) for v in corners]
    camera.data.ortho_scale=max(max(v.x for v in p)-min(v.x for v in p),max(v.y for v in p)-min(v.y for v in p))*1.16
    return {"location_m":list(camera.location),"rotation_euler_radians":list(camera.rotation_euler),"projection":"ORTHO","orthographic_scale_m":camera.data.ortho_scale,"target_m":list(center)}


def produce(slug):
    t=time.perf_counter();started=stamp()
    out=ROOT/slug
    (out/"renders").mkdir(parents=True,exist_ok=True)
    init_scene(slug)
    {"catamaran_workboat":catamaran,"underwater_service_robot":rov,"docking_lift_platform":dock,"marine_equipment_workshop":workshop}[slug]()
    objects=sorted([o for o in ASSET.all_objects if o.type=="MESH"],key=lambda o:o.name)
    author_uvs(objects)
    low,high=bounds(objects)
    counts={"mesh_objects":len(objects),"authored_vertices":sum(len(o.data.vertices) for o in objects),"authored_polygons":sum(len(o.data.polygons) for o in objects)}
    mats=sorted({m.name for o in objects for m in o.data.materials})
    cam,center,span=studio(low,high)
    cameras={"hero":set_camera(cam,center,span,low,high,False)}
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(slug+".blend")))
    export_start=time.perf_counter()
    print("EXPORT_GLB",slug,flush=True)
    bpy.ops.export_scene.gltf(filepath=str(out/(slug+".glb")),export_format="GLB",use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials="EXPORT")
    print("EXPORT_FBX",slug,flush=True)
    bpy.ops.export_scene.fbx(filepath=str(out/(slug+".fbx")),use_selection=True,object_types={"MESH"},use_mesh_modifiers=True,mesh_smooth_type="FACE",add_leaf_bones=False,bake_anim=False,axis_forward="-Z",axis_up="Y",path_mode="AUTO")
    export_seconds=time.perf_counter()-export_start
    render_records=[]
    for view in ["hero","rear"]:
        cameras[view]=set_camera(cam,center,span,low,high,view=="rear")
        bpy.context.scene.render.filepath=str(out/"renders"/(view+".png"))
        rstart=stamp();rt=time.perf_counter()
        print("RENDER",slug,view,flush=True)
        bpy.ops.render.render(write_still=True)
        render_records.append({"view":view,"started_at_utc":rstart,"finished_at_utc":stamp(),"elapsed_seconds":round(time.perf_counter()-rt,3),"camera":cameras[view]})
    set_camera(cam,center,span,low,high,False)
    bpy.context.scene.render.filepath=str(out/"renders"/"hero.png")
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(slug+".blend")))
    finished=stamp()
    data={"asset":slug,"set":"Set05","theme":"Marine work","status":"produced_unreviewed","review_status":"deferred_by_user","units":"meters","front_axis":"-Y","up_axis":"+Z","bounds_from_authored_scene_m":{"min":list(low),"max":list(high),"dimensions":list(high-low)},"production_measurements_not_independent_validation":True,"counts":counts,"named_parts":[o.name for o in objects],"materials":mats,"materials_note":"Named solid-color Principled PBR palette. Opaque muted glazing. No texture dependencies.","uv_authoring":{"method":"Each mesh receives its own Smart UV Project layout during production","angle_degrees":66,"island_margin":.035,"layer_name":"UV_Component","density_target":"No shared texture atlas; independent 0-1 space per named component","independent_uv_or_geometry_checks":"deferred_by_user"},"collections":{"ASSET":"Editable named meshes and edge modifiers","STUDIO":"Neutral ground, four area lights, orthographic camera; excluded from GLB/FBX"},"exports":{"glb":"Selected ASSET meshes only, modifiers evaluated, materials, no cameras/lights/animation","fbx":"Selected ASSET meshes only, modifiers evaluated, no animation"},"reference_image":"../REF/"+slug+".png","reference_prompt":"../REF/"+slug+".prompt.txt","source":"../build.py","render_settings":{"engine":"CYCLES","device":"CPU","threads":4,"samples":32,"denoising":True,"resolution":[960,960],"view_transform":"AgX","background":"neutral studio","actual_render":True,"images_opened_or_inspected":False},"renders":render_records,"timing":{"started_at_utc":started,"finished_at_utc":finished,"started_at_kst":datetime.fromisoformat(started).astimezone(KST).isoformat(),"finished_at_kst":datetime.fromisoformat(finished).astimezone(KST).isoformat(),"blender_script_seconds":round(time.perf_counter()-t,3),"export_seconds":round(export_seconds,3),"render_seconds":round(sum(r["elapsed_seconds"] for r in render_records),3)},"limitations":["Visual, mesh/UV quality and export roundtrip review deferred by user.","Solid palette interpretation of the supplied concept; no weathering textures, animation, rig, collision, LODs, or physical simulation."]}
    (out/"metadata.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    print("PRODUCTION_COMPLETE",slug,json.dumps(data["timing"]),flush=True)


if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    parser=argparse.ArgumentParser()
    parser.add_argument("--asset",choices=ASSETS,required=True)
    produce(parser.parse_args(args).asset)
