"""Independent native-geometry review; produces Blender preview, not UE scene evidence."""
import bpy
import math
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source.blend'))
manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))

def cross2(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])

def clip_triangle(subject,clip):
    if cross2(*clip)<0:
        clip=tuple(reversed(clip))
    output=list(subject)
    for i in range(3):
        ca=clip[i]
        cb=clip[(i+1)%3]
        inp=output
        output=[]
        if not inp:
            break
        prev=inp[-1]
        pside=cross2(ca,cb,prev)
        for cur in inp:
            cside=cross2(ca,cb,cur)
            if cside>=-1e-12:
                if pside < -1e-12:
                    f=pside/(pside-cside)
                    output.append((prev[0]+f*(cur[0]-prev[0]),prev[1]+f*(cur[1]-prev[1])))
                output.append(cur)
            elif pside >= -1e-12:
                f=pside/(pside-cside)
                output.append((prev[0]+f*(cur[0]-prev[0]),prev[1]+f*(cur[1]-prev[1])))
            prev=cur
            pside=cside
    return abs(sum(output[i][0]*output[(i+1)%len(output)][1]-output[(i+1)%len(output)][0]*output[i][1] for i in range(len(output))))*.5 if len(output)>2 else 0.0

results=[]
for asset in manifest['assets']:
    obj=bpy.data.objects[asset['name']]
    uv=obj.data.uv_layers.active.data
    tris=[]
    grid={}
    size=96
    positive=[]
    tested=0
    max_overlap=0.0
    for face in obj.data.polygons:
        tri=tuple(tuple(uv[i].uv) for i in face.loop_indices)
        if len(tri)!=3:
            raise RuntimeError('Export not triangulated')
        index=len(tris)
        tris.append(tri)
        xmin,xmax=min(p[0] for p in tri),max(p[0] for p in tri)
        ymin,ymax=min(p[1] for p in tri),max(p[1] for p in tri)
        cells=[(xx,yy) for xx in range(math.floor(xmin*size),math.floor(xmax*size)+1)
                        for yy in range(math.floor(ymin*size),math.floor(ymax*size)+1)]
        candidates=set(j for cell in cells for j in grid.get(cell,[]))
        for j in candidates:
            tj=tris[j]
            if max(p[0] for p in tj)<=xmin+1e-10 or min(p[0] for p in tj)>=xmax-1e-10:
                continue
            if max(p[1] for p in tj)<=ymin+1e-10 or min(p[1] for p in tj)>=ymax-1e-10:
                continue
            tested+=1
            overlap=clip_triangle(tri,tj)
            max_overlap=max(max_overlap,overlap)
            if overlap>1e-9:
                if len(positive)<20:
                    positive.append({'triangle_a':index,'triangle_b':j,'overlap_uv_area':overlap})
        for cell in cells:
            grid.setdefault(cell,[]).append(index)
    result={'asset':asset['name'],'triangle_count':len(tris),'broadphase_candidate_pairs_tested':tested,
            'positive_overlap_examples':positive,'max_triangle_overlap_area':max_overlap,
            'positive_overlap_threshold_uv_area':1e-9,'passed':not positive}
    asset['uv']['overlap_check']='Exact 2D triangle clipping after 96x96 spatial-hash broadphase; positive-area threshold 1e-9 UV2'
    asset['uv']['overlap_validation']=result
    results.append(result)
    print('UV_OVERLAP',asset['name'],result['passed'],tested,flush=True)

manifest['uv_validation_at_utc']=datetime.now(timezone.utc).isoformat()
manifest['uv_overlap_all_passed']=all(v['passed'] for v in results)
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
(ROOT/'uv_validation.json').write_text(json.dumps(results,indent=2),encoding='utf-8')

positions={'SM_Barn':(-6,5,0),'SM_Shed':(6,5,0),'SM_Cart':(5,-2.2,0),
           'SM_FenceSegment':(-7,-2.1,0),'SM_Gate':(-2.9,-2.1,0),
           'SM_ToolCluster':(2,-6,0),'SM_Barrel':(-.5,-6,0),
           'SM_HayBale':(-3,-6,0),'SM_CropClump':(-5.5,-6,0)}
for name,loc in positions.items():
    bpy.data.objects[name].location=loc

ground=bpy.data.materials.new('Preview ground')
ground.diffuse_color=(.35,.39,.30,1)
ground.use_nodes=True
ground.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.35,.39,.30,1)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.035))
bpy.context.object.data.materials.append(ground)
bpy.context.object.name='Preview ground, not exported'
world=bpy.context.scene.world
world.use_nodes=True
world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.58,.68,.79,1)
world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.45
bpy.ops.object.light_add(type='SUN',location=(0,0,12))
sun=bpy.context.object
sun.rotation_euler=(math.radians(25),math.radians(-24),math.radians(-35))
sun.data.energy=2.3
sun.data.angle=.14
bpy.ops.object.light_add(type='AREA',location=(-8,-10,16))
bpy.context.object.data.energy=1700
bpy.context.object.data.shape='DISK'
bpy.context.object.data.size=14
bpy.ops.object.camera_add(location=(23,-34,25))
cam=bpy.context.object
target=Vector((-.7,.8,1.3))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO'
cam.data.ortho_scale=30
scene=bpy.context.scene
scene.camera=cam
scene.render.engine='CYCLES'
scene.cycles.samples=24
scene.cycles.use_denoising=True
scene.render.resolution_x=1920
scene.render.resolution_y=1320
scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(ROOT/'farm_assets_preview.png')
bpy.ops.render.render(write_still=True)
print('INSPECTION_COMPLETE',flush=True)
