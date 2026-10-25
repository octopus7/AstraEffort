"""Original Set08 mesh authoring. Run one slug in an isolated Blender process.

This script creates assets and images; it does not reopen, reimport, inspect, or
validate them. Source references are read by the author, never used as textures.
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
SLUG = sys.argv[sys.argv.index('--') + 1]
OUT = ROOT / SLUG
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'renders').mkdir(exist_ok=True)
T0 = time.perf_counter()
START = datetime.now(timezone.utc)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection':
        bpy.data.collections.remove(c)
asset = bpy.data.collections.get('Collection')
asset.name = 'ASSET'
studio = bpy.data.collections.new('STUDIO')
bpy.context.scene.collection.children.link(studio)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 40
scene.cycles.use_denoising = True
scene.render.threads_mode = 'FIXED'
scene.render.threads = 4
scene.render.resolution_x = 960
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.film_transparent = False
scene.render.use_file_extension = True
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
scene.render.image_settings.color_depth = '8'
scene.render.fps = 24
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.67, 0.71, 0.76, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.45


def srgb(v):
    return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4


PALETTE = {
    'SteelBlue': ('5D7C8C', .35, .38),
    'BlueEdge': ('3E5666', .48, .33),
    'WarmIvory': ('D3CEC1', .18, .43),
    'Graphite': ('343C41', .55, .36),
    'CopperOrange': ('B97742', .40, .38),
    'BrushedSteel': ('919A9E', .72, .30),
    'Rubber': ('242B2E', .0, .68),
    'Masonry': ('BDB7A8', .0, .76),
    'Concrete': ('92958E', .0, .80),
    'MutedGlazing': ('5E757A', .22, .24),
    'AmberGlass': ('AA8A55', .12, .32),
    'PanelGreen': ('729B8B', .15, .42),
}
MATS = {}
for key, (hexcolor, metal, rough) in PALETTE.items():
    m = bpy.data.materials.new('Set08.' + key)
    m.use_nodes = True
    rgb = tuple(srgb(int(hexcolor[i:i + 2], 16) / 255) for i in (0, 2, 4))
    m.diffuse_color = (*rgb, 1)
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Roughness'].default_value = rough
    MATS[key] = m


def move_collection(o, target=asset):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    target.objects.link(o)
    return o


def finish(o, name, material, bevel=0, smooth=False):
    o.name = name
    o.data.name = name + '.Mesh'
    move_collection(o)
    o.data.materials.append(MATS[material])
    if smooth:
        for p in o.data.polygons:
            p.use_smooth = len(p.vertices) == 4 or len(p.vertices) == 3
    if bevel:
        mod = o.modifiers.new('Soft manufactured edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 3
        mod.limit_method = 'ANGLE'
        mod.angle_limit = .50
        mod.harden_normals = True
        normal = o.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
        normal.keep_sharp = True
        normal.weight = 35
    o['component'] = name
    o['surface_palette'] = material
    return o


def box(name, loc, dims, material, bevel=.06, rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if rotation:
        o.rotation_euler = rotation
    return finish(o, name, material, min(bevel, min(dims) * .40))


def align(o, direction):
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector(direction).normalized().to_track_quat('Z', 'Y')
    return o


def beam(name, a, b, width, depth, material, bevel=.04):
    a, b = Vector(a), Vector(b)
    o = box(name, (a + b) / 2, (width, depth, (b - a).length), material, bevel)
    return align(o, b - a)


def cyl(name, loc, radius, depth, material, axis=(0, 0, 1), bevel=.025, vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, end_fill_type='NGON', location=loc)
    o = finish(bpy.context.object, name, material, bevel, True)
    return align(o, axis)


def rod(name, a, b, radius, material, bevel=.012, vertices=24):
    a, b = Vector(a), Vector(b)
    return cyl(name, (a + b) / 2, radius, (b - a).length, material, b - a, bevel, vertices)


def torus(name, loc, radius, thickness, material, axis=(0, 0, 1)):
    bpy.ops.mesh.primitive_torus_add(major_segments=64, minor_segments=12, location=loc,
                                   major_radius=radius, minor_radius=thickness)
    o = finish(bpy.context.object, name, material, 0, True)
    return align(o, axis)


def sphere(name, loc, scale, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, radius=1, location=loc)
    o = bpy.context.object
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, name, material, 0, True)


def mesh(name, vertices, faces, material, bevel=0, smooth=False):
    data = bpy.data.meshes.new(name + '.Mesh')
    data.from_pydata(vertices, [], faces)
    data.update()
    o = bpy.data.objects.new(name, data)
    asset.objects.link(o)
    return finish(o, name, material, bevel, smooth)


def lathe(name, profile, loc, material, axis=(0, 0, 1), segments=64, extra_materials=None, segment_materials=None):
    verts, faces, rings, face_segments = [], [], [], []
    for r, z in profile:
        ring = []
        count = 1 if abs(r) < 1e-7 else segments
        for j in range(count):
            a = math.tau * j / segments
            ring.append(len(verts))
            verts.append((r * math.cos(a), r * math.sin(a), z))
        rings.append(ring)
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        if len(a) == 1 and len(b) == 1:
            continue
        for j in range(segments):
            k = (j + 1) % segments
            if len(a) == 1:
                faces.append((a[0], b[k], b[j]))
            elif len(b) == 1:
                faces.append((a[j], a[k], b[0]))
            else:
                faces.append((a[j], a[k], b[k], b[j]))
            face_segments.append(i)
    o = mesh(name, verts, faces, material, 0, True)
    if extra_materials:
        for m in extra_materials:
            o.data.materials.append(MATS[m])
    if segment_materials:
        for p, s in zip(o.data.polygons, face_segments):
            p.material_index = segment_materials.get(s, 0)
    o.location = loc
    align(o, axis)
    return o


def tube(name, points, radius, material, corrugations=0, samples_per_span=10, sides=12):
    """Catmull-Rom tube with stable local frames and closed ends."""
    pp = [Vector(p) for p in points]
    path = []
    for i in range(len(pp) - 1):
        p0, p1 = pp[max(0, i - 1)], pp[i]
        p2, p3 = pp[i + 1], pp[min(len(pp) - 1, i + 2)]
        for k in range(samples_per_span):
            t = k / samples_per_span
            path.append(.5 * ((2 * p1) + (-p0 + p2) * t +
                              (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    path.append(pp[-1])
    verts, faces = [], []
    for i, p in enumerate(path):
        tangent = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        helper = Vector((0, 0, 1)) if abs(tangent.z) < .9 else Vector((0, 1, 0))
        u = tangent.cross(helper).normalized()
        v = tangent.cross(u).normalized()
        rad = radius * (1 + .10 * math.cos(math.tau * corrugations * i / (len(path) - 1)))
        for j in range(sides):
            a = math.tau * j / sides
            verts.append(tuple(p + rad * (u * math.cos(a) + v * math.sin(a))))
    for i in range(len(path) - 1):
        for j in range(sides):
            k = (j + 1) % sides
            faces.append((i * sides + j, i * sides + k, (i + 1) * sides + k, (i + 1) * sides + j))
    faces.extend([tuple(reversed(range(sides))), tuple((len(path) - 1) * sides + j for j in range(sides))])
    return mesh(name, verts, faces, material, 0, True)


def prism_x(name, profile_yz, x0, x1, material, bevel=.025):
    n = len(profile_yz)
    verts = [(x, y, z) for x in (x0, x1) for y, z in profile_yz]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    return mesh(name, verts, faces, material, bevel)


def roof_sheet(name, top_yz, x0, x1, thickness, material):
    poly = list(top_yz) + [(y, z - thickness) for y, z in reversed(top_yz)]
    return prism_x(name, poly, x0, x1, material, .018)


def round_rect_points(width, height, radius, steps=7):
    result = []
    for cx, cz, start in ((width / 2 - radius, height / 2 - radius, 0),
                           (-width / 2 + radius, height / 2 - radius, 90),
                           (-width / 2 + radius, -height / 2 + radius, 180),
                           (width / 2 - radius, -height / 2 + radius, 270)):
        for j in range(steps + 1):
            a = math.radians(start + j * 90 / steps)
            result.append((cx + radius * math.cos(a), cz + radius * math.sin(a)))
    return result


def frame(name, center, width, height, border, depth, material, radius=.20):
    outer = round_rect_points(width, height, radius)
    inner = round_rect_points(width - 2 * border, height - 2 * border, max(.025, radius - border))
    n = len(outer)
    cx, cy, cz = center
    verts = [(cx + x, cy + dy, cz + z) for dy in (-depth / 2, depth / 2) for arr in (outer, inner) for x, z in arr]
    faces = []
    for j in range(n):
        k = (j + 1) % n
        faces.extend([(j, k, n + k, n + j), (2 * n + j, 3 * n + j, 3 * n + k, 2 * n + k),
                      (j, 2 * n + j, 2 * n + k, k), (n + j, n + k, 3 * n + k, 3 * n + j)])
    return mesh(name, verts, faces, material, .012)


def bolt(name, loc, axis=(0, -1, 0), radius=.035, material='BrushedSteel'):
    return cyl(name, loc, radius, .025, material, axis, .007, 6)


def vent(name, loc, width, height, count=5, facing='front'):
    x, y, z = loc
    if facing == 'front':
        box(name + '.Recess', (x, y, z), (width, .045, height), 'Graphite', .04)
        for i in range(count):
            zz = z - height * .36 + i * height * .72 / (count - 1)
            box(name + '.Louver.%02d' % i, (x, y - .033, zz), (width * .82, .055, height / (count * 2.5)), 'BrushedSteel', .012)
    else:
        box(name + '.Recess', (x, y, z), (.045, width, height), 'Graphite', .04)
        for i in range(count):
            zz = z - height * .36 + i * height * .72 / (count - 1)
            box(name + '.Louver.%02d' % i, (x + .033, y, zz), (.055, width * .82, height / (count * 2.5)), 'BrushedSteel', .012)


def joint(name, point, radius, width):
    x, y, z = point
    cyl(name + '.Core', point, radius, width, 'Graphite', (0, 1, 0), .045)
    for side in (-1, 1):
        cyl(name + '.Bearing.%+d' % side, (x, y + side * width * .44, z), radius * 1.03, .16, 'WarmIvory', (0, 1, 0), .035)
        cyl(name + '.CopperSeal.%+d' % side, (x, y + side * (width * .5 + .065), z), radius * .88, .05, 'CopperOrange', (0, 1, 0), .012)
        cyl(name + '.BlueCap.%+d' % side, (x, y + side * (width * .5 + .102), z), radius * .76, .085, 'SteelBlue', (0, 1, 0), .020)
        cyl(name + '.AxleCover.%+d' % side, (x, y + side * (width * .5 + .149), z), radius * .59, .035, 'Graphite', (0, 1, 0), .010)
        for k in range(4):
            a = math.tau * k / 4 + math.pi / 4
            bolt(name + '.CapBolt.%+d.%d' % (side, k), (x + radius * .49 * math.cos(a), y + side * (width * .5 + .172), z + radius * .49 * math.sin(a)), (0, side, 0), .028)


def articulated_welding_mech():
    box('Chassis.LowerTray', (0, 0, .52), (1.65, 1.44, .48), 'Graphite', .20)
    box('Chassis.RoundedArmor', (0, 0, .77), (1.84, 1.52, .53), 'WarmIvory', .18)
    box('Chassis.TopDeck', (0, 0, 1.01), (1.68, 1.40, .16), 'SteelBlue', .09)
    for i, (x, y) in enumerate(((-1.03, -.88), (1.03, -.88), (-1.03, .88), (1.03, .88))):
        s = 'Stabilizer.%02d' % i
        cyl(s + '.RubberPad', (x, y, .105), .32, .21, 'Rubber', bevel=.055, vertices=32)
        cyl(s + '.MetalFoot', (x, y, .23), .29, .12, 'BrushedSteel', bevel=.035, vertices=32)
        beam(s + '.AngledLeg', (x, y, .32), (x * .74, y * .74, .72), .38, .36, 'SteelBlue', .10)
        cyl(s + '.Pivot', (x * .85, y * .92, .57), .13, .10, 'Graphite', (0, 1, 0), .02)
        bolt(s + '.PivotBolt', (x * .85, y * .92 - .065, .57), radius=.06)
        bolt(s + '.FootAnchor', (x + .14, y, .30), (0, 0, 1), .045)
    cyl('Waist.TurntableBase', (0, 0, 1.12), .66, .19, 'Graphite', bevel=.04)
    cyl('Waist.RotationDrum', (0, 0, 1.27), .63, .19, 'SteelBlue', bevel=.045)
    cyl('Waist.CopperSeal', (0, 0, 1.38), .57, .055, 'CopperOrange', bevel=.012)
    for k in range(8):
        a = k * math.tau / 8
        bolt('Waist.DeckBolt.%02d' % k, (.57 * math.cos(a), .57 * math.sin(a), 1.405), (0, 0, 1), .032)
    p0, p1, p2 = (-.17, 0, 1.63), (-.70, 0, 2.98), (.62, 0, 2.68)
    beam('Arm.Lower.MainHousing', p0, p1, .56, .52, 'WarmIvory', .13)
    beam('Arm.Upper.MainHousing', p1, p2, .49, .48, 'WarmIvory', .12)
    for side in (-1, 1):
        beam('Arm.Lower.BluePanel.%+d' % side, (-.25, side * .278, 1.83), (-.63, side * .278, 2.80), .34, .045, 'SteelBlue', .045)
        beam('Arm.Upper.BluePanel.%+d' % side, (-.47, side * .255, 2.96), (.42, side * .255, 2.76), .29, .04, 'SteelBlue', .04)
    joint('Joint.Shoulder', p0, .39, .62)
    joint('Joint.Elbow', p1, .36, .62)
    joint('Joint.Wrist', p2, .27, .52)
    headp = (1.03, 0, 2.52)
    beam('Head.WristCoupler', p2, headp, .26, .28, 'Graphite', .06)
    box('Head.BlueToolBody', headp, (.50, .46, .45), 'SteelBlue', .11, (0, .30, 0))
    box('Head.ProtectiveShroud', (1.22, -.015, 2.43), (.43, .56, .43), 'Graphite', .12, (0, .30, 0))
    box('Head.CopperTopPlate', (1.20, -.015, 2.635), (.32, .43, .045), 'CopperOrange', .035, (0, .30, 0))
    tube('Head.TorchNeck', [(1.22, 0, 2.33), (1.35, 0, 2.17), (1.42, 0, 1.97)], .061, 'BrushedSteel', samples_per_span=8, sides=16)
    rod('Head.CopperNozzle', (1.40, 0, 2.02), (1.47, 0, 1.83), .083, 'CopperOrange', .018)
    rod('Head.NozzleOpening', (1.468, 0, 1.837), (1.478, 0, 1.808), .052, 'Graphite', .005)
    box('Controller.Body', (-.58, .55, 1.17), (.63, .48, .57), 'SteelBlue', .10)
    box('Controller.Lid', (-.58, .55, 1.47), (.57, .41, .07), 'WarmIvory', .05)
    tube('Controller.CarryHandle', [(-.78, .55, 1.49), (-.75, .55, 1.62), (-.42, .55, 1.62), (-.38, .55, 1.49)], .035, 'Graphite', samples_per_span=6)
    vent('Chassis.FrontVent', (-.48, -.772, .77), .51, .27, 4)
    box('Chassis.ControlPanel', (.35, -.785, .78), (.70, .09, .34), 'BlueEdge', .06)
    box('Chassis.StatusScreen', (.22, -.842, .81), (.26, .022, .17), 'MutedGlazing', .025)
    for i in range(2):
        box('Chassis.PanelKey.%d' % i, (.48 + .10 * i, -.847, .76), (.064, .034, .075), 'WarmIvory', .016)
    box('Chassis.ServiceRear', (0, .776, .73), (.94, .05, .32), 'SteelBlue', .05)
    for x in (-.36, .36):
        bolt('Chassis.ServiceRear.Bolt.' + str(x), (x, .81, .73), (0, 1, 0), .035)
    tube('Cable.BaseToElbow', [(-.55, .61, 1.38), (-1.03, .48, 1.61), (-1.05, .41, 2.22), (-1.09, .38, 2.85), (-.85, .38, 3.36), (-.42, .35, 3.30), (-.18, .29, 3.09)], .064, 'Rubber', 37, 24, 16)
    tube('Cable.ForearmTool', [(-.19, .28, 3.09), (.27, .30, 3.09), (.79, .29, 2.98), (1.07, .26, 2.72)], .054, 'Rubber', 22, 24, 16)
    tube('Cable.WristServiceLoop', [(.47, -.18, 2.42), (.60, -.26, 2.22), (.99, -.25, 2.20), (1.08, -.21, 2.32)], .045, 'Rubber', 16, 20, 12)
    for i, (p, axis) in enumerate((((-1.05, .41, 2.22), (0, 0, 1)), ((-.85, .38, 3.36), (1, 0, .3)), ((.79, .29, 2.98), (1, 0, -.3)))):
        cyl('Cable.CopperClamp.%d' % i, p, .077, .072, 'CopperOrange', axis, .01, 24)
    return {'intent': 'Compact fixed welding robot with a stout three-jointed arm and four stabilizer feet.',
            'nominal_dimensions_m': [3.0, 2.5, 3.5], 'details': ['Four pads', 'Waist swivel', 'Three layered pivots', 'Welding shroud and blunt nozzle', 'Corrugated cable routes', 'Integrated controller']}


def cylindrical_mixer():
    center = Vector((0, .04, 1.92))
    axis = Vector((0, -.95, .312)).normalized()
    rot = axis.to_track_quat('Z', 'Y')
    def dp(x, y, z):
        return center + rot @ Vector((x, y, z))
    profile = [(0, -.78), (.77, -.78), (1.00, -.64), (1.15, -.33), (1.17, .30),
               (1.08, .59), (.83, .89), (.75, .89), (.77, .74), (.96, .48), (1.02, .12), (.96, -.36), (.74, -.61), (0, -.61)]
    lathe('Drum.ThickOpenShell', profile, center, 'WarmIvory', axis, 80,
          ['Graphite', 'BrushedSteel'], {6: 2, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1})
    torus('Drum.FrontLoadingRim', dp(0, 0, .895), .795, .055, 'BrushedSteel', axis)
    lathe('Drum.CopperDriveBand', [(1.171, -.15), (1.191, -.13), (1.191, .13), (1.171, .15), (1.171, -.15)], center, 'CopperOrange', axis, 80)
    torus('Drum.RearDriveFlange', dp(0, 0, -.24), 1.173, .038, 'Graphite', axis)
    for k in range(48):
        a = k * math.tau / 48
        o = box('Drum.DriveTooth.%02d' % k, dp(1.19 * math.cos(a), 1.19 * math.sin(a), -.24), (.07, .075, .095), 'Graphite', .012)
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = rot @ Vector((math.cos(a), math.sin(a), 0)).to_track_quat('Z', 'Y')
    for k in range(3):
        a = k * math.tau / 3
        r = .69
        o = box('Drum.InternalPaddle.%d' % k, dp(r * math.cos(a), r * math.sin(a), -.03), (.09, .27, 1.0), 'BrushedSteel', .027)
        o.rotation_mode = 'QUATERNION'
        from mathutils import Quaternion
        o.rotation_quaternion = rot @ Quaternion((0, 0, 1), a)
    for side in (-1, 1):
        x = side * 1.32
        for j, y in enumerate((-.70, .76)):
            box('Frame.Foot.%+d.%d' % (side, j), (x, y, .12), (.61, .68, .24), 'Rubber', .075)
            box('Frame.AnchorPlate.%+d.%d' % (side, j), (x, y, .285), (.55, .60, .12), 'SteelBlue', .04)
            for dx in (-.17, .17):
                bolt('Frame.AnchorBolt.%+d.%d.%s' % (side, j, dx), (x + dx, y, .362), (0, 0, 1), .045)
        # Cheeks use a broad tapered structural silhouette, mirrored across X.
        profile_yz = [(-.91, .35), (.98, .35), (.40, 1.94), (.25, 2.15), (-.10, 2.21), (-.38, 2.02)]
        prism_x('Frame.SupportCheek.%+d' % side, profile_yz, x - .14, x + .14, 'SteelBlue', .09)
        cyl('Frame.Trunnion.%+d' % side, (x, .10, 1.95), .29, .46, 'BlueEdge', (1, 0, 0), .05)
        cyl('Frame.TrunnionSeal.%+d' % side, (x + side * .27, .10, 1.95), .215, .055, 'CopperOrange', (1, 0, 0), .018)
        cyl('Frame.TrunnionCap.%+d' % side, (x + side * .31, .10, 1.95), .16, .07, 'Graphite', (1, 0, 0), .025)
    for y in (-.58, .70):
        box('Frame.CrossRail.' + str(y), (0, y, .47), (2.50, .19, .22), 'SteelBlue', .045)
    # Empty front discharge trough. Sidewalls are separate editable parts.
    chute_poly = [(-1.80, .69), (-.87, 1.12), (-.83, 1.24), (-1.85, .82)]
    prism_x('Chute.Floor', chute_poly, -.43, .43, 'WarmIvory', .025)
    for side in (-1, 1):
        prism_x('Chute.Sidewall.%+d' % side, [(-1.84, .81), (-.83, 1.23), (-.83, 1.51), (-1.84, 1.04)], side * .43 - .045, side * .43 + .045, 'BrushedSteel', .025)
        cyl('Chute.Hinge.%+d' % side, (side * .48, -.85, 1.17), .10, .09, 'Graphite', (1, 0, 0), .015)
    # Rear-side feed hopper, visibly hollow at its wide mouth.
    fx, fy = -.73, .84
    verts = []
    for z, sx, sy in ((2.38, .23, .24), (3.15, .55, .47), (3.15, .49, .41), (2.44, .18, .19)):
        verts += [(fx - sx, fy - sy, z), (fx + sx, fy - sy, z), (fx + sx, fy + sy, z), (fx - sx, fy + sy, z)]
    faces = []
    for ring in range(3):
        for j in range(4):
            k = (j + 1) % 4
            faces.append((ring * 4 + j, ring * 4 + k, (ring + 1) * 4 + k, (ring + 1) * 4 + j))
    mesh('Feed.HollowFunnel', verts, faces, 'SteelBlue', .025)
    box('Feed.Throat', (fx, fy, 2.37), (.45, .46, .26), 'CopperOrange', .05)
    for j, (a, b) in enumerate((((fx - .55, fy - .47, 3.15), (fx + .55, fy - .47, 3.15)), ((fx + .55, fy - .47, 3.15), (fx + .55, fy + .47, 3.15)), ((fx + .55, fy + .47, 3.15), (fx - .55, fy + .47, 3.15)), ((fx - .55, fy + .47, 3.15), (fx - .55, fy - .47, 3.15)))):
        rod('Feed.TopLip.%d' % j, a, b, .035, 'BrushedSteel')
    box('Drive.MotorBracket', (1.18, .75, 1.08), (.78, .69, .16), 'BlueEdge', .045)
    cyl('Drive.MotorBody', (1.27, .68, 1.46), .29, .80, 'Graphite', (0, 1, 0), .05)
    for j in range(8):
        torus('Drive.CoolingRib.%d' % j, (1.27, .34 + j * .09, 1.46), .29, .018, 'BrushedSteel', (0, 1, 0))
    cyl('Drive.EndCover', (1.27, 1.11, 1.46), .30, .13, 'SteelBlue', (0, 1, 0), .04)
    box('Drive.Gearbox', (1.29, .24, 1.57), (.54, .33, .53), 'CopperOrange', .11)
    tube('Drive.PowerConduit', [(1.32, .92, 1.18), (1.48, .78, .83), (1.44, -.12, .75)], .045, 'Rubber', 18, 15)
    box('Controls.FrontPanel', (1.35, -.56, 1.03), (.43, .14, .53), 'WarmIvory', .06, (math.radians(-10), 0, 0))
    box('Controls.FaceInset', (1.35, -.651, 1.03), (.31, .035, .39), 'Graphite', .035)
    cyl('Controls.StopButton', (1.35, -.687, .95), .083, .055, 'CopperOrange', (0, -1, 0), .015, 32)
    cyl('Controls.ReadyLamp', (1.35, -.680, 1.15), .041, .035, 'PanelGreen', (0, -1, 0), .009, 24)
    return {'intent': 'Stationary materials mixer with a tilted open drum, visible paddles and empty discharge trough.',
            'nominal_dimensions_m': [3.5, 3.1, 3.2], 'details': ['Open thick drum shell', 'Three internal paddles', 'Drive band and teeth', 'Hollow feed funnel', 'Four isolation feet', 'Motor and controls']}


def workshop_window(name, x, y, z, width, height, side=False):
    if not side:
        box(name + '.Recess', (x, y, z), (width, .13, height), 'BlueEdge', .065)
        box(name + '.Glazing', (x, y - .075, z), (width - .17, .025, height - .17), 'MutedGlazing', .035)
        box(name + '.Mullion', (x, y - .10, z), (.055, .055, height - .11), 'WarmIvory', .012)
        box(name + '.Transom', (x, y - .11, z + height * .12), (width - .12, .055, .055), 'WarmIvory', .012)
        box(name + '.Sill', (x, y - .075, z - height / 2 - .03), (width + .15, .25, .10), 'Concrete', .035)
    else:
        box(name + '.Recess', (x, y, z), (.13, width, height), 'BlueEdge', .065)
        box(name + '.Glazing', (x + .075, y, z), (.025, width - .17, height - .17), 'MutedGlazing', .035)
        box(name + '.Mullion', (x + .10, y, z), (.055, .055, height - .11), 'WarmIvory', .012)
        box(name + '.Transom', (x + .11, y, z + height * .12), (.055, width - .12, .055), 'WarmIvory', .012)
        box(name + '.Sill', (x + .075, y, z - height / 2 - .03), (.25, width + .15, .10), 'Concrete', .035)


def rounded_foundry_workshop():
    # The foundation belongs to the building; the studio ground is separate.
    box('Foundation.Main', (0, 0, .13), (7.00, 5.34, .26), 'Concrete', .13)
    box('Foundation.Office', (-2.22, -2.85, .13), (2.33, 2.12, .26), 'Concrete', .11)
    box('Workshop.InteriorFloor', (0, 0, .28), (6.52, 4.86, .10), 'Masonry', .025)
    box('Wall.Left', (-3.13, 0, 1.90), (.30, 4.90, 3.24), 'Masonry', .085)
    box('Wall.Right', (3.13, 0, 1.90), (.30, 4.90, 3.24), 'Masonry', .085)
    box('Wall.Rear', (0, 2.30, 1.90), (6.16, .30, 3.24), 'Masonry', .085)
    box('Wall.FrontLeft', (-2.01, -2.30, 1.90), (2.52, .30, 3.24), 'Masonry', .07)
    box('Wall.FrontRightPier', (2.99, -2.30, 1.90), (.56, .30, 3.24), 'Masonry', .075)
    box('Wall.BayLintel', (.98, -2.30, 3.31), (3.49, .30, .42), 'Masonry', .055)
    frame('Bay.SoftSteelSurround', (.98, -2.50, 1.84), 3.78, 3.25, .15, .20, 'SteelBlue', .32)
    box('Bay.RollerCase', (.98, -2.56, 3.21), (3.27, .28, .23), 'Graphite', .065)
    box('Bay.RaisedDoorBottom', (.98, -2.71, 3.13), (3.21, .085, .12), 'CopperOrange', .035)
    for j in range(4):
        box('Bay.RolledDoorSlat.%d' % j, (.98, -2.724, 3.19 + j * .035), (3.15, .020, .012), 'BrushedSteel', .004)
    for x in (-.91, 2.86):
        box('Bay.GuardPost.' + str(x), (x, -2.62, .80), (.18, .21, 1.08), 'CopperOrange', .07)
        box('Bay.GuardBoot.' + str(x), (x, -2.62, .33), (.23, .26, .17), 'Graphite', .035)
    # Soft roof surfaces sweep across the full building width.
    front = [(-2.65, 3.54), (-2.40, 3.61), (-1.95, 3.76), (-1.44, 3.92), (-.88, 4.04), (-.28, 4.10), (.10, 4.11)]
    rear = [(.04, 4.70), (.30, 4.74), (.56, 4.68), (.82, 4.52), (1.16, 4.24), (1.65, 3.92), (2.10, 3.71), (2.62, 3.55)]
    roof_sheet('Roof.FrontCurvedSheet', front, -3.47, 3.47, .14, 'SteelBlue')
    roof_sheet('Roof.RearCurvedSheet', rear, -3.47, 3.47, .14, 'SteelBlue')
    box('Roof.ClerestoryBack', (0, .45, 4.29), (6.70, .15, .77), 'BlueEdge', .04)
    box('Roof.ClerestoryLowerRail', (0, -.02, 4.14), (6.73, .18, .15), 'Graphite', .04)
    box('Roof.ClerestoryTopRail', (0, .025, 4.63), (6.78, .20, .15), 'BlueEdge', .05)
    for i in range(5):
        x = -2.65 + i * 1.325
        box('Roof.VentWindowFrame.%d' % i, (x, -.025, 4.39), (1.20, .13, .42), 'WarmIvory', .04)
        box('Roof.VentGlazing.%d' % i, (x, -.101, 4.39), (1.04, .025, .28), 'AmberGlass', .025)
        box('Roof.VentMullion.%d' % i, (x, -.121, 4.39), (.035, .025, .29), 'BlueEdge', .007)
    for i in range(8):
        x = -3.34 + i * .955
        roof_sheet('Roof.FrontStandingSeam.%d' % i, [(y, z + .025) for y, z in front], x - .025, x + .025, .055, 'BlueEdge')
        roof_sheet('Roof.RearStandingSeam.%d' % i, [(y, z + .025) for y, z in rear], x - .025, x + .025, .055, 'BlueEdge')
    sideprofile = [(-2.45, 3.48), (-2.35, 3.58), (-1.95, 3.71), (-1.44, 3.87), (-.88, 3.99), (-.05, 4.05), (-.05, 4.60), (.32, 4.62), (.75, 4.42), (1.20, 4.12), (1.75, 3.84), (2.43, 3.55), (2.43, 3.48)]
    for side in (-1, 1):
        prism_x('Roof.SideGable.%+d' % side, sideprofile, side * 3.18 - .08, side * 3.18 + .08, 'BlueEdge', .035)
        roof_sheet('Roof.FrontFascia.%+d' % side, [(y, z + .03) for y, z in front], side * 3.48 - .065, side * 3.48 + .065, .21, 'SteelBlue')
        roof_sheet('Roof.RearFascia.%+d' % side, [(y, z + .03) for y, z in rear], side * 3.48 - .065, side * 3.48 + .065, .21, 'SteelBlue')
    # Broad courses on the exposed side and rear; no surface texture dependency.
    for j in range(1, 8):
        z = .39 + j * .40
        box('Masonry.RightCourse.%d' % j, (3.285, 0, z), (.012, 4.72, .014), 'Concrete', .004)
        box('Masonry.RearCourse.%d' % j, (0, 2.457, z), (6.15, .012, .014), 'Concrete', .004)
        for k in range(5):
            y = -1.95 + k * .92 + (j % 2) * .35
            box('Masonry.RightJoint.%d.%d' % (j, k), (3.286, y, z - .20), (.012, .015, .38), 'Concrete', .004)
    for x in (-3.0, -.93, 2.90):
        box('Facade.SteelUpright.' + str(x), (x, -2.493, 1.91), (.115, .12, 3.13), 'BlueEdge', .035)
    for y in (-2.20, 2.20):
        box('Wall.RightPlinth.' + str(y), (3.19, y, .67), (.46, .48, .77), 'Concrete', .075)
    # Office annex and its softly capped roof.
    box('Office.Walls', (-2.22, -2.82, 1.30), (2.12, 1.89, 2.05), 'Masonry', .11)
    box('Office.RoundedRoof', (-2.22, -2.82, 2.40), (2.38, 2.12, .30), 'SteelBlue', .14)
    box('Office.RoofLowerTrim', (-2.22, -2.82, 2.245), (2.31, 2.05, .10), 'BlueEdge', .045)
    box('Office.DoorRecess', (-2.71, -3.79, 1.15), (.78, .06, 1.77), 'BlueEdge', .105)
    box('Office.DoorLeaf', (-2.71, -3.84, 1.15), (.65, .06, 1.62), 'SteelBlue', .06)
    frame('Office.DoorWindowFrame', (-2.71, -3.886, 1.43), .34, .60, .055, .04, 'WarmIvory', .075)
    box('Office.DoorWindow', (-2.71, -3.908, 1.43), (.23, .018, .48), 'AmberGlass', .02)
    rod('Office.DoorHandle', (-2.49, -3.944, .90), (-2.49, -3.944, 1.10), .021, 'BrushedSteel')
    workshop_window('Office.FrontWindow', -1.78, -3.79, 1.40, .76, 1.19)
    workshop_window('Office.SideWindow', -1.14, -2.80, 1.39, .91, 1.19, side=True)
    box('Office.EntryStepLower', (-2.72, -3.99, .095), (1.05, .59, .19), 'Concrete', .07)
    box('Office.EntryStepUpper', (-2.72, -3.86, .23), (.95, .38, .16), 'Masonry', .045)
    tube('Office.EntryLamp.Neck', [(-2.71, -3.80, 2.10), (-2.71, -3.97, 2.15), (-2.71, -4.02, 2.00)], .027, 'Graphite', samples_per_span=8)
    lathe('Office.EntryLamp.Shade', [(0, -.04), (.14, -.04), (.16, .0), (.10, .11), (.045, .14), (0, .14)], (-2.71, -4.02, 1.99), 'BlueEdge', segments=32)
    cyl('Office.EntryLamp.Lens', (-2.71, -4.02, 1.96), .115, .018, 'AmberGlass', bevel=.008)
    vent('Wall.FrontHighVent', (-2.18, -2.478, 3.03), .57, .32, 4)
    # Protected furnace occupies the bay, with a deliberately solid enclosure.
    f = (.94, .40, .33)
    lathe('Furnace.MainHousing', [(0, 0), (.92, 0), (.98, .12), (.98, 1.65), (.93, 1.88), (.80, 2.10), (.56, 2.30), (.27, 2.37), (0, 2.37)], f, 'Graphite', segments=64)
    for z in (.53, 1.93):
        cyl('Furnace.Band.' + str(z), (.94, .40, z), 1.015, .12, 'BrushedSteel', bevel=.025)
    cyl('Furnace.TopVent', (.94, .40, 2.84), .24, .30, 'Graphite', bevel=.04)
    box('Furnace.HatchSurround', (.94, -.585, 1.29), (.85, .16, 1.10), 'BrushedSteel', .11)
    box('Furnace.ClosedHatch', (.94, -.690, 1.29), (.67, .09, .90), 'CopperOrange', .085)
    for z in (1.02, 1.56):
        box('Furnace.HatchHinge.' + str(z), (.56, -.738, z), (.12, .13, .19), 'Graphite', .03)
    rod('Furnace.HatchHandle', (1.14, -.79, 1.16), (1.14, -.79, 1.42), .035, 'Graphite')
    box('Furnace.RaisedPad', (.94, .35, .40), (2.30, 2.20, .17), 'Concrete', .055)
    for x in (-.27, .40, 1.07, 1.74, 2.18):
        rod('Furnace.FrontGuardPost.' + str(x), (x, -1.03, .48), (x, -1.03, 1.23), .034, 'CopperOrange')
    for z in (.77, 1.23):
        rod('Furnace.FrontGuardRail.' + str(z), (-.27, -1.03, z), (2.18, -1.03, z), .033, 'CopperOrange')
    for side in (-1, 1):
        x = .95 + side * 1.22
        tube('Furnace.SideGuard.%+d' % side, [(x, -1.02, .49), (x, -1.02, 1.23), (x, .90, 1.23), (x, .90, .49)], .032, 'CopperOrange', samples_per_span=4)
    # Exterior exhaust: furnace-side blower housing, broad bend and short stack.
    box('Exhaust.Foundation', (3.78, 1.22, .20), (1.36, 1.62, .40), 'Concrete', .10)
    cyl('Exhaust.BlowerHousing', (3.65, 1.20, 1.03), .66, .91, 'SteelBlue', (1, 0, 0), .11)
    cyl('Exhaust.BlowerFlange', (3.24, 1.20, 1.03), .71, .11, 'Graphite', (1, 0, 0), .035)
    box('Exhaust.ServiceCabinet', (4.10, .91, .94), (.35, .73, .83), 'BlueEdge', .08)
    vent('Exhaust.ServiceVent', (4.29, .90, .94), .43, .43, 5, facing='side')
    cyl('Exhaust.StackLower', (3.94, 1.27, 2.14), .27, 1.36, 'BrushedSteel', bevel=.035)
    tube('Exhaust.RoofConnector', [(3.18, 1.27, 3.28), (3.56, 1.27, 3.28), (3.90, 1.27, 3.02), (3.94, 1.27, 2.78)], .27, 'BrushedSteel', samples_per_span=10, sides=32)
    cyl('Exhaust.UpperStack', (3.94, 1.27, 3.82), .27, 2.05, 'BrushedSteel', bevel=.035)
    for i, z in enumerate((1.53, 2.80, 3.46, 4.52)):
        cyl('Exhaust.StackCollar.%d' % i, (3.94, 1.27, z), .31, .10, 'CopperOrange' if i in (0, 2) else 'Graphite', bevel=.025)
    cyl('Exhaust.StackDarkMouth', (3.94, 1.27, 4.87), .235, .028, 'Graphite', bevel=.008)
    for a in (0, math.pi):
        rod('Exhaust.CapSupport.' + str(a), (3.94 + .20 * math.cos(a), 1.27 + .20 * math.sin(a), 4.81), (3.94 + .20 * math.cos(a), 1.27 + .20 * math.sin(a), 5.02), .025, 'Graphite')
    cyl('Exhaust.RainCap', (3.94, 1.27, 5.04), .36, .10, 'BlueEdge', bevel=.045)
    box('Rear.ServiceDoor', (-1.85, 2.485, 1.21), (.96, .11, 1.82), 'SteelBlue', .075)
    box('Rear.ServiceDoorInset', (-1.85, 2.554, 1.42), (.66, .025, .95), 'BlueEdge', .045)
    rod('Rear.ServiceDoorHandle', (-1.53, 2.60, 1.04), (-1.53, 2.60, 1.23), .022, 'BrushedSteel')
    for x in (.30, 1.60):
        box('Rear.HighWindowFrame.' + str(x), (x, 2.48, 2.64), (1.05, .10, .66), 'BlueEdge', .06)
        box('Rear.HighWindowGlass.' + str(x), (x, 2.54, 2.64), (.87, .025, .49), 'MutedGlazing', .025)
    return {'intent': 'Small foundry building with an open service bay, protected furnace, raised roof vent and office annex.',
            'nominal_dimensions_m': [8.0, 6.6, 5.1], 'details': ['Curved split roof', 'Five clerestory panels', 'Open service bay', 'Enclosed furnace', 'Office annex', 'External blower and rain-capped stack', 'Shallow building foundation']}


def vertical_material_tower():
    # Four principal columns leave the space below the hopper outlets open.
    for i, (x, y) in enumerate(((-2.40, -.99), (2.40, -.99), (-2.40, .99), (2.40, .99))):
        box('Frame.Footing.%d' % i, (x, y, .18), (.72, .70, .36), 'Concrete', .08)
        box('Frame.AnchorPlate.%d' % i, (x, y, .405), (.57, .55, .11), 'Graphite', .035)
        box('Frame.PrimaryColumn.%d' % i, (x, y, 1.90), (.33, .34, 3.00), 'BlueEdge', .045)
        box('Frame.ColumnBoot.%d' % i, (x, y, .67), (.42, .43, .48), 'Graphite', .045)
        box('Frame.BootCopperStrip.%d' % i, (x, y - .225, .67), (.10, .045, .43), 'CopperOrange', .018)
        for dx in (-.18, .18):
            bolt('Frame.FootBolt.%d.%s' % (i, dx), (x + dx, y, .478), (0, 0, 1), .045)
    for y in (-1.0, 1.0):
        box('Frame.LongHeader.' + str(y), (0, y, 3.38), (5.17, .29, .36), 'BlueEdge', .05)
        for x in (-2.40, 2.40):
            box('Frame.HeaderConnection.%s.%s' % (x, y), (x, y - .165, 3.38), (.38, .055, .37), 'CopperOrange', .035)
            for dx in (-.11, .11):
                bolt('Frame.ConnectionBolt.%s.%s.%s' % (x, y, dx), (x + dx, y - .21, 3.38), radius=.035)
    for x in (-2.40, 0, 2.40):
        box('Frame.CrossHeader.' + str(x), (x, 0, 3.38), (.24, 2.17, .30), 'BlueEdge', .035)
    for i, (a, b) in enumerate((((-2.4, 1, .62), (0, 1, 3.20)), ((2.4, 1, .62), (0, 1, 3.20)), ((-2.4, -.98, .72), (-2.4, .98, 3.20)), ((2.4, -.98, .72), (2.4, .98, 3.20)))):
        beam('Frame.RearSideBrace.%d' % i, a, b, .13, .12, 'Graphite', .025)
    for i, x in enumerate((-1.20, 1.20)):
        prefix = 'Bin.%d' % i
        # Closed, rounded storage body with a conical lower hopper.
        lathe(prefix + '.Hopper', [(0, 2.14), (.22, 2.14), (.27, 2.27), (.55, 2.62), (1.04, 3.29), (1.06, 3.44), (0, 3.44)], (x, 0, 0), 'WarmIvory', segments=72)
        lathe(prefix + '.MainShell', [(0, 3.38), (1.02, 3.38), (1.065, 3.48), (1.065, 6.46), (1.04, 6.57), (.97, 6.74), (.78, 6.93), (.52, 7.08), (.20, 7.16), (0, 7.18)], (x, 0, 0), 'SteelBlue', segments=80,
              extra_materials=['WarmIvory'], segment_materials={4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1})
        lathe(prefix + '.LowerPaleBand', [(1.067, 3.48), (1.078, 3.48), (1.078, 4.20), (1.067, 4.20), (1.067, 3.48)], (x, 0, 0), 'WarmIvory', segments=80)
        for j, z in enumerate((3.48, 4.20, 5.30, 6.47)):
            torus(prefix + '.ShellSeam.%d' % j, (x, 0, z), 1.071, .018, 'BrushedSteel')
        cyl(prefix + '.OutletFlange', (x, 0, 2.22), .32, .10, 'CopperOrange', bevel=.02)
        cyl(prefix + '.OutletValveBody', (x, 0, 2.03), .235, .30, 'Graphite', bevel=.04)
        cyl(prefix + '.OutletLip', (x, 0, 1.86), .27, .07, 'BrushedSteel', bevel=.02)
        cyl(prefix + '.OutletDarkRecess', (x, 0, 1.822), .19, .012, 'Graphite', bevel=.004)
        box(prefix + '.SlideGateHousing', (x, -.28, 2.16), (.53, .39, .12), 'BlueEdge', .04)
        rod(prefix + '.ValveSpindle', (x, -.30, 2.13), (x, -.56, 2.13), .035, 'BrushedSteel')
        torus(prefix + '.ValveHandwheel', (x, -.59, 2.13), .115, .023, 'CopperOrange', (0, 1, 0))
        for k in range(3):
            a = math.tau * k / 3
            rod(prefix + '.HandwheelSpoke.%d' % k, (x, -.59, 2.13), (x + .10 * math.cos(a), -.59, 2.13 + .10 * math.sin(a)), .011, 'CopperOrange', .003, 12)
        # Broad retaining straps and their sparse functional clamps.
        for k, a in enumerate((-.72, math.pi - .72, math.pi / 2)):
            xx, yy = x + 1.09 * math.cos(a), 1.09 * math.sin(a)
            beam(prefix + '.VerticalStrap.%d' % k, (xx, yy, 3.51), (xx, yy, 6.52), .070, .045, 'Graphite', .018)
            for j, z in enumerate((3.63, 5.28, 6.36)):
                box(prefix + '.StrapClamp.%d.%d' % (k, j), (xx, yy, z), (.14, .11, .12), 'BrushedSteel', .025)
        cyl(prefix + '.TopAccessHatch', (x, -.35, 7.04), .24, .10, 'BrushedSteel', bevel=.025)
        cyl(prefix + '.TopHatchInset', (x, -.35, 7.10), .19, .04, 'Graphite', bevel=.012)
        tube(prefix + '.HatchHandle', [(x - .09, -.35, 7.13), (x - .08, -.35, 7.22), (x + .08, -.35, 7.22), (x + .09, -.35, 7.13)], .018, 'BrushedSteel', samples_per_span=4)
        for k in range(4):
            a = k * math.tau / 4
            bolt(prefix + '.HatchBolt.%d' % k, (x + .205 * math.cos(a), -.35 + .205 * math.sin(a), 7.11), (0, 0, 1), .025)
    # Top service deck is a functional part of the tower, not a ground slab.
    box('Walkway.MainDeck', (0, -.53, 7.36), (5.18, 1.13, .14), 'Graphite', .035)
    for y in (-1.05, -.02):
        box('Walkway.EdgeBeam.' + str(y), (0, y, 7.27), (5.30, .13, .18), 'BlueEdge', .025)
    for i in range(18):
        x = -2.45 + i * .288
        box('Walkway.Tread.%02d' % i, (x, -.53, 7.445), (.055, 1.01, .027), 'BrushedSteel', .008)
    for side in (-1, 1):
        y = -.53 + side * .54
        for i, x in enumerate((-2.52, -1.26, 0, 1.26, 2.52)):
            rod('Walkway.Post.%+d.%d' % (side, i), (x, y, 7.40), (x, y, 8.20), .030, 'CopperOrange')
        for z in (7.80, 8.20):
            rod('Walkway.Rail.%+d.%s' % (side, z), (-2.52, y, z), (2.52, y, z), .029, 'CopperOrange')
        box('Walkway.ToeBoard.%+d' % side, (0, y, 7.51), (5.08, .055, .15), 'BlueEdge', .015)
    for z in (7.80, 8.20):
        rod('Walkway.LeftEndRail.' + str(z), (-2.52, -1.07, z), (-2.52, .01, z), .029, 'CopperOrange')
    for x in (-2.05, 0, 2.05):
        beam('Walkway.UnderBracket.' + str(x), (x, -.95, 6.73), (x, -.95, 7.28), .11, .11, 'BlueEdge', .025)
    # Elevator duct and its softly rounded head sit beside the bins.
    ex, ey = 3.20, .30
    box('Elevator.Footing', (ex, ey, .18), (1.25, 1.40, .36), 'Concrete', .09)
    box('Elevator.MainDuct', (ex, ey, 4.13), (.74, .85, 7.56), 'SteelBlue', .09)
    for z in (.62, 2.02, 3.45, 4.88, 6.29, 7.72):
        box('Elevator.SectionCollar.' + str(z), (ex, ey, z), (.83, .94, .11), 'BlueEdge', .035)
        for x in (ex - .30, ex + .30):
            bolt('Elevator.CollarBolt.%s.%s' % (x, z), (x, ey - .49, z), radius=.027)
    # Explicit arched head profile keeps the distinctive belt housing editable.
    profile = [(-.35, 7.80), (-.35, 8.36)]
    for i in range(17):
        a = math.pi - i * math.pi / 16
        profile.append((.28 + .63 * math.cos(a), 8.36 + .63 * math.sin(a)))
    profile += [(.91, 7.80)]
    # The profile is x/z; rotate a YZ prism so the arched silhouette faces front.
    verts = [(ex + x, ey + y, z) for y in (-.49, .49) for x, z in profile]
    n = len(profile)
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    mesh('Elevator.ArchedHead', verts, faces, 'SteelBlue', .06)
    box('Elevator.HeadServicePlate', (3.62, -.216, 8.25), (.36, .05, .40), 'CopperOrange', .04)
    for x in (3.49, 3.75):
        for z in (8.11, 8.39):
            bolt('Elevator.HeadPlateBolt.%s.%s' % (x, z), (x, -.254, z), radius=.026)
    cyl('Elevator.HeadAxleCap', (3.47, -.23, 8.55), .145, .07, 'Graphite', (0, -1, 0), .02)
    box('Elevator.BaseGearbox', (3.22, -.26, .79), (.86, .62, .76), 'BlueEdge', .12)
    cyl('Elevator.BaseMotor', (3.70, -.24, .73), .27, .58, 'Graphite', (1, 0, 0), .04)
    for i in range(5):
        torus('Elevator.MotorFin.%d' % i, (3.49 + i * .09, -.24, .73), .275, .014, 'BrushedSteel', (1, 0, 0))
    cyl('Elevator.MotorCap', (4.01, -.24, .73), .28, .10, 'CopperOrange', (1, 0, 0), .035)
    vent('Elevator.BaseVent', (3.20, -.588, .81), .45, .35, 4)
    # Split feed pipe leads from the elevator to each bin crown.
    tube('Feed.HeaderDuct', [(3.13, .30, 8.15), (2.58, .30, 8.15), (2.31, .30, 7.76), (1.20, .30, 7.76), (-1.20, .30, 7.76)], .105, 'BrushedSteel', samples_per_span=8, sides=24)
    for i, x in enumerate((-1.20, 1.20)):
        tube('Feed.BinBranch.%d' % i, [(x, .30, 7.76), (x, .30, 7.45), (x, .21, 7.19)], .105, 'BrushedSteel', samples_per_span=8, sides=24)
        cyl('Feed.RoofFlange.%d' % i, (x, .21, 7.18), .18, .08, 'CopperOrange', bevel=.02)
    # Ladder is on the outer face; side arcs form the safety cage.
    lx = 3.81
    for y in (-.18, .46):
        rod('Ladder.Stringer.' + str(y), (lx, y, .49), (lx, y, 8.36), .035, 'Graphite')
    for i in range(27):
        z = .58 + i * .29
        rod('Ladder.Rung.%02d' % i, (lx, -.18, z), (lx, .46, z), .024, 'BrushedSteel', .006, 16)
    for i, z in enumerate((2.05, 3.30, 4.55, 5.80, 7.05, 8.30)):
        points = [(lx + .52 * math.cos(-math.pi / 2 + j * math.pi / 12), .14 + .42 * math.sin(-math.pi / 2 + j * math.pi / 12), z) for j in range(13)]
        tube('Ladder.CageHoop.%d' % i, points, .026, 'CopperOrange', samples_per_span=2)
    for i, a in enumerate((-math.pi / 4, 0, math.pi / 4)):
        x, y = lx + .52 * math.cos(a), .14 + .42 * math.sin(a)
        rod('Ladder.CageSpine.%d' % i, (x, y, 2.05), (x, y, 8.30), .024, 'CopperOrange')
    box('Walkway.ElevatorLanding', (2.94, -.53, 7.36), (.78, 1.13, .14), 'Graphite', .035)
    for y in (-1.07, .01):
        rod('Walkway.LandingRail.' + str(y), (2.52, y, 8.20), (3.35, y, 8.20), .029, 'CopperOrange')
    return {'intent': 'Twin-bin bulk storage tower on four principal columns with clear loading space and a side elevator.',
            'nominal_dimensions_m': [7.1, 2.8, 9.0], 'details': ['Two rounded bins', 'Conical hoppers and blunt outlets', 'Four-column frame', 'Arched elevator head', 'Safety-cage service ladder', 'Top service deck', 'Feed header branches']}


BUILDERS = {
    'articulated_welding_mech': articulated_welding_mech,
    'cylindrical_mixer': cylindrical_mixer,
    'rounded_foundry_workshop': rounded_foundry_workshop,
    'vertical_material_tower': vertical_material_tower,
}


def author_uvs(objects):
    """Author a separate packed UV layout on every editable component."""
    bpy.ops.object.select_all(action='DESELECT')
    for i, obj in enumerate(objects):
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.025,
                                 area_weight=.25, correct_aspect=True, scale_to_bounds=True)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.data.uv_layers.active.name = 'UVMap'
        obj['uv_authoring'] = 'Per-component angle-based projection with packed 2.5% island margin; no validation run.'
        obj.select_set(False)
        if i % 50 == 0:
            print('UV authoring component %d/%d' % (i + 1, len(objects)), flush=True)


def studio_setup(bounds):
    low, high = bounds
    size = high - low
    center = (low + high) * .5
    span = max(size)
    # Neutral floor, deliberately isolated from ASSET and all selected exports.
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, low.z - .015))
    ground = bpy.context.object
    ground.name = 'STUDIO.NeutralGround'
    move_collection(ground, studio)
    mat = bpy.data.materials.new('STUDIO.NeutralMatte')
    mat.use_nodes = True
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.43, .46, .48, 1)
    mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .84
    ground.data.materials.append(mat)
    for name, vec, energy, radius in (
        ('Key', (-.9, -1.3, 1.8), 170, .85),
        ('Fill', (1.3, -.3, .9), 110, 1.0),
        ('Rim', (.3, 1.2, 1.6), 190, .75),
    ):
        data = bpy.data.lights.new('STUDIO.' + name, 'AREA')
        data.energy = energy * span * span
        data.shape = 'DISK'
        data.size = radius * span
        ob = bpy.data.objects.new('STUDIO.' + name, data)
        studio.objects.link(ob)
        ob.location = center + Vector(vec) * span
        ob.rotation_euler = (center - ob.location).to_track_quat('-Z', 'Y').to_euler()
    if SLUG == 'rounded_foundry_workshop':
        data = bpy.data.lights.new('STUDIO.BayFill', 'AREA')
        data.energy = 100
        data.shape = 'DISK'
        data.size = 2.0
        ob = bpy.data.objects.new('STUDIO.BayFill', data)
        studio.objects.link(ob)
        ob.location = (1, -1, 2.80)
        ob.rotation_euler = (Vector((1, .8, 1.2)) - ob.location).to_track_quat('-Z', 'Y').to_euler()
    cameras = {}
    for view, direction in (('hero', (1.25, -1.7, 1.05)), ('rear', (-1.25, 1.7, 1.05))):
        direction = Vector(direction).normalized()
        data = bpy.data.cameras.new('STUDIO.' + view)
        data.type = 'ORTHO'
        data.lens = 50
        ob = bpy.data.objects.new('STUDIO.' + view, data)
        studio.objects.link(ob)
        ob.location = center + direction * span * 3.6
        ob.rotation_euler = (center - ob.location).to_track_quat('-Z', 'Y').to_euler()
        quat = ob.rotation_euler.to_quaternion()
        right, up = quat @ Vector((1, 0, 0)), quat @ Vector((0, 1, 0))
        corners = [Vector((x, y, z)) - center for x in (low.x, high.x) for y in (low.y, high.y) for z in (low.z, high.z)]
        w = max(p.dot(right) for p in corners) - min(p.dot(right) for p in corners)
        h = max(p.dot(up) for p in corners) - min(p.dot(up) for p in corners)
        data.ortho_scale = max(w, h) * 1.16
        data.clip_start = .01
        data.clip_end = span * 50
        cameras[view] = ob
    return cameras


def main():
    print('BEGIN AUTHORING ' + SLUG, flush=True)
    design = BUILDERS[SLUG]()
    objects = [o for o in asset.objects if o.type == 'MESH']
    author_uvs(objects)
    bpy.context.view_layer.update()
    # Production dimensions for framing and metadata, not an independent check.
    corners = [o.matrix_world @ Vector(corner) for o in objects for corner in o.bound_box]
    low = Vector(tuple(min(v[i] for v in corners) for i in range(3)))
    high = Vector(tuple(max(v[i] for v in corners) for i in range(3)))
    dimensions = high - low
    cameras = studio_setup((low, high))
    scene.camera = cameras['hero']
    # Save native construction modifiers and named mesh components.
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    scene['asset_slug'] = SLUG
    scene['review_status'] = 'deferred_by_user'
    scene['front_axis'] = '-Y'
    scene['asset_units'] = 'meters'
    scene['studio_note'] = 'STUDIO is render-only. GLB/FBX export selected ASSET meshes.'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (SLUG + '.blend')))
    print('EXPORT GLB ' + SLUG, flush=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / (SLUG + '.glb')), export_format='GLB',
                              use_selection=True, export_apply=True, export_texcoords=True,
                              export_normals=True, export_materials='EXPORT',
                              export_cameras=False, export_lights=False, export_yup=True)
    print('EXPORT FBX ' + SLUG, flush=True)
    bpy.ops.export_scene.fbx(filepath=str(OUT / (SLUG + '.fbx')), use_selection=True,
                             object_types={'MESH'}, use_mesh_modifiers=True, mesh_smooth_type='FACE',
                             add_leaf_bones=False, bake_anim=False, apply_unit_scale=True,
                             global_scale=1.0, axis_forward='-Z', axis_up='Y', path_mode='AUTO')
    render_records = []
    for view, camera in cameras.items():
        scene.camera = camera
        scene.render.filepath = str(OUT / 'renders' / (view + '.png'))
        started = datetime.now(timezone.utc)
        t = time.perf_counter()
        print('RENDER ' + view + ' ' + SLUG, flush=True)
        bpy.ops.render.render(write_still=True)
        render_records.append({
            'view': view, 'path': (OUT / 'renders' / (view + '.png')).relative_to(ROOT).as_posix(),
            'started_at_utc': started.isoformat(), 'finished_at_utc': datetime.now(timezone.utc).isoformat(),
            'elapsed_seconds': round(time.perf_counter() - t, 3),
            'camera_location_m': list(camera.location), 'camera_rotation_radians': list(camera.rotation_euler),
            'projection': 'orthographic', 'orthographic_scale_m': camera.data.ortho_scale,
            'resolution': [960, 960], 'engine': 'Cycles CPU', 'samples': 40, 'denoising': True,
            'color_management': 'AgX / Medium High Contrast', 'preview_inspected': False,
        })
    end = datetime.now(timezone.utc)
    data = {
        'set': 'Set08', 'slug': SLUG, 'theme': 'Materials processing',
        'status': 'produced_unreviewed', 'review_status': 'deferred_by_user',
        'blender_version': bpy.app.version_string, 'source': '../build.py',
        'reference_image': '../REF/' + SLUG + '.png', 'reference_prompt': '../REF/' + SLUG + '.prompt.txt',
        'authoring': 'Original ordinary rounded mesh components; solid named PBR palette; no voxel source or generated surface textures.',
        'design': design, 'units': 'meters', 'front_axis': '-Y', 'up_axis': 'Z',
        'authored_bounds_m': {'minimum': list(low), 'maximum': list(high), 'dimensions': list(dimensions)},
        'dimension_note': 'Measured from authored base-mesh bounding boxes for production framing. Not independent geometry validation.',
        'uv_authoring': {'method': 'Angle-based per-component smart projection', 'angle_degrees': 66,
                         'island_margin': .025, 'map': 'UVMap', 'coverage_or_overlap_validation': 'deferred_by_user'},
        'editable_components': [{'name': o.name, 'material': o['surface_palette'], 'uv_method': o['uv_authoring']} for o in objects],
        'palette': {key: {'srgb_hex': value[0], 'metallic': value[1], 'roughness': value[2]} for key, value in PALETTE.items()},
        'collections': {'ASSET': 'Editable named model meshes', 'STUDIO': 'Ground, area lights and cameras; excluded from exports'},
        'exports': {'blend': SLUG + '.blend', 'glb': SLUG + '.glb', 'fbx': SLUG + '.fbx',
                    'geometry_only': 'Only selected asset meshes and their solid materials; no studio, cameras or lights.'},
        'render_records': render_records,
        'started_at_utc': START.isoformat(), 'finished_at_utc': end.isoformat(),
        'started_at_kst': START.astimezone(timezone(timedelta(hours=9))).isoformat(),
        'finished_at_kst': end.astimezone(timezone(timedelta(hours=9))).isoformat(),
        'blender_script_seconds': round(time.perf_counter() - T0, 3),
        'not_performed': ['generated preview inspection', 'fresh BLEND reopen', 'GLB/FBX reimport', 'geometry validator', 'UV validator', 'reviewer pass'],
        'limitations': ['Static asset; no rig, animation, collision or LOD authored.', 'Solid palette surfaces only.', 'Visual quality and export roundtrips remain unreviewed by user request.'],
    }
    (OUT / 'metadata.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
    print('PRODUCTION COMPLETE ' + SLUG, flush=True)


if __name__ == '__main__':
    main()
