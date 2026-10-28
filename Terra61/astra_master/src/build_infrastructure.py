#!/usr/bin/env python3
"""Create reusable, textured Victorian station infrastructure as GLB.

Authoring axes: X across, Y depth, Z up; each exported asset has a single
-90-degree X root rotation for glTF Y-up. Repeated pieces start at Y=0.
Materials are individual repeatable PNG images: <name>_basecolor.png,
<name>_normal.png and <name>_orm.png, where ORM is the standard
glTF G=roughness, B=metalness packed image.
"""
from __future__ import annotations

import argparse
import io
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image as PILImage
from pygltflib import (
    Accessor, Asset, Attributes, Buffer, BufferView, GLTF2, Image, Material,
    Mesh, Node, NormalMaterialTexture, PbrMetallicRoughness, Primitive, Sampler,
    Scene, Texture, TextureInfo,
)

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / 'modules' / 'infrastructure'
TEXTUREDIR = ROOT / 'textures'
RAIL_Z = 0.22
GAUGE = 1.435

# UV distances specify the real size represented by a full repeat of the image.
# Every image is an individual tile, never an atlas repeatedly mapped to a face.
MATERIALS = {
    'stone':   {'image': 'stone',   'uv_m': (1.00, 1.00), 'roughness': 0.90, 'metallic': 0},
    'paving':  {'image': 'paving',  'uv_m': (0.70, 0.70), 'roughness': 0.94, 'metallic': 0},
    # An 8 m tile contains exactly ten mirrored image repeats on each axis,
    # so matching neighboring plaza tiles have the same colour at their seam.
    'plaza_paving': {'image': 'paving', 'uv_m': (0.80, 0.80), 'roughness': 0.94, 'metallic': 0},
    'brick':   {'image': 'retaining_brick', 'uv_m': (0.68, 0.56), 'roughness': 0.93, 'metallic': 0},
    'ballast': {'image': 'ballast', 'uv_m': (0.35, 0.35), 'roughness': 1.00, 'metallic': 0},
    'wood':    {'image': 'wood',    'uv_m': (2.00, 1.20), 'roughness': 0.90, 'metallic': 0},
    'rail':    {'image': 'rail',    'uv_m': (0.80, 0.80), 'roughness': 0.60, 'metallic': 0.65},
    'rail_top':{'image': 'rail',    'uv_m': (0.80, 0.80), 'roughness': 0.30, 'metallic': 0.85,
                'tint': (0.70, 0.86, 1.0, 1)},
    'safety':  {'image': 'stone',   'uv_m': (1.00, 1.00), 'roughness': 0.90, 'metallic': 0,
                'tint': (0.72, 0.45, 0.11, 1)},
}


class Part:
    """Mesh consisting of material-specific independent flat-shaded faces."""
    def __init__(self, name):
        self.name = name
        self.sections = defaultdict(lambda: {'p': [], 'n': [], 'uv': [], 'idx': []})

    def polygon(self, material, vertices, uv_axes=None):
        vertices = np.asarray(vertices, dtype=float)
        normal = np.cross(vertices[1] - vertices[0], vertices[2] - vertices[0])
        length = np.linalg.norm(normal)
        if length < 1e-10:
            raise ValueError(f'degenerate face in {self.name}: {vertices}')
        normal /= length
        if uv_axes is None:
            axis = int(np.argmax(np.abs(normal)))
            uv_axes = {0: (1, 2), 1: (0, 2), 2: (0, 1)}[axis]
        repeat = MATERIALS[material]['uv_m']
        uv = vertices[:, uv_axes] / np.asarray(repeat)
        sec = self.sections[material]
        first = len(sec['p'])
        sec['p'].extend(vertices.tolist())
        sec['n'].extend([normal.tolist()] * len(vertices))
        sec['uv'].extend(uv.tolist())
        # All supplied polygons are convex; rail caps are triangulated separately.
        for i in range(1, len(vertices)-1):
            sec['idx'].extend([first, first+i, first+i+1])


def box(part, material, bounds, omit_top=False):
    (x0,y0,z0),(x1,y1,z1) = bounds
    faces = [
        [(x0,y1,z0),(x1,y1,z0),(x1,y0,z0),(x0,y0,z0)],
        [(x0,y1,z0),(x0,y0,z0),(x0,y0,z1),(x0,y1,z1)],
        [(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)],
        [(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)],
        [(x1,y1,z0),(x0,y1,z0),(x0,y1,z1),(x1,y1,z1)],
    ]
    if not omit_top:
        faces.append([(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)])
    for f in faces:
        part.polygon(material, f)


def platform():
    parts = []
    part=Part('platform_foundation'); box(part,'stone',[(-2,0,0),(2,8,.16)]); parts.append(part)
    # A 1 mm inset at the ends keeps the stone pier faces from z-fighting.
    part=Part('brick_retaining_wall'); box(part,'brick',[(-1.985,.001,.16),(1.985,7.999,.84)]); parts.append(part)
    part=Part('stone_wall_piers')
    for x0,x1 in ((-2,-1.96),(1.96,2)):
        for y0,y1 in ((0,.09),(3.91,4.09),(7.91,8)):
            box(part,'stone',[(x0,y0,.16),(x1,y1,.84)])
    parts.append(part)
    part=Part('stone_coping')
    for x0,x1 in ((-2,-1.7),(1.7,2)):
        box(part,'stone',[(x0,0,.84),(x1,8,1)])
    parts.append(part)
    part=Part('platform_paving')
    box(part,'paving',[(-1.7,0,.84),(1.7,8,1)],omit_top=True)
    for x0,x1,mat in ((-1.7,-1.64,'paving'),(-1.64,-1.62,'safety'),
                      (-1.62,1.62,'paving'),(1.62,1.64,'safety'),(1.64,1.7,'paving')):
        part.polygon(mat,[(x0,0,1),(x1,0,1),(x1,8,1),(x0,8,1)])
    parts.append(part)
    return parts


def rail(name, center):
    part = Part(name)
    # A simple twelve-sided flat-foot rail: 160 mm foot, narrow web, 90 mm head.
    # The 80 mm profile rises from sleeper top at 0.14 to running surface at 0.22 m.
    profile=[(-.08,.14),(.08,.14),(.08,.155),(.022,.165),(.022,.20),
             (.045,.205),(.045,.22),(-.045,.22),(-.045,.205),(-.022,.20),
             (-.022,.165),(-.08,.155)]
    for i, (x,z) in enumerate(profile):
        xx,zz=profile[(i+1)%len(profile)]
        # Profile is CCW when seen in X/Z; this winding faces outward.
        vertices=[(center+x,8,z),(center+xx,8,zz),
                  (center+xx,0,zz),(center+x,0,z)]
        vertical = abs(zz-z) > abs(xx-x)
        part.polygon('rail_top' if i==6 else 'rail', vertices,
                     uv_axes=(1,2) if vertical else (1,0))
    # Ear-clipped front/back caps reproduce the complete concave rail profile.
    for a,b,c in triangulate_profile(profile):
        cap=[(center+x,z) for x,z in (a,b,c)]
        # X/Z points are counter-clockwise; cross product points -Y.
        part.polygon('rail',[(x,0,z) for x,z in cap],uv_axes=(0,2))
        part.polygon('rail',[(x,8,z) for x,z in reversed(cap)],uv_axes=(0,2))
    return part


def triangulate_profile(profile):
    """Triangulate the simple, counter-clockwise rail profile by ear clipping."""
    remaining=list(profile)
    triangles=[]
    def cross(a,b,c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def inside(p,a,b,c):
        return min(cross(a,b,p),cross(b,c,p),cross(c,a,p)) >= -1e-12
    while len(remaining)>3:
        for i,b in enumerate(remaining):
            a=remaining[i-1]; c=remaining[(i+1)%len(remaining)]
            if cross(a,b,c) <= 1e-12:
                continue
            if any(inside(p,a,b,c) for j,p in enumerate(remaining)
                   if j not in ((i-1)%len(remaining),i,(i+1)%len(remaining))):
                continue
            triangles.append((a,b,c)); remaining.pop(i)
            break
        else:
            raise ValueError('Rail profile could not be triangulated')
    triangles.append(tuple(remaining))
    return triangles


def track():
    parts=[]
    part=Part('ballast_bed'); box(part,'ballast',[(-1.5,0,0),(1.5,8,.08)]); parts.append(part)
    part=Part('wooden_sleepers')
    for i in range(12):
        y=(i+.5)*8/12
        box(part,'wood',[(-1.25,y-.12,.08),(1.25,y+.12,.14)])
    parts.append(part)
    parts.extend([rail('rail_left',-GAUGE/2),rail('rail_right',GAUGE/2)])
    return parts


def ramp():
    parts=[]
    part=Part('ramp_retaining_wall')
    # The side triangles run from ground at y=0 to full platform height at y=8.
    part.polygon('brick',[(-2,8,0),(-2,0,0),(-2,8,1)],uv_axes=(1,2))
    part.polygon('brick',[(2,0,0),(2,8,0),(2,8,1)],uv_axes=(1,2))
    part.polygon('brick',[(2,8,0),(-2,8,0),(-2,8,1),(2,8,1)],uv_axes=(0,2))
    part.polygon('stone',[(-2,8,0),(2,8,0),(2,0,0),(-2,0,0)])
    parts.append(part)
    part=Part('ramp_sloped_deck')
    for x0,x1,mat in ((-2,-1.7,'stone'),(-1.7,-1.64,'paving'),
                      (-1.64,-1.62,'safety'),(-1.62,1.62,'paving'),
                      (1.62,1.64,'safety'),(1.64,1.7,'paving'),(1.7,2,'stone')):
        part.polygon(mat,[(x0,0,0),(x1,0,0),(x1,8,1),(x0,8,1)],uv_axes=(0,1))
    parts.append(part)
    return parts


def plaza():
    parts=[]
    part=Part('plaza_stone_base'); box(part,'stone',[(-4,0,0),(4,8,.1)]); parts.append(part)
    part=Part('plaza_continuous_paving')
    box(part,'plaza_paving',[(-4,0,.1),(4,8,.12)])
    parts.append(part)
    return parts


def checked_image(path):
    """Re-encode as power-of-two PNG for mipmapped repeats in WebGL 1 and 2."""
    with PILImage.open(path) as im:
        if im.mode not in ('RGB','RGBA'):
            im=im.convert('RGB')
        pot=tuple(1 << (n-1).bit_length() for n in im.size)
        if im.size != pot:
            im=im.resize(pot, PILImage.Resampling.LANCZOS)
        out=io.BytesIO(); im.save(out,format='PNG',optimize=True)
        return out.getvalue()


def export(name, parts, texture_dir, out_dir):
    gltf = GLTF2(asset=Asset(version='2.0', generator='Riverdale procedural infrastructure'))
    # The supplied tile crops are not perfectly periodic. Mirroring alternate
    # repeats removes hard edge mismatches without blurring their image detail.
    gltf.samplers=[Sampler(wrapS=33648,wrapT=33648,magFilter=9729,minFilter=9987)]
    gltf.scenes=[Scene(name=name,nodes=[0])]; gltf.scene=0
    gltf.nodes=[Node(name='Z_UP_to_GLTF_Y_UP',rotation=[-math.sqrt(.5),0,0,math.sqrt(.5)],children=[])]
    data=bytearray()
    texture_cache={}
    material_cache={}
    material_images={}

    def add_bytes(raw, target=None):
        while len(data)%4: data.append(0)
        offset=len(data); data.extend(raw)
        gltf.bufferViews.append(BufferView(buffer=0,byteOffset=offset,byteLength=len(raw),target=target))
        return len(gltf.bufferViews)-1

    def add_accessor(array, kind, target, dtype):
        arr=np.asarray(array,dtype=dtype)
        if arr.ndim==1: arr=arr.reshape(-1,1)
        view=add_bytes(arr.tobytes(),target)
        bounds = {}
        if kind == 'VEC3': bounds={'min':arr.min(axis=0).astype(float).tolist(),
                                   'max':arr.max(axis=0).astype(float).tolist()}
        gltf.accessors.append(Accessor(bufferView=view,componentType=5126 if dtype=='<f4' else 5125,
                                       count=len(arr),type=kind,**bounds))
        return len(gltf.accessors)-1

    def add_texture(image_name, map_type, required=False):
        path=texture_dir / f'{image_name}_{map_type}.png'
        if not path.exists():
            if required: raise FileNotFoundError(f'Missing generated material image: {path}')
            return None
        if path not in texture_cache:
            view=add_bytes(checked_image(path))
            gltf.images.append(Image(name=path.name,mimeType='image/png',bufferView=view))
            gltf.textures.append(Texture(sampler=0,source=len(gltf.images)-1,name=path.stem))
            texture_cache[path]=len(gltf.textures)-1
        return texture_cache[path]

    def add_material(key):
        if key in material_cache: return material_cache[key]
        spec=MATERIALS[key]; image_name=spec['image']
        base=add_texture(image_name,'basecolor',True)
        normal=add_texture(image_name,'normal',True)
        orm=add_texture(image_name,'orm',True)
        pbr=PbrMetallicRoughness(baseColorFactor=list(spec.get('tint',(1,1,1,1))),
                                 metallicFactor=spec['metallic'],roughnessFactor=spec['roughness'],
                                 baseColorTexture=TextureInfo(index=base),
                                 metallicRoughnessTexture=TextureInfo(index=orm) if orm is not None else None)
        gltf.materials.append(Material(name=key,pbrMetallicRoughness=pbr,
                                       normalTexture=NormalMaterialTexture(index=normal,scale=.55) if normal is not None else None))
        material_cache[key]=len(gltf.materials)-1
        material_images[key]={k:f'{image_name}_{k}.png' for k in ('basecolor','normal','orm')
                              if (texture_dir/f'{image_name}_{k}.png').exists()}
        return material_cache[key]

    n_tris=0; all_positions=[]
    for part in parts:
        primitives=[]
        for mat,section in part.sections.items():
            pos=np.asarray(section['p'],dtype='<f4'); nor=np.asarray(section['n'],dtype='<f4')
            uv=np.asarray(section['uv'],dtype='<f4'); idx=np.asarray(section['idx'],dtype='<u4')
            if not (np.isfinite(pos).all() and np.isfinite(nor).all() and np.isfinite(uv).all()):
                raise ValueError(f'Nonfinite geometry in {part.name}')
            all_positions.append(pos)
            n_tris += len(idx)//3
            attributes=Attributes(POSITION=add_accessor(pos,'VEC3',34962,'<f4'),
                                  NORMAL=add_accessor(nor,'VEC3',34962,'<f4'),
                                  TEXCOORD_0=add_accessor(uv,'VEC2',34962,'<f4'))
            index=add_accessor(idx,'SCALAR',34963,'<u4')
            primitives.append(Primitive(attributes=attributes,indices=index,mode=4,material=add_material(mat)))
        gltf.meshes.append(Mesh(name=part.name,primitives=primitives))
        gltf.nodes.append(Node(name=part.name,mesh=len(gltf.meshes)-1))
        gltf.nodes[0].children.append(len(gltf.nodes)-1)
    gltf.buffers=[Buffer(byteLength=len(data))]
    gltf.set_binary_blob(bytes(data))
    out_dir.mkdir(parents=True,exist_ok=True)
    filename=name+'.glb'; gltf.save_binary(str(out_dir/filename))
    positions=np.concatenate(all_positions)
    return {'file':filename,'author_bounds_m':np.stack([positions.min(0),positions.max(0)]).astype(float).round(5).tolist(),
            'triangle_count':n_tris,'material_images':material_images,
            'texture_repeat_m':{name:list(MATERIALS[name]['uv_m']) for name in material_images},
            'mesh_names':[p.name for p in parts]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--textures',type=Path,default=TEXTUREDIR)
    parser.add_argument('--out',type=Path,default=OUTDIR)
    parser.add_argument('--only',choices=('platform_segment','track_segment','platform_ramp','plaza_tile'),
                        help='Rebuild just one module and update its existing manifest entry.')
    args=parser.parse_args()
    makers={'platform_segment':platform,'track_segment':track,'platform_ramp':ramp,'plaza_tile':plaza}
    if args.only:
        manifest_path=args.out/'manifest.json'
        if not manifest_path.is_file():
            parser.error('--only requires an existing manifest; run a full build first')
        manifest=json.loads(manifest_path.read_text())
        manifest['modules'][args.only]=export(args.only,makers[args.only](),args.textures,args.out)
        manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
        print(json.dumps(manifest['modules'][args.only],indent=2))
        return
    entries={name:export(name,fn(),args.textures,args.out) for name,fn in makers.items()}
    manifest={
        'description':'Repeating Victorian station infrastructure. Coordinates in meters.',
        'author_axes':'X right, Y depth, Z up; ground Z=0',
        'export_axes':'glTF Y-up: one root rotation of -90 degrees about X',
        'texture_sampler':'MIRRORED_REPEAT reduces discontinuities at generated tile edges; embedded maps are power-of-two for WebGL 1 support.',
        'repeat':'Platform and track are 8 m long; place succeeding pieces at Y + 8 m in author space.',
        'rail_center_gauge':GAUGE,'rail_running_surface_z':RAIL_Z,
        'ramp_join':'At author Y=8 m ramp is Z=1 m; join it to Y=0 m of a platform segment.',
        'plaza_top_z':.12,'modules':entries,
    }
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))


if __name__ == '__main__':
    main()
