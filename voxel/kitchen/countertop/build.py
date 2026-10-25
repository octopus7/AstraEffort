"""Original countertop voxel artwork. Pure make_assets(); no files or export side effects."""
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '_tools'))
from voxelkit import Grid, Asset

PALETTE = [
    (0,0,0,0), (232,225,205,255), (121,151,133,255),
    (75,105,91,255), (181,130,78,255), (217,176,113,255),
    (48,56,57,255), (156,170,170,255), (91,108,112,255),
    (92,133,145,255), (244,239,225,255), (191,105,70,255),
    (35,42,44,255), (217,164,85,255), (151,94,48,255),
    (203,183,106,255),
]

def polygon_prism(g, points, z0, z1, color):
    """Rasterize a deliberate planar knife profile into native cells."""
    x,y=g.x,g.y
    inside=np.zeros((g.shape[0],g.shape[1],1),dtype=bool)
    previous=points[-1]
    for current in points:
        ax,ay=previous; bx,by=current
        if ay != by:
            inside ^= ((ay>y)!=(by>y)) & (x < (bx-ax)*(y-ay)/(by-ay)+ax)
        previous=current
    g.data[inside & (g.z>=z0) & (g.z<z1)]=color

def stand_mixer():
    g=Grid((96,128,128),PALETTE)
    for x in (18,78):
        for y in (20,104):
            g.roundbox((x-7,y-7,0),(x+7,y+7,7),3,6)
    g.roundbox((8,8,4),(88,120,17),7,3)
    g.roundbox((10,10,10),(86,118,22),6,2)
    g.roundbox((30,85,16),(67,116,108),12,1)
    g.roundbox((34,90,25),(64,112,101),9,2)
    g.roundbox((17,17,88),(79,115,121),15,2)
    g.roundbox((17,17,91),(79,30,117),6,1)
    g.roundbox((20,26,87),(76,112,93),3,7)
    g.cylinder((48,101,106),13,22,0,3)
    g.cylinder((79,79,103),7,5,0,8)
    g.cylinder((82,79,103),5,4,0,6)
    g.beam((84,79,102),(84,82,105),1.7,10)
    # A small mechanical speed lever on the visible right cheek.
    g.beam((78,103,97),(88,110,97),2.5,7)
    g.ellipsoid((89,111,97),(4,4,4),6)
    # Metal bowl is a real open tapered shell, not a dark filled cylinder.
    g.cylinder((48,44,22),23,7,2,8)
    g.cone((48,44,42),23,33,42,2,7)
    g.cone((48,44,46),19,29,40,2,10)
    g.cone((48,44,48),17,28,42,2,0)
    g.torus((48,44,63),31,2.5,2,10)
    # Right-side bowl grip; opening runs front/back.
    g.roundbox((77,36,34),(94,52,62),5,7)
    g.roundbox((81,32,40),(91,56,56),2,0)
    # Shaft and three stout bent-wire whisk loops leave working clearance.
    g.cylinder((48,44,81),3,20,2,8)
    for a,b in [((39,44,81),(36,44,70)),((36,44,70),(48,44,64)),
                ((57,44,81),(60,44,70)),((60,44,70),(48,44,64)),
                ((48,35,81),(48,32,70)),((48,32,70),(48,44,64)),
                ((48,53,81),(48,56,70)),((48,56,70),(48,44,64))]:
        g.beam(a,b,2,7)
    g.cylinder((48,44,85),7,6,2,8)
    return Asset('stand_mixer','Stand mixer',g,.40/128,[
        'Sage tilt-head household mixer with open metal bowl, mechanical lever and stout wire whisk.',
        'Bowl and its handle opening, plus side working clearance, remain empty in saved native data.',
        'No half postprocess; all half cells use the shared conservative 2x reduction.',
    ])

def espresso_machine():
    g=Grid((128,104,128),PALETTE)
    for x in (20,108):
        for y in (20,86):
            g.roundbox((x-6,y-6,0),(x+6,y+6,10),3,6)
    g.roundbox((8,8,7),(120,98,24),6,3)
    g.roundbox((12,24,20),(116,96,118),10,2)
    # Deep open front cup bay under the control fascia.
    g.roundbox((23,0,28),(105,66,84),4,0)
    g.box((26,65,29),(102,68,81),8)
    g.roundbox((16,17,83),(112,29,113),6,1)
    g.box((21,15,84),(107,20,89),7)
    # Gauge and two selectors face -Y.
    g.cylinder((64,16,101),10,7,1,8)
    g.cylinder((64,11,101),7,4,1,10)
    g.beam((64,8,101),(68,8,106),1.5,6)
    for x in (35,93):
        g.cylinder((x,15,101),6,8,1,8)
        g.cylinder((x,10,101),4,4,1,6)
    g.cylinder((93,9,101),1.7,2,1,15)
    # Group, portafilter and a warm oak handgrip.
    g.roundbox((54,24,75),(74,51,89),4,8)
    g.cylinder((64,35,75),12,7,2,7)
    g.beam((65,31,76),(78,17,76),3,8)
    g.beam((76,19,76),(91,5,76),4.2,4)
    g.cylinder((64,35,69),3,8,2,8)
    # Steam wand is separated from the body and visibly bent downwards.
    g.beam((105,33,80),(103,19,70),2.5,7)
    g.beam((103,19,70),(103,19,44),2.5,7)
    g.beam((103,19,44),(96,16,37),2.5,7)
    g.cylinder((106,25,80),5,7,0,6)
    # Native slotted drip tray, with a hollow cup.
    g.roundbox((20,10,22),(108,60,27),3,8)
    for x in range(24,106,8):
        g.box((x,14,24),(x+4,56,29),7)
    g.cylinder((58,42,29),11,5,2,10)
    g.cone((58,42,40),10,12,22,2,10)
    g.cone((58,42,44),7,9,24,2,0)
    g.roundbox((68,36,33),(80,49,48),4,10)
    g.roundbox((71,33,37),(77,52,44),1.5,0)
    # Upper warming deck and perimeter rail.
    g.roundbox((20,31,115),(108,88,120),3,7)
    g.beam((24,37,123),(24,82,123),2,8)
    g.beam((104,37,123),(104,82,123),2,8)
    g.beam((24,82,123),(104,82,123),2,8)
    for x in (24,104):
        for y in (39,80):
            g.box((x-2,y-2,118),(x+2,y+2,124),8)
    g.roundbox((113,62,48),(119,87,101),3,9)
    g.box((118,69,68),(120,80,71),10)
    return Asset('espresso_machine','Espresso machine',g,.40/128,[
        'Domestic sage espresso machine with cream fascia, pressure gauge, portafilter, steam wand and slotted drip tray.',
        'The serving cup and front cup bay are actual hollow native volumes; reservoir glass is opaque.',
        'No half postprocess; nominal 0.40m maximum physical grid extent.',
    ])

def toaster():
    g=Grid((128,84,88),PALETTE)
    for x in (24,102):
        for y in (23,62):
            g.roundbox((x-6,y-5,0),(x+6,y+5,8),3,6)
    g.roundbox((8,10,5),(120,74,76),13,1)
    g.roundbox((10,10,7),(118,74,17),5,3)
    g.roundbox((16,18,68),(112,66,77),4,7)
    for y in (29,55):
        g.roundbox((23,y-7,39),(105,y+7,80),4,12)
        g.roundbox((26,y-4,42),(102,y+4,84),2,0)
    # One raised slice leaves the other long slot visibly empty.
    g.roundbox((32,51,56),(96,59,85),4,14)
    g.roundbox((36,50,60),(92,54,82),2,13)
    g.roundbox((36,56,60),(92,60,82),2,13)
    g.box((41,50,64),(44,51,72),14)
    g.box((80,50,69),(83,51,76),14)
    # Visible right-side spring lever and front browning controls.
    g.roundbox((117,38,22),(123,46,62),3,8)
    g.roundbox((120,34,40),(128,50,49),3,6)
    g.cylinder((91,9,30),8,7,1,7)
    g.cylinder((91,5,30),5,4,1,6)
    g.beam((91,3,30),(94,3,34),1.5,10)
    for x in (49,65):
        g.cylinder((x,8,30),3.5,6,1,8)
    g.cylinder((49,4,30),2,2,1,15)
    g.roundbox((24,7,14),(101,12,21),2,7)
    g.roundbox((54,4,15),(74,10,20),2,6)
    return Asset('toaster','Two-slot toaster',g,.31/128,[
        'Rounded cream toaster with two deep native slots, one raised toast slice, crumb tray, browning dial and side lift lever.',
        'Front slot and rear slot end remain genuinely empty at both resolutions.',
        'No half postprocess.',
    ])

def blender():
    g=Grid((96,96,128),PALETTE)
    g.roundbox((23,19,0),(74,74,9),6,6)
    g.roundbox((20,14,5),(76,78,43),11,2)
    g.roundbox((26,16,34),(70,73,46),5,1)
    g.cylinder((45,45,46),20,10,2,8)
    g.cylinder((45,45,50),21,5,2,7)
    # Tapered jug: opaque blue-gray shell around a real empty interior.
    g.cone((45,45,79),19,26,62,2,9)
    g.cone((45,45,82),15,22,60,2,0)
    g.torus((45,45,55),19,2,2,8)
    g.roundbox((67,37,57),(92,53,103),6,1)
    g.roundbox((73,33,64),(86,57,96),3,0)
    g.box((65,39,60),(73,51,66),1)
    g.box((67,39,94),(74,51,101),1)
    # Pour spout and simple measurement dashes on front face.
    g.roundbox((37,14,101),(53,25,112),3,9)
    g.box((41,14,106),(49,21,113),12)
    for z,width in ((67,8),(79,11),(91,8),(103,11)):
        y=22 if z<80 else 20
        g.box((38,y-1,z),(38+width,y+2,z+3),10)
    g.cylinder((45,45,113),28,8,2,1)
    g.torus((45,45,109),26,2,2,8)
    g.cylinder((45,45,121),10,9,2,3)
    g.cylinder((48,14,25),9,8,1,7)
    g.cylinder((48,9,25),6,4,1,6)
    g.beam((48,6,25),(51,6,29),1.5,10)
    g.cylinder((66,16,24),2.5,4,1,15)
    return Asset('blender','Countertop blender',g,.42/128,[
        'Sage motor base with a lidded tapered opaque blue-gray jug, cream handle, pour spout and capacity dashes.',
        'Jug shell has a real empty interior despite the intentionally opaque palette; handle loop is open.',
        'No half postprocess.',
    ])

def stock_pot():
    g=Grid((128,96,92),PALETTE)
    g.cylinder((64,48,10),29,8,2,8)
    g.cone((64,48,44),30,37,64,2,2)
    g.cone((64,48,49),26,33,60,2,7)
    g.cone((64,48,55),24,32,62,2,0)
    g.torus((64,48,76),35,2.5,2,10)
    pot_shell=g.data.copy()
    # Broad rectangular loops on either side; both holes pass through Z.
    g.roundbox((7,31,51),(35,65,66),5,1)
    g.roundbox((93,31,51),(121,65,66),5,1)
    g.roundbox((13,37,47),(30,59,70),3,0)
    g.roundbox((98,37,47),(115,59,70),3,0)
    g.box((31,39,51),(36,57,65),8)
    g.box((92,39,51),(97,57,65),8)
    # Preserve the continuous vessel wall where the grip cutouts meet it.
    # Handle openings must not punch small square holes into the pot side.
    shell_mask=pot_shell>0
    g.data[shell_mask]=pot_shell[shell_mask]
    # Subtle enamel foot and reinforcing side rivets.
    g.torus((64,48,15),30,2,2,3)
    for x in (50,78):
        g.cylinder((x,16,55),2.5,5,1,7)
    return Asset('stock_pot','Stock pot',g,.38/128,[
        'Open sage enamel stock pot with light metal inner wall, bright rim and paired cream loop handles.',
        'No lid obscures the native bowl cavity. Handle holes pass vertically through the handles.',
        'No half postprocess.',
    ])

def frying_pan():
    g=Grid((128,96,32),PALETTE)
    g.cone((48,48,14),33,40,20,2,8)
    g.cone((48,48,19),28,36,20,2,6)
    g.cone((48,48,25),27,35,24,2,0)
    g.torus((48,48,24),38,2,2,7)
    g.roundbox((80,40,12),(102,56,22),4,7)
    g.roundbox((94,37,12),(127,59,26),5,6)
    g.roundbox((98,40,23),(124,56,28),3,4)
    g.cylinder((119,48,20),4,32,2,0)
    for x in (84,92):
        g.cylinder((x,48,22),2,4,2,8)
    return Asset('frying_pan','Frying pan',g,.48/128,[
        'Low open nonstick pan with metal lip, riveted neck and charcoal handle with oak inset.',
        'Bowl and handle hanging hole are empty native volumes, including half size.',
        'No half postprocess; rim and handle are intentionally stout for small voxel readability.',
    ])

def cutting_board_knife():
    g=Grid((128,96,24),PALETTE)
    g.roundbox((4,8,0),(112,88,8),5,5)
    g.roundbox((104,33,0),(128,63,8),5,5)
    # Long-grain edge and restrained staggered oak strips.
    g.box((6,15,0),(110,81,2),4)
    for y in (28,49,70):
        g.box((10,y,6),(106,y+2,8),4)
    for x,y,length in ((17,21,29),(54,39,42),(25,61,37),(68,77,29)):
        g.box((x,y,7),(x+length,y+1,8),4)
    # Juice channel is a shallow native cut, with a wide flat prep area.
    outer=((g.x>=12)&(g.x<104)&(g.y>=16)&(g.y<80))
    inner=((g.x>=16)&(g.x<100)&(g.y>=20)&(g.y<76))
    g.data[outer & ~inner & (g.z>=6)&(g.z<8)]=0
    g.cylinder((118,48,4),5,16,2,0)
    # Chef knife resting on the board, with a pointed curved-edge blade.
    polygon_prism(g,[(18,24),(78,32),(76,49),(61,48),(38,39)],8,12,7)
    polygon_prism(g,[(18,24),(38,37),(62,45),(76,46),(76,49),(61,48),(38,39)],11,13,10)
    g.beam((78,34,13),(76,46,13),3,8)
    g.beam((82,40,14),(109,46,14),5,6)
    g.beam((84,40,18),(107,45,18),2,4)
    for x,y in ((88,41),(103,45)):
        g.cylinder((x,y,19),2,3,2,7)
    return Asset('cutting_board_knife','Cutting board and chef knife',g,.42/128,[
        'Light oak board with long-grain strips, shallow juice groove and open hanging tab; resting steel chef knife with riveted charcoal grip.',
        'Knife edge is exaggerated to survive native reduction. Board has no permanent presentation floor.',
        'No half postprocess.',
    ])

def make_assets():
    return [stand_mixer(),espresso_machine(),toaster(),blender(),stock_pot(),frying_pan(),cutting_board_knife()]

if __name__ == '__main__':
    # The old shared run_theme exports mesh files, so it is deliberately unused.
    from preview_pipeline import main
    main()
