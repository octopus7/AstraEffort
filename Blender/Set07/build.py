"""Set07 original rounded rail freight assets. Run inside Blender 4.5.

Production only: creates geometry/UVs/materials, exports and renders. It does not
reopen, reimport, inspect images, or run geometry/UV validation.
"""
import bpy
import math
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
SLUGS = (
    "rail_inspection_trolley",
    "side_loading_freight_shuttle",
    "barrel_roof_freight_station",
    "mechanical_signal_house",
)
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SLUG = ARGS[0] if ARGS else SLUGS[0]
if SLUG not in SLUGS:
    raise ValueError("Unknown assigned asset")
OUT = ROOT / SLUG
(OUT / "renders").mkdir(parents=True, exist_ok=True)
START = datetime.now(timezone.utc)
T0 = time.perf_counter()

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for old in list(bpy.data.collections):
    bpy.data.collections.remove(old)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
asset = bpy.data.collections.new("ASSET")
studio = bpy.data.collections.new("STUDIO")
scene.collection.children.link(asset)
scene.collection.children.link(studio)
GROUPS = {}
CURRENT = asset
PARTS = []
MAT = {}


def linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def material(name, hexcolor, metal=0.0, rough=0.5, emission=0.0):
    rgb = [linear(int(hexcolor[i:i + 2], 16) / 255.0) for i in (0, 2, 4)]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (*rgb, 1.0)
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*rgb, 1.0)
    bs.inputs["Metallic"].default_value = metal
    bs.inputs["Roughness"].default_value = rough
    if emission:
        bs.inputs["Emission Color"].default_value = (*rgb, 1.0)
        bs.inputs["Emission Strength"].default_value = emission
    m["palette_hex_srgb"] = "#" + hexcolor
    m["surface_type"] = "solid PBR palette; no image textures"
    return m


for key, spec in {
    "red": ("PAINT_BrickRed", "AE5E50", 0.18, 0.39),
    "ivory": ("PAINT_WarmIvory", "E8DFC8", 0.08, 0.42),
    "dark": ("METAL_Graphite", "394448", 0.55, 0.36),
    "steel": ("METAL_SatinSteel", "879294", 0.78, 0.30),
    "rubber": ("RUBBER_Charcoal", "242B2E", 0.0, 0.72),
    "brass": ("ACCENT_BrassYellow", "C6A04C", 0.45, 0.35),
    "glass": ("GLASS_MutedBlueGray", "57747C", 0.32, 0.22),
    "brick": ("MASONRY_Terracotta", "A66C59", 0.0, 0.77),
    "mortar": ("MASONRY_MortarShadow", "7B6458", 0.0, 0.85),
    "stone": ("MASONRY_WarmStone", "BDB09A", 0.0, 0.79),
    "wood": ("WOOD_CrateTimber", "A28A65", 0.0, 0.67),
    "light": ("LENS_WarmWhite", "FFF1C8", 0.05, 0.24, 1.0),
    "amber": ("LENS_Amber", "E4A033", 0.05, 0.27, 0.4),
}.items():
    MAT[key] = material(*spec)


def group(name):
    global CURRENT
    if name not in GROUPS:
        col = bpy.data.collections.new(name)
        asset.children.link(col)
        GROUPS[name] = col
    CURRENT = GROUPS[name]


def adopt(o, name, mat, uv="primitive cylindrical/spherical UV"):
    o.name = name
    o.data.name = name + "_Mesh"
    for c in list(o.users_collection):
        c.objects.unlink(o)
    CURRENT.objects.link(o)
    o.data.materials.clear()
    o.data.materials.append(MAT[mat])
    o["component"] = name
    o["uv_authoring"] = uv
    o["set"] = "Set07"
    PARTS.append(o)
    return o


def softened(o, width=0.04, segments=3, smooth=True):
    if smooth:
        for p in o.data.polygons:
            p.use_smooth = True
    if width:
        m = o.modifiers.new("Rounded manufactured edges", "BEVEL")
        m.width = width
        m.segments = segments
        m.limit_method = "ANGLE"
        m.angle_limit = math.radians(28)
        m.harden_normals = True
    n = o.modifiers.new("Area weighted surface normals", "WEIGHTED_NORMAL")
    n.keep_sharp = True
    n.weight = 40
    return o


def face_atlas(o):
    """Production UVs: each planar source face gets an aspect-preserving island."""
    mesh = o.data
    uv = mesh.uv_layers.active or mesh.uv_layers.new(name="UVMap")
    uv.name = "UVMap"
    n = len(mesh.polygons)
    cols = max(1, math.ceil(math.sqrt(n)))
    rows = max(1, math.ceil(n / cols))
    for p in mesh.polygons:
        axis = max(range(3), key=lambda k: abs(p.normal[k]))
        axes = [k for k in range(3) if k != axis]
        coords = [(mesh.vertices[mesh.loops[i].vertex_index].co[axes[0]],
                   mesh.vertices[mesh.loops[i].vertex_index].co[axes[1]])
                  for i in p.loop_indices]
        lo = [min(c[k] for c in coords) for k in (0, 1)]
        hi = [max(c[k] for c in coords) for k in (0, 1)]
        span = max(hi[0] - lo[0], hi[1] - lo[1], 0.00001)
        col, row = p.index % cols, p.index // cols
        for li, co in zip(p.loop_indices, coords):
            uv.data[li].uv = ((col + 0.05 + 0.90 * (co[0] - lo[0]) / span) / cols,
                              (row + 0.05 + 0.90 * (co[1] - lo[1]) / span) / rows)


def box(name, loc, size, mat, bevel=0.04, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    adopt(o, name, mat, "six separate planar islands; aspect preserved per face; bevel UV interpolation")
    face_atlas(o)
    if rot:
        o.rotation_euler = rot
    return softened(o, min(bevel, min(size) * 0.42), 3)


def cylinder(name, loc, radius, depth, mat, axis="Z", vertices=32, bevel=0.015):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                       end_fill_type="NGON", location=loc)
    o = adopt(bpy.context.object, name, mat, "continuous cylindrical side strip and separate cap islands")
    if axis == "X":
        o.rotation_euler[1] = math.pi / 2
    elif axis == "Y":
        o.rotation_euler[0] = math.pi / 2
    return softened(o, min(bevel, radius * 0.25, depth * 0.25), 3)


def sphere(name, loc, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=loc)
    o = adopt(bpy.context.object, name, mat, "latitude-longitude UV seam")
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def torus(name, loc, major, minor, mat, axis="Z"):
    bpy.ops.mesh.primitive_torus_add(major_segments=36, minor_segments=10,
                                    major_radius=major, minor_radius=minor, location=loc)
    o = adopt(bpy.context.object, name, mat, "two periodic torus surface coordinates")
    if axis == "Y":
        o.rotation_euler[0] = math.pi / 2
    elif axis == "X":
        o.rotation_euler[1] = math.pi / 2
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def beam(name, a, b, width, depth, mat, bevel=0.02):
    a, b = Vector(a), Vector(b)
    o = box(name, (a + b) * 0.5, (width, depth, (b - a).length), mat, bevel)
    o.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    return o


def rod(name, a, b, radius, mat, vertices=20):
    a, b = Vector(a), Vector(b)
    o = cylinder(name, (a + b) * 0.5, radius, (b - a).length, mat, vertices=vertices,
                 bevel=radius * 0.18)
    o.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    return o


def mesh_part(name, verts, faces, mat, uvs=None, bevel=0.0, smooth=False):
    me = bpy.data.meshes.new(name + "_Mesh")
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    CURRENT.objects.link(o)
    adopt(o, name, mat, "surface-specific strip and cap islands" if uvs else "planar face atlas")
    if uvs:
        uv = me.uv_layers.new(name="UVMap")
        for p, coords in zip(me.polygons, uvs):
            for li, xy in zip(p.loop_indices, coords):
                uv.data[li].uv = xy
    else:
        face_atlas(o)
    if bevel:
        softened(o, bevel, 3, smooth)
    elif smooth:
        for p in me.polygons:
            p.use_smooth = True
    return o


def tube(name, points, radius, mat, sides=12):
    """Rounded path tube with arc-length UVs; tangent frames authored directly."""
    ctrl = [Vector(p) for p in points]
    pts = []
    for j in range(len(ctrl) - 1):
        p0, p1 = ctrl[max(0, j - 1)], ctrl[j]
        p2, p3 = ctrl[j + 1], ctrl[min(len(ctrl) - 1, j + 2)]
        for k in range(6):
            t = k / 6
            pts.append(0.5 * ((2 * p1) + (-p0 + p2) * t +
                              (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    pts.append(ctrl[-1])
    dist = [0.0]
    for a, b in zip(pts, pts[1:]):
        dist.append(dist[-1] + (b - a).length)
    verts, faces, uvs = [], [], []
    for i, p in enumerate(pts):
        tangent = (pts[min(i + 1, len(pts) - 1)] - pts[max(0, i - 1)]).normalized()
        ref = Vector((0, 0, 1)) if abs(tangent.z) < 0.92 else Vector((0, 1, 0))
        u = tangent.cross(ref).normalized()
        v = tangent.cross(u).normalized()
        for k in range(sides):
            a = 2 * math.pi * k / sides
            verts.append(tuple(p + radius * (math.cos(a) * u + math.sin(a) * v)))
    for i in range(len(pts) - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            faces.append((i * sides + k, i * sides + k2,
                          (i + 1) * sides + k2, (i + 1) * sides + k))
            u0, u1 = 0.04 + 0.92 * k / sides, 0.04 + 0.92 * (k + 1) / sides
            v0, v1 = 0.04 + 0.68 * dist[i] / dist[-1], 0.04 + 0.68 * dist[i + 1] / dist[-1]
            uvs.append(((u0, v0), (u1, v0), (u1, v1), (u0, v1)))
    for end, center_u, reverse in ((0, 0.24, True), (len(pts) - 1, 0.70, False)):
        ids = list(range(end * sides, (end + 1) * sides))
        if reverse:
            ids.reverse()
        faces.append(ids)
        uvs.append([(center_u + 0.10 * math.cos(2 * math.pi * (i % sides) / sides),
                     0.86 + 0.10 * math.sin(2 * math.pi * (i % sides) / sides)) for i in ids])
    return mesh_part(name, verts, faces, mat, uvs, smooth=True)


def barrel(name, center, length, span, rise, thickness, mat, along="X", steps=32):
    """Closed elliptical barrel shell, separately mapped outer/inner/end strips."""
    verts = []
    for ix in (-1, 1):
        for inner in (False, True):
            for i in range(steps + 1):
                t = math.pi * i / steps
                y = span * 0.5 * math.cos(t)
                z = rise * math.sin(t) - (thickness if inner else 0)
                x = ix * length * 0.5
                xx, yy = (x, y) if along == "X" else (y, x)
                verts.append((center[0] + xx, center[1] + yy, center[2] + z))
    n = steps + 1
    faces, uvs = [], []
    for i in range(steps):
        a, b = i, i + 1
        faces.append((a, 2 * n + a, 2 * n + b, b))
        v0, v1 = 0.05 + 0.38 * i / steps, 0.05 + 0.38 * (i + 1) / steps
        uvs.append(((0.05, v0), (0.95, v0), (0.95, v1), (0.05, v1)))
        faces.append((n + b, 3 * n + b, 3 * n + a, n + a))
        uvs.append(((0.05, v1 + 0.48), (0.95, v1 + 0.48),
                    (0.95, v0 + 0.48), (0.05, v0 + 0.48)))
        for end in (0, 2 * n):
            faces.append((end + a, end + b, end + n + b, end + n + a))
            u0, u1 = 0.05 + 0.9 * i / steps, 0.05 + 0.9 * (i + 1) / steps
            v = 0.44 if end == 0 else 0.94
            uvs.append(((u0, v), (u1, v), (u1, v + 0.025), (u0, v + 0.025)))
    for i in (0, steps):
        faces.append((i, n + i, 3 * n + i, 2 * n + i))
        uvs.append(((0.05, 0.475), (0.05, 0.495), (0.95, 0.495), (0.95, 0.475)))
    return mesh_part(name, verts, faces, mat, uvs, smooth=True)


def barrel_rib(name, center, span, rise, radius, mat, along="X"):
    points = []
    for i in range(17):
        t = math.pi * i / 16
        a, b = span * 0.5 * math.cos(t), rise * math.sin(t)
        points.append((center[0], center[1] + a, center[2] + b) if along == "X"
                      else (center[0] + a, center[1], center[2] + b))
    return tube(name, points, radius, mat, sides=10)


def gable(name, x, y, z, span, rise, depth, mat):
    outline = [(y - span / 2, z)]
    for i in range(1, 25):
        t = math.pi - math.pi * i / 24
        outline.append((y + span / 2 * math.cos(t), z + rise * math.sin(t)))
    n = len(outline)
    verts = [(xx, yy, zz) for xx in (x - depth / 2, x + depth / 2) for yy, zz in outline]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    faces.extend((i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n))
    return mesh_part(name, verts, faces, mat, bevel=0.018)


def bolt(name, loc, axis="Y", mat="steel", radius=0.035):
    return cylinder(name, loc, radius, radius * 0.5, mat, axis, vertices=6, bevel=0.003)


def wheel_rail(label, x, side):
    y = side * 0.79
    z = 0.49
    cylinder(label + "_SteelTread", (x, y, z), 0.455, 0.23, "steel", "Y", 48, 0.025)
    cylinder(label + "_InnerFlange", (x, side * 0.665, z), 0.49, 0.055, "steel", "Y", 48, 0.012)
    cylinder(label + "_WebRecess", (x, side * 0.918, z), 0.34, 0.02, "dark", "Y", 40)
    for k in range(8):
        a = 2 * math.pi * k / 8
        box(label + f"_WebSpoke_{k + 1:02}", (x + 0.20 * math.sin(a), side * 0.935, z + 0.20 * math.cos(a)),
            (0.075, 0.04, 0.26), "steel", 0.018, (0, a, 0))
    cylinder(label + "_Hub", (x, side * 0.955, z), 0.16, 0.13, "dark", "Y")
    cylinder(label + "_RedAxleCap", (x, side * 1.03, z), 0.095, 0.04, "red", "Y")
    for k in range(6):
        a = 2 * math.pi * k / 6
        bolt(label + f"_HubBolt_{k + 1}", (x + 0.124 * math.sin(a), side * 1.03, z + 0.124 * math.cos(a)),
             mat="brass", radius=0.021)


def wheel_rubber(label, x, side):
    y = side * 1.02
    z = 0.49
    cylinder(label + "_Tire", (x, y, z), 0.48, 0.31, "rubber", "Y", 48, 0.065)
    cylinder(label + "_Sidewall", (x, side * 1.195, z), 0.365, 0.035, "rubber", "Y", 40)
    cylinder(label + "_Rim", (x, side * 1.22, z), 0.25, 0.04, "steel", "Y")
    cylinder(label + "_Hub", (x, side * 1.25, z), 0.125, 0.065, "dark", "Y")
    cylinder(label + "_HubCap", (x, side * 1.29, z), 0.065, 0.026, "brass", "Y")
    for k in range(16):
        a = 2 * math.pi * k / 16
        box(label + f"_Tread_{k + 1:02}", (x + 0.464 * math.sin(a), y, z + 0.464 * math.cos(a)),
            (0.10, 0.30, 0.035), "rubber", 0.015, (0, a, 0))


def build_trolley():
    group("01_Rail_Running_Gear")
    for i, x in enumerate((-1.13, 1.08)):
        cylinder(f"Axle_{i + 1}", (x, 0, 0.49), 0.075, 1.95, "dark", "Y")
        for side in (-1, 1):
            wheel_rail(f"RailWheel_{i + 1}_{'L' if side < 0 else 'R'}", x, side)
            box(f"Axlebox_{i + 1}_{side}", (x, side * 0.57, 0.67), (0.32, 0.24, 0.31), "dark", 0.05)
            for k in range(3):
                box(f"LeafSpring_{i + 1}_{side}_{k}", (x, side * 0.51, 0.78 + k * 0.035),
                    (0.55 - 0.08 * k, 0.12, 0.027), "steel", 0.01)
    group("02_Chassis_And_Safety_Steps")
    box("MainChassis", (0, 0, 0.86), (3.3, 1.5, 0.26), "dark", 0.10)
    box("WalkDeck", (0.12, 0, 1.01), (2.95, 1.5, 0.10), "red", 0.04)
    for side in (-1, 1):
        for i, x in enumerate((-1.10, 1.08)):
            box(f"WheelGuard_{side}_{i}", (x, side * 0.82, 1.02), (0.94, 0.42, 0.13), "red", 0.06)
            box(f"GuardIvoryLip_{side}_{i}", (x, side * 1.01, 1.035), (0.91, 0.045, 0.08), "ivory", 0.022)
        for i, (z, yy, length) in enumerate(((0.59, 1.00, 0.65), (0.81, 0.86, 0.78))):
            box(f"AccessStep_{side}_{i}", (0.04, side * yy, z), (length, 0.36, 0.09), "dark", 0.032)
            box(f"StepSafetyNose_{side}_{i}", (0.04, side * (yy + 0.16), z + 0.027),
                (length - 0.03, 0.05, 0.045), "brass", 0.014)
            for k in range(6):
                box(f"StepGrip_{side}_{i}_{k}", (-0.22 + 0.10 * k, side * yy, z + 0.052),
                    (0.024, 0.22, 0.012), "steel", 0.004)
    box("RearBuffer", (1.72, 0, 0.91), (0.20, 1.64, 0.25), "dark", 0.055)
    group("03_Hood_And_Inspection_Sensors")
    box("RoundedHood", (-1.01, 0, 1.38), (1.1, 1.18, 0.74), "red", 0.16)
    box("IvoryHoodCap", (-1.01, 0, 1.75), (1.11, 1.19, 0.15), "ivory", 0.075)
    box("RadiatorSurround", (-1.58, 0, 1.39), (0.075, 0.80, 0.59), "dark", 0.10)
    for k in range(8):
        box(f"RadiatorFin_{k + 1}", (-1.625, -0.31 + k * 0.089, 1.39),
            (0.034, 0.026, 0.45), "steel", 0.011)
    for side in (-1, 1):
        box(f"EngineSideInset_{side}", (-0.99, side * 0.598, 1.36), (0.63, 0.025, 0.36), "red", 0.05)
        for k in range(4):
            box(f"HoodSideLouver_{side}_{k}", (-1.01, side * 0.619, 1.25 + k * 0.075),
                (0.44, 0.035, 0.025), "dark", 0.01)
        cylinder(f"HeadlampHousing_{side}", (-1.63, side * 0.62, 1.22), 0.135, 0.12, "dark", "X")
        cylinder(f"HeadlampLens_{side}", (-1.70, side * 0.62, 1.22), 0.106, 0.018, "light", "X")
    cylinder("HoodServiceCap", (-0.92, 0.26, 1.85), 0.09, 0.08, "dark")
    box("FrontSensorCrossbar", (-1.80, 0, 0.92), (0.23, 1.85, 0.22), "dark", 0.055)
    for i, y in enumerate((-0.65, 0.65)):
        box(f"InspectionSensorCase_{i + 1}", (-1.96, y, 0.98), (0.22, 0.30, 0.25), "brass", 0.06)
        cylinder(f"InspectionSensorLens_{i + 1}", (-2.085, y, 0.99), 0.077, 0.028, "dark", "X")
        cylinder(f"InspectionSensorGlass_{i + 1}", (-2.104, y, 0.99), 0.047, 0.012, "glass", "X")
    box("CenterTrackScanner", (-1.92, 0, 0.72), (0.24, 0.38, 0.20), "brass", 0.045)
    box("ScannerAperture", (-2.05, 0, 0.73), (0.018, 0.24, 0.09), "dark", 0.012)
    group("04_Open_Operator_Cab")
    for side in (-1, 1):
        beam(f"FrontCabPillar_{side}", (-0.42, side * 0.62, 1.05), (-0.30, side * 0.66, 2.62),
             0.13, 0.14, "ivory", 0.055)
        beam(f"RearCabPillar_{side}", (0.98, side * 0.62, 1.07), (0.86, side * 0.66, 2.62),
             0.15, 0.14, "ivory", 0.055)
        tube(f"BoardingGrabRail_{side}", [(-0.42, side * 0.84, 1.04), (-0.49, side * 0.84, 1.16),
             (-0.49, side * 0.84, 1.76), (-0.40, side * 0.77, 1.86)], 0.034, "brass")
        tube(f"RearGrabRail_{side}", [(0.95, side * 0.84, 1.05), (1.01, side * 0.84, 1.18),
             (1.01, side * 0.84, 1.75), (0.91, side * 0.74, 1.84)], 0.032, "brass")
    box("RoundedProtectiveRoof", (0.28, 0, 2.67), (1.85, 1.65, 0.23), "ivory", 0.115)
    box("RoofUnderside", (0.28, 0, 2.56), (1.60, 1.41, 0.07), "dark", 0.035)
    for side in (-1, 1):
        box(f"CabWorkLight_{side}", (-0.62, side * 0.53, 2.54), (0.10, 0.25, 0.15), "dark", 0.04)
        box(f"CabWorkLightLens_{side}", (-0.679, side * 0.53, 2.54), (0.02, 0.18, 0.10), "light", 0.025)
    cylinder("SeatPedestal", (0.49, 0, 1.16), 0.12, 0.28, "dark")
    box("OperatorSeatCushion", (0.48, 0, 1.38), (0.57, 0.62, 0.17), "rubber", 0.08)
    box("OperatorSeatBack", (0.76, 0, 1.77), (0.16, 0.62, 0.70), "rubber", 0.075,
        (0, -0.11, 0))
    box("SeatBackInset", (0.666, 0, 1.79), (0.045, 0.44, 0.46), "dark", 0.06, (0, -0.11, 0))
    rod("SteeringColumn", (-0.35, 0, 1.22), (-0.17, 0, 1.70), 0.047, "dark")
    wheel = torus("SteeringWheel", (-0.17, 0, 1.72), 0.215, 0.027, "rubber")
    wheel.rotation_euler[1] = 0.36
    for k in range(3):
        a = 2 * math.pi * k / 3
        rod(f"SteeringSpoke_{k}", (-0.17, 0, 1.72), (-0.17 + 0.19 * math.cos(a), 0.19 * math.sin(a), 1.72),
            0.014, "dark")
    box("OperatorConsole", (-0.32, 0.36, 1.47), (0.20, 0.31, 0.29), "dark", 0.055)
    box("ConsoleGauge", (-0.43, 0.36, 1.54), (0.015, 0.19, 0.09), "glass", 0.015)
    cylinder("BeaconBase", (0.49, 0.06, 2.82), 0.10, 0.07, "dark")
    cylinder("BeaconLens", (0.49, 0.06, 2.92), 0.082, 0.15, "amber", bevel=0.035)
    group("05_Rear_Service_Toolbox")
    box("ToolboxBody", (1.21, 0, 1.33), (0.61, 1.20, 0.45), "red", 0.065)
    box("ToolboxLid", (1.21, 0, 1.58), (0.65, 1.24, 0.09), "red", 0.04)
    for side in (-1, 1):
        box(f"ToolboxLatch_{side}", (1.55, side * 0.36, 1.43), (0.035, 0.10, 0.16), "brass", 0.02)
        box(f"RearMarker_{side}", (1.83, side * 0.58, 0.95), (0.025, 0.13, 0.09), "amber", 0.02)
    tube("ToolboxTopHandle", [(1.06, -0.21, 1.65), (1.06, -0.21, 1.72),
                               (1.36, -0.21, 1.72), (1.36, -0.21, 1.65)], 0.024, "dark")
    tube("RearSafetyRail", [(1.58, -0.68, 1.08), (1.58, -0.68, 1.75),
                            (1.58, 0.68, 1.75), (1.58, 0.68, 1.08)], 0.033, "dark")


def build_shuttle():
    group("01_Six_Wheel_Running_Gear")
    for i, x in enumerate((-2.12, -0.83, 2.08)):
        cylinder(f"RoadAxle_{i + 1}", (x, 0, 0.49), 0.085, 2.15, "dark", "Y")
        for side in (-1, 1):
            wheel_rubber(f"RoadWheel_{i + 1}_{'L' if side < 0 else 'R'}", x, side)
    group("02_Chassis_And_Load_Bay")
    box("LongLowChassis", (0, 0, 0.79), (5.7, 2.1, 0.43), "red", 0.14)
    box("DarkLowerSill", (0, 0, 0.58), (5.5, 1.86, 0.18), "dark", 0.07)
    box("RecessedLoadDeck", (0.71, 0.15, 1.035), (3.46, 1.76, 0.11), "dark", 0.04)
    for side in (-1, 1):
        box(f"BaySideRail_{side}", (0.65, side * 1.01, 1.05), (3.38, 0.13, 0.13), "ivory", 0.035)
        box(f"ChassisAmberMarker_{side}", (1.55, side * 1.065, 0.82), (0.22, 0.025, 0.10), "amber", 0.025)
        box(f"FrontWheelFender_{side}", (-1.53, side * 1.0, 1.00), (2.2, 0.41, 0.20), "red", 0.08)
        box(f"RearWheelFender_{side}", (2.1, side * 1.0, 1.00), (1.12, 0.41, 0.20), "red", 0.08)
    box("RearPowerPack", (2.33, 0.16, 1.43), (0.68, 1.75, 0.78), "red", 0.11)
    for k in range(5):
        box(f"RearCoolingSlat_{k}", (2.688, 0.15, 1.22 + k * 0.105), (0.025, 1.18, 0.043), "dark", 0.015)
    box("RearImpactBuffer", (2.91, 0, 0.78), (0.21, 2.16, 0.34), "dark", 0.075)
    for side in (-1, 1):
        box(f"RearLamp_{side}", (3.024, side * 0.77, 0.91), (0.025, 0.20, 0.095), "amber", 0.02)
    group("03_Offset_Operator_Cabin")
    box("CabIvoryShell", (-1.91, 0.17, 2.01), (1.68, 1.74, 2.08), "ivory", 0.23)
    box("CabLowerRedDoorBand", (-1.91, 0.17, 1.31), (1.73, 1.79, 0.64), "red", 0.14)
    box("CabRoofCap", (-1.91, 0.17, 3.055), (1.75, 1.83, 0.16), "red", 0.08)
    box("FrontGlazingFrame", (-2.765, 0.17, 2.32), (0.065, 1.48, 1.32), "dark", 0.18)
    box("FrontGlazing", (-2.803, 0.17, 2.33), (0.025, 1.30, 1.16), "glass", 0.125)
    box("WindshieldDivider", (-2.823, 0.17, 2.34), (0.025, 0.045, 1.14), "ivory", 0.014)
    for side in (-1, 1):
        yy = 0.17 + side * 0.885
        box(f"SideWindowFrame_{side}", (-1.91, yy, 2.34), (1.32, 0.04, 1.26), "dark", 0.13)
        box(f"SideWindowPane_{side}", (-1.91, yy + side * 0.027, 2.36), (1.16, 0.025, 1.08), "glass", 0.10)
        box(f"DoorHandle_{side}", (-1.43, yy + side * 0.035, 1.56), (0.20, 0.055, 0.06), "brass", 0.026)
        rod(f"MirrorStem_{side}", (-2.48, yy, 2.38), (-2.49, yy + side * 0.24, 2.39), 0.025, "dark")
        box(f"SideMirror_{side}", (-2.49, yy + side * 0.26, 2.40), (0.11, 0.12, 0.32), "dark", 0.048)
    box("RedFrontNose", (-2.73, 0.10, 1.31), (0.39, 1.91, 0.62), "red", 0.13)
    box("FrontRadiator", (-2.945, 0.10, 1.28), (0.045, 0.61, 0.37), "dark", 0.05)
    for k in range(4):
        box(f"FrontRadiatorLouver_{k}", (-2.974, 0.10, 1.15 + k * 0.086), (0.025, 0.52, 0.027), "steel", 0.009)
    for side in (-1, 1):
        y = 0.10 + side * 0.70
        box(f"FrontLampFrame_{side}", (-2.929, y, 1.35), (0.06, 0.20, 0.38), "dark", 0.05)
        box(f"FrontHeadlamp_{side}", (-2.968, y, 1.43), (0.02, 0.14, 0.16), "light", 0.04)
        box(f"FrontIndicator_{side}", (-2.968, y, 1.24), (0.02, 0.14, 0.08), "amber", 0.025)
    box("FrontImpactBuffer", (-2.97, 0, 0.82), (0.23, 2.18, 0.34), "dark", 0.075)
    box("BoardingStep", (-1.86, -0.96, 0.99), (0.77, 0.37, 0.10), "dark", 0.03)
    box("BoardingStepSafetyLip", (-1.86, -1.16, 1.02), (0.70, 0.05, 0.055), "brass", 0.014)
    cylinder("CabBeaconBase", (-1.88, 0.18, 3.17), 0.115, 0.07, "dark")
    cylinder("CabBeacon", (-1.88, 0.18, 3.28), 0.095, 0.17, "amber", bevel=0.04)
    for y in (-0.45, 0.78):
        box(f"RoofWorkLamp_{y}", (-2.72, y, 3.03), (0.11, 0.22, 0.15), "dark", 0.035)
        box(f"RoofWorkLampLens_{y}", (-2.784, y, 3.03), (0.02, 0.15, 0.095), "light", 0.025)
    group("04_Side_Loading_Mast_And_Forks")
    for i, x in enumerate((-0.15, 1.05)):
        box(f"TraverseRail_{i + 1}", (x, -0.16, 1.10), (0.16, 2.27, 0.14), "steel", 0.03)
        box(f"MastOuterRedHousing_{i + 1}", (x, -0.95, 2.27), (0.24, 0.32, 2.48), "red", 0.075)
        box(f"MastInnerGuide_{i + 1}", (x, -1.14, 2.25), (0.12, 0.11, 2.31), "steel", 0.022)
        box(f"MastFoot_{i + 1}", (x, -0.95, 1.17), (0.41, 0.46, 0.24), "dark", 0.055)
        for z in (1.30, 3.28):
            bolt(f"MastGuideBolt_{i}_{z}", (x, -1.225, z), radius=0.048)
    box("MastTopBridge", (0.45, -0.95, 3.47), (1.61, 0.38, 0.27), "red", 0.075)
    box("CarriageCrosshead", (0.45, -1.20, 1.74), (1.53, 0.27, 0.42), "dark", 0.065)
    cylinder("MainLiftCylinder", (0.45, -0.97, 1.89), 0.108, 1.47, "brass")
    cylinder("PolishedHydraulicRam", (0.45, -0.97, 2.88), 0.058, 0.72, "steel")
    box("HydraulicRamAnchor", (0.45, -0.97, 3.29), (0.26, 0.27, 0.17), "dark", 0.045)
    for i, x in enumerate((0.0, 0.90)):
        box(f"ForkVerticalHeel_{i + 1}", (x, -1.35, 1.42), (0.17, 0.19, 0.80), "dark", 0.045)
        box(f"SidewaysFork_{i + 1}", (x, -1.85, 1.065), (0.19, 1.22, 0.15), "dark", 0.065)
        box(f"BluntForkSafetyTip_{i + 1}", (x, -2.40, 1.07), (0.195, 0.16, 0.16), "brass", 0.06)
    tube("HydraulicHose", [(0.72, -0.90, 1.2), (0.83, -0.98, 1.77), (0.82, -1.02, 2.3),
                           (0.61, -1.04, 2.45)], 0.022, "rubber")
    group("05_Secured_Freight_Container")
    box("ContainerBody", (0.69, 0.25, 1.96), (2.66, 1.42, 1.60), "ivory", 0.075)
    for side in (-1, 1):
        y = 0.25 + side * 0.725
        for i in range(11):
            x = -0.47 + 0.232 * i
            box(f"ContainerCorrugation_{side}_{i:02}", (x, y, 1.96), (0.062, 0.035, 1.37), "ivory", 0.014)
        for z in (1.19, 2.73):
            box(f"ContainerEdgeRail_{side}_{z}", (0.69, y, z), (2.68, 0.095, 0.105), "stone", 0.026)
    for x in (-0.63, 2.01):
        for y in (-0.46, 0.96):
            box(f"ContainerCornerPost_{x}_{y}", (x, y, 1.96), (0.13, 0.14, 1.67), "stone", 0.026)
            for z in (1.18, 2.74):
                box(f"ContainerCornerCasting_{x}_{y}_{z}", (x, y, z), (0.20, 0.18, 0.17), "stone", 0.025)
                box(f"ContainerCornerSocket_{x}_{y}_{z}", (x, y - 0.095, z), (0.08, 0.012, 0.063), "dark", 0.018)
    box("ContainerRearDoorSeam", (2.04, 0.25, 1.96), (0.028, 0.025, 1.42), "dark", 0.007)
    for y in (-0.16, 0.66):
        rod(f"ContainerLockRod_{y}", (2.065, y, 1.31), (2.065, y, 2.59), 0.024, "dark")
        box(f"ContainerLockHandle_{y}", (2.105, y, 1.79), (0.04, 0.26, 0.045), "brass", 0.014)
    for x in (-0.68, 2.06):
        box(f"CargoSecuringStop_{x}", (x, 0.30, 1.14), (0.16, 1.58, 0.20), "red", 0.04)


def window_front(name, x, y, z, width, height, outward=-1, frame="dark"):
    box(name + "_Frame", (x, y, z), (width, 0.11, height), frame, 0.055)
    box(name + "_Pane", (x, y + outward * 0.065, z), (width - 0.14, 0.025, height - 0.14), "glass", 0.035)
    box(name + "_Mullion", (x, y + outward * 0.085, z), (0.045, 0.035, height - 0.12), "ivory", 0.012)
    box(name + "_Transom", (x, y + outward * 0.085, z), (width - 0.12, 0.035, 0.045), "ivory", 0.012)


def crate(name, loc, size):
    box(name + "_Body", loc, size, "wood", 0.04)
    x, y, z = loc
    sx, sy, sz = size
    for side in (-1, 1):
        yy = y + side * (sy / 2 + 0.015)
        for xx in (x - sx * 0.39, x + sx * 0.39):
            box(name + f"_FrontStile_{side}_{xx}", (xx, yy, z), (0.075, 0.045, sz * 0.95), "stone", 0.018)
        for zz in (z - sz * 0.39, z + sz * 0.39):
            box(name + f"_FrontRail_{side}_{zz}", (x, yy, zz), (sx * 0.95, 0.045, 0.075), "stone", 0.018)
        beam(name + f"_DiagonalBrace_{side}", (x - sx * .36, yy, z - sz * .33),
             (x + sx * .36, yy, z + sz * .33), .07, .045, "stone", .016)


def canopy_lamp(name, loc):
    x, y, z = loc
    cylinder(name + "_Stem", (x, y, z + 0.12), 0.025, 0.24, "dark")
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.20, radius2=0.09, depth=0.14,
                                   location=(x, y, z - 0.02))
    o = adopt(bpy.context.object, name + "_Shade", "dark", "conical side strip and caps")
    softened(o, 0.012)
    cylinder(name + "_WarmLens", (x, y, z - 0.10), 0.155, 0.025, "light")


def build_station():
    group("01_Raised_Loading_Platform_And_Ramp")
    box("LoadingPlatformFoundation", (0.25, -0.10, 0.36), (9.50, 5.6, 0.72), "stone", 0.11)
    box("PlatformDeck", (0.25, -0.10, 0.755), (9.54, 5.64, 0.09), "stone", 0.035)
    box("PlatformSafetyEdge", (-0.5, -2.89, 0.80), (8.0, 0.105, 0.08), "brass", 0.026)
    for i, x in enumerate((-3.85, -2.25, -0.65, 0.95, 2.55)):
        box(f"DockRubberBumper_{i + 1}", (x, -2.95, 0.43), (0.25, 0.17, 0.55), "rubber", 0.05)
        for z in (0.23, 0.62):
            bolt(f"DockBumperAnchor_{i}_{z}", (x, -3.044, z), radius=0.032)
    for i in range(9):
        box(f"PlatformPanelJoint_{i}", (-4.10 + i, -2.906, 0.39), (0.014, 0.016, 0.53), "mortar", 0.002)
    x0, x1, y0, y1, z = 3.12, 4.67, -5.05, -2.64, 0.80
    verts = [(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0),
             (x0, y0, 0.06), (x1, y0, 0.06), (x1, y1, z), (x0, y1, z)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh_part("AttachedLoadingRamp", verts, faces, "stone", bevel=0.035)
    for xx in (x0 + 0.04, x1 - 0.04):
        beam(f"RampSafetyEdge_{xx}", (xx, y0 + .04, .085), (xx, y1 - .04, .835),
             .07, .035, "brass", .012)
    group("02_Warehouse_Masonry_And_Cargo_Opening")
    box("WarehouseRearWall", (-0.65, 2.23, 2.25), (6.70, 0.28, 2.90), "brick", .055)
    box("WarehouseLeftEndWall", (-3.88, .40, 2.25), (.26, 3.65, 2.90), "brick", .055)
    box("WarehouseRightEndWall", (2.58, .40, 2.25), (.26, 3.65, 2.90), "brick", .055)
    box("CargoOpeningLeftPier", (-2.97, -1.44, 2.21), (1.97, .28, 2.82), "brick", .05)
    box("CargoOpeningRightPier", (1.99, -1.44, 2.21), (1.14, .28, 2.82), "brick", .05)
    box("CargoDoorHeader", (-.65, -1.44, 3.40), (6.68, .28, .62), "brick", .05)
    box("InteriorWarehouseFloor", (-.65, .40, .825), (6.35, 3.48, .06), "wood", .018)
    for x in (-3.87, 2.58):
        gable(f"BarrelGable_{x}", x, .40, 3.70, 3.65, 1.27, .25, "brick")
    for i in range(9):
        zz = 1.02 + i * .29
        for x, width in ((-2.97, 1.91), (1.99, 1.08)):
            box(f"FrontMortarCourse_{x}_{i}", (x, -1.588, zz), (width, .016, .018), "mortar", .003)
        box(f"RearMortarCourse_{i}", (-.65, 2.379, zz), (6.54, .016, .018), "mortar", .003)
    for x in (-3.86, 2.58):
        for y in (-1.43, 2.23):
            for i in range(5):
                box(f"WarehouseCornerQuoin_{x}_{y}_{i}", (x, y, 1.05 + i * .57),
                    (.38, .39, .22), "stone", .035)
    box("CargoDoorLintel", (-.26, -1.63, 3.095), (3.77, .16, .16), "ivory", .035)
    for x in (-2.10, 1.58):
        box(f"CargoOpeningJamb_{x}", (x, -1.64, 1.94), (.17, .18, 2.34), "ivory", .03)
    for i, x in enumerate((-2.66, 2.05)):
        box(f"OpenSlidingDoorLeaf_{i}", (x, -1.70, 1.91), (1.00, .13, 2.20), "dark", .065)
        for k in range(5):
            box(f"DoorPanelRib_{i}_{k}", (x - .38 + .19 * k, -1.78, 1.91), (.028, .025, 2.04), "steel", .009)
        box(f"DoorPull_{i}", (x, -1.82, 1.83), (.05, .07, .27), "brass", .022)
    box("SlidingDoorTrack", (-.36, -1.70, 3.15), (5.90, .15, .13), "dark", .035)
    for i in range(5):
        window_front(f"CargoTransom_{i}", -1.75 + i * .75, -1.61, 3.44, .68, .40)
    for i in range(3):
        window_front(f"RearServiceWindow_{i}", -2.57 + i * 1.92, 2.40, 2.41, 1.25, .88, outward=1)
    group("03_Barrel_Roof_And_Ventilation")
    barrel("MainBarrelRoof", (-.65, .40, 3.74), 7.15, 4.14, 1.43, .16, "dark")
    for x in (-4.23, 2.93):
        barrel_rib(f"RoofEndFascia_{x}", (x, .40, 3.75), 4.15, 1.43, .072, "steel")
    for i in range(9):
        barrel_rib(f"StandingRoofSeam_{i}", (-3.77 + i * .79, .40, 3.756), 4.13, 1.43, .018, "steel")
    for side in (-1, 1):
        cylinder(f"RoofEaveGutter_{side}", (-.65, .40 + side * 2.09, 3.73), .064, 7.20, "steel", "X")
        tube(f"RearDownpipe_{side}", [(-4.08, .40 + side * 2.06, 3.70), (-4.08, .40 + side * 2.16, 3.50),
                                     (-4.08, .40 + side * 2.16, 1.02), (-4.00, .40 + side * 2.28, .86)],
             .047, "dark")
    for i, x in enumerate((-2.51, 1.13)):
        cylinder(f"RoofVentStem_{i}", (x, .40, 5.24), .18, .36, "steel")
        cylinder(f"RoofVentBand_{i}", (x, .40, 5.41), .24, .12, "brass")
        cylinder(f"RoofVentMushroom_{i}", (x, .40, 5.50), .32, .10, "dark", bevel=.04)
    group("04_Loading_Canopy_And_Stout_Columns")
    box("LoadingCanopyRoof", (-.67, -2.13, 3.28), (7.95, 1.82, .15), "dark", .065,
        (math.radians(3), 0, 0))
    box("CanopyIvoryFascia", (-.67, -3.035, 3.225), (7.97, .105, .17), "ivory", .03)
    box("CanopySafetyTrim", (-.67, -3.095, 3.263), (7.91, .025, .036), "brass", .011)
    for i, x in enumerate((-3.69, -1.99, 1.86)):
        box(f"CanopyColumn_{i}", (x, -2.58, 1.97), (.20, .22, 2.36), "dark", .035)
        box(f"CanopyColumnFoot_{i}", (x, -2.58, .91), (.36, .37, .22), "steel", .045)
        for direction in (-1, 1):
            tube(f"ColumnCurvedBrace_{i}_{direction}", [(x, -2.58, 2.65), (x + direction * .10, -2.58, 2.86),
                                                       (x + direction * .35, -2.58, 3.05),
                                                       (x + direction * .58, -2.58, 3.14)], .05, "dark")
        tube(f"ColumnCollisionGuard_{i}", [(x - .23, -2.82, .83), (x - .23, -2.82, 1.30),
                                            (x + .23, -2.82, 1.30), (x + .23, -2.82, .83)], .043, "brass")
    for i, x in enumerate((-2.86, .55)):
        canopy_lamp(f"CanopyWorkLight_{i}", (x, -2.17, 2.98))
    group("05_Attached_Side_Office")
    box("OfficeMasonry", (3.69, .40, 1.84), (1.92, 3.66, 2.07), "brick", .085)
    box("OfficeStonePlinth", (3.69, .40, .94), (2.02, 3.77, .28), "stone", .05)
    box("OfficeCornice", (3.69, .40, 2.92), (2.13, 3.87, .16), "ivory", .045)
    barrel("OfficeShallowBarrelRoof", (3.69, .40, 3.00), 2.20, 3.96, .62, .12, "dark")
    for x in (2.57, 4.81):
        barrel_rib(f"OfficeRoofEnd_{x}", (x, .40, 3.00), 3.97, .62, .05, "steel")
    for i in range(5):
        barrel_rib(f"OfficeRoofSeam_{i}", (2.82 + .43 * i, .40, 3.012), 3.95, .62, .015, "steel")
    box("OfficeDoorSurround", (3.16, -1.475, 1.80), (.78, .12, 1.89), "ivory", .055)
    box("OfficeDoor", (3.16, -1.55, 1.79), (.62, .06, 1.73), "dark", .04)
    box("OfficeDoorUpperGlass", (3.16, -1.59, 2.13), (.44, .025, .72), "glass", .035)
    box("OfficeDoorHandle", (3.38, -1.62, 1.61), (.045, .065, .18), "brass", .018)
    window_front("OfficeFrontWindow", 4.18, -1.475, 1.98, .88, 1.05)
    box("OfficeSideWindowFrame", (4.679, .35, 1.99), (.10, 1.65, 1.02), "dark", .05)
    box("OfficeSideGlazing", (4.737, .35, 1.99), (.025, 1.49, .86), "glass", .03)
    for y in (-.13, .35, .83):
        box(f"OfficeSideMullion_{y}", (4.759, y, 1.99), (.03, .045, .88), "ivory", .012)
    for i in range(6):
        box(f"OfficeMasonryCourse_{i}", (4.659, .40, 1.18 + i * .25), (.018, 3.5, .016), "mortar", .003)
    tube("OfficePlatformGuard", [(4.84, -1.72, .84), (4.84, -1.72, 1.65),
                                  (4.84, 2.30, 1.65), (4.84, 2.30, .84)], .045, "dark")
    for y in (-.5, .8):
        rod(f"OfficeGuardUpright_{y}", (4.84, y, .84), (4.84, y, 1.65), .037, "brass")
    group("06_Interior_Freight_And_Attached_Fixtures")
    box("InteriorPallet", (-1.22, .12, .94), (1.82, 1.17, .18), "wood", .03)
    crate("FreightCrate_A", (-1.58, .12, 1.46), (.80, .87, .86))
    crate("FreightCrate_B", (-.68, .12, 1.46), (.80, .87, .86))
    crate("FreightCrate_C", (-1.58, .12, 2.26), (.74, .79, .72))
    box("InteriorRearBench", (.68, 1.59, 1.15), (1.67, .56, .16), "wood", .035)
    for x in (.05, 1.30):
        box(f"BenchLeg_{x}", (x, 1.59, .98), (.10, .45, .35), "dark", .025)
    canopy_lamp("InteriorPendant", (-.65, .60, 3.85))


def build_signal_house():
    group("01_Masonry_Base_And_Doors")
    box("BuildingFoundation", (0, .18, .12), (3.82, 3.34, .24), "stone", .10)
    box("GroundFloorMasonry", (0, .18, 1.32), (3.53, 3.05, 2.25), "brick", .095)
    for i in range(9):
        z = .38 + i * .23
        for side in (-1, 1):
            box(f"GroundFrontRearMortar_{side}_{i}", (0, .18 + side * 1.533, z),
                (3.32, .012, .016), "mortar", .003)
            box(f"GroundSideMortar_{side}_{i}", (side * 1.773, .18, z),
                (.012, 2.86, .016), "mortar", .003)
    for x in (-1.70, 1.70):
        for y in (-1.27, 1.63):
            for i in range(5):
                box(f"RoundedStoneQuoin_{x}_{y}_{i}", (x, y, .43 + i * .45),
                    (.34, .35, .23), "stone", .045)
    box("GroundDoorStoneSurround", (-.99, -1.395, 1.21), (.91, .13, 1.94), "stone", .13)
    box("GroundServiceDoor", (-.99, -1.477, 1.20), (.70, .07, 1.73), "dark", .08)
    box("GroundDoorGlazing", (-.99, -1.522, 1.48), (.48, .025, .78), "glass", .045)
    box("GroundDoorMullion", (-.99, -1.544, 1.48), (.035, .025, .75), "ivory", .01)
    cylinder("GroundDoorKnob", (-.74, -1.56, .93), .042, .055, "brass", "Y")
    box("GroundDoorStep", (-.99, -1.65, .15), (1.04, .52, .25), "stone", .07)
    window_front("GroundRearWindow", .28, 1.76, 1.35, 1.35, .91, outward=1)
    group("02_Glazed_Upper_Operator_Room")
    box("UpperFloorBand", (0, .18, 2.48), (3.87, 3.39, .21), "dark", .055)
    box("UpperRoomFloor", (0, .18, 2.59), (3.65, 3.17, .08), "wood", .025)
    box("UpperIvoryKickPanel", (0, .18, 2.85), (3.69, 3.21, .48), "ivory", .045)
    box("WindowSillBand", (0, .18, 3.095), (3.86, 3.38, .10), "dark", .025)
    box("UpperRoomTopBeam", (0, .18, 4.45), (3.85, 3.37, .16), "ivory", .04)
    for x in (-1.80, 1.80):
        for y in (-1.37, 1.73):
            box(f"OperatorRoomCornerPost_{x}_{y}", (x, y, 3.76), (.15, .16, 1.31), "dark", .035)
    for side in (-1, 1):
        y = .18 + side * 1.61
        for i in range(4):
            x = -1.33 + i * .885
            box(f"UpperFrontRearPane_{side}_{i}", (x, y, 3.76), (.81, .045, 1.19), "glass", .045)
            if i < 3:
                box(f"UpperFrontRearMullion_{side}_{i}", (x + .442, y + side * .035, 3.76),
                    (.055, .055, 1.30), "ivory", .014)
        box(f"UpperWindowCrossrail_{side}", (0, y + side * .036, 3.70), (3.54, .05, .05), "ivory", .012)
    for side in (-1, 1):
        x = side * 1.845
        for i in range(3):
            y = -.86 + i * 1.04
            box(f"UpperSidePane_{side}_{i}", (x, y, 3.76), (.045, .96, 1.19), "glass", .045)
            if i < 2:
                box(f"UpperSideMullion_{side}_{i}", (x + side * .035, y + .52, 3.76),
                    (.055, .055, 1.29), "ivory", .013)
        box(f"UpperSideWindowCrossrail_{side}", (x + side * .036, .18, 3.70), (.05, 3.05, .05), "ivory", .012)
    box("UpperStairDoor", (-1.90, 1.02, 3.45), (.11, .81, 1.73), "dark", .055)
    box("UpperStairDoorPane", (-1.967, 1.02, 3.70), (.025, .61, 1.00), "glass", .035)
    box("UpperStairDoorHandle", (-1.999, .74, 3.19), (.055, .045, .18), "brass", .015)
    group("03_Shallow_Curved_Roof_And_Chimney")
    barrel("ShallowCurvedRoof", (0, .18, 4.51), 3.75, 4.17, .65, .14, "dark", along="Y")
    for y in (-1.72, 2.08):
        barrel_rib(f"CurvedRoofFascia_{y}", (0, y, 4.52), 4.18, .65, .065, "steel", along="Y")
    for i in range(6):
        barrel_rib(f"CurvedRoofSeam_{i}", (0, -1.43 + .64 * i, 4.525), 4.15, .65, .017, "steel", along="Y")
    for side in (-1, 1):
        cylinder(f"RoofGutter_{side}", (side * 2.10, .18, 4.51), .055, 3.83, "steel", "Y")
    tube("RearRainDownpipe", [(1.98, 1.81, 4.49), (1.88, 1.91, 4.24),
                               (1.88, 1.91, .32), (1.95, 2.02, .19)], .045, "dark")
    box("ChimneyBrickStack", (-.91, .93, 5.16), (.47, .49, .70), "brick", .05)
    for i in range(3):
        box(f"ChimneyMortarBand_{i}", (-.91, .93, 4.95 + i * .18), (.483, .503, .018), "mortar", .008)
    box("ChimneyStoneCap", (-.91, .93, 5.54), (.61, .63, .12), "stone", .045)
    cylinder("ChimneyFlue", (-.91, .93, 5.73), .14, .29, "dark")
    cylinder("ChimneyFlueLip", (-.91, .93, 5.88), .17, .06, "steel")
    group("04_External_Stout_Stairway")
    sx = -2.55
    box("StairLowerFooting", (sx, -2.42, .11), (1.35, .69, .22), "stone", .07)
    for i in range(11):
        y = -2.39 + i * .294
        z = .23 + i * .229
        box(f"StairTread_{i + 1:02}", (sx, y, z), (1.13, .33, .13), "stone", .035)
        box(f"StairNose_{i + 1:02}", (sx, y - .159, z + .023), (1.07, .035, .055), "ivory", .012)
    box("UpperStairLanding", (sx, 1.02, 2.57), (1.26, 1.02, .17), "dark", .035)
    for x in (-3.11, -1.99):
        beam(f"StairStructuralStringer_{x}", (x, -2.55, .19), (x, .64, 2.56), .13, .18, "dark", .035)
        for i in (0, 3, 7, 10):
            y = -2.39 + i * .294
            z = .23 + i * .229
            box(f"StairBaluster_{x}_{i}", (x, y, z + .46), (.085, .085, .97), "dark", .023)
            sphere(f"StairPostCap_{x}_{i}", (x, y, z + .98), (.061, .061, .061), "brass")
        beam(f"StairHandrail_{x}", (x, -2.48, 1.18), (x, .66, 3.58), .085, .09, "dark", .032)
        beam(f"StairIntermediateRail_{x}", (x, -2.44, .72), (x, .64, 3.12), .045, .055, "dark", .018)
    for x in (-3.11, -1.99):
        box(f"LandingRearPost_{x}", (x, 1.50, 3.04), (.09, .09, 1.02), "dark", .025)
    beam("LandingBackGuard", (-3.11, 1.5, 3.57), (-1.99, 1.5, 3.57), .085, .085, "dark", .03)
    beam("LandingOuterGuard", (-3.11, .61, 3.57), (-3.11, 1.5, 3.57), .085, .085, "dark", .03)
    group("05_Visible_Mechanical_Linkage_Cabinet")
    box("LinkageCabinetFoundation", (.62, -1.77, .14), (1.66, .88, .28), "stone", .07)
    box("LinkageCabinetBack", (.62, -1.56, 1.27), (1.42, .15, 1.98), "dark", .055)
    for x in (-.12, 1.36):
        box(f"CabinetSideWall_{x}", (x, -1.76, 1.30), (.13, .49, 2.02), "dark", .045)
        for z in (.43, 1.13, 2.08):
            bolt(f"CabinetRivet_{x}_{z}", (x, -2.02, z), mat="brass", radius=.027)
    box("CabinetLowerSill", (.62, -1.77, .34), (1.59, .55, .17), "dark", .04)
    barrel("CabinetRoundedTop", (.62, -1.76, 2.28), .62, 1.60, .25, .10, "dark", along="Y")
    for i in range(4):
        x = .10 + i * .35
        rod(f"CabinetVerticalRod_{i}", (x, -1.87, .48), (x, -1.87, 2.14), .027, "steel")
        for z in (.61, 1.73, 2.07):
            box(f"RodGuide_{i}_{z}", (x, -1.86, z), (.13, .10, .075), "brass", .018)
        torus(f"LinkageCrankWheel_{i}", (x, -1.99, .95 + (i % 2) * .29), .125, .026, "brass", "Y")
        cylinder(f"LinkageCrankHub_{i}", (x, -1.99, .95 + (i % 2) * .29), .05, .10, "dark", "Y")
        rod(f"LinkageCrankArm_{i}", (x, -2.05, .95 + (i % 2) * .29),
             (x + .09, -2.05, 1.04 + (i % 2) * .29), .024, "brass")
    rod("CabinetCrossShaft", (-.07, -1.99, .71), (1.31, -1.99, .71), .043, "steel")
    group("06_Semaphore_And_External_Linkages")
    box("SemaphoreFooting", (2.48, -1.06, .13), (.64, .65, .26), "stone", .09)
    box("SemaphoreBasePlate", (2.48, -1.06, .29), (.40, .41, .12), "dark", .035)
    cylinder("SemaphorePost", (2.48, -1.06, 1.94), .092, 3.27, "dark")
    for z in (.43, 1.16, 3.27):
        cylinder(f"SemaphoreCollar_{z}", (2.48, -1.06, z), .133, .105, "steel")
    sphere("SemaphoreFinial", (2.48, -1.06, 3.69), (.13, .13, .14), "brass")
    box("SemaphorePaddle", (3.19, -1.08, 3.36), (1.58, .13, .29), "red", .12)
    box("SemaphoreIvoryBand", (3.49, -1.158, 3.36), (.16, .016, .26), "ivory", .018)
    cylinder("SemaphorePivotPlate", (2.48, -1.185, 3.36), .225, .13, "dark", "Y")
    cylinder("SemaphorePivotHub", (2.48, -1.27, 3.36), .108, .06, "brass", "Y")
    rod("SemaphoreUpperLink", (2.30, -1.22, 3.22), (2.30, -1.22, 1.10), .029, "brass")
    cylinder("SemaphoreBellcrankPivot", (2.40, -1.23, 1.03), .095, .12, "dark", "Y")
    rod("SemaphoreBellcrank", (2.29, -1.30, 1.15), (2.50, -1.30, .95), .036, "brass")
    rod("CabinetToSemaphorePushrod", (1.26, -1.98, .71), (2.48, -1.30, .95), .026, "brass")
    group("07_Operator_Console_And_Service_Fixtures")
    box("UpperOperatorDesk", (.38, -.64, 3.19), (2.10, .58, .12), "wood", .04)
    box("LeverFrameBase", (.38, -.56, 3.32), (1.75, .22, .12), "dark", .028)
    for i in range(5):
        x = -.30 + i * .34
        rod(f"OperatorLever_{i}", (x, -.56, 3.34), (x, -.50, 3.79), .021, "brass")
        sphere(f"OperatorLeverGrip_{i}", (x, -.50, 3.80), (.040, .040, .059), "dark")
    box("GroundRearVent", (-1.06, 1.762, 1.20), (.55, .08, .49), "dark", .04)
    for i in range(4):
        box(f"RearVentLouver_{i}", (-1.06, 1.82, 1.05 + .10 * i), (.45, .04, .031), "steel", .011)


BUILDERS = dict(zip(SLUGS, (build_trolley, build_shuttle, build_station, build_signal_house)))
BUILDERS[SLUG]()
bpy.context.view_layer.update()

# Authoring dimensions also drive studio camera placement. No independent checks.
bounds = [o.matrix_world @ Vector(p) for o in PARTS for p in o.bound_box]
lo = Vector(tuple(min(p[i] for p in bounds) for i in range(3)))
hi = Vector(tuple(max(p[i] for p in bounds) for i in range(3)))
dimensions = hi - lo
target = (lo + hi) * .5
asset["asset_slug"] = SLUG
asset["dimensions_m_at_authoring"] = list(dimensions)
asset["review_status"] = "deferred_by_user"

# Neutral studio is deliberately excluded from geometry exports.
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 3
scene.render.threads_mode = "FIXED"
scene.render.threads = 4
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.film_transparent = False
scene.view_settings.view_transform = "AgX"
scene.world.color = (.18, .18, .18)
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (.72, .75, .78, 1)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = .40

bpy.ops.mesh.primitive_plane_add(size=200, location=(target.x, target.y, lo.z - .025))
floor = bpy.context.object
floor.name = "STUDIO_NeutralGround"
for c in list(floor.users_collection):
    c.objects.unlink(floor)
studio.objects.link(floor)
floor.data.materials.append(material("STUDIO_NeutralPearl", "D8D8D3", 0, .85))


def area(name, offset, energy, size):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    studio.objects.link(obj)
    obj.location = target + Vector(offset)
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


scale = max(dimensions)
area("STUDIO_KeySoftbox", (-scale * .75, -scale, scale * 1.5), 200 * scale * scale, scale * .95)
area("STUDIO_FillSoftbox", (scale * .95, -scale * .15, scale * .9), 110 * scale * scale, scale * .8)
area("STUDIO_RimSoftbox", (scale * .30, scale * .8, scale * 1.25), 170 * scale * scale, scale * .7)
CAMERAS = {}
hero_vec = (1.15, -1.60, 1.03) if SLUG == "barrel_roof_freight_station" else (-1.15, -1.60, 1.03)
for name, v in (("hero", hero_vec), ("rear", (-hero_vec[0], -hero_vec[1], hero_vec[2]))):
    data = bpy.data.cameras.new("STUDIO_" + name)
    data.type = "ORTHO"
    data.lens = 50
    data.clip_start = .05
    data.clip_end = 1000
    cam = bpy.data.objects.new("STUDIO_" + name, data)
    studio.objects.link(cam)
    direction = Vector(v).normalized()
    cam.location = target + direction * scale * 3.0
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    inv = cam.rotation_euler.to_matrix().transposed()
    projected = [inv @ (p - target) for p in bounds]
    width = max(p.x for p in projected) - min(p.x for p in projected)
    height = max(p.y for p in projected) - min(p.y for p in projected)
    data.ortho_scale = max(width, height) * 1.24
    CAMERAS[name] = cam
scene.camera = CAMERAS["hero"]

# Store named editable parts and all studio setup in native Blender project.
bpy.ops.object.select_all(action="DESELECT")
for obj in PARTS:
    obj.select_set(True)
bpy.context.view_layer.objects.active = PARTS[0]
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (SLUG + ".blend")), check_existing=False)
bpy.ops.export_scene.gltf(filepath=str(OUT / (SLUG + ".glb")), export_format="GLB",
                           use_selection=True, export_apply=True, export_texcoords=True,
                           export_normals=True, export_materials="EXPORT", export_yup=True,
                           export_cameras=False, export_lights=False, export_animations=False)
bpy.ops.export_scene.fbx(filepath=str(OUT / (SLUG + ".fbx")), use_selection=True,
                         object_types={"MESH"}, use_mesh_modifiers=True, mesh_smooth_type="FACE",
                         use_tspace=False, add_leaf_bones=False, bake_anim=False,
                         axis_forward="-Z", axis_up="Y", apply_unit_scale=True)

captures = []
for name, cam in CAMERAS.items():
    scene.camera = cam
    scene.render.filepath = str(OUT / "renders" / (name + ".png"))
    t = time.perf_counter()
    begin = datetime.now(timezone.utc)
    bpy.ops.render.render(write_still=True)
    end = datetime.now(timezone.utc)
    captures.append({"file": f"renders/{name}.png", "camera": cam.name,
                     "location_m": list(cam.location), "rotation_euler_radians": list(cam.rotation_euler),
                     "orthographic_scale_m": cam.data.ortho_scale, "target_m": list(target),
                     "started_at_utc": begin.isoformat(), "finished_at_utc": end.isoformat(),
                     "render_seconds": time.perf_counter() - t})

END = datetime.now(timezone.utc)
metadata = {
    "asset": SLUG, "set": "Set07", "theme": "Rail freight", "authoring": "original procedural polygon mesh",
    "status": "produced_unreviewed", "review_status": "deferred_by_user",
    "reference": f"../REF/{SLUG}.png", "prompt": f"../REF/{SLUG}.prompt.txt",
    "units": "meters", "vertical_axis_native": "+Z", "vehicle_front_native": "-X" if SLUG in SLUGS[:2] else "-Y",
    "dimensions_m_at_authoring": [round(v, 5) for v in dimensions],
    "bounds_m_at_authoring": {"minimum": list(lo), "maximum": list(hi)},
    "dimensions_note": "Production measurements used for studio framing, not independent validation.",
    "collections": {"ASSET": "Editable named mesh parts by functional group", "STUDIO": "Cameras, lights and neutral floor; not exported"},
    "export_selection": "Only ASSET mesh objects; evaluated bevel and weighted-normal modifiers; no camera/light/animation exports",
    "uv_authoring": "Planar face islands for manufactured boxes/custom solids; cylindrical/cap UVs for wheels and rods; arc-length swept tube UVs; continuous outer/inner barrel shell islands. UVs are authored without validators.",
    "material_style": "Solid named PBR palette; no generated or photographic surface textures. Glazing is an opaque stylized blue-gray metal/roughness material.",
    "palette": [{"name": m.name, "srgb": m["palette_hex_srgb"]} for m in MAT.values()],
    "parts": [{"name": o.name, "group": o.users_collection[0].name, "material": o.data.materials[0].name,
               "uv_authoring": o["uv_authoring"]} for o in PARTS],
    "studio": {"engine": "Cycles CPU", "threads": 4, "samples": 48, "denoise": True,
               "resolution_px": [1024, 1024], "view_transform": "AgX", "background": "neutral soft studio", "captures": captures},
    "process_start_utc": START.isoformat(), "process_end_utc": END.isoformat(),
    "process_start_kst": START.astimezone(timezone(timedelta(hours=9))).isoformat(),
    "process_end_kst": END.astimezone(timezone(timedelta(hours=9))).isoformat(),
    "authoring_export_render_seconds": time.perf_counter() - T0,
    "limitations": ["Visual/model/UV review and export roundtrip are deferred by explicit user instruction.",
                    "No animation, rigging, collision or LOD assets were requested.",
                    "Hero/rear images are actual Blender renders and have not been opened for inspection."]
}
(OUT / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
print("SET07_PRODUCED", SLUG, "authoring_seconds", round(time.perf_counter() - T0, 3), flush=True)
