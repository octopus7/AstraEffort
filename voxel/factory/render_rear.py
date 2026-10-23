"""Actual rear QA captures from saved assets; never modifies delivered BLENDs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import time
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "_tools"))
from blender_pipeline import point_at

def utc():
    return datetime.now(timezone.utc).isoformat()

qa = ROOT / "qa"
qa.mkdir(exist_ok=True)
started = utc()
timer = time.perf_counter()
captures = []
for slug in ("production_machine", "conveyor", "forklift", "generator"):
    src = ROOT / "assets" / slug / "large" / (slug + ".blend")
    meta = json.loads((src.parent / "metadata.json").read_text(encoding="utf-8"))
    bpy.ops.wm.open_mainfile(filepath=str(src))
    lo, hi = (Vector(v) for v in meta["bounds_m"])
    center = (lo + hi) * .5
    extent = max(hi - lo)
    scene = bpy.context.scene
    scene.camera.location = center + Vector((-1.35, 1.8, 1.2)).normalized() * extent * 3
    point_at(scene.camera, center)
    dst = qa / (slug + "_rear_large.png")
    scene.render.filepath = str(dst)
    capture_start = utc()
    capture_timer = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    captures.append({"asset": slug, "variant": "large", "view": "rear_left",
                     "source_blend": str(src.relative_to(ROOT)),
                     "source_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
                     "image": str(dst.relative_to(ROOT)),
                     "image_sha256": hashlib.sha256(dst.read_bytes()).hexdigest(),
                     "started_at_utc": capture_start, "finished_at_utc": utc(),
                     "elapsed_seconds": time.perf_counter() - capture_timer,
                     "camera_location": list(scene.camera.location),
                     "camera_rotation_radians": list(scene.camera.rotation_euler),
                     "orthographic_scale": scene.camera.data.ortho_scale,
                     "engine": scene.render.engine, "samples": scene.cycles.samples,
                     "threads": scene.render.threads, "resolution": [768, 768]})
(qa / "capture_manifest.json").write_text(json.dumps({
    "actual_blender_renders": True, "started_at_utc": started,
    "finished_at_utc": utc(), "elapsed_seconds": time.perf_counter() - timer,
    "captures": captures}, indent=2), encoding="utf-8")
print("FACTORY_REAR_QA_COMPLETE", flush=True)
