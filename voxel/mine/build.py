"""Original mine machinery authored directly into colored voxel occupancy."""
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_tools"))
from voxelkit import Grid, Asset, run_theme

PALETTE = [
    (0, 0, 0, 0), (106, 115, 75, 255), (138, 146, 102, 255),
    (62, 74, 49, 255), (209, 201, 172, 255), (235, 225, 196, 255),
    (73, 82, 80, 255), (116, 126, 122, 255), (33, 40, 38, 255),
    (55, 65, 60, 255), (194, 100, 43, 255), (230, 137, 63, 255),
    (168, 177, 170, 255), (65, 98, 102, 255), (20, 28, 27, 255),
    (142, 108, 66, 255), (135, 145, 137, 255), (236, 177, 61, 255),
]
OLIVE, OLIVE_L, OLIVE_D, CREAM, CREAM_L = range(1, 6)
STEEL, STEEL_L, CHARCOAL, TREAD, COPPER, COPPER_L, METAL, GLASS, DEEP, ORE, STONE, AMBER = range(6, 18)


def link_yz(g, x0, x1, a, b, radius, color):
    """Flat-sided, rounded-ended structural arm in a Y/Z plane."""
    dy, dz = b[0] - a[0], b[1] - a[1]
    t = np.clip(((g.y - a[0]) * dy + (g.z - a[1]) * dz) / (dy * dy + dz * dz), 0, 1)
    mask = ((g.x >= x0) & (g.x < x1)
            & ((g.y - a[0] - t * dy) ** 2 + (g.z - a[1] - t * dz) ** 2 <= radius ** 2))
    g.data[mask] = color


def track(g, xc):
    # Real loop topology around the two sprockets, with daylight around rollers.
    g.box((xc - 9, 58, 2), (xc + 9, 108, 28), CHARCOAL)
    for y in (58, 108):
        g.cylinder((xc, y, 15), 13, 18, 0, CHARCOAL)
    g.box((xc - 10, 58, 7), (xc + 10, 108, 23), 0)
    for y in (58, 108):
        g.cylinder((xc, y, 15), 8.5, 20, 0, 0)
        g.cylinder((xc, y, 15), 8.2, 14, 0, STEEL)
        g.cylinder((xc, y, 15), 4.8, 20, 0, COPPER)
        g.cylinder((xc, y, 15), 2.4, 22, 0, METAL)
    for y in (71, 83, 95):
        g.cylinder((xc, y, 13), 5.5, 13, 0, STEEL)
        g.cylinder((xc, y, 13), 2.6, 19, 0, COPPER)
    for y in range(55, 113, 6):
        g.box((xc - 10, y, 26), (xc + 10, y + 3, 30), STEEL_L)
        g.box((xc - 10, y, 1), (xc + 10, y + 3, 5), STEEL)
    # Curved end cleats use short radial blocks, not a polygonal substitute.
    for y, sign in ((58, -1), (108, 1)):
        for zoff, yoff in ((-8, 9), (0, 12), (8, 9)):
            g.box((xc - 10, y + sign * yoff - 2, 15 + zoff - 2),
                  (xc + 10, y + sign * yoff + 2, 15 + zoff + 2), STEEL_L)


def excavator():
    g = Grid((104, 128, 112), PALETTE)
    track(g, 20)
    track(g, 84)
    g.roundbox((28, 54, 18), (76, 118, 32), 4, OLIVE_D)
    g.cylinder((52, 87, 34), 23, 10, 2, STEEL)
    g.cylinder((52, 87, 39), 19, 5, 2, COPPER)
    g.roundbox((27, 59, 40), (96, 122, 48), 3, STEEL)
    # Rear power pack and its service cooling louvers.
    g.roundbox((29, 91, 47), (59, 122, 78), 5, OLIVE)
    g.roundbox((32, 96, 76), (57, 119, 81), 2, OLIVE_L)
    g.box((33, 120, 53), (55, 124, 72), CREAM)
    for z in (56, 62, 68):
        g.box((37, 123, z), (51, 125, z + 3), DEEP)
    g.box((36, 104, 79), (44, 112, 83), STEEL)
    g.cylinder((40, 108, 87), 2.8, 14, 2, CHARCOAL)
    g.beam((40, 108, 92), (35, 108, 92), 2.8, CHARCOAL)
    # Cream cab is a framed hollow shell with opaque stylized glass panels.
    g.roundbox((58, 68, 47), (90, 105, 58), 3, CREAM)
    for x in (58, 85):
        for y in (68, 100):
            g.box((x, y, 55), (x + 5, y + 5, 87), CREAM)
    g.box((62, 68, 58), (86, 72, 84), GLASS)
    g.box((86, 73, 58), (90, 100, 84), GLASS)
    g.box((58, 100, 57), (90, 105, 84), OLIVE)
    g.box((89, 83, 56), (92, 87, 85), CREAM)
    g.roundbox((56, 66, 84), (92, 107, 92), 3, CREAM_L)
    g.box((62, 72, 91), (86, 101, 94), STEEL)
    for x in (63, 82):
        g.box((x, 65, 49), (x + 5, 69, 54), AMBER)
    g.box((90, 91, 59), (93, 96, 62), METAL)
    g.cylinder((85, 99, 97), 2.7, 7, 2, AMBER)
    # Open side access walkway with copper handrails.
    g.box((90, 70, 43), (100, 111, 48), STEEL_L)
    for y in (74, 91, 108):
        g.box((97, y, 47), (101, y + 3, 63), COPPER)
    g.box((97, 74, 60), (101, 111, 64), COPPER_L)
    g.box((93, 80, 31), (101, 101, 35), STEEL)
    g.box((94, 81, 33), (102, 100, 37), METAL)
    # Articulated boom uses broad flat side faces and large visible pivots.
    g.roundbox((27, 76, 45), (50, 95, 57), 3, OLIVE_D)
    link_yz(g, 29, 47, (83, 49), (53, 98), 7.4, OLIVE_D)
    link_yz(g, 31, 45, (83, 49), (53, 98), 6.5, OLIVE)
    link_yz(g, 30, 46, (53, 98), (22, 58), 6.1, STEEL)
    link_yz(g, 32, 44, (53, 98), (22, 58), 5.3, OLIVE_L)
    link_yz(g, 32, 44, (22, 58), (18, 46), 4.6, OLIVE)
    for y, z, r in ((83, 49, 7), (53, 98, 7), (22, 58, 5.5), (18, 46, 5.5)):
        g.cylinder((38, y, z), r, 22, 0, COPPER)
        g.cylinder((38, y, z), r * .45, 24, 0, STEEL)
    # Two differently extended hydraulic actuators and exposed silver rods.
    g.beam((49, 84, 52), (49, 66, 77), 3.4, COPPER)
    g.beam((49, 66, 77), (49, 56, 94), 1.9, METAL)
    g.beam((49, 51, 97), (49, 33, 77), 3.0, COPPER)
    g.beam((49, 33, 77), (49, 23, 61), 1.8, METAL)
    # A truly hollow scoop: sidewalls, back, floor and roof lip surround air.
    g.roundbox((18, 2, 16), (58, 35, 50), 6, OLIVE_D)
    g.box((24, 0, 24), (52, 27, 45), 0)
    g.roundbox((24, 3, 22), (52, 27, 46), 3, 0)
    g.box((18, 1, 18), (58, 7, 23), STEEL)
    g.box((20, 2, 45), (56, 8, 50), STEEL_L)
    for x in (20, 30, 40, 50):
        g.box((x, 0, 15), (x + 6, 10, 21), COPPER)
        g.box((x + 1, 0, 17), (x + 5, 5, 21), COPPER_L)
    for x in (18, 54):
        g.box((x, 8, 23), (x + 4, 15, 46), STEEL)
    g.cylinder((38, 27, 45), 5, 44, 0, STEEL)
    return Asset("excavator", "Compact tracked mine excavator", g, voxel_size=.035,
                 notes={"features": ["two separate track belts", "framed cab", "articulated boom", "two hydraulic actuators", "true hollow bucket"],
                        "half": "Independent conservative 2x occupancy reduction; minor pins/cleats simplify; no manual half-grid correction."})


def mine_cart():
    g = Grid((128, 80, 96), PALETTE)
    g.roundbox((8, 12, 20), (120, 68, 31), 3, STEEL)
    for y in (19, 55):
        g.box((12, y, 16), (116, y + 6, 23), CHARCOAL)
    # Four flanged wheel units: inner flange is a larger real disc.
    for x in (30, 98):
        g.cylinder((x, 40, 15), 3.5, 64, 1, STEEL)
        for y in (14, 66):
            inward = 1 if y < 40 else -1
            outward = -inward
            g.cylinder((x, y, 15), 12, 10, 1, STEEL)
            g.cylinder((x, y + inward * 6, 15), 14, 4, 1, STEEL_L)
            g.cylinder((x, y + outward * 5, 15), 8, 3, 1, CHARCOAL)
            g.cylinder((x, y + outward * 7, 15), 4.5, 4, 1, COPPER)
            for dx, dz in ((8, 0), (-8, 0), (0, 8), (0, -8)):
                g.beam((x, y + outward * 7, 15), (x + dx, y + outward * 7, 15 + dz), 1.7, COPPER)
            g.cylinder((x, y + outward * 9, 15), 2.2, 3, 1, METAL)
    # Tapered open steel bed. Floor and wall thickness remain substantive at half.
    z = g.z
    hx = 43 + (z - 29) * .25
    hy = 16 + (z - 29) * .23
    shell = (z >= 29) & (z < 83) & (np.abs(g.x - 64) < hx) & (np.abs(g.y - 40) < hy)
    g.data[shell] = OLIVE
    g.data[shell & (z >= 43) & (z < 58)] = CREAM
    inner = (z >= 35) & (z < 90) & (np.abs(g.x - 64) < hx - 4) & (np.abs(g.y - 40) < hy - 4)
    g.data[inner] = 0
    g.box((8, 11, 80), (120, 69, 87), STEEL)
    g.box((14, 17, 80), (114, 63, 90), 0)
    # Braces follow the tapered walls and strengthen the rim at functional spans.
    for x in (26, 50, 78, 102):
        for y, top_y in ((23, 12), (57, 68)):
            g.beam((x, y, 31), (x, top_y, 81), 2.5, STEEL)
    for x, bx in ((10, 23), (118, 105)):
        for y, by in ((14, 25), (66, 55)):
            g.beam((bx, by, 31), (x, y, 81), 3.2, STEEL)
            g.box((x - 3, y - 3, 81), (x + 3, y + 3, 88), COPPER)
    for x in (9, 115):
        for y in (13, 63):
            g.box((x, y, 23), (x + 5, y + 5, 32), COPPER)
    for x in (1, 118):
        g.roundbox((x, 33, 20), (x + 9, 47, 30), 2, COPPER)
        g.box((x + 1, 37, 21), (x + 8, 43, 27), CHARCOAL)
    # End-mounted hand brake and linkage, visible from the reverse view.
    g.box((115, 55, 28), (121, 61, 63), STEEL)
    g.torus((122, 58, 65), 6, 1.8, 0, COPPER)
    g.beam((122, 53, 65), (122, 63, 65), 1.6, COPPER_L)
    g.beam((122, 58, 60), (122, 58, 70), 1.6, COPPER_L)
    return Asset("mine_cart", "Tapered mine ore cart", g, voxel_size=.035,
                 notes={"features": ["open thick-walled bed", "deep empty interior", "four flanged wheels", "end couplers", "hand brake"],
                        "half": "Independent conservative 2x grid reduction preserves rim, cavity and wheel flanges."})


def mine_elevator():
    g = Grid((116, 92, 128), PALETTE)
    # Four independent footings and slightly inclined headframe posts.
    for x in (17, 69):
        for y in (18, 70):
            g.roundbox((x - 9, y - 9, 1), (x + 9, y + 9, 10), 2, CREAM)
            tx = 27 if x < 40 else 59
            ty = 28 if y < 40 else 60
            g.beam((x, y, 10), (tx, ty, 104), 4.4, STEEL)
            g.box((x - 5, y - 5, 8), (x + 5, y + 5, 13), OLIVE_D)
    for y in (27, 59):
        g.box((20, y - 4, 99), (66, y + 5, 108), OLIVE)
        g.box((21, y - 5, 103), (65, y - 3, 108), OLIVE_L)
    for x in (25, 57):
        g.box((x, 25, 99), (x + 5, 63, 106), OLIVE)
    g.beam((19, 69, 25), (60, 62, 94), 2.7, OLIVE_D)
    g.beam((67, 69, 25), (26, 62, 94), 2.7, OLIVE_D)
    g.beam((19, 23, 30), (24, 63, 89), 2.7, OLIVE_D)
    for x in (29, 55):
        g.box((x, 41, 8), (x + 3, 47, 101), STEEL_L)
    # Suspended cage has an unmistakable clear portal and a slid-aside gate.
    g.box((27, 27, 10), (59, 61, 17), OLIVE_D)
    g.box((30, 30, 15), (56, 58, 19), CREAM)
    for x in (28, 54):
        for y in (28, 56):
            g.box((x, y, 17), (x + 4, y + 4, 57), COPPER)
    g.box((27, 27, 53), (59, 61, 60), COPPER)
    g.box((31, 31, 56), (55, 57, 62), OLIVE)
    for x in (29, 55):
        for y in range(34, 56, 6):
            g.box((x, y, 20), (x + 2, y + 2, 53), STEEL_L)
        for z in (24, 34, 44):
            g.box((x, 32, z), (x + 2, 58, z + 2), STEEL_L)
    for x in range(33, 54, 6):
        g.box((x, 57, 20), (x + 2, 59, 53), STEEL_L)
    for x in (21, 27):
        g.box((x, 25, 20), (x + 2, 28, 50), STEEL_L)
    for z in (20, 28, 36, 44, 50):
        g.box((21, 25, z), (30, 28, z + 2), STEEL_L)
    # Exposed sheave: open spokes, dark running rim and copper web.
    g.cylinder((43, 44, 115), 12, 9, 1, CHARCOAL)
    g.cylinder((43, 44, 115), 8.5, 11, 1, 0)
    g.torus((43, 44, 115), 10.3, 1.8, 1, COPPER)
    for dx, dz in ((10, 0), (-10, 0), (0, 10), (0, -10)):
        g.beam((43, 44, 115), (43 + dx, 44, 115 + dz), 2, COPPER)
    g.cylinder((43, 44, 115), 3.7, 15, 1, STEEL_L)
    g.box((34, 37, 104), (52, 51, 108), STEEL)
    # Continuous cables meet both the rim tangencies and the cage/winch.
    for y in (42, 46):
        g.beam((31, y, 115), (31, y, 65), 1.6, CHARCOAL)
        g.beam((31, y, 65), (43, y, 61), 1.8, STEEL)
        g.beam((55, y, 115), (96, y + 18, 61), 1.7, CHARCOAL)
    # Raised winch platform and exposed winding drum.
    g.roundbox((82, 45, 1), (112, 83, 39), 2, CREAM)
    g.box((80, 43, 38), (114, 85, 44), OLIVE_D)
    g.box((84, 48, 43), (110, 80, 47), STEEL)
    g.cylinder((96, 64, 55), 9.8, 24, 1, CHARCOAL)
    for y in (51, 77):
        g.cylinder((96, y, 55), 12, 4, 1, COPPER)
        g.cylinder((96, y, 55), 5, 6, 1, STEEL)
    for y in (56, 60, 64, 68, 72):
        g.cylinder((96, y, 55), 10.3, 2, 1, STEEL_L)
    g.roundbox((82, 55, 46), (89, 73, 65), 2, OLIVE)
    # Nine real stair treads and two continuous handrails.
    for i in range(9):
        y = 7 + i * 4
        g.box((91, y, 1), (107, y + 4, 5 + i * 4), CREAM)
        g.box((91, y, 3 + i * 4), (107, y + 3, 6 + i * 4), STEEL_L)
        if i % 2 == 0:
            for x in (88, 109):
                g.box((x, y, 4 + i * 4), (x + 3, y + 3, 17 + i * 4), COPPER)
    for x in (89, 110):
        g.beam((x, 8, 16), (x, 43, 51), 1.9, COPPER_L)
    for x in (82, 111):
        for y in (45, 82):
            g.box((x, y, 43), (x + 3, y + 3, 57), COPPER)
    g.box((82, 82, 54), (114, 85, 58), COPPER_L)
    # Ground-level operator box, brackets and plain useful switches.
    g.roundbox((8, 11, 32), (18, 20, 49), 1, OLIVE)
    g.box((10, 9, 42), (16, 12, 47), GLASS)
    g.cylinder((12, 9, 37), 1.8, 3, 1, COPPER_L)
    return Asset("mine_elevator", "Cable mine service elevator", g, voxel_size=.045,
                 notes={"features": ["four structural posts", "open spoked sheave", "continuous cage and winch cables", "clear cage portal", "nine stairs", "exposed winch"],
                        "half": "Conservative 2x reduction; twin close cable strands may merge locally, but the continuous route remains occupied. Static cage and drum."})


def ore_bin(g, lo, hi, rock_color):
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    g.roundbox(lo, hi, 2, CREAM)
    g.box((x0 + 4, y0 + 4, z0 + 4), (x1 - 4, y1 - 4, z1 + 1), 0)
    for x in (x0, x1 - 3):
        for y in (y0, y1 - 3):
            g.box((x, y, z0), (x + 3, y + 3, z1 + 1), STEEL)
    g.box((x0, y0, z1 - 3), (x1, y1, z1 + 1), STEEL_L)
    g.box((x0 + 3, y0 + 3, z1 - 3), (x1 - 3, y1 - 3, z1 + 2), 0)
    for dx, dy, rz in ((.3, .35, 4), (.65, .3, 5), (.4, .65, 4.6), (.7, .7, 3.5)):
        center = (x0 + (x1 - x0) * dx, y0 + (y1 - y0) * dy, z1 - 6)
        g.ellipsoid(center, (4.2, 3.8, rz), rock_color)


def ore_sorter():
    g = Grid((128, 100, 112), PALETTE)
    # Four hopper support legs, individual pads, and diagonal ties.
    for x in (15, 53):
        for y in (51, 87):
            g.roundbox((x - 6, y - 6, 1), (x + 7, y + 7, 9), 1, CREAM)
            g.box((x - 3, y - 3, 8), (x + 4, y + 4, 81), STEEL)
    g.beam((15, 52, 17), (53, 52, 65), 2.6, OLIVE_D)
    g.beam((15, 86, 65), (53, 86, 17), 2.6, OLIVE_D)
    g.box((12, 47, 68), (57, 91, 74), OLIVE_D)
    # Hollow tapered intake funnel. Its bottom outlet opens toward the screen.
    hx = 12 + (g.z - 66) * .37
    hy = 10 + (g.z - 66) * .37
    outer = (g.z >= 66) & (g.z < 106) & (np.abs(g.x - 35) < hx) & (np.abs(g.y - 69) < hy)
    inner = (g.z >= 71) & (g.z < 112) & (np.abs(g.x - 35) < hx - 4) & (np.abs(g.y - 69) < hy - 4)
    g.data[outer] = OLIVE
    g.data[outer & (g.z >= 97) & (g.z < 104)] = CREAM
    g.data[inner] = 0
    g.box((28, 62, 63), (43, 77, 78), 0)
    g.box((42, 60, 65), (52, 78, 74), 0)
    g.box((6, 41, 103), (64, 97, 109), OLIVE)
    g.box((12, 47, 103), (58, 91, 112), 0)
    for x in (8, 58):
        for y in (43, 91):
            g.box((x, y, 102), (x + 4, y + 4, 111), COPPER)
    for x in (19, 49):
        g.beam((x, 45, 102), (29 if x < 35 else 41, 60, 72), 2.2, OLIVE_D)
    # The screen is a genuinely perforated inclined voxel plate.
    cy = 61 - (g.x - 35) * (24 / 49)
    height = 74 - (g.x - 35) * (30 / 49)
    screen = ((g.x >= 35) & (g.x < 84) & (np.abs(g.y - cy) < 13)
              & (np.abs(g.z - height) < 1.8))
    g.data[screen] = STEEL_L
    holes = screen & ((np.floor(g.x).astype(int) % 8) >= 3) & ((np.floor(g.y).astype(int) % 8) >= 3)
    g.data[holes] = 0
    for a, b in (((35, 48, 74), (84, 24, 44)), ((35, 74, 74), (84, 50, 44))):
        g.beam(a, b, 2.8, COPPER)
    for x in (39, 51, 63, 75):
        y = 61 - (x - 35) * 24 / 49
        z = 74 - (x - 35) * 30 / 49
        g.beam((x, y - 12, z - 4), (x, y + 12, z - 4), 1.8, STEEL)
    for y in (27, 51):
        g.box((75, y - 3, 6), (81, y + 3, 46), STEEL)
        g.roundbox((72, y - 6, 1), (85, y + 6, 8), 1, CREAM)
    # Short discharge loop belt rises from screen end into the last bin.
    belt_z = 47 + (g.x - 85) * (14 / 31)
    belt_range = (g.x >= 85) & (g.x < 116) & (g.y >= 30) & (g.y < 50)
    strips = ((g.z >= belt_z + 3) & (g.z < belt_z + 5)) | ((g.z >= belt_z - 5) & (g.z < belt_z - 3))
    g.data[belt_range & strips] = CHARCOAL
    for x, z in ((85, 47), (116, 61)):
        g.cylinder((x, 40, z), 5, 20, 1, CHARCOAL)
        g.cylinder((x, 40, z), 3, 22, 1, STEEL)
        for y in (27, 53):
            g.cylinder((x, y, z), 6, 4, 1, COPPER)
            g.cylinder((x, y, z), 2.8, 6, 1, METAL)
    for y in (28, 52):
        g.beam((84, y, 44), (117, y, 58), 2.8, OLIVE)
    for x in range(86, 117, 6):
        z = 47 + (x - 85) * 14 / 31
        g.box((x, 31, int(z + 4)), (x + 2, 49, int(z + 7)), STEEL_L)
    for y in (28, 52):
        g.box((111, y - 2, 6), (117, y + 3, 59), STEEL)
        g.roundbox((107, y - 6, 1), (121, y + 7, 8), 1, CREAM)
    # Sorted product bins sit below separate drop points.
    ore_bin(g, (28, 1, 1), (57, 25, 26), STONE)
    ore_bin(g, (61, 1, 1), (90, 25, 26), ORE)
    ore_bin(g, (98, 25, 1), (127, 57, 27), COPPER)
    g.beam((51, 45, 51), (44, 27, 29), 4.5, STEEL)
    g.beam((73, 35, 40), (75, 25, 29), 4, STEEL)
    # Service platform and compact controls make the back worth inspecting.
    g.box((9, 32, 43), (31, 49, 49), OLIVE_D)
    for x in (10, 28):
        g.box((x, 33, 48), (x + 3, 36, 64), COPPER)
    g.box((10, 33, 61), (31, 36, 65), COPPER_L)
    g.roundbox((12, 40, 29), (24, 48, 41), 1, OLIVE)
    g.box((15, 38, 34), (21, 41, 39), GLASS)
    return Asset("ore_sorter", "Hopper and inclined mine ore sorter", g, voxel_size=.04,
                 notes={"features": ["open tapered hopper", "perforated inclined screening bed", "short loop discharge belt", "three open ore bins", "service platform"],
                        "half": "Conservative 2x reduction; screen apertures remain patterned openings, while tiny screen cells and ore clumps simplify. Static material-handling depiction."})


def make_assets():
    return [excavator(), mine_cart(), mine_elevator(), ore_sorter()]


if __name__ == "__main__":
    run_theme(Path(__file__).resolve().parent, make_assets())
