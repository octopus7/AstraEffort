import bpy,math,json,time
from pathlib import Path
from datetime import datetime,timezone
work=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh');out=work/'SourceArt';started=time.time()
bpy.ops.wm.open_mainfile(filepath=str(out/'AlderPass.blend'))
def track(x):return -16+.004*(x+10)**2
def height(x,y):
 h=.18+.10*math.sin(x*.18)*math.cos(y*.17);rear=max(0,(y-7)/43)
 h+=rear**1.45*(9+8*math.exp(-((x-19)/21)**2)+4*math.sin(x*.055)**2)
 h+=12*math.exp(-((x-42)/13)**2-((y+1)/15)**2)
 h+=3.4*math.exp(-((x+42)/10)**2-((y-13)/20)**2)
 d=abs(y-track(x));fade=min(1,max(0,(d-4)/9));h=.22+(h-.22)*fade
 if -37<x<21 and -15<y<6:h=.22
 if x<-30:
  lane_blend=min(1,max(0,(abs(y+3)-3)/3));h=.22+(h-.22)*lane_blend
 return h
o=bpy.data.objects['Terrain'];count=0
for v in o.data.vertices:
 if v.co.z>-.01 and v.co.x<-30:
  new=height(v.co.x,v.co.y)
  if abs(new-v.co.z)>.00001:v.co.z=new;count+=1
o.data.update();bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.export_scene.fbx(filepath=str(out/'Terrain.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,global_scale=1,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',bake_anim=False,add_leaf_bones=False)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'AlderPass.blend'))
(work/'Evidence/approach_art_repair.json').write_text(json.dumps({'changed_vertices':count,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'execution_seconds':time.time()-started,'repair':'Flatten western approach lane at z0.22m with 3m shoulder transition, so lane and PlayerStart ground are connected.'},indent=2))
