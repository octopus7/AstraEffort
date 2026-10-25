import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'source.blend'))
old=bpy.data.objects.get('SM_DockStep');bpy.data.objects.remove(old,do_unlink=True)
sections=[(-1.4,-.30),(-.35,.16),(.3,.16),(1.8,0)]
verts=[]
for x,z in sections:verts.extend([(x,-1.35,z),(x,1.35,z),(x,-1.35,z-.12),(x,1.35,z-.12)])
faces=[]
for i in range(len(sections)-1):
    k=i*4;n=k+4;faces.extend([(k,n,n+1,k+1),(k+2,k+3,n+3,n+2),(k,k+2,n+2,n),(k+1,n+1,n+3,k+3)])
faces.extend([(0,1,3,2),(12,14,15,13)])
me=bpy.data.meshes.new('DockRamp');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('SM_DockStep',me);bpy.context.collection.objects.link(o);me.materials.append(bpy.data.materials['Timber'])
bpy.context.view_layer.objects.active=o;o.select_set(True)
mod=o.modifiers.new('Triangulate','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
import math
u0=me.uv_layers.new(name='Unique');u1=me.uv_layers.new(name='Physical128');n=math.ceil(math.sqrt(len(me.polygons)));cell=1/n;pad=2.1/1024
for i,p in enumerate(me.polygons):
    a,b,c=[me.vertices[k].co for k in p.vertices];e=(b-a).normalized();v=(b-a).cross(c-a).normalized().cross(e)
    for j,li in enumerate(p.loop_indices):
        x=(i%n)*cell+pad;y=(i//n)*cell+pad;w=cell-2*pad;u0.data[li].uv=[(x,y),(x+w,y),(x,y+w)][j];d=me.vertices[p.vertices[j]].co-a;u1.data[li].uv=(d.dot(e)/8,d.dot(v)/8)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(P/'FBX/SM_DockStep.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,axis_forward='-Y',axis_up='Z',mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source.blend'))
(P/'dock_ramp.json').write_text(json.dumps({'name':'SM_DockStep','purpose':'Continuous dock access over quay wall then down to dock','local_x_top_z_m':sections,'width_m':2.7,'placement_m':[6.4,1,0],'connection_world_x_z_m':[[5,-.3],[6.05,.16],[6.7,.16],[8.2,0]],'quay_wall_top_m':.1,'UV1_density':128},indent=2))
