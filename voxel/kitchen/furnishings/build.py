"""Pure, independently authored kitchen furnishing occupancy. Front is -Y."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import numpy as np

ROOT = Path(__file__).resolve().parent
TOOLS = ROOT.parents[1] / '_tools'
sys.path.insert(0, str(TOOLS))
from voxelkit import Asset, Grid

PALETTE = [
    (0,0,0,0), (232,225,205,255), (121,151,133,255),
    (75,105,91,255), (181,130,78,255), (217,176,113,255),
    (48,56,57,255), (156,170,170,255), (91,108,112,255),
    (92,133,145,255), (244,239,225,255), (191,105,70,255),
    (35,42,44,255), (217,164,85,255), (151,94,48,255),
    (203,183,106,255),
]
PALETTE_NAMES = ['empty','cream','sage','dark sage','warm oak','pale oak',
                 'charcoal','metal','dark metal','opaque glass','ceramic white',
                 'warm accent','dark cavity','bread','bread crust','indicator']

def front_pull(g, x0, x1, z, front=4, color=6):
    """A true projecting U pull; empty behind the grip, not a painted line."""
    g.roundbox((x0,0,z),(x1,4,z+4),1,color)
    g.box((x0,2,z),(x0+4,front+5,z+4),color)
    g.box((x1-4,2,z),(x1,front+5,z+4),color)

def panel(g, lo, hi):
    x0,y0,z0=lo; x1,y1,z1=hi
    # Keep the entire facade behind Y=8 or farther: four large cells of air
    # remain behind the Y=0..4 grip, including after conservative reduction.
    g.roundbox((x0,y0+2,z0),hi,2,2)
    g.box((x0+4,y0+2,z0+4),(x1-4,y0+4,z1-4),3)
    g.box((x0+6,y0+2,z0+6),(x1-6,y0+4,z1-6),2)

def bowl(g, cx,cy,z,r=11,depth=9):
    g.ellipsoid((cx,cy,z+depth*.6),(r,r,depth),10)
    g.box((cx-r-1,cy-r-1,z+depth),(cx+r+1,cy+r+1,z+2*depth+1),0)
    g.ellipsoid((cx,cy,z+depth),(r-4,r-4,depth-2),0)

def sink_cabinet():
    g=Grid((128,80,124),PALETTE)
    g.roundbox((12,18,2),(116,71,14),2,6)
    g.roundbox((6,10,10),(122,74,87),3,3)
    g.box((9,13,15),(119,71,87),2)
    panel(g,(10,7,18),(61,13,79)); panel(g,(65,7,18),(118,13,79))
    front_pull(g,38,56,58,front=7); front_pull(g,70,88,58,front=7)
    # Exposed right side panel and small countertop overhang.
    g.box((121,17,19),(124,67,78),2)
    g.roundbox((2,5,85),(126,78,94),3,1)
    # Real deep sink: metal bowl, cream surround, empty interior.
    g.roundbox((24,18,69),(104,62,96),6,7)
    g.roundbox((30,24,75),(98,56,101),5,0)
    g.cylinder((64,40,75),6,2,2,8)
    g.cylinder((64,40,75),2.8,8,2,0)
    # Squared stepped gooseneck; suspended outlet over the empty bowl.
    g.roundbox((60,63,94),(68,71,120),3,7)
    g.roundbox((60,40,115),(68,71,123),3,7)
    g.roundbox((60,39,108),(68,47,121),2,7)
    g.box((62,40,107),(66,46,110),8)
    g.cylinder((84,66,96),6,4,2,8)
    g.roundbox((82,63,97),(87,69,107),1,7)
    return Asset('sink_cabinet','Sink cabinet',g,.01,
        ['1.28 m grid width; cream worktop, sage twin doors.',
         'Empty metal basin with real drain bore and overhead faucet.',
         'Projecting handles have empty clearance. No half postprocessing.'])

def kitchen_island():
    g=Grid((128,84,92),PALETTE)
    for x in (14,78,108):
        for y in (19,63):g.box((x-3,y-3,2),(x+3,y+3,14),4)
    g.roundbox((10,14,11),(90,71,82),2,3)
    for x0,x1 in ((14,48),(52,86)):
        panel(g,(x0,8,17),(x1,15,60))
        panel(g,(x0,8,64),(x1,15,79))
        front_pull(g,x0+7,x1-7,48,front=8)
        front_pull(g,x0+7,x1-7,69,front=8)
    # Open side shelving intentionally visible from the +X preview side.
    for z in (13,44,77):g.box((88,17,z),(117,69,z+5),5)
    for y in (17,64):g.box((88,y,15),(117,y+5,81),2)
    # A stack of dishes in the lower bay; upper bay remains empty.
    for z,r in ((20,11),(24,12),(28,12)):
        g.cylinder((102,42,z),r,3,2,10)
    g.roundbox((2,4,82),(126,80,90),3,5)
    # Inlaid plank seams are oak color, not nonfunctional cutouts.
    for x in (27,52,77,102):g.box((x,7,89),(x+2,77,90),4)
    # Side towel rail and folded cloth; open loop above the cloth.
    g.box((116,19,62),(127,23,66),6)
    g.box((116,65,62),(127,69,66),6)
    g.roundbox((123,19,62),(128,69,66),1,6)
    g.roundbox((123,33,37),(127,49,64),1,1)
    g.box((123,33,43),(128,49,47),11)
    return Asset('kitchen_island','Kitchen island',g,.011,
        ['1.408 m grid width; pale oak plank top with sage cupboards and drawers.',
         'Open right-side shelves, ceramic stack and functional towel-rail loop.',
         'No half postprocessing.'])

def dish_cabinet():
    g=Grid((92,54,128),PALETTE)
    for x in (11,81):
        for y in (16,44):g.roundbox((x-4,y-4,2),(x+4,y+4,13),1,4)
    g.roundbox((5,10,9),(87,50,49),2,3)
    panel(g,(8,6,15),(44,12,44)); panel(g,(48,6,15),(84,12,44))
    front_pull(g,20,38,31,front=6); front_pull(g,54,72,31,front=6)
    g.roundbox((2,5,46),(90,52,54),2,1)
    # Open-front hutch: real display shelves, opaque blue-gray back only.
    g.box((6,45,53),(86,50,122),9)
    g.box((5,10,53),(11,50,123),2)
    g.box((81,10,53),(87,50,123),2)
    for z in (55,86,118):g.box((10,10,z),(82,46,z+5),5)
    g.roundbox((2,6,121),(90,52,127),2,1)
    # Two upright plates on the lower display shelf.
    for x in (29,65):
        g.cylinder((x,29,73),13,5,1,10)
        g.cylinder((x,26,73),9,2,1,1)
        g.box((x-6,20,60),(x+6,32,63),4)
    # Bowl and hollow mug on the upper shelf.
    bowl(g,29,29,94,12,9)
    g.cylinder((63,29,101),10,19,2,10)
    g.cylinder((63,29,105),6,16,2,0)
    g.torus((75,29,102),6,2.5,1,10)
    return Asset('dish_cabinet','Dish cabinet',g,.014,
        ['1.792 m grid height; open-front sage hutch over a closed twin-door cupboard.',
         'Two plate stands, a genuinely hollow bowl and mug; opaque blue-gray back.',
         'Display shelves have open clearances. No half postprocessing.'])

def kitchen_cart():
    g=Grid((100,72,128),PALETTE)
    # Independent four caster wheels with metal hubs and short forks.
    for x in (14,86):
        for y in (15,57):
            g.cylinder((x,y,11),9,8,0,6)
            g.cylinder((x+4,y,11),4,2,0,7)
            g.box((x-3,y-3,14),(x+3,y+3,26),8)
    for x in (10,84):
        for y in (12,54):g.roundbox((x,y,23),(x+6,y+6,111),1,2)
    for z in (26,64):
        g.roundbox((7,9,z),(93,63,z+6),2,4)
        for x in range(11,90,13):g.box((x,12,z+4),(min(x+10,90),60,z+7),5)
    # Towels on bottom shelf and open air above; middle shelf is clear.
    for z,c in ((33,1),(38,2),(43,1)):
        g.roundbox((24,24,z),(52,51,z+5),2,c)
    g.roundbox((9,10,83),(92,63,109),2,3)
    panel(g,(13,6,87),(88,12,105))
    front_pull(g,35,65,94,front=6)
    g.roundbox((3,6,109),(96,66,118),3,5)
    g.box((8,12,117),(91,14,118),4)
    g.box((8,58,117),(91,60,118),4)
    # Raised U transport handle on right: void below its grip.
    for y in (14,56):g.roundbox((90,y,112),(99,y+5,126),2,6)
    g.roundbox((94,14,122),(100,61,128),2,6)
    return Asset('kitchen_cart','Kitchen cart',g,.0078,
        ['0.9984 m grid height; four caster wheels, drawer, two slatted shelves and towel stack.',
         'Open storage bays and raised transport handle survive half reduction.',
         'No half postprocessing.'])

def dish_drying_rack():
    g=Grid((128,94,72),PALETTE)
    g.roundbox((3,4,3),(125,90,14),5,2)
    g.roundbox((9,10,9),(119,84,18),3,0)
    # Shallow floor drainage channels, with the floor remaining structural.
    for x in range(15,117,12):g.box((x,16,8),(x+4,78,10),3)
    for x in (13,113):
        for y in (17,77):g.box((x-2,y-2,9),(x+2,y+2,22),8)
    for y in (17,77):g.beam((13,y,20),(115,y,20),2.5,7)
    for x in (13,115):g.beam((x,17,20),(x,77,20),2.5,7)
    # Lower crossbar directly supports each plate and joins both side rails.
    g.box((13,44,17),(115,50,23),7)
    # Four divider loops leave three large real plate slots between them.
    for x in (18,36,54,72):
        points=[(x,20,20),(x,25,39),(x,34,48),(x,60,48),(x,69,39),(x,74,20)]
        for a,b in zip(points,points[1:]):g.beam(a,b,2,7)
    for x in (27,45,63):
        g.cylinder((x,47,44),24,5,0,10)
        g.cylinder((x+3,47,44),18,2,0,1)
    # Hollow utensil cup and individual utensils in the right bay.
    g.roundbox((88,25,18),(116,59,48),3,2)
    g.box((94,31,24),(110,53,51),0)
    g.beam((99,38,25),(99,38,64),2,8)
    g.ellipsoid((99,38,65),(4,5,6),7)
    g.beam((106,47,25),(106,47,62),2,8)
    g.box((103,44,60),(110,50,68),7)
    g.box((105,43,64),(107,51,70),0)
    # Tray handles have an actual rectangular loop clearance.
    for x in (2,122):
        g.roundbox((x,31,9),(x+4,63,23),1,2)
        g.box((x-1,39,13),(x+5,55,19),0)
    return Asset('dish_drying_rack','Dish drying rack',g,.0046,
        ['0.5888 m grid width; drained sage tray, metal loops, three upright plates.',
         'Real slot air gaps, hollow utensil cup and open tray handles.',
         'No half postprocessing.'])

def knife_block():
    g=Grid((78,72,128),PALETTE)
    g.roundbox((6,8,2),(72,65,10),3,4)
    g.roundbox((8,10,7),(70,63,83),4,5)
    # Slanted top is authored as individual occupied voxels, not a smooth mesh.
    mask=np.broadcast_to(g.z > 54 + .5*(g.y-10),g.shape)
    g.data[mask]=0
    g.box((8,17,10),(11,57,54),4)
    g.box((67,17,10),(70,57,54),4)
    # Three used slots plus a conspicuous unused front slot.
    for x in (20,40,60):g.box((x-7,30,51),(x+7,56,86),0)
    g.box((33,17,42),(47,28,73),0)
    # Distinct blade lengths, broad metal blades, bolsters and charcoal grips.
    for x,blade_top,handle_top in ((20,96,125),(40,86,116),(60,101,127)):
        g.box((x-3,34,51),(x+3,53,blade_top),7)
        # Small dark spine makes the blade thickness legible.
        g.box((x+2,49,69),(x+4,53,blade_top),8)
        g.roundbox((x-7,38,blade_top-1),(x+7,55,blade_top+4),1,7)
        g.roundbox((x-6,40,blade_top+3),(x+6,53,handle_top),2,6)
        g.box((x-5,40,handle_top-6),(x+5,42,handle_top-2),4)
    return Asset('knife_block','Knife block',g,.0032,
        ['0.4096 m grid height; slanted pale-oak block with three inserted knives.',
         'An unused front slot and air gaps beside used knife slots are real empty voxels.',
         'Knife handles and exposed blade lengths vary. No half postprocessing.'])

def make_assets():
    """Return six fresh Asset instances; has no filesystem or Blender side effects."""
    return [sink_cabinet(),kitchen_island(),dish_cabinet(),kitchen_cart(),
            dish_drying_rack(),knife_block()]

if __name__ == '__main__':
    from preview_pipeline import main
    main()
