"""Original combine harvester addition, authored as native occupied voxel cells."""
from pathlib import Path
import sys
import math
import numpy as np

sys.dont_write_bytecode = True
sys.path.insert(0, 'D:/github/AstraEffort/voxel/_tools')
from voxelkit import Grid, Asset, run_theme

# The accepted farm palette is reused for visual continuity only; geometry is new.
PALETTE = [
    (0, 0, 0, 0), (40, 43, 40, 255), (62, 68, 65, 255),
    (86, 92, 87, 255), (123, 130, 120, 255), (98, 116, 57, 255),
    (126, 142, 73, 255), (67, 83, 43, 255), (230, 219, 174, 255),
    (170, 76, 41, 255), (195, 96, 53, 255), (133, 58, 35, 255),
    (151, 106, 55, 255), (181, 132, 72, 255), (101, 72, 42, 255),
    (207, 199, 173, 255), (161, 160, 144, 255), (126, 128, 117, 255),
    (160, 186, 181, 255), (108, 137, 137, 255), (220, 157, 48, 255),
    (245, 232, 185, 255), (121, 89, 44, 255), (189, 155, 73, 255),
    (190, 192, 171, 255), (224, 214, 183, 255),
]
TIRE, IRON_D, IRON, METAL = 1, 2, 3, 4
OLIVE, OLIVE_L, OLIVE_D, IVORY = 5, 6, 7, 8
RED, RED_L = 9, 10
GLASS, GLASS_D, AMBER, LAMP, STRAW, BOLT = 18, 19, 20, 21, 23, 24


def wheel(g, x, y, z, radius, width, outward):
    # Rounded tire shoulders plus deliberate cross-tread bars, without random noise.
    g.cylinder((x, y, z), radius - 3, width * 2, 0, TIRE)
    g.ellipsoid((x, y, z), (width, radius, radius), TIRE)
    count = 16 if radius > 20 else 12
    for i in range(count):
        a = i * math.tau / count
        rr = radius - 0.5
        g.beam((x - width * 0.72, y + rr * math.cos(a - 0.055), z + rr * math.sin(a - 0.055)),
               (x + width * 0.72, y + rr * math.cos(a + 0.055), z + rr * math.sin(a + 0.055)),
               1.7, IRON_D)
    side = x + outward * (width - 0.5)
    g.cylinder((side, y, z), radius * 0.57, 3, 0, IVORY)
    g.cylinder((side + outward, y, z), radius * 0.43, 3, 0, OLIVE)
    g.cylinder((side + outward * 2, y, z), 3.4, 4, 0, IRON)
    for i in range(6):
        a = i * math.tau / 6
        bolt_r = radius * 0.29
        g.cylinder((side + outward * 2, y + bolt_r * math.cos(a), z + bolt_r * math.sin(a)),
                   1.2, 2.5, 0, BOLT)


def combine_harvester():
    g = Grid((128, 128, 112), PALETTE)
    # Elevated main chassis, two large front drive wheels and two rear steering wheels.
    g.roundbox((36, 43, 28), (78, 117, 40), 3, IRON_D)
    g.cylinder((56, 62, 26), 4.5, 64, 0, IRON)
    g.cylinder((56, 106, 18), 3.4, 53, 0, IRON)
    wheel(g, 28, 62, 26, 24, 9, -1)
    wheel(g, 84, 62, 26, 24, 9, 1)
    wheel(g, 33, 106, 18, 16, 7, -1)
    wheel(g, 79, 106, 18, 16, 7, 1)
    g.roundbox((36, 65, 38), (80, 115, 85), 6, OLIVE)
    g.roundbox((39, 69, 81), (77, 111, 88), 3, OLIVE_L)
    # Large restrained body panels, cream stripe and physical service latches.
    for x0 in (33, 78):
        g.roundbox((x0, 70, 44), (x0 + 5, 110, 80), 2, OLIVE)
        g.box((x0 - 1, 71, 62), (x0 + 6, 108, 69), IVORY)
        g.box((x0 - 1, 71, 59), (x0 + 6, 108, 62), AMBER)
        for yy in (75, 101):
            g.box((x0 - 1, yy, 47), (x0 + 6, yy + 2, 58), OLIVE_D)
        g.box((x0 - 1, 87, 51), (x0 + 6, 93, 54), METAL)
    # A dark radiator, lamp pair, bumper and tow point make the rear mechanically useful.
    g.roundbox((40, 112, 47), (75, 119, 78), 3, IRON_D)
    for zz in range(50, 77, 5):
        g.box((43, 117, zz), (72, 121, zz + 2), METAL)
    g.roundbox((35, 113, 30), (81, 120, 37), 2, IRON)
    for xx in (36, 75):
        g.box((xx, 116, 40), (xx + 6, 121, 45), RED)
    g.box((52, 116, 24), (63, 125, 30), IRON_D)
    g.box((55, 121, 23), (60, 124, 31), 0)
    # A raised cab with raked front glass and stout framing.
    g.roundbox((31, 38, 49), (81, 71, 58), 4, OLIVE)
    g.box((34, 43, 58), (78, 68, 90), GLASS_D)
    face_y = 39 + 0.18 * (g.z - 60)
    windshield = (g.x >= 35) & (g.x < 77) & (g.z >= 60) & (g.z < 90) & (g.y >= face_y) & (g.y < 46)
    g.data[windshield] = GLASS
    g.data[windshield & ((g.x < 38) | (g.x >= 74) | (g.z < 63) | (g.z >= 87))] = IRON_D
    g.data[windshield & (g.x >= 54) & (g.x < 57)] = IRON_D
    for xx in (33, 76):
        g.box((xx, 45, 61), (xx + 3, 66, 89), GLASS)
        for yy in (44, 64):
            g.box((xx - 1, yy, 57), (xx + 4, yy + 4, 91), IRON_D)
        g.box((xx - 1, 45, 58), (xx + 4, 67, 62), IRON_D)
        g.box((xx - 1, 55, 64), (xx + 4, 61, 67), METAL)
    g.box((35, 65, 59), (77, 69, 90), IRON_D)
    g.box((39, 68, 65), (72, 71, 86), GLASS_D)
    g.roundbox((29, 36, 90), (83, 73, 98), 3, IVORY)
    g.roundbox((35, 42, 96), (77, 67, 101), 3, LAMP)
    for xx in (36, 53, 70):
        g.roundbox((xx, 34, 91), (xx + 7, 39, 96), 1, IRON_D)
        g.box((xx + 1, 33, 92), (xx + 6, 36, 95), LAMP)
    for xx in (33, 79):
        g.cylinder((xx, 43, 101), 2.6, 5, 2, AMBER)
    for xx, mx in ((35, 26), (77, 86)):
        g.beam((xx, 45, 83), (mx, 42, 83), 1.6, IRON_D)
        g.roundbox((mx - 2, 39, 76), (mx + 3, 44, 86), 1, IRON_D)
        g.box((mx - 1, 38, 78), (mx + 2, 41, 84), METAL)
    for xx in (31, 75):
        g.box((xx, 36, 51), (xx + 6, 41, 56), AMBER)
    # A genuinely open flared grain hopper rises behind the cab.
    zx = g.z - 84
    outer = (g.z >= 84) & (g.z < 107) & (np.abs(g.x - 58) <= 17 + 0.30 * zx) & (np.abs(g.y - 89) <= 12 + 0.27 * zx)
    inner = (g.z >= 91) & (g.z < 110) & (np.abs(g.x - 58) < 14 + 0.30 * zx) & (np.abs(g.y - 89) < 9 + 0.27 * zx)
    g.data[outer] = OLIVE
    g.data[inner] = 0
    g.box((44, 80, 90), (72, 98, 92), IRON_D)
    g.box((34, 71, 104), (82, 75, 109), OLIVE_L)
    g.box((34, 103, 104), (82, 107, 109), OLIVE_L)
    g.box((34, 75, 104), (38, 103, 109), OLIVE_L)
    g.box((78, 75, 104), (82, 103, 109), OLIVE_L)
    # Horizontal unloading auger, collars and downturned open discharge boot.
    g.cylinder((79, 87, 84), 7.5, 10, 0, OLIVE_D)
    g.beam((79, 87, 84), (119, 79, 85), 5.4, OLIVE)
    for ta, tb in ((0.12, 0.20), (0.73, 0.81)):
        a = (79 + 40 * ta, 87 - 8 * ta, 84 + ta)
        b = (79 + 40 * tb, 87 - 8 * tb, 84 + tb)
        g.beam(a, b, 6.3, IRON_D)
    g.beam((114, 80, 85), (118, 79, 85), 5.8, IVORY)
    g.beam((119, 79, 85), (121, 79, 76), 5.6, IRON_D)
    g.cylinder((121, 79, 73.5), 3, 7, 2, 0)
    # Feed neck and lifting links join the cutter assembly to the chassis.
    g.roundbox((43, 28, 17), (69, 48, 34), 3, OLIVE_D)
    g.roundbox((47, 31, 28), (65, 49, 40), 3, OLIVE)
    for xx in (38, 74):
        g.beam((xx, 51, 38), (xx, 29, 20), 2.8, IRON_D)
        g.beam((xx, 44, 32), (xx, 34, 23), 3.6, METAL)
    # Broad green header trough and tapered cutter teeth in front of the open reel.
    g.roundbox((4, 10, 7), (110, 35, 16), 3, OLIVE)
    g.roundbox((8, 29, 14), (106, 36, 37), 2, OLIVE_D)
    g.box((10, 30, 31), (104, 35, 35), OLIVE_L)
    for xa, xb in ((2, 12), (102, 112)):
        g.roundbox((xa, 7, 7), (xb, 36, 33), 3, OLIVE)
        g.box((xa, 12, 19), (xb, 29, 23), IVORY)
        g.box((xa, 8, 8), (xb, 14, 13), AMBER)
    g.box((11, 6, 9), (103, 13, 13), AMBER)
    for xx in range(12, 103, 6):
        g.box((xx, 3, 7), (xx + 3, 12, 11), IRON)
        g.box((xx + 1, 1, 8), (xx + 3, 5, 10), METAL)
    # Low feed auger behind the reel: solid shaft with regularly spaced flights.
    g.cylinder((56, 28, 18), 5.2, 88, 0, METAL)
    for xx in range(14, 103, 10):
        g.torus((xx, 28, 18), 5.1, 1.2, 0, IRON_D)
    # Four circular reel supports with spokes, six axial battens and two tine rows.
    g.cylinder((56, 18, 28), 2.7, 100, 0, IRON_D)
    for xx in (15, 43, 71, 99):
        g.torus((xx, 18, 28), 9, 1.8, 0, AMBER)
        for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
            g.beam((xx, 18, 28), (xx, 18 + 9 * math.cos(a), 28 + 9 * math.sin(a)), 1.6, AMBER)
    for a in np.linspace(math.pi / 6, math.tau + math.pi / 6, 6, endpoint=False):
        yy, zz = 18 + 9 * math.cos(a), 28 + 9 * math.sin(a)
        g.beam((13, yy, zz), (101, yy, zz), 1.6, IRON)
    for a in (3 * math.pi / 4, 5 * math.pi / 4):
        yy, zz = 18 + 9 * math.cos(a), 28 + 9 * math.sin(a)
        g.beam((13, yy, zz), (101, yy, zz), 1.5, METAL)
        for xx in range(15, 102, 6):
            g.beam((xx, yy, zz), (xx, yy - 1.2, zz - 4.5), 1.25, METAL)
    for xx in (8, 106):
        g.beam((xx, 30, 16), (xx, 18, 28), 2.5, IRON_D)
        g.cylinder((xx, 18, 28), 6.4, 4, 0, IRON_D)
        g.cylinder((xx, 18, 28), 2.5, 5, 0, METAL)
    # Curved front mudguards and a right-side access ladder clear the wheel hubs.
    rad = np.sqrt((g.y - 62) ** 2 + (g.z - 26) ** 2)
    for xa, xb in ((18, 38), (74, 94)):
        fender = (g.x >= xa) & (g.x < xb) & (rad >= 26.7) & (rad < 30) & (g.z >= 37)
        g.data[fender] = OLIVE
        g.data[fender & ((g.x < xa + 3) | (g.x >= xb - 3))] = OLIVE_L
    g.box((79, 67, 53), (99, 86, 57), IRON_D)
    for yy in (69, 83):
        g.beam((97, yy, 13), (97, yy, 67), 1.6, IRON_D)
        g.beam((97, yy, 66), (83, yy, 66), 1.6, IRON_D)
    for zz in range(16, 58, 7):
        g.box((94, 68, zz), (100, 85, zz + 3), METAL)
    return Asset('combine_harvester', 'Farm combine harvester', g, voxel_size=0.065, notes=[
        'Original harvesting machine with a wide native open reel, circular supports, spokes, battens, tine rows, cutter teeth, feed auger and lifting/feed connection.',
        'Four rounded wheels, raised cab, grain body with a physically open hopper, and a separate unloading auger with collars and a downturned open discharge boot.',
        'Accepted farm palette retained for style continuity only. All geometry authored in this isolated addition; no accepted original asset geometry or source copied.',
        'Opaque flat-color glazing and static machinery. No rig, cutting simulation, grain particles, animation, collision or engine integration.'
    ])


def make_assets():
    return [combine_harvester()]


if __name__ == '__main__':
    run_theme(Path(__file__).resolve().parent, make_assets())
