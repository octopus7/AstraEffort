import bpy,math,json
from pathlib import Path
from datetime import datetime,timezone
work=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh');out=work/'SourceArt'
bpy.ops.wm.open_mainfile(filepath=str(out/'AlderPass.blend'));o=bpy.data.objects['Tunnel'];a=math.atan(.336);adj=[[] for _ in o.data.vertices]
for e in o.data.edges:
 i,j=e.vertices;adj[i].append(j);adj[j].append(i)
seen=set();changed=0
for seed in range(len(adj)):
 if seed in seen:continue
 q=[seed];seen.add(seed);component=[]
 while q:
  i=q.pop();component.append(i)
  for j in adj[i]:
   if j not in seen:seen.add(j);q.append(j)
 if len(component)==42:
  for i in component:
   v=o.data.vertices[i];t=(v.co.x-32)*math.cos(a)+(v.co.y+8.944)*math.sin(a)
   if t<.65:v.co.x+=(.65-t)*math.cos(a);v.co.y+=(.65-t)*math.sin(a);changed+=1
o.data.update();bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.export_scene.fbx(filepath=str(out/'Tunnel.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,global_scale=1,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',bake_anim=False,add_leaf_bones=False)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'AlderPass.blend'))
(work/'Evidence/tunnel_crown_trim.json').write_text(json.dumps({'finished_at_utc':datetime.now(timezone.utc).isoformat(),'trimmed_vertices':changed,'reason':'Blender subdivision-2 icospheres have 42 vertices, corrected connected-component selection.'},indent=2))
