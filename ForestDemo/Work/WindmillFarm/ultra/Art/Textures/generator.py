"""Original deterministic WindmillFarm surface art. No external image inputs.

Run using the bundled Python with Pillow and numpy. Every signal is periodic
on a unit torus; normals use wrapped finite differences. PNGs are 1024 square.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SIZE = 1024
SEED = 2026102201
TAU = 2.0 * np.pi
Y, X = np.mgrid[0:SIZE, 0:SIZE] / SIZE
FX = np.fft.fftfreq(SIZE)[None, :] * SIZE
FY = np.fft.fftfreq(SIZE)[:, None] * SIZE
START = datetime.now(timezone.utc)


def field(seed: int, xfreq: float, yfreq: float | None = None) -> np.ndarray:
    """Smooth zero-mean periodic random field; bandwidth is cycles per tile."""
    if yfreq is None:
        yfreq = xfreq
    rng = np.random.default_rng(SEED + seed)
    white = rng.standard_normal((SIZE, SIZE))
    kernel = np.exp(-0.5 * ((FX / xfreq) ** 2 + (FY / yfreq) ** 2))
    kernel[0, 0] = 0.0
    result = np.fft.ifft2(np.fft.fft2(white) * kernel).real
    result /= result.std() + 1e-12
    return np.tanh(result * 0.65)


def color(base: tuple[int, int, int], value: np.ndarray,
          tint: tuple[float, float, float] = (1., .93, .80),
          second: np.ndarray | None = None,
          second_tint: tuple[float, float, float] = (1., 1., 1.)) -> np.ndarray:
    rgb = np.array(base, dtype=float)[None, None, :] + value[..., None] * np.array(tint)
    if second is not None:
        rgb += second[..., None] * np.array(second_tint)
    return np.uint8(np.clip(np.rint(rgb), 0, 255))


def wood(seed: int, light: bool = False):
    long = field(seed, 26, 1.5)
    cloud = field(seed + 1, 4)
    warp = .42 * field(seed + 2, 3, 2) + .14 * np.sin(TAU * Y * 2)
    broad = np.sin(TAU * (X * 12 + warp))
    fine = np.sin(TAU * (X * 79 + warp * 1.9))
    fibers = field(seed + 3, 150, 8)
    dark_lines = np.maximum(0., broad - .37) ** 2
    height = .55 * long + .18 * fibers - .21 * dark_lines + .09 * fine
    value = 7.5 * long + 3.5 * cloud + 2.2 * fibers - 8.0 * dark_lines
    base = (153, 136, 109) if light else (110, 96, 79)
    return color(base, value, (1., .94, .83)), .80 + .045 * cloud - .025 * fibers, height


def stone(seed: int):
    cloud, round_mottle = field(seed, 4), field(seed + 1, 21)
    grain = field(seed + 2, 115)
    pores = np.maximum(0., field(seed + 3, 60) - .64) ** 2
    height = .35 * cloud + .5 * round_mottle + .10 * grain - .65 * pores
    rgb = color((144, 140, 126), 5.5 * cloud + 6.0 * round_mottle + 1.7 * grain - 19 * pores,
                (.95, .96, .88), second=2.8 * field(seed + 4, 7), second_tint=(1., .45, -.5))
    return rgb, .86 + .04 * round_mottle + .025 * grain, height


def plaster(seed: int):
    clouds, trowel, sand = field(seed, 3), field(seed + 1, 13, 8), field(seed + 2, 150)
    height = .18 * clouds + .25 * trowel + .19 * sand
    return color((195, 184, 153), 4.3 * clouds + 2.8 * trowel + 1.8 * sand), .88 + .025 * trowel + .025 * sand, height


def roof(seed: int):
    clay, wear, grit = field(seed, 8), field(seed + 1, 3), field(seed + 2, 160)
    kiln = field(seed + 3, 2, 18)
    height = .4 * clay + .2 * kiln + .19 * grit
    return color((145, 97, 76), 7.2 * clay + 4.1 * wear + 1.8 * grit,
                 (1., .75, .65), second=3.0 * kiln, second_tint=(.6, .8, .8)), .84 + .04 * clay + .025 * grit, height


def iron(seed: int):
    cloud, streaks = field(seed, 6), field(seed + 1, 60, 5)
    patina = np.maximum(0., field(seed + 2, 19) - .35)
    grain = field(seed + 3, 190)
    height = .12 * cloud + .18 * streaks + .23 * grain + .2 * patina
    return color((67, 71, 70), 3.5 * cloud + 1.8 * streaks + 1.2 * grain,
                 (1., 1., 1.), second=patina * 9, second_tint=(1., .65, .30)), .67 + .07 * cloud + .06 * patina, height


def canvas(seed: int):
    warp = np.sin(TAU * X * 128)
    weft = np.sin(TAU * Y * 128)
    weave = .5 * warp + .5 * weft + .28 * warp * weft
    slubs = field(seed, 50, 4) + field(seed + 1, 4, 50)
    cloud = field(seed + 2, 4)
    height = .5 * weave + .07 * slubs
    return color((212, 204, 176), 2.0 * weave + 1.5 * slubs + 3.5 * cloud), .92 + .025 * weave + .015 * cloud, height


def glass(seed: int):
    cloud, waviness = field(seed, 4), field(seed + 1, 18, 2)
    return color((66, 88, 95), 2.6 * cloud + 1.1 * waviness, (.6, .9, 1.)), .27 + .025 * cloud, .5 * cloud + .1 * waviness


def hay(seed: int):
    warp = .12 * field(seed, 3, 7)
    fine = np.sin(TAU * (X * 94 + Y * 7 + warp))
    strands = field(seed + 1, 110, 7)
    bundle = field(seed + 2, 15, 3)
    cloud = field(seed + 3, 5)
    height = .24 * fine + .6 * strands + .20 * bundle
    return color((183, 166, 112), 6.0 * strands + 4.0 * bundle + 2.0 * fine + 2.2 * cloud), .90 + .035 * strands, height


def leaf(seed: int):
    cloud, cells = field(seed, 4), field(seed + 1, 50)
    thin_veins = np.maximum(0., np.sin(TAU * (12 * X + 6 * Y)) - .70) ** 2
    height = .15 * cells + .5 * thin_veins + .09 * cloud
    return color((112, 131, 87), 4.7 * cloud + 1.3 * cells + 9.0 * thin_veins,
                 (.82, 1., .58)), .77 + .035 * cloud + .015 * cells, height


def soil(seed: int):
    broad, clumps = field(seed, 4), field(seed + 1, 27)
    grit = field(seed + 2, 150)
    speckle = np.maximum(0., field(seed + 3, 85) - .55)
    height = .28 * broad + .6 * clumps + .2 * grit + .2 * speckle
    return color((123, 109, 83), 4.0 * broad + 5.2 * clumps + 2.0 * grit + 4.0 * speckle), .94 + .025 * clumps, height


SLOTS = [
    ('Wood', lambda: wood(10), .20, 'Vertical weathered walnut grain; align V with timber length.', 1., .0),
    ('WoodLight', lambda: wood(20, True), .18, 'Vertical pale weathered timber grain; align V with timber length.', 1., .0),
    ('Stone', lambda: stone(30), .20, 'Rounded mineral cloud, small pores and grains; no baked mortar.', 1., .0),
    ('Plaster', lambda: plaster(40), .12, 'Muted ochre trowel clouds and fine sand.', 1., .0),
    ('Roof', lambda: roof(50), .17, 'Faded warm terracotta kiln variation; tile geometry supplies courses.', 1., .0),
    ('Iron', lambda: iron(60), .10, 'Rough dark iron, faint drawn streaks and sparse muted patina.', .7, .85),
    ('Canvas', lambda: canvas(70), .16, 'Flax plain weave with yarn slubs; no shading painted in.', .75, .0),
    ('Glass', lambda: glass(80), .025, 'Low contrast bluegrey uneven old glass; opacity left to shader.', .5, .0),
    ('Hay', lambda: hay(90), .20, 'Ochre bundled fibers; align V with straw length.', 1., .0),
    ('Leaf', lambda: leaf(100), .07, 'Sage cellular variation and understated periodic diagonal veins.', .65, .0),
    ('Soil', lambda: soil(110), .20, 'Muted earth with soft clumps and fine grit; no landscape atlas.', 1., .0),
]


def normal(height: np.ndarray, target_slope: float):
    # Texture V increases downward. DirectX green follows +dH/dV and red -dH/dU.
    du = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * .5
    dv = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * .5
    slope = np.sqrt(du * du + dv * dv)
    scale = target_slope / (np.percentile(slope, 95) + 1e-12)
    nx, ny = -du * scale, dv * scale
    nz = np.ones_like(nx)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    vector = np.stack([nx / length, ny / length, nz / length], axis=-1)
    png = np.uint8(np.clip(np.rint((vector * .5 + .5) * 255), 0, 255))
    return png, {'target_gradient_magnitude_p95': target_slope,
                 'actual_gradient_magnitude_p95': float(np.percentile(slope * scale, 95)),
                 'max_tilt_degrees': float(np.degrees(np.arctan((slope * scale).max())))}


def edge_test(array: np.ndarray):
    a = array.astype(float)
    if a.ndim == 2:
        a = a[..., None]
    dx, dy = np.abs(np.diff(a, axis=1)), np.abs(np.diff(a, axis=0))
    seamx = np.abs(a[:, 0] - a[:, -1])
    seamy = np.abs(a[0] - a[-1])
    metrics = {}
    for axis, seam, inner in [('u', seamx, dx), ('v', seamy, dy)]:
        mean, ref = float(seam.mean()), float(inner.mean())
        ratio = mean / max(ref, .02)
        metrics[axis] = {'seam_mean_abs_8bit': round(mean, 5),
                         'interior_mean_abs_8bit': round(ref, 5),
                         'seam_to_interior_ratio': round(ratio, 5),
                         'pass': bool(ratio < 1.75 or mean < 1.0)}
    return metrics


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    entries = []
    previews = []
    for slot, make, target, description, strength, metallic in SLOTS:
        rgb, roughness, height = make()
        rough = np.uint8(np.clip(np.rint(roughness * 255), 0, 255))
        nm, normal_metrics = normal(height, target)
        files = {}
        for suffix, data, space in [('BaseColor', rgb, 'sRGB'), ('Roughness', rough, 'linear'), ('Normal', nm, 'linear tangent-space DirectX')]:
            path = ROOT / f'T_{slot}_{suffix}.png'
            Image.fromarray(data).save(path, optimize=True)
            tiling = edge_test(data)
            if not all(v['pass'] for v in tiling.values()):
                raise RuntimeError(f'Unexpected seam test failure: {slot}/{suffix}: {tiling}')
            check = np.asarray(Image.open(path))
            assert check.shape == data.shape and np.array_equal(check, data)
            assert check.var() > 0, f'Flat image: {path}'
            files[suffix] = {'path': path.name, 'dimensions': [SIZE, SIZE], 'color_space': space,
                             'channels': 1 if data.ndim == 2 else 3,
                             'sha256': sha256(path), 'tiling': tiling,
                             'png_roundtrip_exact': True}
        entries.append({'slot': slot, 'description': description, 'files': files,
                        'base_color_mean_srgb_8bit': [round(float(v), 2) for v in rgb.mean(axis=(0, 1))],
                        'base_color_std_srgb_8bit': [round(float(v), 2) for v in rgb.std(axis=(0, 1))],
                        'roughness_mean_linear': round(float(rough.mean() / 255), 4),
                        'normal_metrics': normal_metrics,
                        'ue_recommendations': {'base_color_srgb': True, 'roughness_srgb': False,
                            'roughness_compression': 'Masks (no sRGB)', 'normal_srgb': False,
                            'normal_compression': 'Normalmap', 'flip_green_channel': False,
                            'normal_strength': strength, 'metallic': metallic,
                            'sampler_address_u': 'Wrap', 'sampler_address_v': 'Wrap',
                            'physical_tile_width_m': 1.0}})
        previews.append((slot, Image.fromarray(rgb), Image.fromarray(rough), Image.fromarray(nm)))
    # Source-art QA only; these are not Unreal scene captures.
    sheet = Image.new('RGB', (4 * 256, len(previews) * 152 + 52), (38, 40, 39))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 15), 'WindmillFarm original procedural surface art / BaseColor | Roughness | Normal | 2x2 tile', fill=(230, 230, 221))
    for row, (slot, base, rough, nm) in enumerate(previews):
        y = row * 152 + 52
        draw.text((9, y + 4), slot, fill=(235, 235, 224))
        for col, src in enumerate((base, rough.convert('RGB'), nm)):
            sheet.paste(src.resize((224, 120), Image.Resampling.LANCZOS), (col * 256 + 16, y + 24))
        tile = base.resize((60, 60), Image.Resampling.LANCZOS)
        for xx in range(2):
            for yy in range(2):
                sheet.paste(tile, (3 * 256 + 68 + xx * 60, y + 24 + yy * 60))
    sheet.save(ROOT / 'source_art_contact_sheet.png')
    # Larger three-by-three tiling checks reveal wrapping at useful viewing scale.
    for slot in ('Wood', 'Roof', 'Canvas', 'Soil'):
        base = Image.open(ROOT / f'T_{slot}_BaseColor.png').resize((384, 384), Image.Resampling.LANCZOS)
        tiled = Image.new('RGB', (1152, 1152))
        for xx in range(3):
            for yy in range(3):
                tiled.paste(base, (xx * 384, yy * 384))
        tiled.save(ROOT / f'QA_{slot}_3x3.png')
    finish = datetime.now(timezone.utc)
    manifest = {'theme': 'WindmillFarm', 'effort': 'ultra', 'art_type': 'original procedural source textures',
        'generator': 'generator.py', 'generator_sha256': sha256(Path(__file__)), 'global_seed': SEED,
        'started_at_utc': START.isoformat(), 'finished_at_utc': finish.isoformat(),
        'elapsed_seconds': round((finish - START).total_seconds(), 3),
        'resolution': [SIZE, SIZE], 'source_provenance': {
            'original': True, 'external_images': [], 'image_generation_service_used': False,
            'method': 'Original numpy Fourier-periodic fields and analytic integer-frequency grain/weave; Pillow PNG encoding.',
            'ownership': 'All source and outputs authored solely for WindmillFarm/ultra.'},
        'algorithm': 'Seeded Gaussian white noise is Fourier-filtered on a 2D torus; periodic analytic waves add surface-specific grain, weave and veins. No light, shadows, text, AO, seams or edge borders are painted into the albedos.',
        'normal_convention': 'Tangent space DirectX (+X red, +Y green), U right and texture V down. Wrapped central differences: nx=-dH/dU, ny=+dH/dV, nz=1, normalized. No green-channel flip required in UE.',
        'tiling_validation': 'Compare wrapping-edge finite differences with mean adjacent interior differences on both axes. Pass when ratio<1.75 or mean edge jump<1 8-bit level. Last texel is adjacent to first, not a duplicated sample. Every PNG is reopened and verified lossless/nonconstant.',
        'limitations': ['Physical tile width is a shading recommendation; mesh UV density is verified by the parent scene author.',
                         'Glass is a color/roughness source; transparency and reflections require material setup.',
                         'Procedural source-art previews do not constitute scene evidence.',
                         'No image-generation service was used; no image-generation prompts or outputs exist.'],
        'source_art_preview': 'source_art_contact_sheet.png', 'textures': entries,
        'validation_summary': {'slot_count': len(entries), 'texture_count': len(entries) * 3,
                               'all_dimension_checks_pass': True, 'all_png_roundtrips_exact': True,
                               'all_nonconstant_checks_pass': True, 'all_edge_tests_pass': True}}
    (ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(manifest['validation_summary']))
    print(f'Output: {ROOT}')
    print(f'Generated in {(finish - START).total_seconds():.3f}s')


if __name__ == '__main__':
    main()
