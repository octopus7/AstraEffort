import bpy, os, json, time
from mathutils import Vector
from datetime import datetime, timezone
ROOT=os.path.dirname(os.path.abspath(__file__))
def utc():return datetime.now(timezone.utc).isoformat()
started=utc();run=time.time()
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'mine_elevator.blend'))
scene=bpy.context.scene;camera=scene.camera;asset=bpy.data.collections['ASSET']
scene.view_settings.exposure=-.3
def frame_asset(cam):
    bpy.context.view_layer.update();inv=cam.matrix_world.inverted()
    projected=[inv@(o.matrix_world@v.co) for o in asset.objects if o.type=='MESH' for v in o.data.vertices]
    lo=[min(p[i] for p in projected) for i in (0,1)];hi=[max(p[i] for p in projected) for i in (0,1)]
    cam.location+=cam.rotation_euler.to_quaternion()@Vector(((lo[0]+hi[0])*.5,(lo[1]+hi[1])*.5,0))
    cam.data.ortho_scale=max((hi[0]-lo[0])/.8,(hi[1]-lo[1])*(1440/1080)/.8)
    bpy.context.view_layer.update()
with open(os.path.join(ROOT,'capture_manifest.json'),encoding='utf-8') as f:manifest=json.load(f)
if 'superseded_first_capture' not in manifest:manifest['superseded_first_capture']=manifest['captures']
else:manifest.setdefault('superseded_additional_captures',[]).extend(manifest['captures'])
captures=[]
for name,loc,target in [('hero',(11,-18,11.3),(.54,.15,3.95)),('rear',(11,18,11.7),(.54,.25,3.95))]:
    camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();frame_asset(camera)
    scene.render.filepath=os.path.join(ROOT,'renders',name+'.png')
    before=utc();t=time.time();bpy.ops.render.render(write_still=True)
    captures.append({'view':name,'path':'renders/'+name+'.png','started_at_utc':before,'finished_at_utc':utc(),'elapsed_seconds':time.time()-t,
        'camera_location':list(camera.location),'camera_rotation_euler':list(camera.rotation_euler),'initial_look_at':list(target),'projection':'orthographic','ortho_scale':camera.data.ortho_scale,
        'framing':'Transformed asset vertices centered at 80 percent maximum image dimension','engine':'Cycles','device':'CPU','threads':4,'samples':32,'denoising':True,'resolution':[1440,1080],
        'color_management':'AgX / Medium High Contrast / exposure -0.3','authenticity':'Actual Blender render of delivered model; no generated image compositing.'})
manifest['captures']=captures
manifest['framing_correction']={'started_at_utc':started,'finished_at_utc':utc(),'elapsed_seconds':time.time()-run,'reason':'First capture cropped top and base because landscape orthographic scale required aspect correction.'}
camera.location=(11,-18,11.3);camera.rotation_euler=(Vector((.54,.15,3.95))-camera.location).to_track_quat('-Z','Y').to_euler();frame_asset(camera)
scene.render.filepath=os.path.join(ROOT,'renders','hero.png')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'mine_elevator.blend'))
with open(os.path.join(ROOT,'capture_manifest.json'),'w',encoding='utf-8') as f:json.dump(manifest,f,indent=2)
print('FINAL_CAPTURES_FINISHED',utc(),flush=True)
