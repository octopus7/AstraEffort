import bpy,math,json
from pathlib import Path
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'source.blend'))
bpy.data.objects.remove(bpy.data.objects['SM_QuayWall'],do_unlink=True)
sections=[(-50,.1),(25.8,.1),(26,-.12),(30,-.12),(30.2,.1),(50,.1)]
verts=[]
for y,z in sections:verts.extend([(-.325,y,z),(.325,y,z),(-.325,y,-2),(.325,y,-2)])
faces=[]
for i in range(len(sections)-1):
    k=4*i;n=k+4;faces.extend([(k,k+1,n+1,n),(k+2,n+2,n+3,k+3),(k,k+4,k+6,k+2),(k+1,k+3,k+7,k+5)])
faces.extend([(0,2,3,1),(20,21,23,22)])
me=bpy.data.meshes.new('QuayWithTimberBridgeNotch');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('SM_QuayWall',me);bpy.context.collection.objects.link(o);me.materials.append(bpy.data.materials['Stone'])
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
mod=o.modifiers.new('Triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name);me=o.data
u0=me.uv_layers.new(name='Unique');u1=me.uv_layers.new(name='Physical128');n=math.ceil(math.sqrt(len(me.polygons)));cell=1/n;pad=2.1/1024
for i,p in enumerate(me.polygons):
    a,b,c=[me.vertices[k].co for k in p.vertices];e=(b-a).normalized();v=(b-a).cross(c-a).normalized().cross(e)
    for j,li in enumerate(p.loop_indices):
        x=(i%n)*cell+pad;y=(i//n)*cell+pad;w=cell-2*pad;u0.data[li].uv=[(x,y),(x+w,y),(x,y+w)][j];d=me.vertices[p.vertices[j]].co-a;u1.data[li].uv=(d.dot(e)/8,d.dot(v)/8)
bpy.ops.export_scene.fbx(filepath=str(P/'FBX/SM_QuayWall.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,axis_forward='-Y',axis_up='Z',mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source.blend'))
(P/'wall_notch.json').write_text(json.dumps({'name':'SM_QuayWall','y_top_z_m':sections,'bottom_z_m':-2,'width_m':.65,'purpose':'Recess wall under flat timber deck at design y28; retain normal quay top elsewhere','deck_clearance_m':.12},indent=2))
