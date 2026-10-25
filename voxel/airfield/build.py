"""Four newly authored airfield voxel models; only generic parent utilities used."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_tools'))
from voxelkit import Grid, Asset, run_theme

# Independent palette chosen from this theme's reference sheet.
PALETTE = [
    (0, 0, 0, 0),
    (225, 214, 187),   # 1 warm ivory
    (244, 234, 209),   # 2 ivory light
    (191, 180, 152),   # 3 ivory shadow
    (68, 106, 132),    # 4 aviation blue
    (91, 133, 156),    # 5 blue edge
    (42, 67, 85),      # 6 deep blue
    (219, 158, 53),    # 7 ochre safety stripe
    (246, 189, 77),    # 8 amber highlight
    (43, 47, 47),     # 9 rubber/propeller
    (65, 73, 76),     # 10 dark steel
    (112, 151, 170),  # 11 opaque glazing
    (151, 186, 198),  # 12 glazing light
    (148, 158, 157),  # 13 steel
    (197, 202, 188),  # 14 light alloy
    (145, 144, 130),  # 15 concrete
    (112, 114, 107),  # 16 concrete dark
    (250, 221, 153),  # 17 lamps
    (167, 121, 70),   # 18 shipping timber
]


def tire(g, center, radius, thickness):
    x, y, z = center
    g.cylinder(center, radius, thickness - 2, 0, 9)
    g.cylinder(center, radius - 1, thickness, 0, 9)
    # Alternating broad running blocks are native colored cells, not textures.
    radial = (g.y-y)**2 + (g.z-z)**2
    angle = np.arctan2(g.z-z, g.y-y)
    outer = (radial > (radius-1.5)**2) & (radial <= radius**2) & (np.abs(g.x-x) < thickness/2-1)
    g.data[outer & (np.cos(angle*10) > 0.2)] = 10
    g.cylinder(center, radius*.48, thickness+1, 0, 13)
    g.cylinder(center, radius*.23, thickness+2, 0, 10)


def propeller_plane():
    g = Grid((128, 104, 64), PALETTE)
    # Swept, blunt wings: round planform end caps and a shallow stepped section.
    span = np.abs(g.x-64)
    chord = 13 - 4*(span/60)**1.5
    wing = (span < 60) & (np.abs(g.y-47) < chord) & (g.z >= 27) & (g.z < 32)
    tipshape = (span < 55) | ((span-55)**2 + np.maximum(np.abs(g.y-47)-(chord-5),0)**2 < 25)
    wing &= tipshape
    g.data[wing] = 1
    g.data[wing & (g.z < 29)] = 4
    g.data[wing & (span > 49)] = 4
    g.data[wing & (span >= 45) & (span <= 49)] = 7
    g.data[wing & (np.abs(g.y-54)<1) & (span>22) & (span<44)] = 3
    # Fuselage changes section along its own length, tapering toward the tail.
    tail = np.clip((g.y-53)/45, 0, 1)
    xr = 10.5-7*tail
    zr = 11.5-6.5*tail
    centerz = 35+5*tail
    body = ((g.x-64)/xr)**2 + ((g.z-centerz)/zr)**2 <= 1
    body &= (g.y >= 14) & (g.y < 99)
    nose = np.clip((g.y-14)/10, 0.35, 1)
    body &= np.abs(g.x-64) <= xr*nose
    g.data[body] = 1
    g.data[body & (g.z < centerz-2)] = 4
    g.data[body & (g.z >= centerz-2) & (g.z < centerz)] = 7
    g.cylinder((64, 17, 35), 10.5, 6, 1, 4)
    g.cylinder((64, 13, 35), 7.5, 4, 1, 6)
    # Rounded opaque cockpit shell, visible side/front glass and structural bars.
    canopy = ((g.x-64)/10.5)**2 + ((g.y-40)/16)**2 + ((g.z-43)/14)**2 <= 1
    canopy &= g.z >= 40
    g.data[canopy] = 1
    window = canopy & (g.z>=45) & (g.z<54) & (g.y>=26) & (g.y<54)
    g.data[window] = 11
    g.data[window & (g.z>=50)] = 12
    g.data[window & (((g.y>=38)&(g.y<40)) | ((np.abs(g.x-64)<1.5)&(g.y<32)))] = 1
    # High tail and short rounded stabilizer, with blue blunt tips.
    g.roundbox((43, 86, 39), (85, 101, 43), 2, 1)
    g.box((43, 87, 39), (51, 100, 43), 4)
    g.box((77, 87, 39), (85, 100, 43), 4)
    fin = (np.abs(g.x-64)<2.5) & (g.z>=41) & (g.z<62) & (g.y>=82+(g.z-41)*.6) & (g.y<100)
    g.data[fin] = 1
    g.data[fin & (g.z>=58)] = 4
    g.data[fin & (g.z>=48) & (g.z<51)] = 7
    # Three-point landing gear, all connected to actual airframe structure.
    for x in (35, 93):
        g.beam((x, 47, 28), (x, 46, 12), 1.8, 13)
        g.beam((x, 46, 20), (x, 49, 11), 1.4, 10)
        tire(g, (x, 46, 7), 6.5, 6)
    g.beam((64, 22, 26), (64, 17, 10), 1.8, 13)
    tire(g, (64, 16, 5.5), 5, 5)
    # Two broad propeller blades, pale spinner and amber tips.
    g.beam((51, 8, 19), (77, 8, 51), 2.8, 9)
    g.beam((51, 8, 19), (53, 8, 22), 2.8, 7)
    g.beam((75, 8, 48), (77, 8, 51), 2.8, 7)
    g.cylinder((64, 8, 35), 4.4, 9, 1, 1)
    g.cylinder((64, 3.5, 35), 2.8, 2, 1, 2)
    return Asset('propeller_plane', 'Propeller plane', g, .05,
        ['Original low-wing utility plane: broad blunt wing tips, opaque rounded cockpit, diagonal two-blade propeller and three-point gear.',
         'Native 2x reduction, no manual half-resolution edits; static propeller and landing gear.'])


def airport_tug():
    g = Grid((80, 128, 72), PALETTE)
    g.roundbox((13, 40, 15), (67, 121, 29), 4, 4)
    g.roundbox((17, 43, 27), (63, 117, 35), 4, 1)
    for x in (14, 66):
        for y in (60, 104):
            tire(g, (x, y, 12), 11.5, 11)
            g.roundbox((x-6, y-11, 24), (x+6, y+11, 29), 2, 4)
    # Distinct forward cab with broad tall glazing and a compact beacon.
    g.roundbox((22, 49, 31), (59, 78, 63), 3, 1)
    g.roundbox((26, 47, 39), (55, 51, 58), 2, 11)
    g.box((28, 46, 52), (53, 49, 57), 12)
    g.box((39, 46, 39), (42, 50, 58), 6)
    g.roundbox((57, 54, 39), (61, 74, 58), 2, 11)
    g.box((59, 56, 52), (62, 72, 57), 12)
    g.box((59, 62, 39), (62, 65, 58), 6)
    g.roundbox((20, 46, 61), (62, 80, 66), 2, 2)
    g.box((60, 63, 33), (64, 76, 38), 7)
    g.box((61, 71, 39), (64, 76, 41), 10)
    g.cylinder((41, 62, 66), 4, 3, 2, 10)
    g.cylinder((41, 62, 69), 3, 6, 2, 8)
    # Low hood, headlamps, steps and rear power enclosure.
    g.roundbox((17, 41, 29), (63, 51, 37), 3, 2)
    g.box((28, 39, 25), (53, 42, 32), 10)
    for z in (26, 29):
        g.box((30, 38, z), (51, 40, z+1), 6)
    for x in (21, 57):
        g.box((x-4, 39, 27), (x+4, 43, 34), 7)
        g.box((x-2, 38, 29), (x+2, 40, 33), 17)
    g.roundbox((12, 36, 16), (68, 43, 23), 2, 13)
    g.roundbox((22, 84, 34), (59, 118, 45), 3, 10)
    g.roundbox((24, 85, 43), (58, 117, 48), 2, 13)
    g.box((48, 106, 47), (52, 110, 59), 10)
    g.box((61, 110, 27), (66, 121, 40), 7)
    g.box((14, 110, 27), (19, 121, 40), 7)
    for z in (22, 27):
        g.box((61, 78, z), (72, 85, z+2), 13)
    # Front tow coupling, articulated towbar and its own small support wheel.
    g.roundbox((34, 34, 12), (46, 41, 23), 2, 10)
    g.cylinder((40, 34, 18), 3.5, 4, 1, 13)
    g.beam((40, 36, 17), (40, 13, 11), 2.8, 7)
    g.torus((40, 7, 11), 4, 2, 2, 8)
    g.beam((40, 11, 11), (40, 15, 11.5), 2.3, 7)
    g.box((38, 20, 5), (42, 24, 13), 13)
    tire(g, (40, 22, 5), 4.5, 6)
    return Asset('airport_tug', 'Airport tug', g, .05,
        ['Low aviation tug with tall opaque cab glass, beacon, compact rear power cover and four main tires.',
         'Connected front towbar has a genuinely open coupling eye and a separate support wheel; static geometry.',
         'Native 2x reduction, no manual half-resolution edits.'])


def maintenance_hangar():
    g = Grid((128, 112, 104), PALETTE)
    # A real structural slab occupies only the building footprint.
    g.roundbox((8, 12, 0), (120, 109, 4), 2, 15)
    arch = 68 + 31*np.sqrt(np.maximum(0, 1-((g.x-64)/60)**2))
    extent = (g.x>=4)&(g.x<124)&(g.y>=14)&(g.y<110)
    roof = extent & (g.z<=arch+2) & (g.z>=arch-3)
    g.data[roof] = 4
    g.data[roof & ((np.floor(g.y).astype(int)//9)%4 == 0)] = 5
    insideheight = g.z<arch-3
    side = (((g.x>=8)&(g.x<15))|((g.x>=113)&(g.x<120))) & (g.y>=18)&(g.y<106)&(g.z>=4)&insideheight
    rear = (g.x>=14)&(g.x<114)&(g.y>=103)&(g.y<109)&(g.z>=4)&insideheight
    fascia = (g.x>=13)&(g.x<115)&(g.y>=15)&(g.y<21)&(g.z>=69)&insideheight
    g.data[side|rear|fascia] = 1
    g.data[(side|rear) & ((np.floor(g.z).astype(int)//10)%5==0)] = 2
    # Full-width, permanently open portal; no door panel or facade sealing it.
    for x in (15, 113):
        g.roundbox((x-4, 12, 3), (x+4, 23, 70), 1.5, 13)
        g.box((x-4, 11, 8), (x+4, 13, 28), 7)
    g.box((11, 12, 65), (117, 23, 71), 13)
    g.box((12, 10, 67), (116, 13, 71), 7)
    # Upper facade glass and visible right-side windows.
    g.box((51, 13, 78), (77, 17, 88), 3)
    g.box((53, 12, 80), (75, 15, 86), 11)
    for x in (59, 67):
        g.box((x, 11, 79), (x+2, 15, 87), 13)
    for y in (45, 67, 89):
        g.box((117, y-7, 38), (121, y+8, 50), 3)
        g.box((119, y-5, 40), (122, y+6, 48), 11)
        g.box((120, y-4, 44), (122, y+5, 47), 12)
        g.box((120, y, 39), (122, y+2, 49), 13)
    g.box((119, 26, 5), (122, 38, 33), 4)
    g.box((121, 34, 17), (124, 37, 20), 7)
    g.roundbox((117, 23, 33), (125, 41, 37), 1.5, 5)
    # Interior ribs, workbench and parked tools hug the rear wall.
    for y in (43, 74, 101):
        g.box((15, y, 5), (18, y+3, 76), 3)
        g.box((110, y, 5), (113, y+3, 76), 3)
    for x in (25, 52):
        g.box((x, 90, 4), (x+4, 101, 23), 10)
    g.box((23, 89, 23), (58, 102, 27), 18)
    g.box((25, 92, 27), (36, 100, 33), 13)
    g.roundbox((87, 84, 4), (105, 101, 25), 2, 4)
    for z in (10, 17):
        g.box((90, 82, z), (102, 85, z+2), 13)
    g.box((69, 95, 4), (81, 104, 18), 7)
    g.box((72, 95, 18), (84, 104, 31), 1)
    # Two non-emissive palette luminaires are attached to the roof interior.
    for y in (47, 78):
        g.box((49, y-5, 92), (77, y+5, 96), 10)
        g.box((51, y-4, 90), (75, y+4, 93), 17)
    for x in (21, 105):
        g.box((x, 14, 4), (x+2, 38, 6), 7)
    return Asset('maintenance_hangar', 'Open maintenance hangar', g, .05,
        ['Broad arched native roof above a genuinely empty front maintenance bay. Structural floor, portal posts, rear workbench and service door are part of the building.',
         'Upper and side windows use opaque glazing palette colors. Palette luminaires do not emit light.',
         'No hidden door panel; native 2x reduction with no manual half-resolution edits.'])


def octagonal(g, center, half, chamfer, lowz, highz, color):
    xx, yy = np.abs(g.x-center[0]), np.abs(g.y-center[1])
    mask = (xx<half)&(yy<half)&(xx+yy<2*half-chamfer)&(g.z>=lowz)&(g.z<highz)
    g.data[mask] = color
    return mask


def control_tower():
    g = Grid((92, 92, 128), PALETTE)
    g.roundbox((19, 25, 0), (73, 76, 9), 4, 16)
    taper = 20 - np.clip((g.z-9)/58, 0, 1)*3
    xx, yy = np.abs(g.x-46), np.abs(g.y-48)
    stem = (xx<taper)&(yy<taper)&(xx+yy<2*taper-5)&(g.z>=8)&(g.z<69)
    g.data[stem] = 1
    g.data[stem & ((np.floor(g.z).astype(int)//10)%5==0)] = 2
    # Front stair and door stand below the mast, not around it as a diorama.
    for i in range(5):
        g.box((36, 7+i*4, 0), (56, 11+i*4, 2+i*2), 15)
    g.box((37, 26, 8), (55, 30, 31), 3)
    g.box((40, 25, 9), (52, 29, 29), 4)
    g.box((49, 24, 18), (52, 27, 20), 7)
    g.box((38, 25, 31), (54, 29, 34), 2)
    g.box((42, 24, 31), (50, 27, 33), 17)
    for x in (33, 59):
        g.beam((x, 11, 5), (x, 27, 15), 1.1, 13)
        g.box((x-1, 25, 8), (x+1, 28, 17), 13)
    g.box((62, 40, 39), (65, 51, 51), 3)
    g.box((64, 42, 41), (66, 49, 49), 11)
    # Low balcony rail; glazing starts above it to avoid window occlusion.
    octagonal(g, (46, 48), 36, 11, 66, 71, 1)
    octagonal(g, (46, 48), 34, 11, 69, 73, 2)
    octagonal(g, (46, 48), 26, 8, 71, 79, 6)
    octagonal(g, (46, 48), 27, 9, 75, 79, 1)
    # Panoramic cab tapers outward to a shallow-overhang roof.
    width = 25+(g.z-79)*6/24
    cabmask = octagonal(g, (46, 48), width, 9, 79, 103, 11)
    g.data[cabmask & (g.z>=91)&(g.z<96)] = 12
    for x0, x1 in ((30, 27), (46, 46), (62, 65)):
        g.beam((x0, 23, 79), (x1, 17, 103), 1.5, 6)
    for y0, y1 in ((32, 29), (48, 48), (64, 67)):
        g.beam((71, y0, 79), (77, y1, 103), 1.5, 6)
    octagonal(g, (46, 48), 34, 10, 102, 106, 1)
    octagonal(g, (46, 48), 34, 10, 106, 110, 4)
    # Railing's top is 77, below the start of the large blue window band at 79.
    perimeter = [(21,14),(71,14),(80,23),(80,73),(71,82),(21,82),(12,73),(12,23)]
    for i, p in enumerate(perimeter):
        q = perimeter[(i+1)%len(perimeter)]
        g.beam((p[0],p[1],76), (q[0],q[1],76), 1, 13)
        g.box((p[0]-1,p[1]-1,70),(p[0]+1,p[1]+1,78),13)
    # Roof hardware stays behind the front cab and has no decorative motifs.
    g.roundbox((40, 48, 110), (52, 59, 116), 2, 10)
    g.cylinder((46, 54, 120), 1.7, 12, 2, 13)
    g.cylinder((46, 54, 126), 2.3, 3, 2, 8)
    g.box((55, 54, 112), (58, 58, 121), 13)
    g.roundbox((51, 53, 116), (64, 58, 123), 2, 14)
    for x, y in ((24,28),(68,68)):
        g.cylinder((x,y,112),2,5,2,7)
    return Asset('control_tower', 'Airfield control tower', g, .05,
        ['Tapered ivory tower, stepped front entry, low octagonal balcony rail and broad outward-tapering panoramic opaque glazing.',
         'Roof overhang is shallow; window band begins above railing. Native saved-grid visibility rays check the shared camera direction.',
         'Static roof radio hardware; native 2x reduction with no manual half-resolution edits.'])


def make_assets():
    return [propeller_plane(), airport_tug(), maintenance_hangar(), control_tower()]


if __name__ == '__main__':
    run_theme(Path(__file__).resolve().parent, make_assets())
