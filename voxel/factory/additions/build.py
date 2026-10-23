"""Original articulated assembly workcell; independent native voxel occupancy."""
from pathlib import Path
import sys

sys.path.insert(0, r"D:\github\AstraEffort\voxel\_tools")
from voxelkit import Grid, Asset, run_theme

PALETTE = [(0,0,0,0), (226,169,45,255), (248,198,70,255), (170,115,30,255),
           (69,106,132,255), (93,135,159,255), (45,72,90,255),
           (217,209,184,255), (241,231,206,255), (154,150,135,255),
           (43,47,48,255), (60,65,66,255), (94,100,102,255),
           (141,151,153,255), (28,39,43,255), (63,118,134,255),
           (179,76,43,255), (220,181,99,255)]
YELLOW, EDGE, OCHRE, BLUE, BLUE_L, BLUE_D, IVORY, WHITE, REVEAL, DARK, TREAD, STEEL, METAL, DEEP, GLASS, RED, BRASS = range(1,18)


def make_assets():
    g = Grid((112, 104, 128), PALETTE)
    # Compact machine skid, mounting deck and two actual front fork pockets.
    g.roundbox((6,4,2), (106,96,12), 4, BLUE)
    g.box((12,10,9), (100,90,13), STEEL)
    for x in (30,70):
        g.box((x,0,3), (x+16,14,8), 0)
    for x in (9,95):
        for y in (7,85):
            g.roundbox((x-3,y-3,0), (x+9,y+9,5), 2, DARK)
            g.box((x,y,11), (x+5,y+5,14), METAL)
    # Four-legged fixture table, with a clear service opening beneath its top.
    for x in (16,54):
        for y in (9,40):
            g.box((x,y,12), (x+6,y+6,34), BLUE)
            g.box((x-2,y-2,12), (x+8,y+8,17), STEEL)
    for y in (12,43):
        g.box((19,y,17), (57,y+3,21), BLUE_D)
    g.roundbox((13,6,31), (64,49,38), 2, STEEL)
    g.box((16,9,36), (61,46,40), METAL)
    for x in (19,27,35,43,51):
        g.box((x,38,38), (x+3,44,40), DEEP)
    for x,y in ((16,9),(55,9),(16,40),(55,40)):
        g.box((x,y,36), (x+6,y+6,44), YELLOW)
        g.cylinder((x+3,y-1,40), 1.5, 3, 1, METAL)
    # Machined fixture/workpiece has a real central through bore.
    g.roundbox((26,12,40), (48,34,46), 2, IVORY)
    g.cylinder((37,23,49), 7, 12, 2, METAL)
    g.cylinder((37,23,47), 3.5, 21, 2, 0)
    for x in (24,48):
        g.box((x,16,39), (x+4,29,44), BLUE_D)
        g.box((x,20,43), (x+4,26,47), STEEL)
    # Bolted blue pedestal and the yaw bearing under a large round shoulder.
    g.roundbox((65,55,12), (95,85,31), 4, BLUE)
    g.box((70,54,15), (90,58,28), YELLOW)
    g.cylinder((79,69,32), 15, 7, 2, YELLOW)
    g.cylinder((79,69,36), 12, 5, 2, BLUE_D)
    g.cylinder((79,69,44), 9, 18, 2, STEEL)
    # Broad articulated links remain separate in silhouette.
    g.beam((79,67,62), (64,62,105), 8, YELLOW)
    g.beam((79,61,66), (65,57,101), 3, EDGE)
    g.beam((64,62,105), (37,28,91), 6.7, YELLOW)
    g.beam((61,57,108), (39,30,97), 2.5, EDGE)
    # Shoulder and elbow axles have robust nested round housings.
    for x,y,z,r in ((79,67,57,15),(64,62,105,12)):
        g.cylinder((x,y,z), r, 20, 1, YELLOW)
        g.cylinder((x,y-11,z), r-3, 5, 1, DARK)
        g.cylinder((x,y-14,z), r-6, 4, 1, STEEL)
        g.cylinder((x,y-17,z), 3.2, 4, 1, METAL)
    # Wrist flange and downward-facing parallel gripper.
    g.cylinder((37,28,91), 9, 14, 1, YELLOW)
    g.cylinder((37,20,91), 7, 6, 1, DARK)
    g.cylinder((37,16,91), 4.7, 4, 1, METAL)
    g.cylinder((37,22,83), 5, 10, 2, STEEL)
    g.roundbox((23,17,78), (51,27,84), 2, DARK)
    for x in (23,45):
        g.box((x,18,65), (x+6,26,80), STEEL)
        g.roundbox((x,18,62), (x+6,26,69), 1, IVORY)
        g.cylinder((x+3,16,77), 1.7, 3, 1, METAL)
    # External servo conduit follows the arm and connects into the base.
    for a,b in (((87,79,26),(97,79,57)), ((97,79,57),(80,75,91)),
                ((80,75,91),(68,70,109)), ((68,70,109),(46,40,101)),
                ((46,40,101),(37,28,96))):
        g.beam(a,b,2.2,DARK)
    # Independent operator console: cream shell, recessed screen and switches.
    g.roundbox((90,14,13), (106,37,44), 3, IVORY)
    g.roundbox((86,10,37), (108,34,59), 3, WHITE)
    g.box((90,8,47), (104,12,56), STEEL)
    g.box((92,7,49), (102,9,54), GLASS)
    for x,c in ((91,BLUE_D),(98,BLUE),(104,RED)):
        g.cylinder((x,8,41), 2, 3, 1, c)
    g.box((105,20,20), (109,31,33), REVEAL)
    for z in (23,28):
        g.box((108,22,z), (110,29,z+2), STEEL)
    g.beam((99,35,16),(99,55,16),2,DARK)
    g.beam((99,55,16),(90,61,16),2,DARK)
    # Back pedestal panel and service fasteners.
    g.box((72,84,16), (88,87,27), BLUE_D)
    g.box((76,86,19), (84,89,24), STEEL)
    for x in (69,89):
        g.cylinder((x,56,18),1.7,3,1,METAL)
    return [Asset("robot_workcell", "Articulated robot assembly workcell", g, voxel_size=.04,
                  notes={"features": ["round shoulder elbow and wrist", "two separated blunt gripper fingers", "bored workpiece and fixture table", "pedestal", "machine skid", "side console"],
                         "palette": "Permitted factory palette continuity; geometry is independently authored.",
                         "half": "Native conservative 2x reduction, doubled meters per voxel. Wide gripper and table openings retained; no manual half-grid corrections."})]


if __name__ == "__main__":
    run_theme(Path(__file__).resolve().parent, make_assets())
