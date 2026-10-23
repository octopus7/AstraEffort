"""Freshly authored desert utility assets; each surface originates in a voxel.

The local reference informed the silhouettes and restrained industrial palette.
All geometry here is independently constructed for this theme. The parent-owned
voxelkit supplies only generic occupancy, meshing, export, and rendering tools.
"""
from pathlib import Path
import math
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_tools"))
from voxelkit import Asset, Grid, run_theme

AIR, SAND, PALE, EARTH, ORANGE, RUST, TEAL, DEEP_TEAL, GRAPHITE, RUBBER, IRON, ALLOY, GLASS, REFLECTION, SOLAR, LIGHT = range(16)
PALETTE = [
    (0, 0, 0, 0),
    (210, 182, 136, 255),
    (239, 217, 178, 255),
    (156, 132, 101, 255),
    (205, 99, 36, 255),
    (149, 66, 30, 255),
    (64, 114, 116, 255),
    (37, 77, 82, 255),
    (53, 56, 56, 255),
    (35, 39, 41, 255),
    (88, 92, 89, 255),
    (148, 155, 146, 255),
    (43, 72, 84, 255),
    (100, 139, 146, 255),
    (39, 88, 109, 255),
    (255, 225, 150, 255),
]


def exploration_rover():
    g = Grid((100, 128, 96), PALETTE)
    x, y, z = g.x, g.y, g.z
    # A ladder chassis with three connected axles and outboard dampers.
    g.box((27, 15, 30), (35, 122, 40), GRAPHITE)
    g.box((65, 15, 30), (73, 122, 40), GRAPHITE)
    for yy in (28, 68, 108):
        g.beam((14, yy, 22), (86, yy, 22), 3.4, IRON)
        g.box((29, yy - 5, 25), (71, yy + 5, 34), GRAPHITE)
        for xx in (25, 75):
            g.beam((xx, yy, 23), (xx, yy + 5, 39), 3.1, ORANGE)
            g.beam((xx, yy, 23), (xx, yy + 3, 34), 1.6, ALLOY)
    # Six true fat, rounded voxel tires with raised transverse tread segments.
    for xx, outside in ((14, -1), (86, 1)):
        for yy in (28, 68, 108):
            for offset in (-2, 2):
                g.torus((xx + offset, yy, 22), 13.0, 6.0, 0, RUBBER)
            g.cylinder((xx, yy, 22), 10.5, 17, 0, IRON)
            radial = np.sqrt((y - yy) ** 2 + (z - 22) ** 2)
            angle = np.arctan2(z - 22, y - yy)
            tread = (np.abs(x - xx) <= 9.5) & (radial >= 16.7) & (radial <= 19.4) & (np.cos(angle * 14) > 0.25)
            g.data[tread] = GRAPHITE
            face_x = xx + outside * 9
            g.cylinder((face_x, yy, 22), 8.4, 3, 0, ORANGE)
            g.cylinder((face_x + outside, yy, 22), 5.6, 3, 0, GRAPHITE)
            g.cylinder((face_x + outside * 2, yy, 22), 2.6, 3, 0, IRON)
    # Flat fender surfaces are structural steps, not attached wheel decals.
    for a, b in ((6, 28), (72, 94)):
        g.roundbox((a, 11, 40), (b, 46, 45), 2, IRON)
        g.roundbox((a, 51, 41), (b, 124, 45), 2, EARTH)
    g.roundbox((20, 14, 37), (80, 70, 77), 7, SAND)
    g.roundbox((24, 20, 71), (76, 66, 81), 5, PALE)
    g.box((20, 24, 39), (80, 66, 44), TEAL)
    g.box((19, 34, 44), (81, 64, 48), ORANGE)
    # Front shell is actually cut back to its raked windscreen before glazing.
    front_y = 14 + (z - 44) * 0.34
    cut = (x >= 24) & (x < 76) & (z >= 48) & (z < 72) & (y >= 10) & (y < front_y)
    g.data[cut] = AIR
    frame = (x >= 24) & (x < 76) & (z >= 48) & (z < 72) & (y >= front_y) & (y < front_y + 4)
    g.data[frame] = GRAPHITE
    glazing = (x >= 28) & (x < 72) & (z >= 51) & (z < 69) & (y >= front_y - 0.3) & (y < front_y + 1.6)
    g.data[glazing] = GLASS
    g.data[glazing & (z > 63)] = REFLECTION
    g.data[(x >= 48) & (x < 52) & (z >= 50) & (z < 70) & (y >= front_y - 1) & (y < front_y + 2)] = PALE
    for xx in (19, 78):
        g.roundbox((xx, 35, 51), (xx + 3, 61, 71), 2, GRAPHITE)
        g.box((xx - 1, 38, 54), (xx + 4, 58, 68), GLASS)
        g.box((xx - 1, 39, 64), (xx + 4, 57, 67), REFLECTION)
        g.box((xx - 1, 59, 49), (xx + 4, 62, 71), EARTH)
        g.box((xx - 2, 51, 46), (xx + 4, 58, 49), ALLOY)
        g.box((xx - 5, 43, 35), (xx + 6, 64, 39), IRON)
    # Protected central radiator, tow eyes, side mirrors and square field lamps.
    g.roundbox((31, 8, 35), (69, 16, 49), 2, GRAPHITE)
    for zz in (38, 42, 46):
        g.box((35, 7, zz), (65, 10, zz + 2), IRON)
    g.beam((19, 7, 33), (81, 7, 33), 3, GRAPHITE)
    for xx in (25, 75):
        g.beam((xx, 7, 33), (xx, 7, 53), 2.5, IRON)
        g.roundbox((xx - 5, 6, 43), (xx + 5, 12, 52), 2, GRAPHITE)
        g.box((xx - 3, 5, 45), (xx + 3, 7, 50), LIGHT)
        g.torus((xx, 7, 30), 3.5, 1.5, 1, ORANGE)
    for xx in (15, 85):
        g.beam((xx, 33, 57), (xx, 25, 63), 1.8, GRAPHITE)
        g.roundbox((xx - 3, 22, 57), (xx + 3, 27, 66), 2, GRAPHITE)
        g.box((xx - 2, 21, 59), (xx + 2, 23, 64), ALLOY)
    # Raised roof rack, tied field cases, cable conduit and a short locator mast.
    for xx in (23, 77):
        g.beam((xx, 26, 80), (xx, 63, 80), 2.0, GRAPHITE)
        g.beam((xx, 27, 80), (xx, 27, 85), 1.7, GRAPHITE)
        g.beam((xx, 62, 80), (xx, 62, 85), 1.7, GRAPHITE)
        g.beam((xx, 27, 85), (xx, 62, 85), 1.7, GRAPHITE)
    g.roundbox((28, 34, 80), (72, 61, 90), 3, IRON)
    g.box((31, 36, 89), (69, 59, 92), GRAPHITE)
    for xx in (36, 61):
        g.box((xx, 33, 81), (xx + 3, 62, 92), EARTH)
    g.box((44, 32, 82), (56, 36, 89), ORANGE)
    g.box((48, 31, 84), (52, 34, 87), GRAPHITE)
    for xx in (29, 66):
        g.roundbox((xx, 23, 80), (xx + 8, 30, 87), 1.5, GRAPHITE)
        g.box((xx + 2, 22, 82), (xx + 6, 24, 85), LIGHT)
    g.cylinder((75, 61, 86), 1.5, 13, 2, GRAPHITE)
    g.cylinder((75, 61, 92), 2.3, 3, 2, ORANGE)
    # Rear utility tray is recessed between its edges and carries separate gear.
    g.box((20, 70, 40), (80, 123, 47), SAND)
    g.box((24, 73, 46), (76, 120, 48), IRON)
    for xx in (20, 80):
        for yy in (73, 97, 121):
            g.beam((xx, yy, 45), (xx, yy, 61), 1.8, GRAPHITE)
        g.beam((xx, 73, 61), (xx, 122, 61), 1.8, GRAPHITE)
    g.beam((21, 122, 61), (79, 122, 61), 1.8, GRAPHITE)
    g.roundbox((29, 77, 48), (58, 103, 70), 3, ORANGE)
    g.box((31, 79, 69), (56, 101, 72), RUST)
    for xx in (34, 50):
        g.box((xx, 76, 49), (xx + 3, 104, 72), EARTH)
    g.box((39, 75, 57), (48, 79, 62), GRAPHITE)
    g.roundbox((61, 79, 48), (75, 101, 65), 2, TEAL)
    g.box((65, 82, 64), (71, 97, 68), GRAPHITE)
    g.roundbox((29, 107, 48), (72, 119, 60), 2, SAND)
    g.box((45, 118, 51), (55, 122, 55), ALLOY)
    g.box((76, 104, 49), (84, 120, 63), GRAPHITE)
    for yy in (107, 111, 115):
        g.box((83, yy, 51), (86, yy + 2, 61), IRON)
    g.box((32, 122, 39), (42, 125, 44), ORANGE)
    g.box((60, 122, 39), (70, 125, 44), ORANGE)
    return Asset("exploration_rover", "Six-wheel desert exploration rover", g, 0.045, notes={
        "features": "Six rounded treaded wheels and axle/damper geometry; raked cab; protected radiator; roof cases; recessed cargo tray; rear cooling cassette.",
        "reduction": "Designed with broad frame sections and >=3-voxel rail diameters. No manual half-resolution corrections.",
        "front": "-Y",
    })


def water_tower():
    g = Grid((100, 100, 128), PALETTE)
    # Four square columns on layered sandstone foundation shoes.
    for xx in (25, 71):
        for yy in (27, 73):
            g.roundbox((xx - 9, yy - 9, 1), (xx + 9, yy + 9, 6), 2, GRAPHITE)
            g.box((xx - 7, yy - 7, 6), (xx + 7, yy + 7, 10), SAND)
            g.box((xx - 4, yy - 4, 9), (xx + 4, yy + 4, 76), IRON)
            g.box((xx - 5, yy - 5, 12), (xx + 5, yy + 5, 15), ORANGE)
            g.roundbox((xx - 7, yy - 7, 67), (xx + 7, yy + 7, 80), 2, ORANGE)
            for zz in (69, 76):
                g.box((xx - 4, yy - 8, zz), (xx - 1, yy - 6, zz + 2), GRAPHITE)
                g.box((xx + 2, yy - 8, zz), (xx + 5, yy - 6, zz + 2), GRAPHITE)
    g.beam((25, 73, 21), (71, 73, 61), 2.8, GRAPHITE)
    g.beam((71, 73, 21), (25, 73, 61), 2.8, GRAPHITE)
    g.beam((25, 27, 22), (25, 73, 61), 2.8, GRAPHITE)
    # Tank is a capsule-like cylinder with broad stepped end caps.
    g.cylinder((48, 50, 88), 33, 46, 2, SAND)
    g.ellipsoid((48, 50, 67), (33, 33, 13), SAND)
    g.ellipsoid((48, 50, 109), (33, 33, 14), PALE)
    x, y, z = g.x, g.y, g.z
    body = (g.data == SAND) | (g.data == PALE)
    g.data[body & (z >= 91) & (z < 103)] = TEAL
    g.data[body & (z >= 85) & (z < 91)] = ORANGE
    g.cylinder((48, 50, 123), 13, 4, 2, GRAPHITE)
    g.cylinder((48, 50, 126), 9, 2, 2, IRON)
    g.box((45, 46, 126), (51, 54, 128), ORANGE)
    # Tank exterior access plate and a level-gauge assembly.
    g.roundbox((42, 16, 71), (55, 20, 82), 2, PALE)
    for xx in (44, 51):
        g.box((xx, 15, 74), (xx + 2, 18, 79), EARTH)
    g.cylinder((16, 48, 90), 1.8, 33, 2, ALLOY)
    for zz in (77, 106):
        g.beam((16, 48, zz), (22, 48, zz), 2, GRAPHITE)
    # Ladder faces +X with large orange rungs and return rails onto the roof.
    for yy in (42, 59):
        g.beam((87, yy, 10), (87, yy, 122), 2, GRAPHITE)
        g.beam((87, yy, 122), (74, yy, 122), 2, GRAPHITE)
        g.beam((74, yy, 122), (74, yy, 116), 2, GRAPHITE)
    for zz in range(17, 120, 7):
        g.beam((87, 41, zz), (87, 60, zz), 1.6, ORANGE)
    for zz in (32, 70, 104):
        g.beam((79, 43, zz), (87, 43, zz), 2, IRON)
        g.beam((79, 58, zz), (87, 58, zz), 2, IRON)
    # Drain neck, exposed bent outlet, open valve wheel, and discharge foot.
    g.cone((48, 50, 56), 5, 11, 11, 2, EARTH)
    g.beam((48, 50, 52), (48, 50, 34), 4, GRAPHITE)
    g.beam((48, 50, 34), (48, 22, 27), 4, IRON)
    g.beam((48, 22, 27), (87, 22, 27), 4, IRON)
    g.beam((87, 22, 27), (87, 14, 27), 4, IRON)
    g.beam((87, 14, 27), (87, 14, 8), 4, IRON)
    for xx in (60, 77):
        g.cylinder((xx, 22, 27), 5.3, 3, 0, EARTH)
    g.cylinder((66, 22, 27), 6.2, 10, 0, ORANGE)
    g.cylinder((66, 22, 35), 2, 10, 2, GRAPHITE)
    g.torus((66, 22, 41), 5.2, 1.6, 2, ORANGE)
    g.beam((61, 22, 41), (71, 22, 41), 1.2, ORANGE)
    g.beam((66, 17, 41), (66, 27, 41), 1.2, ORANGE)
    g.cylinder((87, 14, 9), 5.8, 5, 2, GRAPHITE)
    g.cylinder((87, 14, 6), 2.4, 7, 2, AIR)
    return Asset("water_tower", "Four-leg desert reservoir", g, 0.04, notes={
        "features": "Rounded tank with colored level bands; four braced columns; roof hatch; complete ladder; actual bent outlet with open-ring hand valve.",
        "reduction": "Columns 8 voxels wide, pipes 8 voxels diameter, rungs 3.2 voxels diameter. No manual half corrections.",
        "front": "-Y",
    })


def solar_array():
    g = Grid((128, 88, 100), PALETTE)
    # Three separately framed tilted sections share one torsion tube.
    n = np.array((0.0, -0.83, 0.55776339))
    n /= np.linalg.norm(n)
    v = np.array((0.0, n[2], -n[1]))
    dy, dz = g.y - 43, g.z - 65
    q = dy * v[1] + dz * v[2]
    depth = dy * n[1] + dz * n[2]
    # Equal 42-voxel spacing keeps every module on the same 2x reduction phase.
    for cx in (23, 65, 107):
        u = g.x - cx
        outer = (np.abs(u) <= 18) & (np.abs(q) <= 31) & (np.abs(depth) <= 3.2)
        g.data[outer] = GRAPHITE
        edge = outer & (depth >= 1) & ((np.abs(u) >= 15.5) | (np.abs(q) >= 28.5))
        g.data[edge] = PALE
        cells = outer & (np.abs(u) < 15.5) & (np.abs(q) < 28.5) & (depth >= 0.3)
        g.data[cells] = SOLAR
        for k in (-8, 0, 8):
            g.data[cells & (np.abs(u - k) <= 0.9)] = ALLOY
        for k in (-18, -9, 0, 9, 18):
            g.data[cells & (np.abs(q - k) <= 0.9)] = ALLOY
        # Four actual clamp blocks hold each panel's corner.
        clamps = outer & (np.abs(u) >= 14.8) & (np.abs(q) >= 26.5)
        g.data[clamps] = ORANGE
        g.roundbox((cx - 11, 43, 0), (cx + 11, 65, 5), 2, GRAPHITE)
        g.box((cx - 9, 45, 5), (cx + 9, 63, 9), SAND)
        g.box((cx - 6, 48, 9), (cx + 6, 60, 12), EARTH)
        g.box((cx - 4, 50, 11), (cx + 4, 58, 58), IRON)
        g.box((cx - 5, 49, 13), (cx + 5, 59, 17), ORANGE)
        g.beam((cx, 55, 24), (cx, 36, 49), 2.5, GRAPHITE)
        g.beam((cx, 55, 46), (cx, 49, 64), 3.5, IRON)
        g.cylinder((cx, 49, 62), 6.7, 8, 0, ORANGE)
        g.cylinder((cx, 49, 62), 3.3, 10, 0, GRAPHITE)
    g.beam((12, 49, 62), (116, 49, 62), 2.8, GRAPHITE)
    # Recessed battery cabinet and independent control door below the cells.
    g.roundbox((41, 25, 8), (83, 48, 36), 3, SAND)
    g.box((43, 26, 34), (81, 46, 38), PALE)
    g.roundbox((60, 23, 12), (79, 28, 33), 2, TEAL)
    g.box((64, 22, 24), (74, 25, 30), GRAPHITE)
    g.box((66, 21, 26), (72, 24, 28), REFLECTION)
    g.box((73, 21, 16), (77, 25, 20), ORANGE)
    g.box((45, 23, 12), (56, 28, 32), GRAPHITE)
    for zz in (15, 20, 25, 30):
        g.box((47, 22, zz), (54, 25, zz + 2), IRON)
    g.roundbox((29, 32, 10), (40, 47, 33), 2, EARTH)
    g.box((29, 31, 15), (33, 34, 28), ORANGE)
    for start, end in (((38, 49, 58), (38, 49, 40)), ((38, 49, 40), (47, 45, 32)), ((86, 49, 57), (86, 49, 17)), ((86, 49, 17), (80, 42, 17))):
        g.beam(start, end, 1.8, GRAPHITE)
    g.box((45, 30, 4), (53, 41, 10), GRAPHITE)
    g.box((72, 30, 4), (80, 41, 10), GRAPHITE)
    return Asset("solar_array", "Three-section desert solar array", g, 0.045, notes={
        "features": "Three physically separate tilted modules with 4x6 cell groups, clamp corners, torsion tube, three braced stands, battery cabinet and control door.",
        "reduction": "Panel thickness 6.4 voxels; broad silver bus lines and >=3.6-voxel cables survive reduction. No manual half corrections.",
        "front": "-Y",
    })


def repair_garage():
    g = Grid((128, 120, 112), PALETTE)
    x, y, z = g.x, g.y, g.z
    # Hollow barrel vault, extruded along Y. Occupancy is the shell, not a box.
    low_outer = (np.abs(x - 56) <= 48) & (z >= 4) & (z <= 46)
    high_outer = (((x - 56) / 48) ** 2 + ((z - 46) / 52) ** 2 <= 1) & (z >= 46)
    outer = low_outer | high_outer
    low_inner = (np.abs(x - 56) < 41) & (z >= 7) & (z <= 46)
    high_inner = (((x - 56) / 41) ** 2 + ((z - 46) / 45) ** 2 < 1) & (z >= 46)
    inner = low_inner | high_inner
    shell = outer & (y >= 18) & (y < 110) & ~inner
    g.data[shell] = SAND
    g.data[shell & (z < 28)] = TEAL
    for yy, color in ((21, GRAPHITE), (44, ORANGE), (76, ORANGE), (103, GRAPHITE)):
        g.data[shell & (y >= yy) & (y < yy + 4) & (z >= 28)] = color
    g.data[outer & (y >= 105) & (y < 110)] = EARTH
    # Front facade has a true through-opening, with thick stepped portal jambs.
    g.data[outer & (y >= 14) & (y < 21)] = PALE
    g.roundbox((18, 11, 7), (94, 23, 73), 5, ORANGE)
    g.roundbox((23, 9, 7), (89, 26, 68), 3, AIR)
    g.box((24, 9, 7), (88, 26, 16), AIR)
    g.box((10, 15, 2), (102, 110, 7), EARTH)
    g.box((23, 12, 6), (89, 25, 8), ALLOY)
    for xx in range(28, 87, 12):
        g.box((xx, 18, 7), (xx + 6, 21, 9), ORANGE)
    for xx in (10, 94):
        for yy in (20, 103):
            g.roundbox((xx - 6, yy - 8, 0), (xx + 12, yy + 9, 6), 2, GRAPHITE)
            g.box((xx - 3, yy - 5, 6), (xx + 8, yy + 6, 10), EARTH)
    # Header lintel and short roof panels make the dome's construction legible.
    g.box((33, 12, 79), (79, 16, 82), EARTH)
    g.box((48, 11, 77), (52, 17, 89), GRAPHITE)
    g.roundbox((38, 58, 94), (74, 88, 103), 4, GRAPHITE)
    g.box((43, 61, 101), (69, 85, 104), DEEP_TEAL)
    for yy in (67, 75, 83):
        g.box((42, yy, 102), (70, yy + 2, 105), IRON)
    # Interior bench is against the far wall, with visible drawers and shelves.
    g.box((27, 94, 25), (86, 104, 29), IRON)
    for xx in (29, 82):
        g.box((xx, 96, 7), (xx + 3, 102, 26), GRAPHITE)
    g.roundbox((39, 35, 8), (57, 51, 25), 2, ORANGE)
    for zz in (11, 16, 21):
        g.box((41, 34, zz), (55, 37, zz + 2), ALLOY)
    g.roundbox((61, 95, 29), (76, 103, 36), 2, TEAL)
    g.box((65, 94, 31), (72, 97, 34), GRAPHITE)
    for yy in (32, 64):
        g.box((17, yy, 8), (21, yy + 4, 55), GRAPHITE)
        g.box((33, yy, 8), (37, yy + 4, 55), GRAPHITE)
    for zz in (19, 35, 51):
        g.box((17, 32, zz), (37, 68, zz + 3), IRON)
    g.roundbox((21, 38, 22), (32, 50, 32), 2, TEAL)
    g.roundbox((21, 53, 22), (33, 64, 32), 2, EARTH)
    g.roundbox((21, 38, 38), (32, 50, 48), 2, ORANGE)
    g.roundbox((22, 54, 38), (32, 63, 48), 2, SAND)
    for xx, yy in ((76, 77), (85, 88)):
        g.cylinder((xx, yy, 18), 5.5, 20, 2, ORANGE)
        g.cylinder((xx, yy, 28), 5.8, 2, 2, GRAPHITE)
        g.cylinder((xx, yy, 12), 5.8, 2, 2, EARTH)
    g.beam((28, 73, 77), (84, 73, 77), 2, GRAPHITE)
    for xx in (32, 76):
        g.beam((xx, 73, 76), (xx, 73, 82), 1.5, IRON)
        g.box((xx - 4, 69, 72), (xx + 8, 76, 76), GRAPHITE)
        g.box((xx - 2, 68, 72), (xx + 6, 74, 74), LIGHT)
    # Closed personnel door on the right, recessed panel and mechanical handle.
    g.roundbox((100, 36, 8), (108, 62, 51), 3, ORANGE)
    g.roundbox((105, 40, 10), (109, 58, 47), 2, GRAPHITE)
    g.box((108, 45, 31), (110, 53, 42), EARTH)
    g.box((109, 47, 33), (111, 51, 40), GLASS)
    g.box((108, 54, 22), (111, 57, 26), ALLOY)
    g.box((102, 38, 53), (108, 60, 58), GRAPHITE)
    g.box((107, 42, 54), (110, 56, 57), LIGHT)
    # Side compressor: actual tank, equipment body, fan face and connected pipes.
    g.cylinder((115, 91, 15), 7, 26, 1, TEAL)
    g.roundbox((108, 77, 18), (126, 108, 44), 3, SAND)
    g.box((111, 80, 43), (123, 104, 47), IRON)
    g.cylinder((117, 77, 30), 7.6, 4, 1, GRAPHITE)
    g.box((111, 74, 29), (123, 78, 32), IRON)
    g.box((116, 74, 24), (119, 78, 37), IRON)
    g.cylinder((117, 74, 30), 2.4, 3, 1, ORANGE)
    g.box((125, 86, 24), (128, 103, 40), GRAPHITE)
    for yy in (88, 93, 98):
        g.box((127, yy, 26), (128, yy + 2, 38), IRON)
    for yy in (81, 101):
        g.box((110, yy, 5), (124, yy + 5, 13), GRAPHITE)
    g.beam((103, 94, 47), (116, 94, 47), 2.3, GRAPHITE)
    g.beam((116, 94, 47), (116, 94, 42), 2.3, GRAPHITE)
    g.beam((103, 103, 27), (110, 103, 27), 2.4, ORANGE)
    # Aft louvers and external conduit are useful in reverse views.
    g.roundbox((43, 108, 39), (72, 113, 59), 2, GRAPHITE)
    for zz in (42, 47, 52, 57):
        g.box((47, 112, zz), (68, 114, zz + 2), IRON)
    g.beam((90, 110, 20), (90, 110, 57), 1.9, GRAPHITE)
    g.beam((90, 110, 57), (74, 110, 57), 1.9, GRAPHITE)
    return Asset("repair_garage", "Open-front desert repair garage", g, 0.065, notes={
        "features": "True hollow barrel-vault shell and open front portal, workshop shelves/bench/drawers, roof vent, side personnel door, attached compressor and aft vents.",
        "reduction": "Seven-voxel shell walls and broad portal frames preserve the opening; workshop parts remain discrete at half resolution. No manual half corrections.",
        "front": "-Y",
    })


def make_assets():
    return [exploration_rover(), water_tower(), solar_array(), repair_garage()]


if __name__ == "__main__":
    run_theme(Path(__file__).resolve().parent, make_assets())
