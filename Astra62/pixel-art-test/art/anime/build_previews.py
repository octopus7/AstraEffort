from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image


ART = Path(__file__).resolve().parent
ASSETS = ART.parent.parent / 'assets'
PARTS = ('body', 'far-arm-bow', 'near-arm', 'cape-back', 'cape-front')


def render_layer_thumbnails(destination):
    tile = 384
    atlas = Image.new('RGBA', (tile * len(PARTS), tile))
    for index, name in enumerate(PARTS):
        with Image.open(ART / 'layers' / f'{name}.png') as source:
            layer = source.convert('RGBA')
        bounds = layer.getchannel('A').point(lambda a: 255 if a >= 10 else 0).getbbox()
        if bounds is None:
            raise ValueError(f'Empty layer: {name}')
        detail = layer.crop(bounds)
        detail.thumbnail((tile - 30, tile - 30), Image.Resampling.LANCZOS)
        offset = (index * tile + (tile - detail.width) // 2, (tile - detail.height) // 2)
        atlas.alpha_composite(detail, offset)
    atlas.save(destination, optimize=True)


def render_scene_preview(destination):
    with Image.open(ASSETS / 'anime-ruins.png') as source:
        width = 920
        height = round(source.height * width / source.width)
        background = source.convert('RGB').resize((width, height), Image.Resampling.LANCZOS)

    # These match the sprite and its ground shadow in the scene stylesheet.
    box = round(height * .545)
    feet_x, feet_y = width * .276, height * .777
    position = (round(feet_x - box / 2), round(feet_y - box * .9375))
    y, x = np.ogrid[:height, :width]
    radius = np.sqrt(((x - feet_x) / (.050 * width)) ** 2 + ((y - feet_y) / (.006 * height)) ** 2)
    shadow = Image.fromarray((70 * np.clip(1 - radius, 0, 1)).astype('uint8'))
    background.paste('#75592d', (0, 0, width, height), shadow)

    frames = []
    with Image.open(ASSETS / 'anime-walk-12-hd.png') as source:
        sheet = source.convert('RGBA')
    count = 12
    size = sheet.height
    if sheet.width != count * size:
        raise ValueError('The twelve-frame sheet must contain twelve square cells.')
    for index in range(count):
        cell = sheet.crop((index * size, 0, (index + 1) * size, size))
        character = cell.resize((box, box), Image.Resampling.LANCZOS)
        frame = background.copy()
        frame.paste(character, position, character)
        frames.append(frame)
    ticks = [round(index * 1000 / count) for index in range(count + 1)]
    durations = [end - start for start, end in zip(ticks, ticks[1:])]
    frames[0].save(destination, save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, disposal=0, blend=0, optimize=True)


def build_previews():
    with TemporaryDirectory(dir=ASSETS) as directory:
        atlas = Path(directory) / 'anime-layer-previews.png'
        scene = Path(directory) / 'anime-scene-preview.png'
        render_layer_thumbnails(atlas)
        render_scene_preview(scene)
        atlas.replace(ASSETS / atlas.name)
        scene.replace(ASSETS / scene.name)


if __name__ == '__main__':
    build_previews()
