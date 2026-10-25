"""New recycling machinery and architecture, authored directly as native voxel occupancy."""
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_tools'))
from voxelkit import Grid, Asset, run_theme

COLORS = [
    (0, 0, 0, 0),
    (39, 101, 82, 255),    # 1 deep recycling green
    (64, 129, 103, 255),   # 2 upper green
    (26, 70, 59, 255),     # 3 recessed green
    (226, 221, 194, 255),  # 4 warm cladding
    (246, 241, 218, 255),  # 5 ivory trim
    (45, 50, 52, 255),     # 6 belt and tire charcoal
    (75, 89, 93, 255),     # 7 steel frame
    (143, 153, 150, 255),  # 8 silver hardware
    (237, 185, 48, 255),   # 9 safety yellow
    (191, 129, 34, 255),   # 10 recessed yellow
    (58, 81, 91, 255),     # 11 dark blue glazing / screen
    (105, 133, 143, 255),  # 12 glass highlight
    (177, 73, 48, 255),    # 13 tail lamps / stop control
    (163, 116, 65, 255),   # 14 compacted cardboard
    (197, 151, 91, 255),   # 15 lighter cardboard layers
]


def truck_tire(g, x, y):
    # Broad tire rings and recessed metal hubs, all voxel operations.
    g.cylinder((x, y, 12), 11, 10, 0, 6)
    g.cylinder((x, y, 12), 11.6, 5, 0, 6)
    side = -1 if x < 37 else 1
    g.cylinder((x + 5 * side, y, 12), 7, 2, 0, 7)
    g.cylinder((x + 6 * side, y, 12), 5.5, 2, 0, 8)
    g.cylinder((x + 7 * side, y, 12), 2.5, 2, 0, 6)


def collection_truck():
    g = Grid((74, 128, 88), COLORS)
    g.roundbox((18, 12, 15), (56, 120, 26), 3, 7)
    for yy in (29, 52, 106):
        g.cylinder((37, yy, 12), 3, 52, 0, 6)
        for xx in (12, 62):
            truck_tire(g, xx, yy)
    # Main body, with stepped round shoulders and green loading-end reinforcement.
    g.roundbox((13, 34, 29), (61, 96, 83), 7, 4)
    g.roundbox((12, 34, 28), (62, 41, 84), 4, 1)
    g.roundbox((12, 87, 28), (62, 95, 84), 4, 1)
    g.roundbox((12, 39, 28), (62, 91, 35), 2, 2)
    for xx in (13, 59):
        g.roundbox((xx, 44, 38), (xx + 3, 84, 76), 3, 5)
    g.roundbox((23, 40, 81), (51, 90, 85), 2, 5)
    for yy in (44, 83):
        g.box((22, yy, 83), (52, yy + 4, 86), 1)
    # Cab faces +Y so the primary functional frontage at -Y exposes the rear hopper.
    g.roundbox((16, 94, 25), (58, 123, 63), 4, 4)
    g.roundbox((14, 94, 61), (60, 123, 66), 2, 5)
    g.roundbox((19, 119, 43), (55, 124, 60), 2, 6)
    g.box((22, 122, 45), (52, 125, 58), 11)
    g.box((23, 124, 53), (51, 126, 57), 12)
    for xx in (15, 56):
        g.roundbox((xx, 99, 43), (xx + 3, 118, 60), 2, 6)
        g.box((xx - .5, 102, 45), (xx + 3.5, 115, 57), 11)
        g.box((xx - .5, 102, 53), (xx + 3.5, 114, 57), 12)
    g.roundbox((14, 99, 28), (60, 124, 37), 3, 1)
    g.box((24, 123, 31), (50, 126, 41), 6)
    for zz in (33, 38):
        g.box((24, 125, zz), (50, 127, zz + 2), 8)
    g.roundbox((13, 120, 22), (61, 127, 29), 2, 7)
    for xx in (18, 51):
        g.box((xx, 123, 34), (xx + 5, 126, 40), 5)
        g.box((xx, 122, 30), (xx + 5, 126, 34), 9)
    for xx in (12, 62):
        g.beam((xx, 114, 45), (xx, 119, 53), 1.5, 7)
        g.roundbox((xx - 2, 117, 49), (xx + 2, 122, 58), 1, 6)
    g.roundbox((20, 100, 66), (25, 106, 69), 1, 9)
    g.roundbox((49, 100, 66), (54, 106, 69), 1, 9)
    # Side tank and steps, kept outside the loading cavity.
    g.roundbox((52, 72, 20), (64, 91, 32), 3, 8)
    g.box((52, 77, 20), (65, 80, 33), 7)
    g.box((52, 86, 20), (65, 89, 33), 7)
    g.roundbox((56, 96, 20), (66, 103, 25), 1, 7)
    # Hopper: sloped floor, two rising cheeks, back wall and a low loading lip.
    g.roundbox((17, 4, 25), (57, 36, 33), 2, 1)
    g.box((17, 32, 30), (57, 39, 76), 3)
    cheek = (((g.x >= 12) & (g.x < 20)) | ((g.x >= 54) & (g.x < 62))) & (g.y >= 5) & (g.y < 37)
    g.data[cheek & (g.z >= 28) & (g.z <= 47 + .85 * g.y)] = 1
    g.data[cheek & (g.z > 44 + .85 * g.y) & (g.z <= 47 + .85 * g.y)] = 2
    slope = 31 + .25 * g.y
    g.data[(g.x >= 20) & (g.x < 54) & (g.y >= 7) & (g.y < 33) & (g.z >= slope) & (g.z < slope + 3)] = 7
    g.roundbox((16, 2, 31), (58, 10, 38), 2, 8)
    g.roundbox((12, 31, 74), (62, 40, 81), 2, 2)
    for xx in (10, 64):
        g.beam((xx, 30, 68), (xx, 8, 39), 2.3, 9)
        g.cylinder((xx, 8, 39), 4, 4, 0, 8)
        g.beam((xx, 9, 34), (xx, 9, 23), 2, 9)
    g.roundbox((10, 2, 20), (64, 8, 26), 2, 1)
    g.box((12, 1, 23), (18, 5, 28), 13)
    g.box((56, 1, 23), (62, 5, 28), 13)
    g.roundbox((18, 0, 14), (56, 8, 19), 1, 7)
    g.box((18, 0, 17), (56, 2, 20), 9)
    return Asset('collection_truck', 'Rear-loading collection truck', g, .055, [
        'Original six-wheel collection truck with rounded cream body, external tail hydraulics, real sloped rear loading hopper and low rear step.',
        'Functional rear loading face points -Y; cab/vehicle travel direction is +Y so the common preview exposes the hopper.',
        'Native half occupancy uses conservative 2x reduction with no manual size-only edits. Opaque glass, static mechanism.',
    ])


def receiving_funnel(g, cx, cy, toward):
    height = (g.z - 36) / 29
    rx, ry = 7 + 8 * height, 8 + 10 * height
    outer = (g.z >= 36) & (g.z < 66) & (np.abs(g.x - cx) < rx) & (np.abs(g.y - cy) < ry)
    g.data[outer] = 1
    inner = (g.z >= 40) & (g.z < 68) & (np.abs(g.x - cx) < rx - 3) & (np.abs(g.y - cy) < ry - 3)
    g.data[inner] = 0
    g.box((cx - 16, cy - 19, 65), (cx + 16, cy + 19, 69), 5)
    g.box((cx - 12, cy - 15, 64), (cx + 12, cy + 15, 71), 0)
    if toward == 1:
        g.box((cx + 3, cy - 5, 40), (cx + 24, cy + 5, 49), 0)
        g.box((cx + 3, cy - 7, 36), (cx + 24, cy + 7, 40), 7)
        for yy in (cy - 7, cy + 5):
            g.box((cx + 6, yy, 40), (cx + 23, yy + 2, 46), 5)
    else:
        g.box((cx - 24, cy - 5, 40), (cx - 3, cy + 5, 49), 0)
        g.box((cx - 24, cy - 7, 36), (cx - 3, cy + 7, 40), 7)
        for yy in (cy - 7, cy + 5):
            g.box((cx - 23, yy, 40), (cx - 6, yy + 2, 46), 5)
    for yy in (cy - 7, cy + 7):
        g.box((cx - 4, yy - 2, 5), (cx + 4, yy + 2, 38), 1)
        g.box((cx - 6, yy - 4, 1), (cx + 6, yy + 4, 6), 7)


def sorting_machine():
    g = Grid((128, 102, 96), COLORS)
    # Continuous belt and rounded rollers sit above a four-leg frame.
    for xx in (31, 96):
        for yy in (18, 84):
            g.box((xx - 3, yy - 3, 4), (xx + 3, yy + 3, 29), 7)
            g.roundbox((xx - 6, yy - 6, 0), (xx + 6, yy + 6, 5), 1, 7)
    for xx in (29, 93):
        g.roundbox((xx, 10, 25), (xx + 6, 94, 38), 2, 1)
        g.box((xx, 12, 37), (xx + 6, 92, 40), 5)
    for yy in (12, 88):
        g.cylinder((64, yy, 30), 7, 58, 0, 6)
        for xx in (32, 96):
            g.cylinder((xx, yy, 30), 5, 5, 0, 8)
            g.cylinder((xx, yy, 30), 2.5, 6, 0, 7)
    g.box((35, 12, 25), (93, 89, 30), 6)
    g.box((35, 12, 31), (93, 89, 37), 6)
    for yy in range(15, 87, 7):
        g.box((36, yy, 36), (92, yy + 2, 38), 7)
    # Two genuinely open receiving funnels, each with a clear throat toward the belt.
    receiving_funnel(g, 16, 77, 1)
    receiving_funnel(g, 112, 79, -1)
    # Gantry leaves tall clearance over the sorting path.
    for xx in (26, 94):
        g.roundbox((xx, 48, 36), (xx + 8, 60, 87), 2, 1)
        g.box((xx - 1, 47, 39), (xx + 9, 61, 43), 2)
        g.box((xx, 47, 80), (xx + 8, 61, 86), 9)
    g.roundbox((26, 48, 82), (102, 61, 90), 2, 1)
    g.roundbox((51, 47, 88), (77, 63, 95), 2, 4)
    for xx in (43, 73):
        g.roundbox((xx, 50, 75), (xx + 12, 60, 83), 1, 6)
        g.box((xx + 3, 49, 73), (xx + 9, 57, 77), 9)
    # Belt drive on its own real mounting feet; no common display plinth.
    g.roundbox((101, 26, 7), (125, 56, 16), 2, 1)
    for yy in (29, 51):
        g.box((106, yy - 3, 0), (120, yy + 3, 9), 7)
    g.cylinder((110, 41, 26), 10, 17, 0, 7)
    for xx in (102, 106, 110, 114):
        g.cylinder((xx, 41, 26), 10.6, 1.5, 0, 8)
    g.cylinder((120, 41, 26), 11, 7, 0, 9)
    g.cylinder((124, 41, 26), 4, 2, 0, 7)
    g.beam((94, 41, 29), (104, 41, 29), 3, 8)
    g.beam((102, 42, 37), (98, 50, 46), 1.5, 6)
    # Three restrained pieces of feedstock make belt scale and direction readable.
    g.roundbox((46, 25, 38), (57, 36, 43), 1.5, 4)
    g.box((47, 27, 42), (56, 29, 44), 5)
    g.cylinder((75, 41, 42), 4, 9, 2, 8)
    g.cylinder((75, 41, 47), 2, 1, 2, 7)
    g.roundbox((56, 66, 38), (68, 76, 44), 2, 2)
    return Asset('sorting_machine', 'Optical sorting conveyor', g, .045, [
        'Original exposed belt with front/rear rollers, two flared receiving funnels with open lateral throats, twin overhead sensor heads, drive motor and separate mounting feet.',
        'The loose feedstock is static palette geometry. No sorting simulation, conveyor animation or transparency.',
    ])


def compactor():
    g = Grid((102, 84, 128), COLORS)
    # Stout two-rail base and four real steel shoes.
    for xx in (16, 76):
        g.roundbox((xx, 13, 4), (xx + 14, 76, 12), 2, 1)
        for yy in (17, 70):
            g.roundbox((xx - 3, yy - 6, 0), (xx + 17, yy + 6, 6), 1, 7)
    g.roundbox((25, 17, 10), (79, 68, 18), 2, 7)
    g.box((26, 15, 14), (79, 21, 19), 9)
    # Tall side columns and back wall form a clear front chamber.
    g.roundbox((17, 31, 10), (31, 72, 115), 3, 1)
    g.roundbox((73, 31, 10), (87, 72, 115), 3, 1)
    g.box((25, 63, 14), (79, 72, 106), 3)
    g.roundbox((14, 26, 105), (90, 75, 119), 3, 4)
    g.roundbox((41, 35, 118), (72, 65, 127), 2, 1)
    g.box((49, 34, 120), (60, 38, 126), 7)
    g.box((56, 33, 121), (61, 37, 126), 9)
    # Recessed hydraulic ram and bright guide columns stand above the open chamber.
    for xx in (34, 70):
        g.cylinder((xx, 47, 93), 3, 28, 2, 8)
        g.cylinder((xx, 47, 105), 4.5, 4, 2, 7)
    g.cylinder((52, 47, 94), 6.5, 31, 2, 9)
    g.cylinder((52, 47, 80), 8, 7, 2, 7)
    g.roundbox((29, 24, 72), (75, 65, 80), 2, 7)
    g.box((28, 23, 76), (76, 29, 81), 9)
    # Safety posts border the chamber without sealing its opening.
    for xx in (25, 74):
        g.roundbox((xx, 20, 15), (xx + 5, 28, 73), 1, 1)
        g.box((xx, 18, 17), (xx + 4, 22, 71), 9)
    # A compacted cardboard bale, with native alternating layers and wrap straps.
    g.roundbox((35, 22, 18), (70, 57, 47), 2, 14)
    bale = (g.x >= 35) & (g.x < 70) & (g.y >= 22) & (g.y < 57) & (g.z >= 18) & (g.z < 47) & (g.data > 0)
    g.data[bale & ((np.floor((g.z - 18) / 4).astype(int) % 2) == 0)] = 15
    bands = ((g.x >= 42) & (g.x < 45)) | ((g.x >= 61) & (g.x < 64)) | ((g.z >= 28) & (g.z < 31))
    g.data[bale & bands] = 6
    # Side pump and two bent hydraulic hoses connect to the press structure.
    g.roundbox((2, 36, 9), (19, 72, 31), 2, 4)
    g.cylinder((11, 53, 41), 7, 25, 2, 7)
    for zz in (32, 38, 44, 50):
        g.cylinder((11, 53, zz), 7.7, 2, 2, 8)
    for yy in (47, 59):
        g.beam((11, yy, 54), (11, yy, 79), 1.7, 6)
        g.beam((11, yy, 79), (20, yy, 96), 1.7, 6)
        g.box((8, yy - 2, 55), (14, yy + 2, 60), 9)
    # Readable external control panel with screen and two physical controls.
    g.box((84, 30, 47), (92, 39, 69), 1)
    g.roundbox((87, 22, 44), (100, 40, 76), 2, 4)
    g.box((89, 20, 61), (98, 24, 71), 7)
    g.box((91, 19, 63), (96, 22, 69), 11)
    g.box((89, 19, 50), (93, 23, 55), 9)
    g.box((95, 19, 50), (99, 23, 55), 13)
    g.beam((94, 36, 44), (94, 50, 22), 1.8, 6)
    g.beam((94, 50, 22), (84, 58, 19), 1.8, 6)
    return Asset('compactor', 'Vertical hydraulic baler', g, .045, [
        'Original vertical press with open front chamber, raised compression platen, exposed ram and guide columns, strapped cardboard bale, side hydraulic pump and console.',
        'Idle static pose deliberately retains a clear air gap above the bale. No animated press, physics or operational safety claim.',
    ])


def collection_bin(g, x0, color):
    g.roundbox((x0, 16, 10), (x0 + 14, 44, 16), 1, 7)
    g.box((x0, 16, 14), (x0 + 14, 20, 28), color)
    g.box((x0, 40, 14), (x0 + 14, 44, 40), color)
    sides = (((g.x >= x0) & (g.x < x0 + 3)) | ((g.x >= x0 + 11) & (g.x < x0 + 14))) & (g.y >= 20) & (g.y < 41)
    upper = 27 + .6 * (g.y - 20)
    g.data[sides & (g.z >= 14) & (g.z < upper)] = color
    g.data[sides & (g.z >= upper - 2) & (g.z < upper + 1)] = 8
    g.box((x0, 15, 27), (x0 + 14, 20, 30), 8)
    g.box((x0, 40, 39), (x0 + 14, 45, 42), 8)


def recycling_center():
    g = Grid((128, 96, 90), COLORS)
    # Taller receiving hall with an actually hollow interior and open front portal.
    g.roundbox((5, 24, 6), (65, 92, 81), 2, 4)
    g.box((12, 18, 7), (58, 86, 70), 0)
    g.roundbox((8, 18, 3), (62, 90, 10), 1, 8)
    g.box((5, 26, 10), (12, 91, 29), 1)
    g.box((58, 26, 10), (65, 91, 29), 1)
    g.box((12, 85, 10), (58, 88, 29), 7)
    g.roundbox((3, 21, 79), (67, 94, 86), 2, 1)
    g.box((6, 25, 85), (64, 90, 88), 2)
    for xx in (7, 55):
        g.roundbox((xx, 20, 8), (xx + 8, 29, 74), 1.5, 1)
    g.roundbox((7, 20, 69), (63, 29, 77), 1.5, 2)
    for yy in (42, 64):
        g.box((12, yy, 68), (58, yy + 4, 73), 1)
    for xx in (23, 43):
        g.box((xx, 30, 67), (xx + 9, 37, 70), 5)
        g.box((xx, 30, 66), (xx + 9, 37, 68), 9)
    # Lower annex: three separate empty receiving bays, sheltered by one canopy.
    g.roundbox((64, 24, 6), (125, 91, 61), 2, 4)
    g.box((66, 16, 10), (123, 58, 53), 0)
    g.roundbox((64, 15, 3), (126, 91, 10), 1, 8)
    for xx in (64, 83, 102, 121):
        g.box((xx, 18, 8), (xx + 4, 61, 56), 4)
        g.box((xx, 18, 8), (xx + 4, 23, 28), 7)
    g.roundbox((62, 15, 59), (128, 94, 66), 2, 1)
    g.box((64, 18, 65), (125, 90, 68), 2)
    g.box((63, 15, 53), (127, 22, 60), 2)
    for xx in (71, 90, 109):
        g.box((xx, 23, 52), (xx + 8, 28, 55), 5)
    for xx, color in ((68, 1), (87, 9), (106, 7)):
        collection_bin(g, xx, color)
    # Corner guards and a simple roof vent/chimney are real building fixtures.
    for xx in (7, 60, 65, 84, 103, 122):
        g.roundbox((xx - 2, 13, 5), (xx + 2, 19, 28), 1, 9)
        g.box((xx - 3, 14, 3), (xx + 3, 20, 7), 7)
    g.roundbox((108, 74, 65), (118, 85, 86), 1, 7)
    g.box((108, 74, 79), (118, 85, 83), 9)
    g.roundbox((106, 72, 85), (120, 87, 89), 1, 7)
    g.box((63, 71, 68), (67, 82, 77), 7)
    for zz in (70, 74):
        g.box((65, 72, zz), (68, 81, zz + 1), 6)
    return Asset('recycling_center', 'Recycling receiving center', g, .075, [
        'Original stepped-roof hall with a genuinely open vehicle receiving portal, hollow receiving interior, sheltered three-bay annex, three open-topped collection bins, corner guards and roof vent.',
        'Main hall is hollow; annex space is modeled only to the receiving-bay depth. Structural floor is part of the building, not a common diorama base.',
    ])


def make_assets():
    return [collection_truck(), sorting_machine(), compactor(), recycling_center()]


if __name__ == '__main__':
    run_theme(Path(__file__).resolve().parent, make_assets())
