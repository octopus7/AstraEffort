"""Original farm voxel geometry. Native occupied cells are the source of truth."""
from pathlib import Path
import sys
import math
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_tools'))
from voxelkit import Grid, Asset, run_theme


PALETTE = [
    (0, 0, 0, 0),
    (40, 43, 40, 255),       # 1 tire / very dark recess
    (62, 68, 65, 255),       # 2 dark iron
    (86, 92, 87, 255),       # 3 iron
    (123, 130, 120, 255),    # 4 worn metal
    (98, 116, 57, 255),      # 5 olive paint
    (126, 142, 73, 255),     # 6 olive highlights
    (67, 83, 43, 255),       # 7 deep olive
    (230, 219, 174, 255),    # 8 warm ivory
    (170, 76, 41, 255),      # 9 terracotta
    (195, 96, 53, 255),      # 10 roof highlights
    (133, 58, 35, 255),      # 11 dark terracotta
    (151, 106, 55, 255),     # 12 timber
    (181, 132, 72, 255),     # 13 light timber
    (101, 72, 42, 255),      # 14 dark timber
    (207, 199, 173, 255),    # 15 warm plaster
    (161, 160, 144, 255),    # 16 stone
    (126, 128, 117, 255),    # 17 mortar / dark stone
    (160, 186, 181, 255),    # 18 pale opaque glass
    (108, 137, 137, 255),    # 19 glass shade
    (220, 157, 48, 255),     # 20 amber lamp
    (245, 232, 185, 255),    # 21 headlight / sail highlight
    (121, 89, 44, 255),      # 22 grain binding
    (189, 155, 73, 255),     # 23 straw
    (190, 192, 171, 255),    # 24 bolts
    (224, 214, 183, 255),    # 25 sail canvas
]
BLACK, IRON_D, IRON, METAL = 1, 2, 3, 4
OLIVE, OLIVE_L, OLIVE_D, IVORY = 5, 6, 7, 8
ROOF, ROOF_L, ROOF_D, WOOD, WOOD_L, WOOD_D = 9, 10, 11, 12, 13, 14
PLASTER, STONE, MORTAR, GLASS, GLASS_D = 15, 16, 17, 18, 19
AMBER, LAMP, BINDING, STRAW, BOLT, CANVAS = 20, 21, 22, 23, 24, 25


def cylinder_shell(g, center, radius, length, axis, thickness, color):
    axes = [g.x, g.y, g.z]
    axial = np.abs(axes[axis] - center[axis]) <= length / 2
    radial2 = sum((axes[i] - center[i]) ** 2 for i in range(3) if i != axis)
    g.data[axial & (radial2 <= radius * radius) &
           (radial2 >= (radius - thickness) ** 2)] = color


def xy_panel(g, a, b, z0, z1, thickness, color):
    """A voxel panel with endpoints in XY, used for genuinely open barn doors."""
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    delta = b - a
    length = np.linalg.norm(delta)
    u = delta / length
    t = (g.x - a[0]) * u[0] + (g.y - a[1]) * u[1]
    n = -(g.x - a[0]) * u[1] + (g.y - a[1]) * u[0]
    g.data[(t >= 0) & (t <= length) & (np.abs(n) <= thickness / 2) &
           (g.z >= z0) & (g.z < z1)] = color


def tractor_wheel(g, cx, cy, cz, radius, halfwidth, rear):
    dx = g.x - cx
    dy = g.y - cy
    dz = g.z - cz
    radial = np.sqrt(dy * dy + dz * dz)
    theta = np.arctan2(dz, dy)
    barrel_radius = radius - 2.4 * (np.abs(dx) / halfwidth) ** 3
    g.data[(np.abs(dx) <= halfwidth) & (radial <= barrel_radius)] = BLACK
    # Regular diagonal tread blocks are physical projections, not texture noise.
    tread = np.cos((14 if rear else 12) * theta + np.abs(dx) * 0.24) > 0.38
    g.data[(np.abs(dx) <= halfwidth - 0.5) &
           (radial >= barrel_radius - 1.5) & (radial <= barrel_radius + 1.8) & tread] = IRON_D
    side = -1 if cx < 48 else 1
    outer = cx + side * (halfwidth - 0.5)
    hub_r = 15 if rear else 10
    g.cylinder((outer, cy, cz), hub_r, 2.8, 0, IVORY)
    g.cylinder((outer + side * 1.2, cy, cz), hub_r - 3, 3, 0, OLIVE)
    g.cylinder((outer + side * 2, cy, cz), 4 if rear else 3.5, 4, 0, IRON)
    for angle in range(0, 360, 60):
        a = math.radians(angle)
        rr = 8 if rear else 5.5
        g.cylinder((outer + side * 2.3, cy + rr * math.cos(a), cz + rr * math.sin(a)),
                   1.3, 2, 0, BOLT)


def tractor():
    g = Grid((96, 128, 96), PALETTE)
    g.box((31, 15, 18), (65, 110, 30), IRON_D)
    g.cylinder((48, 91, 27), 5, 76, 0, IRON)
    g.cylinder((48, 26, 19), 4, 73, 0, IRON)
    for cx in (16, 80):
        tractor_wheel(g, cx, 91, 27, 25, 10, True)
        tractor_wheel(g, cx, 26, 19, 17, 9, False)

    g.roundbox((30, 11, 30), (66, 64, 57), 5, OLIVE)
    g.box((32, 17, 30), (64, 62, 35), OLIVE_D)
    g.roundbox((33, 16, 54), (63, 59, 59), 2, OLIVE_L)
    g.box((36, 16, 58), (41, 56, 60), OLIVE_D)
    g.box((29, 18, 44), (31, 55, 48), IVORY)
    g.box((65, 18, 44), (67, 55, 48), IVORY)
    for side in (29, 65):
        for yy in range(23, 49, 5):
            g.box((side, yy, 35), (side + 2, yy + 2, 42), OLIVE_D)
    # Deep radiator, spaced vertical bars, paired headlights, and a stout bumper.
    g.roundbox((32, 8, 34), (64, 13, 53), 2, IRON_D)
    for xx in range(34, 64, 4):
        g.box((xx, 7, 36), (xx + 2, 10, 51), METAL)
    for xx in (29, 60):
        g.roundbox((xx, 7, 47), (xx + 7, 11, 55), 1.4, IVORY)
        g.box((xx + 1, 6, 48), (xx + 6, 8, 53), LAMP)
    g.roundbox((23, 1, 18), (73, 10, 27), 2.5, IRON)
    g.box((29, 0, 20), (37, 3, 24), METAL)
    g.box((59, 0, 20), (67, 3, 24), METAL)

    # Cab sill, pale solid-color glazing, strong frame, and raised roof cap.
    g.roundbox((28, 60, 32), (68, 102, 43), 3, OLIVE_D)
    g.box((31, 64, 43), (65, 98, 80), GLASS_D)
    g.box((31, 60, 54), (65, 64, 81), GLASS)
    g.box((27, 64, 51), (31, 98, 80), GLASS)
    g.box((65, 64, 51), (69, 98, 80), GLASS)
    g.box((31, 98, 53), (65, 101, 80), GLASS_D)
    for xx in (28, 64):
        for yy in (61, 97):
            g.beam((xx + 2, yy + 1, 40), (xx + 2, yy + 1, 82), 2.3, IRON_D)
    g.box((29, 60, 79), (67, 102, 83), IRON_D)
    g.box((29, 60, 50), (67, 64, 54), IRON_D)
    g.box((46, 60, 54), (49, 64, 80), IRON_D)
    for xx in (27, 66):
        g.box((xx, 82, 49), (xx + 3, 85, 80), IRON_D)
        g.box((xx, 64, 48), (xx + 3, 99, 52), IRON_D)
        g.box((xx - 1, 84, 56), (xx + 4, 91, 59), METAL)
    g.roundbox((24, 57, 82), (72, 106, 89), 4, IVORY)
    g.roundbox((29, 62, 88), (67, 101, 92), 3, LAMP)
    g.box((27, 59, 81), (69, 104, 84), OLIVE_D)
    for xx in (27, 64):
        g.roundbox((xx, 59, 87), (xx + 5, 65, 93), 1, AMBER)
    # Exhaust, intake, mirrors and access treads all survive a 2-cell reduction.
    g.cylinder((38, 53, 67), 3, 23, 2, IRON_D)
    g.beam((38, 53, 78), (38, 50, 82), 3, IRON_D)
    g.box((35, 48, 80), (41, 53, 83), METAL)
    g.cylinder((59, 48, 61), 2.5, 11, 2, IRON)
    g.cylinder((59, 48, 67), 4, 3, 2, IRON_D)
    for side in (-1, 1):
        sx = 48 + side * 26
        g.beam((48 + side * 19, 65, 76), (sx, 60, 76), 1.6, IRON_D)
        g.roundbox((sx - 2, 58, 69), (sx + 3, 62, 79), 1, IRON_D)
        g.box((sx - 1, 57, 71), (sx + 2, 59, 77), METAL)
        x0 = 21 if side < 0 else 65
        for yy, zz in ((67, 24), (70, 31)):
            g.box((x0, yy, zz), (x0 + 10, yy + 12, zz + 4), IRON)
            for ybar in range(yy + 1, yy + 11, 4):
                g.box((x0, ybar, zz + 3), (x0 + 10, ybar + 2, zz + 5), METAL)
    # Curved rear mudguards follow the wheel radius instead of boxy covers.
    radial = np.sqrt((g.y - 91) ** 2 + (g.z - 27) ** 2)
    for x0, x1 in ((6, 30), (66, 90)):
        guard = (g.x >= x0) & (g.x < x1) & (radial >= 28) & (radial <= 32) & (g.z >= 35)
        g.data[guard] = OLIVE
        g.data[guard & ((g.x < x0 + 3) | (g.x >= x1 - 3))] = OLIVE_L
    # Rear service panel, tail lamps, PTO coupling, and three-point hitch.
    g.box((32, 102, 31), (64, 107, 45), OLIVE_D)
    for xx in (29, 60):
        g.box((xx, 104, 45), (xx + 7, 109, 51), IRON_D)
        g.box((xx, 108, 46), (xx + 4, 110, 50), ROOF)
        g.box((xx + 4, 108, 46), (xx + 7, 110, 50), AMBER)
    g.cylinder((48, 110, 24), 5, 11, 1, METAL)
    g.cylinder((48, 116, 24), 3, 4, 1, IRON_D)
    for xx in (33, 63):
        target = 36 if xx < 48 else 60
        g.beam((xx, 103, 29), (target, 122, 17), 2.5, IRON)
        g.cylinder((target, 122, 17), 4, 4, 0, METAL)
    g.box((42, 108, 13), (54, 124, 18), IRON_D)
    g.box((38, 121, 13), (58, 127, 18), IRON)
    g.box((44, 122, 12), (52, 126, 19), 0)
    return Asset('tractor', 'Orchard tractor', g, voxel_size=0.04, notes=[
        'Original olive tractor with physical diagonal tread blocks, stepped round mudguards, radiator, lamps, mirrors, side steps, exhaust and a rear three-point hitch/PTO.',
        'Glazing is an opaque palette color; no transparency or interior simulation is claimed.',
        'Functional frame members and hitch are at least 3-5 large cells thick. Half uses the shared conservative grid reducer without mesh scaling.'
    ])


def stone_plinth(g, x0, x1, y0, y1, z1, thickness=6):
    g.box((x0, y0, 0), (x1, y1, z1), MORTAR)
    for z0 in range(0, z1, 5):
        offset = 0 if (z0 // 5) % 2 == 0 else 6
        for xx in range(x0 - offset, x1, 12):
            xa, xb = max(x0, xx + 1), min(x1, xx + 11)
            if xb > xa:
                g.box((xa, y0, z0 + 1), (xb, y0 + thickness, min(z0 + 5, z1)), STONE)
                g.box((xa, y1 - thickness, z0 + 1), (xb, y1, min(z0 + 5, z1)), STONE)
        for yy in range(y0 - offset, y1, 12):
            ya, yb = max(y0, yy + 1), min(y1, yy + 11)
            if yb > ya:
                g.box((x0, ya, z0 + 1), (x0 + thickness, yb, min(z0 + 5, z1)), STONE)
                g.box((x1 - thickness, ya, z0 + 1), (x1, yb, min(z0 + 5, z1)), STONE)


def open_barn_door(g, hinge, end):
    a, b = np.array(hinge, dtype=float), np.array(end, dtype=float)
    xy_panel(g, a, b, 11, 61, 4, WOOD)
    delta = b - a
    length = np.linalg.norm(delta)
    for t0 in np.arange(0, length, 5):
        p, q = a + delta * (t0 / length), a + delta * (min(t0 + 3, length) / length)
        xy_panel(g, p, q, 13, 59, 4.5, WOOD_L)
    for zz in (15, 56):
        g.beam((*a, zz), (*b, zz), 1.7, WOOD_D)
    g.beam((*a, 14), (*b, 58), 1.8, IVORY)
    g.beam((*a, 58), (*b, 14), 1.8, WOOD_L)
    for zz in (19, 53):
        p = a + delta * 0.45
        g.beam((*a, zz), (*p, zz), 1.8, IRON)
        g.cylinder((*a, zz), 2, 7, 2, IRON_D)
    latch = a + delta * 0.83
    g.box((latch[0] - 1.5, latch[1] - 3, 31), (latch[0] + 1.5, latch[1] + 3, 39), IRON_D)


def barn():
    g = Grid((120, 128, 120), PALETTE)
    stone_plinth(g, 10, 110, 10, 118, 11)
    g.box((18, 17, 5), (102, 111, 10), WOOD)
    for xx in range(20, 102, 7):
        g.box((xx, 18, 9), (xx + 1, 110, 10), WOOD_D)
    g.box((14, 15, 11), (20, 113, 75), WOOD_D)
    g.box((100, 15, 11), (106, 113, 75), WOOD_D)
    g.box((14, 15, 11), (106, 21, 75), WOOD_D)
    g.box((14, 107, 11), (106, 113, 75), WOOD_D)
    for xx in range(15, 106, 6):
        col = WOOD_L if (xx // 6) % 3 == 0 else WOOD
        g.box((xx, 14, 12), (min(xx + 5, 106), 21, 75), col)
        g.box((xx, 107, 12), (min(xx + 5, 106), 114, 75), col)
    for yy in range(16, 113, 6):
        col = WOOD_L if (yy // 6) % 3 == 0 else WOOD
        g.box((13, yy, 12), (20, min(yy + 5, 113), 75), col)
        g.box((100, yy, 12), (107, min(yy + 5, 113), 75), col)
    # Full gable walls beneath a separately modeled sloping roof shell.
    roof_h = 112 - 0.70 * np.abs(g.x - 60)
    gable = (g.x >= 14) & (g.x < 106) & (g.z >= 74) & (g.z < roof_h - 4)
    g.data[gable & (((g.y >= 15) & (g.y < 21)) | ((g.y >= 107) & (g.y < 113)))] = WOOD
    for xx in range(18, 106, 7):
        mask = (g.x >= xx) & (g.x < xx + 1.5) & (g.z >= 76) & (g.z < roof_h - 4)
        g.data[mask & (((g.y >= 14) & (g.y < 21)) | ((g.y >= 107) & (g.y < 114)))] = WOOD_D
    # Structural corner posts, lintels, and inner trusses are substantial voxels.
    for xx in (14, 101):
        for yy in (14, 108):
            g.box((xx, yy, 10), (xx + 5, yy + 6, 76), WOOD_D)
            g.box((xx + 1, yy - 1, 12), (xx + 4, yy + 6, 74), WOOD_L)
    g.box((13, 12, 69), (107, 21, 76), WOOD_D)
    g.box((13, 12, 72), (107, 16, 76), WOOD_L)
    g.box((13, 106, 69), (107, 115, 76), WOOD_D)
    for yy in (41, 83):
        g.box((21, yy, 66), (99, yy + 4, 71), WOOD_D)
        g.beam((21, yy + 2, 68), (60, yy + 2, 103), 2, WOOD_D)
        g.beam((99, yy + 2, 68), (60, yy + 2, 103), 2, WOOD_D)
    # Open paired front doors, clear threshold and hay visible through the opening.
    g.box((36, 9, 10), (84, 24, 64), 0)
    for xx in (32, 83):
        g.box((xx, 12, 10), (xx + 5, 22, 66), WOOD_D)
        g.box((xx + 1, 10, 12), (xx + 4, 14, 64), WOOD_L)
    g.box((32, 11, 62), (88, 21, 68), WOOD_L)
    g.box((36, 8, 7), (84, 25, 11), WOOD_L)
    open_barn_door(g, (36, 13), (18, 4))
    open_barn_door(g, (84, 13), (102, 4))
    for x0, y0, z0, width in ((25, 47, 10, 23), (25, 67, 10, 23), (26, 59, 24, 21), (73, 82, 10, 22)):
        g.roundbox((x0, y0, z0), (x0 + width, y0 + 16, z0 + 14), 2.5, STRAW)
        for xx in (x0 + 5, x0 + width - 6):
            g.box((xx, y0, z0), (xx + 2, y0 + 16, z0 + 14), BINDING)
        for zz in (z0 + 4, z0 + 8):
            g.box((x0, y0, zz), (x0 + width, y0 + 1, zz + 1), WOOD_L)
    # Framed loft apertures front and rear.
    for y0 in (12, 111):
        g.box((48, y0, 79), (72, y0 + 5, 100), WOOD_D)
        g.box((52, y0 - 1, 82), (68, y0 + 6, 96), GLASS_D)
        g.box((58, y0 - 2, 81), (62, y0 + 6, 98), WOOD_L)
        g.box((49, y0 - 2, 78), (71, y0 + 6, 82), WOOD_L)
        g.box((49, y0 - 2, 97), (71, y0 + 6, 101), WOOD_L)
    # Side windows and real framing on both walls.
    for xx in (11, 103):
        for yy in (41, 82):
            g.box((xx, yy - 9, 31), (xx + 6, yy + 10, 54), IVORY)
            g.box((xx - 1, yy - 5, 35), (xx + 7, yy + 6, 50), GLASS_D)
            g.box((xx - 1, yy - 1, 34), (xx + 7, yy + 2, 51), IVORY)
            g.box((xx - 1, yy - 6, 41), (xx + 7, yy + 7, 44), IVORY)
    # Rear service door, strap hinges, utility hatch and rain drainage.
    g.box((43, 111, 11), (77, 117, 56), WOOD_D)
    g.box((47, 114, 12), (73, 118, 52), WOOD)
    for xx in (49, 55, 61, 67):
        g.box((xx, 117, 14), (xx + 4, 119, 50), WOOD_L)
    g.box((58, 117, 12), (62, 120, 53), WOOD_D)
    for zz in (19, 45):
        g.box((45, 118, zz), (56, 121, zz + 3), IRON)
        g.box((64, 118, zz), (75, 121, zz + 3), IRON)
    g.box((61, 119, 30), (65, 122, 36), IRON_D)
    # Terracotta roof uses purposeful courses and raised tile seams.
    roof_mask = (g.x >= 3) & (g.x < 117) & (g.y >= 2) & (g.y < 126) & (g.z >= roof_h - 4) & (g.z < roof_h + 1)
    g.data[roof_mask] = ROOF
    tile_course = (np.floor(np.abs(g.x - 60) / 7) % 2) == 0
    g.data[roof_mask & tile_course] = ROOF_L
    tile_joint = (np.mod(g.y + 5 * np.floor(np.abs(g.x - 60) / 7), 14) < 1.5)
    g.data[roof_mask & tile_joint] = ROOF_D
    for yy in (2, 122):
        trim = (g.x >= 5) & (g.x < 115) & (g.y >= yy) & (g.y < yy + 4) & (g.z >= roof_h - 8) & (g.z < roof_h - 3)
        g.data[trim] = IVORY
    g.roundbox((56, 1, 109), (64, 127, 116), 2, ROOF_L)
    for xx in (5, 111):
        g.box((xx, 8, 68), (xx + 4, 121, 71), IRON_D)
        g.cylinder((xx + 2, 114, 39), 2, 58, 2, IRON)
        g.beam((xx + 2, 114, 11), (xx + 2, 122, 8), 2, IRON)
    return Asset('barn', 'Timber harvest barn', g, voxel_size=0.065, notes=[
        'Hollow timber barn with individually modeled open front door leaves, braces and hinges, visible hay bales, roof shell, ridge tiles, side windows and interior trusses.',
        'Rear has a separate service door and loft window. Eave gutters and downpipes serve both roof sides.',
        'Stone courses and regular timber/roof divisions are deterministic structural detailing, not random surface noise.'
    ])


def silo():
    g = Grid((80, 92, 128), PALETTE)
    # Four legs and individual feet rather than a display plinth.
    for xx in (17, 63):
        for yy in (21, 65):
            g.roundbox((xx - 6, yy - 6, 0), (xx + 6, yy + 6, 6), 1, STONE)
            g.box((xx - 4, yy - 4, 5), (xx + 4, yy + 4, 50), IRON_D)
            g.box((xx - 3, yy - 3, 6), (xx + 3, yy + 3, 49), IRON)
            g.box((xx - 5, yy - 5, 6), (xx + 5, yy + 5, 9), METAL)
    for yy in (21, 65):
        g.beam((17, yy, 12), (63, yy, 42), 1.8, IRON_D)
        g.beam((63, yy, 12), (17, yy, 42), 1.8, IRON_D)
    for xx in (17, 63):
        g.beam((xx, 21, 12), (xx, 65, 42), 1.8, IRON_D)
    g.cone((40, 43, 34), 8, 28, 30, 2, PLASTER)
    g.cylinder((40, 43, 78), 28, 65, 2, PLASTER)
    radial = np.sqrt((g.x - 40) ** 2 + (g.y - 43) ** 2)
    theta = np.arctan2(g.y - 43, g.x - 40)
    panel_seam = np.abs(np.sin(theta * 10)) < 0.10
    g.data[(radial > 26.5) & (radial <= 28.1) & (g.z > 48) & (g.z < 109) & panel_seam] = STONE
    for zz in (50, 73, 101, 109):
        cylinder_shell(g, (40, 43, zz), 29.4, 3.5, 2, 2.2, IRON)
        for angle in range(0, 360, 30):
            a = math.radians(angle)
            x, y = 40 + 28.9 * math.cos(a), 43 + 28.9 * math.sin(a)
            g.ellipsoid((x, y, zz), (1.4, 1.4, 1.4), BOLT)
    for zz in (62, 86):
        cylinder_shell(g, (40, 43, zz), 28.1, 1.2, 2, 1.1, STONE)
    # Rounded stepped cap made from a clipped ellipsoid, with concentric courses.
    dome = ((g.x - 40) / 30.5) ** 2 + ((g.y - 43) / 30.5) ** 2 + ((g.z - 109) / 15) ** 2
    cap = (dome <= 1) & (g.z >= 109)
    g.data[cap] = ROOF
    g.data[cap & (np.mod(g.z - 109, 4) < 1.2)] = ROOF_L
    g.cylinder((40, 43, 110), 31, 4, 2, ROOF_L)
    g.cylinder((40, 43, 124), 7, 4, 2, IRON_D)
    g.cylinder((40, 43, 126), 5, 3, 2, METAL)
    # Bottom discharge with a gate and angled auger spout, visibly open at its end.
    g.cylinder((40, 43, 19), 8, 9, 2, IRON)
    g.box((31, 35, 14), (49, 51, 18), METAL)
    g.box((47, 38, 14), (58, 43, 17), IRON_D)
    g.cylinder((57, 40, 18), 3, 7, 2, WOOD_D)
    g.beam((40, 39, 20), (40, 13, 10), 4.5, METAL)
    for yy, zz in ((31, 17), (19, 12)):
        g.cylinder((40, yy, zz), 5.4, 3, 1, IRON)
    g.roundbox((33, 4, 4), (47, 16, 12), 1.5, IRON)
    g.box((36, 2, 5), (44, 10, 9), 0)
    # The ladder sits on the front-left tangent so it does not conceal the outlet.
    ladder_ends = ((10, 25), (24, 11))
    for xx, yy in ladder_ends:
        g.beam((xx, yy, 7), (xx, yy, 113), 1.8, IRON_D)
        tx, ty = xx + (40 - xx) * 0.25, yy + (43 - yy) * 0.25
        g.beam((xx, yy, 111), (tx, ty, 119), 1.8, IRON_D)
        for zz in (26, 52, 78, 102):
            g.beam((xx, yy, zz), (xx + (40 - xx) * 0.20, yy + (43 - yy) * 0.20, zz), 1.6, IRON)
    for zz in range(11, 113, 7):
        g.beam((*ladder_ends[0], zz), (*ladder_ends[1], zz), 1.6, METAL)
    xy_panel(g, ladder_ends[0], ladder_ends[1], 109, 112, 8, IRON)
    # Back inspection hatch and a pressure equalization riser give a useful rear view.
    g.roundbox((30, 69, 55), (50, 75, 76), 3, IRON_D)
    g.roundbox((33, 73, 58), (47, 77, 73), 2, METAL)
    for xx in (32, 46):
        for zz in (59, 70):
            g.box((xx, 76, zz), (xx + 2, 79, zz + 2), BOLT)
    g.box((38, 76, 62), (42, 80, 68), IRON_D)
    g.cylinder((64, 64, 80), 2.5, 65, 2, IRON)
    g.beam((64, 64, 111), (60, 64, 117), 2.5, IRON)
    g.cylinder((60, 64, 118), 4, 3, 2, IRON_D)
    for zz in (58, 86, 105):
        g.box((58, 60, zz), (68, 68, zz + 3), METAL)
    return Asset('silo', 'Raised grain silo', g, voxel_size=0.055, notes=[
        'Stepped domed cap, segmented silo walls, structural bands and rivets, hopper, four braced legs, discharge gate and sloped outlet.',
        'Front-left tangent ladder includes stand-off brackets and top handholds; rear includes an inspection hatch and pressure riser. Ladder was moved after actual render review to expose the front discharge spout.',
        'Ladder rungs are three large cells thick; no fluid/grain animation is supplied.'
    ])


def windmill_blade(g, angle):
    # Four distinct canvas sails in the XZ plane; all construction is voxel occupancy.
    ux, uz = math.cos(angle), math.sin(angle)
    px, pz = -uz, ux
    dx, dz = g.x - 64, g.z - 88
    t = dx * ux + dz * uz
    q = dx * px + dz * pz
    sheet = (t >= 16) & (t <= 47) & (np.abs(q) <= 6.8) & (g.y >= 15) & (g.y < 19)
    g.data[sheet] = CANVAS
    g.data[sheet & (np.mod(t - 16, 6) <= 1.2)] = LAMP
    border = (t >= 14) & (t <= 49) & (np.abs(q) <= 8.5) & ((np.abs(q) >= 6.2) | (t < 17) | (t > 46))
    g.data[border & (g.y >= 14) & (g.y < 21)] = WOOD
    for tt in (20, 27, 34, 41):
        slat = (t >= tt) & (t < tt + 2.4) & (np.abs(q) < 8.5) & (g.y >= 13) & (g.y < 16)
        g.data[slat] = WOOD_L
    g.beam((64 + ux * 5, 21, 88 + uz * 5), (64 + ux * 49, 21, 88 + uz * 49), 2.3, WOOD_D)
    g.beam((64 + ux * 4, 20, 88 + uz * 4), (64 + ux * 15, 20, 88 + uz * 15), 3, IRON)


def windmill():
    g = Grid((128, 96, 128), PALETTE)
    stone_plinth(g, 41, 87, 33, 79, 34, thickness=5)
    g.box((46, 38, 9), (82, 74, 34), STONE)
    # Soft tapered tower. Its flat-color panel divisions follow useful vertical bays.
    g.cone((64, 56, 63), 24, 16, 60, 2, PLASTER)
    r = np.sqrt((g.x - 64) ** 2 + (g.y - 56) ** 2)
    maxr = 24 - (g.z - 33) * (8 / 60)
    theta = np.arctan2(g.y - 56, g.x - 64)
    seam = np.abs(np.sin(theta * 8)) < 0.10
    g.data[(g.z >= 35) & (g.z < 93) & (r >= maxr - 1.5) & (r <= maxr + 0.1) & seam] = STONE
    # Timber edge posts articulate the masonry lower storey.
    for xx in (41, 82):
        for yy in (33, 74):
            g.box((xx, yy, 5), (xx + 5, yy + 5, 38), WOOD_D)
            g.box((xx + 1, yy, 8), (xx + 4, yy + 5, 37), WOOD)
    # Round-topped entrance cut into the actual base, with stone steps.
    g.roundbox((54, 29, 3), (74, 37, 29), 5, WOOD_D)
    g.roundbox((57, 28, 4), (71, 34, 27), 4, WOOD)
    for xx in (59, 64, 69):
        g.box((xx, 27, 5), (xx + 1, 30, 23), WOOD_L)
    for zz in (9, 21):
        g.box((56, 26, zz), (63, 30, zz + 3), IRON)
    g.box((68, 25, 13), (71, 29, 18), IRON_D)
    g.box((52, 22, 0), (76, 35, 3), STONE)
    g.box((54, 26, 3), (74, 35, 5), PLASTER)
    # Balcony deck with all four perimeter rail runs and diagonal supports.
    g.box((33, 25, 33), (95, 87, 38), WOOD_D)
    for xx in range(35, 94, 7):
        g.box((xx, 26, 37), (xx + 5, 86, 39), WOOD)
    for yy in (26, 84):
        for xx in (35, 49, 64, 79, 92):
            g.box((xx - 1.5, yy - 1.5, 37), (xx + 1.5, yy + 1.5, 52), WOOD)
        g.box((34, yy - 1.5, 49), (94, yy + 1.5, 53), WOOD_L)
        g.box((34, yy - 1.5, 42), (94, yy + 1.5, 45), WOOD)
    for xx in (35, 92):
        for yy in (40, 55, 70):
            g.box((xx - 1.5, yy - 1.5, 37), (xx + 1.5, yy + 1.5, 52), WOOD)
        g.box((xx - 1.5, 26, 49), (xx + 1.5, 85, 53), WOOD_L)
        g.box((xx - 1.5, 26, 42), (xx + 1.5, 85, 45), WOOD)
    for xx in (42, 85):
        g.beam((xx, 35, 23), (xx, 26, 35), 2.3, WOOD)
        g.beam((xx, 77, 23), (xx, 85, 35), 2.3, WOOD)
    # Front upper windows, side windows and a rear gallery access door.
    for zz, yy in ((58, 32), (78, 36)):
        g.box((56, yy, zz), (72, yy + 6, zz + 14), WOOD_D)
        g.box((59, yy - 1, zz + 3), (69, yy + 2, zz + 11), GLASS_D)
        g.box((62, yy - 2, zz + 2), (65, yy + 2, zz + 12), WOOD_L)
        g.box((55, yy - 2, zz), (73, yy + 3, zz + 3), WOOD_L)
    for xx in (39, 85):
        g.box((xx, 48, 13), (xx + 5, 64, 29), WOOD_D)
        g.box((xx - 1, 52, 16), (xx + 6, 60, 26), GLASS_D)
        g.box((xx - 1, 55, 15), (xx + 6, 58, 27), WOOD_L)
    g.roundbox((55, 74, 39), (73, 81, 65), 3, WOOD_D)
    g.box((59, 78, 41), (69, 83, 62), WOOD)
    g.box((65, 82, 49), (69, 85, 54), IRON_D)
    g.box((54, 77, 5), (74, 83, 29), WOOD_D)
    g.box((58, 81, 7), (70, 85, 26), WOOD)
    g.box((55, 82, 0), (73, 94, 4), STONE)
    # Stepped roof cap, concentric terracotta bands and a rear grain-sack hoist.
    g.cone((64, 56, 97), 25, 7, 22, 2, ROOF)
    for zz in (88, 93, 98, 103):
        rr = 25 - (zz - 86) * (18 / 22)
        cylinder_shell(g, (64, 56, zz), rr + 0.5, 2.5, 2, 3, ROOF_L)
    g.cylinder((64, 56, 108), 7, 3, 2, ROOF_D)
    g.box((61, 73, 68), (67, 91, 73), WOOD_D)
    g.beam((64, 76, 58), (64, 87, 69), 2, WOOD)
    g.cylinder((64, 88, 56), 1.6, 26, 2, IRON_D)
    g.torus((64, 88, 42), 3, 1.5, 1, IRON)
    # Four real sails, central axle, separate hub cap and hub bolts.
    g.cylinder((64, 29, 88), 5, 25, 1, IRON_D)
    for degrees in (45, 135, 225, 315):
        windmill_blade(g, math.radians(degrees))
    g.cylinder((64, 17, 88), 8, 10, 1, IRON)
    g.cylinder((64, 11, 88), 5, 4, 1, WOOD)
    g.cylinder((64, 8, 88), 2, 3, 1, METAL)
    for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
        g.cylinder((64 + 5.5 * math.cos(a), 11, 88 + 5.5 * math.sin(a)), 1.2, 3, 1, BOLT)
    return Asset('windmill', 'Four-sail grain windmill', g, voxel_size=0.055, notes=[
        'Four independently occupied diagonal canvas sails have physical timber borders, cross slats, spars and a bolted hub.',
        'Tapered plaster tower, stone lower storey, complete gallery railings, useful doors and windows, stepped roof, rear loading hoist and rear access steps.',
        'Static machinery only; no rig or animation is supplied. Minimum sail border/slat thickness is approximately 2-3 large cells.'
    ])


def make_assets():
    return [tractor(), barn(), silo(), windmill()]


if __name__ == '__main__':
    run_theme(Path(__file__).resolve().parent, make_assets())
