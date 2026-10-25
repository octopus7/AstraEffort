"""Original camping occupancy. Generic export pipeline is parent owned."""
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_tools'))
from voxelkit import Asset, Grid, run_theme

PALETTE = [
    (0, 0, 0, 0),
    (226, 219, 195),  # 1 cream body
    (197, 187, 159),  # 2 warm trim
    (118, 137, 99),   # 3 sage olive
    (78, 99, 72),     # 4 dark olive
    (137, 85, 43),    # 5 timber
    (178, 121, 62),   # 6 fresh timber
    (209, 155, 86),   # 7 log ends and handrails
    (156, 78, 51),    # 8 clay roof
    (106, 65, 46),    # 9 dark roof edge
    (55, 62, 61),     # 10 charcoal hardware
    (38, 43, 43),     # 11 rubber
    (163, 169, 161),  # 12 metal
    (72, 101, 108),   # 13 opaque blue-gray glass
    (127, 156, 156),  # 14 glass highlight
    (216, 153, 55),   # 15 amber lamp
    (169, 70, 45),    # 16 red switch/tail light
    (130, 130, 119),  # 17 foundation stone
    (161, 158, 143),  # 18 stone variation
    (166, 110, 57),   # 19 copper plumbing
]


def wheels(g, x_centers, y, z, radius, thickness):
    for x in x_centers:
        g.cylinder((x, y, z), radius, thickness, 0, 11)
        outside = x - thickness / 2 - 0.5 if x < g.shape[0] / 2 else x + thickness / 2 + 0.5
        g.cylinder((outside, y, z), radius * .57, 2, 0, 12)
        g.cylinder((outside, y, z), radius * .23, 3, 0, 10)


def camper_van():
    g = Grid((72, 128, 84), PALETTE)
    g.roundbox((14, 16, 13), (58, 118, 23), 3, 10)
    g.roundbox((8, 10, 20), (64, 122, 76), 7, 1)
    front = 11 + np.maximum(g.z - 41, 0) * .36
    g.data[(g.y < front) & (g.x >= 0)] = 0
    g.data[(g.data > 0) & (g.z < 41) & (g.z >= 22)] = 3

    # Windshield is a broad sloped opaque palette surface, with a central mullion.
    screen = (g.y >= front) & (g.y < front + 3) & (g.x >= 12) & (g.x < 60) & (g.z >= 44) & (g.z < 69)
    g.data[screen] = 10
    pane = screen & (g.x >= 16) & (g.x < 56) & (g.z >= 48) & (g.z < 66)
    g.data[pane] = 13
    g.data[pane & (g.x < 22)] = 14
    g.data[pane & (g.x >= 35) & (g.x < 37)] = 10
    g.roundbox((8, 22, 71), (64, 122, 80), 4, 1)
    g.roundbox((25, 71, 79), (47, 93, 83), 2, 2)
    g.box((28, 74, 82), (44, 90, 84), 1)

    # Upper side windows, each with a thick readable frame.
    for ya, yb, za, zb in ((26, 43, 47, 67), (49, 74, 47, 65), (103, 117, 48, 65)):
        for xa, xb in ((6, 10), (62, 66)):
            g.roundbox((xa, ya, za), (xb, yb, zb), 1, 10)
            g.box((xa, ya + 3, za + 3), (xb, yb - 3, zb - 3), 13)
            g.box((xa, ya + 3, za + 3), (xb, ya + 5, zb - 3), 14)
    g.box((62, 60, 50), (66, 62, 62), 2)
    g.box((6, 60, 50), (10, 62, 62), 2)

    # Fixed entry door and two-step boarding sill on the visible right side.
    g.roundbox((62, 77, 28), (66, 98, 70), 2, 10)
    g.roundbox((64, 80, 31), (66, 95, 67), 1, 1)
    g.box((64, 81, 51), (67, 94, 65), 10)
    g.box((65, 83, 54), (67, 92, 63), 13)
    g.box((66, 81, 40), (68, 84, 45), 10)
    g.roundbox((61, 78, 23), (70, 97, 28), 1, 10)
    g.box((64, 80, 27), (70, 95, 29), 12)

    # Stowed awning: continuous roll held by end brackets.
    for y in (48, 116):
        g.box((61, y - 2, 67), (67, y + 2, 75), 10)
    g.cylinder((66, 82, 73), 3, 68, 1, 3)
    for y in (48, 116):
        g.cylinder((66, y, 73), 4, 3, 1, 10)

    # Wheels fit carved arches rather than being painted on the lower body.
    for y in (31, 101):
        for x in (10, 62):
            g.cylinder((x, y, 13), 13, 20, 0, 0)
        g.cylinder((36, y, 13), 2, 52, 0, 10)
        wheels(g, (10, 62), y, 13, 11, 12)
    g.roundbox((10, 5, 20), (62, 16, 26), 2, 4)
    g.roundbox((11, 9, 28), (61, 14, 39), 2, 3)
    g.box((24, 8, 29), (48, 12, 37), 10)
    g.box((24, 7, 32), (48, 10, 34), 12)
    for xa, xb in ((13, 22), (50, 59)):
        g.roundbox((xa, 8, 30), (xb, 12, 38), 1, 2)
        g.box((xa + 1, 7, 32), (xb - 1, 10, 37), 1)
    g.box((11, 8, 30), (14, 12, 36), 15)
    g.box((58, 8, 30), (61, 12, 36), 15)
    for x, direction in ((10, -1), (62, 1)):
        g.beam((x, 26, 47), (x + direction * 5, 21, 47), 2, 10)
        xa = 1 if direction < 0 else 65
        g.roundbox((xa, 17, 43), (xa + 6, 23, 55), 2, 10)
        g.box((xa + 1, 17, 46), (xa + 5, 19, 53), 12)
    for x in (13, 57):
        g.box((x, 120, 29), (x + 3, 123, 39), 16)
    g.roundbox((10, 118, 20), (62, 125, 25), 2, 10)
    return Asset('camper_van', 'Rounded touring camper van', g, .05, [
        'Original cream/olive camper: sloped split windshield, framed side glazing, fixed entry door, boarding step and stowed awning.',
        'Four tires in carved arches; opaque glass with no authored interior. No rig, animation or collision.',
        'Half occupancy uses generic conservative reduction; no manual half edits.'
    ])


def log_cabin():
    g = Grid((128, 112, 116), PALETTE)
    # Actual building/porch foundation only, without a terrain plinth.
    g.roundbox((10, 22, 2), (118, 106, 13), 2, 17)
    for z in (3, 8):
        for x in range(12 + (5 if z == 8 else 0), 116, 12):
            g.box((x, 21, z), (min(x + 9, 117), 24, z + 4), 18)
        for y in range(25 + (5 if z == 8 else 0), 104, 12):
            g.box((116, y, z), (119, min(y + 9, 105), z + 4), 18)
    g.box((14, 20, 12), (114, 101, 17), 6)
    for x in range(16, 114, 8):
        g.box((x, 20, 16), (x + 1, 42, 17), 5)

    # Long horizontal logs have real stepped circular ends.
    for row, z in enumerate(range(22, 78, 8)):
        color = 6 if row % 2 == 0 else 5
        g.cylinder((64, 38, z), 5, 100, 0, color)
        g.cylinder((64, 98, z), 5, 100, 0, color)
        for x in (20, 108):
            g.cylinder((x, 66, z), 5, 78, 1, color)
            g.cylinder((x, 27, z), 4, 2, 1, 7)
            g.cylinder((x, 27, z), 1.5, 3, 1, 5)
        g.cylinder((114, 38, z), 4, 2, 0, 7)
        g.cylinder((114, 98, z), 4, 2, 0, 7)
    g.box((26, 44, 18), (102, 92, 78), 0)

    # Recessed closed doorway behind an open, sheltered porch route.
    g.box((54, 29, 17), (78, 46, 61), 0)
    g.box((50, 31, 17), (54, 45, 65), 7)
    g.box((78, 31, 17), (82, 45, 65), 7)
    g.box((50, 31, 61), (82, 45, 65), 7)
    g.box((54, 42, 17), (78, 46, 61), 5)
    for x in (56, 63, 70):
        g.box((x, 41, 20), (x + 5, 43, 58), 6)
    g.box((72, 38, 35), (75, 42, 39), 10)

    # Window frames stay physically attached to the log shell.
    g.box((29, 31, 36), (48, 36, 62), 5)
    g.box((32, 30, 39), (45, 34, 59), 13)
    g.box((33, 30, 40), (36, 33, 58), 14)
    g.box((38, 29, 39), (40, 33, 59), 7)
    g.box((108, 55, 34), (115, 85, 64), 5)
    g.box((112, 59, 38), (116, 81, 60), 13)
    g.box((114, 60, 39), (116, 64, 59), 14)
    g.box((114, 69, 38), (117, 72, 60), 7)
    g.box((109, 54, 32), (118, 86, 36), 7)

    # Timber gables and roof: broad stepped slopes, softened ridge and fascia.
    roof_top = 106 - .42 * np.abs(g.x - 64)
    gable = (g.x >= 20) & (g.x < 108) & (g.z >= 76) & (g.z < roof_top - 5) & (((g.y >= 34) & (g.y < 42)) | ((g.y >= 94) & (g.y < 102)))
    g.data[gable] = 6
    g.data[gable & ((np.floor((g.z - 76) / 5) % 2) == 1)] = 5
    roof = (g.x >= 6) & (g.x < 122) & (g.y >= 13) & (g.y < 109) & (g.z >= roof_top - 6) & (g.z < roof_top)
    g.data[roof] = 8
    g.data[roof & ((g.y < 17) | (g.y >= 105) | (g.x < 10) | (g.x >= 118) | (g.z < roof_top - 4))] = 9
    for y in range(21, 105, 12):
        g.data[roof & (g.y >= y) & (g.y < y + 2) & (g.z >= roof_top - 2)] = 9
    g.roundbox((60, 13, 102), (68, 109, 108), 2, 8)

    # Porch posts, paired rail wings, central stairway: no railing across entry.
    for x in (21, 107):
        g.cylinder((x, 20, 48), 3.5, 64, 2, 6)
        g.box((x - 5, 16, 73), (x + 5, 24, 81), 7)
    for xa, xb in ((20, 50), (82, 108)):
        g.roundbox((xa, 16, 37), (xb, 21, 42), 1, 7)
    for x in (22, 34, 46, 84, 96, 108):
        g.box((x - 1, 17, 17), (x + 2, 20, 39), 6)
    for x in (18, 107):
        g.box((x, 20, 37), (x + 4, 36, 41), 7)
    g.box((50, 1, 2), (82, 10, 6), 6)
    g.box((50, 7, 5), (82, 16, 10), 6)
    g.box((50, 13, 9), (82, 23, 16), 7)
    return Asset('log_cabin', 'Log cabin with sheltered front porch', g, .05, [
        'Original horizontal cylindrical log shell, real rounded end grain, timber porch, inset closed door and terracotta stepped gable roof.',
        'Foundation belongs to the building; center porch passage and stairway remain clear at both resolutions.',
        'Opaque window surfaces; empty enclosed shell is not a furnished interior. Half uses conservative reduction without manual edits.'
    ])


def generator_trailer():
    g = Grid((76, 128, 80), PALETTE)
    g.roundbox((10, 44, 16), (66, 122, 23), 2, 10)
    g.roundbox((13, 50, 22), (63, 119, 69), 8, 1)
    g.data[(g.data == 1) & (g.z < 37)] = 3
    g.box((19, 57, 28), (57, 112, 62), 0)

    # Front ventilation contains open slot depths, backed by a separate dark panel.
    g.roundbox((20, 48, 38), (56, 52, 61), 1, 2)
    g.box((20, 57, 38), (56, 59, 62), 10)
    for za in (41, 47, 53):
        g.box((24, 47, za), (52, 57, za + 3), 0)
        g.box((23, 47, za - 2), (53, 50, za), 12)

    # Side service controls and a second set of true ventilation slots.
    g.roundbox((61, 58, 38), (66, 79, 59), 1, 10)
    g.box((64, 61, 41), (67, 76, 56), 12)
    g.box((66, 63, 49), (68, 69, 54), 10)
    g.box((67, 64, 50), (69, 68, 53), 14)
    g.box((66, 72, 50), (69, 75, 55), 16)
    for y in (63, 71):
        g.cylinder((67, y + 1, 44), 2, 3, 0, 10)
    g.box((62, 84, 38), (66, 111, 61), 2)
    g.box((58, 86, 39), (60, 109, 60), 10)
    for za in (42, 48, 54):
        g.box((60, 88, za), (67, 108, za + 3), 0)
        g.box((64, 87, za - 2), (67, 109, za), 12)
    g.box((63, 80, 42), (66, 83, 48), 10)

    # Open A-frame drawbar and real ring coupling.
    g.beam((17, 48, 20), (38, 24, 20), 3, 10)
    g.beam((59, 48, 20), (38, 24, 20), 3, 10)
    g.roundbox((35, 16, 17), (41, 30, 23), 1, 10)
    g.torus((38, 11, 20), 7, 2.5, 2, 12)
    g.beam((38, 30, 20), (44, 30, 20), 2, 12)
    g.cylinder((44, 30, 12), 2, 22, 2, 12)
    g.roundbox((39, 25, 1), (49, 35, 5), 1, 10)
    g.beam((44, 30, 23), (49, 30, 23), 1.5, 10)

    # One axle with a wheel on each side; the fender leaves a true wheel gap.
    for x in (10, 66):
        g.roundbox((x - 7, 76, 15), (x + 7, 106, 29), 4, 4)
        g.cylinder((x, 91, 13), 13, 18, 0, 0)
    g.cylinder((38, 91, 13), 2, 56, 0, 10)
    wheels(g, (10, 66), 91, 13, 11, 12)
    for x in (11, 61):
        g.box((x, 120, 18), (x + 4, 123, 23), 16)
    g.box((65, 49, 18), (68, 54, 23), 15)
    g.cylinder((42, 101, 72), 3, 12, 2, 10)
    g.cylinder((42, 101, 77), 4, 3, 2, 10)
    return Asset('generator_trailer', 'Portable generator trailer', g, .05, [
        'Original compact rounded generator on a single-axle trailer, with open ring hitch, A-frame, jack foot and rear exhaust.',
        'Front and side louvers contain actual empty slots backed by dark panels; visible control panel has sockets, meter and red control.',
        'Fixed machinery with no animation; half uses generic conservative reduction without manual edits.'
    ])


def shower_block():
    g = Grid((128, 84, 96), PALETTE)
    g.roundbox((6, 20, 2), (106, 79, 10), 2, 17)
    g.roundbox((8, 24, 10), (104, 74, 79), 2, 1)
    g.data[(g.data == 1) & (g.z < 34)] = 3
    g.box((14, 30, 12), (98, 68, 76), 0)
    g.box((38, 30, 10), (42, 68, 77), 1)
    g.box((68, 30, 10), (72, 68, 77), 1)
    g.box((12, 29, 10), (100, 70, 12), 18)

    # Three entrances, two closed slab doors and a fixed fully open center door.
    for xa in (14, 44, 74):
        xb = xa + 20
        g.box((xa - 3, 21, 10), (xb + 3, 31, 64), 2)
        g.box((xa, 20, 10), (xb, 34, 62), 0)
        g.roundbox((xa - 2, 11, 2), (xb + 2, 25, 7), 1, 18)
        g.box((xa - 1, 19, 7), (xb + 1, 29, 10), 18)
        if xa != 44:
            g.box((xa, 29, 10), (xb, 32, 62), 4)
            g.box((xa + 3, 28, 14), (xb - 3, 31, 59), 3)
            g.box((xa + 9, 27, 14), (xa + 11, 30, 59), 4)
            g.box((xa + 3, 25, 33), (xa + 6, 29, 38), 10)
        g.box((xa - 1, 22, 66), (xb + 1, 25, 76), 10)
        g.box((xa + 2, 21, 68), (xb - 2, 24, 74), 13)
        g.box((xa + 2, 21, 69), (xa + 5, 23, 73), 14)
    g.box((44, 10, 12), (48, 31, 62), 4)
    g.box((47, 13, 16), (49, 27, 58), 3)
    g.box((48, 16, 34), (51, 20, 38), 10)

    # Visible empty central stall with a connected copper riser and shower head.
    g.box((43, 65, 12), (67, 68, 76), 2)
    g.beam((55, 65, 20), (55, 65, 66), 1.5, 19)
    g.beam((55, 65, 66), (55, 56, 66), 2, 12)
    g.cylinder((55, 56, 63), 4, 3, 2, 10)
    g.cylinder((55, 63, 35), 2, 5, 1, 12)
    g.box((52, 47, 11), (58, 53, 13), 10)

    # Three small functional porch lamps and supporting roof corbels.
    for x in (10, 40, 70, 100):
        g.roundbox((x - 2, 20, 48), (x + 2, 24, 57), 1, 10)
        g.box((x - 1, 19, 50), (x + 1, 22, 55), 1)
        g.box((x - 3, 21, 73), (x + 3, 29, 81), 6)
    roof_top = 87 + .05 * (g.y - 20)
    roof = (g.x >= 2) & (g.x < 112) & (g.y >= 17) & (g.y < 81) & (g.z >= roof_top - 7) & (g.z < roof_top)
    g.data[roof] = 10
    g.data[roof & (g.z < roof_top - 5)] = 12
    for x in range(6, 111, 12):
        g.data[roof & (g.x >= x) & (g.x < x + 2) & (g.z >= roof_top - 2)] = 12

    # Side-mounted hot-water cylinder shown by the reference, strapped to wall.
    for z in (22, 56):
        g.beam((102, 53, z), (116, 53, z), 2.5, 10)
    g.cylinder((116, 53, 37), 8, 48, 2, 1)
    g.ellipsoid((116, 53, 13), (8, 8, 3), 1)
    g.ellipsoid((116, 53, 61), (8, 8, 3), 1)
    for z in (22, 56):
        g.cylinder((116, 53, z), 8.5, 3, 2, 12)
    g.beam((116, 53, 62), (116, 53, 72), 2, 19)
    g.beam((116, 53, 72), (102, 53, 72), 2, 19)
    g.beam((116, 53, 11), (116, 70, 11), 2, 10)
    g.beam((116, 70, 11), (116, 70, 45), 2, 10)
    g.beam((116, 70, 45), (102, 70, 45), 2, 19)
    g.box((122, 49, 33), (126, 57, 44), 10)
    g.box((124, 51, 39), (127, 55, 43), 16)
    return Asset('shower_block', 'Three-stall campsite shower block', g, .05, [
        'Original cream/olive three-stall building with two closed doors, a fixed open center door, shower head, riser and floor drain.',
        'External cylindrical hot-water heater and connected supply/return pipework follow the side-mounted heater in the reference.',
        'Foundation and doorstep slabs are structural. No water simulation, door rig or animation. Half uses conservative reduction with no manual edits.'
    ])


def make_assets():
    return [camper_van(), log_cabin(), generator_trailer(), shower_block()]


if __name__ == '__main__':
    run_theme(Path(__file__).resolve().parent, make_assets())
