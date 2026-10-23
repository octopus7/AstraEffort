"""Render the back of each saved farm model without changing the deliverables."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import time
import sys
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent


def stamp():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    captures = []
    primary = json.loads((ROOT / 'capture_manifest.json').read_text(encoding='utf-8'))
    requested = sys.argv[sys.argv.index('--asset') + 1] if '--asset' in sys.argv else None
    if requested:
        primary['captures'] = [item for item in primary['captures'] if item['asset'] == requested]
        captures = [item for item in json.loads((ROOT / 'capture_rear_manifest.json').read_text(encoding='utf-8'))['captures'] if item['asset'] != requested]
    for capture in primary['captures']:
        slug, variant = capture['asset'], capture['variant']
        folder = ROOT / 'assets' / slug / variant
        blend = folder / (slug + '.blend')
        bpy.ops.wm.open_mainfile(filepath=str(blend))
        scene = bpy.context.scene
        camera = scene.camera
        target = Vector(capture['settings']['target'])
        camera.location.y = 2 * target.y - camera.location.y
        camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.threads_mode = 'FIXED'
        scene.render.threads = 4
        output = folder / 'preview_rear.png'
        scene.render.filepath = str(output)
        started, t0 = stamp(), time.perf_counter()
        bpy.ops.render.render(write_still=True)
        captures.append({
            'asset': slug,
            'variant': variant,
            'image': output.relative_to(ROOT).as_posix(),
            'started_at_utc': started,
            'finished_at_utc': stamp(),
            'elapsed_seconds': time.perf_counter() - t0,
            'source_blend_sha256': sha(blend),
            'image_sha256': sha(output),
            'settings': {**capture['settings'],
                         'camera_location': list(camera.location),
                         'camera_rotation_radians': list(camera.rotation_euler),
                         'view': 'Rear three-quarter, matching camera for both resolutions'}
        })
    (ROOT / 'capture_rear_manifest.json').write_text(json.dumps({
        'actual_blender_renders': True,
        'saved_asset_blends_unmodified': True,
        'captures': captures
    }, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
