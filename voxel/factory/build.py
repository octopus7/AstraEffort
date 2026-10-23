"""Original factory voxel assets. Geometry is integer-grid occupancy, not cubes.

Front is -Y and Z is up. All physical feature dimensions are specified here in
large-grid cells. The shared exporter produces a conservative half-grid version
with twice the meters per voxel; no high-resolution mesh is scaled to fake it.
"""
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_tools"))
from voxelkit import Grid, Asset, run_theme


# Index 0 is strictly empty. Every visible color is a limited industrial finish.
PALETTE = [
    (0, 0, 0, 0),
    (226, 169, 45, 255),       # 1 mustard enamel
    (248, 198, 70, 255),       # 2 sunlit / edge enamel
    (170, 115, 30, 255),       # 3 recessed yellow
    (69, 106, 132, 255),       # 4 slate blue steel
    (93, 135, 159, 255),       # 5 blue raised casing
    (45, 72, 90, 255),         # 6 blue shadow / structure
    (217, 209, 184, 255),      # 7 ivory painted panels
    (241, 231, 206, 255),      # 8 ivory raised edges
    (154, 150, 135, 255),      # 9 muted panel reveals
    (43, 47, 48, 255),         # 10 graphite tire / belt
    (60, 65, 66, 255),         # 11 rubber treads
    (94, 100, 102, 255),       # 12 steel
    (141, 151, 153, 255),      # 13 exposed metal
    (28, 39, 43, 255),         # 14 deep openings
    (63, 118, 134, 255),       # 15 instrument glass
    (179, 76, 43, 255),        # 16 emergency switch / beacon
    (220, 181, 99, 255),       # 17 warm metal
]
YELLOW, EDGE, OCHRE = 1, 2, 3
BLUE, BLUE_L, BLUE_D = 4, 5, 6
IVORY, IVORY_L, REVEAL = 7, 8, 9
RUBBER, TREAD, STEEL, METAL, VOID, GLASS, RED, BRASS = range(10, 18)


def bolt(g, center, axis=1, radius=1.6, length=2, color=METAL):
    g.cylinder(center, radius, length, axis, color)


def wheel(g, x, y, z, radius, width):
    """Solid tire, deliberate broad tread rhythm and nested exposed hubs."""
    g.cylinder((x, y, z), radius, width, 0, RUBBER)
    radial = np.sqrt((g.y - y) ** 2 + (g.z - z) ** 2)
    angle = np.arctan2(g.z - z, g.y - y)
    tread = ((radial >= radius - 2.2) & (radial <= radius)
             & (np.abs(g.x - x) <= width / 2)
             & (np.cos(angle * 12) > 0.30))
    g.data[tread] = TREAD
    g.cylinder((x, y, z), radius * .52, width + 2, 0, OCHRE)
    g.cylinder((x, y, z), radius * .40, width + 4, 0, YELLOW)
    g.cylinder((x, y, z), radius * .21, width + 6, 0, STEEL)
    for sign in (-1, 1):
        for dy, dz in ((0, radius * .3), (0, -radius * .3),
                       (radius * .3, 0), (-radius * .3, 0)):
            bolt(g, (x + sign * (width / 2 + 2), y + dy, z + dz),
                 axis=0, radius=1.15, length=2, color=METAL)


def crate(g, lo, hi):
    """Reusable steel shipping crate with framed edges and inset carry handles."""
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    g.roundbox(lo, hi, 2, IVORY)
    g.box((x0 + 3, y0 + 3, z1 - 2), (x1 - 3, y1 - 3, z1), IVORY_L)
    for x in (x0, x1 - 3):
        for y in (y0, y1 - 3):
            g.box((x, y, z0), (x + 3, y + 3, z1), REVEAL)
            g.box((x, y, z1 - 3), (x + 3, y + 3, z1), STEEL)
    for z in (z0 + 2, z1 - 3):
        g.box((x0 + 2, y0, z), (x1 - 2, y0 + 2, z + 2), IVORY_L)
        g.box((x0 + 2, y1 - 2, z), (x1 - 2, y1, z + 2), IVORY_L)
    cx = (x0 + x1) // 2
    g.box((cx - 4, y0 - 1, z0 + 9), (cx + 4, y0 + 2, z0 + 13), REVEAL)
    g.box((cx - 2, y0 - 1, z0 + 10), (cx + 2, y0 + 1, z0 + 12), VOID)


def production_machine():
    g = Grid((112, 88, 128), PALETTE)
    # Four individual feet and a deep blue cast base.
    for x in (10, 78):
        for y in (10, 64):
            g.roundbox((x - 4, y - 4, 2), (x + 18, y + 14, 8), 2, STEEL)
            g.roundbox((x, y, 7), (x + 14, y + 10, 30), 2, BLUE)
            bolt(g, (x + 7, y - 1, 15), radius=2, length=3)
    g.roundbox((8, 8, 16), (96, 76, 32), 3, BLUE)
    g.box((11, 7, 25), (93, 12, 32), BLUE_L)
    for x in (18, 80):
        g.box((x, 5, 18), (x + 5, 9, 31), STEEL)
        bolt(g, (x + 2.5, 4, 25), radius=1.6, length=3)
    # Rounded structural press frame: back web, two columns and crown.
    g.roundbox((14, 55, 29), (86, 76, 118), 7, YELLOW)
    g.roundbox((14, 24, 29), (28, 70, 108), 4, YELLOW)
    g.roundbox((72, 24, 29), (86, 70, 108), 4, YELLOW)
    g.roundbox((12, 18, 97), (88, 74, 120), 7, YELLOW)
    g.box((18, 17, 101), (82, 21, 114), EDGE)
    # A genuine empty opening, preserved through the rear web.
    g.roundbox((29, 18, 40), (71, 68, 96), 3, 0)
    g.box((30, 67, 43), (70, 69, 91), BLUE_D)
    g.roundbox((34, 30, 117), (66, 62, 126), 4, OCHRE)
    g.roundbox((38, 34, 121), (62, 58, 126), 3, EDGE)
    g.cylinder((50, 46, 124), 4, 4, 2, STEEL)
    # Hydraulic sleeve, chrome ram and paired guide rods.
    g.cylinder((50, 44, 94), 12, 14, 2, BLUE_D)
    g.cylinder((50, 44, 84), 9, 26, 2, METAL)
    g.box((42, 34, 76), (46, 37, 97), IVORY_L)
    for x in (34, 66):
        g.cylinder((x, 44, 84), 2.8, 26, 2, STEEL)
    g.roundbox((32, 24, 66), (68, 61, 77), 2, YELLOW)
    g.box((30, 22, 64), (70, 63, 69), STEEL)
    g.box((36, 27, 62), (64, 58, 65), METAL)
    # Slotted die table and two simple fixture stops.
    g.roundbox((23, 12, 32), (77, 62, 41), 2, STEEL)
    g.box((26, 15, 39), (74, 59, 42), METAL)
    for y in (23, 35, 47):
        g.box((31, y, 40), (69, y + 3, 43), VOID)
    for x in (27, 69):
        g.box((x, 21, 41), (x + 5, 28, 47), OCHRE)
        g.box((x + 1, 20, 44), (x + 4, 24, 49), YELLOW)
    # Two open side safety screens. Bars are actual occupied voxels.
    for x in (17, 80):
        for y in (10, 48):
            g.box((x, y, 33), (x + 4, y + 4, 71), YELLOW)
            g.box((x - 1, y - 1, 68), (x + 5, y + 5, 72), STEEL)
        g.box((x, 10, 68), (x + 4, 52, 71), EDGE)
        for y in range(16, 48, 6):
            g.box((x + 1, y, 43), (x + 3, y + 2, 68), STEEL)
        for z in range(43, 68, 6):
            g.box((x + 1, 14, z), (x + 3, 50, z + 2), STEEL)
    # Operator pedestal, cream control box, recessed display and switches.
    g.roundbox((90, 11, 6), (108, 33, 12), 2, STEEL)
    g.roundbox((92, 14, 10), (106, 30, 48), 2, BLUE)
    g.roundbox((87, 6, 45), (109, 32, 69), 3, IVORY)
    g.box((91, 4, 56), (105, 7, 65), STEEL)
    g.box((93, 3, 58), (103, 5, 63), GLASS)
    g.box((94, 3, 61), (101, 4, 63), BLUE_L)
    for x, color in ((91, BLUE_D), (96, METAL), (103, RED)):
        g.cylinder((x, 4, 51), 2.1, 3, 1, color)
    # Side drive with fluted motor, reducer and a protective end grille.
    g.cylinder((90, 60, 91), 7, 16, 0, STEEL)
    g.roundbox((87, 49, 80), (94, 71, 102), 3, BLUE_D)
    g.cylinder((100, 60, 91), 11, 18, 0, BLUE)
    for x in range(94, 109, 4):
        g.cylinder((x, 60, 91), 12, 2, 0, BLUE_L)
    # Even-cell phase and two-cell slot depth survive the 2x reduction.
    g.box((108, 52, 82), (112, 68, 100), VOID)
    for y in range(54, 68, 4):
        g.box((110, y, 84), (112, y + 2, 98), BLUE_L)
    for z in range(84, 99, 6):
        g.box((110, 52, z), (112, 68, z + 2), BLUE_L)
    # Rear service cabinet, pressure accumulator and connected hydraulic pipe.
    g.roundbox((88, 48, 10), (108, 82, 59), 3, BLUE_D)
    g.roundbox((91, 49, 13), (109, 80, 57), 2, IVORY)
    g.box((94, 79, 18), (104, 82, 52), REVEAL)
    g.box((95, 81, 20), (103, 83, 50), IVORY_L)
    g.box((100, 82, 32), (103, 84, 39), STEEL)
    g.box((108, 54, 18), (110, 76, 52), REVEAL)
    g.box((109, 56, 20), (111, 74, 50), IVORY_L)
    for z in (22, 44):
        g.box((110, 54, z), (112, 58, z + 5), STEEL)
    g.box((110, 69, 32), (112, 72, 40), STEEL)
    g.cylinder((23, 80, 67), 5, 46, 2, BLUE_D)
    g.cylinder((23, 80, 89), 6, 5, 2, STEEL)
    g.beam((23, 80, 91), (23, 80, 110), 2, STEEL)
    g.beam((23, 80, 110), (45, 80, 110), 2, STEEL)
    g.beam((45, 80, 110), (45, 69, 110), 2, STEEL)
    g.beam((23, 80, 45), (23, 80, 21), 2, RUBBER)
    g.beam((23, 80, 21), (88, 80, 21), 2, RUBBER)
    for x in (20, 80):
        for z in (101, 113):
            bolt(g, (x, 17, z), radius=1.8, length=3)
    return Asset("production_machine", "Hydraulic production press", g,
                 voxel_size=.04, notes={
                     "design": "Rounded two-column hydraulic press, open ram throat, die slots, side mesh guards, operator console, fluted motor and rear hydraulic service assembly.",
                     "functional_features": ["ram", "open work throat", "die table", "guards", "control pedestal", "rear hydraulic pipe"],
                     "half_resolution": "Conservative 2x voxel reduction. Motor grille bars use even-cell phase after preview-driven correction; guard bars and bolts simplify. No manual half-grid edits or replacement mesh."})


def conveyor():
    g = Grid((128, 64, 76), PALETTE)
    # Four splayed-support stations with broad individual footplates.
    for x in (23, 101):
        for y in (12, 48):
            g.roundbox((x - 6, y - 5, 2), (x + 8, y + 9, 7), 2, STEEL)
            g.box((x - 2, y, 7), (x + 4, y + 5, 37), BLUE)
            g.box((x - 3, y - 1, 8), (x + 5, y + 6, 13), YELLOW)
            bolt(g, (x + 1, y - 2, 11), radius=1.8, length=3)
    for x in (24, 102):
        g.box((x - 2, 15, 15), (x + 3, 51, 20), BLUE_D)
    for y in (14, 50):
        g.box((25, y, 13), (103, y + 3, 17), BLUE_D)
        g.beam((28, y + 1, 16), (48, y + 1, 34), 2.2, BLUE)
        g.beam((99, y + 1, 16), (79, y + 1, 34), 2.2, BLUE)
    # Actual continuous loop: upper/lower strips and hollow rounded ends.
    g.box((18, 17, 32), (110, 47, 50), RUBBER)
    for x in (18, 110):
        g.cylinder((x, 32, 41), 9, 30, 1, RUBBER)
    g.box((18, 16, 36), (110, 48, 46), 0)
    for x in (18, 110):
        g.cylinder((x, 32, 41), 5.7, 32, 1, 0)
    # Rollers refill their centers, leaving visible loop thickness.
    for x in (18, 110):
        g.cylinder((x, 32, 41), 5.7, 40, 1, STEEL)
        for y in (11, 53):
            g.cylinder((x, y, 41), 10, 5, 1, YELLOW)
            g.cylinder((x, y + (-4 if y < 32 else 4), 41), 6.8, 4, 1, TREAD)
            g.cylinder((x, y + (-7 if y < 32 else 7), 41), 3.5, 4, 1, METAL)
    for x in range(17, 112, 7):
        g.box((x, 17, 49), (x + 2, 47, 51), TREAD)
    for y in (11, 49):
        g.roundbox((18, y, 32), (111, y + 4, 46), 2, BLUE)
        g.box((26, y - 1, 44), (103, y + 5, 47), BLUE_L)
        for x in (36, 60, 84):
            g.box((x, y - 1, 35), (x + 4, y + 5, 42), STEEL)
            bolt(g, (x + 2, y - 2, 38), radius=1.5, length=3)
        for x in (20, 103):
            g.box((x, y - 1, 45), (x + 7, y + 5, 49), EDGE)
    # Drive and reduction gear hang from the near side.
    g.roundbox((77, 10, 22), (94, 19, 38), 2, STEEL)
    g.cylinder((86, 8, 28), 8.5, 12, 1, BLUE)
    for y in (4, 8, 12):
        g.cylinder((86, y, 28), 9.5, 2, 1, BLUE_L)
    g.box((80, 2, 22), (94, 4, 34), VOID)
    for x in (82, 86, 90):
        g.box((x, 0, 23), (x + 2, 2, 33), BLUE_L)
    g.beam((92, 17, 28), (102, 17, 37), 2, STEEL)
    crate(g, (31, 21, 51), (55, 43, 74))
    crate(g, (75, 22, 51), (97, 42, 72))
    return Asset("conveyor", "Roller-end factory conveyor", g,
                 voxel_size=.045, notes={
                     "design": "Independent continuous loop belt with two exposed end roller assemblies, four support feet, diagonal bracing, near-side drive and two framed cargo bins.",
                     "functional_features": ["two end rollers", "continuous loop belt", "four feet", "drive motor", "cargo bins"],
                     "half_resolution": "Conservative 2x grid reduction. Motor grille bar phase and slot depth were corrected in the large grid to preserve half-resolution slots. Belt ribs and crate trim merge locally; no manual half-grid edits."})


def forklift():
    g = Grid((88, 128, 112), PALETTE)
    # Chassis is a rounded stepped tub, not a permanently attached floor.
    g.roundbox((16, 48, 16), (72, 122, 38), 7, YELLOW)
    g.roundbox((23, 54, 30), (65, 112, 55), 4, BLUE)
    g.box((27, 57, 47), (61, 102, 53), BLUE_D)
    g.roundbox((20, 100, 34), (68, 123, 69), 7, YELLOW)
    g.roundbox((24, 101, 65), (64, 120, 72), 3, EDGE)
    g.roundbox((19, 118, 22), (69, 126, 32), 3, STEEL)
    # Axles and all four load-bearing tires.
    for y, r in ((62, 13), (106, 11)):
        g.cylinder((44, y, 15), 3.3, 66, 0, STEEL)
        for x in (14, 74):
            wheel(g, x, y, 15, r, 14)
    # Broad rounded fenders expose tire circles at side view.
    for x0, x1 in ((8, 28), (60, 80)):
        g.roundbox((x0, 47, 28), (x1, 78, 39), 5, YELLOW)
        g.box((x0 + 2, 49, 37), (x1 - 2, 73, 41), EDGE)
        g.roundbox((x0 + 1, 94, 27), (x1 - 1, 119, 37), 4, YELLOW)
    # Two-stage mast and paired chain channels, with top bridge.
    for x in (25, 55):
        g.box((x, 38, 15), (x + 8, 47, 108), STEEL)
        g.box((x + 2, 36, 19), (x + 6, 40, 105), METAL)
        g.box((x + 1, 40, 28), (x + 7, 45, 105), VOID)
        g.box((x + 2, 37, 96), (x + 6, 43, 105), METAL)
    g.roundbox((23, 36, 101), (65, 49, 111), 2, STEEL)
    g.box((32, 38, 103), (56, 45, 108), METAL)
    for x in (37, 49):
        g.box((x, 40, 26), (x + 3, 44, 100), OCHRE)
        for z in range(29, 100, 6):
            g.box((x, 39, z), (x + 3, 41, z + 3), METAL)
    g.cylinder((44, 45, 62), 3.5, 65, 2, BLUE_D)
    g.cylinder((44, 45, 88), 2.1, 26, 2, METAL)
    # Carriage and open load backrest, wide enough to read at 64 cells.
    g.box((21, 31, 22), (67, 39, 35), STEEL)
    g.box((22, 31, 45), (66, 37, 50), YELLOW)
    g.box((22, 31, 60), (66, 37, 65), EDGE)
    for x in (22, 32, 42, 52, 62):
        g.box((x, 32, 48), (x + 4, 36, 62), YELLOW)
    for x in (27, 54):
        g.box((x, 29, 8), (x + 7, 36, 43), STEEL)
        g.box((x, 4, 8), (x + 7, 34, 14), STEEL)
        g.box((x, 2, 8), (x + 7, 8, 12), EDGE)
        g.box((x + 1, 8, 12), (x + 6, 29, 14), METAL)
    # Side steps and grab rails make open cab accessible.
    for x0, x1 in ((10, 25), (63, 78)):
        g.box((x0, 80, 19), (x1, 94, 24), BLUE_D)
        g.box((x0, 80, 22), (x1, 94, 25), STEEL)
        g.box((x0 + 2, 82, 24), (x1 - 2, 84, 26), METAL)
        g.box((x0 + 2, 89, 24), (x1 - 2, 91, 26), METAL)
    # Cab posts lean gently at the front; canopy is ivory and stepped round.
    for x in (19, 69):
        g.beam((x, 57, 48), (x, 65, 98), 2.8, STEEL)
        g.box((x - 3, 108, 52), (x + 3, 114, 100), STEEL)
        g.beam((x, 65, 98), (x, 111, 98), 3, STEEL)
        g.beam((x, 78, 43), (x, 78, 61), 1.8, METAL)
    g.roundbox((13, 59, 99), (75, 118, 107), 4, IVORY)
    g.box((19, 66, 106), (69, 111, 109), IVORY_L)
    for x in (27, 43, 59):
        g.box((x, 65, 108), (x + 3, 112, 110), REVEAL)
    # Seat, pedestal, steering column and thick open steering-wheel ring.
    g.box((35, 82, 51), (53, 99, 57), STEEL)
    g.roundbox((31, 80, 55), (57, 101, 62), 3, RUBBER)
    g.roundbox((31, 95, 60), (57, 104, 84), 3, RUBBER)
    g.box((35, 94, 66), (53, 96, 80), TREAD)
    g.box((28, 61, 51), (60, 71, 65), BLUE)
    g.box((31, 59, 60), (57, 63, 66), BLUE_L)
    g.beam((42, 68, 57), (42, 73, 72), 2.3, STEEL)
    g.torus((42, 74, 73), 6.2, 1.8, 2, RUBBER)
    g.beam((37, 74, 73), (47, 74, 73), 1.4, METAL)
    for x in (55, 60):
        g.beam((x, 77, 52), (x, 74, 64), 1.6, STEEL)
        g.ellipsoid((x, 74, 65), (2.2, 2.2, 2.2), RUBBER)
    # Functional headlamps, beacon, rear grille and counterweight service lid.
    for x in (19, 69):
        g.roundbox((x - 4, 54, 82), (x + 4, 61, 90), 1, STEEL)
        g.box((x - 2, 52, 84), (x + 2, 55, 88), IVORY_L)
    g.cylinder((68, 109, 108), 3, 8, 2, RED)
    g.box((31, 121, 41), (57, 124, 59), VOID)
    for z in (43, 49, 55):
        g.box((33, 123, z), (55, 126, z + 3), STEEL)
    g.box((32, 108, 71), (56, 118, 73), OCHRE)
    g.box((41, 110, 72), (47, 115, 75), STEEL)
    for x in (24, 60):
        g.box((x, 122, 32), (x + 5, 125, 37), RED)
    return Asset("forklift", "Counterbalance factory forklift", g,
                 voxel_size=.035, notes={
                     "design": "Four-wheel counterbalance forklift with stepped rounded fenders, paired long forks, two-stage mast, open safety cage, seat and control levers.",
                     "functional_features": ["four wheels", "two separate forks", "mast", "load backrest", "open cab", "steering wheel", "rear grille"],
                     "half_resolution": "Conservative 2x grid reduction; small chain links simplify. Fork gap, four tires and open cab remain major voids."})


def generator():
    g = Grid((128, 72, 96), PALETTE)
    # Long skid rails have real rectangular lifting pockets.
    for y in (10, 54):
        g.roundbox((4, y - 2, 2), (124, y + 10, 16), 2, BLUE)
        g.box((7, y - 3, 12), (121, y + 11, 17), BLUE_L)
        for x in (30, 80):
            g.box((x, y - 4, 5), (x + 18, y + 12, 11), 0)
            g.box((x - 2, y - 3, 5), (x, y + 11, 12), BLUE_D)
        for x in (10, 114):
            g.box((x - 3, y - 2, 2), (x + 7, y + 10, 6), STEEL)
            bolt(g, (x + 2, y - 4, 12), radius=1.8, length=3)
    for x in (12, 61, 112):
        g.box((x, 17, 8), (x + 6, 55, 16), BLUE_D)
    # Main enclosure and bottom steel sill, rounded in the voxel grid.
    g.roundbox((12, 12, 16), (116, 60, 78), 8, YELLOW)
    g.roundbox((12, 12, 16), (116, 60, 25), 3, BLUE)
    g.box((22, 17, 76), (106, 55, 80), EDGE)
    # Framed ivory service doors on the near broad side.
    for x0, x1 in ((33, 66), (69, 99)):
        g.roundbox((x0 - 1, 10, 26), (x1 + 1, 15, 69), 2, OCHRE)
        g.roundbox((x0, 9, 28), (x1, 13, 67), 2, IVORY)
        g.box((x0 + 3, 8, 62), (x1 - 3, 10, 65), IVORY_L)
        for z in (33, 40, 47):
            g.box((x0 + 6, 8, z), (x1 - 6, 11, z + 3), REVEAL)
            g.box((x0 + 6, 7, z + 2), (x1 - 6, 10, z + 4), IVORY_L)
        for z in (32, 60):
            g.box((x0 - 2, 7, z), (x0 + 3, 11, z + 6), STEEL)
            bolt(g, (x0 + .5, 6, z + 3), radius=1.2, length=2)
        g.box((x1 - 6, 7, 51), (x1 - 2, 10, 59), STEEL)
        g.box((x1 - 5, 6, 53), (x1 - 3, 8, 58), VOID)
    # A separate inset instrument panel with glass meter and switches.
    g.roundbox((101, 10, 37), (113, 14, 65), 2, STEEL)
    g.box((103, 8, 53), (111, 11, 62), VOID)
    g.box((104, 7, 55), (110, 9, 60), GLASS)
    g.box((105, 6, 58), (109, 8, 60), BLUE_L)
    for x, c in ((104, YELLOW), (110, RED)):
        g.cylinder((x, 8, 44), 1.8, 3, 1, c)
    # Deep framed radiator grilles at BOTH ends; purposeful bars, no noise.
    for x, outer in ((11, 8), (116, 119)):
        g.roundbox((x - 2, 20, 28), (x + 3, 52, 65), 3, OCHRE)
        g.box((x - 3, 23, 31), (x + 4, 49, 62), VOID)
        for z in range(33, 62, 6):
            g.box((outer - 1, 23, z), (outer + 2, 49, z + 3), STEEL)
        for y in (22, 48):
            g.box((outer - 1, y, 30), (outer + 2, y + 2, 64), BLUE_D)
    # Rear access panels and large cable outlet/socket assembly.
    for x0, x1 in ((25, 57), (62, 99)):
        g.box((x0, 59, 29), (x1, 62, 66), OCHRE)
        g.roundbox((x0 + 2, 61, 31), (x1 - 2, 64, 64), 2, IVORY)
        for z in (36, 44, 52):
            g.box((x0 + 6, 63, z), (x1 - 6, 66, z + 3), REVEAL)
        g.box((x1 - 7, 64, 55), (x1 - 3, 67, 61), STEEL)
    g.roundbox((99, 59, 28), (113, 65, 56), 2, BLUE_D)
    for z in (36, 48):
        g.cylinder((106, 65, z), 4, 4, 1, STEEL)
        g.cylinder((106, 68, z), 2, 3, 1, VOID)
    g.torus((39, 66, 46), 11, 2.2, 1, RUBBER)
    g.beam((39, 66, 57), (39, 65, 66), 2.2, RUBBER)
    g.box((35, 63, 64), (43, 69, 68), STEEL)
    # Exhaust stack and visible bent outlet; cap/fuel filler and lifting eyes.
    g.box((21, 39, 77), (31, 49, 81), STEEL)
    g.cylinder((26, 44, 86), 3.4, 18, 2, RUBBER)
    g.beam((26, 44, 92), (18, 44, 92), 3.4, RUBBER)
    g.cylinder((17, 44, 92), 4, 4, 0, STEEL)
    g.cylinder((15, 44, 92), 2.3, 2, 0, VOID)
    g.cylinder((92, 33, 79), 6, 4, 2, STEEL)
    g.cylinder((92, 33, 82), 4, 3, 2, RUBBER)
    g.box((89, 29, 83), (95, 37, 85), METAL)
    for x in (44, 80):
        g.box((x - 5, 33, 78), (x + 5, 41, 81), OCHRE)
        g.torus((x, 37, 84), 4, 1.8, 1, STEEL)
    return Asset("generator", "Skid-mounted factory generator", g,
                 voxel_size=.04, notes={
                     "design": "Rounded generator enclosure on two pocketed skid rails, paired ivory service doors, dual end radiator grilles, instrument panel, rear cable/service sockets and bent exhaust.",
                     "functional_features": ["skid rails", "forklift pockets", "end grilles", "service doors", "exhaust", "lifting eyes", "rear cable loop"],
                     "half_resolution": "Conservative 2x reduction retains skid holes, grille rhythm and exhaust. Thin lifting eyes and cable section become stepped chunky loops."})


def make_assets():
    return [production_machine(), conveyor(), forklift(), generator()]


if __name__ == "__main__":
    run_theme(Path(__file__).resolve().parent, make_assets())
