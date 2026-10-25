"""Original native geothermal machinery and architecture. Front is -Y."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_tools'))
from voxelkit import Grid, Asset, run_theme

PALETTE = [
    (0, 0, 0, 0),
    (217, 206, 171),  # ceramic insulation
    (167, 158, 135),  # ceramic shade
    (153, 62, 35),    # weathered copper
    (187, 86, 42),    # copper light
    (39, 43, 42),     # basalt rubber
    (76, 84, 82),     # structural steel
    (139, 149, 143),  # pale alloy
    (48, 76, 88),     # blue-grey opaque glazing
    (83, 123, 137),   # glazing reflection
    (218, 146, 36),   # signal amber
    (239, 213, 135),  # warm lamp
    (24, 30, 29),     # dark recess
    (190, 163, 67),   # restrained safety yellow
    (107, 117, 109),  # equipment insulation
]
CE, CS, CU, CL, BA, SE, AL, BG, GR, AM, LA, RE, SY, IN = range(1, 15)


def thermal_rover():
    g = Grid((98, 128, 104), PALETTE)
    # Four road wheels per side sit inside two deep continuous rubber belts.
    for left, right in ((6, 30), (68, 92)):
        mid = (left + right) / 2
        g.roundbox((left, 38, 4), (right, 122, 32), 12, BA)
        g.roundbox((left-1, 49, 11), (right+1, 111, 25), 6, 0)
        for y in (52, 70, 88, 107):
            g.cylinder((mid, y, 18), 9, right-left, 0, SE)
            outward = left if left < 40 else right
            g.cylinder((outward, y, 18), 5.5, 3, 0, AL)
            g.cylinder((outward, y, 18), 2.5, 4, 0, CU)
        for y in range(47, 116, 9):
            g.box((left-1, y, 28), (right+1, y+4, 34), SE)
            g.box((left-1, y, 3), (right+1, y+4, 7), SE)
    g.roundbox((27, 45, 22), (71, 117, 39), 5, SE)
    g.roundbox((24, 38, 34), (74, 95, 64), 9, CE)
    dome = ((g.x-48)/25)**2 + ((g.y-63)/29)**2 + ((g.z-64)/23)**2 <= 1
    g.data[dome & (g.z >= 48)] = CE
    glass = dome & (g.y < 63) & (g.z >= 56)
    g.data[glass] = BG
    g.data[glass & (g.z >= 73) & (g.z < 76)] = GR
    # Structural ceramic ribs and a lower steel guard protect the window band.
    g.data[glass & ((np.abs(g.x-48) < 2) | ((g.y >= 58) & (g.y < 62)) | (g.z < 59))] = CE
    g.data[glass & (g.z >= 66) & (g.z < 68)] = SE
    g.roundbox((25, 86, 35), (76, 120, 77), 6, CU)
    g.box((24, 40, 41), (75, 96, 47), CU)
    g.box((30, 36, 34), (66, 41, 46), RE)
    for z in (36, 40, 44):
        g.box((32, 35, z), (64, 38, z+2), AL)
    g.roundbox((23, 34, 27), (75, 41, 34), 2, SE)
    for x in (25, 66):
        g.roundbox((x, 36, 46), (x+7, 42, 53), 1, SE)
        g.box((x+1, 35, 47), (x+6, 38, 51), LA)
    # Armored rear machinery and heat radiator.
    g.roundbox((74, 92, 43), (80, 117, 73), 2, CE)
    g.box((78, 95, 47), (82, 114, 70), RE)
    for z in (48, 54, 60, 66):
        g.box((79, 96, z), (83, 113, z+2), AL)
    for y in (96, 104, 112):
        g.box((31, y, 76), (68, y+3, 79), SE)
    g.cylinder((63, 109, 84), 3, 17, 2, SE)
    g.cylinder((63, 109, 93), 4, 3, 2, AL)
    g.cylinder((36, 93, 83), 4, 7, 2, AM)
    g.cylinder((36, 93, 87), 3, 2, 2, LA)
    g.cylinder((68, 115, 88), 1.6, 29, 2, SE)
    # Side-mounted sampler reaches clear of both the cabin and the track.
    g.cylinder((76, 66, 58), 7, 10, 0, SE)
    g.beam((77, 66, 58), (88, 44, 75), 4.5, CU)
    g.cylinder((88, 44, 75), 6, 10, 0, SE)
    g.cylinder((93, 44, 75), 3, 2, 0, AL)
    g.beam((88, 42, 74), (88, 19, 60), 4, CE)
    g.beam((93, 43, 74), (93, 21, 62), 1.7, BA)
    g.cylinder((88, 17, 58), 4, 10, 2, SE)
    g.cylinder((88, 16, 44), 7, 22, 2, CU)
    for z in (36, 49):
        g.cylinder((88, 16, z), 7.8, 3, 2, CE)
    g.box((84, 8, 39), (92, 11, 47), BG)
    g.cylinder((88, 16, 30), 6, 8, 2, SE)
    for x, y in ((84, 16), (92, 16), (88, 12), (88, 20)):
        g.box((x-1, y-1, 24), (x+1, y+1, 28), AL)
    g.cylinder((88, 16, 29), 3.1, 12, 2, 0)
    return Asset('thermal_rover', 'Protected thermal sampling rover', g, .035,
                 ['Original tracked enclosed rover with ceramic armor, radiator and articulated sampling arm.',
                  'Sampler crown has a genuinely empty core bore. Window protection is structural.',
                  'No manual half correction; purposeful details use broad native cell features.'])


def geothermal_drill():
    g = Grid((128, 104, 128), PALETTE)
    # Circular drilling deck with a real annulus around the passing drill string.
    g.cylinder((40, 45, 27), 28, 14, 2, SE)
    g.cylinder((40, 45, 35), 30, 4, 2, AL)
    r = np.sqrt((g.x-40)**2 + (g.y-45)**2)
    phase = np.floor((np.arctan2(g.y-45, g.x-40)+np.pi)/(.25*np.pi)).astype(int)
    g.data[(r >= 25) & (r < 28) & (g.z >= 25) & (g.z < 29) & (phase % 2 == 0)] = SY
    g.cylinder((40, 45, 29), 10, 23, 2, 0)
    # Four independent stabilizing outriggers and feet, not a common slab.
    for ax, ay, fx, fy in ((22, 31, 10, 13), (58, 31, 73, 13),
                          (22, 59, 10, 82), (58, 59, 73, 82)):
        g.beam((ax, ay, 31), (fx, fy, 8), 4.5, SE)
        g.roundbox((fx-8, fy-8, 2), (fx+8, fy+8, 7), 1, BA)
        g.box((fx-6, fy-6, 7), (fx+6, fy+6, 10), CE)
        g.cylinder((fx, fy, 11), 5, 4, 2, CU)
    # Open four-post lattice mast and overhung drill carriage.
    for x in (20, 60):
        for y in (42, 66):
            g.box((x-3, y-3, 35), (x+3, y+3, 118), CU if y == 42 else SE)
    for z in (40, 64, 88, 112):
        g.box((18, 63, z), (63, 69, z+4), SE)
    for z, flip in ((43, False), (67, True), (91, False)):
        g.beam((22 if not flip else 58, 66, z), (58 if not flip else 22, 66, z+21), 2.6, SE)
    for x in (20, 60):
        g.beam((x, 43, 52), (x, 65, 77), 2.2, SE)
        g.beam((x, 65, 79), (x, 43, 106), 2.2, SE)
    g.roundbox((17, 36, 114), (64, 72, 123), 2, CU)
    g.box((26, 35, 116), (55, 39, 121), AL)
    g.cylinder((40, 45, 108), 7, 14, 2, SE)
    g.cylinder((40, 45, 63), 3.8, 88, 2, AL)
    for z in range(22, 103, 6):
        g.cylinder((40, 45, z), 5, 2, 2, SE)
    g.cone((40, 45, 15), 2.4, 5, 10, 2, BA)
    g.cylinder((40, 45, 41), 8, 5, 2, CU)
    # Connected pump/manifold skid and insulated separator vessel.
    g.roundbox((82, 20, 3), (124, 97, 8), 2, SE)
    g.cylinder((102, 76, 29), 14, 42, 2, CE)
    g.cylinder((102, 76, 9), 15, 4, 2, BA)
    for z in (14, 44):
        g.cylinder((102, 76, z), 14.5, 4, 2, CU)
    g.cylinder((102, 76, 51), 13, 4, 2, AL)
    g.cylinder((102, 76, 55), 8, 4, 2, SE)
    g.roundbox((88, 27, 9), (119, 48, 34), 3, CU)
    g.roundbox((94, 25, 15), (115, 29, 32), 1, CE)
    g.box((98, 24, 19), (111, 28, 28), RE)
    for z in (20, 25):
        g.box((99, 23, z), (110, 26, z+2), AL)
    for a, b in (((65, 53, 28), (82, 53, 28)), ((82, 53, 28), (82, 76, 28)),
                 ((82, 76, 28), (89, 76, 28)), ((116, 39, 29), (116, 39, 57)),
                 ((116, 39, 57), (102, 64, 57)), ((102, 64, 57), (102, 76, 55))):
        g.beam(a, b, 3.7, CL)
    for z in (37, 51):
        g.cylinder((116, 39, z), 4.7, 3, 2, AL)
    # The control wheel stands clear of the pump front and retains four open
    # sectors after conservative reduction; the short stem meets the housing.
    g.cylinder((104, 24, 24), 2.3, 12, 1, SE)
    g.torus((104, 18, 24), 10, 1.7, 1, CU)
    g.beam((94, 18, 24), (114, 18, 24), 1.3, AL)
    g.beam((104, 18, 14), (104, 18, 34), 1.3, AL)
    for x in (92, 110):
        g.cylinder((x, 56, 51), 4.5, 4, 1, AL)
        g.cylinder((x, 53, 51), 3, 2, 1, BG)
        g.beam((x, 58, 48), (x, 69, 40), 1.8, SE)
    g.cylinder((61, 42, 125), 3, 5, 2, AM)
    return Asset('geothermal_drill', 'Stabilized geothermal drilling plant', g, .045,
                 ['Open lattice mast, separate threaded drill string, clear deck annulus and four stabilizer feet.',
                  'Pipe-connected pump/manifold and insulated vessel share their own structural equipment skid.',
                  'Front-accessible handwheel with four open sectors; static geometry, no manual half correction.'])


def cooling_tower():
    g = Grid((112, 112, 128), PALETTE)
    radial = np.sqrt((g.x-56)**2 + (g.y-56)**2)
    # Continuous shell with a narrowed waist and open chimney all the way through.
    outer = 31 + 9*((g.z-82)/41)**2
    shell = (g.z >= 43) & (g.z < 124) & (radial <= outer) & (radial >= outer-4)
    g.data[shell] = CE
    g.data[shell & ((g.z >= 104) & (g.z < 110))] = CU
    g.data[shell & ((g.z >= 44) & (g.z < 48))] = CL
    for z in (56, 72, 88):
        g.data[shell & (g.z >= z) & (g.z < z+2)] = CS
    # The top lip is also a ring; nothing caps the central throat.
    g.cylinder((56, 56, 124), 41, 4, 2, CE)
    g.cylinder((56, 56, 124), 36, 6, 2, 0)
    g.data[(radial >= 35) & (radial < 37) & (g.z >= 120) & (g.z < 124)] = AL
    # Ventilated lower plenum is annular and has broad real intake slots.
    g.cylinder((56, 56, 32), 41, 23, 2, SE)
    g.cylinder((56, 56, 32), 31, 25, 2, 0)
    g.cylinder((56, 56, 43), 43, 4, 2, AL)
    g.cylinder((56, 56, 43), 31, 6, 2, 0)
    for lo, hi in (((44, 12, 26), (68, 30, 36)), ((82, 44, 26), (102, 68, 36)),
                   ((44, 82, 26), (68, 102, 36)), ((10, 44, 26), (30, 68, 36))):
        g.box(lo, hi, 0)
    for z in (27, 33):
        g.box((44, 17, z), (68, 20, z+2), AL)
        g.box((93, 44, z), (96, 68, z+2), AL)
        g.box((44, 93, z), (68, 96, z+2), AL)
        g.box((17, 44, z), (20, 68, z+2), AL)
    # Four splayed concrete/steel feet leave the underside open.
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        foot = (56+sx*38, 56+sy*38)
        anchor = (56+sx*27, 56+sy*27)
        g.beam((foot[0], foot[1], 7), (anchor[0], anchor[1], 38), 5, SE)
        g.roundbox((foot[0]-8, foot[1]-8, 2), (foot[0]+8, foot[1]+8, 7), 1, BA)
        g.box((foot[0]-6, foot[1]-6, 7), (foot[0]+6, foot[1]+6, 10), CS)
    # Two explicit external insulated risers bend into the shell wall.
    for x, toward in ((9, 1), (103, -1)):
        g.roundbox((x-7, 48, 2), (x+7, 64, 8), 1, SE)
        g.cylinder((x, 56, 39), 5, 62, 2, CU)
        g.beam((x, 56, 69), (x+toward*12, 56, 81), 5, CU)
        g.beam((x+toward*12, 56, 81), (x+toward*18, 56, 81), 5, CU)
        for z in (12, 62):
            g.cylinder((x, 56, z), 6, 4, 2, AL)
        g.box((x-3, 48, 14), (x+3, 51, 20), AM)
    return Asset('cooling_tower', 'Open-throat geothermal cooling tower', g, .05,
                 ['Hollow waisted ceramic shell with an uncapped 72-cell-diameter top throat.',
                  'Annular lower plenum, real intake slots, four structural feet and two connected copper risers.',
                  'No water, smoke, lava or environmental base. No manual half correction.'])


def volcano_observatory():
    g = Grid((128, 112, 128), PALETTE)
    radius = np.sqrt((g.x-52)**2 + (g.y-60)**2)
    g.cylinder((52, 60, 16), 43, 12, 2, SE)
    g.cylinder((52, 60, 36), 43, 32, 2, CE)
    glazing = (radius <= 43) & (radius >= 39) & (g.z >= 28) & (g.z < 50) & (g.y < 76)
    g.data[glazing] = BG
    g.data[glazing & (g.z >= 44) & (g.z < 47)] = GR
    # Glazing is an uninterrupted curved band with regularly spaced stout mullions.
    for x in (15, 32, 50, 68, 86):
        g.data[glazing & (g.x >= x) & (g.x < x+3)] = SE
    g.cylinder((52, 60, 24), 44, 6, 2, CE)
    g.data[(radius >= 42) & (radius <= 44) & (g.z >= 20) & (g.z < 23)] = CU
    g.cylinder((52, 60, 54), 45, 6, 2, CE)
    roof = ((g.x-52)/43)**2 + ((g.y-60)/43)**2 + ((g.z-54)/17)**2 <= 1
    g.data[roof & (g.z >= 55)] = CE
    g.data[roof & (g.z >= 61) & (g.z < 64) & (radius >= 30)] = CS
    g.cylinder((52, 60, 70), 24, 5, 2, SE)
    g.cylinder((52, 60, 74), 19, 4, 2, CE)
    # Individual perimeter foot pads rather than a landscape base.
    for theta in np.deg2rad((0, 60, 120, 180, 240, 300)):
        x, y = 52+40*np.cos(theta), 60+40*np.sin(theta)
        g.roundbox((x-5, y-5, 4), (x+5, y+5, 14), 2, SE)
    # A projecting, actually open airlock vestibule is attached to the chamber.
    g.roundbox((87, 29, 10), (122, 68, 52), 7, CE)
    g.roundbox((94, 27, 15), (116, 62, 45), 3, 0)
    g.roundbox((90, 26, 12), (121, 35, 50), 5, CU)
    g.roundbox((96, 24, 17), (115, 37, 44), 3, 0)
    g.box((95, 60, 15), (116, 64, 44), SE)
    g.cylinder((105, 59, 32), 6, 3, 1, AL)
    g.cylinder((105, 57, 32), 4, 2, 1, BG)
    g.box((87, 17, 2), (124, 39, 5), SE)
    g.box((90, 20, 5), (121, 40, 8), AL)
    g.box((93, 23, 8), (118, 42, 12), SE)
    g.box((96, 26, 12), (115, 43, 16), AL)
    for x in (93, 117):
        g.box((x, 25, 27), (x+3, 29, 38), AM)
    g.box((100, 24, 46), (111, 28, 49), LA)
    # Attached thermal-management pack and real pipe elbows.
    g.roundbox((98, 72, 12), (124, 100, 54), 3, SE)
    g.box((121, 75, 17), (126, 97, 50), CE)
    g.box((124, 78, 20), (127, 94, 47), RE)
    for z in (21, 27, 33, 39, 45):
        g.box((125, 79, z), (128, 94, z+2), AL)
    g.beam((87, 84, 52), (100, 84, 61), 2.8, CU)
    g.beam((100, 84, 61), (114, 84, 61), 2.8, CU)
    g.beam((114, 84, 61), (114, 84, 52), 2.8, CU)
    g.cylinder((100, 84, 61), 3.8, 4, 0, AL)
    # Roof thermal imager, wind instrument and a tall communications antenna.
    g.cylinder((35, 53, 83), 3, 17, 2, SE)
    g.roundbox((27, 44, 89), (44, 61, 102), 3, SE)
    g.cylinder((35, 43, 96), 5, 4, 1, CU)
    g.cylinder((35, 40, 96), 3, 2, 1, BG)
    g.cylinder((65, 65, 79), 6, 8, 2, CU)
    g.cylinder((65, 65, 100), 2.3, 42, 2, SE)
    g.cylinder((65, 65, 122), 1.3, 9, 2, AL)
    g.cylinder((65, 65, 93), 4, 4, 2, AM)
    g.cylinder((52, 78, 85), 2, 20, 2, SE)
    g.beam((43, 78, 93), (61, 78, 93), 1.7, AL)
    g.beam((52, 69, 93), (52, 87, 93), 1.7, AL)
    for x, y in ((43, 78), (61, 78), (52, 69), (52, 87)):
        g.cylinder((x, y, 94), 3, 4, 2, SE)
    return Asset('volcano_observatory', 'Glazed volcano monitoring observatory', g, .05,
                 ['Original rounded protected observation chamber with ceramic dome and opaque panoramic glazing.',
                  'Open airlock vestibule, rear inner door, access steps, attached thermal plant and three roof instruments.',
                  'No landscape or smoke effects. No manual half correction.'])


def make_assets():
    return [thermal_rover(), geothermal_drill(), cooling_tower(), volcano_observatory()]


if __name__ == '__main__':
    run_theme(Path(__file__).resolve().parent, make_assets())
