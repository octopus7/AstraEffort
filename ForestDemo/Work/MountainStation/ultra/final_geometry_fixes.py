import bpy,bmesh,math
from mathutils import Vector
ROOT=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra'
bpy.ops.wm.open_mainfile(filepath=ROOT+'/SourceArt/AlderPass.blend')
o=bpy.data.objects['SM_Fences'];bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.x<-20],context='VERTS');bm.to_mesh(o.data);bm.free()
# Text must be readable in UE's left-handed coordinate basis after the scene's
# handedness conversion. Mirror local horizontal glyph coordinates only.
labels=[(-5,.475),(1.37,.47),(10,-3.26),(-10.05,3.86),(17,4.27),(-24,7.925),(8,16.925),(-22,-7.078)]
a=math.atan(.024*34);forward=Vector((math.cos(a),math.sin(a),0));horiz=Vector((math.sin(a),-math.cos(a),0));centre=Vector((31,-9+.012*34**2,.82+.0015*13**2-.25))+forward*(-.90)+Vector((0,0,5.55))
unmatched=[]
for v in bpy.data.objects['SM_Lettering'].data.vertices:
    if v.co.x>28:v.co-=2*(v.co-centre).dot(horiz)*horiz;continue
    candidates=[(cx,cy) for cx,cy in labels if abs(v.co.y-cy)<.08 and abs(v.co.x-cx)<3]
    if not candidates:unmatched.append(tuple(v.co));continue
    cx,cy=min(candidates,key=lambda p:abs(v.co.x-p[0]));v.co.x=2*cx-v.co.x
assert not unmatched,str(unmatched[:10])
for name in ['SM_Fences','SM_Lettering']:
    o=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.export_scene.fbx(filepath=ROOT+'/SourceArt/'+name+'.fbx',use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,axis_forward='Y',axis_up='Z',mesh_smooth_type='FACE',use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False)
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/SourceArt/AlderPass.blend')
print('FINAL_GEOMETRY_FIXED',flush=True)
