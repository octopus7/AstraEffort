"""An empty U-shaped harbor repair dock, authored as original occupied voxels."""
from pathlib import Path
import sys
import math
import numpy as np

sys.dont_write_bytecode = True
sys.path.insert(0, 'D:/github/AstraEffort/voxel/_tools')
from voxelkit import Grid, Asset, run_theme

PALETTE = [
    (0,0,0,0), (43,48,47,255), (67,76,74,255), (100,111,106,255),
    (150,158,145,255), (49,112,115,255), (76,141,141,255), (35,81,86,255),
    (218,214,188,255), (239,232,205,255), (178,77,42,255), (206,103,57,255),
    (136,56,34,255), (151,112,65,255), (185,142,84,255), (105,79,49,255),
    (153,154,138,255), (182,181,158,255), (120,127,117,255), (118,163,170,255),
    (165,193,190,255), (235,170,58,255), (174,155,111,255), (189,195,178,255),
    (250,223,153,255), (34,39,38,255),
]
BLACK, STEEL, METAL, METAL_L = 1,2,3,4
TEAL, TEAL_L, TEAL_D, IVORY, IVORY_L = 5,6,7,8,9
ORANGE, ORANGE_L, ORANGE_D, WOOD, WOOD_L, WOOD_D = 10,11,12,13,14,15
STONE, STONE_L, MORTAR, GLASS, GLASS_L, AMBER, ROPE, BOLT, LAMP, RUBBER = range(16,26)


def mooring_post(g, x, y):
    g.box((x-4,y-4,38),(x+4,y+4,41),METAL)
    g.cylinder((x,y,44),2.8,8,2,BLACK)
    g.roundbox((x-4,y-4,47),(x+4,y+4,51),1,STEEL)


def hull_stand(g, x, y):
    # A four-foot timber cradle with an actual open A-frame and a metal contact pad.
    g.box((x-7,y-6,6),(x+7,y+6,9),WOOD_D)
    for sx, sy in ((-5,-4),(-5,4),(5,-4),(5,4)):
        g.box((x+sx-2,y+sy-2,6),(x+sx+2,y+sy+2,10),STEEL)
    g.beam((x-5,y,9),(x,y,26),2.3,WOOD)
    g.beam((x+5,y,9),(x,y,26),2.3,WOOD_L)
    g.beam((x,y-5,9),(x,y,24),2.0,WOOD)
    g.beam((x,y+5,9),(x,y,24),2.0,WOOD_D)
    g.box((x-5,y-4,26),(x+5,y+4,29),METAL)
    for sx in (-3,3):
        g.cylinder((x+sx,y,29),1.2,2,2,BOLT)


def repair_dock():
    g = Grid((128,128,72),PALETTE)
    # Two independent long sidewalls and the rear closure form the U; no front wall.
    g.roundbox((4,6,0),(26,124,36),3,TEAL)
    g.roundbox((102,6,0),(124,124,36),3,TEAL)
    g.roundbox((4,101,0),(124,125,36),3,TEAL)
    walls = g.data > 0
    g.data[walls & (g.z<8)] = WOOD_D
    g.data[walls & (g.z>=8) & (g.z<12)] = ORANGE
    # Sparse regular construction joints give the painted masonry useful scale.
    seam = (np.mod(g.z-12,7)<1) | (np.mod(g.y+6*(np.floor(g.z/7)%2),13)<1)
    g.data[walls & (g.z>=13) & (g.z<34) & seam] = TEAL_D
    g.data[walls & (g.z>=32)] = IVORY
    # Low dry bay floor, with paving joints and two timber handling runners.
    g.roundbox((25,0,0),(103,104,6),1,STONE)
    floor = (g.x>=26)&(g.x<102)&(g.y>=0)&(g.y<103)&(g.z>=5)&(g.z<6)
    g.data[floor] = STONE_L
    g.data[floor & ((np.mod(g.x,12)<1)|(np.mod(g.y+6*(np.floor(g.x/12)%2),12)<1))] = MORTAR
    for x in (39,87):
        g.box((x,0,5),(x+3,101,7),WOOD)
        for y in (10,42,74):
            g.box((x, y, 6),(x+3,y+2,8),WOOD_L)
    # Continuous walkways, rounded ivory inner coping and external parapet caps.
    for xa,xb in ((7,23),(105,121)):
        g.box((xa,9,35),(xb,121,38),WOOD)
        for y in range(11,121,7):
            g.box((xa,y,37),(xb,y+1,38),WOOD_D)
    g.box((23,105,35),(105,122,38),WOOD)
    for x in range(25,105,7):
        g.box((x,105,37),(x+1,122,38),WOOD_D)
    g.roundbox((22,7,34),(28,104,39),1.5,IVORY)
    g.roundbox((100,7,34),(106,104,39),1.5,IVORY)
    g.roundbox((25,99,34),(103,105,39),1.5,IVORY)
    g.roundbox((3,9,35),(9,122,42),1.5,IVORY)
    g.roundbox((119,9,35),(125,122,42),1.5,IVORY)
    for y in range(14,123,13):
        g.box((3,y,37),(9,y+1,42),STONE_L)
        g.box((119,y,37),(125,y+1,42),STONE_L)
    # Timber lining and clamped pilasters on the inside walls and rear face.
    g.box((25,10,6),(28,101,31),WOOD_D)
    g.box((100,10,6),(103,101,31),WOOD_D)
    for y in range(12,102,8):
        g.box((25,y,7),(28,y+6,30),WOOD)
        g.box((100,y,7),(103,y+6,30),WOOD)
    g.box((28,100,6),(100,104,31),WOOD_D)
    for x in range(29,100,8):
        g.box((x,99,7),(x+6,103,30),WOOD)
    for x in (26,102):
        for y in (22,60,98):
            g.box((x-3,y-3,1),(x+3,y+3,38),WOOD_L)
            for z in (1,24):
                g.box((x-4,y-4,z),(x+4,y+4,z+5),STEEL)
                g.box((x-4,y-2,z+1),(x+4,y+2,z+3),METAL)
    for x in (38,66,92):
        g.box((x-3,98,6),(x+3,104,38),WOOD_L)
        for z in (7,25):
            g.box((x-4,97,z),(x+4,104,z+5),STEEL)
    # Exactly three discrete centerline keel blocks.
    for y in (24,54,84):
        g.roundbox((57,y-7,6),(71,y+7,11),1,STONE)
        g.box((59,y-6,11),(69,y+6,15),STONE_L)
        g.box((60,y-7,15),(68,y+7,19),WOOD_L)
        for yy in (y-7,y+5):
            g.box((59,yy,15),(69,yy+2,20),STEEL)
    # Two longitudinal rows of paired hull supports, leaving the middle and entry clear.
    for x in (46,82):
        for y in (34,72):
            hull_stand(g,x,y)
    # A narrow access ladder occupies the left rear edge, outside the central working volume.
    for y in (84,96):
        g.beam((30,y,6),(30,y,41),1.5,STEEL)
        g.beam((30,y,40),(25,y,45),1.5,STEEL)
        for z in (14,30):
            g.box((24,y-1,z),(31,y+2,z+3),METAL)
    for z in (10,18,26,34):
        g.beam((30,84,z),(30,96,z),1.5,METAL_L)
    # Compact tool cabinet with drawers and an actual recessed tool shelf.
    g.roundbox((9,82,38),(23,102,60),2,IVORY)
    g.box((10,80,39),(22,85,49),ORANGE)
    g.box((12,79,43),(20,82,45),STEEL)
    g.box((11,79,50),(21,85,57),BLACK)
    g.box((12,81,50),(20,86,52),WOOD)
    for x in (14,18):
        g.beam((x,80,52),(x,80,56),1.2,METAL_L)
    g.roundbox((7,80,58),(25,104,63),3,TEAL)
    g.box((10,80,59),(22,83,61),IVORY)
    # Rear hauling winch, bearing stools, drum flanges and coarse rope windings.
    for x in (41,65):
        g.box((x-2,107,38),(x+3,119,49),STEEL)
        g.cylinder((x,113,48),9.5,3,0,METAL)
    g.cylinder((53,113,48),7.5,21,0,ROPE)
    for x in range(44,64,3):
        g.cylinder((x,113,48),8.1,1.2,0,WOOD_D)
    g.cylinder((67,113,48),3,7,0,STEEL)
    g.torus((70,113,48),4.5,1.4,0,ORANGE)
    g.beam((53,107,53),(53,101,42),1.4,ROPE)
    g.beam((53,101,42),(53,101,10),1.3,ROPE)
    # Functional dock-edge fittings stay on the walls and rear deck.
    for x,y in ((15,15),(113,15),(15,115),(113,115),(87,114)):
        mooring_post(g,x,y)
    for x in (31,55,79,103):
        g.beam((x,123,38),(x,123,47),1.6,STEEL)
        g.box((x-2,121,46),(x+2,125,49),METAL)
    g.beam((29,123,47),(105,123,47),1.5,WOOD_D)
    for x in (3,125):
        for y in (31,80):
            g.torus((x,y,24),4.8,1.8,0,RUBBER)
            g.beam((x,y,29),(x,y,38),1.3,BLACK)
    return Asset('repair_dock','Empty harbor repair dock',g,voxel_size=0.10,notes=[
        'Original empty U-shaped repair dock: two long sidewalls, rear deck, lowered paved bay and an unobstructed open front; no boat, water or landscape.',
        'Three separate keel blocks and four timber A-frame supports arranged as two mirrored pairs, plus a compact cabinet, rear winch and access ladder.',
        'Original accepted harbor palette retained for visual continuity only. No accepted original geometry/source copied.',
        'Static opaque palette game-art model; no rig, winch animation, dry-dock water system or engineering-capacity claim.'
    ])


def make_assets():
    return [repair_dock()]


if __name__ == '__main__':
    run_theme(Path(__file__).resolve().parent,make_assets())
