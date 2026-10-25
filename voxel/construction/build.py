"""Original construction voxel assets. Native occupancy is the source of truth."""
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_tools'))
from voxelkit import Grid, Asset, run_theme

PALETTE = [
    (0, 0, 0, 0),
    (229, 166, 48, 255),   # 1 equipment yellow
    (246, 192, 76, 255),   # 2 upper yellow
    (170, 112, 32, 255),   # 3 recessed ochre
    (47, 56, 62, 255),     # 4 rubber / deep mechanism
    (68, 82, 95, 255),     # 5 slate structural steel
    (105, 121, 131, 255),  # 6 bare steel
    (227, 218, 192, 255),  # 7 warm ivory
    (247, 239, 217, 255),  # 8 light trim
    (51, 83, 106, 255),    # 9 opaque blue glazing
    (87, 124, 147, 255),   # 10 glazing highlight
    (205, 99, 39, 255),    # 11 orange lamps / hubs
    (153, 154, 140, 255),  # 12 concrete / muted steel
]


def wheel(g, x, y, z, radius, width):
    """Axle runs X; tread is a native stepped silhouette, not a mesh modifier."""
    g.cylinder((x, y, z), radius, width, 0, 4)
    # Alternating inset tread bands remain broad enough to read at half resolution.
    qy, qz = g.y - y, g.z - z
    angle = np.arctan2(qz, qy)
    radial = qy * qy + qz * qz
    mask = (np.abs(g.x - x) < width / 2 - 1) & (radial > (radius - 2.2) ** 2) & (radial <= radius ** 2) & (np.cos(angle * 12) > .25)
    g.data[mask] = 5
    for side in (-1, 1):
        sx = x + side * (width / 2 - .5)
        g.cylinder((sx, y, z), radius - 2, 1.5, 0, 5)
        g.cylinder((sx + side * .7, y, z), radius * .54, 2, 0, 1)
        g.cylinder((sx + side * 1.5, y, z), radius * .23, 2, 0, 11)


def mixer():
    g = Grid((70, 128, 86), PALETTE)
    g.roundbox((18, 16, 14), (52, 117, 25), 3, 5)
    for yy in (27, 81, 106):
        g.cylinder((35, yy, 12), 4, 49, 0, 4)
        for xx in (11, 59):
            wheel(g, xx, yy, 12, 11, 10)
    # Continuous running boards and tank are independent truck parts.
    g.roundbox((12, 37, 19), (21, 67, 27), 2, 6)
    g.roundbox((49, 37, 19), (58, 67, 27), 2, 6)
    g.roundbox((20, 43, 23), (31, 64, 38), 3, 7)
    g.box((23, 45, 22), (26, 63, 39), 5)
    # Compact cab with blunt corners and broad glazing.
    g.roundbox((15, 8, 24), (55, 44, 62), 5, 1)
    g.roundbox((13, 9, 60), (57, 43, 65), 2, 2)
    g.roundbox((18, 7, 42), (52, 12, 59), 2, 4)
    g.box((21, 6, 44), (49, 9, 57), 9)
    g.box((22, 5, 52), (48, 7, 56), 10)
    g.box((33, 5, 44), (36, 8, 58), 5)
    for xx in (14, 53):
        g.roundbox((xx, 17, 41), (xx + 3, 38, 58), 2, 4)
        g.box((xx - .5, 20, 44), (xx + 3.5, 35, 56), 9)
        g.box((xx - .5, 20, 53), (xx + 3.5, 34, 56), 10)
    g.roundbox((18, 5, 29), (52, 10, 40), 2, 5)
    for zz in (31, 35, 39):
        g.box((23, 4, zz), (47, 6, zz + 1), 4)
    g.roundbox((12, 3, 22), (58, 11, 29), 2, 6)
    for xx in (17, 48):
        g.box((xx, 4, 34), (xx + 5, 7, 40), 8)
        g.box((xx, 2, 24), (xx + 4, 5, 27), 11)
    for xx in (12, 57):
        g.beam((xx, 14, 47), (xx, 8, 52), 1.5, 5)
        g.roundbox((xx - 2, 7, 48), (xx + 2, 12, 57), 1.5, 4)
    for xx in (23, 45):
        g.roundbox((xx, 21, 65), (xx + 4, 26, 68), 1, 11)
    # Drum cradle, broad spheroidal barrel and the rear neck.
    g.box((22, 53, 25), (48, 98, 35), 3)
    g.beam((22, 57, 30), (22, 88, 38), 3, 1)
    g.beam((48, 57, 30), (48, 88, 38), 3, 1)
    centered_z = g.z - (56 + .10 * (g.y - 79))
    drum = ((g.x - 35) / 22.5) ** 2 + ((g.y - 79) / 36) ** 2 + (centered_z / 24) ** 2 <= 1
    g.data[drum] = 7
    g.data[drum & (((g.y >= 59) & (g.y < 65)) | ((g.y >= 88) & (g.y < 95)))] = 2
    g.cylinder((35, 111, 59), 9, 8, 1, 5)
    g.cylinder((35, 115, 59), 7, 5, 1, 7)
    # Open rear feed hopper; its right branch empties into a U-shaped chute.
    g.roundbox((25, 110, 60), (46, 122, 74), 2, 1)
    g.box((29, 113, 64), (42, 119, 76), 0)
    g.beam((44, 114, 61), (56, 106, 58), 4, 6)
    g.box((51, 102, 58), (66, 109, 66), 6)
    g.box((55, 103, 61), (62, 110, 68), 0)
    floor = 57 - .74 * (g.y - 106)
    chute = (g.y >= 106) & (g.y < 125) & (g.x >= 51) & (g.x < 66)
    g.data[chute & (g.z >= floor) & (g.z < floor + 3)] = 6
    g.data[chute & ((g.x < 54) | (g.x >= 63)) & (g.z >= floor) & (g.z < floor + 9)] = 5
    g.beam((52, 114, 30), (57, 119, 45), 2, 1)
    # Rear cross bumper and small fenders do not enclose the wheels.
    g.roundbox((12, 117, 18), (57, 122, 24), 2, 6)
    for xx in (12, 50):
        g.box((xx, 120, 21), (xx + 5, 123, 25), 11)
    return Asset('concrete_mixer', 'Concrete mixer truck', g, .055, [
        'Original six-wheel truck, stepped rounded drum, open feed hopper and descending U-shaped rear-right discharge chute.',
        'Opaque palette glazing; static parts. Half uses conservative native reduction without manual correction.',
    ])


def loader():
    g = Grid((88, 128, 90), PALETTE)
    g.roundbox((24, 37, 21), (64, 71, 34), 4, 1)
    g.roundbox((23, 76, 21), (65, 118, 39), 4, 1)
    g.cylinder((44, 73, 27), 10, 15, 2, 5)
    g.box((36, 63, 23), (52, 84, 31), 5)
    for yy in (49, 103):
        g.cylinder((44, yy, 17), 5, 58, 0, 4)
        for xx in (17, 71):
            wheel(g, xx, yy, 17, 16, 13)
    # Four stepped fender shelves, clear of the tire shoulders.
    for xx in (13, 62):
        for yy in (49, 103):
            g.roundbox((xx, yy - 17, 33), (xx + 13, yy + 17, 37), 2, 5)
    g.roundbox((24, 94, 34), (64, 121, 56), 4, 1)
    g.roundbox((27, 95, 54), (61, 119, 59), 2, 2)
    g.box((29, 119, 39), (59, 122, 51), 4)
    for zz in (41, 45, 49):
        g.box((30, 121, zz), (58, 123, zz + 1), 6)
    g.box((63, 100, 40), (65, 116, 51), 4)
    for zz in (42, 46, 50):
        g.box((64, 101, zz), (66, 115, zz + 1), 6)
    g.roundbox((22, 119, 22), (66, 125, 32), 2, 1)
    for xx in (23, 59):
        g.box((xx, 123, 28), (xx + 5, 126, 33), 11)
    # Cabin occupies the rear half; color blocks are intentionally broad at 64 cells.
    g.roundbox((25, 64, 39), (63, 96, 79), 3, 5)
    g.roundbox((28, 63, 48), (60, 67, 75), 2, 9)
    g.box((31, 62, 68), (57, 65, 74), 10)
    for xx in (24, 61):
        g.roundbox((xx, 69, 49), (xx + 3, 91, 75), 2, 9)
        g.box((xx - .5, 71, 68), (xx + 3.5, 89, 74), 10)
        g.box((xx - .5, 81, 48), (xx + 3.5, 84, 76), 5)
    for xx in (24, 59):
        g.box((xx, 64, 41), (xx + 5, 69, 79), 1)
        g.box((xx, 91, 41), (xx + 5, 96, 79), 1)
    g.roundbox((22, 61, 77), (66, 99, 83), 2, 2)
    for xx in (26, 58):
        g.roundbox((xx, 64, 83), (xx + 4, 69, 86), 1, 11)
    g.box((61, 78, 42), (66, 83, 45), 8)
    # Right access steps and rear exhaust.
    g.box((64, 78, 21), (72, 91, 25), 5)
    g.box((63, 81, 29), (70, 91, 33), 6)
    g.beam((66, 90, 36), (66, 90, 54), 1.5, 5)
    g.beam((66, 90, 54), (63, 94, 54), 1.5, 5)
    g.cylinder((55, 111, 66), 3, 18, 2, 4)
    g.beam((55, 111, 74), (55, 115, 76), 3, 5)
    # Twin lift arms and bright exposed piston rods stay physically separate.
    for xx in (28, 60):
        g.beam((xx, 67, 44), (xx, 43, 45), 4.5, 1)
        g.beam((xx, 43, 45), (xx, 32, 24), 4.5, 1)
        g.cylinder((xx, 66, 44), 5.5, 9, 0, 5)
        g.beam((xx, 60, 29), (xx, 49, 36), 3.5, 4)
        g.beam((xx, 49, 36), (xx, 39, 42), 2, 6)
    g.beam((28, 34, 27), (60, 34, 27), 3, 5)
    # A scoop is built as floor, sloped cheeks and back only: the interior is empty.
    g.roundbox((6, 5, 8), (82, 37, 14), 2, 5)
    g.roundbox((7, 31, 11), (81, 38, 40), 2, 5)
    side = ((g.x >= 6) & (g.x < 12)) | ((g.x >= 76) & (g.x < 82))
    slope = 14 + .82 * (g.y - 5)
    g.data[side & (g.y >= 6) & (g.y < 35) & (g.z >= 11) & (g.z <= slope)] = 5
    g.roundbox((6, 32, 37), (82, 39, 42), 2, 6)
    g.box((12, 5, 12), (76, 9, 15), 6)
    for xx in (14, 27, 40, 53, 66):
        g.roundbox((xx, 1, 8), (xx + 8, 9, 13), 1.5, 6)
    # Trim lift-arm capsules at the back-wall plane; no tips intrude into the scoop.
    g.box((12, 9, 15), (76, 31, 37), 0)
    return Asset('wheel_loader', 'Wheel loader', g, .05, [
        'Original articulated loader with four wheels, twin exposed lift arms, hydraulic rods, open scoop and five blunt teeth.',
        'Bucket is natively hollow, including at half resolution. Opaque blue cab glazing; no rig or moving mechanism.',
    ])


def crane():
    g = Grid((128, 60, 128), PALETTE)
    # Four real stabilizer shoes and diagonal outriggers, no presentation plinth.
    for xx in (19, 61):
        for yy in (10, 50):
            g.roundbox((xx - 7, yy - 7, 0), (xx + 7, yy + 7, 6), 2, 5)
            g.box((xx - 6, yy - 6, 0), (xx + 6, yy - 3, 4), 1)
            g.roundbox((xx - 4, yy - 4, 5), (xx + 4, yy + 4, 10), 1, 12)
            g.beam((xx, yy, 9), (40, 30, 17), 3, 5)
            g.cylinder((xx, yy, 10), 2.5, 5, 2, 1)
    g.roundbox((27, 17, 6), (53, 43, 14), 2, 5)
    g.roundbox((30, 20, 13), (50, 40, 20), 2, 1)
    # Four-corner open tower with one diagonal per bay on each face.
    for xx in (34, 46):
        for yy in (24, 36):
            g.beam((xx, yy, 18), (xx, yy, 96), 2.4, 1)
    levels = (20, 43, 66, 89, 96)
    for zz in levels:
        for yy in (24, 36):
            g.beam((34, yy, zz), (46, yy, zz), 2, 2)
        for xx in (34, 46):
            g.beam((xx, 24, zz), (xx, 36, zz), 2, 2)
    for i, (za, zb) in enumerate(zip(levels[:3], levels[1:4])):
        a, b = ((34, 46) if i % 2 == 0 else (46, 34))
        for yy in (24, 36):
            g.beam((a, yy, za), (b, yy, zb), 1.7, 1)
        for xx in (34, 46):
            ya, yb = ((24, 36) if i % 2 == 0 else (36, 24))
            g.beam((xx, ya, za), (xx, yb, zb), 1.7, 1)
    g.roundbox((28, 18, 91), (53, 42, 97), 2, 5)
    g.cylinder((40, 30, 99), 10, 6, 2, 3)
    # Long jib is an open rectangular truss with broad clear windows between diagonals.
    for yy in (24, 36):
        for zz in (101, 112):
            g.beam((10, yy, zz), (124, yy, zz), 1.8, 1)
    stations = (10, 23, 36, 49, 62, 75, 88, 101, 114, 124)
    for xx in stations:
        g.beam((xx, 24, 101), (xx, 36, 101), 1.6, 2)
        g.beam((xx, 24, 112), (xx, 36, 112), 1.6, 2)
    for i, (xa, xb) in enumerate(zip(stations[:-1], stations[1:])):
        za, zb = ((101, 112) if i % 2 == 0 else (112, 101))
        for yy in (24, 36):
            g.beam((xa, yy, za), (xb, yy, zb), 1.6, 2)
    # Rear ballast, high A-frame and tension stays.
    g.roundbox((3, 19, 93), (20, 41, 115), 2, 12)
    g.box((3, 18, 106), (20, 42, 110), 11)
    g.beam((32, 30, 113), (40, 30, 124), 2.4, 1)
    g.beam((48, 30, 113), (40, 30, 124), 2.4, 1)
    g.roundbox((36, 26, 123), (44, 34, 127), 1, 5)
    g.beam((40, 30, 125), (13, 30, 114), 1, 5)
    g.beam((40, 30, 125), (109, 30, 114), 1, 5)
    # Operator cabin projects toward the viewer, with ivory frame and inset panes.
    g.roundbox((45, 13, 83), (61, 30, 99), 2, 7)
    g.box((47, 12, 87), (59, 15, 96), 9)
    g.box((48, 11, 92), (58, 14, 96), 10)
    g.box((52, 11, 86), (54, 15, 97), 7)
    g.box((59, 17, 87), (62, 27, 96), 9)
    g.roundbox((44, 12, 98), (62, 31, 101), 1, 8)
    # Trolley, two ropes, hanging load block, and a deliberately open blunt J-hook.
    g.roundbox((94, 21, 97), (109, 39, 102), 2, 5)
    for xx in (98, 105):
        g.beam((xx, 30, 98), (xx, 30, 66), 1.2, 4)
    g.roundbox((95, 25, 60), (109, 35, 68), 2, 5)
    for xx in (96, 102):
        g.box((xx, 24, 61), (xx + 3, 27, 67), 1)
    hook_points = ((99, 30, 61), (99, 30, 56), (97, 30, 51), (100, 30, 46), (106, 30, 46), (111, 30, 50), (111, 30, 53))
    for a, b in zip(hook_points[:-1], hook_points[1:]):
        g.beam(a, b, 2, 4)
    return Asset('tower_crane', 'Tower crane', g, .065, [
        'Original four-shoe tower crane, open mast and jib trusses, rear ballast, cab, paired suspension ropes, load block and blunt open J-hook.',
        'Truss bays and hook throat retain empty native cells at both sizes. Static model; no structural load certification or rig.',
    ])


def office():
    g = Grid((128, 84, 72), PALETTE)
    for xx in (12, 116):
        for yy in (25, 73):
            g.roundbox((xx - 6, yy - 6, 0), (xx + 6, yy + 6, 10), 1.5, 4)
    g.roundbox((6, 20, 7), (122, 78, 64), 3, 7)
    # Broad wall corrugations are purposeful modular-container construction detail.
    for xx in range(13, 116, 7):
        g.box((xx, 19, 11), (xx + 2, 22, 61), 8)
        g.box((xx, 76, 11), (xx + 2, 79, 61), 8)
    for yy in range(27, 74, 7):
        g.box((5, yy, 11), (8, yy + 2, 61), 8)
        g.box((120, yy, 11), (123, yy + 2, 61), 8)
    for xx in (5, 117):
        for yy in (18, 73):
            g.roundbox((xx, yy, 5), (xx + 6, yy + 6, 65), 1, 5)
    g.roundbox((4, 18, 5), (124, 80, 11), 1.5, 5)
    g.roundbox((3, 17, 62), (125, 81, 68), 2.5, 5)
    g.roundbox((9, 22, 67), (119, 76, 70), 1, 6)
    for yy in range(25, 73, 7):
        g.box((11, yy, 69), (117, yy + 1, 71), 5)
    # Front door is closed; the handle, glazing, frame and landing make its function clear.
    g.roundbox((53, 15, 9), (81, 22, 56), 1.5, 8)
    g.box((57, 14, 10), (77, 18, 52), 5)
    g.box((60, 13, 35), (74, 16, 49), 9)
    g.box((61, 12, 44), (73, 15, 48), 10)
    g.roundbox((73, 11, 23), (76, 15, 30), 1, 8)
    g.roundbox((61, 14, 57), (73, 20, 61), 1, 11)
    for xx in (17, 87):
        g.roundbox((xx, 15, 29), (xx + 27, 22, 54), 1.5, 8)
        g.box((xx + 3, 14, 32), (xx + 24, 18, 51), 9)
        g.box((xx + 4, 13, 45), (xx + 23, 16, 50), 10)
        g.box((xx + 12, 12, 32), (xx + 15, 17, 51), 5)
        g.box((xx + 2, 12, 29), (xx + 25, 20, 32), 7)
    # A side window and a compact external AC unit are separate readable wall fittings.
    g.roundbox((120, 27, 30), (125, 47, 54), 1, 8)
    g.box((123, 30, 33), (126, 44, 51), 9)
    g.box((124, 31, 45), (127, 43, 50), 10)
    g.box((124, 36, 33), (127, 39, 51), 5)
    g.roundbox((120, 55, 31), (128, 73, 49), 2, 8)
    g.box((126, 58, 34), (128, 70, 46), 4)
    for yy in (59, 63, 67):
        g.box((127, yy, 35), (128, yy + 1, 45), 6)
    g.box((121, 59, 25), (125, 62, 32), 5)
    g.box((121, 68, 25), (125, 71, 32), 5)
    # Real access steps, three rising treads; yellow paint marks only their edges.
    g.roundbox((52, 1, 0), (83, 19, 4), 1.5, 5)
    g.roundbox((54, 7, 4), (81, 20, 8), 1, 6)
    g.roundbox((56, 13, 8), (79, 21, 11), 1, 5)
    for xx, yy, zz, width in ((52, 1, 1, 31), (54, 7, 5, 27), (56, 13, 9, 23)):
        g.box((xx, yy, zz), (xx + 3, yy + 5, zz + 3), 1)
        g.box((xx + width - 3, yy, zz), (xx + width, yy + 5, zz + 3), 1)
    for xx in (5, 118):
        g.box((xx, 16, 62), (xx + 5, 20, 67), 11)
        g.box((xx, 17, 7), (xx + 5, 20, 11), 11)
    return Asset('site_office', 'Portable site office', g, .05, [
        'Original modular site office with stepped rounded container envelope, ribbed cladding, framed opaque windows, closed glazed door, handle, three access steps, raised corner feet and wall AC.',
        'No modeled interior. Corrugation and small highlights simplify under conservative half reduction.',
    ])


def make_assets():
    return [mixer(), loader(), crane(), office()]


if __name__ == '__main__':
    run_theme(Path(__file__).resolve().parent, make_assets())
