"""Independent harbor models authored as occupied, colored voxel grids."""
from pathlib import Path
import math
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_tools'))
from voxelkit import Grid, Asset, run_theme

PALETTE = [
    (0, 0, 0, 0),
    (43, 48, 47, 255), (67, 76, 74, 255), (100, 111, 106, 255),
    (150, 158, 145, 255), (49, 112, 115, 255), (76, 141, 141, 255),
    (35, 81, 86, 255), (218, 214, 188, 255), (239, 232, 205, 255),
    (178, 77, 42, 255), (206, 103, 57, 255), (136, 56, 34, 255),
    (151, 112, 65, 255), (185, 142, 84, 255), (105, 79, 49, 255),
    (153, 154, 138, 255), (182, 181, 158, 255), (120, 127, 117, 255),
    (118, 163, 170, 255), (165, 193, 190, 255), (235, 170, 58, 255),
    (174, 155, 111, 255), (189, 195, 178, 255), (250, 223, 153, 255),
    (34, 39, 38, 255),
]
GRAPHITE, STEEL, METAL, METAL_L = 1, 2, 3, 4
TEAL, TEAL_L, TEAL_D, IVORY, IVORY_L = 5, 6, 7, 8, 9
BRICK, BRICK_L, BRICK_D = 10, 11, 12
WOOD, WOOD_L, WOOD_D = 13, 14, 15
STONE, STONE_L, MORTAR = 16, 17, 18
GLASS, GLASS_L, AMBER, ROPE, BOLT, LAMP, RUBBER = 19, 20, 21, 22, 23, 24, 25


def ring(g, cx, cy, z, radius, color, thickness=1.6, segments=24):
    points = [(cx + radius * math.cos(i * 2 * math.pi / segments),
               cy + radius * math.sin(i * 2 * math.pi / segments), z)
              for i in range(segments + 1)]
    for a, b in zip(points, points[1:]):
        g.beam(a, b, thickness, color)


def crate(g, lo, hi, paint=WOOD):
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    g.roundbox(lo, hi, 1, paint)
    for xx in (x0 + 2, x1 - 4):
        g.box((xx, y0, z0), (xx + 2, y1, z1), WOOD_L if paint == WOOD else TEAL_D)
    for zz in (z0 + 2, z1 - 4):
        g.box((x0, y0, zz), (x1, y0 + 2, zz + 2), WOOD_D)
        g.box((x0, y1 - 2, zz), (x1, y1, zz + 2), WOOD_D)
    g.beam((x0 + 1, y0 - 0.5, z0 + 2), (x1 - 1, y0 - 0.5, z1 - 2), 1.3, WOOD_L)


def bollard(g, x, y, z, color=GRAPHITE):
    g.cylinder((x, y, z + 3), 2.5, 6, 2, color)
    g.box((x - 4, y - 3, z + 5), (x + 4, y + 3, z + 8), color)
    g.box((x - 4, y - 4, z), (x + 4, y + 4, z + 2), METAL)


def boat_width(y):
    return 31 * np.sqrt(np.clip((y - 2) / 37, 0, 1)) - np.maximum(y - 111, 0) * 0.32


def fishing_boat():
    g = Grid((80, 128, 108), PALETTE)
    width = np.maximum(boat_width(g.y), 0.2)
    xx = np.abs(g.x - 40)
    bottom = 3 + 4 * ((g.y - 71) / 68) ** 2 + 17 * (xx / width) ** 2
    top = 38 + np.clip((41 - g.y) / 39, 0, 1) * 3
    hull = (g.y >= 3) & (g.y < 126) & (xx <= width) & (g.z >= bottom) & (g.z <= top)
    g.data[hull] = TEAL
    g.data[hull & (g.z < 15)] = BRICK
    g.data[hull & (g.z < 9)] = BRICK_D
    g.data[hull & (g.z >= 26) & (g.z < 28)] = IVORY
    g.data[hull & (np.mod(g.z, 7) < 1) & (g.z >= 16) & (g.z < 35)] = TEAL_D
    # Open deck is cut into the real hull; the cap follows the curved sheer.
    interior = (g.y >= 11) & (g.y < 121) & (xx < width - 4)
    g.data[interior & (g.z >= 34)] = 0
    g.data[interior & (g.z >= 31) & (g.z < 35)] = WOOD
    g.data[interior & (g.z >= 34) & (g.z < 35) & (np.mod(g.x, 6) < 1)] = WOOD_D
    g.data[hull & (g.z >= top - 4) & ~interior] = IVORY
    # Hull rubbing strips, hanging tire fenders and mooring stanchions.
    for yy in (34, 67, 99):
        ww = float(boat_width(yy))
        for sign in (-1, 1):
            xside = 40 + sign * (ww + 0.3)
            g.torus((xside, yy, 28), 4.4, 2.0, 0, RUBBER)
            g.beam((xside, yy, 34), (40 + sign * (ww - 1), yy, 41), 1.3, GRAPHITE)
    railing_y = (16, 29, 46, 69, 90, 111, 121)
    for sign in (-1, 1):
        pts = []
        for yy in railing_y:
            xside = 40 + sign * (float(boat_width(yy)) - 2)
            zz = 46 + max(0, (40 - yy) / 30)
            g.beam((xside, yy, 38), (xside, yy, zz), 1.6, WOOD_D)
            pts.append((xside, yy, zz))
        for a, b in zip(pts, pts[1:]):
            g.beam(a, b, 1.4, STEEL)
    bollard(g, 40, 15, 39)
    bollard(g, 19, 117, 37)
    bollard(g, 61, 117, 37)
    # Forward wheelhouse with visible front and side glazing, rear service door.
    g.roundbox((22, 29, 35), (58, 69, 64), 2, IVORY)
    for x0, x1 in ((25, 33), (36, 44), (47, 55)):
        g.box((x0, 27, 48), (x1, 31, 60), TEAL_D)
        g.box((x0 + 1, 26, 49), (x1 - 1, 29, 59), GLASS)
    for xx in (20, 57):
        for y0, y1 in ((34, 45), (49, 62)):
            g.box((xx, y0, 48), (xx + 3, y1, 61), TEAL_D)
            g.box((xx - 1, y0 + 1, 50), (xx + 4, y1 - 1, 60), GLASS)
    g.box((39, 67, 36), (54, 72, 62), TEAL_D)
    g.box((42, 70, 38), (51, 74, 60), IVORY)
    g.box((44, 73, 50), (49, 75, 58), GLASS)
    g.box((49, 74, 43), (52, 77, 47), METAL)
    g.roundbox((18, 25, 63), (62, 72, 70), 3, TEAL)
    g.box((23, 30, 70), (57, 68, 72), IVORY)
    for xx in (23, 57):
        g.beam((xx, 32, 71), (xx, 32, 77), 1.4, BRICK)
        g.beam((xx, 62, 71), (xx, 62, 77), 1.4, BRICK)
        g.beam((xx, 32, 77), (xx, 62, 77), 1.4, BRICK)
    g.beam((23, 32, 77), (57, 32, 77), 1.4, BRICK)
    g.cylinder((40, 47, 87), 1.8, 32, 2, IVORY)
    g.beam((30, 47, 90), (50, 47, 90), 1.7, IVORY)
    g.roundbox((33, 44, 98), (47, 50, 102), 1.5, IVORY_L)
    g.cylinder((40, 47, 104), 2.5, 4, 2, AMBER)
    g.cylinder((55, 61, 87), 1.4, 29, 2, GRAPHITE)
    g.cylinder((25, 60, 78), 3.5, 16, 2, GRAPHITE)
    g.cylinder((25, 60, 86), 4.5, 3, 2, STEEL)
    # A functional stern drum and lifting frame leave a clear working deck around them.
    for x0 in (24, 52):
        g.box((x0, 90, 35), (x0 + 5, 102, 48), STEEL)
    g.cylinder((40, 96, 47), 7.5, 24, 0, ROPE)
    for xx0 in range(29, 53, 3):
        g.cylinder((xx0, 96, 47), 8.1, 1.3, 0, WOOD_D)
    for xx0 in (26, 54):
        g.cylinder((xx0, 96, 47), 10, 3, 0, METAL)
        g.cylinder((xx0, 96, 47), 3.5, 5, 0, GRAPHITE)
    g.box((54, 88, 35), (62, 101, 42), TEAL_D)
    g.cylinder((60, 93, 42), 3, 5, 2, STEEL)
    for x0, x1 in ((20, 27), (60, 53)):
        g.beam((x0, 111, 35), (x1, 111, 77), 2.7, STEEL)
    g.beam((25, 111, 77), (55, 111, 77), 2.7, STEEL)
    g.beam((27, 111, 67), (53, 111, 77), 1.8, GRAPHITE)
    g.cylinder((40, 111, 75), 4, 6, 1, METAL)
    g.beam((40, 96, 54), (40, 109, 78), 1.3, ROPE)
    g.beam((40, 114, 76), (40, 117, 59), 1.4, GRAPHITE)
    g.roundbox((36, 114, 54), (44, 121, 62), 1.2, BRICK)
    g.torus((40, 117, 51), 3.5, 1.7, 1, GRAPHITE)
    crate(g, (13, 76, 35), (28, 89, 47), WOOD)
    crate(g, (53, 77, 35), (67, 89, 45), TEAL)
    g.torus((59, 54, 43), 4.5, 1.8, 0, BRICK_L)
    # Useful stern details include a boarding ladder, rudder and propeller assembly.
    for xx0 in (51, 61):
        g.beam((xx0, 125, 25), (xx0, 125, 43), 1.4, STEEL)
    for zz in (28, 34, 40):
        g.beam((51, 125, zz), (61, 125, zz), 1.4, METAL)
    g.box((38, 119, 6), (42, 128, 21), TEAL_D)
    g.cylinder((40, 121, 14), 3, 10, 1, METAL)
    for ang in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
        g.beam((40, 125, 14), (40 + 5 * math.cos(ang), 125, 14 + 5 * math.sin(ang)), 1.8, WOOD_L)
    return Asset('fishing_boat', 'Harbor working fishing boat', g, voxel_size=0.06, notes=[
        'Original curved occupied hull with an open timber deck, forward wheelhouse, stern winch and lifting frame, real fenders and mooring fittings.',
        'Rear working deck, boarding ladder, rudder and propeller are authored geometry. Glazing uses opaque flat palette colors.',
        'All ropes are static voxel beams; no sailing, water, rigging or machinery animation is included.'
    ])


def lighthouse():
    g = Grid((76, 76, 128), PALETTE)
    g.roundbox((7, 7, 0), (69, 69, 11), 6, MORTAR)
    g.cylinder((38, 38, 16), 26, 17, 2, STONE)
    # Planned masonry courses and radial joints, without random texturing.
    rr = np.sqrt((g.x - 38) ** 2 + (g.y - 38) ** 2)
    theta = np.arctan2(g.y - 38, g.x - 38)
    g.data[(rr <= 26.1) & (rr >= 24.8) & (g.z >= 8) & (g.z < 24) & (np.mod(g.z, 6) < 1)] = MORTAR
    joint = np.abs(np.sin(theta * 10 + np.floor(g.z / 6) * 0.6)) < 0.10
    g.data[(rr <= 26.1) & (rr >= 24.8) & (g.z >= 8) & (g.z < 24) & joint] = MORTAR
    g.cone((38, 38, 57), 22, 16, 70, 2, IVORY)
    radius = 22 - (g.z - 22) * 6 / 70
    wall = (g.z >= 22) & (g.z <= 92) & (rr <= radius) & (rr >= radius - 1)
    g.data[wall & (np.mod(g.z - 22, 7) < 1)] = STONE_L
    g.data[wall & (np.abs(np.sin(theta * 12 + np.floor(g.z / 7) * 0.45)) < 0.055)] = STONE_L
    band = (g.z >= 56) & (g.z < 70) & (rr <= radius + 0.3)
    g.data[band] = BRICK
    g.data[band & (np.mod(g.z, 6) < 1)] = BRICK_L
    g.cone((38, 38, 91), 17, 23, 7, 2, TEAL_D)
    g.cylinder((38, 38, 93), 24, 4, 2, BRICK)
    g.cylinder((38, 38, 95), 21.5, 2, 2, STONE_L)
    # Front access arch and three broad steps.
    g.roundbox((28, 9, 10), (48, 20, 38), 4.5, STONE_L)
    g.roundbox((31, 8, 11), (45, 16, 35), 3, TEAL_D)
    g.box((33, 7, 12), (43, 12, 31), TEAL)
    g.box((35, 6, 26), (41, 9, 31), GLASS)
    g.box((40, 5, 18), (43, 9, 22), AMBER)
    for y0, z0, width in ((0, 0, 30), (4, 3, 26), (8, 6, 22)):
        g.box((38 - width / 2, y0, z0), (38 + width / 2, 20, z0 + 4), STONE_L)
    for zz, yy in ((39, 15), (77, 18)):
        g.box((32, yy, zz), (44, yy + 7, zz + 16), STONE_L)
        g.box((35, yy - 1, zz + 3), (41, yy + 3, zz + 13), TEAL_D)
        g.box((36, yy - 2, zz + 4), (40, yy + 1, zz + 12), GLASS)
        g.box((31, yy - 2, zz + 14), (45, yy + 3, zz + 17), METAL)
    # The lantern is actual open framed construction with a separate central lamp.
    g.cylinder((38, 38, 97), 14.5, 4, 2, GRAPHITE)
    g.cylinder((38, 38, 108), 6.2, 17, 2, LAMP)
    for zz in (104, 108, 112, 116):
        g.cylinder((38, 38, zz), 6.8, 1.8, 2, AMBER)
    for angle in range(0, 360, 45):
        a = math.radians(angle)
        lx, ly = 38 + 13 * math.cos(a), 38 + 13 * math.sin(a)
        g.beam((lx, ly, 97), (lx, ly, 117), 1.5, STEEL)
        rx, ry = 38 + 22 * math.cos(a), 38 + 22 * math.sin(a)
        g.beam((rx, ry, 95), (rx, ry, 102), 1.4, STEEL)
    ring(g, 38, 38, 117, 13, STEEL, 1.7, 16)
    ring(g, 38, 38, 102, 22, GRAPHITE, 1.4, 24)
    ring(g, 38, 38, 98, 22, STEEL, 1.3, 24)
    g.cone((38, 38, 121), 19, 4.5, 12, 2, TEAL)
    for zz, rad in ((116, 19.2), (120, 14), (124, 9)):
        g.cylinder((38, 38, zz), rad, 2, 2, TEAL_L)
    g.cylinder((38, 38, 126), 3, 4, 2, GRAPHITE)
    # Rear ventilation, a recessed maintenance door and perimeter service bollards.
    g.roundbox((31, 57, 13), (45, 65, 32), 2, MORTAR)
    g.box((34, 63, 15), (42, 67, 29), TEAL_D)
    g.box((36, 66, 20), (40, 69, 24), METAL)
    g.box((33, 56, 39), (43, 61, 51), STEEL)
    for zz in (41, 45, 49):
        g.box((32, 60, zz), (44, 63, zz + 2), METAL)
    for xx, yy in ((12, 17), (64, 17), (12, 60), (64, 60)):
        bollard(g, xx, yy, 10, TEAL_D)
    return Asset('lighthouse', 'Lantern harbor lighthouse', g, voxel_size=0.075, notes=[
        'Stepped tapered masonry tower, brick identification band, front arch and stairs, gallery balustrade, separate eight-post lantern structure and central lamp.',
        'Lantern bays are deliberately open so the actual frame and lamp remain readable in both voxel sizes; no optical beam or glass transmission simulation is claimed.',
        'Rear service door and louvered vent are modeled. Static geometry only.'
    ])


def warehouse():
    g = Grid((128, 112, 96), PALETTE)
    # Building footing plus an attached timber loading platform with visible piers.
    g.box((12, 26, 0), (116, 101, 18), MORTAR)
    for x0 in range(12, 116, 13):
        g.box((x0 + 1, 25, 2), (x0 + 12, 30, 9), STONE)
        g.box((x0 + 1, 97, 2), (x0 + 12, 102, 9), STONE)
    g.box((3, 3, 14), (125, 30, 18), WOOD_D)
    g.box((114, 25, 14), (127, 104, 18), WOOD_D)
    for x0 in range(4, 125, 6):
        g.box((x0, 4, 17), (min(x0 + 5, 125), 29, 20), WOOD)
    for y0 in range(30, 104, 6):
        g.box((115, y0, 17), (127, min(y0 + 5, 104), 20), WOOD)
    for xx in (10, 34, 58, 82, 106, 121):
        g.box((xx - 3, 5, 1), (xx + 4, 12, 18), WOOD_D)
        g.box((xx - 4, 4, 0), (xx + 5, 13, 5), STEEL)
        g.box((xx - 4, 4, 12), (xx + 5, 13, 15), METAL)
    g.box((5, 7, 9), (124, 11, 14), WOOD_D)
    g.box((3, 2, 17), (125, 6, 21), STONE_L)
    # Broad corner columns, plank walls and a hollow cargo hall.
    g.box((15, 29, 18), (113, 97, 21), WOOD)
    g.box((14, 27, 19), (20, 99, 65), TEAL_D)
    g.box((108, 27, 19), (114, 99, 65), TEAL_D)
    g.box((14, 27, 19), (114, 33, 65), TEAL_D)
    g.box((14, 93, 19), (114, 99, 65), TEAL_D)
    for xx in range(16, 114, 6):
        g.box((xx, 26, 21), (min(xx + 4, 114), 33, 65), TEAL)
        g.box((xx, 93, 21), (min(xx + 4, 114), 100, 65), TEAL)
    for yy in range(29, 99, 6):
        g.box((13, yy, 21), (20, min(yy + 4, 99), 65), TEAL)
        g.box((108, yy, 21), (115, min(yy + 4, 99), 65), TEAL)
    for xx in (12, 109):
        for yy in (25, 94):
            g.box((xx, yy, 18), (xx + 7, yy + 7, 66), IVORY)
    g.box((12, 25, 59), (116, 33, 65), IVORY)
    g.box((108, 26, 59), (116, 100, 65), IVORY)
    # Barrel roof shell and matching curved gable panels, distinct from a flat block.
    arch = 65 + 25 * np.sqrt(np.clip(1 - ((g.x - 64) / 56) ** 2, 0, 1))
    gable = (g.x >= 14) & (g.x < 114) & (g.z >= 64) & (g.z < arch - 3)
    g.data[gable & (((g.y >= 27) & (g.y < 33)) | ((g.y >= 93) & (g.y < 99)))] = TEAL
    g.data[gable & (np.mod(g.x, 6) < 1.4) & (((g.y >= 26) & (g.y < 33)) | ((g.y >= 93) & (g.y < 100)))] = TEAL_D
    roof = (g.x >= 7) & (g.x < 121) & (g.y >= 21) & (g.y < 105) & (g.z >= arch - 4) & (g.z < arch + 1)
    g.data[roof] = STEEL
    g.data[roof & (np.mod(g.y, 12) < 1.5)] = GRAPHITE
    g.data[roof & (np.mod(g.x, 10) < 1.2)] = METAL
    g.data[roof & (((g.y >= 21) & (g.y < 25)) | ((g.y >= 101) & (g.y < 105)))] = TEAL_L
    for xx in (7, 117):
        g.box((xx, 22, 63), (xx + 4, 104, 68), TEAL)
    for yy in (43, 77):
        # Low-profile skylights mounted on the right shoulder of the curved roof.
        g.box((77, yy, 86), (91, yy + 13, 90), GRAPHITE)
        g.box((79, yy + 2, 89), (89, yy + 11, 92), GLASS)
        g.box((83, yy + 1, 90), (85, yy + 12, 93), METAL)
    for xx in (32, 100):
        g.cylinder((xx, 89, 85), 3.5, 12, 2, GRAPHITE)
        g.cylinder((xx, 89, 91), 5, 3, 2, METAL)
    # Open front sliding doors and rails, with a separate side cargo opening.
    g.box((31, 22, 20), (78, 35, 58), 0)
    for x0, x1 in ((16, 32), (78, 94)):
        g.box((x0, 21, 20), (x1, 26, 58), BRICK_D)
        for xx in range(x0 + 1, x1, 4):
            g.box((xx, 19, 21), (min(xx + 3, x1), 25, 57), BRICK)
        for zz in (25, 50):
            g.box((x0, 18, zz), (x1, 23, zz + 3), BRICK_L)
        g.box((x0 + 7, 17, 33), (x0 + 10, 22, 40), GRAPHITE)
    g.box((13, 19, 58), (97, 24, 62), STEEL)
    for xx in (20, 28, 82, 90):
        g.cylinder((xx, 21, 60), 2.5, 5, 1, GRAPHITE)
    g.box((106, 52, 20), (118, 80, 58), 0)
    for y0, y1 in ((37, 52), (80, 95)):
        g.box((112, y0, 20), (118, y1, 58), BRICK_D)
        for yy in range(y0 + 1, y1, 4):
            g.box((115, yy, 21), (120, min(yy + 3, y1), 57), BRICK)
        for zz in (25, 50):
            g.box((116, y0, zz), (121, y1, zz + 3), BRICK_L)
    g.box((115, 34, 58), (120, 98, 62), STEEL)
    # Real cargo remains clear of the two circulation openings.
    crate(g, (25, 46, 21), (43, 63, 39))
    crate(g, (27, 48, 39), (41, 61, 52), TEAL)
    crate(g, (77, 74, 21), (96, 91, 39))
    crate(g, (83, 45, 21), (99, 59, 34), TEAL)
    crate(g, (5, 9, 21), (21, 23, 34))
    # Task lights and upper front aperture are hardware, not painted decals.
    for xx in (28, 86):
        g.box((xx - 3, 19, 64), (xx + 3, 24, 70), GRAPHITE)
        g.box((xx - 2, 18, 65), (xx + 2, 21, 69), LAMP)
    g.box((57, 24, 72), (71, 29, 83), IVORY)
    g.box((61, 23, 74), (67, 27, 81), GLASS)
    # Back loading shutter and a personnel door, drainage and right-hand stairs.
    g.box((31, 97, 20), (62, 103, 53), IVORY)
    g.box((35, 101, 21), (58, 105, 50), STEEL)
    for zz in range(23, 50, 5):
        g.box((35, 104, zz), (58, 106, zz + 2), METAL)
    g.box((84, 97, 20), (102, 103, 52), IVORY)
    g.box((88, 102, 21), (98, 106, 49), TEAL_D)
    g.box((90, 105, 38), (96, 108, 47), GLASS)
    g.box((95, 105, 30), (99, 109, 34), METAL)
    for xx in (10, 118):
        g.cylinder((xx, 100, 41), 1.8, 50, 2, STEEL)
        g.beam((xx, 100, 17), (xx, 107, 14), 1.8, STEEL)
    for i in range(5):
        g.box((108, 2 + i * 4, i * 4), (127, 6 + i * 4, i * 4 + 4), STONE)
    bollard(g, 99, 9, 20)
    bollard(g, 121, 98, 20)
    return Asset('warehouse', 'Barrel-roof harbor warehouse', g, voxel_size=0.075, notes=[
        'Original hollow cargo hall with a curved barrel roof, skylights, open front and side sliding cargo doors, rails, interior cargo, attached loading deck and access stairs.',
        'Loading platform is part of the warehouse asset; it has actual support piers and no unrelated diorama floor.',
        'Rear loading shutter, personnel access and rain downpipes are visible geometry. Door and roof glass colors are opaque.'
    ])


def cargo_crane():
    g = Grid((100, 128, 128), PALETTE)
    # Four outward-splayed legs on individual masonry pads support the slew deck.
    for fx, fy, tx, ty in ((18, 76, 28, 83), (82, 76, 72, 83), (18, 116, 28, 109), (82, 116, 72, 109)):
        g.roundbox((fx - 8, fy - 8, 0), (fx + 8, fy + 8, 7), 1, STONE)
        g.box((fx - 5, fy - 5, 6), (fx + 5, fy + 5, 10), BRICK)
        g.beam((fx, fy, 9), (tx, ty, 36), 4.2, TEAL)
        g.box((tx - 5, ty - 5, 32), (tx + 5, ty + 5, 41), TEAL_D)
    for yy in (83, 109):
        g.beam((28, yy, 30), (72, yy, 30), 3, TEAL_D)
    for xx in (28, 72):
        g.beam((xx, 83, 28), (xx, 109, 28), 3, TEAL_D)
    g.roundbox((23, 77, 35), (77, 115, 42), 2, TEAL)
    g.box((25, 79, 40), (75, 113, 44), STONE_L)
    g.cylinder((50, 97, 46), 20, 7, 2, GRAPHITE)
    g.cylinder((50, 97, 49), 18, 3, 2, METAL)
    g.roundbox((22, 81, 50), (87, 120, 55), 2, GRAPHITE)
    # Cab, rear counterweight and machinery case all sit above the rotating deck.
    g.roundbox((59, 91, 55), (81, 115, 77), 2, BRICK)
    g.box((61, 88, 58), (79, 93, 74), IVORY)
    g.box((63, 87, 60), (77, 90, 72), GLASS)
    g.box((69, 86, 59), (72, 91, 73), IVORY)
    g.box((79, 93, 58), (84, 112, 74), IVORY)
    g.box((82, 96, 60), (85, 110, 72), GLASS)
    g.box((82, 102, 59), (86, 105, 73), IVORY)
    g.roundbox((57, 89, 76), (84, 117, 81), 2, TEAL)
    g.box((65, 96, 81), (75, 110, 83), TEAL_L)
    g.box((62, 114, 55), (77, 119, 75), BRICK_D)
    g.box((65, 117, 57), (74, 121, 73), BRICK)
    g.box((67, 120, 65), (72, 123, 71), GLASS)
    g.box((72, 120, 59), (76, 124, 63), METAL)
    g.roundbox((26, 105, 55), (51, 121, 70), 2, BRICK)
    for zz in (58, 63, 68):
        g.box((28, 120, zz), (49, 123, zz + 2), BRICK_D)
    g.box((20, 94, 55), (29, 108, 65), TEAL_D)
    for yy in (97, 102):
        g.box((19, yy, 57), (22, yy + 2, 63), GRAPHITE)
    # Large transverse winch and boom heel pivots.
    g.cylinder((41, 100, 67), 8, 17, 0, ROPE)
    for xx in range(33, 51, 3):
        g.cylinder((xx, 100, 67), 8.7, 1.3, 0, WOOD_D)
    for xx in (31, 51):
        g.cylinder((xx, 100, 67), 10, 3, 0, METAL)
        g.box((xx - 2, 95, 54), (xx + 3, 105, 64), STEEL)
    for xx in (41, 59):
        g.cylinder((xx, 84, 64), 7, 6, 0, BRICK)
        g.cylinder((xx, 84, 64), 3, 8, 0, METAL)
    # An open lattice boom has two truss sides and physical cross members.
    lower0, lower1 = np.array((50, 84, 63.0)), np.array((50, 13, 114.0))
    upper0, upper1 = np.array((50, 91, 73.0)), np.array((50, 20, 124.0))
    def pt(a, b, t, x):
        p = a + (b - a) * t
        return (x, float(p[1]), float(p[2]))
    for xx in (42, 58):
        g.beam(pt(lower0, lower1, 0, xx), pt(lower0, lower1, 1, xx), 2.7, TEAL)
        g.beam(pt(upper0, upper1, 0, xx), pt(upper0, upper1, 1, xx), 2.7, TEAL_L)
        for i in range(6):
            a, b = i / 6, (i + 1) / 6
            if i % 2 == 0:
                g.beam(pt(lower0, lower1, a, xx), pt(upper0, upper1, b, xx), 2.1, TEAL_D)
            else:
                g.beam(pt(upper0, upper1, a, xx), pt(lower0, lower1, b, xx), 2.1, TEAL_D)
    for t in (0, 0.25, 0.5, 0.75, 1):
        g.beam(pt(lower0, lower1, t, 42), pt(lower0, lower1, t, 58), 2.2, TEAL)
        g.beam(pt(upper0, upper1, t, 42), pt(upper0, upper1, t, 58), 2.2, TEAL)
    g.cylinder((50, 16, 119), 6.5, 21, 0, TEAL_D)
    g.cylinder((61, 16, 119), 4, 3, 0, METAL)
    g.cylinder((39, 16, 119), 4, 3, 0, METAL)
    g.beam((41, 100, 75), (50, 20, 125), 1.4, GRAPHITE)
    # Two thick suspension cables, orange sheave block and an open J hook.
    for xx in (47, 53):
        g.beam((xx, 13, 118), (xx, 13, 67), 1.5, GRAPHITE)
    g.roundbox((43, 8, 58), (57, 19, 70), 2, BRICK)
    g.cylinder((50, 7, 64), 3, 3, 1, METAL)
    g.torus((50, 13, 51), 6, 2.3, 1, GRAPHITE)
    g.box((50, 6, 52), (60, 21, 58), 0)
    g.beam((47, 13, 59), (45, 13, 55), 2.3, GRAPHITE)
    g.beam((56, 13, 48), (56, 13, 51), 2.0, GRAPHITE)
    # Access ladder and deck guard rails keep the supporting structure useful.
    for xx in (31, 42):
        g.beam((xx, 76, 4), (xx, 76, 45), 1.5, GRAPHITE)
    for zz in range(7, 45, 6):
        g.beam((31, 76, zz), (42, 76, zz), 1.6, METAL)
    for xx in (25, 75):
        for yy in (80, 111):
            g.beam((xx, yy, 42), (xx, yy, 50), 1.4, METAL)
        g.beam((xx, 80, 50), (xx, 111, 50), 1.4, GRAPHITE)
    g.beam((25, 112, 50), (75, 112, 50), 1.4, GRAPHITE)
    g.box((25, 79, 41), (31, 85, 46), BRICK)
    g.box((69, 79, 41), (75, 85, 46), BRICK)
    return Asset('cargo_crane', 'Four-leg harbor cargo crane', g, voxel_size=0.07, notes=[
        'Stout four-legged splayed base, circular slew bearing, glazed cab, rear counterweight and access door, real transverse winch, two-sided open lattice boom.',
        'Two suspension cables connect a separate orange sheave block to the boom tip; the hanging hook has an authored opening and is not a decal.',
        'Ladder, guard rails and mechanical details are deliberately thick for native half-resolution reduction. Static machinery only.'
    ])


def make_assets():
    return [fishing_boat(), lighthouse(), warehouse(), cargo_crane()]


if __name__ == '__main__':
    run_theme(Path(__file__).resolve().parent, make_assets())
