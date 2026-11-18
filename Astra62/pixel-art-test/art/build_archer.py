"""Build the four registered 64 px walk strips from the archer artwork.

Requires Pillow. Pass --preview-dir to save enlarged frames and a proof sheet.
The body stays in place. The two legs sample the same walk half a cycle apart.
"""

import argparse
import math
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw


ART = Path(__file__).resolve().parent
SIZE = (64, 64)
TAU = math.tau

# The original illustrated portrait supplies the head and trailing hair. These
# paired ramps convert its locally mixed pixels into single, deliberate colors.
HAIR_RAMP = {
    "121719": "19242a", "27171a": "37232b", "401b1c": "562c2c",
    "642820": "76392a", "87351d": "a04a2b", "a4491e": "ba602f",
    "bd6426": "d7823a", "ce842f": "e99c49", "e6a03b": "f3b353",
    "f8c358": "ffda7a", "825031": "a25d3b", "a96b45": "c47d51",
    "d28c58": "e8a267", "eba56a": "f5ba7e", "ffc382": "ffcf91",
    "ffdcad": "ffe5ad", "354327": "3f5740", "596032": "71874c",
}

P = {
    "ink": "#1a252b", "wine": "#512f32", "hair": "#9e4b2e",
    "copper": "#cb7139", "amber": "#ed9b46", "goldhair": "#ffce6a",
    "palehair": "#ffe49a", "skindark": "#97553e", "skinmid": "#d4875a",
    "skin": "#f1b277", "skinlit": "#ffd696", "facegleam": "#ffe5af",
    "mantledeep": "#223a36", "mantleshadow": "#344c38", "mantle": "#516c44",
    "leaf": "#769249", "leaflit": "#a0b45c", "leafglint": "#c0c872",
    "tealdeep": "#243c3e", "tealshade": "#2f514b", "teal": "#427066",
    "teallit": "#709183", "tealglint": "#96a783", "leatherdeep": "#432e31",
    "leather": "#79503b", "leathermid": "#9d6341", "leatherlit": "#c48a55",
    "leatherglint": "#e2ac68", "golddeep": "#936b3c", "brass": "#d5a65d",
    "brasslit": "#f9d57e", "fletch": "#b2a98a", "fletchlit": "#e9dab1",
    "string": "#b6a786", "eye": "#41775f", "eyelit": "#9ec785",
}

NEAR = {
    "edge": "#23302e", "tightshadow": "#4d503f", "tight": "#74754f",
    "tightsun": "#989461", "bootedge": "#392b2e", "bootshadow": "#674234",
    "boot": "#916040", "bootsun": "#b77c4c", "stitch": "#d49b5c",
}
FAR = {
    "edge": "#202d32", "tightshadow": "#35453f", "tight": "#53624b",
    "tightsun": "#727952", "bootedge": "#352c2f", "bootshadow": "#4d3934",
    "boot": "#6f4d3b", "bootsun": "#926447", "stitch": "#aa8053",
}


def color(value):
    return P.get(value, value)


def point(pt):
    return tuple(math.floor(n + 0.5) for n in pt)


def polygon(draw, fill, vertices, edge=None):
    draw.polygon([point(v) for v in vertices], fill=color(fill), outline=color(edge) if edge else None)


def line(draw, fill, vertices, width=1):
    draw.line([point(v) for v in vertices], fill=color(fill), width=width)


def dot(draw, fill, *coords):
    draw.point([point(v) for v in coords], fill=color(fill))


def segment_map(start, end):
    """Map length fractions and lateral offsets onto an articulated limb."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)

    def mapped(vertices):
        return [(start[0] + u * dx + w * dy / length, start[1] + u * dy - w * dx / length)
                for u, w in vertices]

    return mapped


def sample(track, phase):
    """Interpolate a closed pose track. Both ends of the table are the same pose."""
    for (a, *start), (b, *end) in zip(track, track[1:]):
        if phase <= b:
            w = (phase - a) / (b - a)
            return [x + (y - x) * w for x, y in zip(start, end)]
    return list(track[-1][1:])


# The heel meets the baseline, the sole rolls flat and the toe leaves last.
# Phase, horizontal ankle, sole angle in degrees, clearance above ground.
FOOT_TRACK = [
    (0, 40.5, -17, 0), (.08, 38.6, -1, 0), (.23, 33.7, 0, 0),
    (.34, 29.8, 3, 0), (.42, 26, 12, 0), (.50, 22.4, 25, 0),
    (.58, 21.4, 38, 2.4), (.66, 23.2, 28, 5.8), (.75, 28.7, 7, 7),
    (.84, 34.4, -10, 5.5), (.92, 38.6, -20, 2.6), (1, 40.5, -17, 0),
]
BODY_TRACK = [(0, 0), (.10, 1), (.18, .4), (.29, -1.1), (.39, -1.25), (.5, 0)]
FOOT_OUTLINE = [(-2.3, -.8), (-1.2, -1.8), (1.4, -1.6), (2.6, .1), (3.6, 1.2),
                (5.9, 1.1), (6.9, 2), (6.5, 3.1), (5.1, 3.9), (-1.7, 3.9), (-2.5, 3)]


def leg(draw, phase, near, bob):
    shades = NEAR if near else FAR
    x, angle, clearance = sample(FOOT_TRACK, phase)
    hip = (32.3 if near else 33.2, 37.3 + bob)
    angle = math.radians(angle)
    c, s = math.cos(angle), math.sin(angle)
    sole = max(vx * s + vy * c for vx, vy in FOOT_OUTLINE)
    ankle = (x, 60 - clearance - sole)

    def footcoords(vertices):
        return [(ankle[0] + vx*c - vy*s, ankle[1] + vx*s + vy*c) for vx, vy in vertices]

    dx, dy = ankle[0] - hip[0], ankle[1] - hip[1]
    distance = math.hypot(dx, dy)
    upper, lower = 11.8, 10.8
    along = min(upper, (distance**2 + upper**2 - lower**2)/(2*distance))
    bend = math.sqrt(max(0, upper**2 - along**2))
    knee = (hip[0] + (dx*along + dy*bend)/distance, hip[1] + (dy*along - dx*bend)/distance)
    thigh = segment_map(hip, knee)
    shin = segment_map(knee, ankle)

    polygon(draw, shades['tight'], thigh([(-.12, -3.2), (-.06, 2.8), (.42, 3), (.83, 2.2),
            (1.08, 1.3), (1.13, -1.3), (.71, -2.2), (.30, -3)]), shades['edge'])
    polygon(draw, shades['tightshadow'], thigh([(.02, -2.5), (.35, -2.4), (.76, -1.8),
            (1.02, -.8), (.94, -.2), (.63, -.4), (.28, -1.1)]))
    line(draw, shades['tightsun'], thigh([(.14, 1.45), (.48, 1.55), (.77, 1.10)]))
    polygon(draw, shades['tight'], shin([(-.13, -1.6), (-.09, 1.7), (.20, 2),
            (.53, 1.4), (.55, -1.4), (.20, -2)]), shades['edge'])

    polygon(draw, shades['bootshadow'], shin([(.16, -2.4), (.13, 2.6), (.37, 2.6),
            (.67, 1.9), (1.12, 1.6), (1.14, -1.9), (.77, -1.6), (.43, -2.45)]), shades['bootedge'])
    polygon(draw, shades['boot'], shin([(.28, -.5), (.23, 1.8), (.48, 1.9),
            (.75, 1.1), (.90, .8), (.82, -.8)]))
    polygon(draw, shades['boot'], shin([(.10, -3), (.08, 2.5), (.21, 3.2),
            (.34, 2.5), (.30, .8), (.43, -.35), (.31, -2.6)]), shades['bootedge'])
    line(draw, shades['bootsun'], shin([(.14, -2), (.12, .8), (.15, 2.2)]))
    line(draw, shades['bootsun'], shin([(.58, -.6), (.52, 1.1)]))
    dot(draw, shades['stitch'], *shin([(.74, .5)]))

    polygon(draw, shades['bootshadow'], footcoords(FOOT_OUTLINE), shades['bootedge'])
    polygon(draw, shades['boot'], footcoords([(-1.45,-.4), (.65,-.75), (2.45,.9), (4,1.6),
            (5.9,1.6), (5.85,2.7), (2,2.9), (.1,2.1), (-1.2,2.3)]))
    line(draw, shades['bootsun'], footcoords([(2.4,1), (3.8,1.5), (5.7,1.35)]))
    line(draw, shades['bootedge'], footcoords([(-1.45,3.2), (1,3.35), (3.7,3.45)]))
    line(draw, shades['bootsun'], footcoords([(-1.3,-.2), (1.2,-.75)]))


def bow(draw, hand, tilt):
    # The string is a separate uninterrupted line, visible inside both limbs.
    c, s = math.cos(tilt), math.sin(tilt)

    def mounted(vertices):
        return [(hand[0] + x*c - y*s, hand[1] + x*s + y*c) for x, y in vertices]

    limbs = [(0,-17), (-2,-17), (-3,-15), (-3,-12), (-1,-9), (1,-7),
             (2,-5), (2,-3), (.5,-1.5), (.2,0), (1.4,3), (1.5,6), (0,8.8),
             (-2.8,11.9), (-5.4,14), (-6,16), (-5,17)]
    line(draw, 'string', mounted([(-2,-16), (-6,16)]))
    line(draw, 'leatherdeep', mounted(limbs), 2)
    line(draw, 'leathermid', mounted(limbs))
    line(draw, 'leatherglint', mounted([(-2,-16), (-3,-15), (-3,-13)]))
    line(draw, 'leatherlit', mounted([(-1,-9), (1,-7), (2,-5)]))
    line(draw, 'leatherglint', mounted([(1.4,3), (1.5,6), (0,8.8)]))
    line(draw, 'leatherlit', mounted([(-1,10), (-2.8,11.9), (-5.1,13.8)]))
    line(draw, 'leatherdeep', mounted([(1,-2), (0,0), (1,1.7)]), 2)
    dot(draw, 'brass', *mounted([(-.2,-16.8), (-5.1,16.6)]))


def far_arm(draw, phase, bob):
    swing = math.cos(TAU*phase)
    shoulder = (35.8, 22.8 + bob)
    elbow = (38.8 + 2*swing, 28.9 + bob)
    hand = (49 + 1.5*swing, 30.8 + .6*swing + bob)
    upper = segment_map(shoulder, elbow)
    lower = segment_map(elbow, hand)
    polygon(draw, 'skinmid', upper([(0,-1.8), (0,1.7), (.6,1.8), (1.12,1.2),
            (1.15,-1.5), (.45,-1.4)]), 'leatherdeep')
    line(draw, 'skin', upper([(.50,1),(.98,.7)]))
    polygon(draw, 'leather', lower([(-.12,-1.3),(-.1,1.3),(.23,1.9),(.76,1.6),
            (.87,1.1),(.84,-1.4),(.28,-1.7)]), 'leatherdeep')
    line(draw, 'leatherlit', lower([(.28,1.2),(.47,1.2)]))
    line(draw, 'leathermid', lower([(.54,-1),(.64,1)]))
    bow(draw, hand, .06 - .035*swing)
    hx, hy = hand
    polygon(draw, 'skinmid', [(hx-2,hy-.5),(hx-1,hy-1.7),(hx+.9,hy-1.6),
            (hx+1.8,hy-.5),(hx+1.4,hy+1.4),(hx+.3,hy+2),(hx-1.1,hy+1.5)], 'leatherdeep')
    line(draw, 'skinlit', [(hx-.9,hy-.7),(hx+.9,hy-.6)])
    dot(draw, 'skin', (hx+.7,hy+.9))


def torso(draw, bob, phase):
    sway = round(.8 * math.cos(TAU * phase - .55))

    def m(vertices):
        return [(x,y+bob) for x,y in vertices]

    polygon(draw, 'tealshade', m([(31,20),(36,20),(38,22),(40,23),(41,25),(39,27),
            (38,30),(39,33),(40,36),(41,39),(38,38),(35,37),(34,39),(31,39),
            (29+sway,41),(27,39),(24+sway,40),(26,36),(28,33),(27,29),(27,25)]), 'ink')
    polygon(draw, 'teal', m([(34,22),(38,22),(40,25),(38,26),(37,29),(36,32),
            (33,32),(33,29),(35,26)]))
    line(draw, 'teallit', m([(39,24),(39,25),(37,27),(37,29)]))
    polygon(draw, 'mantleshadow', m([(29,32),(35,32),(35,35),(33,37),(32,39),
            (30,39),(29+sway,41),(27,39),(25+sway,40),(26,37)]))
    polygon(draw, 'mantle', m([(30,34),(34,33),(33,36),(31,38),(29+sway,40),
            (29,38),(27+sway,39),(28,36)]))
    line(draw, 'leaf', m([(33,35),(32,37),(30+sway,39)]))
    polygon(draw, 'teal', m([(36,32),(38,33),(39,36),(40,37),(40,38),
            (37,36),(35,35)]))
    line(draw, 'leaflit', m([(35,34),(36,36),(39,38)]))
    # The diagonal baldric passes under the waist belt and the small satchel.
    line(draw, 'leatherdeep', m([(37,21),(36,24),(33,27),(30,30),(28,32)]), 3)
    line(draw, 'leather', m([(37,21),(36,24),(33,27),(30,30),(28,32)]), 2)
    line(draw, 'leatherlit', m([(36,24),(35,25)]))
    line(draw, 'leathermid', m([(33,27),(31,29)]))
    dot(draw, 'brasslit', *m([(35,24),(36,25)]))
    polygon(draw, 'leather', m([(28,29),(32,30),(38,30),(39,31),(38,32),
            (34,32),(31,31),(28,31)]), 'leatherdeep')
    line(draw, 'leatherlit', m([(31,30),(34,31)]))
    polygon(draw, 'brass', m([(36,30),(38,30),(38,32),(36,32)]))
    dot(draw, 'brasslit', *m([(36,30),(37,30)])); dot(draw, 'leatherdeep', *m([(37,31)]))
    polygon(draw, 'leather', m([(28,31),(32,32),(32,34),(30,36),(27,35),(26,34)]), 'leatherdeep')
    line(draw, 'leathermid', m([(27,32),(30,33),(32,32)])); dot(draw, 'brasslit', *m([(29,33)]))


def free_arm(draw, phase, bob):
    swing = math.cos(TAU*phase)
    shoulder = (30.3, 23.6 + bob)
    elbow = (28 - 3.5*swing, 30.4 + bob)
    wrist = (27.6 - 6.6*swing, 37 + bob - .7*math.sin(TAU*phase))
    upper = segment_map(shoulder, elbow)
    lower = segment_map(elbow, wrist)
    polygon(draw, 'skinmid', upper([(0,-1.9),(0,2.2),(.63,2.1),(1.10,1.25),
            (1.12,-1.45),(.54,-1.8)]), 'leatherdeep')
    polygon(draw, 'skin', upper([(.25,-.6),(.31,1.45),(.64,1.5),(1,1.1),
            (.93,-.35),(.68,-.65)]))
    line(draw, 'skinlit', upper([(.5,.95),(.8,.95)]))
    polygon(draw, 'leather', lower([(-.10,-1.65),(-.02,1.7),(.10,2.2),
            (.72,1.5),(1.04,1.1),(1,-1.2),(.77,-1.3),(.32,-1.8)]), 'leatherdeep')
    line(draw, 'leathermid', lower([(.19,.8),(.39,1.1),(.69,.55)]))
    line(draw, 'leatherlit', lower([(.11,-.8),(.10,1.2)]))
    line(draw, 'leathermid', lower([(.77,-1),(.83,1.1)]))
    wx, wy = wrist
    polygon(draw, 'skinmid', [(wx-1.05,wy-.1),(wx+.8,wy-.1),(wx+1.4,wy+1.3),
            (wx+1.3,wy+2.3),(wx+.2,wy+2.3),(wx+.25,wy+3.5),(wx-.65,wy+3),
            (wx-1.5,wy+2.1),(wx-1.7,wy+.9)], 'leatherdeep')
    line(draw, 'skinlit', [(wx-.7,wy+.7),(wx+.2,wy+.65)])
    dot(draw, 'skin', (wx-.75,wy+1.7))


def quiver(draw, bob, phase):
    tilt = .65*math.sin(TAU*phase-.25)

    def fixed(vertices):
        return [(x+tilt*max(0,(31-y)/17), y+bob) for x,y in vertices]

    for x,y in [(20.3,14.5),(23,14),(24.5,15.8)]:
        line(draw, 'leather', fixed([(x,y+.3),(x+3, y+8)]))
        polygon(draw, 'fletch', fixed([(x-1.4,y-.6),(x,y),(x+.6,y-.6),(x+1.5,y+1.5),
                (x+1.4,y+3.2),(x-.2,y+2.1)]), 'leatherdeep')
        line(draw, 'fletchlit', fixed([(x-.7,y-.35),(x+.65,y+1.65)]))
    polygon(draw, 'leather', fixed([(21,20),(27,18.5),(29,29),(28,31),(25,32),(23,30)]), 'ink')
    polygon(draw, 'leathermid', fixed([(22,20),(27,19),(27.3,21),(22.7,22.3)]), 'leatherdeep')
    line(draw, 'leatherlit', fixed([(22,20),(26.5,19)]))
    line(draw, 'leathermid', fixed([(23.5,24),(25.1,29.5)]))


def cape(draw, bob, phase, underside=False):
    lift = math.sin(TAU*phase-.55)
    drag = math.cos(TAU*phase-.45)

    def cloth(vertices):
        out = []
        for x,y in vertices:
            freedom = min(1, max(0,(34-x)/16)) * min(1,max(0,(y-19)/9))
            out.append((x + freedom*1.3*drag, y + bob + freedom*1.65*lift))
        return out

    if underside:
        polygon(draw, 'mantledeep', cloth([(32,20),(36,21),(33,24),(30,28),(28,30),
                (27,29),(25,32),(24,31),(21,34),(20,33),(17,35),(18,31),(18,29),
                (21,25),(26,23),(28,20)]), 'ink')
        polygon(draw, 'mantleshadow', cloth([(30,22),(33,22),(31,26),(27,29),(27,28),
                (24,31),(23,30),(19,33),(20,29),(23,26)]))
        return
    polygon(draw, 'mantle', cloth([(29,19),(33,19),(36,20),(38,22),(37,23),(35,24),
            (33,27),(31,27),(30,29),(29,28),(27,29),(26,28),(24,30),(23,29),
            (20,30),(17,32),(17,29),(19,27),(22,25),(25,24),(26,21)]), 'mantledeep')
    polygon(draw, 'leaf', cloth([(29,20),(34,20),(35,21),(32,21),(28,23),(26,25),
            (23,26),(20,28),(19,29),(19,28),(22,25),(25,24),(27,21)]))
    polygon(draw, 'mantleshadow', cloth([(34,22),(35,23),(32,26),(29,28),(30,26),
            (32,24),(28,26),(25,28),(27,25),(30,23)]))
    line(draw, 'leaflit', cloth([(32,24),(30,26),(29,27)]))
    line(draw, 'leaflit', cloth([(28,25),(26,27),(24,28)]))
    line(draw, 'leaf', cloth([(24,27),(21,29),(18,30)]))
    dot(draw, 'leafglint', *cloth([(29,20),(28,21)]))
    polygon(draw, 'mantleshadow', cloth([(28,20),(29,18),(32,18),(35,19),(37,20),
            (37,22),(35,22),(32,21),(29,21),(27,23)]), 'mantledeep')
    line(draw, 'leaf', cloth([(29,19),(32,19),(35,20)]))
    line(draw, 'mantle', cloth([(29,21),(31,20),(34,21),(36,21)]))
    polygon(draw, 'brass', cloth([(36,21),(38,21),(39,22),(38,23),(36,22)]), 'golddeep')
    line(draw, 'brasslit', cloth([(36,21),(38,22)]))


def native_hair(source):
    native = source.convert('RGBA').crop((68,-72,1172,1296)).resize(SIZE, Image.Resampling.LANCZOS)
    pairs = [(ImageColor.getrgb('#'+key), ImageColor.getrgb('#'+value)) for key,value in HAIR_RAMP.items()]
    face = Image.new('RGBA', SIZE)
    tail = Image.new('RGBA', SIZE)
    # Bounds follow the two overlapping masses in the original illustration.
    face_rows = {8:(31,38),9:(30,41),10:(28,42),11:(28,42),12:(27,43),13:(27,43),
                 14:(26,41),15:(25,41),16:(27,40),17:(26,40),18:(26,36),19:(26,36),20:(33,36)}
    tail_rows = {7:(24,30),8:(23,31),9:(22,29),10:(22,28),11:(21,27),12:(18,25),
                 13:(17,24),14:(16,21),15:(16,20),16:(13,17),17:(12,18),
                 18:(11,17),19:(13,15),20:(13,14),21:(14,14)}
    for target, rows in ((tail,tail_rows),(face,face_rows)):
        d = ImageDraw.Draw(target)
        for y, (left,right) in rows.items():
            for x in range(left,right+1):
                r,g,b,a = native.getpixel((x,y))
                if a < 110:
                    continue
                _,match = min(pairs,key=lambda p:(r-p[0][0])**2 + 1.35*(g-p[0][1])**2 + .8*(b-p[0][2])**2)
                d.point((x,y), fill=match+(255,))
    # Pixel-scale facial features and ear are art-directed after resampling.
    d = ImageDraw.Draw(face)
    polygon(d, '#643a37', [(22,11),(25,11),(29,12),(34,13),(36,13),(35,15),(33,17),
            (31,16),(28,15),(25,13)])
    polygon(d, '#e6a17c', [(23,11),(26,12),(28,12),(32,13),(35,14),(34,15),
            (32,16),(30,15),(27,13)])
    line(d, '#ffdab1', [(23,11),(25,12),(28,12),(31,13),(34,14)])
    line(d, '#bd795f', [(28,13),(30,14),(32,15)])
    dot(d, '#ffd6a1', (33,15)); dot(d, 'brasslit', (33,16))
    line(d, 'wine', [(38,13),(40,13)])
    dot(d, '#fff2cb', (38,14)); dot(d, '#36856b', (39,14)); dot(d, '#24272a', (40,14))
    dot(d, 'facegleam', (40,15),(41,15)); dot(d, 'leatherdeep', (42,15))
    dot(d, 'skin', (39,16),(40,16)); dot(d, 'skindark', (41,16))
    dot(d, 'skinlit', (37,17),(38,17),(39,17)); dot(d, '#9a5d49', (40,17))
    dot(d, 'skin', (38,18),(39,18)); dot(d, 'wine',(40,18),(38,19))
    line(d, 'amber', [(33,17),(34,16),(35,15)])
    dot(d, 'goldhair', (35,15),(36,12),(37,11),(40,10))
    dot(d, 'palehair', (37,11))
    d = ImageDraw.Draw(tail)
    line(d, 'goldhair', [(23,10),(24,9),(26,8)]); dot(d,'palehair',(25,8))
    line(d, 'amber', [(17,14),(19,13)]); dot(d, 'goldhair',(19,12),(13,17))
    dot(d, 'brass', (16,15)); dot(d, 'leaf', (28,8),(29,8))
    return face, tail


def trailing_hair(original, phase):
    layer = Image.new('RGBA', SIZE)
    for y in range(5,25):
        for x in range(8,33):
            freedom = min(1,max(0,(29-x)/16))
            sy = y-round(1.4*math.sin(TAU*phase-.8)*freedom)
            sx = x-round(1.1*math.cos(TAU*phase-.65)*min(1,max(0,(sy-8)/12)))
            pixel = original.getpixel((sx,sy))
            if pixel[3]:
                layer.putpixel((x,y), pixel)
    return layer


def sprite(phase, hair):
    face, tail = hair
    frame = Image.new('RGBA', SIZE)
    d = ImageDraw.Draw(frame)
    bob = round(sample(BODY_TRACK, phase % .5)[0])
    leg(d, (phase+.5)%1, False, bob)
    leg(d, phase, True, bob)
    far_arm(d, phase, bob)
    quiver(d, bob, phase)
    frame.alpha_composite(trailing_hair(tail, phase), (0,bob))
    torso(d, bob, phase)
    cape(d, bob, phase, underside=True)
    free_arm(d, phase, bob)
    cape(d, bob, phase)
    frame.alpha_composite(face, (0,bob))
    return frame


def previews(folder, frames):
    folder.mkdir(parents=True,exist_ok=True)
    proof = Image.new('RGB',(6*64,2*64), '#c2ad83')
    for i,img in enumerate(frames):
        x, y = i%6*64, i//6*64
        ImageDraw.Draw(proof).rectangle((x,y,x+63,y+63), fill='#84937b' if i%2 else '#a5a98c')
        proof.paste(img,(x,y),img)
    proof.resize((1152,384), Image.Resampling.NEAREST).save(folder/'walk-proof.png')
    for i in (0,3,6,9):
        mat = Image.new('RGBA', SIZE, '#798976'); mat.alpha_composite(frames[i])
        mat.resize((384,384), Image.Resampling.NEAREST).convert('RGB').save(folder/f'walk-{i:02d}.png')


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--preview-dir', type=Path)
    options = args.parse_args()
    with Image.open(ART/'archer-source.png') as source:
        hair = native_hair(source)
    output = ART.parent/'assets'
    output.mkdir(exist_ok=True)
    for count in (4,6,8,12):
        frames = [sprite(i/count,hair) for i in range(count)]
        strip = Image.new('RGBA',(64*count,64))
        for i,frame in enumerate(frames):
            strip.paste(frame,(64*i,0))
        strip.save(output/f'elf-walk-{count:02d}.png',optimize=True)
        if count == 12 and options.preview_dir:
            previews(options.preview_dir,frames)


if __name__ == '__main__':
    main()
