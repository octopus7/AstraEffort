"""Original sled-mounted ice core rig, authored in native voxel occupancy.

Only the accepted Antarctic palette is reused for theme continuity. Geometry
is newly authored here. The scientific barrel is blunt, the deck bore is a
real opening, and the rig is shown planted on four stabilizers.
"""
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, "D:/github/AstraEffort/voxel/_tools")
from voxelkit import Asset, Grid, run_theme

EMPTY, IVORY, SNOW, SHADOW, NAVY, BLUE, DARK, STEEL, SILVER, ORANGE, AMBER, GLASS, SKY, BLACK, LAMP, SLATE = range(16)
PALETTE = [
    (0, 0, 0, 0), (231, 222, 202, 255), (249, 242, 224, 255),
    (184, 182, 169, 255), (31, 67, 91, 255), (42, 87, 117, 255),
    (41, 47, 53, 255), (98, 112, 121, 255), (152, 162, 163, 255),
    (233, 111, 24, 255), (255, 159, 45, 255), (35, 108, 147, 255),
    (91, 169, 193, 255), (25, 33, 40, 255), (255, 239, 184, 255),
    (67, 78, 85, 255),
]


def ice_core_drill():
    g = Grid((112, 98, 128), PALETTE)
    # The two continuous transport runners have gently lifted, blunt noses.
    for xx in (25, 87):
        g.roundbox((xx - 8, 9, 3), (xx + 8, 94, 13), 4, NAVY)
        g.roundbox((xx - 7, 7, 8), (xx + 7, 23, 17), 4, BLUE)
        g.box((xx - 4, 26, 12), (xx + 4, 87, 16), SHADOW)
        g.box((xx - 4, 10, 16), (xx + 4, 18, 19), NAVY)
        for yy in (33, 76):
            g.box((xx - 5, yy - 4, 14), (xx + 5, yy + 4, 24), STEEL)
            g.box((xx - 6, yy - 5, 20), (xx + 6, yy + 5, 25), NAVY)
    g.box((22, 23, 18), (90, 29, 25), DARK)
    g.box((22, 69, 18), (90, 76, 25), DARK)
    # Four separate stabilizers carry the rig while coring.
    for xx in (8, 104):
        for yy in (25, 81):
            g.roundbox((xx - 7, yy - 7, 0), (xx + 7, yy + 7, 4), 2, DARK)
            g.box((xx - 5, yy - 5, 4), (xx + 5, yy + 5, 7), ORANGE)
            g.cylinder((xx, yy, 15), 3.2, 19, 2, SILVER)
            g.box((xx - 5, yy - 4, 22), (xx + 5, yy + 4, 30), NAVY)
            g.box((xx - 3, yy - 5, 24), (xx + 3, yy - 3, 28), ORANGE)
            g.beam((xx, yy, 27), (17 if xx < 56 else 95, yy, 27), 3, STEEL)
    # Deck and grated standing areas. The central bore is cut all the way
    # through the structural depth, before inserting the narrow barrel.
    g.roundbox((10, 20, 23), (102, 89, 29), 3, NAVY)
    g.roundbox((11, 21, 28), (101, 88, 33), 2, IVORY)
    for left, right in ((15, 39), (74, 99)):
        g.box((left, 28, 32), (right, 83, 35), SLATE)
        for yy in range(30, 82, 6):
            for xx in range(left + 2, right - 2, 6):
                g.box((xx, yy, 33), (xx + 3, yy + 3, 36), EMPTY)
    g.box((46, 31, 0), (66, 57, 36), EMPTY)
    # Split front safety rail leaves access to the coring throat.
    for a, b in ((13, 38), (74, 100)):
        for xx in (a, b):
            g.box((xx - 2, 22, 32), (xx + 2, 26, 36), DARK)
            g.beam((xx, 24, 35), (xx, 24, 45), 1.7, ORANGE)
        g.beam((a, 24, 45), (b, 24, 45), 1.7, ORANGE)
    for yy in (27, 56, 85):
        g.beam((101, yy, 34), (101, yy, 45), 1.7, ORANGE)
    g.beam((101, 26, 45), (101, 86, 45), 1.7, ORANGE)
    # Upright mast: two broad columns, two distinct steel guide rails,
    # rear diagonal braces, and a square header with a blunt top winch.
    for xx in (40, 72):
        g.roundbox((xx - 5, 44, 33), (xx + 5, 59, 111), 2, IVORY)
        g.box((xx - 6, 42, 33), (xx + 6, 61, 39), NAVY)
        g.box((xx - 4, 42, 43), (xx + 4, 45, 51), BLUE)
        g.box((xx - 4, 42, 91), (xx + 4, 45, 99), BLUE)
        g.beam((xx, 74, 33), (xx, 57, 98), 2.7, NAVY)
        g.box((xx - 5, 70, 32), (xx + 5, 78, 36), STEEL)
    for xx in (45, 67):
        g.cylinder((xx, 43, 72), 2.0, 74, 2, STEEL)
        g.box((xx - 2, 41, 35), (xx + 2, 46, 40), DARK)
    g.roundbox((35, 43, 108), (77, 62, 114), 2, SNOW)
    for xx in (40, 72):
        g.roundbox((xx - 3, 43, 112), (xx + 3, 61, 127), 1.5, NAVY)
    g.cylinder((56, 52, 119), 7.5, 27, 0, DARK)
    for xx in (44, 68):
        g.cylinder((xx, 52, 119), 9, 3, 0, STEEL)
    for xx in (48, 53, 58, 63):
        g.cylinder((xx, 52, 119), 7.8, 2, 0, SLATE)
    for xx in (36, 76):
        g.cylinder((xx, 52, 119), 4.6, 4, 0, ORANGE)
        g.cylinder((xx, 52, 119), 1.8, 6, 0, DARK)
    # Vertical core tube passes through the open deck slot; its lower end is
    # a blunt sampling shoe, not an ornamental pointed spike.
    g.cylinder((56, 42, 68), 4.5, 64, 2, STEEL)
    g.cylinder((56, 42, 23), 4.0, 32, 2, STEEL)
    g.cylinder((56, 42, 7), 5.0, 5, 2, DARK)
    for zz in (20, 38, 58, 85, 97):
        g.cylinder((56, 42, zz), 4.9, 2, 2, SILVER)
    g.cylinder((56, 42, 34), 6.7, 5, 2, DARK)
    g.beam((56, 44, 117), (56, 44, 98), 1.5, DARK)
    # The orange sliding drive visibly bridges the two guide rails.
    g.roundbox((45, 33, 64), (67, 53, 78), 3, ORANGE)
    g.box((44, 35, 75), (68, 51, 79), AMBER)
    for xx in (44, 68):
        g.roundbox((xx - 3, 39, 66), (xx + 3, 48, 76), 1.5, DARK)
        g.box((xx - 1, 38, 69), (xx + 1, 42, 73), SILVER)
    g.roundbox((51, 31, 66), (61, 35, 75), 1.5, NAVY)
    g.box((54, 30, 69), (58, 33, 73), STEEL)
    # Independent left power cabinet, front cooling fins, side access latch
    # and an insulated supply line to the mast base.
    g.roundbox((14, 40, 34), (36, 69, 65), 3, IVORY)
    g.box((15, 41, 34), (35, 68, 39), NAVY)
    g.roundbox((18, 38, 42), (32, 42, 59), 2, DARK)
    for zz in (45, 50, 55):
        g.box((20, 37, zz), (30, 40, zz + 2), STEEL)
    g.box((35, 49, 45), (39, 62, 58), ORANGE)
    g.box((38, 53, 49), (40, 58, 54), DARK)
    g.box((18, 44, 64), (32, 65, 67), SNOW)
    g.box((23, 51, 66), (29, 58, 69), ORANGE)
    g.beam((33, 66, 59), (33, 73, 59), 2.3, DARK)
    g.beam((33, 73, 59), (33, 73, 79), 2.3, DARK)
    g.cylinder((33, 73, 79), 3.0, 4, 2, SLATE)
    g.beam((34, 68, 41), (41, 70, 41), 2, DARK)
    g.beam((41, 70, 41), (48, 61, 41), 2, DARK)
    # Three individually modeled capped sample canisters in a fixed rack.
    g.roundbox((71, 65, 34), (105, 82, 39), 2, NAVY)
    for xx in (78, 88, 98):
        g.cylinder((xx, 74, 52), 4.0, 30, 2, IVORY)
        g.cylinder((xx, 74, 39), 4.5, 4, 2, BLUE)
        g.cylinder((xx, 74, 68), 4.8, 5, 2, NAVY)
        g.cylinder((xx, 74, 72), 1.8, 4, 2, ORANGE)
        g.cylinder((xx, 74, 64), 4.1, 2, 2, SHADOW)
    for xx in (72, 104):
        g.box((xx - 2, 71, 38), (xx + 2, 78, 57), DARK)
    g.beam((72, 68, 52), (104, 68, 52), 1.8, ORANGE)
    g.beam((72, 80, 52), (104, 80, 52), 1.8, STEEL)
    # Tow point and rear utility couplers make both transport ends useful.
    g.beam((56, 24, 19), (56, 16, 14), 2.1, STEEL)
    g.torus((56, 12, 14), 4.3, 1.7, 2, NAVY)
    g.box((49, 85, 31), (63, 91, 38), BLUE)
    for xx in (52, 60):
        g.cylinder((xx, 90, 35), 2.3, 4, 1, ORANGE)
    return Asset("ice_core_drill", "Sled-mounted Antarctic ice core drill", g, 0.045, notes={
        "features": "Two sled runners, four planted stabilizers, open through-deck coring slot, blunt vertical barrel, two-column mast with top winch and sliding drive, side power cabinet and three sample cylinders.",
        "half_strategy": "Slot 20 by 26 large voxels, barrel 8-9 voxels diameter, guide rails 4 voxels diameter, stabilizers 6.4 voxels diameter. No manual half postprocess.",
        "palette": "Accepted Antarctic palette, reused only as authorized theme colors; geometry independently authored.",
        "front": "-Y",
        "static_pose": "Stabilizers deployed; no animation or articulated rig supplied.",
    })


def make_assets():
    return [ice_core_drill()]


if __name__ == "__main__":
    run_theme(Path(__file__).resolve().parent, make_assets())
