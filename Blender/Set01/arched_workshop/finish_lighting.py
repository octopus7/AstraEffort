"""Fix area-emitter containment without modifying any asset mesh/export."""
import bpy
import json
import time
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'arched_workshop.blend'))
scene=bpy.context.scene
for obj in bpy.data.collections['STUDIO'].objects:
    if obj.type=='LIGHT' and obj.name.startswith('Interior overhead strip illumination') and obj.location.y>1:
        obj.data.size=1.4
    if obj.type=='LIGHT' and obj.name.startswith('Interior workbench task illumination'):
        obj.data.size=.60
manifest=json.loads(ROOT.joinpath('capture_manifest.json').read_text(encoding='utf8'))
manifest['previous_render_views']=manifest['views']
manifest['views']=[]
manifest['lighting_revision_started_at_utc']=datetime.now(timezone.utc).isoformat()
manifest['lighting_revision_reason']='Interior area emitters contained inside masonry shell to remove exterior light spill.'
for view,camera in [('hero','CAMERA | hero front left'),('rear','CAMERA | rear right'),('front_detail','CAMERA | low front opening')]:
    cam=bpy.data.objects[camera]
    scene.camera=cam
    scene.render.filepath=str(ROOT/'renders'/f'{view}.png')
    start=datetime.now(timezone.utc)
    begin=time.monotonic()
    bpy.ops.render.render(write_still=True)
    manifest['views'].append({'view':view,'path':f'renders/{view}.png','camera_location':list(cam.location),'camera_rotation_euler':list(cam.rotation_euler),'orthographic_scale':cam.data.ortho_scale,'started_at_utc':start.isoformat(),'finished_at_utc':datetime.now(timezone.utc).isoformat(),'render_seconds':time.monotonic()-begin})
    ROOT.joinpath('capture_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print('FINAL_CAPTURE',view,flush=True)
scene.camera=bpy.data.objects['CAMERA | hero front left']
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'arched_workshop.blend'))
manifest['lighting_revision_finished_at_utc']=datetime.now(timezone.utc).isoformat()
ROOT.joinpath('capture_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print('LIGHTING_FINISHED',flush=True)
