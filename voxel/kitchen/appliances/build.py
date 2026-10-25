"""Newly authored kitchen appliance voxels. Pure make_assets(); no exporters."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '_tools'))
from voxelkit import Grid, Asset

PALETTE = [
    (0, 0, 0, 0), (232, 225, 205, 255), (121, 151, 133, 255),
    (75, 105, 91, 255), (181, 130, 78, 255), (217, 176, 113, 255),
    (48, 56, 57, 255), (156, 170, 170, 255), (91, 108, 112, 255),
    (92, 133, 145, 255), (244, 239, 225, 255), (191, 105, 70, 255),
    (35, 42, 44, 255), (217, 164, 85, 255), (151, 94, 48, 255),
    (203, 183, 106, 255),
]


def double_door_fridge():
    g = Grid((88, 76, 128), PALETTE)
    g.roundbox((6, 18, 6), (82, 74, 126), 6, 1)
    g.box((12, 20, 2), (22, 34, 8), 6)
    g.box((66, 20, 2), (76, 34, 8), 6)
    g.box((12, 56, 2), (22, 70, 8), 6)
    g.box((66, 56, 2), (76, 70, 8), 6)
    g.roundbox((8, 14, 14), (42, 24, 122), 4, 10)
    g.roundbox((46, 14, 14), (80, 24, 122), 4, 10)
    # A true recessed door seam separates the two fronts.
    g.box((42, 12, 16), (46, 20, 120), 0)
    g.box((10, 14, 8), (78, 20, 14), 2)
    for x in (32, 50):
        g.roundbox((x, 4, 56), (x + 6, 10, 106), 2, 3)
        g.box((x, 8, 56), (x + 6, 18, 62), 3)
        g.box((x, 8, 100), (x + 6, 18, 106), 3)
    g.roundbox((13, 12, 94), (27, 15, 110), 2, 9)
    g.box((16, 10, 100), (24, 12, 104), 15)
    return Asset('double_door_fridge', 'Double-door fridge', g, .016,
                 ['Two closed vertical doors; separate stepped pulls with air behind each grip.',
                  'Sage toe plinth, small opaque temperature display; no modeled lettering.',
                  'Occupied height approximately 1.98 m. No half postprocess.'])


def range_oven():
    g = Grid((96, 88, 128), PALETTE)
    g.roundbox((6, 16, 8), (90, 84, 106), 5, 1)
    for x in (12, 76):
        for y in (22, 68):
            g.box((x, y, 2), (x + 8, y + 10, 12), 6)
    g.roundbox((6, 14, 102), (90, 86, 110), 3, 2)
    g.roundbox((8, 76, 108), (88, 86, 126), 4, 1)
    g.box((37, 73, 114), (59, 77, 122), 6)
    g.box((42, 71, 116), (54, 73, 120), 15)
    # Four independent burner bowls with raised pan-rest crosses.
    for x in (28, 68):
        for y in (34, 62):
            g.cylinder((x, y, 111), 12, 6, 2, 6)
            g.cylinder((x, y, 114), 7, 4, 2, 8)
            g.box((x - 15, y - 2, 114), (x + 15, y + 2, 118), 6)
            g.box((x - 2, y - 15, 114), (x + 2, y + 15, 118), 6)
    g.roundbox((12, 10, 22), (84, 18, 84), 4, 6)
    g.roundbox((16, 8, 26), (80, 14, 80), 3, 1)
    g.roundbox((22, 6, 34), (74, 10, 68), 4, 9)
    g.box((28, 4, 58), (64, 6, 62), 7)
    # Oven pull is attached at its ends; its center is not fused to the door.
    g.roundbox((20, 0, 76), (76, 4, 82), 2, 3)
    g.box((20, 2, 76), (26, 16, 82), 3)
    g.box((70, 2, 76), (76, 16, 82), 3)
    for x in (22, 40, 58, 76):
        g.cylinder((x, 10, 94), 6, 8, 1, 7)
        g.box((x - 2, 4, 94), (x + 2, 7, 100), 6)
    g.box((16, 12, 12), (80, 16, 18), 2)
    return Asset('range_oven', 'Range and oven', g, .008,
                 ['Four burner bowls with chunky pan rests; opaque blue-gray oven window.',
                  'Free space behind the oven pull. Four feet and rear control riser.',
                  'Occupied height approximately 0.99 m. No half postprocess.'])


def microwave():
    g = Grid((128, 92, 80), PALETTE)
    g.roundbox((6, 14, 10), (122, 88, 74), 7, 1)
    for x in (18, 104):
        for y in (24, 72):
            g.box((x, y, 4), (x + 8, y + 10, 12), 6)
    g.roundbox((10, 10, 16), (94, 18, 68), 4, 6)
    g.roundbox((16, 10, 22), (88, 14, 62), 4, 9)
    g.box((22, 8, 54), (72, 10, 58), 7)
    # The right-side grip stands forward of the opaque window.
    g.roundbox((82, 2, 22), (88, 6, 62), 2, 3)
    g.box((82, 4, 22), (88, 12, 28), 3)
    g.box((82, 4, 56), (88, 12, 62), 3)
    g.roundbox((98, 10, 50), (116, 14, 66), 2, 6)
    g.box((102, 8, 56), (112, 10, 62), 15)
    g.cylinder((107, 9, 38), 7, 6, 1, 7)
    g.box((105, 4, 38), (109, 6, 44), 6)
    g.roundbox((100, 8, 20), (114, 12, 28), 2, 2)
    # Actual inset ventilation openings on the visible right side.
    for y in (32, 44, 56, 68):
        g.box((114, y, 28), (124, y + 4, 54), 0)
    return Asset('microwave', 'Microwave', g, .0048,
                 ['Cream enclosure, opaque window, inset screen and rotary control.',
                  'The pull has an air gap; four side vents are empty native pockets.',
                  'Occupied width approximately 0.56 m. No half postprocess.'])


def dishwasher():
    g = Grid((96, 128, 112), PALETTE)
    # One static open dishwasher, including its horizontal front door.
    g.roundbox((6, 58, 6), (90, 126, 110), 5, 1)
    g.box((14, 54, 18), (82, 116, 102), 0)
    g.box((14, 116, 18), (82, 120, 102), 8)
    g.box((14, 58, 16), (82, 116, 22), 8)
    g.box((10, 56, 18), (14, 120, 104), 6)
    g.box((82, 56, 18), (86, 120, 104), 6)
    g.box((14, 56, 100), (82, 120, 104), 6)
    g.roundbox((8, 6, 6), (88, 62, 18), 4, 1)
    g.roundbox((14, 12, 16), (82, 56, 22), 3, 8)
    g.roundbox((58, 22, 20), (76, 38, 25), 2, 10)
    g.box((62, 26, 24), (72, 34, 28), 2)
    g.box((22, 8, 20), (54, 14, 24), 6)
    for x in (30, 42):
        g.box((x, 8, 24), (x + 6, 12, 28), 15)
    # Two open wire racks, not solid shelves.
    for z in (34, 72):
        g.box((14, 60, z), (82, 64, z + 6), 7)
        g.box((14, 112, z), (82, 116, z + 6), 7)
        g.box((14, 60, z), (18, 116, z + 6), 7)
        g.box((78, 60, z), (82, 116, z + 6), 7)
        for x in (16, 28, 40, 52, 64, 76):
            g.box((x, 64, z), (x + 4, 116, z + 4), 7)
        for y in (64, 76, 88, 100, 112):
            g.box((18, y, z), (78, y + 4, z + 4), 7)
        for x in (14, 78):
            g.box((x, 60, z), (x + 4, 64, z + 14), 7)
            g.box((x, 112, z), (x + 4, 116, z + 14), 7)
        g.box((14, 60, z + 10), (82, 64, z + 14), 7)
    for x in (28, 44, 60):
        g.cylinder((x, 94, 50), 14, 4, 0, 10)
        g.cylinder((x + 2, 94, 50), 9, 2, 0, 2)
    # Two small cups on the upper rack with visibly empty tops.
    for x in (32, 60):
        g.cylinder((x, 90, 86), 9, 20, 2, 10)
        g.cylinder((x, 90, 90), 5, 16, 2, 0)
    return Asset('dishwasher', 'Open dishwasher', g, .008,
                 ['Static open pose with lowered door, detergent recess and two true open wire racks.',
                  'Three plates in lower rack; two cups have hollow tops in upper rack.',
                  'Occupied height approximately 0.83 m; door is intentionally open. No half postprocess.'])


def range_hood():
    g = Grid((128, 80, 104), PALETTE)
    t = (g.z - 14) / 36
    canopy = ((g.z >= 14) & (g.z < 50) &
              (abs(g.x - 64) <= 62 - 40 * t) &
              (abs(g.y - 44) <= 32 - 14 * t))
    g.data[canopy] = 1
    g.roundbox((2, 12, 12), (126, 78, 22), 4, 2)
    g.box((22, 24, 10), (106, 66, 24), 0)
    # A sparse removable filter lies within the underside opening.
    for x in range(22, 108, 12):
        g.box((x, 24, 16), (x + 4, 66, 20), 8)
    for y in (26, 44, 62):
        g.box((18, y, 16), (110, y + 4, 20), 8)
    g.roundbox((42, 28, 46), (86, 66, 104), 4, 1)
    g.box((50, 36, 22), (78, 58, 106), 0)
    g.box((40, 26, 98), (88, 68, 104), 2)
    g.box((50, 36, 98), (78, 58, 106), 0)
    g.roundbox((22, 10, 18), (106, 16, 28), 3, 1)
    for x in (76, 86, 96):
        g.box((x, 8, 20), (x + 4, 12, 24), 6)
    g.box((28, 8, 20), (36, 12, 24), 15)
    return Asset('range_hood', 'Range hood', g, .0072,
                 ['Flared canopy with sage lower lip and an open chimney duct.',
                  'Underside has a real void and sparse filter bars, not a painted cavity.',
                  'Occupied width approximately 0.89 m. No half postprocess.'])


def rice_cooker():
    g = Grid((112, 112, 128), PALETTE)
    for x in (24, 76):
        for y in (28, 82):
            g.roundbox((x, y, 4), (x + 12, y + 12, 18), 3, 6)
    g.ellipsoid((56, 60, 28), (46, 44, 18), 2)
    g.cylinder((56, 60, 54), 46, 56, 2, 1)
    g.ellipsoid((56, 60, 80), (46, 46, 20), 1)
    g.cylinder((56, 60, 96), 46, 8, 2, 3)
    g.ellipsoid((56, 60, 100), (47, 45, 10), 1)
    g.roundbox((34, 10, 42), (78, 18, 64), 4, 2)
    g.roundbox((46, 8, 52), (66, 12, 60), 2, 6)
    g.box((50, 6, 54), (62, 8, 58), 15)
    g.box((40, 8, 44), (46, 12, 48), 10)
    g.box((66, 8, 44), (72, 12, 48), 11)
    # Lifted carry handle with visible air through its center.
    g.roundbox((24, 52, 100), (88, 68, 126), 7, 3)
    g.roundbox((32, 48, 106), (80, 72, 120), 4, 0)
    g.cylinder((80, 80, 109), 7, 6, 2, 8)
    g.box((78, 78, 110), (82, 82, 114), 12)
    g.roundbox((46, 28, 104), (66, 38, 112), 3, 2)
    return Asset('rice_cooker', 'Rice cooker', g, .0028,
                 ['Closed oval cooker with sage base, lid seam, steam valve and simple front controls.',
                  'Upright carry handle has a native through-gap; the lid is a static closed pose.',
                  'Occupied height approximately 0.34 m. No half postprocess.'])


def electric_kettle():
    g = Grid((128, 96, 128), PALETTE)
    g.cylinder((56, 56, 8), 36, 10, 2, 6)
    g.cylinder((56, 56, 14), 34, 8, 2, 2)
    g.ellipsoid((56, 56, 32), (35, 32, 20), 1)
    g.cylinder((56, 56, 56), 34, 52, 2, 1)
    g.ellipsoid((56, 56, 80), (34, 32, 20), 1)
    # Right-hand loop stays chunky enough for half-grid reduction.
    g.roundbox((84, 46, 28), (124, 62, 102), 10, 3)
    g.roundbox((92, 42, 38), (116, 66, 90), 7, 0)
    # Rising front-left spout, with a real open channel into the vessel.
    g.beam((34, 35, 63), (16, 14, 92), 10, 1)
    g.ellipsoid((56, 56, 61), (26, 24, 27), 0)
    g.beam((42, 43, 59), (14, 12, 100), 5.5, 0)
    g.cylinder((56, 56, 98), 26, 6, 2, 3)
    g.ellipsoid((56, 56, 102), (25, 25, 6), 1)
    g.roundbox((48, 48, 106), (64, 64, 116), 4, 3)
    g.roundbox((86, 48, 20), (102, 60, 28), 3, 11)
    g.roundbox((46, 20, 38), (66, 24, 74), 3, 9)
    for z in (46, 58, 70):
        g.box((50, 18, z), (60, 20, z + 4), 7)
    return Asset('electric_kettle', 'Electric kettle', g, .00265,
                 ['Cream kettle on charcoal power base; open rising spout and sage loop handle.',
                  'Hollow vessel and spout channel are native voids; opaque water gauge.',
                  'Occupied height approximately 0.30 m. No half postprocess.'])


def make_assets():
    return [double_door_fridge(), range_oven(), microwave(), dishwasher(),
            range_hood(), rice_cooker(), electric_kettle()]


if __name__ == '__main__':
    for asset in make_assets():
        print(asset.slug, asset.grid.shape, asset.voxel_size)
