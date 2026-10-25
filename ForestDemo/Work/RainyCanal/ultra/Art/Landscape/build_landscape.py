import bpy,math,random,json,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
ROOT=P.parents[1]
sys.path.insert(0,str(ROOT))
from design import BUILDINGS,building_clear
random.seed(20261022)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
SLOTS=['Ground','Stone','CanalWater','PuddleWater','Rain','Leaf','Timber']
MATS={s:bpy.data.materials.new(s) for s in SLOTS}
for s,m in MATS.items():m.diffuse_color=(*({'Ground':(.22,.3,.21),'Stone':(.42,.45,.43),'CanalWater':(.12,.25,.29),'PuddleWater':(.2,.28,.3),'Rain':(.5,.65,.75),'Leaf':(.2,.32,.2),'Timber':(.25,.18,.12)}[s]),1)

def uv(o):
    me=o.data;me.calc_loop_triangles()
    tri=bpy.data.meshes.new(o.name+'_tri');verts=[v.co[:] for v in me.vertices]
    faces=[tuple(t.vertices) for t in me.loop_triangles];mi=[me.polygons[t.polygon_index].material_index for t in me.loop_triangles]
    tri.from_pydata(verts,[],faces);tri.update()
    for m in me.materials:tri.materials.append(m)
    for p,i in zip(tri.polygons,mi):p.material_index=i
    old=me;o.data=tri
    if old.users==0:bpy.data.meshes.remove(old)
    u0=tri.uv_layers.new(name='Unique');u1=tri.uv_layers.new(name='Physical128')
    n=math.ceil(math.sqrt(len(faces)));cell=1/n;pad=min(2.1/1024,cell*.12)
    for i,p in enumerate(tri.polygons):
        ids=list(p.vertices);a,b,c=[tri.vertices[v].co for v in ids]
        axis=(b-a).normalized();normal=(b-a).cross(c-a).normalized();second=normal.cross(axis)
        x=(i%n)*cell+pad;y=(i//n)*cell+pad;usable=cell-2*pad
        for j,li in enumerate(p.loop_indices):
            u0.data[li].uv=[(x,y),(x+usable,y),(x,y+usable)][j]
            d=tri.vertices[ids[j]].co-a
            u1.data[li].uv=(d.dot(axis)/8,d.dot(second)/8)
    return o

def mesh(name,verts,faces,slot):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);me.materials.append(MATS[slot]);return o
def box(name,loc,scale,slot,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(MATS[slot])
    if bevel:
        mod=o.modifiers.new('SoftEdges','BEVEL');mod.width=bevel;mod.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
    return o
def join(name,objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
    bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');return o

objects=[]
for side in (-1,1):
    x0,x1=((-50,-6) if side<0 else (6,50))
    objects.append(mesh('SM_Bank'+('West' if side<0 else 'East'),[(x0,-50,0),(x1,-50,0),(x1,50,0),(x0,50,0)],[(0,1,2,3)],'Ground'))
objects.append(mesh('SM_CanalWater',[(-6,-50,0),(6,-50,0),(6,50,0),(-6,50,0)],[(0,1,2,3)],'CanalWater'))
objects.append(box('SM_CanalBed',(0,0,-1.8),(12,100,.3),'Stone'))
objects.append(box('SM_QuayWall',(0,0,-.95),(.65,100,2.1),'Stone',.08))
objects.append(box('SM_QuayCap',(0,0,.1),(.8,2,.2),'Stone',.05))
objects.append(box('SM_Dock',(0,0,-.14),(4,4,.28),'Timber',.05))
objects.append(box('SM_DockStep',(0,0,-.15),(1.2,4,.3),'Stone',.04))
v=[(0,0,0)];N=48
for i in range(N):
    t=i*math.tau/N;r=1+.065*math.sin(t*5)+.035*math.cos(t*9);v.append((r*math.cos(t),r*math.sin(t),0))
objects.append(mesh('SM_Puddle',v,[(0,i+1,(i+1)%N+1) for i in range(N)],'PuddleWater'))
# Crossed translucent streaks. Every drop retains one phase in the vertex color.
verts=[];faces=[];colors=[]
for i in range(2200):
    x=random.uniform(-49,49);y=random.uniform(-49,49)
    if not building_clear(x,y,1):continue
    z=.17 if abs(x)>6 else -.7
    phase=random.random();length=random.uniform(.23,.46);w=random.uniform(.007,.012)
    for axis in (0,1):
        k=len(verts)
        for q,(h,dz) in enumerate([(-w,0),(w,0),(w,length),(-w,length)]):
            verts.append((x+(h if axis==0 else 0),y+(h if axis==1 else 0),z+dz));colors.append((phase,q/3,0,1))
        faces.append((k,k+1,k+2,k+3))
rain=mesh('SM_RainVolume',verts,faces,'Rain');uv(rain)
col=rain.data.color_attributes.new(name='Col',type='FLOAT_COLOR',domain='POINT')
for item,value in zip(col.data,colors):item.color=value
objects.append(rain)
# Rounded tree with distinct irregular crown lobes, original source.
parts=[box('Trunk',(0,0,1.2),(.36,.4,2.4),'Timber',.09)]
for i,(x,y,z,r) in enumerate([(0,0,3.4,1.65),(-.95,.15,3.2,1.2),(.8,.35,3.7,1.3),(.2,-.95,3.4,1.2),(0,.5,4.1,1.1)]):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=r,location=(x,y,z));o=bpy.context.object;o.scale=(1,.9,1.03);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(MATS['Leaf']);parts.append(o)
objects.append(join('SM_CanalTree',parts))
parts=[]
for x,y,z,r in [(-.35,0,.38,.5),(.3,.1,.45,.6),(0,-.25,.3,.4)]:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=r,location=(x,y,z));o=bpy.context.object;o.scale=(1,.9,.8);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(MATS['Leaf']);parts.append(o)
objects.append(join('SM_Shrub',parts))
parts=[]
for i in range(11):
    t=random.uniform(0,math.tau);r=random.uniform(0,.18);x,y=math.cos(t)*r,math.sin(t)*r;h=random.uniform(.2,.5);w=.025
    parts.append(mesh('Blade',[(x-w,y,0),(x+w,y,0),(x+math.cos(t)*.13,y+math.sin(t)*.13,h)],[(0,1,2)],'Leaf'))
objects.append(join('SM_GrassFringe',parts))
manifest=[]
out=P/'FBX';out.mkdir(exist_ok=True)
for o in objects:
    if o!=rain:uv(o)
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    path=out/(o.name+'.fbx')
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},apply_unit_scale=True,axis_forward='-Y',axis_up='Z',mesh_smooth_type='FACE',use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False)
    me=o.data
    manifest.append({'name':o.name,'fbx':str(path),'triangles':len(me.polygons),'vertices':len(me.vertices),'materials':[m.name for m in me.materials],'uv_channels':len(me.uv_layers),'bounds_m':[[min(v.co[j] for v in me.vertices) for j in range(3)],[max(v.co[j] for v in me.vertices) for j in range(3)]],'location_m':list(o.location),'uv1_target_px_per_m':128,'uv0_padding_px':min(2.1,1024/math.ceil(math.sqrt(len(me.polygons)))*.12)})
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source.blend'))
(P/'manifest.json').write_text(json.dumps({'original':True,'seed':20261022,'meshes':manifest,'rain_drops':len(colors)//8,'rain_height_m':14,'UV1':'Per-triangle physical isometric density128px/m; intentionally repeating; world spatial coherence comes from material where needed.'},indent=2))
print('LANDSCAPE_EXPORTED',len(objects))
