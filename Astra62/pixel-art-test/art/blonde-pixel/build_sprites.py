"""Hand-pixelled, compact blonde elf in one-second, right-facing walk cycles.

The illustration supplies the gait timing. The shorter limbs, broad skirt and
large head are drawn on the 64 px grid. Pass --preview-dir for joint positions,
transparent limbs and enlarged pose sheets. Pillow is the only dependency.
"""

import argparse
from dataclasses import dataclass
from fractions import Fraction
import json
import math
from pathlib import Path
import sys

from PIL import Image
from compact_head import draw_head, draw_ponytail
from pixel_brush import Brush, PALETTE, ip


ART=Path(__file__).resolve().parent
OUT=ART.parent.parent/'assets'
sys.path.insert(0,str(ART.parent))
from walk_cycle import body_drop, sample_foot

COUNTS=(4,6,8,12)
TAU=math.tau
SOURCE_SCALE=.542/8
FLOOR=59

def unit(v):
    length=math.hypot(*v) or 1
    return v[0]/length,v[1]/length


def along(a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]; ux,uy=unit((dx,dy))
    return lambda pts:[(a[0]+t*dx+w*uy,a[1]+t*dy-w*ux) for t,w in pts]


def move(dx=0,dy=0):
    return lambda pts:[(x+dx,y+dy) for x,y in pts]


def clamp(value):
    return min(1.,max(0.,value))


def turn(point,angle):
    x,y=point
    c,s=math.cos(angle),math.sin(angle)
    return x*c-y*s,x*s+y*c


def offset(a,b):
    return a[0]+b[0],a[1]+b[1]


def compact_joints(pose, near):
    """Retarget the shared walking poses around the planted ankles and carrying shoulder."""
    hip, knee, ankle, shoulder, elbow, wrist = pose
    legs = [(37.4 + (x - 38) * .83, 55 + (y - 55) * .78) for x, y in (hip, knee, ankle)]
    if near:
        socket = (34.2 + (shoulder[0] - 35.6) * .85, 27.4 + (shoulder[1] - 20.9) * .80)
        reach = 0
    else:
        socket = (40.5 + (shoulder[0] - 37.9) * .85, 27.9 + (shoulder[1] - 21.6) * .80)
        reach = 2.15
    arm_joints = [(socket[0] + (x - shoulder[0]) * .83 + reach * fraction,
                   socket[1] + (y - shoulder[1]) * .83)
                  for (x, y), fraction in ((elbow, .46), (wrist, 1))]
    return [*legs, socket, *arm_joints]


def torso_points(phase, bob, points):
    stride = TAU * phase
    rotation = math.cos(stride - .12)
    weight = math.cos(2 * stride - .82)
    result = []
    for x, y in points:
        hip = clamp((y - 25) / 13)
        hem = clamp((y - 35) / 9)
        side = max(-1., min(1., (x - 37) / 9))
        dx = (1.20 * hip - .56) * rotation + hem * (.70 * math.sin(stride - .72) + .38 * side * weight)
        dy = bob + hem * (.90 * side * math.sin(stride - .50) - .48 * weight)
        result.append((x + dx, y + dy))
    return result


def back_cape(image, phase, bob):
    stride = TAU * phase

    def drape(points):
        result = []
        for x, y in points:
            free = clamp((36 - x) / 19) * clamp((y - 25) / 11)
            delay = .55 + .65 * free
            dx = -.56 * (1 - free) * math.cos(stride) + 1.7 * free * math.sin(stride - delay)
            dy = bob + free * (1.75 * math.sin(stride - delay) + .45 * math.sin(2 * stride - .68))
            result.append((x + dx, y + dy))
        return result

    b = Brush(image, drape)
    # The pink lining is visible between the two ends of the green traveling cloak.
    b.p('pink', [(34,26),(37,29),(37,38),(34,42),(32,43),(30,43),(29,44),
                 (27,44),(26,43),(24,44),(22,44),(21,43),(19,44),(17,42),
                 (15,41),(13,39),(13,37),(23,32)], 'roseink')
    b.p('blush', [(15,38),(21,37),(26,38),(31,36),(35,36),(34,40),
                  (31,42),(29,42),(28,43),(26,42),(24,43),(22,42),(20,43),(17,40)])
    b.l('pearl', [(23,42),(24,42),(25,41)])
    b.p('olive', [(35,24),(37,26),(37,32),(36,36),(34,39),(31,41),(28,42),
                  (25,42),(22,44),(20,46),(19,46),(18,43),(17,40),(16,39),
                  (13,40),(11,42),(8,43),(9,40),(10,38),(13,36),(17,35),
                  (21,34),(26,31),(31,27)], 'olivedeep')
    b.p('oliveshade', [(34,27),(34,31),(32,34),(28,37),(26,40),(25,41),
                       (22,43),(20,45),(19,42),(19,40),(22,38),(27,34),(31,29)])
    b.p('olivelit', [(31,27),(29,30),(25,33),(20,35),(17,36),
                     (13,37),(10,40),(13,39),(16,38),(21,37),(27,33)])
    b.l('gold', [(9,42),(11,40),(14,38),(17,37),(20,36)])
    b.l('goldlight', [(10,41),(12,39),(14,38)])
    b.l('metal', [(19,42),(20,45),(23,42),(26,41),(29,41),(32,39)])
    b.l('gold', [(20,44),(22,42),(25,41),(28,41)])
    # A forked gold sprig follows the wide, shaded lower fold.
    b.l('gold', [(21,42),(22,40),(24,38),(25,37)])
    b.l('gold', [(23,39),(21,38),(20,38)])
    b.d('goldlight', (25,37),(20,38))


def torso(image, bob, phase):
    def fabric(points):
        return torso_points(phase, bob, points)

    b = Brush(image, fabric)
    # White puffed blouse, moss-green bodice and a leather belt with a square buckle.
    b.p('olive', [(34,25),(38,25),(41,27),(43,28),(44,30),(43,32),(43,35),
                  (45,37),(44,39),(32,40),(31,37),(32,34),(32,29)], 'olivedeep')
    b.p('ivorymid', [(36,25),(39,26),(42,27),(44,29),(44,31),
                     (42,33),(37,32),(34,29)], 'ivoryshade')
    b.p('pearl', [(37,26),(40,27),(42,28),(43,29),(43,31),(41,32),
                  (38,31),(37,29)])
    b.l('white', [(39,27),(41,28),(42,29)])
    b.l('ivorymid', [(39,29),(39,31),(40,32)])
    b.p('oliveshade', [(33,30),(37,31),(40,32),(43,31),(43,35),(41,37),
                       (34,37),(32,35)], 'olivedeep')
    b.p('olive', [(35,32),(38,33),(39,35),(37,36),(34,35)])
    b.l('metal', [(42,32),(41,34),(42,35)])
    b.d('goldlight', (42,32),(41,34))

    # Pink scalloped petticoat under a full yellow-green skirt. Each major fold
    # gets a continuous area of one value so the embroidery has room to read.
    b.p('rose', [(33,36),(42,36),(45,38),(47,40),(48,42),(48,43),
                 (47,44),(45,44),(44,45),(42,45),(41,44),(39,46),
                 (37,46),(36,45),(34,46),(32,45),(30,45),(29,44),(27,43),(28,41)], 'roseink')
    b.p('blush', [(29,41),(33,41),(38,42),(43,41),(47,41),(47,43),
                  (45,43),(44,44),(42,44),(41,43),(39,45),(37,45),
                  (36,44),(34,45),(32,44),(30,44),(29,43)])
    b.l('pearl', [(30,43),(32,44),(33,44)])
    b.l('pearl', [(37,44),(38,45),(40,44)])
    b.d('pearl', (44,43),(46,43))

    b.p('lime', [(33,35),(41,35),(43,36),(45,38),(46,39),(48,41),
                 (46,42),(44,43),(42,43),(41,42),(38,44),(36,44),
                 (34,43),(32,44),(30,43),(27,42),(29,39)], 'leafdark')
    b.p('leaf', [(33,37),(35,36),(34,39),(32,42),(30,42),(29,41),(31,39)])
    b.p('limelit', [(35,37),(38,36),(42,37),(44,39),(46,41),(43,42),
                    (41,41),(38,43),(36,43),(34,42),(32,43),(33,41)])
    b.l('lime', [(38,37),(38,39),(37,40)])
    b.l('lime', [(42,38),(42,39),(44,41)])
    # Register each two-leaf sprig to its fold, then stamp its pixels together.
    for x, y in ((32,40), (38,41), (44,40)):
        anchor = ip(fabric([(x,y)])[0])
        leaf = Brush(image, move(*anchor))
        leaf.p('leafdark', [(-2,-1),(-1,-1),(0,1),(-1,1),(-2,0)])
        leaf.l('leafdark', [(0,1),(1,0),(2,-2)])
        leaf.d('leaf', (1,-1),(2,-1))
    b.p('ivorymid', [(33,35),(40,35),(43,36),(45,38),(43,38),(42,37),
                     (40,38),(39,39),(37,38),(36,39),(34,38),(32,39),
                     (30,39),(31,37)], 'metal')
    b.l('pearl', [(31,38),(33,37),(35,37),(36,38),(38,37)])
    b.l('goldlight', [(40,37),(41,36),(43,37)])
    b.p('leather', [(32,34),(35,34),(39,33),(42,33),(43,34),(42,35),
                    (39,36),(35,36),(33,37),(32,36)], 'brown')
    b.l('tan', [(33,35),(35,35),(37,34)])
    b.p('gold', [(39,33),(42,33),(42,35),(39,35)])
    b.d('brown', (40,34),(41,34))
    b.d('shine', (39,33))


def quiver(image, bob, phase):
    stride = TAU * phase

    def shoulder_strap(points):
        return [(x - 3 + .65 * math.cos(stride - .1) + .70 * math.sin(stride - .56) * clamp((40 - y) / 9),
                 y - .5 + bob + .40 * math.sin(2 * stride - .72) * clamp((40 - y) / 9)) for x,y in points]

    b = Brush(image, shoulder_strap)
    for x, y in [(25,32),(28,31),(30,32)]:
        b.l('brown', [(x,y),(x+2,38)])
        b.l('roseink', [(x-1,y-2),(x-1,y),(x+1,y+2)])
        b.l('pink', [(x,y-2),(x,y),(x+1,y+1)])
        b.d('pearl', (x,y-2),(x-1,y-1))
    b.p('leather', [(25,35),(30,33),(32,34),(33,40),(32,42),
                    (29,43),(27,41)], 'brown')
    b.l('tan', [(26,36),(28,35),(31,34)])
    b.l('metal', [(28,39),(30,40),(32,39)])
    b.d('goldlight', (29,40))
    b.l('tan', [(29,41),(30,42)])


def mantle(image, phase, bob):
    stride = TAU * phase

    def shoulders(points):
        return [(x - .56 * math.cos(stride) + .42 * clamp((38-x)/13) * math.sin(stride-.85),
                 y + bob + .58 * clamp((38-x)/13) * math.sin(2*stride-.74)) for x,y in points]

    b = Brush(image, shoulders)
    b.p('olive', [(32,26),(34,24),(37,24),(39,25),(41,26),(42,27),(43,28),
                  (41,28),(40,27),(39,28),(37,29),(34,31),(31,32),(28,32),
                  (25,31),(23,30),(26,30),(29,28)], 'olivedeep')
    b.p('oliveshade', [(31,28),(34,26),(37,25),(38,26),(35,27),
                       (33,29),(31,30),(27,30)])
    b.l('olivelit', [(27,30),(30,29),(32,28),(34,26)])
    b.l('gold', [(25,30),(28,31),(31,31),(34,30),(37,28),(39,26)])
    b.l('goldlight', [(29,31),(31,31),(33,30)])
    b.d('gold', (33,28),(36,26))
    b.p('metal', [(39,25),(41,25),(42,27),(41,28),(39,27),(38,26)])
    b.d('goldlight', (39,26),(40,25))
    b.d('lime', (40,26))


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
    # Keep the ball's rolling motion from the source stride at the shorter stride length.
    heel=(ankle_x-ankle_from_heel[0],0)
    ball=offset(heel,ball_from_heel)
    upper=offset(heel,ankle_from_heel)
    boot=BootPose(heel,ball,upper,rear_pitch,toe_pitch,toe_length,flex,compression)
    floor_shift=FLOOR-key.lift*SOURCE_SCALE*.86-max(y for _,y in boot.outsole())
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
            if not near:
                x*=.85
                y*=.80
            tail=clamp(y/2.5)
            warp_x=x+tail*.77*twist
            warp_y=y+tail*.43*math.sin(2*TAU*phase-.77)
            result.append((cuff[0]+uy*warp_x+ux*warp_y*(1-.35*tail),
                           cuff[1]-ux*warp_x+uy*warp_y*(1-.35*tail)+.35*tail*warp_y))
        return result
    r=Brush(image,ribbon)
    r.p('pink' if near else 'rose',[(-3.15,-.7),(-3.12,-2),(-2,-2.1),(-.1,-.45),(1,-1.05),
                (2.2,-2.0),(3.05,-1.65),(2.95,.05),(1.35,.85),(1.86,2.80),
                (.77,2.45),(.03,1.06),(-1.48,2.5),(-2.25,2.35),(-1.55,.8),(-2.8,.73)],'roseink')
    r.l('blush' if near else 'pink',[(-2.5,-1.4),(-1.35,-.74),(-.30,-.15)])
    r.l('pearl' if near else 'pink',[(.78,-.05),(1.76,-.82),(2.45,-1.05)])
    r.d('pearl' if near else 'pink',(-2.20,-1.30));r.d('white' if near else 'blush',(2,-1.16))
    r.d('pink' if near else 'rose',(-1.05,1.12),(1.12,1.40))
    r.d('blush' if near else 'pink',(-1.62,1.91))
    r.d('gold' if near else 'metal',(0,0))
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
    limb.p('skin' if near else 'rear',upper_face+lower_right+lower_left+upper_back,
           'skinrim' if near else 'roseink')
    limb.p('skinlit' if near else 'shade',upper([(.13,-.48),(.13,1.4),(.47,1.63),
           (.84,1.32),(.92,.72),(.82,.08),(.45,-.70)]))
    limb.l('skinlit' if near else 'shade',lower([(.03,.82),(.25,.82),(.48,.48)]))
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
    skin='skin' if near else 'shade'
    skin_light='skinlit' if near else 'skin'
    b.p(skin,upper([(-.05,-1.65),(-.03,1.85),(.64,1.75),(1.08,1.45),(1.10,-1.4),(.52,-1.68)]),'skinrim')
    b.p(skin,lower([(-.11,-1.50),(-.12,1.55),(.52,1.49),(.96,1.15),
        (1.06,-1.10),(.57,-1.4)]),'skinrim')
    b.l(skin_light,lower([(.06,.58),(.45,.55),(.73,.45)]))
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
        b.p('skin',hand([(-.1,-1.08),(-.16,.95),(.30,1.52),(.57,1.24),(.76,.82),
            (1.12,.51),(1.13+.16*open_hand,-.30),(.90,-.84),(.73,-1.27),(.30,-1.27)]),'skinrim')
        b.l('skinlit',hand([(.05,.30),(.43,.74),(.77,.47)]))
        b.d('skin',*hand([(.91,.06)]))
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
    front=compact_joints(pose[0],True)
    rear=compact_joints(pose[1],False)
    back_cape(img,p,bob)
    draw_ponytail(img,p,bob,PALETTE)
    rear_arm=arm(img,rear,p,False)
    far_leg,far_boot,far_joints=leg(rear,(p+.5)%1,False)
    near_leg,near_boot,near_joints=leg(front,p,True)
    img.alpha_composite(far_leg)
    img.alpha_composite(near_leg)
    torso(img,bob,p)
    quiver(img,bob,p)
    near_arm=arm(img,front,p,True)
    mantle(img,p,bob)
    draw_head(img,p,bob,PALETTE)
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
