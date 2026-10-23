"""Original Antarctic field equipment authored as occupied, colored voxels.

Front is -Y and vertical is +Z. The shared parent-owned voxelkit handles only
surface extraction, export, rendering, and validation. No external geometry,
textures, generated images, or other theme resources are used in these models.
"""
from pathlib import Path
import math
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_tools"))
from voxelkit import Asset, Grid, run_theme


EMPTY, IVORY, SNOW, SHADOW, NAVY, BLUE, DARK, STEEL, SILVER, ORANGE, AMBER, GLASS, SKY, BLACK, LAMP, SLATE = range(16)
PALETTE = [
    (0, 0, 0, 0),
    (231, 222, 202, 255),
    (249, 242, 224, 255),
    (184, 182, 169, 255),
    (31, 67, 91, 255),
    (42, 87, 117, 255),
    (41, 47, 53, 255),
    (98, 112, 121, 255),
    (152, 162, 163, 255),
    (233, 111, 24, 255),
    (255, 159, 45, 255),
    (35, 108, 147, 255),
    (91, 169, 193, 255),
    (25, 33, 40, 255),
    (255, 239, 184, 255),
    (67, 78, 85, 255),
]


def window_front(g, x0, x1, y, z0, z1, columns):
    """Deep framed, opaque polar glazing with a consistent reflected strip."""
    g.roundbox((x0, y, z0), (x1, y + 6, z1), 3, DARK)
    g.box((x0 + 3, y, z0 + 3), (x1 - 3, y + 2, z1 - 3), GLASS)
    g.box((x0 + 4, y, z1 - 7), (x1 - 4, y + 1, z1 - 4), SKY)
    for x in np.linspace(x0 + 3, x1 - 3, columns + 1)[1:-1]:
        p = int(round(x))
        g.box((p - 1, y - 1, z0 + 2), (p + 2, y + 3, z1 - 2), NAVY)
    g.box((x0 + 3, y - 1, z0 + 1), (x1 - 3, y + 2, z0 + 3), STEEL)


def louver_front(g, lo, hi, spacing=4):
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    g.box(lo, hi, DARK)
    for z in range(z0 + 2, z1 - 1, spacing):
        g.box((x0 + 2, y0 - 1, z), (x1 - 2, y0 + 1, z + 2), STEEL)


def foot(g, x, y, z=0, width=15, depth=13):
    g.roundbox((x - width / 2, y - depth / 2, z), (x + width / 2, y + depth / 2, z + 5), 2, DARK)
    g.box((x - width / 2 + 2, y - depth / 2 + 2, z + 4), (x + width / 2 - 2, y + depth / 2 - 2, z + 7), STEEL)
    g.box((x - 4, y - 4, z + 7), (x + 4, y + 4, z + 10), ORANGE)


def research_station():
    g = Grid((128, 100, 100), PALETTE)
    # Six independent load-spreading pads with visible telescopic columns.
    for x in (22, 64, 106):
        for y in (38, 75):
            foot(g, x, y, 1, 19, 16)
            g.cylinder((x, y, 19), 3.4, 22, 2, SILVER)
            g.box((x - 5, y - 5, 23), (x + 5, y + 5, 33), DARK)
            g.box((x - 6, y - 6, 27), (x + 6, y + 6, 32), NAVY)
            g.box((x - 2, y - 7, 26), (x + 2, y - 5, 30), ORANGE)
    for x in (22, 106):
        g.beam((x, 39, 23), (x, 51, 34), 2.2, STEEL)
        g.beam((x, 74, 23), (x, 63, 34), 2.2, STEEL)
    g.roundbox((6, 25, 30), (122, 88, 40), 6, DARK)
    g.roundbox((5, 24, 34), (123, 89, 77), 11, IVORY)
    x, y, z = g.x, g.y, g.z
    g.data[(g.data != 0) & (z >= 34) & (z < 39)] = NAVY
    # Crown is gently stepped rather than bevel-smoothed.
    g.roundbox((10, 28, 71), (118, 85, 81), 7, SNOW)
    for px in (34, 61, 88):
        # Panel joints follow the existing occupied shell; no arbitrary noise.
        mask = (g.data == SNOW) & (x >= px) & (x < px + 1) & (z >= 75)
        g.data[mask] = SHADOW
    window_front(g, 12, 82, 23, 44, 68, 5)
    # Side glazing and smaller aft observation windows.
    g.roundbox((4, 38, 45), (10, 73, 66), 3, DARK)
    g.box((4, 41, 48), (6, 70, 63), GLASS)
    g.box((4, 42, 59), (5, 69, 62), SKY)
    for py in (51, 62):
        g.box((3, py, 47), (7, py + 2, 64), NAVY)
    g.roundbox((21, 85, 48), (67, 90, 66), 3, NAVY)
    g.box((24, 88, 51), (64, 90, 63), GLASS)
    for px in (36, 51):
        g.box((px, 88, 50), (px + 2, 91, 64), NAVY)
    # Recessed orange airlock is the service focal point.
    g.roundbox((89, 22, 38), (113, 31, 69), 4, SHADOW)
    g.roundbox((92, 21, 39), (110, 26, 66), 3, ORANGE)
    g.roundbox((98, 20, 52), (106, 23, 62), 2, DARK)
    g.box((100, 20, 54), (104, 21, 60), GLASS)
    g.box((94, 19, 45), (97, 22, 49), STEEL)
    for pz in (44, 59):
        g.box((109, 20, pz), (112, 25, pz + 3), STEEL)
    g.box((91, 19, 69), (111, 25, 72), NAVY)
    g.box((96, 18, 69), (105, 20, 71), LAMP)
    # Eight solid stepped treads and rounded safety rails are attached to sill.
    for i in range(8):
        zz = 4 + i * 4
        yy = 1 + i * 3
        g.box((89, yy, zz), (114, yy + 5, zz + 4), DARK)
        g.box((90, yy, zz + 3), (113, yy + 4, zz + 4), SILVER)
        for xx in range(92, 113, 5):
            g.box((xx, yy, zz + 3), (xx + 2, yy + 2, zz + 4), SLATE)
    g.box((88, 23, 34), (115, 30, 38), STEEL)
    for xx in (87, 116):
        g.beam((xx, 3, 17), (xx, 26, 46), 1.8, ORANGE)
        for yy, zz in ((4, 6), (15, 21), (25, 35)):
            g.beam((xx, yy, zz), (xx, yy, zz + 13), 1.8, ORANGE)
        g.beam((xx, 25, 47), (xx, 31, 47), 1.8, ORANGE)
    # Aft technical bay, horizontal louvers, access bolts and cable route.
    g.roundbox((82, 85, 41), (116, 97, 65), 4, IVORY)
    g.box((87, 95, 47), (104, 98, 60), DARK)
    for pz in (49, 53, 57):
        g.box((89, 97, pz), (102, 99, pz + 2), STEEL)
    g.box((109, 95, 45), (114, 98, 61), BLUE)
    g.beam((79, 89, 44), (79, 93, 68), 2, DARK)
    g.beam((79, 93, 68), (92, 93, 68), 2, DARK)
    # Right-side replaceable heat exchanger and adjacent utility access hatch.
    g.roundbox((120, 43, 44), (127, 78, 68), 3, SHADOW)
    g.box((125, 48, 48), (128, 63, 64), DARK)
    for pz in (50, 54, 58, 62):
        g.box((127, 49, pz), (128, 62, pz + 2), STEEL)
    g.roundbox((125, 66, 49), (128, 75, 64), 1.5, IVORY)
    g.box((127, 67, 54), (128, 70, 59), NAVY)
    g.box((127, 72, 52), (128, 74, 55), ORANGE)
    g.beam((123, 80, 42), (123, 80, 69), 1.7, NAVY)
    for px in (17, 46, 76):
        g.box((px, 22, 39), (px + 6, 25, 42), BLUE)
    for px in (12, 116):
        g.roundbox((px, 28, 43), (px + 5, 31, 49), 1, DARK)
        g.box((px + 1, 27, 44), (px + 4, 29, 48), AMBER)
    # Roof instruments: two vent cassettes, guarded duct, mast and beacon.
    for lo, hi in (((24, 53, 80), (48, 71, 88)), ((78, 56, 80), (98, 74, 88))):
        g.roundbox(lo, hi, 2, NAVY)
        for px in range(lo[0] + 3, hi[0] - 2, 4):
            g.box((px, lo[1] + 2, hi[2] - 1), (px + 2, hi[1] - 2, hi[2] + 1), STEEL)
    g.cylinder((62, 62, 84), 9, 8, 2, SHADOW)
    g.cone((62, 62, 90), 9, 6, 4, 2, SNOW)
    for yy in (48, 77):
        g.beam((22, yy, 88), (102, yy, 88), 1.5, STEEL)
        for xx in (23, 62, 101):
            g.beam((xx, yy, 80), (xx, yy, 88), 1.6, DARK)
    g.cylinder((33, 58, 91), 2, 14, 2, STEEL)
    g.cylinder((33, 58, 97), 2.8, 4, 2, ORANGE)
    g.cylinder((93, 66, 92), 1.6, 14, 2, DARK)
    return Asset("research_station", "Six-leg polar research station", g, 0.065, notes={
        "design": "Rounded insulated habitat, six telescopic legs, five-bay window band, airlock and eight-tread stair, side heat exchanger, aft service bay and roof HVAC.",
        "half_resolution_strategy": "Structural diameter >= 3.2 large voxels; stair risers and window mullions intentionally coarse. No manual half corrections.",
        "front": "-Y",
    })


def snowcat():
    g = Grid((104, 128, 84), PALETTE)
    x, y, z = g.x, g.y, g.z
    # Two actual hollow capsule-section track belts, with inset individual wheels.
    dy = np.maximum(np.maximum(35 - y, y - 108), 0)
    radial = np.sqrt(dy * dy + (z - 20) ** 2)
    for xl, xr in ((6, 27), (77, 98)):
        side = (x >= xl) & (x < xr)
        g.data[side & (radial <= 15) & (radial >= 9)] = DARK
        for yy in (35, 53, 71, 89, 108):
            g.cylinder(((xl + xr) / 2, yy, 20), 8.6, xr - xl - 2, 0, STEEL)
            for xx in (xl, xr - 2):
                g.cylinder((xx + 1, yy, 20), 5.3, 2, 0, DARK)
                g.cylinder((xx + 1, yy, 20), 2.8, 3, 0, ORANGE)
                g.cylinder((xx + 1, yy, 20), 1.1, 4, 0, SILVER)
        # Raised transverse tread bars continue around the end arcs.
        for yy in range(35, 109, 7):
            g.box((xl - 1, yy, 4), (xr + 1, yy + 3, 7), SLATE)
            g.box((xl - 1, yy, 33), (xr + 1, yy + 3, 36), SLATE)
        for yy, zz in ((24, 10), (21, 17), (22, 25), (27, 31), (115, 8), (120, 15), (120, 23), (116, 30)):
            g.box((xl - 1, yy, zz), (xr + 1, yy + 3, zz + 4), SLATE)
        g.box((xl + 2, 38, 28), (xr - 2, 105, 32), BLUE)
    g.roundbox((21, 28, 27), (83, 122, 40), 5, DARK)
    g.box((19, 78, 36), (85, 122, 42), IVORY)
    g.box((21, 79, 42), (83, 120, 44), STEEL)
    # Cab has a soft roof, deep front windscreen and independently framed side glass.
    g.roundbox((18, 31, 35), (86, 80, 73), 6, IVORY)
    g.roundbox((22, 35, 69), (82, 76, 78), 5, SNOW)
    g.box((20, 31, 37), (84, 35, 43), NAVY)
    slope = 30.5 + (z - 43) * 0.15
    # Cut the insulated shell back to the raked glazing surface. Without this
    # opening the higher glazing voxels sit behind the original rounded wall.
    opening = (x >= 24) & (x < 80) & (z >= 44) & (z < 69) & (y >= 28) & (y < slope)
    g.data[opening] = EMPTY
    front = (x >= 24) & (x < 80) & (z >= 44) & (z < 69) & (y >= slope) & (y < slope + 4)
    g.data[front] = DARK
    glass = (x >= 27) & (x < 77) & (z >= 47) & (z < 66) & (y >= slope - 0.6) & (y < slope + 1.3)
    g.data[glass] = GLASS
    g.data[glass & (z >= 61) & (x < 48)] = SKY
    g.data[(x >= 50) & (x < 54) & (z >= 46) & (z < 68) & (y >= slope - 1) & (y < slope + 2)] = NAVY
    g.beam((29, 31, 48), (42, 33, 58), 1.4, DARK)
    g.beam((57, 31, 48), (70, 33, 58), 1.4, DARK)
    for xx in (17, 84):
        g.roundbox((xx, 43, 47), (xx + 3, 73, 68), 2, DARK)
        g.box((xx - 1, 46, 50), (xx + 4, 69, 65), GLASS)
        g.box((xx - 1, 47, 61), (xx + 4, 57, 64), SKY)
        g.box((xx - 2, 60, 42), (xx + 4, 68, 45), ORANGE)
        g.box((xx - 3, 55, 32), (xx + 5, 72, 36), STEEL)
        g.box((xx - 2, 67, 49), (xx + 4, 70, 67), NAVY)
    for xx in (16, 88):
        g.beam((xx, 43, 56), (xx, 31, 59), 1.8, DARK)
        g.roundbox((xx - 3, 29, 55), (xx + 3, 34, 65), 2, DARK)
        g.box((xx - 2, 28, 57), (xx + 2, 30, 63), SILVER)
    for xx in (25, 69):
        g.roundbox((xx, 29, 69), (xx + 10, 36, 76), 2, DARK)
        g.box((xx + 2, 28, 71), (xx + 8, 30, 74), LAMP)
        g.roundbox((xx - 6, 27, 39), (xx + 1, 33, 46), 1.5, ORANGE)
        g.box((xx - 5, 26, 41), (xx, 28, 45), LAMP)
    g.box((38, 30, 38), (66, 33, 43), STEEL)
    g.roundbox((38, 48, 77), (65, 66, 82), 2, SLATE)
    for xx in range(42, 64, 5):
        g.box((xx, 50, 81), (xx + 2, 64, 83), DARK)
    g.cylinder((74, 67, 79), 2.8, 6, 2, ORANGE)
    # Blade is genuinely curved in profile with thick blunt ends and five ribs.
    blade_y = 6.0 + ((z - 14.0) ** 2) / 135.0
    blade = (x >= 5) & (x < 99) & (z >= 6) & (z < 34) & (y >= blade_y) & (y < blade_y + 5)
    g.data[blade] = STEEL
    g.data[blade & (z < 10)] = SILVER
    for xx in (6, 96):
        g.box((xx, 8, 7), (xx + 3, 17, 34), DARK)
        g.box((xx, 15, 12), (xx + 3, 18, 22), ORANGE)
    for xx in (24, 42, 60, 78):
        rib = blade & (x >= xx) & (x < xx + 2) & (y >= blade_y + 3)
        g.data[rib] = SLATE
    for xx in (30, 74):
        g.beam((xx, 10, 14), (xx, 38, 28), 3, NAVY)
        g.beam((xx, 11, 26), (xx, 38, 32), 1.8, SILVER)
    # Cargo bed holds a generator box and a closed blue spare-parts cassette.
    g.roundbox((32, 85, 44), (66, 111, 64), 3, ORANGE)
    g.box((35, 88, 62), (63, 108, 66), AMBER)
    for xx in (36, 59):
        g.box((xx, 85, 45), (xx + 3, 112, 66), DARK)
    g.box((43, 84, 51), (55, 87, 58), STEEL)
    g.box((46, 83, 53), (52, 86, 56), DARK)
    g.roundbox((69, 84, 44), (83, 108, 58), 2, BLUE)
    g.box((69, 83, 49), (84, 86, 52), STEEL)
    for xx in (19, 85):
        for yy in (82, 103, 119):
            g.beam((xx, yy, 42), (xx, yy, 56), 1.6, STEEL)
        g.beam((xx, 82, 56), (xx, 120, 56), 1.6, STEEL)
    g.beam((20, 120, 56), (84, 120, 56), 1.6, STEEL)
    for xx in (25, 78):
        g.beam((xx, 115, 43), (xx, 115, 72), 2.6, DARK)
    g.beam((25, 115, 72), (78, 115, 72), 2.6, DARK)
    g.box((27, 121, 37), (37, 124, 41), ORANGE)
    g.box((67, 121, 37), (77, 124, 41), ORANGE)
    g.beam((46, 122, 31), (58, 122, 31), 2.5, STEEL)
    g.box((39, 78, 51), (63, 82, 67), DARK)
    for pz in (54, 58, 62):
        g.box((42, 81, pz), (60, 83, pz + 2), STEEL)
    return Asset("snowcat", "Tracked Antarctic utility snowcat", g, 0.045, notes={
        "design": "Two separated capsule track belts with road wheels and treads, blunt curved snow blade, glazed cab, cargo generator and rear protective hoop.",
        "half_resolution_strategy": "Track shell is six voxels thick, blade five voxels, road-wheel hubs and load-bearing bars retained by conservative reduction. No manual half corrections.",
        "front": "-Y",
    })


def radar():
    g = Grid((112, 112, 128), PALETTE)
    for xx in (17, 95):
        for yy in (23, 90):
            foot(g, xx, yy, 0, 20, 18)
            g.box((xx - 5, yy - 5, 9), (xx + 5, yy + 5, 18), DARK)
            g.beam((xx, yy, 15), (30 if xx < 56 else 82, 36 if yy < 56 else 77, 23), 4, STEEL)
    g.roundbox((22, 27, 15), (90, 87, 37), 5, NAVY)
    g.roundbox((24, 29, 21), (88, 85, 41), 4, IVORY)
    g.box((24, 31, 18), (88, 83, 23), BLUE)
    louver_front(g, (44, 27, 25), (67, 30, 37), 4)
    for xx in (27, 79):
        g.box((xx, 27, 27), (xx + 7, 31, 37), NAVY)
        g.box((xx + 1, 26, 32), (xx + 6, 29, 36), LAMP)
    for xx in (23, 86):
        g.box((xx, 47, 26), (xx + 3, 66, 37), DARK)
        for yy in (49, 54, 59, 64):
            g.box((xx - 1, yy, 28), (xx + 4, yy + 2, 35), STEEL)
    g.roundbox((42, 83, 25), (69, 88, 38), 2, SHADOW)
    g.box((63, 87, 29), (66, 90, 34), ORANGE)
    g.cylinder((56, 60, 42), 23, 5, 2, STEEL)
    g.cylinder((56, 60, 46), 19, 5, 2, NAVY)
    g.cylinder((56, 60, 49), 15, 4, 2, DARK)
    # Bearing cradle and U-yoke remain structurally connected behind the bowl.
    g.beam((22, 69, 49), (90, 69, 49), 5, BLUE)
    for xx in (22, 90):
        g.beam((xx, 69, 48), (xx, 65, 79), 5, NAVY)
        g.cylinder((xx, 65, 78), 10, 10, 0, BLUE)
        g.cylinder((xx - 1 if xx < 56 else xx + 1, 65, 78), 6, 12, 0, ORANGE)
        g.cylinder((xx - 2 if xx < 56 else xx + 2, 65, 78), 3, 13, 0, DARK)
    g.cylinder((56, 65, 78), 5.5, 69, 0, STEEL)
    g.beam((56, 82, 46), (56, 79, 86), 3.2, DARK)
    g.beam((56, 80, 61), (56, 79, 88), 1.8, SILVER)
    # Concave paraboloid, four-voxel thick wall. Its interior is open air.
    center = np.array((56.0, 59.0, 81.0))
    normal = np.array((0.0, -0.78, 0.6257795))
    normal /= np.linalg.norm(normal)
    vertical = np.array((0.0, normal[2], -normal[1]))
    dx = g.x - center[0]
    dy = g.y - center[1]
    dz = g.z - center[2]
    depth = dy * normal[1] + dz * normal[2]
    vv = dy * vertical[1] + dz * vertical[2]
    rr = dx * dx + vv * vv
    sag = rr * 0.0064
    shell = (rr <= 45 ** 2) & (depth >= sag - 4.2) & (depth <= sag + 0.8)
    g.data[shell] = IVORY
    g.data[shell & (depth < sag - 2.0)] = SHADOW
    g.data[shell & (rr >= 41.5 ** 2)] = SNOW
    # Deliberate concentric inner construction seam, gentle in color.
    g.data[shell & (rr >= 29.2 ** 2) & (rr < 30.2 ** 2) & (depth >= sag - 1.3)] = SHADOW
    for angle in (0, 60, 120, 180, 240, 300):
        a = math.radians(angle)
        end = center + np.array((math.cos(a), 0, 0)) * 40 + vertical * (math.sin(a) * 40) + normal * (40 ** 2 * 0.0064 - 5)
        start = center - normal * 5
        g.beam(tuple(start), tuple(end), 1.8, NAVY)
    # Feed and tripod arms are in front of, not painted onto, the open surface.
    focus = center + normal * 34
    g.beam(tuple(center + normal * 2), tuple(focus), 3.0, BLUE)
    g.ellipsoid(tuple(focus), (5.3, 5.2, 5.2), IVORY)
    g.ellipsoid(tuple(focus + normal * 3.5), (3.2, 3.2, 3.2), ORANGE)
    for angle in (90, 210, 330):
        a = math.radians(angle)
        radial = np.array((math.cos(a) * 39, 0, 0)) + vertical * (math.sin(a) * 39)
        rim = center + radial + normal * (39 ** 2 * 0.0064 + 1)
        g.beam(tuple(rim), tuple(focus - normal * 2), 1.65, DARK)
    # Rear power umbilical, retained as geometry in reverse views.
    for a, b in (((76, 84, 29), (76, 94, 29)), ((76, 94, 29), (76, 94, 52)), ((76, 94, 52), (68, 82, 63))):
        g.beam(a, b, 2, DARK)
    return Asset("radar", "Open polar radar antenna", g, 0.04, notes={
        "design": "Tilted concave paraboloid with real five-voxel open shell, three feed supports, rear ribs, bearing yoke and four-foot electronics pedestal.",
        "half_resolution_strategy": "Dish wall and yoke thickness preserve cavity and concavity at 64-cell longest axis; support capsules have diameter >= 3.3 voxels. No manual half corrections.",
        "front": "-Y; dish normal tilts upward approximately 39 degrees",
    })


def weather_instrument():
    g = Grid((80, 80, 128), PALETTE)
    for xx in (14, 66):
        for yy in (14, 66):
            foot(g, xx, yy, 0, 18, 16)
            g.box((xx - 4, yy - 4, 9), (xx + 4, yy + 4, 15), DARK)
    for a, b in (((14, 14, 12), (66, 14, 12)), ((66, 14, 12), (66, 66, 12)), ((66, 66, 12), (14, 66, 12)), ((14, 66, 12), (14, 14, 12))):
        g.beam(a, b, 2.6, SILVER)
    for a in ((14, 14, 12), (66, 14, 12), (66, 66, 12), (14, 66, 12)):
        g.beam(a, (40, 40, 15), 2.4, STEEL)
    g.cylinder((40, 40, 24), 5.5, 25, 2, IVORY)
    g.cylinder((40, 40, 65), 3.6, 92, 2, IVORY)
    for zz in (17, 28, 57, 90, 105):
        g.cylinder((40, 40, zz), 5.2, 4, 2, NAVY)
    # Weatherproof logger cabinet with recessed vent, two latches and cable gland.
    g.roundbox((25, 25, 29), (47, 44, 61), 3, SHADOW)
    g.roundbox((26, 23, 30), (46, 29, 60), 2, IVORY)
    louver_front(g, (30, 22, 46), (40, 25, 55), 3)
    for zz in (34, 54):
        g.box((44, 22, zz), (49, 28, zz + 5), ORANGE)
        g.box((46, 21, zz + 1), (48, 24, zz + 4), DARK)
    for xx in (28, 42):
        for zz in (33, 57):
            g.box((xx, 22, zz), (xx + 2, 24, zz + 2), SILVER)
    g.cylinder((38, 42, 27), 3, 6, 2, DARK)
    for a, b in (((48, 41, 32), (52, 41, 32)), ((52, 41, 32), (52, 42, 54)), ((52, 42, 54), (44, 42, 60))):
        g.beam(a, b, 1.8, DARK)
    # Tilted solar panel, stepped frame, blue cells and discrete bus lines.
    normal = np.array((0.0, -0.835, 0.5502045))
    normal /= np.linalg.norm(normal)
    tangent = np.array((0.0, normal[2], -normal[1]))
    panel_center = np.array((62.0, 35.0, 76.0))
    u = g.x - panel_center[0]
    dy = g.y - panel_center[1]
    dz = g.z - panel_center[2]
    v = dy * tangent[1] + dz * tangent[2]
    n = dy * normal[1] + dz * normal[2]
    panel = (np.abs(u) <= 15) & (np.abs(v) <= 20) & (np.abs(n) <= 2.7)
    g.data[panel] = IVORY
    cells = panel & (np.abs(u) < 12.5) & (np.abs(v) < 17.5) & (n >= 1.0)
    g.data[cells] = BLUE
    for xx in (-6, 0, 6):
        g.data[cells & (np.abs(u - xx) < 0.65)] = SILVER
    for yy in (-10.5, -3.5, 3.5, 10.5):
        g.data[cells & (np.abs(v - yy) < 0.65)] = SILVER
    g.data[panel & (n < -1.5)] = STEEL
    g.beam((41, 42, 73), (61, 40, 73), 2.5, NAVY)
    g.beam((42, 43, 66), (60, 43, 77), 2.0, STEEL)
    # Radiation shield has open air slots between seven rounded plates.
    g.beam((40, 38, 72), (21, 31, 72), 2.3, NAVY)
    g.cylinder((21, 31, 80), 3.2, 24, 2, NAVY)
    for zz in (71, 75, 79, 83, 87, 91):
        g.cylinder((21, 31, zz), 8.3, 2.0, 2, IVORY)
        g.cone((21, 31, zz + 1), 8.3, 6.7, 2.0, 2, SNOW)
    g.cone((21, 31, 94), 8.5, 6.0, 3, 2, SNOW)
    g.beam((21, 31, 69), (21, 33, 65), 1.8, DARK)
    g.beam((21, 33, 65), (29, 37, 62), 1.8, DARK)
    g.beam((21, 31, 73), (11, 31, 73), 1.7, STEEL)
    g.cylinder((11, 31, 82), 1.6, 25, 2, DARK)
    g.cylinder((11, 31, 96), 1.0, 10, 2, SILVER)
    # Functional wind vane below the anemometer: tail fin and pointed counterweight.
    g.beam((17, 40, 104), (68, 40, 104), 1.7, STEEL)
    fin = (g.x >= 57) & (g.x < 74) & (np.abs(g.y - 40) <= 2) & (np.abs(g.z - 104) <= 3 + (g.x - 57) * 0.31)
    g.data[fin] = BLUE
    arrow = (g.x >= 13) & (g.x < 23) & (np.abs(g.y - 40) <= 2) & (np.abs(g.z - 104) <= (g.x - 13) * 0.45 + 0.7)
    g.data[arrow] = ORANGE
    g.cylinder((40, 40, 106), 4, 5, 2, NAVY)
    # Three genuinely hollow cup sensors, tangential to their rotor.
    g.cylinder((40, 40, 115), 2.8, 13, 2, DARK)
    g.ellipsoid((40, 40, 119), (4, 4, 4), STEEL)
    for angle in (-90, 30, 150):
        a = math.radians(angle)
        c = np.array((40 + 19 * math.cos(a), 40 + 19 * math.sin(a), 119.0))
        axis = np.array((-math.sin(a), math.cos(a), 0))
        g.beam((40, 40, 119), tuple(c), 1.55, STEEL)
        dx, dy, dz = g.x - c[0], g.y - c[1], g.z - c[2]
        r2 = dx * dx + dy * dy + dz * dz
        along = dx * axis[0] + dy * axis[1]
        cup = (r2 <= 6.4 ** 2) & (along <= 1.6)
        g.data[cup] = DARK
        cavity = (r2 < 3.9 ** 2) & (along > -3.2)
        g.data[cavity] = EMPTY
        lip = cup & (along > -0.4) & (r2 >= 4.7 ** 2)
        g.data[lip] = STEEL
    return Asset("weather_instrument", "Autonomous polar weather mast", g, 0.025, notes={
        "design": "Open outrigger base, sealed logger, tilted solar panel, stacked radiation shield, true hollow rotor cups, directional wind vane and service cables.",
        "half_resolution_strategy": "Cabinet, panel, mast and cups remain volumetric; small gaps and grid lines may simplify naturally. Cup wall >= 2.5 voxels. No manual half corrections.",
        "front": "-Y",
    })


def make_assets():
    """Return four fresh independent grids without reading or modifying files."""
    return [research_station(), snowcat(), radar(), weather_instrument()]


if __name__ == "__main__":
    run_theme(Path(__file__).resolve().parent, make_assets())
