"""Hand-pixelled 64 px version of the approved blonde elf, on a one-second walk.

The illustration rig supplies the joints, and the shared stride supplies
independent heel and toe angles. The boot, cloth, flowers and hair are drawn
on the 64 px grid. Pass --preview-dir for joint positions, transparent limbs
and enlarged pose sheets. Pillow is the only external dependency.
"""

import argparse
from dataclasses import dataclass
from fractions import Fraction
import json
import math
from pathlib import Path
import sys

from PIL import Image, ImageDraw


ART=Path(__file__).resolve().parent
OUT=ART.parent.parent/'assets'
sys.path.insert(0,str(ART.parent))
from walk_cycle import body_drop, sample_foot

COUNTS=(4,6,8,12)
TAU=math.tau
SOURCE_SCALE=.542/8
FLOOR=59

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


def clamp(value):
    return min(1.,max(0.,value))


def turn(point,angle):
    x,y=point
    c,s=math.cos(angle),math.sin(angle)
    return x*c-y*s,x*s+y*c


def offset(a,b):
    return a[0]+b[0],a[1]+b[1]


def torso_points(phase,bob,points):
    stride=TAU*phase
    pelvis=math.cos(stride-.12)
    transfer=math.cos(2*stride-.82)
    result=[]
    for x,y in points:
        hip=clamp((y-18)/12)
        hem=clamp((y-29)/10)
        side=max(-1.,min(1.,(x-38)/7))
        dx=(1.44*hip-.75)*pelvis+hem*(1.05*math.sin(stride-.72)+1.05*side*transfer)
        dy=bob+hem*(.80*side*math.sin(stride-.50)-.65*transfer)
        result.append((x+dx,y+dy))
    return result


def trail(phase,kind):
    if kind=='hair':
        def warp(pts):
            result=[]
            for x,y in pts:
                free=min(1,max(0,(33-x)/18))*min(1,max(0,(y-10)/7))
                rest=.28*math.cos(TAU*phase)
                result.append((x-rest+free*1.40*math.sin(TAU*phase-.45-.45*free),
                               y+free*(1.8*math.sin(TAU*phase-.48-.55*free)+.36*math.cos(2*TAU*phase))))
            return result
    else:
        def warp(pts):
            result=[]
            for x,y in pts:
                free=min(1,max(0,(37-x)/17))*min(1,max(0,(y-23)/11))
                delay=.50+.72*free
                result.append((x-.5*(1-free)*math.cos(TAU*phase)+free*2.20*math.sin(TAU*phase-delay),
                               y+free*(2.25*math.sin(TAU*phase-delay)+.54*math.sin(2*TAU*phase-.68))))
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


def neck_and_head(image,bob,phase):
    stride=TAU*phase
    shift=-.28*math.cos(stride)
    head=move(shift,.84*bob)
    b=Brush(image,head)
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
    def ribbon(points):
        result=[]
        for x,y in points:
            tip=clamp((33-x)/9)*clamp((y-6)/6)
            loop=clamp((10-y)/7)
            dx=tip*.95*math.sin(stride-.75)+loop*.40*math.sin(stride-.52)
            dy=tip*1.35*math.sin(stride-1.02)+loop*.43*math.cos(2*stride-.76)
            result.append((x+shift+dx,y+.84*bob+dy))
        return result
    b=Brush(image,ribbon)
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
    b=Brush(image,head)
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
    b=Brush(image,lambda points:torso_points(phase,bob,points))
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
        (31,36),(33,34)],'leafdark')
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
    stride=TAU*phase
    dx=.68*math.cos(stride-.1)
    b=Brush(image,lambda pts:[(x+dx+.88*math.sin(stride-.56)*clamp((35-y)/9),
                              y+bob+.50*math.sin(2*stride-.72)*clamp((35-y)/9)) for x,y in pts])
    for x,y in [(27,27),(28.5,26),(30,26.5),(31,26)]:
        b.l('brown',[(x,y),(x+2,32)])
        b.p('pink',[(x-1,y-1),(x,y),(x,y-1),(x+1,y),(x+1,y+2),(x,y+1)],'roseink')
        b.l('blush',[(x-1,y-1),(x,y+1)]);b.d('pearl',(x,y))
    b.p('leather',[(28,31),(32,29),(33,30),(34,34),(33,36),(32,37),(30,36)],'brown')
    b.l('tan',[(29,31),(32,30)]);b.l('tan',[(30,33),(31,35)]);b.d('gold',(30,32),(33,35))


def mantle(image,phase,bob):
    stride=TAU*phase
    def shoulder(points):
        return [(x-.61*math.cos(stride)+.65*clamp((38-x)/12)*math.sin(stride-.86),
                 y+bob+.75*clamp((38-x)/12)*math.sin(2*stride-.75)) for x,y in points]
    b=Brush(image,shoulder); d=.36*math.sin(stride-.78)
    b.p('olive',[(32,20),(34,18),(37,18),(39,20),(40,20),(41,22),(42,23),
        (41,23),(39,22),(37,23),(34,25),(31,26),(28,26),(26+d,26),(25+d,25),
        (28,24),(30,23),(32,21)],'olivedeep')
    b.p('oliveshade',[(32,21),(34,19),(36,19),(38,20),(36,20),(34,21),(33,22)])
    b.l('olivelit',[(27+d,25),(30,24),(33,23),(35,21)]);b.l('gold',[(26+d,25),(28,26),(31,26),(34,25),(37,23),(39,21)])
    b.d('goldlight',(28,25),(32,25),(35,23));b.d('metal',(30,24),(34,22))
    b.l('olivelit',[(34,19),(36,19)]);b.l('gold',[(38,20),(39,21),(41,22)])
    b.d('goldlight',(39,20),(40,21));b.d('metal',(40,22))


@dataclass(frozen=True)
class BootPose:
    heel: tuple
    ball: tuple
    ankle: tuple
    rear_pitch: float
    toe_pitch: float
    toe_length: float
    flex: float
    compression: float

    def back(self,x,y):
        return offset(self.heel,turn((x,y),self.rear_pitch))

    def front(self,x,y):
        return offset(self.ball,turn((x,y),self.toe_pitch))

    def outsole(self):
        back=self.back
        front=self.front
        return [back(0,0),back(1.75,0),back(2.0,-.66),back(3.30,-.73),
                back(4.65,-.18),self.ball,front(self.toe_length-.95,0),
                front(self.toe_length-.30,-.25),front(self.toe_length,-.65)]


def boot_pose(phase,ankle_x):
    key=sample_foot(phase)
    rear_pitch=math.radians(key.heel_deg)
    toe_pitch=math.radians(key.toe_deg)
    flex=clamp((key.heel_deg-key.toe_deg)/48)
    compression=clamp(body_drop(phase)/11)*clamp(1-key.lift/17)
    toe_length=3.65-.40*flex-.18*compression
    ankle_from_heel=turn((2.0,-3.55+.38*compression),rear_pitch)
    ball_from_heel=turn((5.85,-.07),rear_pitch)
    # The illustrated pose keys carry the solved ankle X as the planted ball rolls.
    heel=(ankle_x-ankle_from_heel[0],0)
    ball=offset(heel,ball_from_heel)
    upper=offset(heel,ankle_from_heel)
    boot=BootPose(heel,ball,upper,rear_pitch,toe_pitch,toe_length,flex,compression)
    floor_shift=FLOOR-key.lift*SOURCE_SCALE-max(y for _,y in boot.outsole())
    return BootPose(offset(heel,(0,floor_shift)),offset(ball,(0,floor_shift)),
                    offset(upper,(0,floor_shift)),rear_pitch,toe_pitch,toe_length,flex,compression)


def knee_for_boot(nodes,ankle):
    hip,reference_knee,reference_ankle=nodes[:3]
    upper=math.dist(hip,reference_knee)
    lower=math.dist(reference_knee,reference_ankle)
    reach=math.dist(hip,ankle)
    # Retain the drawing's two segment lengths and the right-facing knee bend.
    stretch=max(1.,(reach+.08)/(upper+lower))
    upper*=stretch
    lower*=stretch
    forward=(upper*upper-lower*lower+reach*reach)/(2*reach)
    height=math.sqrt(max(0,upper*upper-forward*forward))
    ux,uy=unit((ankle[0]-hip[0],ankle[1]-hip[1]))
    return hip[0]+ux*forward+uy*height,hip[1]+uy*forward-ux*height


def shoe_leather(image,fit,near):
    b=Brush(image)
    back,front=fit.back,fit.front
    flex,load=fit.flex,fit.compression
    tip=fit.toe_length
    toe_height=2.92-.43*flex-.23*load
    base='leather' if near else 'rearboot'
    shade='brown' if near else 'rearshaft'
    light='tan' if near else 'leather'
    # The welt spans a heel block, recessed arch, ball pad and round toe.
    # The two leather panels meet over the ball even when their sole angles differ.
    top=[back(-.35,-.55),back(-.40,-2.35),back(.18,-3.35),back(1.35,-4.32+.28*load),
         back(2.65,-4.10+.45*load),back(3.55,-3.62+.34*load),back(4.46,-3.16+.35*flex),
         front(.10,-toe_height+.18*flex),front(1.05,-toe_height-.07),
         front(tip-1.24,-toe_height-.22),front(tip-.46,-toe_height+.21),front(tip+.12,-1.52)]
    b.p(base,top+list(reversed(fit.outsole())),shade)
    b.p(light,[back(.42,-2.67),back(1.56,-3.42+.30*load),back(2.42,-3.16+.32*load),
               back(3.46,-2.67+.30*flex),back(3.14,-2.08),back(1.45,-2.04)])
    # A flexible toe cap holds its own highlight and sole edge while the heel rises.
    b.l(light,[front(.87,-toe_height+.52),front(tip-1.10,-toe_height+.38),
               front(tip-.35,-toe_height+.80)])
    b.l('sole',fit.outsole())
    b.l(shade,[back(.12,-.62),back(1.52,-.63),back(2.05,-1.08)])
    b.d('sole',back(.05,0),back(1.58,0))
    if flex>.34:
        b.l(shade,[back(4.25,-2.24),front(.48,-1.02)])
        b.d(light,front(.76,-1.86))
    elif fit.toe_pitch<-.13:
        b.l(shade,[back(4.12,-1.92),back(4.90,-1.51)])
    else:
        b.d(shade,back(4.65,-1.80+.45*load))
    b.d('gold' if near else 'tan',back(2.30,-3.14+.36*load))


def shin_and_ribbon(image,knee,fit,phase,near):
    lower=along(knee,fit.ankle)
    boot=Brush(image,lower)
    base='leather' if near else 'rearboot'
    shadow='brown' if near else 'rearshaft'
    light='tan' if near else 'leather'
    pinch=.42*fit.flex+.26*fit.compression
    boot.p(base,[(.39,-2.06),(.39,2.18),(.56,2.08),(.72,1.63+pinch),
                 (.83,1.48),(.97,1.40),(1.07,1.48),(1.09,-1.64),(.89,-1.55),
                 (.78,-1.86+pinch),(.70,-1.72),(.61,-2.1)],'sole')
    boot.l(light,[(.57,.86),(.69,1.03),(.82,.62)])
    boot.l(shadow,[(.71,-1.10),(.76,-.15),(.81,.14+pinch)])
    boot.l('metal' if near else 'tan',[(.62,.66),(.71,-.10),(.78,.66)])
    shoe_leather(image,fit,near)
    ux,uy=unit((fit.ankle[0]-knee[0],fit.ankle[1]-knee[1]))
    cuff=lower([(.41,.05)])[0]
    twist=math.sin(TAU*phase-.56)
    def ribbon(points):
        result=[]
        for x,y in points:
            tail=clamp(y/2.5)
            warp_x=x+tail*.77*twist
            warp_y=y+tail*.43*math.sin(2*TAU*phase-.77)
            result.append((cuff[0]+uy*warp_x+ux*warp_y*(1-.35*tail),
                           cuff[1]-ux*warp_x+uy*warp_y*(1-.35*tail)+.35*tail*warp_y))
        return result
    r=Brush(image,ribbon)
    r.p('pink',[(-3.15,-.7),(-3.12,-2),(-2,-2.1),(-.1,-.45),(1,-1.05),
                (2.2,-2.0),(3.05,-1.65),(2.95,.05),(1.35,.85),(1.86,2.80),
                (.77,2.45),(.03,1.06),(-1.48,2.5),(-2.25,2.35),(-1.55,.8),(-2.8,.73)],'roseink')
    r.l('blush',[(-2.5,-1.4),(-1.35,-.74),(-.30,-.15)])
    r.l('pearl' if near else 'blush',[(.78,-.05),(1.76,-.82),(2.45,-1.05)])
    r.d('pearl',(-2.20,-1.30));r.d('white' if near else 'pearl',(2,-1.16))
    r.d('pink',(-1.05,1.12),(1.12,1.40));r.d('blush',(-1.62,1.91))
    r.d('gold',(0,0))
    return cuff


def leg(nodes,phase,near):
    hip=nodes[0]
    fit=boot_pose(phase,nodes[2][0])
    knee=knee_for_boot(nodes,fit.ankle)
    upper=along(hip,knee)
    lower=along(knee,fit.ankle)
    image=Image.new('RGBA',(64,64))
    limb=Brush(image)
    upper_face=upper([(-.16,-2.45),(-.15,2.80),(.47,2.70),(.83,2.02),(.97,1.85)])
    lower_right=lower([(.03,1.8),(.29,1.85),(.56,1.5),(.87,1.2)])
    lower_left=lower([(.87,-1.2),(.53,-1.55),(.25,-1.85),(.02,-1.78)])
    upper_back=upper([(.82,-1.88),(.50,-2.32),(.20,-2.65)])
    limb.p('skin' if near else 'shade',upper_face+lower_right+lower_left+upper_back,
           'skinrim' if near else 'roseink')
    limb.p('skinlit' if near else 'skin',upper([(.13,-.48),(.13,1.4),(.47,1.63),
           (.84,1.32),(.92,.72),(.82,.08),(.45,-.70)]))
    limb.l('skinlit' if near else 'skin',lower([(.03,.82),(.25,.82),(.48,.48)]))
    limb.d('shade' if near else 'rear',*upper([(.93,-.58)]))
    boot=Image.new('RGBA',(64,64))
    cuff=shin_and_ribbon(boot,knee,fit,phase,near)
    image.alpha_composite(boot)
    toe=fit.front(fit.toe_length-.95,0)
    coords={'hip':hip,'knee':knee,'ankle':fit.ankle,'heel':fit.heel,'ball':fit.ball,
            'toe':toe,'toe_tip':fit.front(fit.toe_length,-.65),'cuff':cuff,
            'heel_pitch_deg':math.degrees(fit.rear_pitch),'toe_pitch_deg':math.degrees(fit.toe_pitch),
            'sole_clearance_px':FLOOR-max(y for _,y in fit.outsole())}
    return image,boot,coords


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
    theta=.076*math.cos(TAU*phase-.24)
    b=Brush(image,lambda pts:[offset(grip,turn(point,theta)) for point in pts])
    b.l('tan',[(1,-15),(-8,10)])
    wood=[(3,-16),(2,-16),(1,-15),(0,-14),(0,-13),(2,-11),(3,-9),(4,-7),
          (4,-5),(3,-3),(1,-1),(0,0),(-.8,2),(-2,4),(-3,6),(-5,7),
          (-7,8),(-8,9),(-8,10),(-7,10)]
    b.l('umber',wood,2);b.l('gold',wood);b.l('goldlight',[(2,-16),(1,-15),(0,-14)])
    b.l('metal',[(1,-12),(3,-9),(4,-7)]);b.d('goldlight',(3,-9),(4,-6),(-6,8))
    b.l('leather',[(1,-1),(0,1),(-1,2)],2);b.d('tan',(0,0),(-1,1))
    flower(b,4,-6,True);flower(b,-3.5,5.5,False)


def arm(image,nodes,phase,near):
    stride=TAU*phase
    sh,el,wr=nodes[3:]
    direction=1. if near else -.48
    sh=offset(sh,(-.51*direction*math.cos(stride-.14),-.22*direction*math.sin(stride)))
    el=offset(el,(-.91*direction*math.cos(stride+.31),.54*direction*math.cos(stride+.68)))
    wr=offset(wr,(-.82*direction*math.cos(stride-.42),.45*direction*math.sin(stride-.28)))
    b=Brush(image);upper=along(sh,el);lower=along(el,wr)
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
        open_hand=.5-.5*math.cos(stride-.70)
        dx,dy=turn((dx,dy),.38*math.sin(stride-.81)-.09)
        hand=along(wr,(wx+dx*(2.75+.52*open_hand),wy+dy*(2.75+.52*open_hand)))
        b.p('skin',hand([(-.1,-.92),(-.16,.86),(.32,1.32),(.57,1.06),(.70,.65),
            (1.10,.47),(1.10+.16*open_hand,-.24),(.91,-.64),(.76,-1.05),(.34,-1.20)]),'skinrim')
        b.l('skinlit',hand([(.05,.35),(.42,.72)]))
        b.d('skin',*hand([(.84,.12)]))
        hand_end=hand([(1.10+.16*open_hand,-.24)])[0]
    else:
        dx,dy=unit((wr[0]-el[0],wr[1]-el[1]));grip=(wr[0]+dx*1.8,wr[1]+dy*1.8)
        bow(image,grip,phase);h=Brush(image,move(*grip))
        h.p('skin',[(-1.7,-.5),(-.7,-1.3),(.9,-1),(1.45,-.1),(1.20,1),(.1,1.65),(-1.3,.9)],'skinrim')
        h.l('skinlit',[(-.75,-.45),(.75,-.45)]);h.d('skin',(.65,1))
        hand_end=grip
    return {'shoulder':sh,'elbow':el,'wrist':wr,'hand':hand_end}


def sprite(pose,phase,proof=None):
    p=float(phase)
    bob=body_drop(p)*SOURCE_SCALE
    img=Image.new('RGBA',(64,64))
    front,rear=pose
    back_cape(img,p,bob)
    rear_arm=arm(img,rear,p,False)
    far_leg,far_boot,far_joints=leg(rear,(p+.5)%1,False)
    near_leg,near_boot,near_joints=leg(front,p,True)
    img.alpha_composite(far_leg)
    img.alpha_composite(near_leg)
    hair_tail(img,p,bob)
    torso(img,bob,p)
    quiver(img,bob,p)
    near_arm=arm(img,front,p,True)
    mantle(img,p,bob)
    neck_and_head(img,bob,p)
    if proof is not None:
        proof.update({'near-leg':near_leg,'far-leg':far_leg,'near-boot':near_boot,'far-boot':far_boot})
    return img,{'near':{**near_joints,**near_arm},'far':{**far_joints,**rear_arm}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preview-dir',type=Path)
    parser.add_argument('--output-dir',type=Path,default=OUT)
    args=parser.parse_args();poses=json.loads((ART/'pose-keys.json').read_text(encoding='utf8'))
    args.output_dir.mkdir(parents=True,exist_ok=True)
    frames={};joints={};isolated={}
    for key,pose in poses.items():
        phase=Fraction(key)
        layers={} if args.preview_dir and (phase*12).denominator==1 else None
        frames[phase],joints[key]=sprite(pose,phase,layers)
        if layers is not None:
            isolated[int(12*phase)]=layers
    for count in COUNTS:
        strip=Image.new('RGBA',(64*count,64))
        for i in range(count):
            strip.paste(frames[Fraction(i,count)],(i*64,0))
        strip.save(args.output_dir/f'blonde-pixel-walk-{count:02d}.png',optimize=True)
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
        samples=folder/'leg-samples'
        samples.mkdir(exist_ok=True)
        leg_sheet=Image.new('RGB',(6*50,4*33),'#a5aba0')
        boot_sheet=Image.new('RGB',(6*28,4*23),'#a5aba0')
        for i,layers in sorted(isolated.items()):
            for name,tile in layers.items():
                tile.save(samples/f'{name}-{i:02d}.png')
            for side,row in [('near',0),('far',2)]:
                color=('#a5aba0','#879c98')[i%2]
                cell=Image.new('RGBA',(50,33),color)
                cell.alpha_composite(layers[f'{side}-leg'].crop((12,30,62,63)))
                leg_sheet.paste(cell,(i%6*50,(i//6+row)*33))
                fit=joints[str(Fraction(i,12))][side]
                heelx=ip(fit['heel'])[0]
                shoe=layers[f'{side}-boot'].crop((heelx-11,39,heelx+17,62))
                cell=Image.new('RGBA',shoe.size,color)
                cell.alpha_composite(shoe)
                boot_sheet.paste(cell,(i%6*28,(i//6+row)*23))
        leg_sheet.resize((leg_sheet.width*3,leg_sheet.height*3),Image.Resampling.NEAREST).save(folder/'leg-poses.png')
        boot_sheet.resize((boot_sheet.width*5,boot_sheet.height*5),Image.Resampling.NEAREST).save(folder/'boot-poses.png')


if __name__=='__main__':
    main()
