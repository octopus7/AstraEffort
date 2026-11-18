"""Export the twelve-frame pixel scene as a four-times, nearest-neighbor APNG."""

from pathlib import Path

from PIL import Image, ImageDraw


ASSETS = Path(__file__).resolve().parents[2] / "assets"


def build_scene_preview():
    with Image.open(ASSETS / "blonde-pixel-ruins.png") as image:
        plate = image.convert("RGBA")
    with Image.open(ASSETS / "blonde-pixel-walk-12.png") as image:
        sheet = image.convert("RGBA")
    if plate.size != (208, 117) or sheet.size != (768, 64):
        raise ValueError("Expected a 208 × 117 scene and twelve 64 × 64 cells.")

    # Mirror the three native rows of the contact shadow in the scene stylesheet.
    shadow = Image.new("RGBA", plate.size)
    draw = ImageDraw.Draw(shadow)
    for y, left, right in [(89, 51, 62), (90, 47, 66), (91, 51, 62)]:
        draw.line((left, y, right, y), fill=(60, 52, 63, 64))
    plate.alpha_composite(shadow)

    frames = []
    for index in range(12):
        frame = plate.copy()
        cell = sheet.crop((index * 64, 0, (index + 1) * 64, 64))
        frame.alpha_composite(cell, (25, 31))
        frames.append(frame.convert("RGB").resize((832, 468), Image.Resampling.NEAREST))
    ticks = [round(index * 1000 / 12) for index in range(13)]
    durations = [end - start for start, end in zip(ticks, ticks[1:])]
    frames[0].save(ASSETS / "blonde-pixel-scene-preview.png", save_all=True,
                   append_images=frames[1:], duration=durations, loop=0, blend=0, disposal=0)


if __name__ == "__main__":
    build_scene_preview()
