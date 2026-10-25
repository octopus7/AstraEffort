"""Four original bakery assets, authored by main as real colored voxel grids."""
from pathlib import Path
import sys,json
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_tools'))
from voxelkit import Grid,Asset,reduce_half

P=[(0,0,0,0),(234,220,193),(197,177,145),(69,120,118),(43,78,80),(169,85,53),(122,60,41),(129,86,47),(207,154,78),(239,195,120),(49,52,54),(105,112,112),(172,179,174),(93,126,137),(244,211,134),(31,35,36),(245,238,219),(175,53,39),(90,135,64)]
def loaf(g,x,y,z,rx=6,ry=4):
    g.ellipsoid((x,y,z),(rx,ry,3.4),8)
    for dx in (-2,2):g.box((x+dx-1,y-2,z+2),(x+dx+1,y+2,z+3),9)

def shop():
    g=Grid((128,96,112),P)
    g.roundbox((4,13,0),(124,91,9),3,2)
    g.roundbox((10,25,8),(118,86,76),3,1)
    for z in range(14,76,9):
        g.box((10,24,z),(118,27,z+1),2)
        g.box((116,25,z),(119,86,z+1),2)
        for x in range(12+(z//9%2)*7,116,15):g.box((x,24,z),(x+1,27,z+9),2)
        for y in range(28+(z//9%2)*7,84,15):g.box((116,y,z),(119,y+1,z+9),2)
    g.box((14,29,13),(114,82,71),0)
    # Solid gable and a shallow tiled roof; the ridge is round and low.
    for x in range(6,122):
        top=101-int(abs(x-64)*.49)
        if 10<=x<118:g.box((x,25,71),(x+1,86,top),1)
        g.box((x,20,top),(x+1,91,top+4),5)
        for y in range(21,91,12):g.box((x,y,top+3),(x+1,y+2,top+5),6)
    g.roundbox((61,19,99),(67,92,106),2,5)
    # Open recessed display window, with two genuinely visible bread shelves.
    g.roundbox((15,22,18),(80,29,64),2,7)
    g.box((20,20,23),(75,39,60),0)
    g.box((20,38,22),(75,40,61),2)
    for z in (25,43):
        g.box((21,25,z),(74,39,z+3),7)
        for x in (29,46,63):loaf(g,x,29,z+6)
    # Plain separate door, small panes and practical handle.
    g.roundbox((86,22,10),(111,29,63),2,7)
    g.box((90,20,13),(107,25,59),3)
    g.box((93,19,39),(104,22,56),13)
    g.box((98,18,38),(100,21,57),7)
    g.box((91,18,46),(106,21,48),7)
    g.roundbox((102,17,27),(105,21,34),1,10)
    g.roundbox((84,5,0),(114,24,5),2,2)
    g.box((87,13,4),(111,24,9),1)
    # Sloped canvas awning and short bracket supports.
    for y in range(10,28):
        z=62+(y-10)//2;g.box((13,y,z),(81,y+1,z+3),3)
    for x in range(13,81,10):g.roundbox((x,9,60),(min(x+9,81),12,65),1,3)
    for x in (17,76):g.beam((x,12,61),(x,25,53),1.7,7)
    g.box((116,46,31),(121,72,55),7);g.box((119,49,34),(122,69,52),13)
    g.box((120,58,33),(123,61,53),1)
    g.box((87,61,91),(101,75,108),1)
    for z in (94,101):g.box((86,61,z),(102,75,z+2),2)
    g.roundbox((85,59,107),(103,77,112),1.5,5)
    g.box((91,65,104),(97,71,112),0)
    return Asset('bakery_shop','동네 빵집',g,.055,['Original bakery with a recessed open display and two bread shelves; other windows use opaque palette glazing.','Display aperture is a stylized open shopfront so the modeled bread remains visible without transparency.'])

def mixer():
    g=Grid((96,104,128),P)
    for x in (21,77):
        for y in (17,87):g.roundbox((x-5,y-5,0),(x+5,y+5,7),2,10)
    g.roundbox((14,8,6),(86,96,18),5,3)
    g.cylinder((42,37,25),13,17,2,11)
    # Deep genuinely empty mixing bowl, not a colored solid cylinder.
    g.ellipsoid((42,37,62),(31,31,31),12)
    g.box((8,3,70),(76,72,125),0)
    g.ellipsoid((42,37,63),(26,26,26),0)
    g.cylinder((42,37,91),26,52,2,0)
    g.torus((42,37,69),29.2,2.1,2,12)
    g.torus((75,37,53),7,1.8,0,11)
    for y in (31,43):g.beam((69,y,53),(75,y,53),2,12)
    g.roundbox((64,66,17),(87,93,107),6,3)
    g.roundbox((28,24,102),(89,94,123),8,3)
    g.roundbox((27,23,100),(89,94,108),3,1)
    g.cylinder((42,37,97),11,9,2,12)
    g.cylinder((42,37,87),4,13,2,11)
    points=[(42,37,83),(47,37,78),(51,37,71),(49,37,62),(42,37,57),(36,37,57)]
    for a,b in zip(points,points[1:]):g.beam(a,b,2.4,12)
    g.roundbox((72,63,65),(85,68,94),2,1)
    for z,c in ((86,18),(77,17),(68,10)):g.cylinder((78,62,z),2.5,3,1,c)
    g.cylinder((88,81,111),6,4,0,10)
    return Asset('dough_mixer','반죽 혼합기',g,.018,['Original floor mixer with an actual hollow bowl and curved dough hook.','Static mechanism; no ingredient or animation simulation.'])

def oven():
    g=Grid((128,96,112),P)
    g.roundbox((14,15,0),(114,84,45),3,2)
    for z in range(7,45,9):
        g.box((14,14,z),(114,17,z+1),1)
        g.box((112,15,z),(115,84,z+1),1)
    g.box((34,12,8),(95,66,36),0)
    for x,z in ((43,14),(57,14),(71,14),(85,14),(50,25),(64,25),(78,25)):
        g.cylinder((x,41,z),5,45,1,7);g.cylinder((x,17,z),3.5,2,1,8)
    g.roundbox((7,8,43),(121,90,49),3,1)
    dome=((g.x-64)/48)**2+((g.y-51)/37)**2+((g.z-51)/43)**2<=1
    g.data[dome&(g.z>=49)]=5
    g.data[dome&(g.z>=49)&((g.z.astype(int)%9)==0)]=6
    cavity=((g.x-64)/38)**2+((g.y-52)/28)**2+((g.z-52)/33)**2<=1
    g.data[cavity&(g.z>=50)]=0
    arch=((np.abs(g.x-64)<=32)&(g.z>=48)&(g.z<=69))|((((g.x-64)/32)**2+((g.z-69)/25)**2<=1)&(g.z>=69))
    g.data[arch&(g.y>=11)&(g.y<25)]=6
    opening=((np.abs(g.x-64)<=25)&(g.z>=51)&(g.z<=68))|((((g.x-64)/25)**2+((g.z-68)/18)**2<=1)&(g.z>=68))
    g.data[opening&(g.y>=8)&(g.y<56)]=0
    for x in (33,89):
        for z in (53,63):g.box((x,10,z),(x+6,13,z+7),5)
    g.roundbox((60,10,87),(68,25,94),1,1)
    g.box((37,20,49),(91,65,51),10)
    g.box((41,21,51),(87,49,53),11)
    for x in (48,60,72,83):loaf(g,x,29,56,4.5,8)
    g.box((81,61,80),(96,76,108),1)
    for z in (87,96,104):g.box((80,61,z),(97,76,z+2),2)
    g.roundbox((79,59,107),(98,78,112),1.5,5)
    g.box((85,65,99),(92,72,112),0)
    return Asset('bread_oven','벽돌 빵 화덕',g,.025,['Original domed brick oven with true open baking mouth, internal bread tray and lower firewood cubby.','No fire/smoke effects or heat simulation.'])

def van():
    g=Grid((80,128,84),P)
    g.roundbox((11,13,18),(69,119,28),3,10)
    g.roundbox((9,16,26),(71,119,42),4,3)
    g.roundbox((8,55,29),(72,122,79),6,3)
    g.roundbox((11,15,35),(69,61,70),6,1)
    g.roundbox((10,5,27),(70,34,44),4,1)
    g.box((13,14,43),(67,18,66),10)
    g.box((17,12,47),(63,16,63),13)
    g.box((39,11,46),(42,15,64),1)
    for x in (10,67):
        g.box((x,30,45),(x+4,53,64),10)
        g.box((x-1,33,48),(x+5,49,61),13)
        g.box((x,50,27),(x+4,52,44),2)
        g.box((x-1,45,40),(x+5,50,43),10)
    # Four wheel arches precede tire insertion, preserving actual clearance.
    for y in (29,98):
        for x in (9,71):g.cylinder((x,y,17),17,18,0,0)
    for y in (29,98):
        g.cylinder((40,y,16),4,66,0,11)
        for x in (9,71):
            g.cylinder((x,y,16),14,12,0,15)
            g.cylinder((x,y,16),9,13,0,11)
            g.cylinder((x,y,16),5,14,0,12)
            # Subtle sturdy tire tread blocks at every quadrant.
            for z in (3,27):g.box((x-6,y-4,z),(x+6,y+4,z+3),10)
    g.roundbox((6,2,21),(74,9,28),2,10)
    g.box((28,3,30),(52,6,39),10)
    for z in (32,37):g.box((29,2,z),(51,4,z+2),11)
    for x in (15,59):
        g.roundbox((x,2,31),(x+6,7,40),1,10)
        g.box((x+1,1,33),(x+5,3,38),14)
    for x in (3,71):
        g.box((x,25,48),(x+6,31,57),10)
        g.beam((x+3,29,48),(max(12,min(x+3,68)),33,48),1.6,11)
    g.box((13,120,33),(67,124,74),4)
    for x in (16,42):g.roundbox((x,122,35),(x+23,125,72),2,3)
    g.box((39,123,34),(42,126,73),4)
    for x in (17,64):
        for z in (42,65):g.roundbox((x-2,124,z),(x+2,127,z+5),1,10)
    for x in (36,44):g.box((x,124,48),(x+2,127,55),12)
    g.roundbox((6,121,20),(74,127,27),2,10)
    for x in (12,64):g.box((x,122,28),(x+4,125,34),17)
    return Asset('delivery_van','빵 배달 밴',g,.035,['Original four-wheel rounded delivery van with separate cab/cargo body and rear hinged doors.','Static opaque windows; rear door details are modeled but partly hidden by the common front camera.'])

def make_assets():return [shop(),mixer(),oven(),van()]

def feature_checks(assets):
    checks={
      'bakery_shop':{'air':[(45,25,38)],'solid':[(99,23,25),(30,29,31),(90,68,98)]},
      'dough_mixer':{'air':[(42,27,57),(42,37,72)],'solid':[(42,37,32),(77,78,70),(42,37,97),(49,37,71)]},
      'bread_oven':{'air':[(64,24,70),(60,22,34)],'solid':[(40,55,5),(64,51,92),(48,29,56)]},
      'delivery_van':{'air':[(40,28,8)],'solid':[(9,29,16),(71,29,16),(9,98,16),(71,98,16),(50,88,57)]}}
    results=[]
    for asset in assets:
        for size,g,s in [('large',asset.grid,1),('half',reduce_half(asset.grid),2)]:
            for kind,points in checks[asset.slug].items():
                for pt in points:
                    value=int(g.data[tuple(int(p//s) for p in pt)])
                    assert bool(value)==(kind=='solid'),(asset.slug,size,kind,pt,value)
                    results.append({'asset':asset.slug,'variant':size,'kind':kind,'point_large_coordinates':pt,'passed':True})
    return results

if __name__=='__main__':
    from blender_pipeline import run_theme
    root=Path(__file__).resolve().parent;assets=make_assets()
    (root/'palette.json').write_text(json.dumps({'colors':P,'style':'Ivory, muted teal, terracotta, bread/wood, graphite; original bakery palette.'},indent=2),encoding='utf-8')
    (root/'feature_validation.json').write_text(json.dumps(feature_checks(assets),indent=2),encoding='utf-8')
    run_theme(root,assets)
