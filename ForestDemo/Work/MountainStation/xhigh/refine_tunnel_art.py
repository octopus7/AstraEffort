import bpy,math,json
from mathutils import Vector
from pathlib import Path
from datetime import datetime,timezone
work=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh');out=work/'SourceArt'
bpy.ops.wm.open_mainfile(filepath=str(out/'AlderPass.blend'))
o=bpy.data.objects['Tunnel'];px=32;py=-8.944;ang=math.atan(.336)
def p(t,u,z):return (px+math.cos(ang)*t-math.sin(ang)*u,py+math.sin(ang)*t+math.cos(ang)*u,z)
# Ground the rock crown and keep its overhang behind the masonry entrance.
adj=[[] for _ in o.data.vertices]
for e in o.data.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
seen=set();trimmed=0
for seed in range(len(adj)):
 if seed in seen:continue
 q=[seed];component=[];seen.add(seed)
 while q:
  i=q.pop();component.append(i)
  for j in adj[i]:
   if j not in seen:seen.add(j);q.append(j)
 if len(component)==42:
  for i in component:
   v=o.data.vertices[i];t=(v.co.x-px)*math.cos(ang)+(v.co.y-py)*math.sin(ang)
   if t<.65:v.co.x+=(.65-t)*math.cos(ang);v.co.y+=(.65-t)*math.sin(ang);trimmed+=1
v=[];f=[];n=25;ts=[.6,3,7,11,15.5]
for t in ts:
 for i in range(n):
  a=i*math.pi/(n-1);v.append(p(t,math.cos(a)*9,3.48+math.sin(a)*5.3))
for row in range(len(ts)-1):
 for i in range(n-1):f.append((row*n+i,row*n+i+1,(row+1)*n+i+1,(row+1)*n+i))
inner=len(v)
for i in range(n):
 a=i*math.pi/(n-1);v.append(p(.6,math.cos(a)*2.92,3.48+math.sin(a)*2.92))
for i in range(n-1):f.append((i,i+1,inner+i+1,inner+i))
for s in [-1,1]:
 k=len(v);v.extend([p(.6,s*2.92,.22),p(.6,s*9,.22),p(.6,s*9,3.48),p(.6,s*2.92,3.48)]);f.append(tuple(range(k,k+4)))
 k=len(v);v.extend([p(.6,s*9,.22),p(15.5,s*9,.22),p(15.5,s*9,3.48),p(.6,s*9,3.48)]);f.append(tuple(range(k,k+4)))
mesh=bpy.data.meshes.new('Grounded_tunnel_rock_mass');mesh.from_pydata(v,[],f);mesh.materials.append(bpy.data.materials['Rock']);mesh.update()
for face in mesh.polygons:face.use_smooth=True
mass=bpy.data.objects.new('Grounded_tunnel_rock_mass',mesh);bpy.context.collection.objects.link(mass)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);mass.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.join()
bpy.ops.export_scene.fbx(filepath=str(out/'Tunnel.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,global_scale=1,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',bake_anim=False,add_leaf_bones=False)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'AlderPass.blend'))
manifest=json.loads((out/'geometry_manifest.json').read_text());manifest['assemblies']['Tunnel']['vertices']=len(o.data.vertices);manifest['assemblies']['Tunnel']['polygons']=len(o.data.polygons);manifest['tunnel_refinement']='Grounded rock shell outside vaulted clearance; crown clipped behind front masonry.';(out/'geometry_manifest.json').write_text(json.dumps(manifest,indent=2))
(work/'Evidence/tunnel_refinement.json').write_text(json.dumps({'finished_at_utc':datetime.now(timezone.utc).isoformat(),'trimmed_crown_vertices':trimmed,'shell_vertices_added':len(v)},indent=2))
