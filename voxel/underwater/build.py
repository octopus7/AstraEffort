"""Independent underwater voxel assets. Opaque glazing is deliberately stylized.

No existing theme models or source are inputs. Every filled or empty cell below
is authored here; generic surface/export utilities are supplied by the parent.
Coordinates are X right, Y back, Z up; the front of each model is toward -Y.
"""
from pathlib import Path
import math
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_tools"))
from voxelkit import Asset, Grid, run_theme

VOID, IVORY, CREAM, SHADE, PETROL, BLUE, GLASS, REFLECT, OCHRE, GOLD, GRAPHITE, IRON, SILVER, DARK_GLASS, LAMP, PIPE = range(16)
PALETTE = [
    (0, 0, 0, 0),
    (225, 220, 203, 255), (247, 239, 214, 255), (174, 176, 164, 255),
    (30, 68, 84, 255), (44, 99, 119, 255), (44, 118, 148, 255),
    (97, 164, 183, 255), (222, 163, 36, 255), (246, 193, 60, 255),
    (38, 47, 54, 255), (85, 102, 111, 255), (144, 158, 163, 255),
    (23, 66, 87, 255), (255, 235, 172, 255), (48, 125, 132, 255),
]


def submersible():
    g = Grid((128, 112, 100), PALETTE)
    # Two long landing runners, with suspended cross-members and load struts.
    for xx in (38, 90):
        g.roundbox((xx - 5, 25, 2), (xx + 5, 99, 7), 2, IVORY)
        g.box((xx - 3, 31, 6), (xx + 3, 93, 9), OCHRE)
        g.beam((xx, 39, 9), (xx + (4 if xx < 64 else -4), 49, 31), 3.0, GRAPHITE)
        g.beam((xx, 88, 9), (xx + (4 if xx < 64 else -4), 79, 31), 3.0, GRAPHITE)
        g.box((xx - 5, 35, 8), (xx + 5, 44, 12), IRON)
        g.box((xx - 5, 83, 8), (xx + 5, 92, 12), IRON)
    g.beam((38, 53, 17), (90, 53, 17), 3, GRAPHITE)
    # Rounded pressure hull and opaque curved front observation blister.
    g.ellipsoid((64, 65, 52), (36, 35, 31), IVORY)
    g.roundbox((37, 49, 56), (91, 87, 78), 7, IVORY)
    g.data[(g.data == IVORY) & (g.z > 19) & (g.z < 33)] = PETROL
    g.ellipsoid((64, 35, 52), (29, 17, 25), GLASS)
    x, y, z = g.x, g.y, g.z
    lens = ((x - 64) / 31) ** 2 + ((z - 52) / 27) ** 2
    rim = (lens >= 0.79) & (lens <= 1.03) & (y >= 28) & (y < 36)
    g.data[rim] = OCHRE
    # Glazing ribs follow a real convex surface, not a floating front card.
    glass_voxels = g.data == GLASS
    g.data[glass_voxels & (x >= 61) & (x < 65)] = PETROL
    g.data[glass_voxels & (z >= 62) & (z < 66)] = REFLECT
    for xx in (40, 82):
        g.roundbox((xx, 25, 28), (xx + 9, 32, 37), 2, GRAPHITE)
        g.box((xx + 2, 24, 30), (xx + 7, 27, 35), LAMP)
    # Each outboard duct is drilled completely through; its recessed rotor
    # occupies only four spokes and a hub, leaving open water quadrants.
    for xx, attach_x in ((18, 40), (110, 88)):
        g.beam((xx, 63, 52), (attach_x, 63, 52), 4.2, PETROL)
        g.cylinder((xx, 59, 52), 17, 22, 1, OCHRE)
        g.cylinder((xx, 59, 52), 12, 28, 1, VOID)
        g.torus((xx, 48, 52), 14.5, 2.5, 1, GOLD)
        g.torus((xx, 69, 52), 14.3, 2, 1, GRAPHITE)
        g.cylinder((xx, 61, 52), 3.4, 10, 1, IRON)
        for dx, dz in ((11, 0), (-11, 0), (0, 11), (0, -11)):
            g.beam((xx, 61, 52), (xx + dx, 61, 52 + dz), 1.6, GRAPHITE)
        g.cylinder((xx, 55, 52), 2.0, 3, 1, SILVER)
    # Two compact articulated manipulators with actual open gripping jaws.
    for xx, drift in ((38, -7), (90, 7)):
        g.cylinder((xx, 33, 31), 5.5, 8, 0, OCHRE)
        elbow = (xx + drift, 18, 25)
        wrist = (xx + drift, 7, 19)
        g.beam((xx, 32, 31), elbow, 3.0, GRAPHITE)
        g.beam(elbow, wrist, 2.5, OCHRE)
        g.cylinder(elbow, 4.2, 7, 0, IRON)
        for dx in (-4, 4):
            g.beam(wrist, (wrist[0] + dx, 4, 17), 1.7, IRON)
            g.beam((wrist[0] + dx, 4, 17), (wrist[0] + dx, 2, 13), 1.7, GRAPHITE)
            g.beam((wrist[0] + dx, 2, 13), (wrist[0] + dx * 0.45, 2, 12), 1.4, GRAPHITE)
    # Top hatch, acoustic packages and side/rear maintenance fittings.
    g.roundbox((46, 53, 77), (82, 81, 85), 4, PETROL)
    g.box((51, 58, 84), (77, 76, 88), CREAM)
    g.box((57, 59, 87), (71, 74, 90), GRAPHITE)
    for xx in (42, 86):
        g.beam((xx, 57, 81), (xx, 82, 81), 1.8, OCHRE)
        g.beam((xx, 58, 75), (xx, 58, 81), 1.8, OCHRE)
        g.beam((xx, 81, 75), (xx, 81, 81), 1.8, OCHRE)
    g.cylinder((75, 77, 92), 1.5, 13, 2, GRAPHITE)
    g.cylinder((54, 72, 91), 3.2, 8, 2, OCHRE)
    g.box((52, 70, 90), (56, 72, 94), LAMP)
    for xx in (31, 97):
        g.cylinder((xx, 76, 56), 6.5, 6, 0, PETROL)
        g.cylinder((xx, 76, 56), 3.8, 8, 0, IRON)
    g.roundbox((49, 96, 42), (79, 103, 62), 3, PETROL)
    for zz in (46, 51, 56):
        g.box((54, 101, zz), (74, 104, zz + 2), IRON)
    g.torus((64, 104, 63), 5.3, 1.6, 1, OCHRE)
    return Asset("submersible", "Ducted-thruster research submersible", g, 0.035, notes={
        "features": "Rounded opaque viewport, two through-bored thruster ducts with recessed spokes, paired manipulators, landing runners and maintenance fittings.",
        "glazing": "Opaque solid-color voxels, no simulated transparency.",
        "half_detail": "Duct wall >=5 voxels; gripper fingers and rotor spokes >=3.2 voxels diameter; no manual half correction.",
    })


def dome_laboratory():
    g = Grid((128, 128, 108), PALETTE)
    # Load ring and radial foundation shoes are part of the laboratory asset.
    for angle in (0, 45, 135, 180, 225, 315):
        a = math.radians(angle)
        px, py = 64 + 49 * math.cos(a), 70 + 49 * math.sin(a)
        g.roundbox((px - 7, py - 7, 0), (px + 7, py + 7, 6), 2, GRAPHITE)
        g.box((px - 4, py - 4, 5), (px + 4, py + 4, 14), IRON)
    g.cylinder((64, 70, 13), 48, 10, 2, PETROL)
    g.cylinder((64, 70, 20), 46, 7, 2, IVORY)
    g.cylinder((64, 70, 35), 44, 29, 2, GLASS)
    x, y, z = g.x, g.y, g.z
    dome = ((x - 64) / 44) ** 2 + ((y - 70) / 44) ** 2 + ((z - 49) / 42) ** 2 <= 1
    g.data[dome & (z >= 49)] = GLASS
    g.data[(g.data == GLASS) & (z >= 38) & (z < 42)] = REFLECT
    theta = np.arctan2(y - 70, x - 64)
    wider_dome = ((x - 64) / 46) ** 2 + ((y - 70) / 46) ** 2 + ((z - 49) / 44) ** 2 <= 1
    ribs = wider_dome & (z >= 49) & (np.abs(np.sin(theta * 4)) <= 0.17)
    g.data[ribs] = CREAM
    g.cylinder((64, 70, 49), 46, 5, 2, IVORY)
    for angle in range(0, 360, 45):
        a = math.radians(angle)
        px, py = 64 + 44 * math.cos(a), 70 + 44 * math.sin(a)
        g.beam((px, py, 21), (px, py, 50), 2.4, PETROL)
        g.box((px - 3, py - 3, 20), (px + 3, py + 3, 25), OCHRE)
        g.box((px - 3, py - 3, 47), (px + 3, py + 3, 52), OCHRE)
    # Crown hatch and small independent mast housings.
    g.cylinder((64, 70, 91), 16, 6, 2, PETROL)
    g.cylinder((64, 70, 94), 15, 4, 2, OCHRE)
    g.cylinder((64, 70, 97), 13, 4, 2, CREAM)
    g.box((60, 65, 98), (68, 75, 101), GRAPHITE)
    g.cylinder((70, 73, 103), 1.6, 9, 2, GRAPHITE)
    g.cylinder((58, 68, 102), 3, 7, 2, OCHRE)
    g.box((56, 65, 101), (60, 67, 105), LAMP)
    # Front airlock is an open recess ending at an opaque sealed inner door.
    g.roundbox((40, 0, 3), (88, 35, 10), 3, PETROL)
    g.cylinder((64, 17, 30), 21, 32, 1, IVORY)
    g.cylinder((64, 5, 30), 22, 6, 1, GRAPHITE)
    g.cylinder((64, 8, 30), 14.5, 24, 1, VOID)
    g.torus((64, 2, 30), 18.2, 3.0, 1, CREAM)
    g.cylinder((64, 22, 30), 14, 4, 1, DARK_GLASS)
    g.box((62, 19, 18), (66, 23, 42), PETROL)
    g.box((51, 18, 29), (77, 22, 32), IRON)
    for xx in (44, 81):
        g.box((xx, 7, 23), (xx + 4, 14, 38), OCHRE)
        g.box((xx + 1, 6, 27), (xx + 3, 9, 35), LAMP)
    g.box((49, 0, 6), (79, 8, 10), SILVER)
    g.box((53, 1, 9), (75, 6, 12), OCHRE)
    # Recessed aft equipment panels and conduit remain present in reverse views.
    g.roundbox((52, 111, 24), (77, 119, 42), 3, PETROL)
    for zz in (27, 32, 37):
        g.box((56, 117, zz), (73, 120, zz + 2), IRON)
    g.beam((83, 112, 21), (83, 112, 44), 2, GRAPHITE)
    return Asset("dome_laboratory", "Ribbed undersea dome laboratory", g, 0.06, notes={
        "features": "Eight meridian ribs and framed wall segments, circular foundation ring, crown hatch, front airlock recess and aft utility panel.",
        "glazing": "Opaque blue voxels intentionally represent window segments; no transparency claim or furnished interior.",
        "half_detail": "Ribs, wall posts and airlock throat are sized for the half grid; no manual half correction.",
    })


def rounded_profile(x, z, cx, cz, hx, hz, radius):
    qx, qz = np.abs(x - cx) - (hx - radius), np.abs(z - cz) - (hz - radius)
    return np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qz, 0) ** 2) + np.minimum(np.maximum(qx, qz), 0) <= radius


def connecting_tunnel():
    g = Grid((84, 128, 84), PALETTE)
    x, y, z = g.x, g.y, g.z
    outer = rounded_profile(x, z, 42, 42, 34, 31, 12)
    aperture = rounded_profile(x, z, 42, 42, 27, 24, 10)
    walls = outer & ~aperture & (y >= 7) & (y < 121)
    g.data[walls] = IVORY
    # Reinforced end collars retain the same fully open through-aperture.
    reinforced = rounded_profile(x, z, 42, 42, 38, 35, 14)
    for yy in (8, 120):
        ring = reinforced & ~aperture & (np.abs(y - yy) <= 4)
        g.data[ring] = GRAPHITE
        g.data[ring & (y < yy - 1)] = IVORY
        belt = outer & ~aperture & (y >= yy + (-9 if yy > 64 else 5)) & (y < yy + (-5 if yy > 64 else 9))
        g.data[belt] = OCHRE
    # Long side observation glazing and framed ceiling panels are opaque.
    for xa, xb, face_x in ((7, 15, 6), (69, 77, 76)):
        g.box((xa, 23, 30), (xb, 107, 56), GLASS)
        g.box((face_x, 24, 49), (face_x + 2, 106, 53), REFLECT)
        for yy in (22, 43, 65, 87, 106):
            g.box((face_x, yy, 29), (face_x + 2, yy + 3, 58), PETROL)
        g.box((face_x, 22, 29), (face_x + 2, 109, 32), PETROL)
        g.box((face_x, 22, 55), (face_x + 2, 109, 58), PETROL)
    top_glass = walls & (x >= 21) & (x < 63) & (y >= 24) & (y < 106) & (z >= 67)
    g.data[top_glass] = BLUE
    for yy in (24, 45, 66, 87, 104):
        g.box((21, yy, 72), (63, yy + 2, 75), PETROL)
    # Walk deck, thin edge guides and visible internal end luminaires.
    g.box((20, 4, 17), (64, 124, 20), IRON)
    for xx in (22, 59):
        g.box((xx, 5, 20), (xx + 3, 123, 22), OCHRE)
    for yy in (10, 118):
        for xx in (17, 64):
            g.box((xx, yy - 2, 40), (xx + 3, yy + 2, 56), PETROL)
            g.box((xx + 1, yy - 3, 44), (xx + 3, yy, 53), LAMP)
    for xx in (18, 66):
        for yy in (26, 104):
            g.roundbox((xx - 7, yy - 9, 1), (xx + 7, yy + 9, 7), 2, GRAPHITE)
            g.box((xx - 4, yy - 5, 6), (xx + 4, yy + 5, 17), IRON)
    g.roundbox((30, 55, 72), (54, 77, 80), 2, PETROL)
    g.box((34, 58, 79), (50, 74, 83), IRON)
    g.box((37, 59, 81), (47, 73, 84), OCHRE)
    return Asset("connecting_tunnel", "Open-ended pressure connecting tunnel", g, 0.05, notes={
        "features": "Continuous rounded pressure shell with two genuinely open end apertures, reinforced collars, walkway, framed side and ceiling windows and exterior supports.",
        "glazing": "Opaque colored voxel panels; end apertures are empty volume, not painted dark discs.",
        "half_detail": "Seven-voxel side walls and broad window frames; no manual half correction.",
    })


def seabed_miner():
    g = Grid((128, 128, 108), PALETTE)
    # Three pairs of planted legs have discrete hips, knees and ankle shoes.
    for side in (-1, 1):
        hip_x, knee_x, foot_x = 64 + side * 24, 64 + side * 44, 64 + side * 52
        for hip_y, knee_y, foot_y in ((57, 43, 36), (80, 79, 79), (101, 113, 117)):
            g.roundbox((foot_x - 10, foot_y - 8, 1), (foot_x + 10, foot_y + 8, 6), 2, PETROL)
            g.box((foot_x - 8, foot_y - 6, 6), (foot_x + 8, foot_y + 6, 10), OCHRE)
            g.cylinder((foot_x, foot_y, 14), 4, 12, 2, GRAPHITE)
            g.beam((hip_x, hip_y, 54), (knee_x, knee_y, 45), 4, GRAPHITE)
            g.cylinder((hip_x, hip_y, 54), 7, 10, 0, OCHRE)
            g.cylinder((hip_x + side * 5, hip_y, 54), 3.4, 4, 0, IRON)
            g.cylinder((knee_x, knee_y, 45), 7.5, 10, 1, OCHRE)
            g.cylinder((knee_x, knee_y - 5, 45), 4, 3, 1, PETROL)
            g.beam((knee_x, knee_y, 40), (foot_x, foot_y, 17), 5.3, IVORY)
            g.beam((knee_x + side * 3, knee_y + 2, 39), (foot_x + side * 2, foot_y + 2, 19), 2, IRON)
    # Central pod combines a low structural cradle with a rounded crew capsule.
    g.roundbox((38, 53, 37), (90, 107, 60), 5, PETROL)
    g.ellipsoid((64, 80, 65), (27, 29, 26), IVORY)
    g.roundbox((41, 56, 48), (87, 102, 77), 5, IVORY)
    g.ellipsoid((64, 53, 67), (22, 12, 18), GLASS)
    x, y, z = g.x, g.y, g.z
    rim = ((x - 64) / 23) ** 2 + ((z - 67) / 19) ** 2
    g.data[(rim >= 0.77) & (rim <= 1.05) & (y >= 47) & (y < 53)] = OCHRE
    glazing = g.data == GLASS
    g.data[glazing & (x >= 62) & (x < 65)] = PETROL
    g.data[glazing & (z >= 74) & (z < 78)] = REFLECT
    for xx in (44, 76):
        g.box((xx, 44, 49), (xx + 8, 50, 55), GRAPHITE)
        g.box((xx + 1, 43, 51), (xx + 7, 46, 54), LAMP)
    # The drill is a genuine tapered volume with a raised winding cutting ridge.
    g.roundbox((48, 40, 29), (80, 60, 49), 3, OCHRE)
    g.cylinder((64, 38, 36), 13, 22, 1, GRAPHITE)
    g.torus((64, 29, 36), 12, 2.5, 1, OCHRE)
    g.cone((64, 17, 36), 3, 13, 28, 1, SILVER)
    distance = np.sqrt((x - 64) ** 2 + (z - 36) ** 2)
    nominal_radius = 3 + (y - 3) * 10 / 28
    phase = np.arctan2(z - 36, x - 64) - (y - 3) * 0.60
    cutter = (y >= 3) & (y < 31) & (distance >= nominal_radius - 0.5) & (distance <= nominal_radius + 2.5) & (np.cos(phase) >= 0.35)
    g.data[cutter] = IRON
    g.cylinder((64, 4, 36), 3.0, 5, 1, GRAPHITE)
    for xx in (49, 79):
        g.beam((xx, 44, 34), (xx, 55, 39), 2.6, GRAPHITE)
        g.beam((xx, 44, 42), (xx, 57, 47), 1.7, SILVER)
    # Crown rack, restrained utility fittings and rear radiator/cable assembly.
    g.roundbox((45, 66, 85), (83, 97, 93), 4, PETROL)
    g.box((49, 70, 92), (79, 94, 96), CREAM)
    g.box((58, 74, 95), (70, 90, 99), GRAPHITE)
    for xx in (43, 85):
        g.beam((xx, 68, 93), (xx, 98, 93), 1.7, OCHRE)
        g.beam((xx, 69, 87), (xx, 69, 93), 1.7, OCHRE)
        g.beam((xx, 97, 87), (xx, 97, 93), 1.7, OCHRE)
    g.cylinder((79, 94, 101), 1.5, 12, 2, GRAPHITE)
    g.cylinder((49, 73, 98), 2.8, 7, 2, OCHRE)
    for xx in (36, 92):
        g.cylinder((xx, 90, 64), 7.2, 7, 0, PETROL)
        g.cylinder((xx, 90, 64), 4.3, 9, 0, OCHRE)
        g.cylinder((xx, 90, 64), 2.2, 10, 0, IRON)
    g.roundbox((50, 105, 54), (78, 111, 75), 3, GRAPHITE)
    for zz in (58, 63, 68, 73):
        g.box((54, 110, zz), (74, 113, zz + 2), IRON)
    g.beam((89, 102, 49), (96, 107, 49), 2, PIPE)
    g.beam((96, 107, 49), (96, 107, 64), 2, PIPE)
    g.beam((96, 107, 64), (89, 99, 67), 2, PIPE)
    return Asset("seabed_miner", "Six-leg seabed drilling crawler", g, 0.045, notes={
        "features": "Six stout planted legs with rotary joints, rounded observation pod, protected lights, tapered helical drill, roof rack and rear cooling equipment.",
        "glazing": "Opaque stylized viewport with solid reflected-color bands.",
        "half_detail": "Lower-leg armor diameter 10.6 voxels; hip bearings 14 voxels; drill ridge is actual occupied geometry. No manual half correction.",
    })


def docking_station():
    g = Grid((112, 128, 94), PALETTE)
    # An independent docking deck, with structural edge beams and four shoes.
    g.roundbox((6, 3, 3), (106, 125, 11), 3, GRAPHITE)
    g.roundbox((7, 4, 10), (105, 124, 15), 2, IVORY)
    g.box((24, 17, 13), (88, 114, 16), PETROL)
    for xx in (12, 94):
        for yy in (12, 115):
            g.box((xx - 5, yy - 6, 0), (xx + 7, yy + 6, 6), IRON)
    for yy in (18, 42, 67, 92, 117):
        g.box((6, yy, 9), (15, yy + 3, 17), OCHRE)
        g.box((97, yy, 9), (106, yy + 3, 17), OCHRE)
    # Two rounded pressure guide arches have empty throats above the deck.
    x, y, z = g.x, g.y, g.z
    outer = ((np.abs(x - 56) <= 32) & (z >= 14) & (z <= 52)) | (((x - 56) ** 2 + (z - 52) ** 2 <= 32 ** 2) & (z >= 52))
    inner = ((np.abs(x - 56) < 24) & (z >= 14) & (z <= 52)) | (((x - 56) ** 2 + (z - 52) ** 2 < 24 ** 2) & (z >= 52))
    for yy in (30, 100):
        arch = outer & ~inner & (np.abs(y - yy) <= 4)
        g.data[arch] = IRON
        g.data[arch & (y >= yy + 2)] = PETROL
        g.data[arch & (z >= 67) & (z < 73)] = OCHRE
        g.data[arch & (y < yy - 2) & (x < 29) & (z < 55)] = OCHRE
        g.box((18, yy - 8, 12), (36, yy + 8, 19), PETROL)
        g.box((76, yy - 8, 12), (94, yy + 8, 19), PETROL)
        g.box((21, yy - 7, 18), (32, yy + 7, 22), OCHRE)
        g.box((80, yy - 7, 18), (91, yy + 7, 22), OCHRE)
        for xx in (35, 68):
            g.roundbox((xx, yy - 6, 76), (xx + 9, yy + 3, 82), 1.5, GRAPHITE)
            g.box((xx + 2, yy - 7, 77), (xx + 7, yy - 4, 80), LAMP)
        for xx in (25, 84):
            g.box((xx - 1, yy - 5, 37), (xx + 3, yy - 2, 49), OCHRE)
            g.box((xx, yy - 6, 40), (xx + 2, yy - 4, 47), LAMP)
    # Deck guides, central connector pads and physically recessed side grates.
    for xx in (29, 80):
        g.box((xx, 20, 15), (xx + 3, 112, 18), OCHRE)
    g.box((40, 48, 15), (72, 82, 19), IRON)
    g.box((44, 52, 18), (68, 78, 20), PETROL)
    for xx in (42, 66):
        for yy in (50, 76):
            g.box((xx, yy, 19), (xx + 4, yy + 4, 21), SILVER)
    g.box((11, 40, 14), (22, 91, 16), GRAPHITE)
    for yy in range(42, 90, 5):
        g.box((12, yy, 15), (21, yy + 2, 18), IRON)
    # Short corner connector posts and cabinet occupy the right service strip.
    for xx in (16, 96):
        for yy in (15, 116):
            g.box((xx - 4, yy - 4, 15), (xx + 4, yy + 4, 33), PETROL)
            g.box((xx - 5, yy - 5, 31), (xx + 5, yy + 5, 35), OCHRE)
            g.box((xx - 2, yy - 5, 20), (xx + 2, yy - 3, 28), LAMP)
    g.roundbox((87, 55, 16), (108, 84, 61), 3, IVORY)
    g.box((90, 58, 59), (105, 81, 64), CREAM)
    g.roundbox((91, 53, 31), (104, 58, 56), 2, PETROL)
    g.box((94, 52, 46), (101, 55, 52), GRAPHITE)
    g.box((96, 51, 48), (100, 54, 50), REFLECT)
    g.box((94, 52, 35), (98, 55, 39), OCHRE)
    g.box((101, 52, 35), (104, 55, 39), IRON)
    for xx, color in ((94, OCHRE), (103, PIPE)):
        g.cylinder((xx, 53, 24), 3.4, 6, 1, color)
        points = [(xx, 50, 24), (xx, 44, 23), (xx + 2, 37, 17), (xx + 2, 19, 16), (xx - 7, 13, 16)]
        for a, b in zip(points, points[1:]):
            g.beam(a, b, 1.8, color)
        g.cylinder((xx - 7, 13, 17), 3, 6, 2, GRAPHITE)
    g.box((107, 64, 32), (110, 78, 52), GRAPHITE)
    for yy in (66, 71, 76):
        g.box((109, yy, 34), (112, yy + 2, 50), IRON)
    for yy in (88, 119):
        g.beam((103, yy, 15), (103, yy, 33), 1.7, OCHRE)
    g.beam((103, 88, 33), (103, 120, 33), 1.7, OCHRE)
    return Asset("docking_station", "Dual-guide undersea docking platform", g, 0.055, notes={
        "features": "Two genuinely open rounded guide arches, reinforced platform, recessed deck grates, guide strips, connector pads/posts, service cabinet and distinct attached cable runs.",
        "half_detail": "Arch wall eight voxels, clear throat forty-eight voxels, cable diameter 3.6 voxels. No manual half correction.",
    })


def make_assets():
    return [submersible(), dome_laboratory(), connecting_tunnel(), seabed_miner(), docking_station()]


if __name__ == "__main__":
    run_theme(Path(__file__).resolve().parent, make_assets())
