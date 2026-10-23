"""Additional actual rear views of the harbor deliverables; leaves BLEND files intact."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import time
import bpy
from mathutils import Vector

root = Path(__file__).resolve().parent
source = json.loads((root / 'capture_manifest.json').read_text(encoding='utf-8'))
records = []
for item in source['captures']:
    directory = root / 'assets' / item['asset'] / item['variant']
    blend = directory / (item['asset'] + '.blend')
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    scene = bpy.context.scene
    target = Vector(item['settings']['target'])
    camera = scene.camera
    camera.location.y = 2 * target.y - camera.location.y
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4
    png = directory / 'preview_rear.png'
    scene.render.filepath = str(png)
    started = datetime.now(timezone.utc).isoformat()
    tick = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    records.append({
        'asset': item['asset'], 'variant': item['variant'],
        'image': png.relative_to(root).as_posix(),
        'started_at_utc': started,
        'finished_at_utc': datetime.now(timezone.utc).isoformat(),
        'elapsed_seconds': time.perf_counter() - tick,
        'source_blend_sha256': hashlib.sha256(blend.read_bytes()).hexdigest(),
        'image_sha256': hashlib.sha256(png.read_bytes()).hexdigest(),
        'settings': {**item['settings'], 'camera_location': list(camera.location),
                     'camera_rotation_radians': list(camera.rotation_euler), 'view': 'Rear three-quarter'}
    })
(root / 'capture_rear_manifest.json').write_text(json.dumps({
    'actual_blender_renders': True,
    'source_blends_unmodified': True,
    'captures': records
}, indent=2), encoding='utf-8')
