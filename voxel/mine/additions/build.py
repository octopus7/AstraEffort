"""Independently authored six-wheel ore hauler with an empty open dump body."""
from pathlib import Path
import sys
import math
import numpy as np
sys.path.insert(0, r"D:\github\AstraEffort\voxel\_tools")
from voxelkit import Grid, Asset, run_theme

PALETTE=[(0,0,0,0),(106,115,75,255),(138,146,102,255),(62,74,49,255),
         (209,201,172,255),(235,225,196,255),(73,82,80,255),(116,126,122,255),
         (33,40,38,255),(55,65,60,255),(194,100,43,255),(230,137,63,255),
         (168,177,170,255),(65,98,102,255),(20,28,27,255),(142,108,66,255),
         (135,145,137,255),(236,177,61,255)]
OLIVE,OLIVE_L,OLIVE_D,CREAM,WHITE,STEEL,STEEL_L,DARK,TREAD,COPPER,COPPER_L,METAL,GLASS,DEEP,ORE,STONE,AMBER=range(1,18)

def make_assets():
    g=Grid((104,128,96),PALETTE)
    # Raised longitudinal chassis and three axles; no display floor.
    g.roundbox((24,17,27),(80,119,43),6,OLIVE_D)
    for x in (29,69):
        g.box((x,20,22),(x+6,119,32),STEEL)
    for y in (28,76,109):
        g.cylinder((52,y,22),4,76,0,STEEL)
        for x in (16,88):
            g.cylinder((x,y,18),16,18,0,DARK)
            g.torus((x,y,18),12.5,3.5,0,DARK)
            for k in range(16):
                a=k*math.tau/16
                g.ellipsoid((x,y+15.5*math.cos(a),18+15.5*math.sin(a)),(10,2.2,2.2),TREAD)
            g.cylinder((x,y,18),8,22,0,STEEL_L)
            g.cylinder((x,y,18),4.3,25,0,COPPER)
            g.cylinder((x,y,18),2,27,0,METAL)
    # Front radiator deck, offset cab and engine pack.
    g.roundbox((19,9,35),(85,49,49),4,OLIVE)
    g.roundbox((22,13,47),(50,43,67),4,OLIVE)
    g.box((26,10,51),(46,14,63),DEEP)
    for z in (53,58):
        g.box((27,9,z),(45,12,z+2),STEEL_L)
    g.roundbox((53,13,46),(82,43,77),4,CREAM)
    g.roundbox((56,10,54),(79,16,73),2,STEEL)
    g.box((59,8,57),(76,12,70),GLASS)
    g.roundbox((80,19,55),(85,38,72),2,GLASS)
    g.box((81,28,54),(86,32,73),CREAM)
    g.roundbox((50,10,75),(85,46,80),3,WHITE)
    g.box((81,34,49),(85,39,53),STEEL)
    g.cylinder((77,9,81),2.6,7,2,COPPER_L)
    g.cylinder((27,9,71),3,20,2,DARK)
    g.cylinder((27,9,81),4,3,2,STEEL)
    # Broad front bumper and a clearly recessed radiator with slats.
    g.roundbox((11,4,25),(93,12,32),2,STEEL)
    g.box((31,7,31),(59,12,45),DEEP)
    for z in (33,38,43):
        g.box((33,5,z),(57,9,z+2),STEEL_L)
    for x in (12,82):
        g.roundbox((x,3,25),(x+10,13,36),2,COPPER)
        g.box((x+2,1,29),(x+8,5,34),WHITE)
    # Access ladder beside the cab, and handrails around the engine deck.
    for z in (21,29,37,45):
        g.box((88,44,z),(101,52,z+3),STEEL_L)
    for y in (43,51):
        g.box((98,y,20),(101,y+3,53),COPPER)
    for x in (21,84):
        for y in (15,38):
            g.box((x,y,48),(x+3,y+3,61),COPPER)
        g.box((x,15,59),(x+3,41,63),COPPER_L)
    # Deep tapered dump body. All central cargo volume is genuinely empty.
    hx=32+(g.z-43)*.19
    hy=32+(g.z-43)*.15
    outer=(g.z>=43)&(g.z<86)&(np.abs(g.x-52)<hx)&(np.abs(g.y-85)<hy)
    g.data[outer]=OLIVE
    g.data[outer&(g.z<50)]=STEEL
    g.data[outer&(g.z>=53)&(g.z<68)]=CREAM
    inner=(g.z>=49)&(g.z<94)&(np.abs(g.x-52)<hx-5)&(np.abs(g.y-85)<hy-5)
    g.data[inner]=0
    g.box((12,46,83),(92,124,89),OLIVE_L)
    g.box((18,52,83),(86,118,94),0)
    # Protective cab canopy is part of the front dump wall.
    g.roundbox((12,15,81),(92,54,88),3,CREAM)
    g.box((17,16,86),(87,50,90),WHITE)
    # Ribs follow the sloping body walls; clamps are substantial at half size.
    for y in (60,82,105,119):
        for xb,xt in ((22,14),(82,90)):
            g.beam((xb,y,47),(xt,y,84),2.7,STEEL)
            g.box((xb-3,y-3,44),(xb+3,y+3,50),COPPER)
            g.box((xt-3,y-3,82),(xt+3,y+3,88),COPPER)
    for x in (30,74):
        g.beam((x,116,48),(x,124,84),2.4,STEEL)
    # Rear hinge axle and two externally visible hoist cylinders.
    g.cylinder((52,114,40),4,72,0,STEEL)
    for x in (18,86):
        g.cylinder((x,114,40),5.5,8,0,COPPER)
    for x in (16,88):
        g.box((x-4,70,32),(x+4,82,39),OLIVE_D)
        g.beam((x,74,35),(x,96,54),3.4,COPPER)
        g.beam((x,96,54),(x,109,64),2,METAL)
        g.cylinder((x,109,64),4,8,0,STEEL)
    # Rear lamps and lock brackets are useful from the opposite view.
    for x in (24,76):
        g.box((x,122,43),(x+5,126,49),COPPER)
        g.box((x+1,125,44),(x+4,127,47),AMBER)
    return [Asset("haul_truck","Six-wheel open-bed mine haul truck",g,voxel_size=.055,
                  notes={"features":["six giant off-road tires","offset front cab and engine deck","deep empty dump bed","wall ribs","rear hinge","external hoist cylinders"],
                         "palette":"Permitted mine palette continuity; original geometry.",
                         "half":"Conservative 2x native reduction; no manual correction. Bed cavity and six wheel positions remain separate; fine tread and grille details simplify."})]

if __name__=="__main__":
    run_theme(Path(__file__).resolve().parent,make_assets())
