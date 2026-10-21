import bpy,math
from pathlib import Path
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.01
def coast(x):return -2900+270*math.sin(x/1350)+120*math.sin(x/540)
vs=[];fs=[]
for j in range(26):
 for i in range(101):
  x=-5000+i*100;y=-5000+((coast(x)-100)+5000)*j/25;z=min(64,100+(y-coast(x))*.16+1.5);vs.append((x,y,z))
for j in range(25):
 for i in range(100):a=j*101+i;fs.append((a,a+1,a+102,a+101))
me=bpy.data.meshes.new('Seabed');me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new('SM_CausticsBed',me);bpy.context.collection.objects.link(ob);ob.select_set(True);bpy.context.view_layer.objects.active=ob
for p in me.polygons:p.use_smooth=True
m=bpy.data.materials.new('M_Seabed');me.materials.append(m)
bpy.ops.export_scene.fbx(filepath='D:/github/AstraEffort/ForestDemo/Work/high/TexturePass/Source/SM_CausticsBed.fbx',use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',bake_anim=False,mesh_smooth_type='FACE')
