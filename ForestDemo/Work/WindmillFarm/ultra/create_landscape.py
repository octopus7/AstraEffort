import bpy,math,random,json,sys,time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from landscape_design import height
OUT=ROOT/'Art/Landscape'
OUT.mkdir(parents=True,exist_ok=True)
random.seed(2241)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
MATS={}
for n,col in {'Ground':(.32,.40,.22,1),'Soil':(.25,.19,.12,1),'Wood':(.24,.18,.12,1),'Leaf':(.27,.38,.19,1),'Hay':(.62,.54,.28,1),'Stone':(.44,.46,.41,1)}.items():
    m=bpy.data.materials.new(n);m.diffuse_color=col;MATS[n]=m
items=[];manifest=[]
def remember(o,mat):
    o.data.materials.append(MATS[mat]);items.append(o);return o
def sphere(name,loc,scale,mat,sub=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in o.data.polygons:p.use_smooth=True
    return remember(o,mat)
def segment(name,a,b,r1,r2,mat,verts=10):
    a,b=Vector(a),Vector(b);v=b-a
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r1,radius2=r2,depth=v.length,location=(a+b)*.5)
    o=bpy.context.object;o.name=name;o.rotation_euler=v.to_track_quat('Z','Y').to_euler()
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in o.data.polygons:p.use_smooth=True
    return remember(o,mat)
def mesh(name,verts,faces,mat):
    d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o)
    return remember(o,mat)
def export(name,uv=True):
    global items
    bpy.ops.object.select_all(action='DESELECT')
    for o in items:o.select_set(True)
    bpy.context.view_layer.objects.active=items[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
    bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    if uv:
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008);bpy.ops.object.mode_set(mode='OBJECT')
    o.data.calc_loop_triangles()
    uvdata=o.data.uv_layers.active.data
    stats=[]
    for t in o.data.loop_triangles:
        a,b,c=(o.data.vertices[i].co for i in t.vertices);wa=(b-a).cross(c-a).length*.5
        ua,ub,uc=(uvdata[i].uv for i in t.loops);area=abs((ub.x-ua.x)*(uc.y-ua.y)-(uc.x-ua.x)*(ub.y-ua.y))*.5
        if wa>1e-10:stats.append(1024*math.sqrt(area/wa))
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',bake_space_transform=False,add_leaf_bones=False,use_mesh_modifiers=True)
    bounds=[[min(v.co[k] for v in o.data.vertices),max(v.co[k] for v in o.data.vertices)] for k in range(3)]
    manifest.append({'name':name,'file':name+'.fbx','bounds_m':bounds,'triangles':len(o.data.loop_triangles),'materials':[m.name for m in o.data.materials],'uv_density_px_m_at1024':{'min':min(stats),'median':sorted(stats)[len(stats)//2],'max':max(stats)},'uv_outside01':sum(not(0<=v.uv.x<=1 and 0<=v.uv.y<=1) for v in uvdata),'uv_method':'smart project, 0.008 margin' if uv else 'unique planar ground; macro color2048 plus tiled detail'});items=[]
    o.hide_set(True)
    return o

# Single ground grid, with open boundaries that are closed by an earth skirt.
verts=[];faces=[];N=100
for j in range(N+1):
    for i in range(N+1):
        x,y=i-50,j-50;verts.append((x,y,height(x,y)))
for j in range(N):
    for i in range(N):
        a=j*(N+1)+i;faces.append((a,a+1,a+N+2,a+N+1))
o=mesh('ground',verts,faces,'Ground');layer=o.data.uv_layers.new(name='UVMap')
for p in o.data.polygons:
    p.use_smooth=True
    for li in p.loop_indices:
        v=o.data.vertices[o.data.loops[li].vertex_index].co;layer.data[li].uv=((v.x+50)/100,(v.y+50)/100)
export('SM_Ground',False)
# Thin visible soil edge stops light leaks and gives the plot a grounded base.
v=[];f=[]
perimeter=[(x,-50) for x in range(-50,51)]+[(50,y) for y in range(-49,51)]+[(x,50) for x in range(49,-51,-1)]+[(-50,y) for y in range(49,-50,-1)]
for x,y in perimeter:v.extend([(x,y,height(x,y)),(x,y,-1.2)])
for k in range(len(perimeter)):
    a=k*2;b=((k+1)%len(perimeter))*2;f.append((a,b,b+1,a+1))
mesh('soil edge',v,f,'Soil');export('SM_EarthEdge')

for variant in range(3):
    rnd=random.Random(930+variant)
    h=4.8+variant*.5
    segment('trunk',(0,0,0),(.13,-.12,h*.73),.28,.13,'Wood',12)
    for k in range(7):
        t=k*2.4;end=(math.cos(t)*(1.15+rnd.random()*.7),math.sin(t)*(1.1+rnd.random()*.7),h*.65+rnd.random()*1.2)
        segment('branch',(.08,0,h*.42),end,.12,.035,'Wood',8)
        sphere('crown',end,(1.45+rnd.random()*.4,1.3+rnd.random()*.4,1.20+rnd.random()*.35),'Leaf',2)
    sphere('crown centre',(0,0,h),(1.6,1.7,1.35),'Leaf',2)
    export('SM_OrchardTree'+str(variant+1))

# Solid curved grass blades rather than alpha cards; no texture-cutout fringe.
for k in range(23):
    a=random.random()*math.tau;r=math.sqrt(random.random())*.5;x,y=math.cos(a)*r,math.sin(a)*r
    h=random.uniform(.18,.48);w=random.uniform(.025,.055);lean=random.uniform(.08,.22)
    d=Vector((math.cos(a),math.sin(a),0));p=Vector((-d.y,d.x,0));c=Vector((x,y,0))
    verts=[c-p*w,c+p*w,c+d*lean*.4+p*w*.55+Vector((0,0,h*.55)),c+d*lean*.4-p*w*.55+Vector((0,0,h*.55)),c+d*lean+Vector((0,0,h))]
    mesh('grass',verts,[(0,1,2,3),(3,2,4)],'Leaf')
export('SM_GrassTuft')
for k in range(12):
    x,y=random.uniform(-.43,.43),random.uniform(-.43,.43);h=random.uniform(.75,1.1)
    segment('stalk',(x,y,0),(x+.06,y+.02,h),.012,.008,'Hay',5)
    for j in range(5):
        z=h-.18+j*.055
        for side in (-1,1):
            sphere('grain',(x+.06+side*.035,y,z),(.045,.025,.065),'Hay',1)
    for j in range(2):
        a=(x,y,.25+j*.18);b=(x+(-1)**j*.18,y+.1,.5+j*.18)
        segment('leaf',a,b,.018,.001,'Hay',5)
export('SM_WheatPatch')
for k in range(6):
    a=k*math.tau/6
    sphere('rock',(math.cos(a)*.22,math.sin(a)*.18,.22),(.4+random.random()*.15,.33,.28),'Stone',1)
export('SM_FieldRock')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'landscape_source.blend'))
(OUT/'manifest.json').write_text(json.dumps({'units':'metres','fbx_axis_forward':'-Y','fbx_axis_up':'Z','assets':manifest,'source':'Original procedural geometry for WindmillFarm only','uv_exceptions':['Dense vegetation has many tiny packed islands: density measured, no claim of uniform128px/m.','Ground uses unique 100m planar macro atlas plus repeated material detail.']},indent=2))
print('LANDSCAPE_COMPLETE',len(manifest))
