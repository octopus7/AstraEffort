import bpy,math
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
v=[];f=[];NX=200;NY=40
for j in range(NY+1):
 for i in range(NX+1):
  x=-50+i*100/NX;y=-50+(16.5+2*math.sin(x*.07))*j/NY;v.append((x,-y,-.18))
for j in range(NY):
 for i in range(NX):
  a=j*(NX+1)+i;f.append((a+NX+1,a+NX+2,a+1,a))
me=bpy.data.meshes.new('SeaWaves');me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new('SeaWaves',me);bpy.context.collection.objects.link(o);o.select_set(True);bpy.context.view_layer.objects.active=o
for p in me.polygons:p.use_smooth=True
bpy.ops.export_scene.fbx(filepath='D:/github/AstraEffort/ForestDemo/Work/medium/TexturePass/Source/SeaWaves.fbx',use_selection=True,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',bake_anim=False)
