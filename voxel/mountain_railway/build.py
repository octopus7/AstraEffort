"""Five independently authored mountain railway voxel models."""
from pathlib import Path
import sys
import math
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_tools'))
from voxelkit import Grid, Asset, run_theme

PALETTE = [
    (0, 0, 0, 0),
    (45, 51, 48, 255), (65, 74, 68, 255), (97, 109, 97, 255),
    (146, 154, 136, 255), (62, 91, 61, 255), (84, 113, 77, 255),
    (43, 68, 47, 255), (219, 212, 181, 255), (239, 229, 198, 255),
    (159, 65, 43, 255), (187, 89, 59, 255), (117, 48, 37, 255),
    (145, 101, 55, 255), (178, 129, 72, 255), (101, 73, 45, 255),
    (146, 148, 132, 255), (182, 178, 151, 255), (111, 119, 109, 255),
    (116, 150, 155, 255), (160, 183, 177, 255), (235, 189, 84, 255),
    (250, 227, 166, 255), (184, 190, 166, 255), (30, 36, 34, 255),
]
DARK, STEEL, METAL, METAL_L = 1, 2, 3, 4
GREEN, GREEN_L, GREEN_D, IVORY, IVORY_L = 5, 6, 7, 8, 9
RED, RED_L, RED_D = 10, 11, 12
TIMBER, TIMBER_L, TIMBER_D = 13, 14, 15
STONE, STONE_L, MORTAR = 16, 17, 18
GLASS, GLASS_L, AMBER, LAMP, BOLT, RUBBER = 19, 20, 21, 22, 23, 24


def rolling_bogie(grid, y):
    """Substantial two-axle bogie, shared only by this theme's two new vehicles."""
    grid.box((10, y - 14, 10), (46, y + 14, 16), DARK)
    grid.cylinder((28, y, 17), 7, 6, 2, STEEL)
    for axle_y in (y - 9, y + 9):
        grid.cylinder((28, axle_y, 9), 2.5, 37, 0, STEEL)
        for x in (11, 45):
            grid.cylinder((x, axle_y, 9), 8, 6, 0, RUBBER)
            grid.cylinder((x, axle_y, 9), 6, 7.5, 0, STEEL)
            grid.cylinder((x, axle_y, 9), 3, 9, 0, METAL)
    for x in (6, 44):
        grid.roundbox((x, y - 15, 10), (x + 6, y + 15, 15), 1.5, STEEL)
        for axle_y in (y - 9, y + 9):
            grid.box((x - 1, axle_y - 3, 8), (x + 7, axle_y + 3, 14), METAL)
        grid.box((x, y - 4, 8), (x + 6, y + 4, 16), DARK)
        for z in (9, 12, 15):
            grid.box((x - 1, y - 4, z), (x + 7, y + 4, z + 2), METAL)


def train_couplings(grid):
    for y0, y1 in ((0, 11), (117, 128)):
        grid.box((23, y0, 12), (33, y1, 18), STEEL)
        end = 1 if y0 == 0 else 127
        grid.box((21, end - 1, 11), (35, end + 1, 20), DARK)
        grid.box((26, end - 2, 13), (30, end + 2, 18), 0)
    for y in (8, 120):
        for x in (12, 44):
            grid.cylinder((x, y, 18), 3.2, 7, 1, STEEL)
            grid.cylinder((x, y - 3 if y < 64 else y + 3, 18), 4, 2.5, 1, METAL)


def locomotive():
    g = Grid((56, 128, 76), PALETTE)
    rolling_bogie(g, 31)
    rolling_bogie(g, 96)
    g.roundbox((8, 8, 17), (48, 120, 24), 2, STEEL)
    g.roundbox((18, 51, 7), (38, 77, 17), 3, DARK)
    g.cylinder((15, 63, 12), 3.5, 19, 1, METAL)
    # A rounded low diesel nose leads into a sloped cab face and long engine body.
    g.roundbox((7, 8, 22), (49, 38, 44), 7, GREEN)
    g.roundbox((7, 34, 22), (49, 116, 59), 5, GREEN)
    cab_front = 25 + 0.5 * (g.z - 40)
    wedge = (g.x >= 7) & (g.x < 49) & (g.z >= 40) & (g.z < 59) & (g.y >= cab_front) & (g.y < 45)
    g.data[wedge] = IVORY
    painted = g.data > 0
    g.data[painted & (g.z >= 37) & (g.z < 40)] = RED
    g.data[painted & (g.z >= 40) & (g.z < 45)] = IVORY
    g.roundbox((6, 31, 57), (50, 117, 65), 4, GREEN)
    g.roundbox((10, 35, 63), (46, 113, 67), 3, GREEN_L)
    # Two dark, recessed panes follow the cab slope instead of projecting flat boxes.
    for xa, xb in ((11, 25), (31, 45)):
        window = (g.x >= xa) & (g.x < xb) & (g.z >= 46) & (g.z < 57) & (g.y >= cab_front) & (g.y < cab_front + 3)
        g.data[window] = DARK
        g.data[window & (g.x >= xa + 2) & (g.x < xb - 2) & (g.z >= 48) & (g.z < 55)] = GLASS_L
    # Nose lamps and protective pilot/buffer beam.
    for x, z, rad in ((28, 38, 3.4), (14, 28, 2.8), (42, 28, 2.8)):
        g.cylinder((x, 8, z), rad + 1, 4, 1, DARK)
        g.cylinder((x, 5, z), rad, 2.5, 1, LAMP)
    g.roundbox((8, 5, 20), (48, 11, 25), 1.5, RED_D)
    g.box((15, 8, 10), (41, 13, 17), STEEL)
    # Cab side windows, handles, ladders and long horizontal louver banks.
    for x0 in (5, 48):
        g.box((x0, 35, 45), (x0 + 3, 47, 58), IVORY)
        g.box((x0 - 1, 37, 47), (x0 + 4, 45, 56), GLASS)
        g.box((x0, 46, 27), (x0 + 3, 52, 55), GREEN_D)
        g.box((x0 - 1, 48, 35), (x0 + 4, 50, 44), METAL_L)
        for y0, y1 in ((57, 77), (81, 101)):
            g.box((x0 - 1, y0, 29), (x0 + 4, y1, 55), DARK)
            for zz in range(31, 55, 5):
                g.box((x0 - 2, y0 + 1, zz), (x0 + 5, y1 - 1, zz + 2), GREEN_L)
        g.box((x0, 103, 29), (x0 + 3, 112, 55), GREEN_D)
        g.box((x0 - 1, 106, 38), (x0 + 4, 109, 42), METAL)
        g.box((x0, 52, 56), (x0 + 3, 112, 59), IVORY)
        for yy, zz in ((44, 18), (45, 23)):
            g.box((x0 - 1, yy, zz), (x0 + 4, yy + 10, zz + 3), METAL)
        g.box((x0, 15, 24), (x0 + 3, 115, 27), RED)
    # Roof cooling fan, grille and exhaust stack.
    g.cylinder((28, 68, 67), 8.5, 3, 2, DARK)
    g.cylinder((28, 68, 69), 3, 2, 2, METAL)
    for a in np.linspace(0, math.pi * 2, 6, endpoint=False):
        g.beam((28, 68, 68), (28 + 7 * math.cos(a), 68 + 7 * math.sin(a), 68), 1.2, STEEL)
    g.box((14, 101, 65), (42, 112, 68), DARK)
    for xx in range(16, 42, 5):
        g.box((xx, 102, 67), (xx + 2, 111, 69), METAL)
    g.cylinder((28, 90, 69), 3.5, 10, 2, STEEL)
    g.cylinder((28, 90, 74), 4.5, 2, 2, DARK)
    # Rear maintenance access is independent of the front cab.
    g.roundbox((19, 113, 26), (37, 120, 56), 2, IVORY)
    g.box((22, 118, 28), (34, 122, 53), GREEN_D)
    g.box((24, 121, 43), (32, 124, 51), GLASS)
    g.box((31, 121, 34), (35, 124, 38), METAL)
    for xx in (17, 39):
        g.beam((xx, 119, 30), (xx, 119, 51), 1.4, IVORY)
    for xx in (11, 45):
        g.cylinder((xx, 117, 31), 2.3, 4, 1, RED_L)
    train_couplings(g)
    return Asset('locomotive', 'Mountain diesel locomotive', g, voxel_size=0.06, notes=[
        'Rounded low diesel nose, sloped twin-pane cab, two physical two-axle bogies, large horizontal side louvers, roof fan/exhaust, buffers and open coupler sockets.',
        'Rear maintenance door, handrails and lamps are authored. Glazing is an opaque palette color. No vehicle rig or drivetrain simulation.'
    ])


def passenger_car():
    g = Grid((56, 128, 72), PALETTE)
    rolling_bogie(g, 31)
    rolling_bogie(g, 97)
    g.roundbox((8, 9, 17), (48, 119, 23), 2, STEEL)
    g.roundbox((6, 10, 22), (50, 118, 61), 6, GREEN)
    occupied = g.data > 0
    g.data[occupied & (g.z >= 34) & (g.z < 37)] = RED
    g.data[occupied & (g.z >= 37)] = IVORY
    # Large panes leave substantial structural divisions in the native coarse model.
    for x0 in (4, 48):
        for ya, yb in ((19, 35), (39, 55), (59, 75), (79, 95), (99, 113)):
            g.box((x0, ya, 39), (x0 + 4, yb, 58), DARK)
            g.box((x0 - 1, ya + 2, 41), (x0 + 5, yb - 2, 56), GLASS)
            g.box((x0 - 1, ya + 2, 52), (x0 + 5, yb - 2, 54), METAL_L)
        g.box((x0, 16, 24), (x0 + 4, 114, 27), GREEN_L)
    # Rounded roof with service housings, formed directly in voxels.
    g.roundbox((5, 9, 57), (51, 119, 68), 5.5, STEEL)
    g.roundbox((11, 15, 65), (45, 113, 70), 2.5, METAL)
    for y0 in (35, 85):
        g.roundbox((20, y0, 68), (36, y0 + 15, 72), 1.5, DARK)
        for xx in (23, 28, 33):
            g.box((xx, y0 + 2, 71), (xx + 2, y0 + 13, 72), METAL)
    # Paired end vestibules with doors, rubber gangway surrounds and sturdy grab rails.
    for ya, yb, face in ((5, 13, 5), (115, 123, 122)):
        g.roundbox((16, ya, 23), (40, yb, 60), 3, DARK)
        g.box((19, ya - 1, 24), (37, yb + 1, 57), RED_D)
        g.box((22, ya - 2, 25), (34, yb + 2, 55), RED)
        g.box((24, ya - 3, 40), (32, yb + 3, 53), GLASS_L)
        g.box((31, face - 2, 32), (35, face + 3, 37), METAL_L)
        for xx in (13, 43):
            g.beam((xx, face, 28), (xx, face, 54), 1.5, IVORY)
        g.box((16, ya - 1, 19), (40, yb + 1, 23), METAL)
    # Underfloor battery and air reservoirs remain distinct from the bogies.
    g.roundbox((18, 52, 10), (39, 73, 17), 2, DARK)
    g.cylinder((13, 66, 12), 3.2, 20, 1, METAL)
    train_couplings(g)
    return Asset('passenger_car', 'Mountain passenger coach', g, voxel_size=0.065, notes=[
        'Five substantial side windows per side, rounded roof, two separate two-axle bogies, two end vestibule doors, gangway surrounds, grab rails and couplings.',
        'Windows are opaque flat palette glazing; no transparent passenger interior, rig or animation is claimed.'
    ])


def station():
    g = Grid((128, 96, 96), PALETTE)
    # The station includes its own small platform, masonry courses and inset access steps.
    g.roundbox((2, 0, 0), (126, 92, 14), 2, MORTAR)
    for z0 in (1, 7):
        for xx in range(3 - (6 if z0 > 1 else 0), 126, 12):
            xa, xb = max(3, xx + 1), min(125, xx + 11)
            if xb > xa:
                g.box((xa, 0, z0), (xb, 5, z0 + 5), STONE)
                g.box((xa, 87, z0), (xb, 92, z0 + 5), STONE)
        for yy in range(1, 92, 12):
            g.box((2, yy, z0), (7, min(yy + 10, 91), z0 + 5), STONE)
            g.box((121, yy, z0), (126, min(yy + 10, 91), z0 + 5), STONE)
    g.box((3, 1, 13), (125, 91, 15), STONE_L)
    for xx in range(8, 125, 13):
        g.box((xx, 4, 14), (xx + 1, 90, 15), STONE)
    g.box((3, 0, 14), (125, 4, 16), AMBER)
    g.box((108, 0, 0), (128, 28, 17), 0)
    for i in range(4):
        g.box((108, i * 7, 0), (127, (i + 1) * 7, 3 + i * 4), STONE_L)
    # Rear room leaves a real sheltered front platform and open left bay.
    g.box((41, 42, 15), (109, 83, 19), TIMBER)
    g.box((41, 42, 18), (47, 83, 63), IVORY)
    g.box((103, 42, 18), (109, 83, 63), IVORY)
    g.box((41, 42, 18), (109, 48, 63), IVORY)
    g.box((41, 77, 18), (109, 83, 63), IVORY)
    for zz in (22, 29):
        for wall in (((41, 42, zz), (109, 48, zz + 6)), ((103, 42, zz), (109, 83, zz + 6)), ((41, 77, zz), (109, 83, zz + 6))):
            g.box(wall[0], wall[1], GREEN)
    for xx in range(43, 109, 6):
        g.box((xx, 41, 18), (xx + 2, 48, 34), GREEN_D)
        g.box((xx, 77, 18), (xx + 2, 84, 34), GREEN_D)
    for xx, yy in ((18, 18), (109, 18), (18, 78), (109, 78)):
        g.box((xx - 3, yy - 3, 15), (xx + 3, yy + 3, 64), TIMBER_D)
        g.box((xx - 4, yy - 4, 15), (xx + 4, yy + 4, 34), GREEN)
        g.beam((xx, yy, 51), (xx + (9 if xx < 64 else -9), yy, 63), 2, TIMBER)
    g.box((15, 15, 59), (113, 23, 65), TIMBER)
    g.box((15, 75, 59), (113, 83, 65), TIMBER)
    # Broad eaves, timber gables and regular green roof courses.
    roof_height = 91 - 0.55 * np.abs(g.x - 64)
    roof = (g.x >= 6) & (g.x < 122) & (g.y >= 10) & (g.y < 94) & (g.z >= roof_height - 5) & (g.z < roof_height + 1)
    gable = (g.x >= 18) & (g.x < 110) & (g.z >= 63) & (g.z < roof_height - 4)
    g.data[gable & (((g.y >= 15) & (g.y < 22)) | ((g.y >= 77) & (g.y < 84)))] = TIMBER
    g.data[roof] = GREEN
    g.data[roof & (np.mod(np.abs(g.x - 64), 8) < 1.2)] = GREEN_L
    g.data[roof & (np.mod(g.y + 5 * np.floor(np.abs(g.x - 64) / 8), 14) < 1.2)] = GREEN_D
    for yy in (10, 90):
        fascia = (g.x >= 8) & (g.x < 120) & (g.y >= yy) & (g.y < yy + 4) & (g.z >= roof_height - 8) & (g.z < roof_height - 4)
        g.data[fascia] = TIMBER_L
    g.roundbox((60, 9, 88), (68, 95, 94), 2, GREEN_L)
    # Main front window, entrance and a plain physical station sign panel.
    g.box((49, 39, 34), (83, 45, 57), TIMBER_D)
    g.box((52, 38, 37), (80, 42, 54), GLASS)
    for xx in (60, 70):
        g.box((xx, 37, 36), (xx + 3, 43, 55), IVORY)
    g.box((51, 37, 44), (81, 43, 47), IVORY)
    g.box((89, 39, 15), (106, 46, 55), TIMBER_D)
    g.box((92, 38, 17), (103, 42, 53), RED)
    g.box((94, 37, 34), (101, 40, 49), GLASS_L)
    g.box((101, 36, 24), (105, 40, 29), METAL)
    g.box((47, 19, 55), (85, 24, 67), GREEN_D)
    g.box((50, 18, 57), (82, 22, 65), IVORY_L)
    # Bench has separate seat, backrest slats, legs and arm rests.
    for xx in (48, 75):
        for yy in (28, 35):
            g.box((xx, yy, 15), (xx + 3, yy + 3, 25), STEEL)
    g.box((44, 27, 23), (82, 38, 26), TIMBER)
    for zz in (29, 34, 39):
        g.box((44, 36, zz), (82, 39, zz + 3), TIMBER_L)
    for xx in (45, 78):
        g.box((xx, 36, 24), (xx + 3, 40, 42), TIMBER_D)
        g.box((xx, 27, 29), (xx + 3, 39, 32), TIMBER_D)
    for xx, yy in ((23, 21), (87, 38)):
        g.box((xx - 3, yy - 3, 50), (xx + 3, yy + 3, 58), DARK)
        g.box((xx - 2, yy - 4, 52), (xx + 2, yy + 2, 56), LAMP)
    # A glazed side entrance remains visible beside the deep porch roof and posts.
    g.box((107, 54, 15), (112, 74, 56), TIMBER_D)
    g.box((111, 57, 17), (115, 71, 53), RED)
    g.box((114, 59, 35), (117, 69, 50), GLASS_L)
    g.box((115, 67, 25), (118, 70, 30), METAL)
    g.box((108, 53, 15), (121, 75, 18), STONE_L)
    g.box((65, 80, 16), (82, 86, 51), TIMBER_D)
    g.box((68, 84, 18), (79, 88, 49), GREEN_D)
    g.box((70, 87, 35), (77, 90, 46), GLASS)
    g.box((76, 87, 26), (80, 90, 30), METAL)
    g.box((92, 65, 68), (102, 75, 94), STONE)
    for zz in (73, 80, 87):
        g.box((91, 64, zz), (103, 76, zz + 1), MORTAR)
    g.box((90, 63, 93), (104, 77, 96), RED)
    return Asset('station', 'Sheltered mountain station', g, voxel_size=0.075, notes=[
        'Compact station with its own masonry platform and access steps, broad green eaves, an open sheltered bay, bench, entrance, large window and physical blank sign panel.',
        'Roof/chimney, rear access and side glazing are independently authored. All lamps/glazing use opaque palette colors; no illumination or text decal is claimed.'
    ])


def railway_bridge():
    g = Grid((128, 56, 64), PALETTE)
    g.box((4, 8, 5), (124, 48, 50), STONE)
    for xa, xb in ((1, 33), (95, 127)):
        g.roundbox((xa, 3, 0), (xb, 53, 7), 1, STONE)
    # Deterministic masonry divisions apply to actual occupied arch/abutment cells.
    blocks = g.data > 0
    mortar = (np.mod(g.z, 7) < 1) | (np.mod(g.x + (np.floor(g.z / 7) % 2) * 6, 12) < 1)
    g.data[blocks & mortar] = MORTAR
    curve = 18 + 26 * np.sqrt(np.clip(1 - ((g.x - 64) / 38) ** 2, 0, 1))
    opening = (g.x >= 26) & (g.x <= 102) & (g.y >= 0) & (g.z < curve)
    g.data[opening] = 0
    # Light voussoirs follow the stepped curved opening without a hidden filled core.
    archband = (g.x >= 25) & (g.x <= 103) & (g.y >= 7) & (g.y < 49) & (g.z >= curve) & (g.z < curve + 4)
    g.data[archband] = STONE_L
    angle = np.arctan2((g.z - 18) / 26, (g.x - 64) / 38)
    g.data[archband & (np.mod(np.floor(angle * 12 / math.pi), 2) == 0)] = IVORY
    # Deck, parapet caps, wooden cross sleepers and two uninterrupted steel rail heads.
    g.box((2, 7, 49), (126, 49, 54), STONE_L)
    g.box((3, 12, 53), (125, 44, 55), MORTAR)
    for yy in (6, 47):
        g.box((3, yy, 51), (125, yy + 4, 57), STONE_L)
    for xx in range(4, 127, 10):
        g.box((xx, 15, 54), (min(xx + 5, 128), 42, 58), TIMBER_D)
        g.box((xx, 15, 57), (min(xx + 5, 128), 42, 59), TIMBER)
        for yy in (19, 35):
            g.box((xx, yy - 2, 58), (min(xx + 5, 128), yy + 4, 60), METAL)
    for yy in (20, 36):
        g.box((0, yy - 3, 58), (128, yy + 3, 60), STEEL)
        g.box((0, yy - 1, 59), (128, yy + 1, 63), DARK)
        g.box((0, yy - 2, 62), (128, yy + 2, 64), METAL_L)
    for xa, xb in ((4, 23), (105, 124)):
        for yy in (5, 46):
            g.box((xa, yy, 50), (xb, yy + 5, 57), IVORY)
    return Asset('railway_bridge', 'Open-arch masonry railway bridge', g, voxel_size=0.10, notes=[
        'Two broad masonry abutments and a genuinely empty, stepped elliptical arch beneath the railway deck; no floor or backing closes the opening.',
        'Paired continuous rail heads, webs/flanges, individual timber sleepers and clips are actual native occupied cells.',
        'Architectural visualization only; no structural engineering or track-gauge compatibility claim.'
    ])


def cable_car():
    g = Grid((80, 72, 128), PALETTE)
    g.roundbox((10, 10, 3), (70, 62, 76), 10, GREEN)
    cabin = g.data > 0
    g.data[cabin & (g.z >= 30) & (g.z < 35)] = RED
    g.data[cabin & (g.z >= 35)] = IVORY
    # Curved cabin surfaces carry large recessed panes with substantial dark frames.
    front = cabin & (g.y < 16) & (g.x >= 15) & (g.x < 65) & (g.z >= 37) & (g.z < 69)
    g.data[front] = DARK
    fglass = front & (g.x >= 18) & (g.x < 62) & (g.z >= 40) & (g.z < 66)
    g.data[fglass & (g.y < 12)] = 0
    g.data[fglass & (g.y >= 12)] = GLASS_L
    g.data[front & (g.x >= 38) & (g.x < 42)] = DARK
    for side in ('left', 'right'):
        smask = cabin & ((g.x < 16) if side == 'left' else (g.x >= 64)) & (g.y >= 17) & (g.y < 56) & (g.z >= 37) & (g.z < 69)
        g.data[smask] = DARK
        g.data[smask & (g.y >= 20) & (g.y < 53) & (g.z >= 40) & (g.z < 66)] = GLASS
        g.data[smask & (g.y >= 34) & (g.y < 38)] = DARK
    back = cabin & (g.y >= 56) & (g.x >= 18) & (g.x < 62) & (g.z >= 38) & (g.z < 68)
    g.data[back] = DARK
    g.data[back & (g.x >= 21) & (g.x < 59) & (g.z >= 41) & (g.z < 65)] = GLASS
    g.data[back & (g.x >= 38) & (g.x < 42)] = DARK
    g.roundbox((10, 10, 71), (70, 62, 80), 4, IVORY_L)
    g.roundbox((16, 16, 78), (64, 56, 83), 2, IVORY)
    # Paired sliding side doors stand proud of the capsule and retain their split line.
    g.roundbox((66, 25, 14), (73, 50, 69), 2, RED_D)
    g.box((71, 27, 17), (75, 48, 67), RED)
    g.box((70, 36, 16), (76, 39, 68), DARK)
    for ya, yb in ((28, 35), (40, 47)):
        g.box((73, ya, 40), (76, yb, 65), DARK)
        g.box((75, ya + 1, 43), (78, yb - 1, 62), GLASS_L)
    for yy in (33, 40):
        g.box((75, yy, 29), (78, yy + 2, 37), METAL)
    g.box((66, 24, 12), (77, 51, 16), METAL)
    for xx in (21, 59):
        g.cylinder((xx, 11, 23), 3.5, 4, 1, DARK)
        g.cylinder((xx, 8, 23), 2.5, 2, 1, LAMP)
    g.box((32, 60, 12), (49, 65, 29), GREEN_D)
    g.box((43, 64, 18), (47, 68, 22), METAL)
    # Separate load bracket, braced overhead hanger and four grooved trolley wheels.
    g.roundbox((22, 22, 82), (58, 50, 87), 1.5, DARK)
    for xx in (25, 55):
        for yy in (25, 47):
            g.cylinder((xx, yy, 87), 2, 2, 2, BOLT)
            g.beam((xx, yy, 86), (40, 36, 103), 2.4, STEEL)
    g.box((35, 31, 86), (45, 41, 113), DARK)
    g.box((33, 29, 98), (47, 43, 103), METAL)
    g.box((29, 21, 109), (51, 51, 114), STEEL)
    for xx in (28, 52):
        g.beam((xx, 21, 113), (xx, 51, 113), 2, DARK)
        for yy in (24, 48):
            g.cylinder((xx, yy, 119), 7, 5, 0, RUBBER)
            g.cylinder((xx, yy, 119), 5.5, 6, 0, STEEL)
            g.cylinder((xx, yy, 119), 3, 8, 0, IVORY)
            g.cylinder((xx, yy, 119), 1.4, 9, 0, METAL)
        g.beam((xx, 8, 126), (xx, 64, 126), 1.3, DARK)
    return Asset('cable_car', 'Alpine capsule cable car', g, voxel_size=0.055, notes=[
        'Rounded capsule cabin with large recessed opaque panes, split side doors, threshold and front lamps; a separate braced hanger supports four trolley pulleys and short cable segments.',
        'Rear service panel and glazing are authored. Static visualization only: no suspended motion, cable dynamics, animation or transparent interior.'
    ])


def make_assets():
    return [locomotive(), passenger_car(), station(), railway_bridge(), cable_car()]


if __name__ == '__main__':
    run_theme(Path(__file__).resolve().parent, make_assets())
