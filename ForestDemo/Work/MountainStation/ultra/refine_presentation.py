import bpy,math,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra'
bpy.ops.wm.open_mainfile(filepath=ROOT+'/SourceArt/AlderPass.blend')
terrain=bpy.data.objects['SM_Terrain'];dg=bpy.context.evaluated_depsgraph_get();bvh=BVHTree.FromObject(terrain,dg)
def height(x,y):
    hit=bvh.ray_cast(Vector((x,y,50)),Vector((0,0,-1)))
    return hit[0].z if hit[0] else 0.38
def original_ground(x,y):
    h=.3+15*math.exp(-((x+28)/19)**2-((y-32)/20)**2)+12*math.exp(-((x-36)/18)**2-((y-30)/22)**2)+6*math.exp(-((x-42)/12)**2-((y-6)/13)**2)+.22*math.sin(x*.17)*math.cos(y*.13)
    clearing=math.exp(-((x+2)/20)**6-((y-5)/17)**6);h=h*(1-clearing)+.38*clearing
    cut=math.exp(-(abs(y-(-9+.012*(x+3)**2))/4.6)**6)
    return h*(1-cut)+(.82+.0015*max(0,abs(x)-18)**2-.55)*cut
for p in terrain.data.polygons:p.material_index=0
for name in ['SM_Fences','SM_Shrubs']:
    for v in bpy.data.objects[name].data.vertices:
        x,y,z=v.co
        if -35<x<-14 and -5<y<12:v.co.z-=original_ground(x,y)-height(x,y)
lamp=bpy.data.objects['SM_Lamps'];base=min(v.co.z for v in lamp.data.vertices if v.co.x<-20);delta=height(-26,3)-base
for v in lamp.data.vertices:
    if v.co.x<-20:v.co.z+=delta
angle=math.atan(.024*34)
for v in bpy.data.objects['SM_TunnelHill'].data.vertices:v.co+=Vector((5*math.cos(angle),5*math.sin(angle),0))
old=bpy.data.objects['SM_Footpath'];mat=old.data.materials[0];bpy.data.objects.remove(old,do_unlink=True)
path=[(-45,-33),(-36,-21),(-31,-10),(-33,-3),(-33,5),(-30,10),(-23,13),(-16,16),(-7,17),(4,16),(14,19),(20,27),(17,34),(7,37),(-2,32),(-6,25),(-7,17)]
def spline(points):
    out=[];pp=[points[0]]+points+[points[-1]]
    for i in range(1,len(pp)-2):
        p0,p1,p2,p3=[Vector(v) for v in pp[i-1:i+3]]
        for j in range(15):
            t=j/15;v=.5*(2*p1+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t);out.append(v)
    out.append(Vector(points[-1]));return out
verts=[];faces=[]
for pts in [spline(path),[Vector((-33+i*.2,5)) for i in range(16)]]:
    start=len(verts)
    for i,p in enumerate(pts):
        d=pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)];n=Vector((-d.y,d.x)).normalized()*1.05
        for s in (-1,1):
            q=p+n*s;verts.append((q.x,q.y,height(q.x,q.y)+.06))
    for i in range(len(pts)-1):a=start+i*2;faces.append((a,a+2,a+3,a+1))
me=bpy.data.meshes.new('Contour-following footpath');me.from_pydata(verts,[],faces);me.materials.append(mat);o=bpy.data.objects.new('SM_Footpath',me);bpy.context.collection.objects.link(o);bpy.context.view_layer.objects.active=o;o.select_set(True)
mod=o.modifiers.new('Path surface depth','SOLIDIFY');mod.thickness=.025;bpy.ops.object.modifier_apply(modifier=mod.name)
for name in ['SM_Terrain','SM_Footpath','SM_Fences','SM_Lamps','SM_Shrubs','SM_TunnelHill']:
    o=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.export_scene.fbx(filepath=ROOT+'/SourceArt/'+name+'.fbx',use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,axis_forward='Y',axis_up='Z',mesh_smooth_type='FACE',use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False)
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/SourceArt/AlderPass.blend')
print('PRESENTATION_REFINED',flush=True)
