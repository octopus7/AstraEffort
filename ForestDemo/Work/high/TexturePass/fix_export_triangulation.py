import bpy,json
from pathlib import Path
R=Path('D:/github/AstraEffort/ForestDemo/Work/high/TexturePass')
audit=json.loads((R/'uv_audit.json').read_text());count=0
for base,info in audit['meshes'].items():
 for name in info['variants']:
  ob=bpy.data.objects[name];assert not ob.modifiers,name
  old=ob.data;old.calc_loop_triangles();uv=old.uv_layers.active.data
  triangles=list(old.loop_triangles)
  new=bpy.data.meshes.new(name+'_ExplicitTriangles');new.from_pydata([v.co[:] for v in old.vertices],[],[list(t.vertices) for t in triangles]);new.update()
  for m in old.materials:new.materials.append(m)
  layer=new.uv_layers.new(name='UVMap')
  for face,tri in zip(new.polygons,triangles):
   face.material_index=tri.material_index;face.use_smooth=old.polygons[tri.polygon_index].use_smooth
   for dst,src in zip(face.loop_indices,tri.loops):layer.data[dst].uv=uv[src].uv
  ob.data=new;bpy.ops.object.select_all(action='DESELECT');ob.hide_set(False);ob.select_set(True);bpy.context.view_layer.objects.active=ob
  bpy.ops.export_scene.fbx(filepath=str(R/'Source/FBX'/(name+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',axis_forward='-Y',axis_up='Z',bake_anim=False,mesh_smooth_type='FACE',use_mesh_modifiers=True)
  ob.hide_set(True);count+=1
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Source/UVAssetsTriangulated.blend'))
print('HIGH_EXPLICIT_TRIANGLES_EXPORTED',count)
