"""Native VOX + PNG only. All transient render surfaces use reparsed VOX data."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
sys.dont_write_bytecode = True
import time
import struct
import numpy as np
import bpy

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parents[1] / '_tools'))
from build import make_assets, PALETTE
from voxelkit import write_vox, read_vox, reduce_half, grid_stats
from blender_pipeline import build_surface, add_studio


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    started = utc()
    t0 = time.perf_counter()
    build_start = time.perf_counter()
    assets = make_assets()
    build_seconds = time.perf_counter() - build_start
    requested = sys.argv[sys.argv.index('--asset') + 1] if '--asset' in sys.argv else None
    if requested:
        assets = [a for a in assets if a.slug == requested]
    assert assets
    captures, records = [], []
    write_json(ROOT / 'palette.json', {'indices': list(range(len(PALETTE))), 'rgba': PALETTE,
                                     'source': 'Kitchen BRIEF.md common palette; no extra shades'})
    for asset in assets:
        large = asset.grid
        assert max(large.shape) == 128 and all(n % 2 == 0 for n in large.shape)
        half = reduce_half(large)
        if asset.half_postprocess:
            asset.half_postprocess(half)
        bounds = grid_stats(large, asset.voxel_size)['bounds_m']
        for variant, authored, scale in [('large', large, asset.voxel_size),
                                         ('half', half, asset.voxel_size * 2)]:
            dst = ROOT / 'assets' / asset.slug / variant
            dst.mkdir(parents=True, exist_ok=True)
            vox = dst / (asset.slug + '.vox')
            native_started = utc()
            nt = time.perf_counter()
            write_vox(vox, authored)
            reopened = read_vox(vox)
            assert struct.unpack_from('<I', vox.read_bytes(), 4)[0] == 150
            assert np.array_equal(authored.data, reopened.data)
            assert authored.palette == reopened.palette[:len(authored.palette)]
            native_seconds = time.perf_counter() - nt
            surface_start = time.perf_counter()
            _, surface = build_surface(asset, reopened, scale)
            surface_seconds = time.perf_counter() - surface_start
            settings = add_studio(bounds)
            settings['camera_bounds_large_m'] = bounds
            settings['color_mode'] = 'RGB'
            settings['transparent'] = False
            settings['lights'] = [
                {'name': o.name, 'type': o.data.type, 'location': list(o.location),
                 'rotation_radians': list(o.rotation_euler), 'energy_w': o.data.energy,
                 'shape': o.data.shape, 'size_m': o.data.size}
                for o in bpy.context.scene.objects if o.type == 'LIGHT'
            ]
            settings['world_background_rgba'] = list(bpy.context.scene.world.node_tree.nodes['Background'].inputs[0].default_value)
            settings['world_strength'] = bpy.context.scene.world.node_tree.nodes['Background'].inputs[1].default_value
            image = dst / 'preview.png'
            bpy.context.scene.render.filepath = str(image)
            render_started = utc()
            rt = time.perf_counter()
            bpy.ops.render.render(write_still=True)
            render_seconds = time.perf_counter() - rt
            render_finished = utc()
            assert struct.unpack('>II', image.read_bytes()[16:24]) == (768, 768)
            capture = {
                'asset': asset.slug, 'variant': variant,
                'image': image.relative_to(ROOT).as_posix(),
                'native_file': vox.relative_to(ROOT).as_posix(),
                'started_at_utc': render_started, 'finished_at_utc': render_finished,
                'elapsed_seconds': render_seconds, 'settings': settings,
                'source_vox_sha256': sha(vox), 'image_sha256': sha(image),
                'rendered_from_reparsed_vox': True, 'actual_blender_render': True,
                'blender_version': bpy.app.version_string,
            }
            captures.append(capture)
            stats = grid_stats(reopened, scale)
            metadata = {
                'asset': asset.slug, 'label': asset.label, 'variant': variant,
                'format': 'MagicaVoxel VOX 150',
                'coordinate_system': 'X right, Y back, Z up; front -Y',
                'origin': 'XY grid center, bottom grid plane Z=0',
                'palette': PALETTE, 'notes': asset.notes,
                'half_method': '2x2x2 nonempty majority, higher palette index breaks ties',
                'half_postprocess': None, 'same_physical_grid_extents': True,
                'camera_bounds_source': 'large native occupied bounds',
                'native_roundtrip_passed': True, 'rendered_from_reparsed_vox': True,
                'surface': surface, **stats,
                'timing': {'native_write_roundtrip_started_at_utc': native_started,
                           'native_write_roundtrip_seconds': native_seconds,
                           'surface_build_seconds': surface_seconds,
                           'render_seconds': render_seconds},
                'sha256': {'native': sha(vox), 'preview': sha(image)},
            }
            write_json(dst / 'metadata.json', metadata)
            records.append({'asset': asset.slug, 'variant': variant, **metadata['timing']})
            print('NATIVE_PREVIEW_COMPLETE ' + asset.slug + ' ' + variant, flush=True)
            write_json(ROOT / 'render_progress.json', {'started_at_utc': started,
                       'updated_at_utc': utc(), 'completed_this_run': len(captures),
                       'latest': asset.slug + '/' + variant})
    if requested and (ROOT / 'capture_manifest.json').exists():
        existing = json.loads((ROOT / 'capture_manifest.json').read_text(encoding='utf-8'))['captures']
        captures = [c for c in existing if c['asset'] != requested] + captures
    write_json(ROOT / 'capture_manifest.json', {
        'actual_blender_renders': True,
        'source': 'Every PNG rendered from native VOX reparsed before transient surface construction.',
        'no_scene_or_exchange_mesh_saved': True,
        'command': 'blender.exe --background --factory-startup --threads 4 --python-exit-code 1 --python preview_pipeline.py',
        'captures': captures})
    timing = {'started_at_utc': started, 'finished_at_utc': utc(),
              'elapsed_seconds': time.perf_counter() - t0, 'authored_grid_build_seconds': build_seconds,
              'render_seconds': sum(r['render_seconds'] for r in records),
              'surface_build_seconds': sum(r['surface_build_seconds'] for r in records),
              'native_write_roundtrip_seconds': sum(r['native_write_roundtrip_seconds'] for r in records),
              'requested_asset': requested, 'records': records}
    write_json(ROOT / ('pipeline_timing_' + requested + '.json' if requested else 'pipeline_timing.json'), timing)


if __name__ == '__main__':
    main()
