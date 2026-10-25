"""Original forestry colored-voxel assets. Pure native geometry, no imported meshes."""
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_tools'))
from voxelkit import Grid, Asset, run_theme

PALETTE = [
    (0, 0, 0, 0),
    (61, 103, 67),       # 1 forest paint
    (83, 128, 80),       # 2 sunlit green panels
    (34, 65, 47),        # 3 deep green trim
    (211, 158, 50),      # 4 ochre safety metal
    (242, 190, 75),      # 5 yellow raised edges
    (39, 44, 43),        # 6 rubber / black hose
    (57, 63, 59),        # 7 tread
    (66, 77, 78),        # 8 graphite chassis
    (120, 133, 133),     # 9 steel
    (178, 188, 180),     # 10 bright steel
    (106, 143, 152),     # 11 opaque glazing
    (150, 179, 184),     # 12 glazing highlight
    (243, 217, 153),     # 13 lamp
    (175, 121, 66),      # 14 timber beams
    (199, 145, 81),      # 15 timber light
    (110, 72, 44),       # 16 bark
    (137, 89, 50),       # 17 bark light
    (84, 56, 39),        # 18 bark fissures
    (216, 172, 105),     # 19 cut wood
    (179, 128, 67),      # 20 growth rings
    (149, 148, 130),     # 21 concrete feet
    (115, 113, 98),      # 22 concrete seam
]


def wheel(g, x, y, z, r=14, width=12):
    """Blunt stepped tyre, radial tread blocks and contrasting exposed hub."""
    g.cylinder((x, y, z), r, width - 4, 0, 6)
    g.cylinder((x, y, z), r - 1.5, width, 0, 6)
    radial = (g.y - y) ** 2 + (g.z - z) ** 2
    angular = np.floor((np.arctan2(g.z - z, g.y - y) + np.pi) * 14 / (2 * np.pi))
    tread = (np.abs(g.x - x) < width / 2 - 1) & (radial >= (r - 2.2) ** 2) & (radial <= r ** 2)
    g.data[tread & ((angular.astype(int) % 2) == 0)] = 7
    g.cylinder((x, y, z), r * .55, width + 1, 0, 4)
    g.cylinder((x, y, z), r * .35, width + 2, 0, 5)
    g.cylinder((x, y, z), r * .19, width + 3, 0, 8)


def log(g, center, radius, length, axis):
    """Native bark stripes and concentric cut-end grain, without textures."""
    g.cylinder(center, radius, length, axis, 16)
    coords = (g.x, g.y, g.z)
    q = [a - center[i] for i, a in enumerate(coords)]
    radial = sum(q[i] ** 2 for i in range(3) if i != axis)
    extent = np.abs(q[axis]) <= length / 2
    ring = (radial <= radius ** 2) & (radial > (radius - 2.1) ** 2) & extent
    across = [i for i in range(3) if i != axis]
    angle = np.arctan2(q[across[1]], q[across[0]])
    strip = np.floor((angle + np.pi) * 8 / (2 * np.pi)).astype(int)
    band = np.floor((coords[axis] + 2 * strip) / 9).astype(int)
    g.data[ring & ((strip + band) % 4 == 0)] = 17
    g.data[ring & ((strip * 2 + band) % 9 == 0)] = 18
    cap = extent & (np.abs(q[axis]) >= length / 2 - 2) & (radial <= (radius - 1.2) ** 2)
    g.data[cap] = 19
    rings = (((np.sqrt(radial) >= radius * .34) & (np.sqrt(radial) < radius * .48)) |
             ((np.sqrt(radial) >= radius * .68) & (np.sqrt(radial) < radius * .80)))
    g.data[cap & rings] = 20


def cab(g, lo, hi):
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    g.roundbox(lo, hi, 4, 1)
    g.roundbox((x0 + 2, y0 - 1, z0 + 7), (x1 - 2, y0 + 3, z1 - 4), 2, 4)
    g.roundbox((x0 + 5, y0 - 2, z0 + 10), (x1 - 5, y0 + 2, z1 - 7), 2, 11)
    g.box((x0 + 7, y0 - 2, z1 - 13), (x1 - 7, y0 + 1, z1 - 8), 12)
    g.roundbox((x1 - 3, y0 + 5, z0 + 8), (x1 + 1, y1 - 4, z1 - 5), 2, 4)
    g.roundbox((x1 - 2, y0 + 8, z0 + 11), (x1 + 2, y1 - 7, z1 - 8), 1.5, 11)
    g.box((x1 - 1, y0 + 10, z1 - 14), (x1 + 2, y1 - 9, z1 - 9), 12)
    g.box((x1, y0 + 7, z0 + 11), (x1 + 2, y0 + 10, z1 - 7), 3)
    g.roundbox((x0 - 2, y0 - 3, z1 - 3), (x1 + 3, y1 + 2, z1 + 3), 3, 2)
    g.box((x0 + 3, y0 - 4, z1 - 1), (x0 + 8, y0 - 2, z1 + 2), 13)
    g.box((x1 - 8, y0 - 4, z1 - 1), (x1 - 3, y0 - 2, z1 + 2), 13)
    g.box((x1 + 1, y1 - 8, z0 + 6), (x1 + 3, y1 - 3, z0 + 8), 8)


def logging_harvester():
    g = Grid((128, 96, 128), PALETTE)
    g.roundbox((22, 12, 25), (71, 84, 36), 4, 8)
    g.roundbox((27, 51, 34), (67, 85, 55), 5, 1)
    g.roundbox((30, 55, 51), (64, 80, 59), 3, 2)
    for y in range(58, 78, 5):
        g.box((66, y, 40), (69, y + 2, 51), 3)
    g.roundbox((23, 10, 29), (71, 18, 36), 2, 9)
    for x in (21, 72):
        for y in (25, 70):
            wheel(g, x, y, 16)
            g.roundbox((x - 7, y - 13, 29), (x + 7, y + 13, 35), 3, 1)
    cab(g, (29, 15, 36), (64, 45, 76))
    for z in (26, 31, 36):
        g.box((70, 39, z), (77, 48, z + 2), 9)
    g.cylinder((48, 58, 59), 13, 8, 2, 8)
    g.cylinder((48, 58, 64), 10, 4, 2, 4)
    # A folded articulated boom reaches the independent hanging head.
    a, b, c, d = (48, 58, 65), (58, 57, 116), (98, 31, 96), (108, 24, 79)
    g.beam(a, b, 6, 8).beam((49, 58, 70), (58, 57, 113), 4, 1)
    g.beam(b, c, 6, 3).beam((62, 54, 114), (95, 33, 97), 4.5, 2)
    g.beam(c, d, 4, 8)
    g.beam((42, 54, 68), (51, 52, 99), 3, 4)
    g.beam((51, 52, 99), (55, 52, 110), 1.6, 10)
    g.beam((63, 55, 118), (87, 39, 112), 2.5, 8)
    g.beam((87, 39, 112), (97, 31, 101), 1.7, 10)
    for center in (a, b, c):
        g.cylinder(center, 7, 12, 1, 8)
        g.cylinder((center[0], center[1] - 7, center[2]), 3, 3, 1, 9)
    for p, q in [((62, 60, 110), (65, 61, 85)), ((65, 61, 85), (86, 41, 76)), ((86, 41, 76), (103, 26, 80))]:
        g.beam(p, q, 1.7, 6)
    # Two roller pairs flank an unobstructed central feed throat.
    g.roundbox((91, 22, 33), (126, 32, 76), 3, 1)
    g.roundbox((92, 8, 31), (125, 31, 37), 2, 4)
    g.roundbox((92, 10, 70), (125, 32, 76), 2, 5)
    g.box((91, 13, 37), (96, 29, 70), 4)
    g.box((121, 13, 37), (126, 29, 70), 4)
    for x in (101, 116):
        for z in (44, 61):
            g.cylinder((x, 15, z), 6.2, 12, 1, 6)
            g.cylinder((x, 8, z), 4.2, 3, 1, 9)
            g.cylinder((x, 6, z), 2, 2, 1, 8)
            for dz in (-4, 0, 4):
                g.box((x - 5, 11, z + dz - 1), (x + 5, 20, z + dz + 1), 7)
    g.box((107, 6, 38), (110, 22, 68), 0)
    g.cylinder((108, 25, 78), 5, 8, 2, 8)
    g.roundbox((99, 22, 27), (120, 35, 34), 3, 3)
    return Asset('logging_harvester', 'Logging harvester', g, .05,
                 ['Four-wheel forest machine with folded hydraulic boom, hanging harvesting head, four feed rollers and open central feed throat.',
                  'Glazing is intentionally opaque palette material. Native conservative half reduction; no manual correction.'])


def timber_forwarder():
    g = Grid((80, 128, 120), PALETTE)
    g.roundbox((17, 8, 24), (64, 121, 34), 4, 8)
    g.roundbox((20, 8, 33), (60, 29, 44), 4, 1)
    g.box((22, 6, 33), (58, 10, 41), 3)
    for x in (26, 34, 42, 50):
        g.box((x, 5, 34), (x + 3, 8, 40), 8)
    g.roundbox((17, 4, 25), (64, 11, 31), 2, 9)
    for x in (13, 67):
        for y in (21, 45, 80, 108):
            wheel(g, x, y, 15, r=13, width=12)
    cab(g, (21, 17, 36), (59, 47, 76))
    g.roundbox((20, 12, 33), (61, 24, 40), 3, 2)
    for z in (27, 32, 37):
        g.box((62, 38, z), (72, 47, z + 2), 9)
    # Structural bunk, open slatted headboard and three pairs of retaining stakes.
    g.box((14, 54, 31), (67, 122, 37), 3)
    for y in (59, 88, 117):
        g.roundbox((10, y - 3, 33), (70, y + 3, 40), 2, 8)
    for x in (14, 26, 40, 54, 66):
        g.box((x - 2, 51, 35), (x + 2, 56, 88), 8)
    for z in (44, 64, 82):
        g.box((12, 51, z), (68, 56, z + 3), 9)
    for x, z in ((27, 47), (53, 47), (27, 66), (53, 66), (40, 83)):
        log(g, (x, 89, z), 9.2, 62, 1)
    for x in (13, 67):
        for y in (62, 89, 117):
            g.roundbox((x - 3, y - 3, 34), (x + 3, y + 3, 86), 1.5, 1)
            g.box((x - 3, y - 3, 79), (x + 3, y + 3, 87), 4)
            g.box((x - 4, y - 4, 36), (x + 4, y + 4, 42), 4)
    # Crane arcs above the bunk, leaving a genuine opening between the claws.
    g.cylinder((40, 51, 55), 10, 9, 2, 8)
    a, b, c = (40, 51, 57), (22, 64, 111), (40, 100, 112)
    g.beam(a, b, 5.5, 3).beam((39, 53, 63), (23, 64, 108), 3.5, 1)
    g.beam(b, c, 5, 8)
    g.beam((25, 67, 112), (37, 96, 113), 3, 1)
    g.beam((44, 55, 64), (32, 64, 99), 2.7, 4)
    g.beam((32, 64, 99), (26, 65, 110), 1.7, 10)
    for p in (a, b, c):
        g.cylinder(p, 6, 11, 0, 8)
        g.cylinder((p[0] + 6, p[1], p[2]), 2.8, 2, 0, 4)
    g.beam(c, (40, 105, 103), 3, 8)
    g.cylinder((40, 105, 102), 5, 7, 2, 4)
    g.beam((40, 105, 100), (29, 105, 98), 3, 5)
    g.beam((40, 105, 100), (51, 105, 98), 3, 5)
    for p, q in [((29, 105, 98), (25, 105, 89)), ((25, 105, 89), (32, 105, 83)),
                 ((51, 105, 98), (55, 105, 89)), ((55, 105, 89), (48, 105, 83))]:
        g.beam(p, q, 2.5, 4)
    return Asset('timber_forwarder', 'Timber forwarder', g, .05,
                 ['Eight-wheel forwarder with slatted headboard, six retaining stakes, five bark-and-end-grain logs, and elevated open grapple.',
                  'Loaded static pose; native conservative half reduction with no manual correction.'])


def sawmill():
    g = Grid((128, 128, 118), PALETTE)
    # Piers and frame: no common presentation slab.
    for x in (16, 100):
        for y in (48, 116):
            g.roundbox((x - 7, y - 7, 0), (x + 7, y + 7, 11), 1.5, 21)
            g.box((x - 4, y - 4, 9), (x + 4, y + 4, 81), 14)
            g.box((x - 3, y - 5, 11), (x + 2, y - 3, 79), 15)
    # Warm plank rear and left walls leave the front and right machinery bay open.
    g.box((12, 53, 11), (18, 116, 80), 14)
    g.box((18, 115, 11), (100, 121, 79), 14)
    for y in range(56, 115, 9):
        g.box((11, y, 12), (13, y + 2, 77), 15)
    for x in range(21, 99, 9):
        g.box((x, 114, 12), (x + 2, 116, 78), 15)
    g.box((12, 43, 77), (105, 53, 85), 15)
    g.box((12, 112, 77), (105, 122, 85), 15)
    for y in (48, 116):
        g.beam((17, y, 60), (36, y, 81), 2.5, 14)
        g.beam((99, y, 61), (82, y, 81), 2.5, 14)
        g.beam((16, y, 83), (57, y, 108), 3, 15)
        g.beam((57, y, 108), (102, y, 83), 3, 15)
        g.beam((57, y, 82), (57, y, 106), 2.5, 14)
    # Stepped rounded gable roof, thin enough to read as a roof at half resolution.
    roofz = 112 - .56 * np.abs(g.x - 58)
    roof = (g.x >= 5) & (g.x < 111) & (g.y >= 40) & (g.y < 126) & (g.z <= roofz) & (g.z >= roofz - 5)
    g.data[roof] = 1
    g.data[roof & (((np.floor(g.y).astype(int) - 40) // 9) % 4 == 0)] = 2
    g.roundbox((54, 40, 108), (62, 126, 115), 2, 3)
    # Narrow lumber shelter to the right is a genuine part of the building.
    for y in (72, 116):
        g.box((119, y - 3, 0), (127, y + 5, 7), 21)
        g.box((121, y - 1, 6), (125, y + 3, 54), 14)
    g.box((102, 115, 8), (124, 121, 54), 14)
    side_z = 66 - .40 * (g.x - 100)
    sidemask = (g.x >= 100) & (g.x < 128) & (g.y >= 66) & (g.y < 126) & (g.z <= side_z) & (g.z >= side_z - 4)
    g.data[sidemask] = 1
    g.data[sidemask & ((np.floor(g.y).astype(int) // 9) % 4 == 0)] = 2
    for z in range(8, 36, 6):
        g.box((104, 80, z), (120, 111, z + 4), 15)
        g.box((104, 79, z), (120, 81, z + 2), 19)
    # Feed table with exposed transverse rollers and a log entering the cutter.
    for x in (40, 87):
        g.roundbox((x - 3, 8, 18), (x + 3, 109, 26), 2, 1)
        for y in (15, 49, 99):
            g.box((x - 3, y - 3, 1), (x + 3, y + 3, 21), 8)
    for y in (14, 26, 38, 50, 62, 74, 86, 98):
        g.cylinder((63.5, y, 26), 3.5, 47, 0, 9)
        g.cylinder((87, y, 26), 4.2, 3, 0, 8)
    log(g, (62, 45, 38), 8.5, 57, 1)
    # Circular blade lies in the feeding direction (YZ), with native stepped teeth.
    radial = (g.y - 83) ** 2 + (g.z - 44) ** 2
    angle = np.arctan2(g.z - 44, g.y - 83)
    teeth = (np.floor((angle + np.pi) * 20 / (2 * np.pi)).astype(int) % 2 == 0)
    disc = (np.abs(g.x - 78.5) < 1.8) & ((radial <= 18 ** 2) | ((radial <= 21 ** 2) & teeth))
    g.data[disc] = 10
    g.cylinder((79, 83, 44), 5, 8, 0, 8)
    g.cylinder((84, 83, 44), 2.5, 3, 0, 9)
    g.roundbox((74, 61, 64), (86, 107, 69), 2, 1)
    for y in (61, 103):
        g.box((81, y, 24), (86, y + 4, 65), 4)
    g.roundbox((52, 92, 28), (73, 108, 48), 4, 3)
    g.box((47, 57, 29), (52, 62, 43), 4)
    g.box((49, 56, 38), (52, 58, 41), 13)
    return Asset('sawmill', 'Open timber sawmill', g, .05,
                 ['Open timber-framed portal, structural footings, gabled green roof and side lumber shelter.',
                  'Eight feed rollers, bark-covered input log, stepped toothed circular blade and safety posts remain native geometry.',
                  'Static demonstrative layout; no moving mechanism. No manual half correction.'])


def log_rack():
    g = Grid((128, 70, 104), PALETTE)
    # Two structural trestles, joined longitudinally; no diorama platform.
    for x in (24, 104):
        for y in (13, 57):
            g.roundbox((x - 9, y - 7, 0), (x + 9, y + 7, 7), 1.5, 21)
            g.box((x - 7, y - 7, 2), (x - 5, y + 7, 6), 22)
            g.roundbox((x - 4, y - 4, 6), (x + 4, y + 4, 97), 2, 1)
            g.box((x - 5, y - 5, 91), (x + 5, y + 5, 97), 2)
        g.roundbox((x - 5, 12, 7), (x + 5, 58, 14), 2, 3)
    for y in (13, 57):
        g.roundbox((20, y - 3, 9), (108, y + 3, 16), 2, 1)
    for z in (25, 52, 79):
        log(g, (64, 35, z), 11.5, 114, 0)
        for x in (24, 104):
            radial = (g.y - 35) ** 2 + (g.z - z) ** 2
            saddle = (np.abs(g.x - x) <= 4) & (radial <= 15 ** 2) & (radial >= 11.7 ** 2) & (g.z <= z)
            g.data[saddle] = 1
            # Yellow stop blocks connect the concave saddles to both posts.
            for y in (20, 50):
                g.roundbox((x - 5, y - 4, z - 4), (x + 5, y + 4, z + 5), 1.5, 4)
                g.box((x - 5, y - 2, z + 2), (x + 5, y + 2, z + 6), 5)
    return Asset('log_rack', 'Three-tier log rack', g, .05,
                 ['Three individually separated logs with native bark strips and cut-end rings.',
                  'Two footed trestles, six concave saddles and yellow stop blocks support the logs. No common presentation base.',
                  'Native conservative half reduction; no manual corrections.'])


def make_assets():
    return [logging_harvester(), timber_forwarder(), sawmill(), log_rack()]


if __name__ == '__main__':
    run_theme(Path(__file__).resolve().parent, make_assets())
