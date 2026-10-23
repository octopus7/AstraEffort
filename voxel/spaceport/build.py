"""Five original spaceport assets; native colored voxel occupancy is authoritative."""
from pathlib import Path
import sys
import math
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_tools"))
from voxelkit import Grid, Asset, run_theme

PALETTE = [(0, 0, 0, 0), (218, 221, 211, 255), (242, 242, 230, 255),
           (172, 182, 179, 255), (91, 122, 142, 255), (124, 155, 170, 255),
           (54, 78, 97, 255), (48, 57, 62, 255), (29, 37, 42, 255),
           (139, 151, 156, 255), (209, 104, 77, 255), (238, 138, 102, 255),
           (55, 104, 127, 255), (90, 146, 164, 255), (246, 197, 107, 255),
           (41, 48, 51, 255), (73, 83, 87, 255), (116, 118, 111, 255)]
IVORY, WHITE, IVORY_D, BLUE, BLUE_L, BLUE_D, GRAPHITE, CHARCOAL, METAL, CORAL, CORAL_L, GLASS, GLASS_L, AMBER, RUBBER, TREAD, ROCK = range(1, 18)


def transport_rocket():
    g = Grid((96, 96, 128), PALETTE)
    g.cylinder((48, 48, 68), 22, 66, 2, IVORY)
    g.ellipsoid((48, 48, 42), (22, 22, 15), IVORY)
    g.ellipsoid((48, 48, 96), (22, 22, 28), IVORY)
    body = g.data > 0
    g.data[body & (g.z >= 44) & (g.z < 51)] = BLUE
    g.data[body & (g.z >= 90) & (g.z < 94)] = WHITE
    g.data[body & (g.x >= 37) & (g.x < 40) & (g.y < 35) & (g.z >= 95) & (g.z < 116)] = CORAL
    g.cylinder((48, 48, 122), 7, 5, 2, GRAPHITE)
    g.cylinder((48, 48, 126), 2.3, 3, 2, CORAL)
    # Three separate hollow engine bells beneath the capsule body.
    for x, y in ((39, 41), (57, 41), (48, 59)):
        g.cylinder((x, y, 32), 5.4, 8, 2, GRAPHITE)
        g.cone((x, y, 22), 8, 4.4, 18, 2, GRAPHITE)
        g.cone((x, y, 18), 6.3, 2.7, 12, 2, 0)
        g.cylinder((x, y, 14), 8.3, 3, 2, METAL)
        g.cylinder((x, y, 13.5), 6.3, 4, 2, 0)
    # Four independent landing legs and pads, separated around the fuselage.
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        attach = (48 + sx * 14, 48 + sy * 14, 44)
        knee = (48 + sx * 24, 48 + sy * 24, 25)
        foot = (48 + sx * 34, 48 + sy * 34, 8)
        g.beam(attach, knee, 5, IVORY)
        g.beam((attach[0] + sx * 2, attach[1] + sy * 2, 41),
               (knee[0] + sx, knee[1] + sy, 27), 2.1, CORAL)
        g.beam(knee, foot, 2.8, GRAPHITE)
        g.ellipsoid(knee, (4.5, 4.5, 4.5), METAL)
        g.roundbox((foot[0] - 6, foot[1] - 6, 2), (foot[0] + 6, foot[1] + 6, 8), 2, GRAPHITE)
        g.box((foot[0] - 3, foot[1] - 3, 7), (foot[0] + 3, foot[1] + 3, 9), CORAL)
    # External service pods remain secondary to the rounded capsule silhouette.
    for x, y in ((22, 48), (74, 48), (48, 74)):
        g.cylinder((x, y, 71), 4.7, 40, 2, BLUE)
        g.ellipsoid((x, y, 51), (4.7, 4.7, 6), BLUE_D)
        g.ellipsoid((x, y, 91), (4.7, 4.7, 6), BLUE_L)
        g.cylinder((x, y, 53), 5.2, 4, 2, CORAL)
        g.cylinder((x, y, 92), 3.2, 7, 2, METAL)
    # Framed access hatch with porthole, hinges and a distinct latch.
    g.roundbox((38, 22, 59), (58, 30, 88), 3, CORAL)
    g.roundbox((41, 20, 62), (55, 26, 85), 2, WHITE)
    g.box((44, 18, 73), (52, 22, 81), GRAPHITE)
    g.box((46, 17, 75), (50, 19, 79), GLASS)
    for z in (64, 80):
        g.box((39, 19, z), (43, 23, z + 4), METAL)
    g.box((52, 18, 65), (55, 21, 70), GRAPHITE)
    g.cylinder((48, 26, 103), 4.2, 5, 1, GRAPHITE)
    g.cylinder((48, 23, 103), 2.7, 3, 1, GLASS)
    g.box((44, 24, 51), (52, 29, 56), GRAPHITE)
    # Rear cable run and maintenance port are functional, restrained details.
    g.beam((57, 69, 58), (57, 69, 88), 1.8, METAL)
    g.box((42, 69, 62), (52, 73, 76), IVORY_D)
    g.box((44, 72, 65), (50, 75, 73), BLUE_D)
    return Asset("transport_rocket", "Four-leg capsule transport rocket", g, voxel_size=.055,
                 notes={"features": ["capsule nose", "framed access hatch", "four landing legs", "three hollow engine bells", "service pods"],
                        "half": "Conservative 2x voxel reduction. Landing legs, feet and engine mouth voids are structural; fine hinges and pod collars simplify."})


def hangar():
    g = Grid((128, 112, 88), PALETTE)
    # Broad, low elliptical barrel vault with a genuinely open front volume.
    arch = (np.abs(g.x - 64) < 56) & (g.z >= 8) & ((g.z <= 39) | (((g.x - 64) / 56) ** 2 + ((g.z - 39) / 40) ** 2 <= 1))
    shell = arch & (g.y >= 12) & (g.y < 104)
    g.data[shell] = BLUE
    g.data[arch & (g.y >= 8) & (g.y < 20)] = IVORY
    g.data[shell & (g.y >= 96)] = IVORY
    g.data[shell & (((g.y >= 30) & (g.y < 35)) | ((g.y >= 78) & (g.y < 83))) & (g.z >= 50)] = CORAL
    inner = (np.abs(g.x - 64) < 46) & (g.z >= 10) & ((g.z <= 38) | (((g.x - 64) / 46) ** 2 + ((g.z - 38) / 31) ** 2 <= 1))
    g.data[inner & (g.y < 98)] = 0
    # This floor belongs to the building rather than a shared display diorama.
    g.roundbox((7, 5, 3), (121, 105, 10), 2, GRAPHITE)
    g.box((22, 11, 9), (106, 98, 11), METAL)
    for x in (25, 99):
        g.box((x, 12, 10), (x + 3, 94, 12), CORAL)
    for y in range(14, 92, 17):
        g.box((62, y, 10), (66, y + 8, 12), WHITE)
    for x in (10, 108):
        g.roundbox((x, 7, 9), (x + 10, 20, 44), 2, BLUE_D)
        g.box((x + 3, 5, 16), (x + 7, 9, 39), CORAL)
        g.roundbox((x - 2, 4, 5), (x + 12, 19, 14), 2, IVORY)
    # Under-arch approach lights are attached just below the roof.
    for x, z in ((32, 59), (64, 67), (96, 59)):
        g.box((x - 6, 16, z), (x + 6, 25, z + 4), GRAPHITE)
        g.box((x - 4, 15, z), (x + 4, 18, z + 2), AMBER)
    # Interior lockers, service pipes and a clear central vehicle path.
    for x in (28, 86):
        g.roundbox((x, 83, 11), (x + 15, 97, 27), 2, BLUE_D)
        g.box((x + 3, 81, 14), (x + 12, 85, 24), IVORY)
        g.box((x + 8, 80, 17), (x + 10, 83, 21), GRAPHITE)
    for x in (24, 104):
        g.beam((x, 95, 15), (x, 95, 44), 2, CORAL)
        g.beam((x, 95, 44), (64, 95, 44), 2, CORAL)
    # Side maintenance annex and two low, attached roof ventilators.
    g.roundbox((2, 44, 10), (21, 84, 32), 3, IVORY)
    g.box((0, 53, 13), (5, 76, 28), BLUE_D)
    g.box((0, 57, 16), (3, 73, 26), BLUE)
    for x in (43, 70):
        g.roundbox((x, 51, 74), (x + 15, 68, 83), 3, GRAPHITE)
        for xx in (x + 3, x + 7, x + 11):
            g.box((xx, 53, 81), (xx + 2, 66, 85), METAL)
    for x in (58, 68):
        g.box((x, 104, 15), (x + 3, 108, 69), GRAPHITE)
    for z in range(18, 69, 7):
        g.box((59, 105, z), (70, 109, z + 2), METAL)
    return Asset("hangar", "Low barrel-vault spacecraft hangar", g, voxel_size=.065,
                 notes={"features": ["broad rounded arch", "true open spacecraft doorway", "clear interior vehicle path", "approach lights", "service annex"],
                        "half": "Independent conservative half grid retains the full doorway and interior; roof ribs/lights simplify."})


def exploration_rover():
    g = Grid((92, 128, 100), PALETTE)
    g.roundbox((23, 14, 25), (69, 119, 45), 7, BLUE_D)
    g.roundbox((21, 17, 38), (71, 119, 49), 4, IVORY)
    # Six discrete wheels and suspension stubs, three on each side.
    for y in (30, 66, 102):
        g.cylinder((46, y, 20), 3.2, 64, 0, GRAPHITE)
        for x in (14, 78):
            g.cylinder((x, y, 16), 14, 14, 0, RUBBER)
            for k in range(12):
                angle = k * math.tau / 12
                dy, dz = 12.5 * math.cos(angle), 12.5 * math.sin(angle)
                g.box((x - 8, y + dy - 2, 14 + dz), (x + 8, y + dy + 2, 18 + dz), TREAD)
            g.cylinder((x, y, 16), 7, 18, 0, CORAL)
            g.cylinder((x, y, 16), 3.3, 20, 0, METAL)
            inward = 30 if x < 46 else 62
            g.beam((x, y, 20), (inward, y + 5, 33), 3, GRAPHITE)
    # Rounded pressurized cabin and thick wraparound window frames.
    g.roundbox((22, 12, 43), (70, 66, 78), 7, IVORY)
    g.roundbox((25, 10, 50), (67, 18, 72), 4, BLUE_D)
    g.roundbox((28, 8, 53), (64, 13, 69), 3, GLASS)
    g.box((44, 7, 53), (48, 12, 70), IVORY)
    for x0, x1 in ((20, 25), (67, 72)):
        g.roundbox((x0, 23, 53), (x1, 51, 72), 2, GLASS)
        g.box((x0, 35, 52), (x1, 39, 73), IVORY)
    g.roundbox((25, 18, 75), (67, 61, 81), 3, WHITE)
    for x in (28, 58):
        g.box((x, 9, 42), (x + 7, 14, 48), GRAPHITE)
        g.box((x + 1, 7, 43), (x + 6, 10, 47), AMBER)
    g.roundbox((20, 7, 33), (72, 17, 39), 2, GRAPHITE)
    g.box((23, 8, 36), (69, 12, 40), CORAL)
    # Mid-body equipment pack with visible service hatch and clamps.
    g.roundbox((24, 67, 47), (68, 88, 71), 4, BLUE)
    g.box((68, 71, 51), (72, 84, 66), IVORY_D)
    g.box((70, 73, 53), (74, 82, 64), WHITE)
    g.box((72, 77, 56), (75, 80, 61), GRAPHITE)
    for x in (28, 61):
        g.box((x, 67, 66), (x + 3, 87, 73), CORAL)
    # Open rear sample tray, filled sparsely enough to show its interior walls.
    g.roundbox((22, 90, 45), (70, 122, 59), 3, IVORY)
    g.box((27, 95, 49), (65, 117, 62), 0)
    for x in (23, 65):
        g.box((x, 100, 54), (x + 4, 112, 61), CORAL)
    for x, y, rz in ((34, 102, 4.5), (49, 108, 5.5), (59, 102, 3.5)):
        g.ellipsoid((x, y, 52), (5, 4, rz), ROCK)
    g.box((29, 121, 48), (39, 124, 52), CORAL)
    g.box((53, 121, 48), (63, 124, 52), CORAL)
    # A wide sensor head and a separate communications antenna.
    g.cylinder((30, 53, 87), 2.5, 15, 2, GRAPHITE)
    g.roundbox((22, 47, 91), (38, 60, 99), 2, WHITE)
    for x in (27, 33):
        g.cylinder((x, 46, 95), 2.2, 4, 1, GRAPHITE)
        g.cylinder((x, 44, 95), 1.2, 2, 1, GLASS_L)
    g.box((36, 50, 93), (40, 57, 97), CORAL)
    g.cylinder((63, 80, 82), 1.8, 25, 2, GRAPHITE)
    g.cylinder((63, 80, 94), 2.1, 4, 2, CORAL)
    return Asset("exploration_rover", "Six-wheel pressurized exploration rover", g, voxel_size=.035,
                 notes={"features": ["six separate wheels", "pressurized cabin", "sensor mast", "communications antenna", "open sample tray"],
                        "half": "Conservative 2x reduction retains six wheels and tray cavity; tire cleats, antennae and sample stones become chunkier."})


def fuel_tank():
    g = Grid((128, 80, 112), PALETTE)
    # Common skid with four distinct pads and visible crossmembers.
    for y in (11, 61):
        g.roundbox((5, y, 4), (123, y + 8, 14), 2, GRAPHITE)
        for x in (12, 112):
            g.roundbox((x - 7, y - 3, 1), (x + 7, y + 11, 6), 2, METAL)
            g.box((x - 3, y - 1, 9), (x + 3, y + 9, 15), CORAL)
    for x in (17, 61, 106):
        g.box((x, 18, 7), (x + 6, 62, 14), GRAPHITE)
    # Two solid capsule-ended pressure vessels, individually supported.
    for x in (36, 92):
        g.box((x - 8, 29, 11), (x + 8, 51, 23), GRAPHITE)
        vessel = Grid(g.shape, PALETTE)
        vessel.cylinder((x, 40, 57), 22, 48, 2, IVORY)
        vessel.ellipsoid((x, 40, 33), (22, 22, 18), IVORY)
        vessel.ellipsoid((x, 40, 81), (22, 22, 18), IVORY)
        mask = vessel.data > 0
        g.data[mask] = IVORY
        g.data[mask & (g.z >= 40) & (g.z < 68)] = BLUE
        g.data[mask & (g.z >= 73) & (g.z < 77)] = CORAL
        g.cylinder((x, 40, 100), 6, 5, 2, GRAPHITE)
        g.cylinder((x, 40, 103), 4, 5, 2, METAL)
        g.beam((x, 17, 30), (x, 17, 87), 1.8, GRAPHITE)
        for z in (31, 84):
            g.box((x - 3, 16, z), (x + 3, 25, z + 5), CORAL)
    # Connected overhead and front service pipes tie both vessels together.
    g.beam((36, 40, 104), (92, 40, 104), 3, METAL)
    g.beam((64, 40, 20), (64, 40, 105), 3.1, GRAPHITE)
    for x in (36, 92):
        g.beam((x, 20, 31), (x, 8, 31), 2.5, CORAL)
        g.beam((x, 20, 66), (64, 20, 66), 2.3, GRAPHITE)
    g.beam((36, 8, 31), (92, 8, 31), 2.5, CORAL)
    g.beam((64, 20, 18), (64, 20, 67), 3, GRAPHITE)
    for z in (35, 60):
        g.cylinder((64, 20, z), 4, 4, 2, CORAL)
    for x in (49, 79):
        g.torus((x, 5, 31), 4.5, 1.6, 1, CORAL_L)
        g.cylinder((x, 5, 31), 2.2, 6, 1, METAL)
        g.beam((x - 4, 4, 31), (x + 4, 4, 31), 1.2, CORAL_L)
        g.beam((x, 4, 27), (x, 4, 35), 1.2, CORAL_L)
    g.roundbox((57, 1, 17), (71, 12, 39), 2, IVORY)
    g.box((60, 0, 28), (68, 3, 35), BLUE_D)
    g.box((62, 0, 30), (66, 1, 33), GLASS_L)
    g.box((60, 0, 21), (64, 3, 25), CORAL)
    # Rear end caps and service couplings provide a complete independent unit.
    for x in (36, 92):
        g.cylinder((x, 61, 51), 5, 6, 1, GRAPHITE)
        g.cylinder((x, 65, 51), 3, 3, 1, METAL)
    return Asset("fuel_tank", "Twin capsule fuel-storage skid", g, voxel_size=.04,
                 notes={"features": ["two capsule-ended vessels", "common skid", "joined overhead manifold", "front transfer pipe", "two valves", "control panel"],
                        "half": "Conservative 2x reduction keeps twin vessels and continuous pipe routes; valve loops and small collars simplify."})


def control_tower():
    g = Grid((108, 100, 128), PALETTE)
    g.roundbox((29, 25, 2), (79, 75, 12), 5, GRAPHITE)
    g.roundbox((35, 31, 8), (73, 69, 63), 6, IVORY)
    g.box((38, 29, 12), (42, 34, 60), CORAL)
    g.roundbox((43, 27, 11), (65, 34, 38), 2, IVORY_D)
    g.box((46, 25, 13), (62, 30, 35), GRAPHITE)
    g.box((49, 24, 22), (59, 27, 31), BLUE_D)
    g.box((59, 23, 15), (62, 27, 21), METAL)
    g.roundbox((76, 45, 8), (88, 62, 30), 2, BLUE)
    g.box((85, 49, 13), (90, 59, 25), IVORY)
    g.beam((77, 51, 25), (70, 51, 25), 2, GRAPHITE)
    # Rear ladder is attached to the shaft and reaches the operations deck.
    for x in (49, 60):
        g.box((x, 69, 13), (x + 3, 74, 62), GRAPHITE)
    for z in range(16, 62, 7):
        g.box((50, 72, z), (62, 76, z + 2), METAL)
    # Broad observation platform with rounded, stepped corners.
    g.roundbox((12, 8, 59), (96, 92, 67), 12, GRAPHITE)
    g.roundbox((15, 11, 65), (93, 89, 70), 10, IVORY)
    # Flared window shell, with a genuinely hollow cabin interior.
    rx = 29 + (g.z - 68) * (7 / 30)
    ry = 26 + (g.z - 68) * (7 / 30)
    cabin = (g.z >= 68) & (g.z < 98) & ((np.abs(g.x - 54) / rx) ** 4 + (np.abs(g.y - 50) / ry) ** 4 <= 1)
    g.data[cabin] = GLASS
    inner = (g.z >= 72) & (g.z < 96) & ((np.abs(g.x - 54) / (rx - 4)) ** 4 + (np.abs(g.y - 50) / (ry - 4)) ** 4 <= 1)
    g.data[inner] = 0
    # Sloping mullions subdivide broad windows on all four sides.
    for x0, x1 in ((30, 26), (42, 40), (54, 54), (66, 68), (78, 82)):
        g.beam((x0, 24, 69), (x1, 17, 98), 1.8, GRAPHITE)
        g.beam((x0, 76, 69), (x1, 83, 98), 1.8, GRAPHITE)
    for y0, y1 in ((32, 27), (50, 50), (68, 73)):
        g.beam((25, y0, 69), (18, y1, 98), 1.8, GRAPHITE)
        g.beam((83, y0, 69), (90, y1, 98), 1.8, GRAPHITE)
    # Low safety balustrade leaves the window line visible.
    for x in (19, 39, 69, 89):
        for y in (15, 85):
            g.box((x, y, 67), (x + 3, y + 3, 74), GRAPHITE)
    for y in (15, 85):
        g.box((19, y, 73), (92, y + 3, 76), CORAL)
    g.roundbox((9, 5, 98), (99, 95, 107), 11, BLUE)
    g.roundbox((17, 13, 105), (91, 87, 111), 8, WHITE)
    g.box((50, 9, 106), (56, 91, 109), CORAL)
    # Compact rooftop communication equipment and two unequal antennae.
    g.roundbox((32, 41, 110), (48, 58, 118), 3, GRAPHITE)
    g.box((35, 43, 116), (45, 55, 120), METAL)
    g.cylinder((40, 49, 123), 1.8, 9, 2, GRAPHITE)
    g.cylinder((40, 49, 127), 2, 2, 2, CORAL)
    g.cylinder((70, 56, 117), 1.8, 15, 2, GRAPHITE)
    g.cylinder((70, 56, 124), 2, 3, 2, CORAL)
    g.roundbox((61, 26, 110), (78, 41, 117), 3, GRAPHITE)
    for x in (64, 69, 74):
        g.box((x, 28, 116), (x + 2, 39, 119), METAL)
    return Asset("control_tower", "Rounded spaceport control tower", g, voxel_size=.05,
                 notes={"features": ["stout shaft", "broad flared window cabin", "rounded roof", "antennae", "rear access ladder", "service pod"],
                        "half": "Conservative 2x reduction preserves shaft/cabin hierarchy, window mullions and roof equipment. Cabin floor was lowered eight large cells after preview review to expose a taller window band. Glass uses opaque palette color."})


def make_assets():
    return [transport_rocket(), hangar(), exploration_rover(), fuel_tank(), control_tower()]


if __name__ == "__main__":
    run_theme(Path(__file__).resolve().parent, make_assets())
