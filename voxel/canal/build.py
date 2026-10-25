"""Original canal assets. Pure native voxel authoring; shared export pipeline."""
from pathlib import Path
import math
import sys
import numpy as np

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_tools'))
from voxelkit import Grid, Asset, run_theme

PALETTE_NAMES = [
    'empty', 'deep_teal', 'paint_teal', 'soft_teal', 'ink', 'iron',
    'iron_highlight', 'brass', 'limestone_cap', 'limestone', 'aged_stone',
    'oak', 'oak_light', 'oak_endgrain', 'terracotta', 'clay_light',
    'clay_shadow', 'window_dark', 'window_light', 'hull_charcoal', 'weight_stone',
]
PALETTE = [
    (0, 0, 0, 0), (36, 79, 85), (63, 112, 115), (101, 147, 145),
    (38, 58, 60), (68, 84, 87), (113, 128, 125), (199, 162, 93),
    (227, 217, 188), (184, 182, 157), (143, 153, 135),
    (173, 125, 73), (208, 164, 106), (118, 84, 54),
    (166, 95, 64), (194, 123, 82), (123, 71, 50),
    (48, 95, 104), (141, 179, 177), (48, 56, 57), (104, 113, 107),
]
DEEP, TEAL, SOFT, INK, IRON, METAL, BRASS, CAP, STONE, AGED = range(1, 11)
OAK, LIGHTWOOD, ENDWOOD, CLAY, LIGHTCLAY, DARKCLAY, GLASS, LIGHTGLASS, HULL, WEIGHT = range(11, 21)


def masonry(g, lo, hi):
    """Real independent stone pier/abutment, shallow staggered coursing."""
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    g.roundbox(lo, hi, 2.5, STONE)
    for k, z in enumerate(range(int(z0) + 10, int(z1) - 2, 12)):
        g.box((x0, y0, z), (x1, y0 + 1, z + 1), AGED)
        g.box((x1 - 1, y0, z), (x1, y1, z + 1), AGED)
        for x in range(int(x0) + 7 + (k % 2) * 7, int(x1), 14):
            g.box((x, y0, z - 9), (x + 1, y0 + 1, z), AGED)
        for y in range(int(y0) + 7 + (k % 2) * 7, int(y1), 14):
            g.box((x1 - 1, y, z - 9), (x1, y + 1, z), AGED)


def bollard(g, x, y, z):
    g.cylinder((x, y, z + 1.5), 3.7, 3, 2, IRON)
    g.cylinder((x, y, z + 5), 2.4, 7, 2, INK)
    g.cylinder((x, y, z + 8.5), 3.2, 2, 2, CAP)


def gear_y(g, x, y, z):
    """Exposed toothed hand gear, axle, spokes and offset crank."""
    g.torus((x, y, z), 6.5, 2.1, 1, DEEP)
    for i in range(8):
        angle = i * math.pi / 4
        gx, gz = x + 8 * math.cos(angle), z + 8 * math.sin(angle)
        g.roundbox((gx - 2, y - 3, gz - 2), (gx + 2, y + 3, gz + 2), 0.8, IRON)
    for dx, dz in ((6, 0), (-6, 0), (0, 6), (0, -6)):
        g.beam((x, y, z), (x + dx, y, z + dz), 1.5, IRON)
    g.cylinder((x, y - 2, z), 2.8, 15, 1, METAL)
    g.beam((x, y - 10, z), (x + 7, y - 10, z + 3), 1.7, IRON)
    g.cylinder((x + 7, y - 13, z + 3), 2, 8, 1, LIGHTWOOD)


def canal_boat():
    g = Grid((48, 128, 58), PALETTE)
    # Rounded barge hull, flat load-bearing bottom and layered rubbing strakes.
    g.roundbox((2, 2, 2), (46, 126, 33), 10, HULL)
    occupied = g.data > 0
    g.data[occupied & (g.z >= 13) & (g.z < 29)] = DEEP
    g.data[occupied & (g.z >= 23) & (g.z < 25)] = CLAY
    g.roundbox((3, 3, 28), (45, 125, 33), 2.5, CAP)
    g.roundbox((6, 7, 30), (42, 121, 32), 1, LIGHTWOOD)
    # A genuinely hollow cargo well; aft crates leave most of its floor exposed.
    g.roundbox((7, 43, 18), (41, 112, 40), 3, 0)
    g.box((9, 46, 18), (39, 109, 20), OAK)
    for x in (15, 23, 31):
        g.box((x, 46, 19), (x + 1, 109, 20), ENDWOOD)
    for lo, hi in [((10, 86, 20), (24, 103, 32)), ((26, 94, 20), (38, 106, 30))]:
        g.roundbox(lo, hi, 1, OAK)
        for z in (lo[2] + 2, hi[2] - 3):
            g.box((lo[0], lo[1], z), (hi[0], hi[1], z + 2), LIGHTWOOD)
        for x in (lo[0] + 2, hi[0] - 4):
            g.box((x, lo[1], lo[2]), (x + 2, hi[1], hi[2]), ENDWOOD)
    # Compact wheelhouse forward. Painted opaque glazing is intentionally solid.
    g.roundbox((9, 13, 31), (39, 42, 49), 3, TEAL)
    g.box((14, 12, 36), (34, 14, 46), CAP)
    g.box((16, 11, 38), (23, 13, 44), GLASS)
    g.box((25, 11, 38), (32, 13, 44), GLASS)
    g.box((16, 11, 42), (19, 12, 44), LIGHTGLASS)
    g.box((38, 17, 36), (40, 29, 46), CAP)
    g.box((39, 19, 38), (41, 27, 44), GLASS)
    g.box((39, 19, 42), (41, 22, 44), LIGHTGLASS)
    g.box((38, 32, 31), (40, 40, 46), ENDWOOD)
    g.box((39, 33, 32), (41, 39, 45), OAK)
    g.box((40, 35, 38), (42, 37, 40), BRASS)
    g.roundbox((7, 10, 48), (41, 45, 52), 2, HULL)
    g.roundbox((11, 14, 51), (37, 41, 53), 1, IRON)
    g.cylinder((17, 30, 55), 2, 6, 2, INK)
    g.cylinder((17, 30, 57), 2.8, 2, 2, CAP)
    for x, y in ((11, 10), (37, 10), (11, 118), (37, 118)):
        bollard(g, x, y, 31)
    # Ring fender and simple aft tiller are functional nautical fittings.
    g.torus((24, 3, 18), 6.5, 2.5, 1, HULL)
    g.beam((24, 117, 32), (24, 117, 42), 1.8, IRON)
    g.beam((24, 117, 41), (31, 117, 41), 1.8, LIGHTWOOD)
    return Asset('canal_boat', 'Canal cargo boat', g, 0.065, [
        'Rounded barge hull with exposed recessed cargo well and two aft crates.',
        'Cabin glazing uses solid opaque palette colors. No water or terrain base.',
        'Half uses shared conservative nonempty-majority reduction without manual changes.',
    ])


def lock_gate():
    g = Grid((128, 52, 90), PALETTE)
    for x0 in (2, 104):
        masonry(g, (x0, 8, 5), (x0 + 22, 46, 64))
        g.roundbox((x0 - 2, 6, 0), (x0 + 24, 48, 10), 2, AGED)
        g.roundbox((x0 - 2, 6, 60), (x0 + 24, 48, 68), 2, CAP)
    # Two true gate leaves swing toward -Y by 30 degrees, preserving an open gap.
    for hinge_x, direction in ((24, 1), (104, -1)):
        dx, dy = direction * math.cos(math.pi / 6), -0.5
        u = (g.x - hinge_x) * dx + (g.y - 30) * dy
        v = -(g.x - hinge_x) * dy + (g.y - 30) * dx
        plank = (u >= 0) & (u <= 37) & (abs(v) <= 3) & (g.z >= 10) & (g.z < 58)
        g.data[plank] = OAK
        g.data[plank & ((u % 8) < 1.5)] = ENDWOOD
        g.data[plank & ((g.z < 14) | (g.z >= 55))] = LIGHTWOOD
        strap = plank & (((g.z >= 23) & (g.z < 27)) | ((g.z >= 44) & (g.z < 48)) | (u < 3) | (u > 34))
        g.data[strap] = IRON
        g.cylinder((hinge_x, 30, 36), 3.6, 54, 2, INK)
        for z in (17, 51):
            g.cylinder((hinge_x, 30, z), 4.5, 5, 2, METAL)
        for uu in (3, 34):
            px, py = hinge_x + uu * dx, 30 + uu * dy
            g.beam((px, py, 56), (px, py, 66), 1.8, IRON)
            for z in (25, 46):
                g.cylinder((px, py - 3.4, z), 1.4, 2, 1, BRASS)
        g.beam((hinge_x + 3 * dx, 30 + 3 * dy, 65),
               (hinge_x + 34 * dx, 30 + 34 * dy, 65), 1.8, IRON)
    for x in (13, 115):
        g.roundbox((x - 4, 23, 66), (x + 4, 33, 76), 1, DEEP)
        gear_y(g, x, 26, 78)
        # Operating shaft descends visibly into each hinge gearbox.
        g.cylinder((x + (6 if x < 64 else -6), 34, 69), 2, 18, 2, IRON)
        g.beam((x, 31, 73), (24 if x < 64 else 104, 30, 63), 2, METAL)
    return Asset('lock_gate', 'Partly open double lock gates', g, 0.06, [
        'Two angled timber leaves with iron straps, hinge barrels, toothed hand gears and cranks.',
        'Continuous central air gap; stonework consists only of the two functional support piers.',
        'Static partly open pose; no rig or operable animation.',
    ])


def drawbridge():
    g = Grid((84, 128, 104), PALETTE)
    for y0, y1 in ((2, 22), (100, 126)):
        masonry(g, (4, y0, 4), (80, y1, 23))
        g.roundbox((2, y0 - 1, 0), (82, y1 + 1, 6), 2, AGED)
        g.roundbox((2, y0 - 1, 21), (82, y1 + 1, 26), 2, CAP)
    # Deck native occupancy lies in a 30-degree local YZ frame.
    c, s = math.cos(math.pi / 6), math.sin(math.pi / 6)
    u = -(g.y - 100) * c + (g.z - 25) * s
    v = (g.y - 100) * s + (g.z - 25) * c
    deck = (g.x >= 19) & (g.x < 65) & (u >= 0) & (u <= 80) & (abs(v) <= 3)
    g.data[deck] = OAK
    g.data[deck & (v > 1)] = LIGHTWOOD
    g.data[deck & ((u % 8) < 1.4)] = ENDWOOD
    girder = (((g.x >= 17) & (g.x < 22)) | ((g.x >= 62) & (g.x < 67))) & (u >= 0) & (u <= 80) & (v >= -5) & (v <= 0)
    g.data[girder] = DEEP
    cross = (g.x >= 17) & (g.x < 67) & (u >= 0) & (u <= 80) & (v >= -5) & (v <= -2) & ((u % 20) < 3)
    g.data[cross] = IRON
    # The outboard lift links meet this transverse structural nose member.
    g.beam((13, 31, 64), (71, 31, 64), 2.3, IRON)
    for x in (19, 65):
        for uu in (0, 16, 32, 48, 64, 80):
            yy, zz = 100 - uu * c, 25 + uu * s
            g.beam((x, yy, zz + 3), (x, yy, zz + 18), 1.8, IRON)
        for dz in (10, 18):
            g.beam((x, 100, 25 + dz), (x, 100 - 80 * c, 65 + dz), 1.6, CAP)
    # Heel axle and twin uprights carry the overhead counterbalance assembly.
    g.cylinder((42, 100, 25), 4.7, 63, 0, IRON)
    for x in (13, 71):
        g.roundbox((x - 4, 96, 25), (x + 4, 104, 80), 2, DEEP)
        g.roundbox((x - 6, 94, 25), (x + 6, 106, 31), 2, IRON)
        g.beam((x, 38, 94), (x, 124, 69), 3.2, DEEP)
        g.beam((x, 38, 94), (x, 31, 65), 1.8, IRON)
        g.beam((x, 124, 69), (x, 121, 61), 2, IRON)
        g.roundbox((x - 7, 116, 44), (x + 7, 127, 63), 3, WEIGHT)
        g.roundbox((x - 5, 117, 61), (x + 5, 126, 65), 1, IRON)
        for z in (49, 56):
            g.box((x - 7, 116, z), (x + 7, 117, z + 1), IRON)
    g.cylinder((42, 100, 76), 3.4, 68, 0, IRON)
    for x in (8, 76):
        g.cylinder((x, 100, 76), 7, 6, 0, IRON)
        g.cylinder((x + (4 if x > 42 else -4), 100, 76), 4, 3, 0, CAP)
        g.cylinder((x + (6 if x > 42 else -6), 100, 76), 2, 2, 0, BRASS)
    # Manual winch on the visible right tower.
    g.torus((77, 100, 42), 6, 2, 0, IRON)
    g.cylinder((76, 100, 42), 2, 8, 0, METAL)
    g.beam((77, 94, 42), (77, 106, 42), 1.4, IRON)
    g.beam((77, 100, 36), (77, 100, 48), 1.4, IRON)
    g.cylinder((80, 104, 46), 1.6, 6, 0, LIGHTWOOD)
    for x in (11, 73):
        bollard(g, x, 11, 26)
    return Asset('drawbridge', 'Raised counterweighted drawbridge', g, 0.065, [
        'Deck raised 30 degrees around a real heel axle; twin overhead balance arms and counterweights.',
        'Air navigation corridor under the span; only two structural abutments, no canal/terrain floor.',
        'Static pose with modeled pivot and winch; no rig or mechanical simulation.',
        'A demonstrated large-grid lift-link gap was closed with the deck nose crossmember.',
    ])


def lockkeepers_house():
    g = Grid((128, 104, 128), PALETTE)
    # Foundations and front steps belong to the building, not a scenic ground tile.
    g.roundbox((4, 18, 0), (94, 98, 10), 2, AGED)
    g.roundbox((8, 22, 8), (88, 94, 75), 3, CAP)
    g.box((8, 22, 9), (88, 94, 16), STONE)
    for i in range(3):
        g.box((38, 4 + 5 * i, 0), (66, 19 + 5 * i, 3 + 3 * i), STONE)
    for z in range(18, 72, 12):
        for x in (8, 80):
            g.box((x, 21, z), (x + 8, 26, z + 7), STONE)
        g.box((84, 26, z), (89, 34, z + 7), STONE)
        g.box((84, 82, z), (89, 94, z + 7), STONE)
    # Gable walls and distinct stepped clay roof skins.
    roof_height = 112 - abs(g.x - 48) * 0.79
    attic = (g.x >= 8) & (g.x < 88) & (g.y >= 22) & (g.y < 94) & (g.z >= 74) & (g.z < roof_height - 3)
    g.data[attic] = CAP
    roof = (g.x >= 2) & (g.x < 94) & (g.y >= 16) & (g.y < 100) & (g.z <= roof_height) & (g.z > roof_height - 6)
    g.data[roof] = CLAY
    g.data[roof & ((g.y % 12) < 2)] = DARKCLAY
    g.data[roof & ((np.floor(abs(g.x - 48) / 6) % 2) == 0) & ((g.y % 12) >= 2)] = LIGHTCLAY
    g.roundbox((45, 15, 109), (51, 101, 113), 2, CLAY)
    g.box((3, 17, 72), (9, 99, 76), DEEP)
    g.box((87, 17, 72), (93, 99, 76), DEEP)
    # Front entrance and opaque inset glazing with stout readable mullions.
    g.box((38, 20, 10), (65, 25, 55), STONE)
    g.box((42, 19, 11), (61, 24, 51), DEEP)
    g.box((45, 18, 33), (58, 20, 47), CAP)
    g.box((47, 17, 35), (56, 19, 45), GLASS)
    g.box((56, 17, 24), (59, 20, 27), BRASS)
    for x0, x1, z0, z1 in ((15, 34, 32, 57), (39, 57, 83, 99)):
        g.box((x0, 20, z0), (x1, 24, z1), STONE)
        g.box((x0 + 3, 19, z0 + 3), (x1 - 3, 21, z1 - 3), GLASS)
        xm = (x0 + x1) // 2
        g.box((xm - 1, 18, z0 + 3), (xm + 1, 21, z1 - 3), CAP)
        g.box((x0 + 3, 18, (z0 + z1) // 2), (x1 - 3, 21, (z0 + z1) // 2 + 2), CAP)
        g.box((x0 - 1, 17, z0 - 2), (x1 + 1, 24, z0 + 1), CAP)
    g.box((86, 42, 32), (90, 66, 58), STONE)
    g.box((89, 45, 35), (91, 63, 55), GLASS)
    g.box((90, 53, 35), (92, 55, 55), CAP)
    g.box((90, 45, 44), (92, 63, 46), CAP)
    g.box((86, 40, 30), (93, 68, 33), CAP)
    # Working chimney and rainwater downpipe.
    g.roundbox((69, 73, 87), (82, 87, 122), 1, CLAY)
    for z in (94, 102, 110, 118):
        g.box((69, 73, z), (82, 87, z + 1), DARKCLAY)
    g.roundbox((67, 71, 119), (84, 89, 124), 1, CAP)
    g.box((71, 75, 124), (75, 80, 128), INK)
    g.box((77, 81, 124), (81, 86, 128), INK)
    g.beam((91, 90, 74), (91, 90, 8), 2, IRON)
    g.beam((91, 90, 8), (95, 90, 5), 2, IRON)
    # Freestanding lock control cabinet with gauge, lever, vents and conduit.
    g.roundbox((94, 24, 0), (127, 61, 9), 2, STONE)
    g.roundbox((97, 28, 9), (124, 57, 56), 2, TEAL)
    g.box((100, 27, 14), (121, 29, 52), DEEP)
    g.roundbox((95, 26, 54), (126, 59, 59), 2, CAP)
    g.box((101, 26, 39), (112, 28, 50), METAL)
    g.box((103, 25, 41), (110, 27, 48), CAP)
    g.beam((106, 24, 42), (109, 24, 46), 0.9, INK)
    g.box((114, 26, 24), (119, 28, 40), IRON)
    g.beam((116, 25, 27), (116, 21, 38), 1.5, BRASS)
    g.cylinder((116, 21, 39), 2, 4, 0, LIGHTWOOD)
    g.box((103, 26, 24), (108, 28, 29), BRASS)
    for z in (18, 24, 30, 36):
        g.box((123, 35, z), (125, 49, z + 2), INK)
    g.beam((88, 66, 20), (95, 66, 20), 2.5, IRON)
    g.beam((95, 66, 20), (99, 54, 20), 2.5, IRON)
    return Asset('lockkeepers_house', "Lock keeper's house and control cabinet", g, 0.05, [
        'Compact limestone building, stepped terracotta gable, chimney, entrance and side window.',
        'Separate lock-control cabinet includes analog gauge, operating lever, vents and conduit.',
        'Windows are opaque palette inserts; no accessible interior or common diorama floor.',
    ])


def make_assets():
    return [canal_boat(), lock_gate(), drawbridge(), lockkeepers_house()]


if __name__ == '__main__':
    run_theme(Path(__file__).resolve().parent, make_assets())
