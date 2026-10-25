"""Original fire/rescue voxel assets; native colored occupancy is authoritative."""
from pathlib import Path
import sys
import numpy as np

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_tools'))
from voxelkit import Grid, Asset, run_theme

# A coherent but restrained emergency-service palette, authored for this theme.
PALETTE = [
    (0, 0, 0, 0),
    (192, 48, 32),       # 1 vermilion body
    (123, 35, 29),       # 2 darker panel / brick
    (237, 226, 201),     # 3 ivory paint / stone
    (39, 45, 49),        # 4 tire / graphite
    (82, 92, 97),        # 5 steel dark
    (163, 174, 178),     # 6 brushed aluminum
    (47, 91, 116),       # 7 opaque cockpit glazing
    (96, 155, 178),      # 8 blue reflected band
    (239, 162, 38),      # 9 warning amber
    (251, 225, 136),     # 10 lamp lens
    (103, 107, 103),     # 11 concrete
    (195, 190, 174),     # 12 warm interior wall
    (221, 78, 42),       # 13 hose rubber / hot red panel
    (24, 33, 38),        # 14 dark recess
]
R, RD, IV, BK, ST, AL, GL, GH, AM, LP, CO, IN, HO, DK = range(1, 15)


def wheel(g, x, y, z, radius, width):
    g.cylinder((x, y, z), radius, width, 0, BK)
    side = 1 if x > g.shape[0] / 2 else -1
    outer = x + side * (width / 2 - 1)
    g.cylinder((outer, y, z), radius * .62, 2, 0, AL)
    g.cylinder((outer + side, y, z), radius * .40, 2, 0, ST)
    g.cylinder((outer + side * 2, y, z), radius * .22, 2, 0, R)
    # Sparse hub bolts are functional machinery detail, not texture noise.
    for dy, dz in ((0, 5), (0, -5), (5, 0), (-5, 0)):
        if radius >= 10:
            g.cylinder((outer + side * 2, y + dy, z + dz), 1.1, 2, 0, IV)


def preserve_engine_half_detail(g):
    """Restore observed lost shutter stripes and hose separation in native 64 grid."""
    for x in (4, 27):
        for ya, yb in ((24, 32), (48, 57)):
            for z in (17, 19, 21, 23, 25, 27):
                g.box((x, ya, z), (x+1, yb, z+1), ST)
        # A dark recessed color line separates the two coiled hose turns.
        ring = np.sqrt((g.y-39.5)**2 + (g.z-21.5)**2)
        g.data[(g.x >= x) & (g.x < x+1) & (np.abs(ring-3.4) <= .60) & (g.data == HO)] = RD


def fire_engine():
    g = Grid((64, 128, 76), PALETTE)
    # Ladder engine chassis, passenger cab and equipment body.
    g.roundbox((10, 10, 15), (54, 123, 25), 3, BK)
    g.roundbox((11, 8, 20), (53, 46, 62), 5, R)
    g.roundbox((12, 43, 24), (52, 121, 60), 3, R)
    g.box((11, 45, 25), (53, 120, 29), IV)
    g.roundbox((10, 10, 56), (54, 44, 64), 3, IV)
    # Framed front and side windows, no transparency dependency.
    g.roundbox((14, 7, 34), (50, 12, 57), 3, IV)
    g.roundbox((17, 6, 37), (47, 10, 54), 2, GL)
    g.box((31, 5, 36), (33, 11, 55), IV)
    g.box((18, 5, 49), (30, 7, 52), GH)
    g.box((34, 5, 49), (45, 7, 52), GH)
    for side in (0, 1):
        x0, x1 = (10, 14) if side == 0 else (50, 54)
        g.roundbox((x0, 15, 35), (x1, 39, 56), 2, IV)
        g.roundbox((x0-1 if side == 0 else x0+1, 18, 38),
                   (x1-1 if side == 0 else x1+1, 36, 53), 1, GL)
        g.box((x0, 39, 27), (x1, 41, 53), RD)
        g.box((x0-1, 34, 32), (x1+1, 40, 34), ST)
        mirror_x = 7 if side == 0 else 57
        g.beam((mirror_x, 17, 41), (12 if side == 0 else 52, 19, 43), 1.5, ST)
        g.roundbox((mirror_x-2, 11, 39), (mirror_x+2, 17, 49), 1, BK)
    # Front equipment: broad grille, bumper, lamps and towing points.
    g.box((21, 6, 25), (43, 10, 35), DK)
    for z in (27, 31):
        g.box((22, 5, z), (42, 7, z+1), ST)
    g.roundbox((8, 4, 16), (56, 12, 23), 2, IV)
    for x in (14, 43):
        g.roundbox((x, 6, 25), (x+7, 10, 32), 1, ST)
        g.box((x+1, 5, 26), (x+6, 7, 31), LP)
    g.box((22, 3, 17), (26, 6, 20), ST)
    g.box((38, 3, 17), (42, 6, 20), ST)
    # Large, readable side shutter bays with recessed frames.
    for side in (0, 1):
        xa, xb = (9, 14) if side == 0 else (50, 55)
        outside = 8 if side == 0 else 54
        for ya, yb in ((47, 65), (94, 116)):
            g.box((xa, ya, 30), (xb, yb, 57), IV)
            g.box((xa-1 if side == 0 else xa+1, ya+2, 32),
                  (xb-1 if side == 0 else xb+1, yb-2, 55), AL)
            for z in range(34, 55, 4):
                g.box((outside, ya+2, z), (outside+2, yb-2, z+1), ST)
            g.box((outside-1, ya+4, 33), (outside+3, yb-4, 35), BK)
        # Open hose compartment with actual coil rings and empty interstices.
        g.box((xa, 66, 30), (xb, 93, 57), IV)
        g.box((xa-1, 68, 32), (xb+1, 91, 55), 0)
        back_x = 15 if side == 0 else 49
        g.box((back_x-1, 68, 32), (back_x+1, 91, 55), DK)
        center_x = 10 if side == 0 else 54
        for major in (5, 9):
            g.torus((center_x, 79, 43), major, 1.8, 0, HO)
        g.cylinder((center_x, 79, 43), 3, 8, 0, AL)
        g.beam((center_x, 87, 38), (center_x, 88, 33), 1.7, HO)
        g.cylinder((center_x, 88, 33), 2.4, 3, 0, AL)
    # Four wheel arches are cut before the independent tires are installed.
    for x in (11, 53):
        for y in (29, 104):
            g.cylinder((x, y, 14), 15, 14, 0, 0)
            wheel(g, x, y, 14, 12, 10)
    # Ladder supports and true open rungs, mounted above the equipment roof.
    for y in (51, 107):
        g.box((22, y, 60), (42, y+4, 66), ST)
    g.roundbox((21, 25, 65), (25, 119, 71), 1, AL)
    g.roundbox((39, 25, 65), (43, 119, 71), 1, AL)
    for y in range(29, 119, 9):
        g.box((24, y, 66), (40, y+3, 69), ST)
    # Second sliding rail pair remains visibly narrower than the lower ladder.
    g.box((26, 28, 70), (29, 108, 73), AL)
    g.box((35, 28, 70), (38, 108, 73), AL)
    for y in range(33, 107, 12):
        g.box((28, y, 71), (36, y+2, 73), ST)
    for x in (16, 42):
        g.roundbox((x-3, 23, 64), (x+3, 30, 69), 2, AM)
        g.box((x-2, 24, 68), (x+2, 29, 70), LP)
    g.box((10, 119, 20), (54, 124, 24), IV)
    for x in (13, 47):
        g.box((x, 121, 29), (x+4, 123, 35), AM)
    return Asset('fire_engine', 'Ladder fire engine', g, .05,
                 ['Original four-wheel engine with shutter grooves, exposed hose coils and two-level roof ladder.',
                  'Half correction after actual render inspection: restore one-native-cell shutter stripes and dark separation between hose coil turns; ladder geometry is unchanged.'],
                 half_postprocess=preserve_engine_half_detail)


def rescue_robot():
    g = Grid((96, 128, 108), PALETTE)
    # Paired continuous track loops with visible road wheels and raised grousers.
    for xa, xb in ((7, 29), (67, 89)):
        cx = (xa+xb)/2
        g.roundbox((xa, 39, 4), (xb, 123, 31), 11, BK)
        g.roundbox((xa-1, 48, 11), (xb+1, 114, 24), 6, 0)
        for y in (52, 68, 84, 100, 110):
            g.cylinder((cx, y, 17), 8, 22, 0, ST)
            outside = xa if xa < 40 else xb-1
            g.cylinder((outside, y, 17), 4.5, 3, 0, AL)
            g.cylinder((outside-1 if xa < 40 else outside+1, y, 17), 2, 2, 0, BK)
        for y in range(50, 115, 8):
            g.box((xa-1, y, 28), (xb+1, y+3, 33), ST)
            g.box((xa-1, y, 3), (xb+1, y+3, 7), ST)
    g.roundbox((27, 54, 19), (69, 116, 32), 4, ST)
    g.roundbox((26, 50, 29), (70, 115, 48), 5, R)
    g.box((27, 54, 40), (69, 111, 44), IV)
    g.roundbox((25, 48, 27), (71, 55, 35), 2, IV)
    g.box((34, 47, 28), (62, 51, 33), BK)
    # Side vents and carrying loops.
    for x in (25, 68):
        for y in (80, 87, 94, 101):
            g.box((x, y, 31), (x+3, y+3, 39), DK)
    for x in (33, 62):
        g.torus((x, 49, 27), 3.5, 1.4, 1, ST)
    # Mechanically recognizable manipulator: turntable, three joints and an open jaw.
    g.cylinder((48, 71, 48), 14, 7, 2, ST)
    g.cylinder((48, 71, 53), 10, 5, 2, BK)
    g.cylinder((48, 70, 59), 8.5, 25, 0, BK)
    g.beam((48, 70, 59), (48, 47, 81), 6, R)
    g.beam((55, 70, 59), (55, 48, 78), 2, AL)
    g.cylinder((48, 47, 81), 8, 23, 0, ST)
    g.cylinder((60, 47, 81), 4, 3, 0, AL)
    g.beam((48, 45, 80), (48, 22, 66), 5, R)
    g.beam((54, 44, 82), (54, 23, 69), 1.6, BK)
    g.cylinder((48, 22, 66), 6.5, 18, 0, ST)
    g.roundbox((35, 16, 60), (61, 24, 70), 2, BK)
    for sign in (-1, 1):
        g.beam((48+sign*11, 18, 65), (48+sign*19, 8, 61), 3, ST)
        g.beam((48+sign*19, 8, 61), (48+sign*14, 3, 59), 3, BK)
        g.cylinder((48+sign*12, 19, 65), 3.3, 4, 0, AL)
    # Separate sensor mast and single optical lens, deliberately not a character face.
    g.cylinder((48, 95, 64), 5, 31, 2, AL)
    g.cylinder((48, 95, 77), 10, 5, 2, BK)
    g.roundbox((33, 83, 79), (63, 106, 98), 4, R)
    g.roundbox((32, 81, 79), (64, 87, 99), 3, IV)
    g.roundbox((37, 79, 83), (59, 84, 95), 2, DK)
    g.cylinder((48, 78, 89), 5.5, 3, 1, GL)
    g.cylinder((48, 76, 89), 2.7, 2, 1, GH)
    g.box((43, 89, 98), (53, 101, 101), ST)
    g.cylinder((65, 106, 71), 1.8, 43, 2, ST)
    g.cylinder((65, 106, 94), 3.3, 7, 2, AM)
    g.cylinder((65, 106, 98), 2.6, 2, 2, LP)
    return Asset('rescue_robot', 'Tracked rescue manipulator', g, .025,
                 ['Single-lens camera pod and separate articulated mechanical manipulator; no character face.',
                  'Two track loops, five road wheels per side and an open two-jaw gripper.',
                  'No manual half corrections.'])


def fire_station():
    g = Grid((128, 96, 120), PALETTE)
    # The foundation slab belongs to the building, with no landscape or diorama.
    g.roundbox((3, 3, 1), (125, 91, 6), 1, CO)
    g.box((5, 10, 6), (99, 87, 73), R)
    g.box((10, 17, 7), (94, 82, 65), 0)
    g.box((12, 8, 7), (46, 19, 62), 0)
    g.box((56, 8, 7), (90, 19, 62), 0)
    # Pale inner walls make both empty, deep bays legible.
    g.box((10, 18, 7), (12, 82, 63), IN)
    g.box((92, 18, 7), (94, 82, 63), IN)
    g.box((12, 80, 7), (92, 82, 63), IN)
    # Stone piers and shutter lintels frame the wide clear entrances.
    for xa, xb in ((5, 12), (46, 56), (90, 99)):
        g.box((xa, 8, 6), (xb, 17, 65), IV)
        g.box((xa, 7, 6), (xb, 18, 16), CO)
    for xa, xb in ((11, 47), (55, 91)):
        g.roundbox((xa-2, 7, 61), (xb+2, 18, 69), 2, IV)
        g.box((xa+2, 9, 59), (xb-2, 14, 63), ST)
        for z in (59, 61):
            g.box((xa+2, 8, z), (xb-2, 10, z+1), AL)
    g.box((5, 9, 68), (99, 88, 72), IV)
    # Very restrained brick courses and corner stones, never a noisy checkerboard.
    for z in range(20, 68, 10):
        g.box((97, 18, z), (100, 87, z+1), RD)
        g.box((5, 9, z), (12, 11, z+1), CO)
        g.box((46, 9, z), (56, 11, z+1), CO)
    # Gabled roof: native sloped silhouette with a hollow volume below it.
    roof_z = 88 - np.abs(g.x - 52) * .29
    roof_region = (g.x >= 2) & (g.x < 102) & (g.y >= 7) & (g.y < 90)
    g.data[roof_region & (g.z >= roof_z-4) & (g.z < roof_z)] = ST
    gable = (g.x >= 5) & (g.x < 99) & (((g.y >= 10) & (g.y < 15)) | ((g.y >= 83) & (g.y < 87)))
    g.data[gable & (g.z >= 72) & (g.z < roof_z-4)] = R
    # Ivory stepped gable fascia remains a thin trim over the slate roof.
    g.data[roof_region & (g.y < 10) & (g.z >= roof_z-3) & (g.z < roof_z+1)] = IV
    g.box((49, 10, 85), (55, 88, 89), ST)
    for y in range(18, 88, 12):
        g.data[roof_region & (g.y >= y) & (g.y < y+1) & (g.z >= roof_z-1) & (g.z < roof_z)] = BK
    g.box((44, 9, 74), (60, 12, 81), DK)
    for x in range(45, 59, 4):
        g.box((x, 8, 75), (x+1, 10, 80), AL)
    # Genuine bay equipment sits at the back, leaving the full entry passages clear.
    g.roundbox((17, 74, 7), (31, 80, 29), 1, R)
    g.box((20, 73, 11), (28, 75, 23), ST)
    for x in (64, 86):
        g.box((x, 74, 7), (x+2, 80, 43), ST)
    for z in (13, 27, 41):
        g.box((64, 74, z), (88, 80, z+2), AL)
    for x in (68, 78):
        g.roundbox((x, 75, 29), (x+6, 80, 37), 1, AM)
    for x in (17, 41, 61, 85):
        g.box((x, 4, 6), (x+2, 69, 7), AM)
    for x in (8, 51, 96):
        g.cylinder((x, 5, 13), 2.2, 14, 2, AM)
        g.cylinder((x, 5, 16), 2.3, 3, 2, BK)
    # Attached office and hose-drying tower are structurally part of the station.
    g.roundbox((98, 31, 6), (124, 87, 49), 1, R)
    g.box((98, 31, 6), (124, 87, 14), CO)
    g.box((97, 28, 47), (126, 89, 52), IV)
    g.box((105, 29, 8), (119, 33, 39), IV)
    g.box((108, 28, 9), (116, 31, 36), ST)
    g.box((109, 27, 21), (115, 30, 34), GL)
    g.box((114, 26, 17), (116, 29, 19), AL)
    for ya, yb in ((58, 69), (74, 83)):
        g.box((123, ya, 20), (126, yb, 38), IV)
        g.box((124, ya+2, 23), (127, yb-2, 35), GL)
    g.box((101, 46, 49), (123, 71, 110), R)
    g.box((100, 44, 49), (105, 72, 110), IV)
    g.box((119, 44, 49), (124, 72, 110), IV)
    g.box((104, 44, 60), (120, 49, 105), DK)
    for x in (108, 116):
        g.beam((x, 43, 103), (x, 43, 68), 2, HO)
        g.beam((x, 43, 68), (x-2, 41, 61), 2, HO)
        for z in (72, 98):
            g.cylinder((x, 43, z), 2.5, 3, 2, AL)
    g.box((98, 41, 108), (126, 75, 113), IV)
    for x in (101, 123):
        g.box((x, 44, 113), (x+2, 72, 118), ST)
    for y in (44, 70):
        g.box((101, y, 115), (125, y+2, 118), ST)
    for x in (28, 70):
        g.box((x, 5, 67), (x+7, 10, 71), BK)
        g.box((x+1, 4, 67), (x+6, 7, 70), LP)
    return Asset('fire_station', 'Two-bay rescue station', g, .06,
                 ['Two open vehicle bays, pale interior, back-wall tools, office and hose-drying tower.',
                  'Foundation and marked bay floor are real building structure, not a common diorama base.',
                  'No manual half corrections; both entrances retain broad clear central passages.'])


def rotor_blade(g, a, b, width, zlo, zhi, color):
    ax, ay = a; bx, by = b
    dx, dy = bx-ax, by-ay
    t = ((g.x-ax)*dx + (g.y-ay)*dy) / (dx*dx+dy*dy)
    d2 = (g.x-(ax+np.clip(t, 0, 1)*dx))**2 + (g.y-(ay+np.clip(t, 0, 1)*dy))**2
    g.data[(d2 <= width*width) & (g.z >= zlo) & (g.z < zhi)] = color


def rescue_helicopter():
    g = Grid((128, 128, 84), PALETTE)
    # Rounded stepped fuselage and forward wraparound opaque blue cockpit.
    body = ((g.x-64)/20)**2 + ((g.y-48)/35)**2 + ((g.z-40)/22)**2 <= 1
    g.data[body] = R
    g.data[body & (g.z >= 29) & (g.z < 33)] = IV
    cockpit = body & (g.y < 42) & (g.z >= 34)
    g.data[cockpit] = GL
    g.data[cockpit & (g.z >= 48) & (g.z < 51) & (g.y < 28)] = GH
    g.data[cockpit & ((np.abs(g.x-64) < 1.8) | ((g.y >= 38) & (g.y < 42)) | (g.z < 37))] = IV
    # Door opening and cabin interior; the right side is open for rescue loading.
    g.box((55, 44, 28), (86, 65, 53), 0)
    g.box((55, 44, 28), (58, 65, 53), DK)
    g.box((58, 44, 28), (82, 65, 31), AL)
    g.box((80, 43, 30), (84, 46, 54), IV)
    g.box((78, 63, 30), (83, 66, 54), IV)
    g.box((78, 44, 52), (84, 65, 55), IV)
    g.roundbox((54, 49, 58), (75, 77, 66), 4, R)
    for x in (57, 62, 67, 72):
        g.box((x, 63, 64), (x+2, 73, 67), BK)
    # Tapered boom, vertical fin and a separate mechanical tail rotor.
    g.cone((64, 95, 44), 9, 3.2, 50, 1, R)
    g.box((62, 110, 43), (66, 123, 64), R)
    fin = (g.x >= 62) & (g.x < 66) & (g.y >= 108) & (g.y < 124) & (g.z >= 51) & (g.z < 69) & (g.y >= 107+(g.z-51)*.4)
    g.data[fin] = R
    g.box((62, 114, 58), (66, 123, 62), IV)
    g.roundbox((47, 107, 44), (81, 114, 49), 2, IV)
    g.cylinder((69, 116, 55), 3.5, 7, 0, ST)
    for a, b in (((72, 108, 47), (72, 124, 63)), ((72, 108, 63), (72, 124, 47))):
        g.beam(a, b, 2, BK)
    for y, z in ((108, 47), (124, 63), (108, 63), (124, 47)):
        g.ellipsoid((72, y, z), (2, 2.5, 2.5), AM)
    g.cylinder((74, 116, 55), 2.3, 2, 0, AL)
    # Independent skids and their four braced connections, clear beneath the body.
    for x, sign in ((44, -1), (84, 1)):
        g.beam((x, 18, 7), (x, 85, 7), 2.4, ST)
        g.beam((x, 18, 7), (x, 12, 12), 2.4, ST)
        for y in (31, 65):
            g.beam((64+sign*16, y, 25), (x, y+2, 9), 2.3, ST)
    # Main rotor: four planar blades, visibly spaced above the cabin.
    g.cylinder((64, 52, 69), 3.4, 17, 2, ST)
    g.cylinder((64, 52, 73), 7, 3, 2, AL)
    rotor_blade(g, (9, 14), (119, 90), 3, 77, 80, BK)
    rotor_blade(g, (9, 90), (119, 14), 3, 77, 80, BK)
    for a, b in (((9, 14), (15, 18)), ((113, 86), (119, 90)),
                 ((9, 90), (15, 86)), ((113, 18), (119, 14))):
        rotor_blade(g, a, b, 3.1, 77, 80, AM)
    g.cylinder((64, 52, 80), 5, 4, 2, R)
    # Outboard drum, cable and open rescue hook, kept outside the skid footprint.
    g.beam((78, 54, 56), (91, 54, 56), 2.3, ST)
    g.cylinder((90, 54, 51), 5, 9, 1, AL)
    for y in (49, 58):
        g.cylinder((90, y, 51), 6, 2, 1, ST)
    for y in (51, 54, 57):
        g.torus((90, y, 51), 4.5, .8, 1, IV)
    g.beam((93, 54, 49), (93, 54, 20), 1.3, DK)
    g.beam((93, 54, 22), (93, 54, 17), 1.8, AM)
    g.torus((93, 54, 13), 4, 1.7, 0, AM)
    g.box((90, 49, 14), (97, 53, 19), 0)
    for x in (55, 71):
        g.roundbox((x-3, 17, 23), (x+3, 22, 28), 1, ST)
        g.box((x-2, 16, 24), (x+2, 18, 27), LP)
    return Asset('rescue_helicopter', 'Winch rescue helicopter', g, .05,
                 ['Rounded cockpit, true side opening, separate skids, four main rotor blades and tail rotor.',
                  'Outboard static winch cable with an open hook; no animation or operational simulation.',
                  'No manual half corrections.'])


def make_assets():
    return [fire_engine(), rescue_robot(), fire_station(), rescue_helicopter()]


if __name__ == '__main__':
    run_theme(Path(__file__).resolve().parent, make_assets())
