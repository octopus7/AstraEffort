"""Original Set06 mesh authoring. Run one asset per clean Blender process.

No generated render is inspected and no output is reopened by this script.
UV creation and measurements happen during production, not independent review.
"""
import bpy
import json
import math
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
TAU = math.tau
ASSET = None
M = {}


def now():
    return datetime.now(timezone.utc).isoformat()


def material(name, color, metallic=0.0, roughness=0.5, transmission=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Transmission Weight'].default_value = transmission
    bsdf.inputs['IOR'].default_value = 1.42
    return mat


def setup():
    global ASSET, M
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)
    ASSET = bpy.data.collections.new('ASSET')
    bpy.context.scene.collection.children.link(ASSET)
    M = {
        'pine': material('S06_Pine_Painted_Metal', (0.155, 0.255, 0.19), .22, .42),
        'sage': material('S06_Sage_Painted_Metal', (.29, .40, .29), .12, .48),
        'cream': material('S06_Warm_Cream_Enamel', (.79, .74, .58), .13, .39),
        'terra': material('S06_Terracotta_Enamel', (.56, .235, .115), .16, .43),
        'rubber': material('S06_Charcoal_Rubber', (.038, .047, .043), 0, .72),
        'iron': material('S06_Dark_Steel', (.095, .12, .105), .62, .39),
        'steel': material('S06_Brushed_Hydraulic_Steel', (.43, .49, .46), .8, .27),
        'glass': material('S06_Muted_Blue_Glazing', (.22, .35, .36), .06, .18, .57),
        'poly': material('S06_Nursery_Frosted_Glazing', (.62, .74, .67), 0, .28, .81),
        'stone': material('S06_Warm_Masonry', (.50, .49, .41), 0, .82),
        'wood': material('S06_Nursery_Bench_Timber', (.39, .255, .13), 0, .68),
        'soil': material('S06_Potting_Soil', (.105, .070, .035), 0, .96),
        'pot': material('S06_Nursery_Terracotta', (.48, .25, .145), 0, .82),
        'leaf': material('S06_Sapling_Leaf_Green', (.23, .39, .07), 0, .64),
        'leaf2': material('S06_Sapling_Leaf_Sage', (.36, .49, .12), 0, .62),
        'bark': material('S06_Sapling_Stem', (.31, .235, .10), 0, .8),
        'lamp': material('S06_Warm_Lamp_Diffuser', (.92, .79, .45), .05, .22),
    }
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 24
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 7
    sc.cycles.transmission_bounces = 5
    sc.render.threads_mode = 'FIXED'
    sc.render.threads = 4
    sc.render.resolution_x = 960
    sc.render.resolution_y = 960
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'AgX'
    sc.render.image_settings.color_depth = '8'
    bpy.context.preferences.filepaths.save_version = 0


def finish_object(ob, name, mat, bevel=0, smooth=False):
    ob.name = name
    for col in list(ob.users_collection):
        col.objects.unlink(ob)
    ASSET.objects.link(ob)
    if mat:
        ob.data.materials.append(M[mat] if isinstance(mat, str) else mat)
    if smooth:
        for p in ob.data.polygons:
            p.use_smooth = True
    if bevel:
        mod = ob.modifiers.new('Soft_manufactured_edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 3
    if bevel and not smooth:
        mod = ob.modifiers.new('Weighted_corner_normals', 'WEIGHTED_NORMAL')
        mod.keep_sharp = True
        mod.weight = 50
    return ob


def box(name, loc, size, mat='pine', bevel=.045, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.object
    ob.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if rot:
        ob.rotation_euler = rot
    return finish_object(ob, name, mat, min(bevel, min(size) * .3))


def cyl(name, loc, radius, depth, mat='pine', axis='Z', bevel=.025, vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    ob = bpy.context.object
    if axis == 'X':
        ob.rotation_euler[1] = math.pi / 2
    elif axis == 'Y':
        ob.rotation_euler[0] = math.pi / 2
    return finish_object(ob, name, mat, min(bevel, depth * .22, radius * .3), True)


def cone(name, loc, lower, upper, depth, mat='pine', vertices=40, bevel=.018):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=lower, radius2=upper, depth=depth, location=loc)
    return finish_object(bpy.context.object, name, mat, bevel, True)


def rod(name, a, b, radius, mat='pine', vertices=16):
    a, b = Vector(a), Vector(b)
    ob = cyl(name, (a + b) / 2, radius, (b - a).length, mat, bevel=min(radius * .22, .025), vertices=vertices)
    ob.rotation_euler = (b - a).to_track_quat('Z', 'Y').to_euler()
    return ob


def beam(name, a, b, width, depth=None, mat='pine'):
    a, b = Vector(a), Vector(b)
    ob = box(name, (a + b) / 2, (width, depth or width, (b - a).length), mat, bevel=width * .18)
    ob.rotation_euler = (b - a).to_track_quat('Z', 'Y').to_euler()
    return ob


def mesh(name, verts, faces, mat='pine', bevel=0, smooth=False):
    data = bpy.data.meshes.new(name + '_Mesh')
    data.from_pydata(verts, [], faces)
    data.update()
    ob = bpy.data.objects.new(name, data)
    ASSET.objects.link(ob)
    return finish_object(ob, name, mat, bevel, smooth)


def tube(name, points, radius, mat='pine', sides=10, closed=False):
    points = [Vector(p) for p in points]
    verts = []
    for i, p in enumerate(points):
        if closed:
            tangent = points[(i + 1) % len(points)] - points[(i - 1) % len(points)]
        else:
            tangent = points[min(i + 1, len(points) - 1)] - points[max(i - 1, 0)]
        q = tangent.to_track_quat('Z', 'Y')
        for j in range(sides):
            v = q @ Vector((radius * math.cos(TAU * j / sides), radius * math.sin(TAU * j / sides), 0))
            verts.append(p + v)
    faces = []
    for i in range(len(points) if closed else len(points) - 1):
        ni = (i + 1) % len(points)
        for j in range(sides):
            k = (j + 1) % sides
            faces.append((i * sides + j, i * sides + k, ni * sides + k, ni * sides + j))
    if not closed:
        faces.extend([tuple(range(sides - 1, -1, -1)), tuple((len(points) - 1) * sides + j for j in range(sides))])
    return mesh(name, verts, faces, mat, smooth=True)


def circle(name, center, radius, thickness, mat='pine', start=0, end=TAU, segments=64):
    closed = abs(end - start - TAU) < .001
    count = segments if closed else segments + 1
    pts = [(center[0] + radius * math.cos(start + (end - start) * i / segments),
            center[1] + radius * math.sin(start + (end - start) * i / segments), center[2]) for i in range(count)]
    return tube(name, pts, thickness, mat, closed=closed)


def thin_panel(name, verts, mat='glass', thickness=.025):
    ob = mesh(name, verts, [tuple(range(len(verts)))], mat)
    mod = ob.modifiers.new('Panel_thickness', 'SOLIDIFY')
    mod.thickness = thickness
    mod = ob.modifiers.new('Panel_edge_softening', 'BEVEL')
    mod.width = .012
    mod.segments = 2
    return ob


def tire(prefix, center, radius, width, small=False):
    x, y, z = center
    side = 1 if x >= 0 else -1
    cyl(prefix + '_Rubber_Carcass', center, radius, width, 'rubber', 'X', .085 if not small else .045, 40)
    outer = x + side * width * .51
    cyl(prefix + '_Cream_Rim', (outer, y, z), radius * .57, .065, 'cream', 'X', .025)
    cyl(prefix + '_Green_Hub', (outer + side * .045, y, z), radius * .31, .09, 'pine', 'X', .025)
    for j in range(16):
        t = TAU * j / 16
        box(prefix + f'_Tread_{j:02}', (x, y + math.sin(t) * radius, z + math.cos(t) * radius),
            (width * 1.02, radius * .23, radius * .10), 'rubber', .022, (-t, 0, 0))
    for j in range(6):
        t = TAU * j / 6
        cyl(prefix + f'_Hub_Bolt_{j}', (outer + side * .105, y + math.sin(t) * radius * .23, z + math.cos(t) * radius * .23),
            radius * .045, .025, 'steel', 'X', .005, 8)


def leaf(name, base, direction, length, width, mat):
    verts = []
    rows = 7
    for side in (-1, 1):
        for i in range(rows):
            t = i / (rows - 1)
            w = width * max(.025, math.sin(math.pi * t))
            bend = length * .10 * math.sin(math.pi * t)
            for j in (-1, 0, 1):
                verts.append((j * w, bend + (1 - abs(j)) * width * .18 + side * .006, t * length))
    faces = []
    offset = rows * 3
    for s in range(2):
        for i in range(rows - 1):
            for j in range(2):
                a = s * offset + i * 3 + j
                face = (a, a + 1, a + 4, a + 3)
                faces.append(face if s == 1 else tuple(reversed(face)))
    outline = [i * 3 for i in range(rows)] + [i * 3 + 2 for i in range(rows - 1, -1, -1)]
    for i, a in enumerate(outline):
        b = outline[(i + 1) % len(outline)]
        faces.append((a, b, b + offset, a + offset))
    ob = mesh(name, verts, faces, mat, smooth=True)
    ob.location = base
    ob.rotation_euler = Vector(direction).to_track_quat('Z', 'Y').to_euler()
    return ob


def potted_sapling(prefix, base, scale=1, variant=0):
    x, y, z = base
    r, h = .16 * scale, .24 * scale
    cone(prefix + '_Pot', (x, y, z + h / 2), r * .75, r, h, 'pot', 24, .012 * scale)
    circle(prefix + '_Pot_Rim', (x, y, z + h), r, .018 * scale, 'pot', segments=24)
    cyl(prefix + '_Soil', (x, y, z + h), r * .87, .02 * scale, 'soil', bevel=.006, vertices=24)
    stem_h = (.49 + .04 * (variant % 3)) * scale
    rod(prefix + '_Stem', (x, y, z + h), (x + .035 * scale, y, z + h + stem_h), .012 * scale, 'bark', 8)
    for j in range(6):
        t = .2 + j * .12
        ang = j * 2.35 + variant * .7
        base_pt = (x + .035 * t * scale, y, z + h + stem_h * t)
        direction = (math.cos(ang) * .83, math.sin(ang) * .83, .48)
        leaf(prefix + f'_Leaf_{j}', base_pt, direction, (.26 - .013 * j) * scale, .085 * scale, 'leaf' if j % 2 else 'leaf2')
    leaf(prefix + '_New_Growth', (x + .03 * scale, y, z + h + stem_h * .87), (.1, .03, 1), .22 * scale, .065 * scale, 'leaf2')


def tree_transplanter():
    box('Rear_Main_Frame', (0, 1.0, .96), (1.84, 2.85, .40), 'pine', .16)
    box('Front_Main_Frame', (0, -.91, .96), (1.72, 1.35, .36), 'pine', .13)
    cyl('Articulated_Waist_Steering_Pivot', (0, -.12, 1.15), .31, .64, 'iron', bevel=.04)
    cyl('Waist_Pivot_Cap', (0, -.12, 1.50), .35, .13, 'pine')
    for sx in (-1, 1):
        rod(f'Waist_Steering_Ram_{sx}', (sx * .64, -.6, 1.08), (sx * .64, .45, 1.08), .085, 'steel')
        for iy, y in enumerate((-.92, 1.45)):
            tire(f'Wheel_{sx}_{iy}', (sx * 1.08, y, .70), .67, .50)
            box(f'Rounded_Fender_{sx}_{iy}', (sx * 1.03, y, 1.31), (.77, 1.22, .20), 'rubber', .09)
    box('Engine_Counterweight', (0, 1.85, 1.65), (1.91, 1.15, 1.13), 'cream', .24)
    box('Rear_Protective_Bumper', (0, 2.48, .98), (1.95, .20, .34), 'pine', .08)
    box('Rear_Engine_Access', (0, 2.44, 1.67), (1.37, .075, .70), 'pine', .055)
    for i in range(6):
        box(f'Rear_Cooling_Louvre_{i}', (0, 2.49, 1.43 + i * .075), (.96, .035, .025), 'iron', .009)
    for sx in (-1, 1):
        box(f'Side_Engine_Vent_{sx}', (sx * .969, 1.83, 1.79), (.045, .71, .48), 'terra', .045)
        for i in range(5):
            box(f'Side_Vent_Slat_{sx}_{i}', (sx * .999, 1.83, 1.63 + i * .075), (.025, .56, .027), 'iron', .008)
        box(f'Rear_Stop_Lamp_{sx}', (sx * .72, 2.51, 1.20), (.24, .06, .12), 'terra', .025)
    cyl('Exhaust_Lower_Shroud', (.63, 1.85, 2.37), .125, .43, 'iron')
    tube('Bent_Exhaust_Pipe', [(.63, 1.85, 2.42), (.63, 1.85, 2.91), (.63, 1.91, 3.06), (.63, 2.07, 3.13)], .065, 'iron')
    box('Cab_Floor', (0, .50, 1.50), (1.80, 1.95, .30), 'pine', .10)
    box('Cab_Roof', (0, .54, 3.08), (1.94, 1.97, .25), 'cream', .11)
    box('Roof_Amber_Service_Beacon', (0, .51, 3.25), (.56, .34, .11), 'terra', .05)
    for sx in (-1, 1):
        beam(f'Cab_Front_Pillar_{sx}', (sx * .78, -.43, 1.64), (sx * .78, -.28, 2.99), .13, .14, 'cream')
        beam(f'Cab_Rear_Pillar_{sx}', (sx * .78, 1.33, 1.64), (sx * .78, 1.30, 2.99), .13, .14, 'cream')
        thin_panel(f'Cab_Side_Glazing_{sx}', [(sx * .80, -.32, 1.74), (sx * .80, 1.25, 1.74), (sx * .80, 1.25, 2.91), (sx * .80, -.23, 2.91)], 'glass', .035)
        beam(f'Cab_Door_Divider_{sx}', (sx * .82, .45, 1.68), (sx * .82, .45, 2.99), .055, .075, 'pine')
        box(f'Door_Handle_{sx}', (sx * .86, .25, 2.05), (.07, .23, .055), 'iron', .025)
        for i in range(2):
            box(f'Cab_Step_{sx}_{i}', (sx * 1.0, .40, .60 + i * .28), (.44, .70, .11), 'steel', .04)
        beam(f'Mirror_Bracket_{sx}', (sx * .81, -.27, 2.74), (sx * 1.10, -.31, 2.70), .055, mat='iron')
        box(f'Mirror_{sx}', (sx * 1.12, -.31, 2.62), (.16, .13, .35), 'iron', .065)
        box(f'Work_Light_Housing_{sx}', (sx * .75, -.48, 2.98), (.26, .20, .21), 'iron', .04)
        box(f'Work_Light_Lens_{sx}', (sx * .75, -.59, 2.98), (.19, .025, .14), 'lamp', .025)
    thin_panel('Cab_Front_Windscreen', [(-.70, -.45, 1.73), (.70, -.45, 1.73), (.70, -.31, 2.94), (-.70, -.31, 2.94)], 'glass', .035)
    thin_panel('Cab_Rear_Windscreen', [(-.69, 1.32, 1.90), (.69, 1.32, 1.90), (.69, 1.31, 2.92), (-.69, 1.31, 2.92)], 'glass', .035)
    beam('Single_Windscreen_Wiper', (-.05, -.49, 1.79), (.40, -.42, 2.42), .025, .035, 'iron')
    box('Operator_Seat_Cushion', (0, .65, 1.88), (.59, .57, .17), 'rubber', .07)
    box('Operator_Seat_Backrest', (0, .91, 2.20), (.62, .14, .63), 'rubber', .08, (.09, 0, 0))
    box('Operator_Dashboard', (0, -.15, 2.03), (1.15, .30, .25), 'iron', .07)
    rod('Steering_Column', (0, .02, 1.75), (0, -.02, 2.24), .035, 'iron')
    circle('Steering_Wheel', (0, -.02, 2.24), .18, .025, 'rubber', segments=24)
    box('Cradle_Reach_Beam', (0, -1.64, 1.16), (.64, 1.45, .35), 'pine', .09)
    cradle = (0, -2.38, 1.07)
    circle('Empty_Rootball_Cradle_Upper_Rim', cradle, 1.00, .14, 'pine')
    circle('Cradle_Lower_Stabilizer_Ring', (0, -2.38, .80), .91, .07, 'iron')
    # Four blunt digging shells: curved angular strips with distinct inner skins.
    for p in range(4):
        angle = math.radians(45 + 90 * p)
        profile = [(.72, .35, .19), (.92, .64, .30), (1.05, 1.05, .38), (1.20, 1.65, .37), (1.36, 2.22, .30), (1.36, 2.48, .25)]
        verts = []
        cols = 8
        for skin in (-1, 1):
            for r, z, half in profile:
                for j in range(cols + 1):
                    t = angle + half * (2 * j / cols - 1)
                    rr = r + skin * .055
                    verts.append((rr * math.cos(t), -2.38 + rr * math.sin(t), z))
        faces = []
        material_ids = []
        layer = len(profile) * (cols + 1)
        for skin in range(2):
            for row in range(len(profile) - 1):
                for j in range(cols):
                    a = skin * layer + row * (cols + 1) + j
                    face = (a, a + 1, a + cols + 2, a + cols + 1)
                    faces.append(face if skin else tuple(reversed(face)))
                    material_ids.append(2 if row == 0 else (1 if skin == 0 else 0))
        outline = list(range(cols + 1)) + [r * (cols + 1) + cols for r in range(1, len(profile))] + list(range(layer - 2, layer - cols - 2, -1)) + [r * (cols + 1) for r in range(len(profile) - 2, 0, -1)]
        for j, a in enumerate(outline):
            b = outline[(j + 1) % len(outline)]
            faces.append((a, b, b + layer, a + layer))
            material_ids.append(0)
        ob = mesh(f'Digging_Petal_{p}_Curved_Shell', verts, faces, 'pine', .018, True)
        ob.data.materials.append(M['cream'])
        ob.data.materials.append(M['iron'])
        for poly, mid in zip(ob.data.polygons, material_ids):
            poly.material_index = mid
        radial = Vector((math.cos(angle), math.sin(angle), 0))
        a = Vector((0, -2.38, 1.02)) + radial * 1.18
        b = Vector((0, -2.38, 2.30)) + radial * 1.50
        c = a.lerp(b, .55)
        rod(f'Petal_{p}_Ram_Barrel', a, c, .11, 'pine')
        rod(f'Petal_{p}_Chrome_Piston', c, b, .06, 'steel')
        for label, point in (('Lower', a), ('Upper', b)):
            box(f'Petal_{p}_{label}_Hydraulic_Clevis', point, (.22, .22, .20), 'terra', .055)
        tube(f'Petal_{p}_Hydraulic_Hose', [a + radial * .12, a + radial * .20 + Vector((0, 0, .25)), c + radial * .18, b + radial * .10], .025, 'rubber')
    return {'label': 'Articulated tree transplanter', 'design': 'Empty circular root cradle, four curved blunt digging petals, hydraulic rams, compact articulated cab and four tires.', 'front': '-Y', 'intended_dimensions_m': [3.25, 6.45, 3.32]}


def nursery_carrier_robot():
    box('Rounded_Battery_Chassis', (0, 0, .72), (1.66, 2.84, .59), 'cream', .19)
    box('Lower_Impact_Bumper', (0, 0, .47), (1.76, 2.96, .27), 'pine', .11)
    for sx in (-1, 1):
        for i, y in enumerate((-.98, 0, .98)):
            tire(f'Carrier_Wheel_{sx}_{i}', (sx * .87, y, .38), .35, .26, True)
            box(f'Wheel_Guard_{sx}_{i}', (sx * .80, y, .73), (.32, .69, .12), 'rubber', .045)
        box(f'Side_Service_Cover_{sx}', (sx * .842, .15, .76), (.035, 1.58, .30), 'pine', .035)
        box(f'Battery_Release_{sx}', (sx * .87, .62, .82), (.055, .24, .055), 'iron', .023)
    box('Front_Navigation_Bar_Housing', (0, -1.456, .83), (1.16, .12, .23), 'iron', .09)
    box('Front_Sensor_Continuous_Glass', (0, -1.525, .83), (1.03, .025, .12), 'glass', .045)
    for sx in (-1, 1):
        box(f'Front_Clearance_Lamp_{sx}', (sx * .69, -1.47, .75), (.15, .055, .13), 'terra', .035)
    box('Rear_Battery_Access_Panel', (0, 1.452, .76), (1.20, .07, .37), 'pine', .06)
    box('Rear_Battery_Latch', (0, 1.505, .90), (.36, .05, .065), 'terra', .025)
    for i in range(4):
        box(f'Rear_Battery_Vent_{i}', (0, 1.497, .63 + i * .05), (.57, .025, .018), 'iron', .005)
    for level, z in enumerate((1.09, 2.04)):
        box(f'Rack_{level}_Tray_Floor', (0, 0, z), (1.46, 2.50, .12), 'pine', .055)
        for sx in (-1, 1):
            box(f'Rack_{level}_Side_Lip_{sx}', (sx * .72, 0, z + .12), (.09, 2.52, .22), 'pine', .045)
            tube(f'Rack_{level}_Side_Rail_{sx}', [(sx * .70, -1.21, z + .18), (sx * .70, -1.21, z + .37), (sx * .70, -1.10, z + .43), (sx * .70, 1.10, z + .43), (sx * .70, 1.21, z + .37), (sx * .70, 1.21, z + .18)], .046, 'pine')
        for sy in (-1, 1):
            box(f'Rack_{level}_End_Lip_{sy}', (0, sy * 1.23, z + .11), (1.48, .09, .20), 'pine', .035)
        for sx in (-1, 1):
            for sy in (-1, 1):
                box(f'Rack_{level}_Corner_Cap_{sx}_{sy}', (sx * .72, sy * 1.23, z + .17), (.19, .20, .37), 'cream', .065)
        for row, y in enumerate((-.77, 0, .77)):
            for col, x in enumerate((-.33, .33)):
                potted_sapling(f'Rack_{level}_Sapling_{row}_{col}', (x, y, z + .065), .86 if level == 0 else 1.0, row + col + level)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f'Rack_Vertical_Support_{sx}_{sy}', (sx * .70, sy * 1.20, 1.58), (.11, .13, 1.02), 'cream', .045)
    box('Top_Rear_Localization_Module', (0, 1.24, 2.42), (.45, .17, .15), 'pine', .05)
    box('Localization_Module_Window', (0, 1.335, 2.42), (.32, .02, .075), 'glass', .018)
    return {'label': 'Autonomous nursery tray carrier', 'design': 'Six-wheel rounded battery chassis, two open plant racks with twelve saplings, continuous navigation bar and rear battery hatch.', 'front': '-Y', 'intended_dimensions_m': [2.0, 3.1, 3.05]}


def arched_nursery_greenhouse():
    radius, spring, half_len = 2.15, 1.60, 3.20
    box('Greenhouse_Interior_Floor', (0, 0, .12), (4.34, 6.54, .24), 'stone', .075)
    for sx in (-1, 1):
        for i in range(8):
            box(f'Side_Foundation_Block_{sx}_{i}', (sx * 2.08, -2.85 + i * .815, .37), (.37, .80, .39), 'stone', .028)
        box(f'Side_Terracotta_Coping_{sx}', (sx * 2.08, 0, .61), (.47, 6.58, .13), 'terra', .045)
    for sy in (-1, 1):
        if sy == 1:
            box('Rear_Foundation_Course', (0, half_len, .38), (4.28, .36, .41), 'stone', .04)
            box('Rear_Terracotta_Coping', (0, half_len, .62), (4.42, .43, .13), 'terra', .04)
        else:
            for sx in (-1, 1):
                box(f'Front_Foundation_Wing_{sx}', (sx * 1.63, -half_len, .37), (1.07, .37, .40), 'stone', .03)
                box(f'Front_Coping_Wing_{sx}', (sx * 1.63, -half_len, .61), (1.13, .44, .13), 'terra', .04)
    for i in range(7):
        y = -half_len + i * (half_len * 2 / 6)
        points = [(-radius, y, .66), (-radius, y, spring)]
        points += [(radius * math.cos(math.pi - math.pi * j / 32), y, spring + radius * math.sin(math.pi - math.pi * j / 32)) for j in range(1, 33)]
        points += [(radius, y, .66)]
        tube(f'Vault_Structural_Rib_{i}', points, .095, 'pine', 10)
        for sx in (-1, 1):
            box(f'Rib_Foot_Shoe_{i}_{sx}', (sx * radius, y, .75), (.25, .24, .24), 'iron', .03)
    for bay in range(6):
        ya = -half_len + bay * half_len * 2 / 6
        yb = -half_len + (bay + 1) * half_len * 2 / 6
        for section in range(6):
            aa, ab = section * math.pi / 6, (section + 1) * math.pi / 6
            verts = []
            n = 8
            for y in (ya + .035, yb - .035):
                for j in range(n + 1):
                    a = aa + (ab - aa) * j / n
                    verts.append((radius * math.cos(a), y, spring + radius * math.sin(a)))
            faces = [(j, j + 1, n + 2 + j, n + 1 + j) for j in range(n)]
            ob = mesh(f'Roof_Glazing_Bay_{bay}_Strip_{section}', verts, faces, 'poly', smooth=True)
            mod = ob.modifiers.new('Glazing_sheet_thickness', 'SOLIDIFY')
            mod.thickness = .018
        for sx in (-1, 1):
            thin_panel(f'Lower_Side_Glazing_{bay}_{sx}', [(sx * radius, ya + .04, .68), (sx * radius, yb - .04, .68), (sx * radius, yb - .04, spring), (sx * radius, ya + .04, spring)], 'poly')
    for a in (0, math.pi / 4, math.pi / 2, 3 * math.pi / 4, math.pi):
        rod(f'Vault_Longitudinal_Rail_{a:.2f}', (radius * math.cos(a), -half_len, spring + radius * math.sin(a)), (radius * math.cos(a), half_len, spring + radius * math.sin(a)), .045, 'pine')
    def roof_h(x):
        return spring + math.sqrt(max(0, radius * radius - x * x))
    for sy in (-1, 1):
        y = sy * half_len
        for sx in (-1, 1):
            xa, xb = (1.03, radius - .08) if sx == 1 else (-radius + .08, -1.03)
            upper = [(xb - (xb - xa) * i / 12, y, roof_h(xb - (xb - xa) * i / 12) - .06) for i in range(13)]
            thin_panel(f'Endwall_Side_Glazing_{sy}_{sx}', [(xa, y, .68), (xb, y, .68)] + upper, 'poly')
            beam(f'Endwall_Entry_Post_{sy}_{sx}', (sx * 1.03, y, .65), (sx * 1.03, y, roof_h(1.03)), .10, .10, 'pine')
        upper = [(1.03 - 2.06 * i / 16, y, roof_h(1.03 - 2.06 * i / 16) - .06) for i in range(17)]
        thin_panel(f'Endwall_Transom_Glazing_{sy}', [(-1.03, y, 2.61), (1.03, y, 2.61)] + upper, 'poly')
        box(f'Entry_Transom_{sy}', (0, y - .035, 2.62), (2.21, .17, .13), 'pine', .035)
        if sy == 1:
            thin_panel('Rear_Central_Glazing', [(-.98, y, .69), (.98, y, .69), (.98, y, 2.55), (-.98, y, 2.55)], 'poly')
            box('Rear_Center_Mullion', (0, y, 1.61), (.07, .08, 1.91), 'pine', .025)
    # The front sliding leaf is parked left, keeping the aisle visibly open.
    door_x, door_y = -.94, -3.28
    thin_panel('Sliding_Entry_Glazing', [(door_x - .58, door_y, .28), (door_x + .58, door_y, .28), (door_x + .58, door_y, 2.51), (door_x - .58, door_y, 2.51)], 'poly')
    for sx in (-1, 1):
        box(f'Sliding_Door_Stile_{sx}', (door_x + sx * .60, door_y, 1.40), (.10, .10, 2.34), 'pine', .035)
    for z in (.25, 2.55):
        box(f'Sliding_Door_Rail_{z}', (door_x, door_y, z), (1.28, .11, .11), 'pine', .03)
    box('Sliding_Door_Handle', (door_x + .46, door_y - .07, 1.29), (.065, .07, .30), 'iron', .03)
    box('Sliding_Door_Top_Track', (-.50, -3.29, 2.72), (3.14, .18, .11), 'iron', .04)
    box('Entry_Threshold', (0, -3.27, .24), (2.10, .43, .10), 'iron', .03)
    for j, yc in enumerate((-2.12, 0, 2.12)):
        top_a, top_b = (2.18, yc - .43, 2.00), (2.18, yc + .43, 2.00)
        bot_a, bot_b = (2.59, yc - .43, 1.35), (2.59, yc + .43, 1.35)
        thin_panel(f'Open_Vent_Flap_{j}', [top_a, top_b, bot_b, bot_a], 'poly')
        for k, (a, b) in enumerate(((top_a, top_b), (top_b, bot_b), (bot_b, bot_a), (bot_a, top_a))):
            beam(f'Vent_Flap_Frame_{j}_{k}', a, b, .075, .075, 'pine')
        rod(f'Vent_Opening_Stay_{j}', (2.18, yc, 1.20), (2.55, yc, 1.39), .025, 'iron')
    for sx in (-1, 1):
        for bank, y in enumerate((-1.90, 0, 1.90)):
            x = sx * 1.30
            box(f'Bench_{sx}_{bank}_Timber_Top', (x, y, 1.03), (1.00, 1.60, .10), 'wood', .035)
            for dx in (-.38, .38):
                for dy in (-.62, .62):
                    box(f'Bench_{sx}_{bank}_Leg_{dx}_{dy}', (x + dx, y + dy, .63), (.09, .09, .78), 'pine', .023)
            box(f'Bench_{sx}_{bank}_Nursery_Tray', (x, y, 1.12), (.87, 1.38, .10), 'pine', .035)
            for r, dy in enumerate((-.43, .43)):
                for c, dx in enumerate((-.22, .22)):
                    potted_sapling(f'Bench_{sx}_{bank}_Plant_{r}_{c}', (x + dx, y + dy, 1.17), .62, bank + r + c)
    rod('Ridge_Vent_Actuator_Housing', (0, -2.9, 3.86), (0, 2.9, 3.86), .065, 'iron')
    return {'label': 'Arched nursery greenhouse', 'design': 'Single-span curved glazing over seven pine-green ribs, low masonry curb, sliding entrance, three opening side vents and six planting benches.', 'front': '-Y', 'intended_dimensions_m': [4.95, 6.75, 3.95]}


def stairs(prefix, start, end, width=.85, count=11):
    start, end = Vector(start), Vector(end)
    d = end - start
    horizontal = Vector((d.x, d.y, 0)).normalized()
    side = Vector((-horizontal.y, horizontal.x, 0))
    tread = Vector((d.x, d.y, 0)).length / count
    rotation = math.atan2(horizontal.y, horizontal.x) - math.pi / 2
    for i in range(count):
        p = start + d * ((i + .5) / count)
        p.z = start.z + d.z * ((i + 1) / count)
        box(prefix + f'_Tread_{i:02}', p, (width, tread * 1.10, .105), 'steel', .022, (0, 0, rotation))
    for s in (-1, 1):
        off = side * width * .47
        beam(prefix + f'_Stringer_{s}', start + off + Vector((0, 0, -.07)), end + off + Vector((0, 0, -.07)), .12, .18, 'pine')
        rod(prefix + f'_Handrail_{s}', start + off + Vector((0, 0, .90)), end + off + Vector((0, 0, .90)), .045, 'terra')
        rod(prefix + f'_Midrail_{s}', start + off + Vector((0, 0, .48)), end + off + Vector((0, 0, .48)), .030, 'pine')
        for j in range(0, count + 1, 2):
            p = start + d * (j / count) + off
            rod(prefix + f'_Rail_Post_{s}_{j}', p, p + Vector((0, 0, .91)), .038, 'pine')


def forest_watchtower():
    floor_z, cabin_r, balcony_r = 4.08, 1.72, 2.48
    for sx in (-1, 1):
        for sy in (-1, 1):
            prefix = f'Leg_{sx}_{sy}'
            foot = Vector((sx * 1.56, sy * 1.56, .37))
            top = Vector((sx * 1.11, sy * 1.11, 3.93))
            cyl(prefix + '_Individual_Concrete_Footing', (foot.x, foot.y, .19), .53, .38, 'stone', bevel=.055)
            cyl(prefix + '_Anchor_Plate', (foot.x, foot.y, .42), .47, .10, 'iron', bevel=.025)
            rod(prefix + '_Broad_Splayed_Support', foot, top, .23, 'cream', 24)
            rod(prefix + '_Lower_Green_Collar', foot, foot.lerp(top, .17), .27, 'pine', 24)
            rod(prefix + '_Upper_Green_Collar', foot.lerp(top, .82), top, .26, 'pine', 24)
            for i in range(4):
                a = TAU * i / 4 + math.pi / 4
                cyl(prefix + f'_Anchor_Bolt_{i}', (foot.x + .34 * math.cos(a), foot.y + .34 * math.sin(a), .50), .045, .10, 'steel', vertices=8, bevel=.007)
    for sy in (-1, 1):
        beam(f'Cross_Brace_{sy}_A', (-1.40, sy * 1.43, 1.18), (1.14, sy * 1.14, 3.66), .16, .18, 'pine')
        beam(f'Cross_Brace_{sy}_B', (1.40, sy * 1.43, 1.18), (-1.14, sy * 1.14, 3.66), .16, .18, 'pine')
    for sx in (-1, 1):
        beam(f'Side_Cross_Brace_{sx}', (sx * 1.41, -1.41, 1.20), (sx * 1.15, 1.15, 3.65), .16, .18, 'pine')
    for a, b in (((-1.40, -1.40, 1.20), (1.40, -1.40, 1.20)), ((1.40, -1.40, 1.20), (1.40, 1.40, 1.20)), ((1.40, 1.40, 1.20), (-1.40, 1.40, 1.20)), ((-1.40, 1.40, 1.20), (-1.40, -1.40, 1.20))):
        beam(f'Lower_Tie_Beam_{a}', a, b, .18, .21, 'pine')
    cyl('Circular_Balcony_Deck', (0, 0, floor_z - .10), balcony_r, .22, 'pine', bevel=.055, vertices=64)
    cyl('Cabin_Internal_Floor', (0, 0, floor_z + .045), cabin_r, .10, 'wood', bevel=.025, vertices=48)
    # Twelve editable window bays; southeast bay is the access door.
    n = 12
    door_sector = 10
    for i in range(n):
        a, b = TAU * i / n, TAU * (i + 1) / n
        am = (a + b) / 2
        pa = (cabin_r * math.cos(a), cabin_r * math.sin(a))
        pb = (cabin_r * math.cos(b), cabin_r * math.sin(b))
        if i != door_sector:
            thin_panel(f'Cabin_Cream_Lower_Wall_{i}', [(pa[0], pa[1], 4.16), (pb[0], pb[1], 4.16), (pb[0], pb[1], 4.79), (pa[0], pa[1], 4.79)], 'cream', .075)
            thin_panel(f'Observation_Window_{i}', [(pa[0], pa[1], 4.84), (pb[0], pb[1], 4.84), (pb[0], pb[1], 6.15), (pa[0], pa[1], 6.15)], 'glass', .035)
            rod(f'Window_Lower_Rail_{i}', (pa[0], pa[1], 4.82), (pb[0], pb[1], 4.82), .055, 'pine')
        else:
            thin_panel('Cabin_Access_Door', [(pa[0], pa[1], 4.16), (pb[0], pb[1], 4.16), (pb[0], pb[1], 6.12), (pa[0], pa[1], 6.12)], 'pine', .065)
            r = cabin_r + .045
            aa, ab = a + .11, b - .11
            thin_panel('Door_Upper_Window', [(r * math.cos(aa), r * math.sin(aa), 5.13), (r * math.cos(ab), r * math.sin(ab), 5.13), (r * math.cos(ab), r * math.sin(ab), 5.89), (r * math.cos(aa), r * math.sin(aa), 5.89)], 'glass', .025)
            p = Vector(((cabin_r + .08) * math.cos(a + .10), (cabin_r + .08) * math.sin(a + .10), 4.98))
            rod('Cabin_Door_Handle', p, p + Vector((0, 0, .20)), .026, 'iron')
        rod(f'Cabin_Window_Post_{i}', (pa[0], pa[1], 4.13), (pa[0], pa[1], 6.25), .075, 'pine')
        rod(f'Window_Upper_Rail_{i}', (pa[0], pa[1], 6.19), (pb[0], pb[1], 6.19), .075, 'pine')
    circle('Cabin_Cream_Roof_Fascia', (0, 0, 6.26), 1.90, .115, 'cream')
    cone('Shallow_Conical_Roof', (0, 0, 6.67), 2.09, .43, .76, 'pine', 64, .035)
    circle('Terracotta_Eaves_Gutter', (0, 0, 6.31), 2.09, .065, 'terra')
    for i in range(12):
        a = TAU * i / 12
        rod(f'Roof_Standing_Seam_{i}', (2.02 * math.cos(a), 2.02 * math.sin(a), 6.34), (.47 * math.cos(a), .47 * math.sin(a), 7.06), .020, 'sage', 8)
    cyl('Roof_Blunt_Vent_Drum', (0, 0, 7.10), .43, .26, 'cream', bevel=.035)
    cone('Roof_Rounded_Vent_Cap', (0, 0, 7.28), .49, .33, .16, 'terra', 48, .055)
    cyl('Roof_Service_Vent', (.80, .43, 6.92), .095, .48, 'iron', bevel=.025)
    cyl('Roof_Service_Vent_Cap', (.80, .43, 7.17), .15, .10, 'iron', bevel=.03)
    rod('Radio_Antenna', (-.69, .55, 6.82), (-.69, .55, 7.55), .020, 'iron', 10)
    # Railing gap aligns with the external stair's upper landing.
    for z, thick, mat in ((4.58, .035, 'pine'), (5.07, .05, 'terra')):
        circle(f'Balcony_Rail_{z}', (0, 0, z), 2.40, thick, mat, start=math.radians(-20), end=math.radians(290), segments=70)
    for i in range(19):
        a = math.radians(-20 + 310 * i / 18)
        rod(f'Balcony_Railing_Post_{i}', (2.40 * math.cos(a), 2.40 * math.sin(a), 4.08), (2.40 * math.cos(a), 2.40 * math.sin(a), 5.08), .043, 'pine')
    for i in range(12):
        a = TAU * i / 12
        beam(f'Balcony_Underside_Bracket_{i}', (1.36 * math.cos(a), 1.36 * math.sin(a), 3.43), (2.32 * math.cos(a), 2.32 * math.sin(a), 3.94), .13, .16, 'pine')
    stairs('Lower_External_Stair', (3.05, -3.23, .22), (3.05, -.20, 2.20), .84, 11)
    box('Mid_Stair_Landing', (2.58, .14, 2.20), (1.90, .92, .16), 'pine', .035)
    stairs('Upper_Return_Stair', (2.08, -.20, 2.20), (2.08, -2.36, 4.08), .84, 10)
    box('Upper_Entry_Landing', (1.69, -2.31, 4.06), (1.61, 1.00, .18), 'pine', .05)
    for x in (1.68, 3.48):
        rod(f'Mid_Landing_Outer_Post_{x}', (x, .51, 2.20), (x, .51, 3.15), .04, 'pine')
    rod('Mid_Landing_Back_Handrail', (1.68, .51, 3.15), (3.48, .51, 3.15), .045, 'terra')
    rod('Mid_Landing_Back_Midrail', (1.68, .51, 2.70), (3.48, .51, 2.70), .032, 'pine')
    for x in (1.72, 3.45):
        cyl(f'Landing_Support_Footing_{x}', (x, .41, .12), .25, .24, 'stone', bevel=.03)
        rod(f'Landing_Support_Post_{x}', (x, .41, .24), (x, .41, 2.17), .075, 'pine')
    box('Observation_Desk', (0, .56, 4.92), (1.30, .56, .10), 'wood', .05)
    for x in (-.48, .48):
        box(f'Desk_Leg_{x}', (x, .56, 4.55), (.075, .075, .70), 'iron', .02)
    cyl('Desk_Observation_Instrument_Base', (0, .52, 5.02), .17, .12, 'iron', bevel=.02)
    rod('Observation_Instrument', (-.18, .52, 5.13), (.18, .52, 5.13), .10, 'pine', 20)
    return {'label': 'Circular forest lookout tower', 'design': 'Short splayed four-leg lookout, individual footings, glazed observation cabin, wraparound balcony, shallow cap roof and return staircase.', 'front': '-Y', 'intended_dimensions_m': [6.1, 6.1, 7.6]}


def author_uvs(objects):
    # Production UV unwrap, one named component at a time. No UV validator runs.
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.025, area_weight=.25, correct_aspect=True, scale_to_bounds=True)
        bpy.ops.object.mode_set(mode='OBJECT')
        if ob.data.uv_layers:
            ob.data.uv_layers.active.name = 'UV0_Component_Unwrap'
        ob.select_set(False)


def studio(objects):
    scene = bpy.context.scene
    collection = bpy.data.collections.new('STUDIO')
    scene.collection.children.link(collection)
    corners = [ob.matrix_world @ Vector(corner) for ob in objects for corner in ob.bound_box]
    low = Vector(tuple(min(p[i] for p in corners) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in corners) for i in range(3)))
    center = (low + high) / 2
    dims = high - low
    size = max(dims)
    studio_mat = material('STUDIO_Neutral_Warm_Gray', (.63, .64, .61), 0, .84)
    bpy.ops.mesh.primitive_plane_add(size=size * 200, location=(0, 0, low.z - .025))
    floor = bpy.context.object
    floor.name = 'STUDIO_Ground'
    floor.data.materials.append(studio_mat)
    for col in list(floor.users_collection):
        col.objects.unlink(floor)
    collection.objects.link(floor)
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.72, .76, .79, 1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .35
    def area(name, loc, energy, size_factor):
        data = bpy.data.lights.new(name, 'AREA')
        data.energy = energy * size * size
        data.shape = 'DISK'
        data.size = size * size_factor
        ob = bpy.data.objects.new(name, data)
        collection.objects.link(ob)
        ob.location = center + Vector(loc) * size
        ob.rotation_euler = (center - ob.location).to_track_quat('-Z', 'Y').to_euler()
    area('STUDIO_Key_Softbox', (-.9, -1.25, 1.6), 80, .90)
    area('STUDIO_Fill_Softbox', (1.2, -.4, .85), 42, 1.10)
    area('STUDIO_Rear_Rim', (.25, 1.1, 1.65), 105, .85)
    data = bpy.data.cameras.new('STUDIO_Orthographic_Camera')
    camera = bpy.data.objects.new('STUDIO_Orthographic_Camera', data)
    collection.objects.link(camera)
    scene.camera = camera
    data.type = 'ORTHO'
    data.lens = 50
    data.clip_end = 5000
    def place(view):
        direction = Vector((1.15, -1.65, 1.05) if view == 'hero' else (-1.15, 1.65, 1.05)).normalized()
        camera.location = center + direction * size * 3.6
        camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
        q = camera.rotation_euler.to_quaternion().inverted()
        projected = [q @ (p - center) for p in corners]
        width = max(p.x for p in projected) - min(p.x for p in projected)
        height = max(p.y for p in projected) - min(p.y for p in projected)
        data.ortho_scale = max(width, height) * 1.23
    return low, high, center, place


BUILDERS = {
    'tree_transplanter': tree_transplanter,
    'nursery_carrier_robot': nursery_carrier_robot,
    'arched_nursery_greenhouse': arched_nursery_greenhouse,
    'forest_watchtower': forest_watchtower,
}


def main():
    slug = sys.argv[sys.argv.index('--') + 1]
    start = now()
    setup()
    info = BUILDERS[slug]()
    bpy.context.view_layer.update()
    objects = list(ASSET.objects)
    for ob in objects:
        ob['set'] = 'Set06'
        ob['asset'] = slug
        ob['part_name'] = ob.name
    author_uvs(objects)
    low, high, center, camera_place = studio(objects)
    out = ROOT / slug
    (out / 'renders').mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(filepath=str(out / (slug + '.glb')), export_format='GLB', use_selection=True, export_apply=True,
                              export_texcoords=True, export_normals=True, export_materials='EXPORT', export_cameras=False,
                              export_lights=False, export_animations=False)
    bpy.ops.export_scene.fbx(filepath=str(out / (slug + '.fbx')), use_selection=True, object_types={'MESH'}, use_mesh_modifiers=True,
                             add_leaf_bones=False, bake_anim=False, axis_forward='-Z', axis_up='Y', apply_unit_scale=True,
                             path_mode='AUTO', mesh_smooth_type='FACE')
    camera_place('hero')
    bpy.context.scene.render.filepath = str(out / 'renders' / 'hero.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(out / (slug + '.blend')))
    captures = []
    for view in ('hero', 'rear'):
        camera_place(view)
        sc = bpy.context.scene
        sc.render.filepath = str(out / 'renders' / (view + '.png'))
        began = now()
        bpy.ops.render.render(write_still=True)
        captures.append({'view': view, 'started_at_utc': began, 'finished_at_utc': now(), 'camera_location_m': list(sc.camera.location),
                         'camera_rotation_radians': list(sc.camera.rotation_euler), 'orthographic_scale_m': sc.camera.data.ortho_scale,
                         'resolution': [960, 960], 'engine': 'CYCLES', 'device': 'CPU', 'samples': 24, 'denoising': True})
    metadata = {
        'set': 'Set06', 'slug': slug, **info,
        'status': 'produced_unreviewed', 'review_status': 'deferred_by_user',
        'source_reference': '../REF/' + slug + '.png', 'source_prompt': '../REF/' + slug + '.prompt.txt',
        'geometry_style': 'Original ordinary rounded mesh geometry; no voxels, no external creative geometry.',
        'units': 'meters', 'origin': [0, 0, 0], 'blender_version': bpy.app.version_string,
        'authored_bounds_min_m': list(low), 'authored_bounds_max_m': list(high), 'authored_dimensions_m': list(high - low),
        'measurements_note': 'Authored scene bounds before render; production measurements only, not independent validation.',
        'editable_mesh_parts': len(objects), 'source_vertices': sum(len(o.data.vertices) for o in objects),
        'source_polygons': sum(len(o.data.polygons) for o in objects),
        'uv_authoring': 'UV0_Component_Unwrap: per-component Smart Project, 66 degree angle, 0.025 island margin. No UV validation performed.',
        'materials': sorted({m.name for ob in objects for m in ob.data.materials}),
        'material_note': 'Named solid-color Principled PBR palette. Glazing uses transmission; FBX material fidelity remains unreviewed.',
        'collections': {'ASSET': 'Named editable mesh parts with softening modifiers', 'STUDIO': 'Neutral ground, camera and three area lights; omitted from geometry exports'},
        'export_note': 'Selected ASSET meshes only; modifiers applied by GLB/FBX exporters, no camera/light/animation export.',
        'started_at_utc': start, 'finished_at_utc': now(), 'captures': captures,
        'deferred_checks': ['visual inspection', 'fresh BLEND reopen', 'GLB/FBX reimport', 'geometry validation', 'UV validation', 'reviewer agents'],
        'limitations': ['Static model; no rig, animation, collision or LOD set.', 'Generated previews have not been viewed.', 'Export roundtrip and visual/material fidelity remain unreviewed.'],
    }
    (out / 'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print('SET06_ASSET_PRODUCED ' + slug, flush=True)


if __name__ == '__main__':
    main()
