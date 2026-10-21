"""Reconstruct deterministic crown in WORLD coordinates, preserving the grounded shell."""
import bpy,bmesh,math,random,json
from mathutils import Vector
from pathlib import Path
from datetime import datetime,timezone
work=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh');out=work/'SourceArt'
bpy.ops.wm.open_mainfile(filepath=str(out/'AlderPass.blend'));o=bpy.data.objects['Tunnel'];a=math.atan(.336)
bm=bmesh.new();bm.from_mesh(o.data);seen=set();remove=[];components=0
for seed in bm.verts:
 if seed in seen:continue
 q=[seed];seen.add(seed);comp=[]
 while q:
  v=q.pop();comp.append(v)
  for edge in v.link_edges:
   w=edge.other_vert(v)
   if w not in seen:seen.add(w);q.append(w)
 if len(comp)==42:remove.extend(comp);components+=1
assert components==26,components
bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(o.data);bm.free()
random.seed(21743)
# Exactly the random draws preceding the original tunnel crown in create_art.py.
for i in range(360):
 random.uniform(-49,49);random.choice([-1,1]);random.uniform(1.45,2.06);random.uniform(.07,.16)
new=[];trimmed=0
for i in range(26):
 t=random.uniform(1,15);u=random.uniform(-7,7);z=6+random.uniform(0,2.3)+max(0,2-abs(u))*.5
 pos=(32+math.cos(a)*t-math.sin(a)*u,-8.944+math.sin(a)*t+math.cos(a)*u,z)
 scale=(random.uniform(2,4),random.uniform(2,4),random.uniform(1.4,3))
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=pos);rock=bpy.context.object;rock.scale=scale
 rock.data.materials.append(bpy.data.materials['Rock' if i%3 else 'RockLight']);bpy.context.view_layer.update();matrix=rock.matrix_world.copy();inv=matrix.inverted()
 for v in rock.data.vertices:
  w=matrix@v.co;t0=(w.x-32)*math.cos(a)+(w.y+8.944)*math.sin(a)
  if t0<.65:w.x+=(.65-t0)*math.cos(a);w.y+=(.65-t0)*math.sin(a);trimmed+=1
  u0=-(w.x-32)*math.sin(a)+(w.y+8.944)*math.cos(a)
  if abs(u0)<3.2:w.z=max(w.z,3.48+math.sqrt(max(0,3.2**2-u0**2))+.2)
  v.co=inv@w
 for face in rock.data.polygons:face.use_smooth=True
 new.append(rock)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
for rock in new:rock.select_set(True)
bpy.context.view_layer.objects.active=o;bpy.ops.object.join()
bpy.ops.export_scene.fbx(filepath=str(out/'Tunnel.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,global_scale=1,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',bake_anim=False,add_leaf_bones=False)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'AlderPass.blend'))
(work/'Evidence/tunnel_source_final.json').write_text(json.dumps({'finished_at_utc':datetime.now(timezone.utc).isoformat(),'reconstructed_rock_components':components,'world_space_trimmed_vertices':trimmed,'supersedes':'tunnel_crown_trim.json (local-space attempt was not imported into final UE map)'},indent=2))
