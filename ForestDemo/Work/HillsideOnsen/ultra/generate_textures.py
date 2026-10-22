"""Original deterministic HillsideOnsen/ultra surface art; standard library only.

Run with any Python 3.11+: python generate_textures.py
Writes only ./Textures and ./texture_manifest.json. No external images are read.
Surface maps sample periodic functions at inclusive endpoints, giving exactly
matching opposite border pixels. This intentional one-pixel duplication is tiny
at 512 px and makes wrap seams independently verifiable in the saved files.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import random
import struct
import time
import zlib

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "Textures"
TAU = 2 * math.pi
SIZE = 512


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def smooth(a, b, x):
    t = clamp((x-a)/(b-a))
    return t*t*(3-2*t)


class PeriodicNoise:
    def __init__(self, seed, nx, ny=None):
        self.nx = nx
        self.ny = ny or nx
        rng = random.Random(seed)
        self.grid = [[rng.uniform(-1, 1) for _ in range(self.nx)]
                     for _ in range(self.ny)]

    def __call__(self, u, v):
        x, y = (u % 1)*self.nx, (v % 1)*self.ny
        ix, iy = math.floor(x), math.floor(y)
        sx, sy = x-ix, y-iy
        sx, sy = sx*sx*(3-2*sx), sy*sy*(3-2*sy)
        a = self.grid[iy % self.ny][ix % self.nx]
        b = self.grid[iy % self.ny][(ix+1) % self.nx]
        c = self.grid[(iy+1) % self.ny][ix % self.nx]
        d = self.grid[(iy+1) % self.ny][(ix+1) % self.nx]
        return (a+(b-a)*sx)*(1-sy) + (c+(d-c)*sx)*sy


def rgb(base, change, weights=(1, 1, 1)):
    values = tuple(base[i]+change*weights[i] for i in range(3))
    assert all(math.isfinite(v) for v in values)
    return tuple(round(clamp(v, 0, 255)) for v in values)


def png_write(path, width, height, channels, pixels):
    assert len(pixels) == width*height*channels
    def chunk(kind, payload):
        return (struct.pack(">I", len(payload))+kind+payload+
                struct.pack(">I", zlib.crc32(kind+payload) & 0xffffffff))
    color_type = {1: 0, 3: 2, 4: 6}[channels]
    scan = b"".join(b"\0"+pixels[y*width*channels:(y+1)*width*channels]
                    for y in range(height))
    payload = b"\x89PNG\r\n\x1a\n"
    payload += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0))
    payload += chunk(b"IDAT", zlib.compress(scan, 9))
    payload += chunk(b"IEND", b"")
    path.write_bytes(payload)


def png_read_verify(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    at, comp, width, height, channels = 8, bytearray(), None, None, None
    while at < len(data):
        n = struct.unpack(">I", data[at:at+4])[0]
        kind, body = data[at+4:at+8], data[at+8:at+8+n]
        crc = struct.unpack(">I", data[at+8+n:at+12+n])[0]
        assert zlib.crc32(kind+body) & 0xffffffff == crc, (path, kind)
        if kind == b"IHDR":
            width, height, depth, ct, *_ = struct.unpack(">IIBBBBB", body)
            assert depth == 8
            channels = {0: 1, 2: 3, 6: 4}[ct]
        elif kind == b"IDAT":
            comp.extend(body)
        at += 12+n
    decoded = zlib.decompress(comp)
    stride = width*channels
    assert len(decoded) == height*(stride+1)
    rows = []
    for y in range(height):
        assert decoded[y*(stride+1)] == 0
        rows.append(decoded[y*(stride+1)+1:(y+1)*(stride+1)])
    pixels = b"".join(rows)
    border = []
    for y in range(height):
        border.extend(abs(a-b) for a,b in zip(rows[y][:channels], rows[y][-channels:]))
    border.extend(abs(a-b) for a,b in zip(rows[0], rows[-1]))
    means = [sum(pixels[c::channels])/(width*height) for c in range(channels)]
    stdev = [math.sqrt(sum((v-means[c])**2 for v in pixels[c::channels])/(width*height))
             for c in range(channels)]
    result = dict(width=width, height=height, channels=channels,
                  crc_valid=True, decoded_bytes_valid=True, finite=True,
                  minimum=min(pixels), maximum=max(pixels),
                  channel_mean=[round(x, 4) for x in means],
                  channel_stdev=[round(x, 4) for x in stdev],
                  opposite_border_max_delta=max(border),
                  sha256=hashlib.sha256(data).hexdigest())
    if channels == 4:
        alpha_edge = list(rows[0][3::4])+list(rows[-1][3::4])
        alpha_edge += [rows[y][3] for y in range(height)]
        alpha_edge += [rows[y][-1] for y in range(height)]
        result["alpha_border_max"] = max(alpha_edge)
        assert result["alpha_border_max"] == 0
    assert result["opposite_border_max_delta"] == 0
    return result, pixels


def build_surfaces():
    wood_lo, wood_long, wood_fine = PeriodicNoise(43101, 8, 3), PeriodicNoise(43102, 48, 4), PeriodicNoise(43103, 96, 12)
    stone_lo, stone_mid, stone_fine = PeriodicNoise(43201, 4), PeriodicNoise(43202, 18), PeriodicNoise(43203, 94)
    plaster_lo, plaster_fine = PeriodicNoise(43301, 7), PeriodicNoise(43302, 99)
    slate_lo, slate_fine = PeriodicNoise(43401, 6), PeriodicNoise(43402, 84)
    gravel_lo, gravel_fine = PeriodicNoise(43501, 10), PeriodicNoise(43502, 120)
    grass_lo, grass_mid, grass_fine = PeriodicNoise(43601, 6), PeriodicNoise(43602, 28), PeriodicNoise(43603, 112)
    water_lo = PeriodicNoise(43701, 7)
    steam_lo, steam_fine = PeriodicNoise(43801, 7, 13), PeriodicNoise(43802, 17, 23)
    rng = random.Random(43503)
    cells = 30
    points = [[(rng.uniform(.18,.82), rng.uniform(.18,.82), rng.uniform(-1,1))
               for _ in range(cells)] for _ in range(cells)]
    slate_colors = [[random.Random(43410+y*8+x).uniform(-1,1) for x in range(8)] for y in range(12)]

    def wood_fields(u, v):
        warp = .023*math.sin(TAU*v)+.011*math.sin(TAU*(2*v+u))+.012*wood_lo(u,v)
        phase = TAU*(20*u+warp*12)
        broad = math.sin(phase)
        thin = max(0, math.sin(phase*2+1.4*math.sin(TAU*v)))**12
        pores = wood_fine(u,v)
        return 5*wood_lo(u,v)+4*wood_long(u,v)+2.1*broad-3.5*thin+1.6*pores

    def cedar(u,v):
        return rgb((143, 111, 78), wood_fields(u,v), (1,.85,.62))

    def limestone(u,v):
        n = 6.8*stone_lo(u,v)+3.1*stone_mid(u,v)+1.8*stone_fine(u,v)
        fleck = smooth(.42,.8,stone_fine(u,v))
        return rgb((183,178,162), n-1.8*fleck, (1,.96,.86))

    def plaster(u,v):
        return rgb((224,219,201), 2.1*plaster_lo(u,v)+1.35*plaster_fine(u,v), (1,.97,.87))

    def slate(u,v):
        x,y = (u%1)*8,(v%1)*12
        row=math.floor(y)
        x += .5*(row%2)
        column=math.floor(x)%8
        fx,fy=x%1,y%1
        gap = 1-smooth(.008,.042,min(fx,1-fx,fy*.8,(1-fy)*.8))
        lip = 1-smooth(.025,.11,fy)
        n=3.1*slate_colors[row][column]+2.6*slate_lo(u,v)+1.0*slate_fine(u,v)-8.2*gap+2*lip
        return rgb((91,108,118),n,(.9,.97,1))

    def gravel(u,v):
        x,y=(u%1)*cells,(v%1)*cells
        ix,iy=math.floor(x),math.floor(y)
        candidates=[]
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                px,py,tone=points[(iy+dy)%cells][(ix+dx)%cells]
                d=(ix+dx+px-x)**2+(iy+dy+py-y)**2
                candidates.append((d,tone))
        candidates.sort()
        d0,tone=candidates[0]
        edge=1-smooth(.008,.07,candidates[1][0]-d0)
        n=5*tone+2.4*gravel_lo(u,v)+1.5*gravel_fine(u,v)-5.2*edge+1.2*(.3-d0)
        return rgb((178,168,144),n,(1,.97,.86))

    def grass(u,v):
        n=6.0*grass_lo(u,v)+3.1*grass_mid(u,v)+2.4*grass_fine(u,v)
        blades=math.sin(TAU*(83*u+29*v)+1.7*grass_mid(u,v))*math.sin(TAU*(47*u-61*v))
        return rgb((111,135,99), n+1.8*blades, (.9,1,.77))

    def water(u,v):
        w=water_lo(u,v)
        wave=(.47*math.sin(TAU*(7*u+3*v)+.5*math.sin(TAU*(u-v)))+
              .29*math.sin(TAU*(4*u-9*v)+.7*math.sin(TAU*(2*u+v)))+
              .15*math.sin(TAU*(13*u+11*v))+.09*w)
        grey=round(128+39*wave)
        return (grey,grey,grey)

    def cedar_rough(u,v):
        return (round(clamp(190+wood_fields(u,v)*.6,0,255)),)

    def stone_rough(u,v):
        return (round(clamp(209+4*stone_lo(u,v)+2*stone_fine(u,v),0,255)),)

    def steam(u,v):
        a=0
        # Soft slender columns do not depict illustrative clouds.
        for cx,amplitude,width,phase in ((.32,.38,.075,0),(.53,.57,.095,1.6),(.68,.33,.065,3.3)):
            center=cx+.045*math.sin(TAU*(v*.8)+phase)+.018*math.sin(TAU*(v*2.2)+phase)
            spread=width*(.5+.85*v)
            column=math.exp(-((u-center)/spread)**2*1.4)
            a+=amplitude*column
        vertical=smooth(.035,.18,v)*(1-smooth(.60,.96,v))
        side=smooth(.02,.14,u)*(1-smooth(.86,.98,u))
        noise=clamp(.69+.30*steam_lo(u,v)+.12*steam_fine(u,v),.25,1)
        alpha=round(255*clamp(a*vertical*side*noise*.80))
        if u in (0,1) or v in (0,1):
            alpha=0
        return (235,239,231,alpha)

    return [
        ("T_Cedar_BaseColor","CEDAR",cedar,3,SIZE,"basecolor",[4,4],43101,"Warm muted cedar; grain follows V. Periodic warped sine growth lines plus three anisotropic noise bands."),
        ("T_Limestone_BaseColor","LIMESTONE",limestone,3,SIZE,"basecolor",[4,4],43201,"Warm grey limestone; subtle three-scale mineral mottling with restrained flecks; no fake hard cracks."),
        ("T_Plaster_BaseColor","PLASTER",plaster,3,SIZE,"basecolor",[4,4],43301,"Ivory plaster with quiet low-frequency variation and fine grain."),
        ("T_Slate_BaseColor","SLATE",slate,3,SIZE,"basecolor",[4,4],43401,"Blue-grey slate tiles, 8 columns x 12 staggered rows, subtle grout and upper lip shading."),
        ("T_Gravel_BaseColor","GRAVEL",gravel,3,SIZE,"basecolor",[2,2],43501,"Beige aggregate; 30 x 30 jittered periodic Voronoi cells, muted particle shades and soft narrow gaps."),
        ("T_Grass_BaseColor","GRASS",grass,3,SIZE,"basecolor",[4,4],43601,"Muted sage ground cover; three periodic noise scales and fine crossing organic fiber modulation."),
        ("T_Water_Ripples","WATER",water,3,SIZE,"height_detail",[4,4],43701,"Linear grayscale periodic height/detail field; not a tangent-space normal. Three crossing sine-wave families."),
        ("T_Steam_Opacity","STEAM",steam,4,256,"opacity",None,43801,"Soft vertically elongated wisps. Constant warm-white RGB, alpha mask with exactly zero outer edges; non-tiling card."),
        ("T_Cedar_Roughness","WOOD ROUGH",cedar_rough,1,SIZE,"roughness",[4,4],43101,"Linear roughness aligned to the cedar basecolor. Mean near 0.75."),
        ("T_Limestone_Roughness","STONE ROUGH",stone_rough,1,SIZE,"roughness",[4,4],43201,"Linear roughness aligned to limestone basecolor. Mean near 0.82."),
    ]


FONT = {
 'A':['01110','10001','10001','11111','10001','10001','10001'],
 'B':['11110','10001','10001','11110','10001','10001','11110'],
 'C':['01111','10000','10000','10000','10000','10000','01111'],
 'D':['11110','10001','10001','10001','10001','10001','11110'],
 'E':['11111','10000','10000','11110','10000','10000','11111'],
 'G':['01111','10000','10000','10111','10001','10001','01110'],
 'H':['10001','10001','10001','11111','10001','10001','10001'],
 'I':['111','010','010','010','010','010','111'],
 'L':['10000','10000','10000','10000','10000','10000','11111'],
 'M':['10001','11011','10101','10101','10001','10001','10001'],
 'N':['10001','11001','11001','10101','10011','10011','10001'],
 'O':['01110','10001','10001','10001','10001','10001','01110'],
 'P':['11110','10001','10001','11110','10000','10000','10000'],
 'R':['11110','10001','10001','11110','10100','10010','10001'],
 'S':['01111','10000','10000','01110','00001','00001','11110'],
 'T':['11111','00100','00100','00100','00100','00100','00100'],
 'U':['10001','10001','10001','10001','10001','10001','01110'],
 'V':['10001','10001','10001','10001','01010','01010','00100'],
 'W':['10001','10001','10001','10101','10101','11011','10001'],
 ' ':['000']*7,
}


def contact_sheet(records):
    width,height=1344,620
    canvas=bytearray([36,40,40])*(width*height)
    def put(x,y,color):
        i=(y*width+x)*3
        canvas[i:i+3]=bytes(color)
    for idx,(label,size,ch,pixels) in enumerate(records):
        ox,oy=16+(idx%5)*266,16+(idx//5)*306
        for y in range(256):
            for x in range(256):
                i=(int(y*size/256)*size+int(x*size/256))*ch
                p=pixels[i:i+ch]
                if ch==1:
                    color=p*3
                elif ch==4:
                    alpha=p[3]/255
                    bg=91 if (x//16+y//16)%2 else 113
                    color=[round(p[c]*alpha+bg*(1-alpha)) for c in range(3)]
                else:
                    color=p
                put(ox+x,oy+y,color)
        tx=ox+5
        for char in label:
            glyph=FONT[char]
            for gy,row in enumerate(glyph):
                for gx,bit in enumerate(row):
                    if bit=='1':
                        for sy in range(2):
                            for sx in range(2):
                                put(tx+gx*2+sx,oy+270+gy*2+sy,(222,226,215))
            tx+=(len(glyph[0])+1)*2
    png_write(OUT/'contact_sheet.png',width,height,3,canvas)


def main():
    start=time.perf_counter()
    utc_start=dt.datetime.now(dt.timezone.utc).isoformat()
    OUT.mkdir(parents=True,exist_ok=True)
    assets,records={},[]
    for name,label,fn,ch,size,role,tile,seed,method in build_surfaces():
        pixels=bytearray()
        for y in range(size):
            v=y/(size-1)
            for x in range(size):
                values=fn(x/(size-1),v)
                assert len(values)==ch
                assert all(math.isfinite(n) and 0<=n<=255 for n in values)
                pixels.extend(values)
        path=OUT/(name+'.png')
        png_write(path,size,size,ch,pixels)
        validation,decoded=png_read_verify(path)
        assert decoded==pixels
        assets[name]=dict(path=str(path),relative_path='Textures/'+name+'.png',
                          role=role,size=[size,size],channels=ch,
                          color_space='sRGB' if role=='basecolor' else 'linear',
                          unreal_srgb=role=='basecolor',
                          alpha='straight opacity in A; all outer edges zero' if ch==4 else 'none',
                          repeat_tile_size_m=tile,
                          address_mode='clamp' if ch==4 else 'wrap',
                          principal_seed=seed,method=method,
                          intended_use='translucent steam card; A to opacity, RGB or constant tint to color' if ch==4 else role,
                          validation=validation)
        records.append((label,size,ch,decoded))
        print(name,validation['channel_mean'], 'seam_delta',validation['opposite_border_max_delta'],flush=True)
    contact_sheet(records)
    result=dict(theme='HillsideOnsen',effort='ultra',
                provenance='Original deterministic procedural surface art authored in this task. No external images or other scene assets read; no image-generation service used.',
                generator=str(Path(__file__).resolve()),
                python_dependencies='Python standard library only; no PIL/numpy required',
                generated_at_start_utc=utc_start,
                generated_at_finish_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                elapsed_seconds=round(time.perf_counter()-start,3),
                sample_layout='Periodic functions sampled inclusive endpoints. Opposite PNG borders byte-identical; one endpoint texel is duplicated.',
                uv_guidance='Parent owns 128 px/m chart density and measured atlas layout. Material shader must convert chart UVs back to surface metres then divide by repeat_tile_size_m. Tile sizes describe spatial pattern frequency, not UV chart packing. Cedar grain follows V; rotate charts to align with timber length. Slate rows follow U; V advances roof courses.',
                water_guidance='Linear grayscale height_detail only, not a normal map. Pan two scaled samples slowly in opposite directions to perturb water normal using derivatives or small value modulation; keep amplitude restrained. This texture contains no refraction or caustic simulation.',
                steam_guidance='Linear opacity mask with warm-white tint. Clamp UVs. Use low opacity, depth fade and slow vertical translation/stretch in UE; not physical vapor simulation. Card should face or partly face intended view.',
                assets=assets,contact_sheet=str(OUT/'contact_sheet.png'),
                validation_summary='10 PNGs decoded and CRC checked; dimensions/channel counts verified; all finite 8-bit values; every opposite border byte-identical; steam alpha border exactly 0. Contact sheet requires visual inspection.',
                limitations=['Procedural maps are subtle stylized surface details, not photogrammetric scans.',
                             'No tangent-space normal maps are supplied. Roughness detail is available for cedar and limestone.',
                             'Texture generation does not validate UE import, material assignment, final UVs or rendered appearance.'])
    (ROOT/'texture_manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Generated and verified',len(assets),'textures in',result['elapsed_seconds'],'seconds',flush=True)


if __name__=='__main__':
    main()
