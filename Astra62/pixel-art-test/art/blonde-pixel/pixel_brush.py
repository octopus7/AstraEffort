"""Palette and native-grid drawing primitives for the blonde pixel archer."""

import math

from PIL import ImageDraw


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


def ip(point):
    return tuple(math.floor(value + .5) for value in point)


class Brush:
    def __init__(self, image, coordinates=None, palette=PALETTE):
        self.draw = ImageDraw.Draw(image)
        self.coordinates = coordinates or (lambda points: points)
        self.palette = palette

    def pixels(self, points):
        return [ip(point) for point in self.coordinates(points)]

    def p(self, fill, points, edge=None):
        self.draw.polygon(self.pixels(points), fill=self.palette[fill],
                          outline=self.palette[edge] if edge else None)

    def l(self, fill, points, width=1):
        self.draw.line(self.pixels(points), fill=self.palette[fill], width=width)

    def d(self, fill, *points):
        self.draw.point(self.pixels(points), fill=self.palette[fill])
