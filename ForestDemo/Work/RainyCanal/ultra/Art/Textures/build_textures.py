"""Original RainyCanal/ultra material artwork. No downloaded or shared art.

Run with the bundled Python runtime. Outputs remain beside this source.
All patterns are periodic on an 8 m square domain, sampled at 1024 x 1024.
The terminal sample duplicates the initial periodic sample for exact PNG edges.
Normals are tangent-space DirectX (+Y green down), linear-data RGB PNG.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
N = 1024
PERIOD_M = 8.0
SEED = 2026102207
U, V = np.meshgrid(np.linspace(0, 1, N), np.linspace(0, 1, N))
STARTED = datetime.now(timezone.utc)
MANIFEST = {
    'theme': 'RainyCanal', 'effort': 'ultra',
    'provenance': 'Original deterministic procedural surface artwork authored for this assignment. No external or previous-theme artwork read or used.',
    'resolution': [N, N], 'repeat_m': [PERIOD_M, PERIOD_M],
    'nominal_density_px_per_m': 128.0,
    'sample_density_px_per_m': (N-1)/PERIOD_M,
    'seed': SEED,
    'base_color_encoding': '8-bit RGB sRGB, opaque, import sRGB=true',
    'roughness_encoding': '8-bit grayscale linear, import sRGB=false; metallic not encoded',
    'normal_encoding': '8-bit tangent-space RGB DirectX; flat (128,128,255), +green points down texture V; UE normal-map compression, sRGB=false, no green flip',
    'seam_method': 'Analytic periodic domain; final column duplicates first, final row duplicates first before export. Periodic central differences are computed on 1023 unique samples; normals receive matching terminal edges. PNG QA reopens files and compares every opposite-edge channel exactly.',
    'texture_filtering': 'Wrap address on both axes. Bilinear/trilinear. Do not use clamp.',
    'materials': {},
}


def smooth(a, b, value):
    t = np.clip((value-a)/(b-a), 0.0, 1.0)
    return t*t*(3.0-2.0*t)


def noise(seed, fmin=1, fmax=8, octaves=16):
    """Bounded zero-centered analytic periodic color/height variation."""
    rng = np.random.default_rng(seed)
    result = np.zeros((N, N), dtype=np.float64)
    weight = 0.0
    for _ in range(octaves):
        fx, fy = rng.integers(fmin, fmax+1, size=2)
        fx *= rng.choice([-1, 1])
        amp = 1.0 / math.sqrt(abs(fx) + fy)
        result += amp * np.sin(2*math.pi*(fx*U+fy*V)+rng.uniform(0, 2*math.pi))
        weight += amp
    return result/weight*2.0


MACRO = noise(SEED, 1, 5, 16)
MID = noise(SEED+1, 7, 22, 24)
FINE = noise(SEED+2, 28, 64, 24)


def periodic_edges(array):
    array = np.array(array, copy=True)
    array[-1, ...] = array[0, ...]
    array[:, -1, ...] = array[:, 0, ...]
    return array


def normals_from_height(height):
    """Meters in/out: DirectX normal, surface +Z, texture V down."""
    core = periodic_edges(height)[:-1, :-1]
    spacing = PERIOD_M/(N-1)
    dx = (np.roll(core, -1, axis=1)-np.roll(core, 1, axis=1))/(2*spacing)
    dy = (np.roll(core, -1, axis=0)-np.roll(core, 1, axis=0))/(2*spacing)
    normal = np.stack([-dx, dy, np.ones_like(core)], axis=-1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    normal = np.pad(normal, ((0, 1), (0, 1), (0, 0)), mode='wrap')
    return np.rint((normal*0.5+0.5)*255).astype(np.uint8)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_png(path):
    im = Image.open(path)
    a = np.asarray(im).astype(np.int16)
    lr = np.abs(a[:, 0]-a[:, -1])
    tb = np.abs(a[0]-a[-1])
    # Store same-scale adjacent-pixel changes for context, not a substitute for edge tests.
    inner_lr = np.abs(a[:, 1]-a[:, 0])
    inner_tb = np.abs(a[1]-a[0])
    values = {
        'file': path.name, 'sha256': sha256(path),
        'size_bytes': path.stat().st_size, 'resolution': list(im.size), 'mode': im.mode,
        'opposite_edges': {
            'left_right_max_abs_channel_error': int(lr.max()),
            'top_bottom_max_abs_channel_error': int(tb.max()),
            'left_right_unequal_channels': int(np.count_nonzero(lr)),
            'top_bottom_unequal_channels': int(np.count_nonzero(tb)),
            'pass_exact': bool(lr.max() == 0 and tb.max() == 0),
            'first_interior_x_mean_abs_step': float(inner_lr.mean()),
            'first_interior_y_mean_abs_step': float(inner_tb.mean()),
        },
        'channel_min': np.min(a, axis=(0, 1)).tolist(),
        'channel_max': np.max(a, axis=(0, 1)).tolist(),
        'channel_mean': np.mean(a, axis=(0, 1)).tolist(),
    }
    if im.mode == 'L':
        values['linear_percentiles_0_5_50_95_100'] = (np.percentile(a, [0, 5, 50, 95, 100])/255).tolist()
    return values


def export(slot, base, roughness, height, params):
    base = periodic_edges(np.rint(np.clip(base, 0, 255)).astype(np.uint8))
    rough = periodic_edges(np.rint(np.clip(roughness, 0, 1)*255).astype(np.uint8))
    normal = periodic_edges(normals_from_height(height))
    maps = {'BaseColor': base, 'Roughness': rough, 'Normal': normal}
    record = {'parameters': params, 'files': {}, 'height_range_m': [float(height.min()), float(height.max())]}
    for kind, arr in maps.items():
        file = OUT/f'T_{slot}_{kind}.png'
        Image.fromarray(arr).save(file, optimize=True)
        record['files'][kind] = inspect_png(file)
    decoded = normal.astype(np.float64)/255*2-1
    decoded /= np.linalg.norm(decoded, axis=-1, keepdims=True)
    angles = np.rad2deg(np.arccos(np.clip(decoded[:, :, 2], -1, 1)))
    record['decoded_normal_tilt_degrees_50_95_99_max'] = np.percentile(angles, [50, 95, 99, 100]).tolist()
    record['normal_blue_min'] = int(normal[:, :, 2].min())
    MANIFEST['materials'][slot] = record
    print(f'{slot}: 3 PNGs, exact edges; roughness {rough.min()/255:.3f}..{rough.max()/255:.3f}; normal max tilt {angles.max():.2f} degrees', flush=True)


def block_field(seed, columns, rows, radius_px, gap_px, distort=0.0):
    """Staggered, softly irregular rounded rectangles; returns stone mask and identity."""
    rng = np.random.default_rng(seed)
    pxw, pxh = (N-1)/columns, (N-1)/rows
    xx = U*columns + distort*noise(seed+81, 1, 4)
    yy = V*rows + distort*noise(seed+82, 1, 4)
    row = np.floor(yy).astype(int)
    yy = yy-np.floor(yy)
    xx = xx+(row % 2)*0.5
    col = np.floor(xx).astype(int)
    xx = xx-np.floor(xx)
    rid, cid = row % rows, col % columns
    var = rng.uniform(-1, 1, (rows, columns))[rid, cid]
    widths = rng.uniform(-0.35, 0.35, (rows, columns))[rid, cid]
    qx = np.abs(xx-0.5)*pxw-(pxw/2-gap_px/2-radius_px)+widths
    qy = np.abs(yy-0.5)*pxh-(pxh/2-gap_px/2-radius_px)+widths
    sdf = np.sqrt(np.maximum(qx, 0)**2+np.maximum(qy, 0)**2)+np.minimum(np.maximum(qx, qy), 0)-radius_px
    inside = smooth(-0.6, 0.9, -sdf)
    bevel = smooth(-0.1, 3.1, -sdf)
    return inside, bevel, var, xx, yy


def stone():
    mask, bevel, var, x, y = block_field(SEED+100, 13, 24, 6.0, 2.3, 0.035)
    stone_color = np.array([145, 145, 131]) + (var*9 + MACRO*5 + MID*3 + FINE*1.2)[:, :, None]*np.array([1.0, 0.94, 0.78])
    mortar = np.array([94, 103, 94]) + MACRO[:, :, None]*4
    base = mortar*(1-mask[:, :, None])+stone_color*mask[:, :, None]
    damp = smooth(-0.5, 0.6, MACRO + noise(SEED+103, 1, 4))
    base -= damp[:, :, None]*np.array([5, 5, 4])
    rough = np.clip(0.54-0.23*damp + var*0.025 + MID*0.025 - (1-bevel)*0.045, 0.24, 0.60)
    height = bevel*(0.0034 + var*0.00045) + MID*0.00012 + FINE*0.00004
    export('Stone', base, rough, height, {'seed': SEED+100, 'layout': '13 columns by 24 staggered rows', 'block_size_m': [8/13, 8/24], 'gap_px': 2.3, 'corner_radius_px': 6.0, 'base_srgb': [145, 145, 131], 'mortar_srgb': [94, 103, 94], 'roughness_target': [0.24, 0.60], 'normal_height_m': 0.0034, 'use': 'Quay, bridge and building foundation limestone; softly bevelled warm-gray blocks, damp variable face roughness.'})


def cobble():
    mask, bevel, var, x, y = block_field(SEED+200, 27, 28, 7.2, 2.0, 0.16)
    warm = noise(SEED+203, 1, 5)
    face = np.array([112, 117, 110]) + (var*13+MACRO*4+MID*2)[:, :, None] + warm[:, :, None]*np.array([5, 2, -2])
    mortar = np.array([67, 80, 74]) + MID[:, :, None]*2
    base = mortar*(1-mask[:, :, None])+face*mask[:, :, None]
    damp = smooth(-0.55, 0.7, MACRO+noise(SEED+206, 1, 5)*0.6)
    base -= damp[:, :, None]*3
    rough = np.clip(0.55-0.28*damp+var*0.025+MID*0.025-(1-bevel)*0.045, 0.20, 0.60)
    height = bevel*(0.0038+var*0.0005) + MID*0.00008 + FINE*0.000035
    export('Cobble', base, rough, height, {'seed': SEED+200, 'layout': '27 columns by 28 staggered rows with smooth periodic distortion', 'paver_size_m': [8/27, 8/28], 'gap_px': 2.0, 'corner_radius_px': 7.2, 'base_srgb': [112, 117, 110], 'mortar_srgb': [67, 80, 74], 'roughness_target': [0.20, 0.60], 'normal_height_m': 0.0038, 'use': 'Wet rounded lane pavers; shallow water sheen is material roughness variation, not baked lighting.'})


def plaster(slot, color, seed):
    local = noise(seed, 1, 7)
    trowel = noise(seed+1, 8, 28, 32)
    hue = noise(seed+2, 2, 5)
    base = np.array(color) + (local*4.0+trowel*2.2+FINE*0.6)[:, :, None] + hue[:, :, None]*np.array([1.3, 0.6, -0.7])
    rough = np.clip(0.75+local*0.045+trowel*0.04+FINE*0.012, 0.60, 0.85)
    height = local*0.00015+trowel*0.00018+FINE*0.000025
    export(slot, base, rough, height, {'seed': seed, 'base_srgb': color, 'pattern': 'Low contrast mineral limewash and broad trowel variation, no baked shadows or fixture marks', 'roughness_target': [0.60, 0.85], 'use': 'Dry protected building facades. Broad low-frequency variation remains calm at distance.'})


def timber():
    seed = SEED+500
    rng = np.random.default_rng(seed)
    columns, rows = 32, 4
    xx = U*columns
    col = np.floor(xx).astype(int) % columns
    phase_offsets = rng.integers(0, 4, columns)/4
    yy = V*rows+phase_offsets[col]
    row = np.floor(yy).astype(int) % rows
    fx, fy = xx-np.floor(xx), yy-np.floor(yy)
    vari = rng.uniform(-1, 1, (rows, columns))[row, col]
    edge = np.minimum(fx, 1-fx)*(N-1)/columns
    ends = np.minimum(fy, 1-fy)*(N-1)/rows
    inside = smooth(0.6, 2.1, edge)*smooth(0.5, 1.8, ends)
    wavy = np.sin(2*np.pi*(U*160 + 0.18*np.sin(2*np.pi*V*4)+0.1*np.sin(2*np.pi*(V*9+U*2))))
    grain = wavy*0.6+np.sin(2*np.pi*(U*280 + 0.1*np.sin(2*np.pi*V*7)))*0.22
    broad = np.sin(2*np.pi*(U*64+0.2*np.sin(2*np.pi*V*2)))
    face = np.array([112, 88, 63]) + (grain*2.9+broad*2+vari*8+MACRO*4)[:, :, None]*np.array([1.0, 0.85, 0.7])
    joint = np.array([66, 59, 45])
    base = joint*(1-inside[:, :, None])+face*inside[:, :, None]
    rough = np.clip(0.49+vari*0.055+MACRO*0.05+grain*0.018-(1-inside)*0.06, 0.30, 0.65)
    height = inside*0.0022+grain*0.000085+broad*0.00010
    export('Timber', base, rough, height, {'seed': seed, 'base_srgb': [112, 88, 63], 'plank_width_m': 0.25, 'plank_length_m': 2.0, 'grain_direction': 'Vertical / V; orient plank UV V along timber length', 'roughness_target': [0.30, 0.65], 'normal_height_m': 0.0022, 'use': 'Weathered warm wooden trim, shutters, benches and deck details; periodic restrained grain.'})


def roof(slot, color, seed, clay=False):
    cols, rows = (24, 28) if not clay else (28, 24)
    mask, bevel, var, x, y = block_field(seed, cols, rows, 3.0, 1.6, 0.012)
    grain = noise(seed+19, 10, 36)
    # Broad convex clay roll / restrained flat slate relief; absent directional baked lighting.
    roll = (np.sin(np.pi*x)**2) if clay else np.zeros_like(x)
    tint = (var*8.0+MACRO*3.0+grain*2.3)[:, :, None]
    face = np.array(color)+tint*np.array([1.0, 0.94, 0.88])
    grout = np.array(color)*0.64+np.array([0, 3, 2])
    base = grout*(1-mask[:, :, None])+face*mask[:, :, None]
    wet = smooth(-0.5, 0.6, MACRO+noise(seed+22, 1, 5))
    rough = np.clip(0.57-0.17*wet+var*0.035+grain*0.03, 0.30, 0.65)
    height = bevel*(0.0024+var*0.0003+roll*0.0012)+grain*0.00008
    export(slot, base, rough, height, {'seed': seed, 'base_srgb': color, 'tile_size_m': [8/cols, 8/rows], 'layout': f'{cols} columns by {rows} staggered rows', 'gap_px': 1.6, 'roughness_target': [0.30, 0.65], 'use': 'Muted roof tiles, glazed by rain without a uniform mirror surface; geometric roof slope supplies drainage direction.'})


def metal():
    seed = SEED+800
    patina = noise(seed, 1, 7)
    dull = noise(seed+1, 8, 20)
    oxide = smooth(0.1, 0.75, patina)*0.5
    base = np.array([36, 48, 43]) + (patina*3+dull*1.5)[:, :, None] + oxide[:, :, None]*np.array([5, 1, -2])
    rough = np.clip(0.30+patina*0.06+dull*0.035, 0.20, 0.40)
    height = dull*0.00006+FINE*0.000015
    export('Metal', base, rough, height, {'seed': seed, 'base_srgb': [36, 48, 43], 'roughness_target': [0.20, 0.40], 'recommended_metallic': 0.7, 'recommended_metallic_note': 'Parent may use 0.7-0.9 for iron or 0 for painted finish. This PNG set does not encode metallic.', 'use': 'Dark green-black iron railings, lamps and brackets; subtle broad weathering, no repetitive heavy corrosion.'})


def leaf():
    seed = SEED+900
    rng = np.random.default_rng(seed)
    columns, rows = 24, 24
    yy = V*rows
    row_unwrapped = np.floor(yy).astype(int)
    xx = U*columns+(row_unwrapped % 2)*0.5
    row = row_unwrapped % rows
    col = np.floor(xx).astype(int) % columns
    fx, fy = xx-np.floor(xx)-0.5, yy-np.floor(yy)-0.5
    angle = rng.uniform(-math.pi, math.pi, (rows, columns))[row, col]
    variation = rng.uniform(-1, 1, (rows, columns))[row, col]
    rx = fx*np.cos(angle)-fy*np.sin(angle)
    ry = fx*np.sin(angle)+fy*np.cos(angle)
    radius = np.sqrt((rx/0.30)**2+(ry/0.43)**2)
    mask = 1-smooth(0.86, 1.02, radius)
    vein = np.exp(-(rx/0.024)**2)*mask
    sideveins = (np.sin(2*np.pi*(np.abs(rx)*9+ry*5))**12)*mask*0.26
    back = np.array([62, 85, 57])+(MACRO*4+MID*1.5)[:, :, None]
    face = np.array([82, 107, 67])+(variation*7+MACRO*4+MID*2)[:, :, None]*np.array([0.9, 1.0, 0.7])
    base = back*(1-mask[:, :, None])+face*mask[:, :, None]+(vein*3+sideveins*2)[:, :, None]
    rough = np.clip(0.58+MID*0.035+variation*0.025-mask*0.09, 0.40, 0.68)
    height = mask*0.0008+vein*0.00012+sideveins*0.00008
    export('Leaf', base, rough, height, {'seed': seed, 'base_srgb': [82, 107, 67], 'background_srgb': [62, 85, 57], 'pattern': '24 by 24 alternating rows of individually rotated soft leaf forms', 'cell_size_m': [1/3, 1/3], 'opacity': 'Opaque; this is a foliage-surface pattern, not a cutout/opacity atlas', 'roughness_target': [0.40, 0.68], 'use': 'Rounded shrub and canopy forms with a calm muted leaf surface. Not intended as an individual leaf card texture.'})


def make_preview():
    slots = list(MANIFEST['materials'])
    width, height = 1580, 1760
    canvas = Image.new('RGB', (width, height), (30, 37, 37))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 24)
    small = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 17)
    title = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 36)
    draw.text((34, 20), 'Rainy Canal | Original surface textures', fill=(229, 225, 207), font=title)
    draw.text((35, 68), '1024 x 1024  |  8 m repeat at nominal 128 px/m  |  BaseColor / Roughness / DirectX Normal', fill=(165, 180, 174), font=small)
    for i, slot in enumerate(slots):
        x, y = 35+(i%2)*780, 116+(i//2)*326
        draw.text((x, y), slot, fill=(232, 228, 214), font=font)
        rec = MANIFEST['materials'][slot]
        minr, _, medr, _, maxr = rec['files']['Roughness']['linear_percentiles_0_5_50_95_100']
        draw.text((x+260, y+6), f'R {minr:.2f} - {maxr:.2f} | median {medr:.2f}', fill=(171, 189, 180), font=small)
        for j, kind in enumerate(['BaseColor', 'Roughness', 'Normal']):
            thumb = Image.open(OUT/f'T_{slot}_{kind}.png').convert('RGB').resize((240, 240), Image.Resampling.LANCZOS)
            canvas.paste(thumb, (x+j*250, y+41))
            draw.text((x+j*250, y+285), kind, fill=(157, 172, 167), font=small)
    canvas.save(OUT/'Texture_Collage.png', optimize=True)
    # Native-scale repeating crops expose real spacing, relief and seams.
    seam = Image.new('RGB', (1600, 1040), (30, 37, 37))
    d = ImageDraw.Draw(seam)
    d.text((24, 18), 'Tile-boundary preview | center cross is the wrap seam', fill=(229, 225, 207), font=font)
    for i, slot in enumerate(['Stone', 'Cobble', 'Timber', 'RoofSlate', 'RoofClay', 'Leaf']):
        original = Image.open(OUT/f'T_{slot}_BaseColor.png')
        arr = np.asarray(original)
        # Build a centered 480px crop straddling the exact 2x2 tile seam at 1:1 pixels.
        indexes = np.r_[np.arange(N-240, N), np.arange(240)]
        crop = Image.fromarray(arr[indexes][:, indexes])
        x, y = 24+(i%3)*525, 62+(i//3)*488
        seam.paste(crop, (x, y))
        d.rectangle((x, y, x+100, y+25), fill=(30, 37, 37))
        d.text((x+5, y+2), slot, fill=(229, 225, 207), font=small)
    seam.save(OUT/'Tile_Seam_Preview.png', optimize=True)


def finalize():
    make_preview()
    finished = datetime.now(timezone.utc)
    all_files = [f for r in MANIFEST['materials'].values() for f in r['files'].values()]
    MANIFEST['started_at_utc'] = STARTED.isoformat()
    MANIFEST['finished_at_utc'] = finished.isoformat()
    MANIFEST['generation_wall_seconds'] = (finished-STARTED).total_seconds()
    MANIFEST['qa'] = {
        'png_count': len(all_files), 'expected_png_count': 30,
        'all_1024_square': all(f['resolution'] == [1024, 1024] for f in all_files),
        'all_opposite_edges_exact': all(f['opposite_edges']['pass_exact'] for f in all_files),
        'all_normals_positive_z': all(r['normal_blue_min'] > 127 for r in MANIFEST['materials'].values()),
        'normal_max_tilt_degrees': max(r['decoded_normal_tilt_degrees_50_95_99_max'][-1] for r in MANIFEST['materials'].values()),
        'ue_import_or_render_performed': False,
        'note': 'These are material source assets, not scene evidence. Final UE lighting/UV/material validation belongs to the scene builder.',
    }
    MANIFEST['source'] = {'file': Path(__file__).name, 'sha256': sha256(Path(__file__))}
    MANIFEST['previews'] = [{'file': p, 'sha256': sha256(OUT/p)} for p in ['Texture_Collage.png', 'Tile_Seam_Preview.png']]
    (OUT/'texture_manifest.json').write_text(json.dumps(MANIFEST, indent=2), encoding='utf-8')
    report = [
        '# RainyCanal ultra — original procedural texture set', '',
        'Thirty 1024×1024 source PNGs: BaseColor, linear Roughness, and DirectX tangent Normal for Stone, Cobble, PlasterCream, PlasterSage, PlasterRose, Timber, RoofSlate, RoofClay, Metal, and Leaf.', '',
        'All source artwork is original deterministic code in `build_textures.py`. No external images, earlier themes, existing source art or shared creative assets were read or reused. Seed, color values, feature sizes, heights, roughness targets and full SHA256 values are recorded in `texture_manifest.json`.', '',
        '## Material usage', '',
        '- Use world-scaled UVs with one repeat per 8 m for the intended 128 px/m nominal density. The exact sampled interval is 1023/8 = 127.875 px/m because an endpoint pixel is duplicated to make opposite edges exactly equal.',
        '- BaseColor: sRGB enabled. Roughness: sRGB disabled and a linear grayscale/masks sampler. Normal: UE normal compression, sRGB disabled, DirectX (+green down texture V), no green flip. Wrap both axes.',
        '- Stone: warm grey rounded limestone; Cobble: darker rounded wet pavers. Both use broad roughness variation, not a uniform mirror sheen.',
        '- Plaster variants use independent low-contrast limewash patterns with dry roughness. Timber grain follows V; rotate island UVs so V follows the member length.',
        '- Metal is opaque dark green-black iron; select a metallic parameter appropriate to iron or painted metal in the parent material.',
        '- Leaf is an opaque canopy/shrub surface with softly rotated leaves, not a leaf-card opacity atlas.',
        '- No shadows, AO or reflected scene lighting are deliberately baked into BaseColor. Gentle mortar/joint colors are surface pigmentation; actual scene lighting remains dynamic.', '',
        '## Executed file validation', '',
        f'- Build start UTC: {STARTED.isoformat()}. Finish UTC: {finished.isoformat()}. Measured generation seconds: {(finished-STARTED).total_seconds():.3f}.',
        '- Reopened all 30 PNGs: each is 1024×1024, expected mode and readable. Every horizontal and vertical opposite-edge channel is exactly equal (maximum error 0, unequal channel count 0).',
        '- Normals are derived from periodic meter-scaled height central differences, normalized, encoded as DirectX RGB, and have positive Z throughout. Opposite normal-map edges are exactly equal.',
        '- Edge-derivative neighborhoods and roughness ranges/percentiles are recorded per image. Preview `Tile_Seam_Preview.png` shows 1:1 crops crossing the wrap join.', '',
        '| Surface | Roughness min / median / max | Normal max tilt |', '|---|---:|---:|',
    ]
    for slot, record in MANIFEST['materials'].items():
        lo, _, mid, _, hi = record['files']['Roughness']['linear_percentiles_0_5_50_95_100']
        tilt = record['decoded_normal_tilt_degrees_50_95_99_max'][-1]
        report.append(f'| {slot} | {lo:.3f} / {mid:.3f} / {hi:.3f} | {tilt:.2f}° |')
    report += ['', '## Scope and limits', '',
        'This folder provides source material artwork. No Unreal session, import, scene render, mesh UV density check or final material compilation was performed by this texture task. The scene builder must perform those checks. Screenshots in this folder are texture previews only and must not be presented as actual UE scene evidence.', '',
        'Reproduce with the supplied bundled Python interpreter and `build_textures.py`; only NumPy and Pillow are required. Output file bytes are deterministic for the same Pillow implementation; manifest build timestamps and elapsed runtime change on each run.', '',
        'Visual inspection status is recorded separately in `VISUAL_QA.md` after reviewing the generated previews.', '',
        '![Texture contact sheet](Texture_Collage.png)', '',
        '![Tile seam preview](Tile_Seam_Preview.png)', '',
    ]
    (OUT/'REVIEW.md').write_text('\n'.join(report), encoding='utf-8')
    assert MANIFEST['qa']['png_count'] == 30
    assert MANIFEST['qa']['all_1024_square']
    assert MANIFEST['qa']['all_opposite_edges_exact']
    assert MANIFEST['qa']['all_normals_positive_z']
    print(json.dumps(MANIFEST['qa'], indent=2), flush=True)


if __name__ == '__main__':
    stone()
    cobble()
    plaster('PlasterCream', [202, 193, 173], SEED+301)
    plaster('PlasterSage', [135, 151, 133], SEED+302)
    plaster('PlasterRose', [183, 145, 128], SEED+303)
    timber()
    roof('RoofSlate', [81, 103, 108], SEED+600)
    roof('RoofClay', [137, 98, 80], SEED+700, clay=True)
    metal()
    leaf()
    finalize()
