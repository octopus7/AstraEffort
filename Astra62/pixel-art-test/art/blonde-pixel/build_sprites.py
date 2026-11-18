"""Hand-pixelled 64 px version of the approved blonde elf, on a one-second walk.

Only the joint positions come from the illustration rig. Every visible shape,
highlight, leaf, flower and strand below is drawn on the 64 px grid. Pillow is
the only dependency. Pass --preview-dir for enlarged contacts and a pose table.
"""

import argparse
from fractions import Fraction
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw


ART=Path(__file__).resolve().parent
OUT=ART.parent.parent/'assets'
COUNTS=(4,6,8,12)
TAU=math.tau

# Deliberate, shared ramps keep the eye, the leaf motifs and the white flowers
# distinct from the gold, skin and pale-pink ramps even on a green background.
PALETTE={
    'ink':'#3b3231','brown':'#69453a','leather':'#946044','tan':'#be8253',
    'umber':'#8e563d','ochre':'#b97349','honey':'#e8a160','blonde':'#fac480',
    'goldlight':'#ffe1a0','shine':'#fff2c9','metal':'#bd813f','gold':'#edb45b',
    'roseink':'#985b68','rose':'#c78091','pink':'#e8a7b5','blush':'#f8ced5',
    'pearl':'#fff0e3','white':'#fff8e8','skinrim':'#ae6e60','shade':'#dc9b84',
    'skin':'#f4c2a6','skinlit':'#ffe0bd','olivedeep':'#464737','oliveshade':'#5d6045',
    'olive':'#74794d','olivelit':'#959a5f','leafdark':'#527040','leaf':'#91a455',
    'lime':'#bcca68','limelit':'#e1e792','ivoryshade':'#b7989a','ivorymid':'#e1c3c2',
    'eyedark':'#355c45','eye':'#77a758','sole':'#4c3736','rear':'#c99694',
    'rearboot':'#795648','rearshaft':'#59453e',
}


def ip(p):
    return tuple(math.floor(n+.5) for n in p)


def unit(v):
    length=math.hypot(*v) or 1
    return v[0]/length,v[1]/length


def along(a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]; ux,uy=unit((dx,dy))
    return lambda pts:[(a[0]+t*dx+w*uy,a[1]+t*dy-w*ux) for t,w in pts]


def move(dx=0,dy=0):
    return lambda pts:[(x+dx,y+dy) for x,y in pts]


class Brush:
    def __init__(self,image,coordinates=None):
        self.draw=ImageDraw.Draw(image);self.coordinates=coordinates or (lambda x:x)

    def p(self,fill,pts,edge=None):
        self.draw.polygon([ip(x) for x in self.coordinates(pts)],fill=PALETTE[fill],
                          outline=PALETTE[edge] if edge else None)

    def l(self,fill,pts,width=1):
        self.draw.line([ip(x) for x in self.coordinates(pts)],fill=PALETTE[fill],width=width)

    def d(self,fill,*pts):
        self.draw.point([ip(x) for x in self.coordinates(pts)],fill=PALETTE[fill])


def track(keys,t):
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if t<=b:
            return x+(y-x)*(t-a)/(b-a)
    return keys[-1][1]


ANGLE=[(0,-24),(.09,-4),(.24,0),(.36,5),(.44,15),(.50,25),(.58,35),
       (.66,29),(.75,9),(.84,-9),(.925,-20),(1,-24)]
LIFT=[(0,0),(.5,0),(.58,1.7),(.66,4.2),(.75,5.0),(.84,4.5),(.925,2.4),(1,0)]
BOB=[(0,0),(.085,1),(.16,.55),(.24,-.7),(.32,-1),(.42,-.7),(.5,0)]
SHOE=[(-2.2,-1.1),(-.9,-2),(1,-1.65),(2.4,.1),(3.6,.8),(5.6,.45),
      (6.2,1.2),(6.1,2.45),(4.9,3.0),(2,3.35),(.4,3.55),(-.3,4.05),(-2.3,3.8)]


def trail(phase,kind):
    if kind=='hair':
        def warp(pts):
            result=[]
            for x,y in pts:
                free=min(1,max(0,(33-x)/18))*min(1,max(0,(y-10)/7))
                result.append((x+free*.85*math.sin(TAU*phase-.55),
                               y+free*1.25*math.sin(TAU*phase-.8)))
            return result
    else:
        def warp(pts):
            result=[]
            for x,y in pts:
                free=min(1,max(0,(37-x)/17))*min(1,max(0,(y-23)/11))
                result.append((x+free*1.15*math.sin(TAU*phase-1.05),
                               y+free*1.4*math.sin(TAU*phase-.85)))
            return result
    return warp


def flutter(image,phase,bob,kind):
    deform=trail(phase,kind)
    return Brush(image,lambda pts:[(x,y+bob) for x,y in deform(pts)])


def back_cape(image,phase,bob):
    b=flutter(image,phase,bob,'cape')
    b.p('rose',[(36,21),(37,31),(36,36),(33,39),(31,40),(30,40),(29,41),
        (27,40),(26,41),(24,40),(23,40),(21,39),(20,40),(17,37),(15,36),
        (13,35),(13,33),(21,31),(28,27)],'roseink')
    b.p('blush',[(16,34),(21,33),(26,33),(32,34),(34,35),(32,38),(31,39),
        (30,39),(29,40),(28,39),(27,40),(25,39),(24,40),(22,39),(20,39),
        (18,37),(16,36)])
    b.l('pink',[(23,38),(24,39),(25,39)]);b.d('pearl',(27,39),(30,38),(18,36))
    b.p('olive',[(36,20),(37,23),(36,27),(36,32),(36,35),(34,37),(31,39),
        (27,39),(24,38),(22,39),(19,42),(18,43),(17,41),(16,37),(16,35),
        (14,35),(12,37),(10,39),(9,40),(9,37),(10,35),(13,32),(17,31),
        (21,30),(25,28),(28,25),(33,22)],'olivedeep')
    b.p('oliveshade',[(35,23),(34,27),(32,31),(31,34),(32,36),(34,36),
        (31,38),(28,38),(25,37),(24,37),(23,36),(27,31),(31,27)])
    b.p('olivelit',[(32,23),(29,27),(24,30),(20,32),(15,33),(13,35),
        (11,36),(12,34),(15,32),(21,30),(26,28)])
    b.p('gold',[(25,28),(22,30),(17,31),(14,32),(11,34),(9,37),(9,40),
        (10,38),(12,36),(15,34),(19,32),(22,31)],'metal')
    b.l('goldlight',[(10,37),(11,35),(14,33),(17,32)]);b.d('shine',(13,34),(16,32))
    b.l('gold',[(17,37),(18,41),(18,42),(21,40),(23,39)])
    b.l('metal',[(19,39),(19,37),(21,36)]);b.l('gold',[(19,38),(20,37),(21,37)])
    b.d('goldlight',(19,40),(21,35),(22,36));b.l('gold',[(25,37),(28,38),(31,38),(33,37)])


def hair_tail(image,phase,bob):
    b=flutter(image,phase,bob,'hair')
    b.p('ochre',[(31,10),(35,11),(35,15),(33,19),(30,21),(26,23),(23,24),
        (20,24),(17,23),(15,23),(13,25),(13,27),(14,28),(16,27),(15,29),
        (13,30),(11,29),(9,27),(9,24),(10,22),(13,20),(12,20),(12,18),
        (13,16),(16,15),(20,15),(22,16),(25,16),(28,15),(30,13)],'umber')
    b.p('honey',[(31,12),(34,12),(34,15),(32,18),(29,20),(26,21),(23,21),
        (21,20),(18,20),(16,21),(14,22),(12,24),(12,27),(13,29),(11,28),
        (10,26),(10,24),(12,22),(15,20),(17,19),(21,18),(25,18),(28,16)])
    b.p('blonde',[(30,13),(32,11),(34,12),(33,15),(30,18),(27,20),(24,20),
        (21,19),(18,18),(16,18),(13,19),(14,17),(16,16),(19,16),(22,17),
        (25,17),(28,16)])
    b.p('goldlight',[(14,17),(17,15.8),(19,16),(21,17),(24,17),(26,16.5),
        (24,18),(22,18),(19,17),(16,17),(14,18)])
    b.l('shine',[(16,16),(18,16),(20,17)]);b.l('goldlight',[(27,17),(29,16),(31,14)])
    b.p('blonde',[(32,17),(31,19),(28,22),(25,24),(22,25),(18,25),(16,24),
        (14,24),(12,26),(12,27),(11,27),(10,25),(11,23),(13,21),(16,20),
        (19,20),(22,21),(25,21),(29,20)])
    b.p('honey',[(32,18),(31,20),(28,22),(24,24),(21,24),(18,23),
        (16,23),(18,22),(21,22),(25,23),(29,21)])
    b.l('goldlight',[(11,24),(13,22),(16,21),(18,21)]);b.d('shine',(14,21),(16,20))
    b.l('goldlight',[(11,26),(11,27),(13,29)]);b.d('ochre',(14,29))


def neck_and_head(image,bob):
    b=Brush(image,move(0,bob))
    # Nape and profile under the separately clustered fringe.
    b.p('honey',[(33,10),(35,8),(38,7),(40,8),(42,8),(43,10),(44,11),(43,13),
        (42,14),(41,15),(39,17),(37,19),(35,20),(36,18),(33,19),
        (34,17),(31,18),(32,16),(30,17),(31,14)],'umber')
    b.p('ochre',[(32,14),(37,12),(39,14),(38,17),(36,18),(33,18),(35,16),
        (32,17),(34,15),(31,16)])
    b.p('shade',[(37,13),(39,12),(41,11),(42,12),(42,14),(43,15),(43,16),
        (42,16),(42,17),(41,18),(40,19),(38,19),(37,20),(36,19),(37,17),(35,16)],'skinrim')
    b.p('skinlit',[(38,13),(41,12),(41,14),(42,15),(42,16),(41,16),
        (41,17),(40,18),(38,18),(37,17),(37,15)])
    b.d('skin',(41,17),(38,17),(37,18));b.d('skinlit',(42,15));b.d('brown',(43,16))
    b.l('skinrim',[(39,19),(40,19)]);b.d('skin',(41,18))
    # Sharp swept ear, warm rose interior and pale upper ridge.
    b.p('roseink',[(30,13),(32,13),(35,14),(37,14),(36,16),(35,17),(33,16),(31,15)])
    b.p('pink',[(30,13),(32,14),(35,14),(36,15),(35,16),(33,15)])
    b.l('blush',[(30,13),(32,13),(34,14)]);b.d('rose',(34,15));b.d('gold',(35,17))
    b.p('blonde',[(32,11),(33,9),(35,8),(37,7),(40,7),(42,8),(43,10),
        (44,11),(44,12),(43,13),(43,11),(42,12),(40,13),(39,13),(38,14),
        (37,16),(37,17),(38,18),(36,18),(35,17),(35,15),(36,13),(34,14),(33,14)],'umber')
    b.p('honey',[(33,11),(35,9),(37,8),(40,8),(41,9),(39,10),(37,12),
        (35,14),(34,13),(35,12),(33,13)])
    b.p('blonde',[(35,10),(37,8),(40,8),(42,9),(43,11),(42,11),(41,10),
        (40,12),(37,13),(36,16),(36,13),(37,11)])
    b.l('goldlight',[(35,10),(37,9),(39,8)]);b.l('shine',[(37,8),(39,8)])
    b.l('goldlight',[(40,9),(39,11),(37,13)]);b.d('goldlight',(42,10),(36,16))
    # A four-pixel eye group at native resolution keeps the expression steady.
    b.l('brown',[(39,13),(40,13),(41,13)]);b.d('ivorymid',(38,14));b.d('pearl',(39,14))
    b.d('eyedark',(40,14));b.d('ink',(41,14));b.d('eye',(40,15));b.d('skin',(41,15))
    # Tall ribbon, its two loops and folded tails.
    b.p('pink',[(33,9),(33,7),(34,5),(35,3),(36,4),(37,6),(37,8),
        (36,9),(34,11),(32,11)],'roseink')
    b.p('blush',[(34,8),(34,6),(35,4),(36,5),(36,7),(35,9)])
    b.l('pearl',[(35,4),(36,5),(36,6)]);b.d('rose',(34,9),(35,8))
    b.p('pink',[(33,10),(32,11),(30,10),(28,10),(27,9),(26,8),(25,6),(27,5),
        (29,5),(31,6),(33,8),(34,9),(34,10)],'roseink')
    b.p('blush',[(26,6),(28,6),(30,6),(32,8),(33,9),(31,9),(29,8),(28,9),(27,8)])
    b.l('pearl',[(26,6),(28,6),(30,7)]);b.l('rose',[(29,8),(31,9),(32,10)])
    b.p('pink',[(33,9),(33,11),(31,13),(30,15),(29,16),(29,14),(27,14),
        (29,12),(26,13),(24,13),(23,14),(23,12),(22,11),(24,11),(26,12),
        (28,11),(30,10)],'roseink')
    b.l('blush',[(23,11),(25,12),(27,12),(29,11)]);b.l('pearl',[(30,13),(31,12)])
    b.d('rose',(29,14),(32,10));b.d('blush',(29,15))
    b.p('leafdark',[(33,9),(36,9),(36,11),(35,13),(33,14),(32,12)])
    b.d('limelit',(35,9),(36,11));b.d('pearl',(32,10),(34,9),(34,11),(33,11),(36,12))
    b.d('white',(33,9),(34,10),(32,11),(35,11),(34,12),(35,13));b.d('gold',(33,10),(35,12))
    # The ear crosses in front of the ribbon tails. Its rose underside and
    # long pale ridge form a separate silhouette from the golden side lock.
    b.p('roseink',[(29,13),(31,13),(34,14),(36,14),(36,16),(35,17),(33,16),(31,15)])
    b.p('pink',[(30,13),(32,14),(34,14),(35,15),(35,16),(33,15)])
    b.l('blush',[(29,13),(31,13),(34,14)]);b.d('rose',(33,15),(34,15));b.d('gold',(35,16))
    b.l('honey',[(36,14),(36,16),(37,17)]);b.d('goldlight',(36,16))
    b.d('white',(39,14));b.d('eye',(40,14));b.d('eyedark',(41,14));b.d('ink',(41,13))
    b.d('skinlit',(41,15),(42,15));b.d('skin',(40,16),(39,17))


def torso(image,bob,phase):
    b=Brush(image,move(0,bob)); drag=round(.75*math.sin(TAU*phase-.45))
    b.p('olive',[(36,18),(38,19),(39,21),(41,22),(42,24),(41,26),(41,29),
        (42,31),(43,32),(44,33),(42,35),(33,35),(32,33),(34,30),(34,27),
        (33,25),(33,21)],'olivedeep')
    b.p('ivorymid',[(36,19),(38,20),(40,21),(41,22),(42,24),(41,25),
        (39,26),(36,25),(35,24),(35,21)],'ivoryshade')
    b.p('pearl',[(37,20),(39,21),(40,22),(40,24),(39,25),(37,24),(36,22)])
    b.l('white',[(39,21),(40,22),(41,23)]);b.d('ivorymid',(38,23),(40,24))
    b.p('oliveshade',[(35,25),(38,26),(41,25),(41,30),(38,31),(34,30)],'olivedeep')
    b.l('olive',[(36,26),(36,29)]);b.l('gold',[(40,25),(40,28)]);b.d('goldlight',(41,26),(40,28))
    b.p('rose',[(35,29),(40,29),(42,31),(43,32),(45,34),(46,36),
        (46,37),(45,38),(44,38),(43,39),(42,39),(41,38),(40,39),(39,40),
        (38,39),(37,40),(36,39),(35,39),(34,40),(33,39),(32,39),(32,38),
        (31,38),(31,36),(33,33)],'roseink')
    b.p('blush',[(32,36),(34,35),(43,35),(45,36),(45,37),(44,38),
        (42,38),(41,37),(40,39),(39,39),(38,38),(37,39),(36,38),
        (35,39),(34,38),(33,39),(32,38)])
    b.d('pearl',(33,37),(35,38),(38,38),(41,38),(44,37));b.d('pink',(34,38),(37,38),(43,38))
    b.p('lime',[(35,30),(40,30),(42,31),(43,33),(44,34),(46,36),
        (44,37),(42,37),(41,36),(40,37),(38,37),(36,36),(35,37),(33,37),
        (31+drag,36),(33,34)],'leafdark')
    b.p('limelit',[(35,32),(39,31),(42,33),(44,35),(43,36),(41,35),
        (39,36),(37,35),(35,36),(33,35)])
    b.l('lime',[(35,32),(34,34),(33,35)]);b.l('lime',[(38,32),(38,35)])
    # Individual dark-green leaf emblems, large enough for the 1× preview.
    for x,y in [(34,35),(38,35),(42,35)]:
        b.d('leafdark',(x-1,y-1),(x,y),(x+1,y-1));b.d('leaf',(x-1,y),(x,y))
    b.l('leafdark',[(40,35),(41,34)]);b.d('limelit',(36,36),(44,35))
    b.p('ivorymid',[(35,29),(40,29),(41,30),(42,31),(44,33),(42,33),(41,32),
        (39,33),(38,32),(37,33),(35,32),(33,33),(32,33),(34,30)],'metal')
    b.l('pearl',[(33,32),(35,31),(36,32),(37,32),(38,31)]);b.l('goldlight',[(39,31),(40,30),(41,31),(43,32)])
    b.p('leather',[(34,28),(37,28),(40,27),(41,28),(40,29),(37,30),(34,30)],'brown')
    b.l('tan',[(35,28),(37,28)]);b.d('goldlight',(39,28),(40,28));b.d('brown',(40,29))
    b.p('leather',[(34,28),(36,27),(37,28),(36,30),(35,31),(33,31)],'brown')
    b.d('gold',(35,29));b.d('tan',(34,29))


def quiver(image,bob,phase):
    dx=.55*math.sin(TAU*phase-.3)
    b=Brush(image,lambda pts:[(x+dx*min(1,max(0,(35-y)/9)),y+bob) for x,y in pts])
    for x,y in [(27,27),(28.5,26),(30,26.5),(31,26)]:
        b.l('brown',[(x,y),(x+2,32)])
        b.p('pink',[(x-1,y-1),(x,y),(x,y-1),(x+1,y),(x+1,y+2),(x,y+1)],'roseink')
        b.l('blush',[(x-1,y-1),(x,y+1)]);b.d('pearl',(x,y))
    b.p('leather',[(28,31),(32,29),(33,30),(34,34),(33,36),(32,37),(30,36)],'brown')
    b.l('tan',[(29,31),(32,30)]);b.l('tan',[(30,33),(31,35)]);b.d('gold',(30,32),(33,35))


def mantle(image,phase,bob):
    b=Brush(image,move(0,bob)); d=round(.55*math.sin(TAU*phase-.6))
    b.p('olive',[(32,20),(34,18),(37,18),(39,20),(40,20),(41,22),(42,23),
        (41,23),(39,22),(37,23),(34,25),(31,26),(28,26),(26+d,26),(25+d,25),
        (28,24),(30,23),(32,21)],'olivedeep')
    b.p('oliveshade',[(32,21),(34,19),(36,19),(38,20),(36,20),(34,21),(33,22)])
    b.l('olivelit',[(27+d,25),(30,24),(33,23),(35,21)]);b.l('gold',[(26+d,25),(28,26),(31,26),(34,25),(37,23),(39,21)])
    b.d('goldlight',(28,25),(32,25),(35,23));b.d('metal',(30,24),(34,22))
    b.l('olivelit',[(34,19),(36,19)]);b.l('gold',[(38,20),(39,21),(41,22)])
    b.d('goldlight',(39,20),(40,21));b.d('metal',(40,22))


def shape_foot(ankle,angle,points):
    c,s=math.cos(angle),math.sin(angle)
    return [(ankle[0]+x*c-y*s,ankle[1]+x*s+y*c) for x,y in points]


def leg(image,nodes,phase,near):
    hip,knee,ankle=nodes[:3];angle=math.radians(track(ANGLE,phase))
    lift=track(LIFT,phase)
    sole=max(y for _,y in shape_foot((0,0),angle,SHOE))
    ankle=(ankle[0],59-lift-sole)
    upper=along(hip,knee);lower=along(knee,ankle)
    limb=Brush(image)
    upper_face=upper([(-.15,-2.45),(-.12,2.8),(.47,2.75),(.84,2.15),(1.0,1.8)])
    lower_right=lower([(.02,1.8),(.32,1.85),(.57,1.45),(.86,1.2)])
    lower_left=lower([(.87,-1.2),(.55,-1.5),(.25,-1.8),(0,-1.8)])
    upper_back=upper([(.82,-1.85),(.49,-2.3),(.20,-2.65)])
    limb.p('skin' if near else 'shade',upper_face+lower_right+lower_left+upper_back,'skinrim' if near else 'roseink')
    limb.p('skinlit' if near else 'skin',upper([(.12,-.5),(.13,1.35),(.49,1.65),(.89,1.2),
         (.90,.15),(.48,-.75)]))
    limb.l('skinlit' if near else 'skin',lower([(.02,.80),(.3,.85),(.53,.50)]))
    limb.d('shade' if near else 'rear',*upper([(.88,-.85)]))
    boot=Brush(image,lower);base='leather' if near else 'rearboot';shadow='brown' if near else 'rearshaft'
    boot.p(base,[(.48,-2.05),(.45,2.25),(.64,2.0),(.91,1.65),(1.1,1.8),
        (1.1,-1.7),(.82,-1.65),(.68,-2.1)],'sole')
    boot.l('tan' if near else 'leather',[(.64,1.05),(.88,.85)]);boot.l(shadow,[(.70,-1),(.89,-.85)])
    shoe=Brush(image,lambda pts:shape_foot(ankle,angle,pts))
    shoe.p(base,SHOE,'sole');shoe.p('tan' if near else 'leather',[(-1.4,-.4),(.35,-.9),(2,.4),
        (3.5,1.1),(5.65,1),(5.65,1.8),(3.2,2),(1.5,1.5),(-.2,1.1)])
    shoe.l(shadow,[(-1.9,2.55),(.35,2.75),(1.9,2.65)]);shoe.d('gold' if near else 'tan',(0,-.65))
    # Pale bow loops are drawn around the boot shaft rather than on the foot.
    bx,by=lower([(.48,.1)])[0];r=Brush(image,move(bx,by))
    r.p('pink',[(-3,-1),(-3,-2),(-2,-2),(0,-.5),(1,-1),(2,-2),(3,-2),
        (3,0),(2,1),(1,1),(2,2),(1,2),(0,1),(-1,2),(-2,2),(-1,1),(-3,1)],'roseink')
    r.l('blush',[(-2,-1),(-1,-1),(0,0)]);r.l('pearl' if near else 'blush',[(1,0),(2,-1),(3,-1)])
    r.d('pearl',(-2,-1));r.d('white' if near else 'pearl',(2,-1));r.d('gold',(0,0))
    r.d('pink',(-1,1),(1,1));r.d('blush',(-2,2),(1,2))
    return ankle


def flower(b,x,y,large):
    if large:
        b.p('leafdark',[(x-3,y+2),(x-2,y),(x-3,y-1),(x-1,y-1),(x-1,y-3),
            (x+1,y-2),(x+2,y-3),(x+2,y-1),(x+3,y),(x+2,y+1),(x+2,y+3),(x,y+2),(x-1,y+3)])
        b.d('leaf',(x-2,y+1),(x+1,y-2),(x+2,y+2));b.d('limelit',(x-2,y),(x+2,y-1))
        b.d('ivorymid',(x-1,y+1),(x+1,y+1));b.d('white',(x,y-1),(x-1,y),(x+1,y),(x,y+1));b.d('gold',(x,y))
    else:
        b.p('leafdark',[(x-2,y+1),(x-1,y-1),(x,y-1),(x+1,y-2),(x+2,y-1),(x+1,y),(x+1,y+2)])
        b.d('limelit',(x-1,y-1),(x+1,y+1));b.d('pearl',(x,y-1),(x-1,y),(x+1,y));b.d('gold',(x,y))


def bow(image,grip,phase):
    theta=.055*math.cos(TAU*phase-.14)
    b=Brush(image,lambda pts:shape_foot(grip,theta,pts))
    b.l('tan',[(1,-15),(-8,10)])
    wood=[(3,-16),(2,-16),(1,-15),(0,-14),(0,-13),(2,-11),(3,-9),(4,-7),
          (4,-5),(3,-3),(1,-1),(0,0),(-.8,2),(-2,4),(-3,6),(-5,7),
          (-7,8),(-8,9),(-8,10),(-7,10)]
    b.l('umber',wood,2);b.l('gold',wood);b.l('goldlight',[(2,-16),(1,-15),(0,-14)])
    b.l('metal',[(1,-12),(3,-9),(4,-7)]);b.d('goldlight',(3,-9),(4,-6),(-6,8))
    b.l('leather',[(1,-1),(0,1),(-1,2)],2);b.d('tan',(0,0),(-1,1))
    flower(b,4,-6,True);flower(b,-3.5,5.5,False)


def arm(image,nodes,phase,near):
    sh,el,wr=nodes[3:];b=Brush(image);upper=along(sh,el);lower=along(el,wr)
    b.p('skin',upper([(-.05,-1.6),(-.03,1.7),(.64,1.6),(1.08,1.30),(1.10,-1.3),(.52,-1.6)]),'skinrim')
    b.p('skin',lower([(-.11,-1.45),(-.12,1.42),(.52,1.4),(.96,1.05),
        (1.06,-1.05),(.57,-1.3)]),'skinrim')
    b.l('skinlit',lower([(.06,.55),(.45,.5),(.73,.4)]))
    sleeve=Brush(image,upper)
    sleeve.p('ivorymid',[(-.34,-1.6),(-.19,1.7),(.21,2.35),(.52,1.75),(.63,1.7),
         (.62,.25),(.76,-.7),(.57,-1.7),(.41,-2.2),(.1,-2.3)],'roseink')
    sleeve.p('pearl',[(-.21,-1),(-.11,1.4),(.16,1.8),(.38,1.3),(.46,.6),(.31,-.4),(.13,-1.5)])
    sleeve.l('pink',[(.52,-1.35),(.56,-.2),(.48,.9)]);sleeve.d('white',(.08,.6))
    cuff=Brush(image,lower);cuff.p('olive',[(.68,-1.45),(.67,1.55),(.97,1.32),(1.01,-1.3)],'metal')
    cuff.l('goldlight',[(.7,-.8),(.70,.8)]);cuff.d('leafdark',(.86,0))
    if near:
        dx,dy=unit((wr[0]-el[0],wr[1]-el[1]));wx,wy=wr
        hand=along((wx,wy),(wx+dx*2.6,wy+dy*2.8))
        b.p('skin',hand([(-.1,-1),(-.16,.9),(.38,1.35),(.74,1.05),(.74,.65),
            (1.12,.54),(1.15,-.32),(.85,-.75),(.74,-1.15),(.35,-1.25)]),'skinrim')
        b.l('skinlit',hand([(.12,.45),(.50,.65)]));b.d('skin',*hand([(.86,.20)]))
    else:
        dx,dy=unit((wr[0]-el[0],wr[1]-el[1]));grip=(wr[0]+dx*1.8,wr[1]+dy*1.8)
        bow(image,grip,phase);h=Brush(image,move(*grip))
        h.p('skin',[(-1.7,-.5),(-.7,-1.3),(.9,-1),(1.45,-.1),(1.20,1),(.1,1.65),(-1.3,.9)],'skinrim')
        h.l('skinlit',[(-.75,-.45),(.75,-.45)]);h.d('skin',(.65,1))


def sprite(pose,phase):
    p=float(phase);bob=round(track(BOB,p%.5));img=Image.new('RGBA',(64,64))
    rear=pose[1];front=pose[0]
    back_cape(img,p,bob);arm(img,rear,p,False)
    far_ankle=leg(img,rear,(p+.5)%1,False);near_ankle=leg(img,front,p,True)
    hair_tail(img,p,bob);torso(img,bob,p);quiver(img,bob,p)
    arm(img,front,p,True);mantle(img,p,bob);neck_and_head(img,bob)
    return img,{'near':{'shoulder':front[3],'wrist':front[5],'hip':front[0],'ankle':near_ankle},
                'far':{'shoulder':rear[3],'wrist':rear[5],'hip':rear[0],'ankle':far_ankle}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preview-dir',type=Path)
    args=parser.parse_args();poses=json.loads((ART/'pose-keys.json').read_text(encoding='utf8'))
    frames={};joints={}
    for key,pose in poses.items():
        phase=Fraction(key);frames[phase],joints[key]=sprite(pose,phase)
    for count in COUNTS:
        strip=Image.new('RGBA',(64*count,64))
        for i in range(count):
            strip.paste(frames[Fraction(i,count)],(i*64,0))
        strip.save(OUT/f'blonde-pixel-walk-{count:02d}.png',optimize=True)
    if args.preview_dir:
        folder=args.preview_dir;folder.mkdir(parents=True,exist_ok=True)
        for count,cols,zoom in [(4,4,4),(12,6,3)]:
            proof=Image.new('RGBA',(cols*64,count//cols*64))
            for i in range(count):
                b=Image.new('RGBA',(64,64),'#829688' if i%2 else '#b0baa2')
                b.alpha_composite(frames[Fraction(i,count)]);proof.paste(b,(i%cols*64,i//cols*64))
            proof.resize((proof.width*zoom,proof.height*zoom),Image.Resampling.NEAREST).convert('RGB').save(folder/f'walk-{count:02d}-proof.png')
        b=Image.new('RGBA',(64,64),'#8ba194');b.alpha_composite(frames[Fraction(0)])
        b.resize((384,384),Image.Resampling.NEAREST).convert('RGB').save(folder/'contact.png')
        (folder/'joint-coordinates.json').write_text(json.dumps(joints,indent=2),encoding='utf8')


if __name__=='__main__':
    main()
