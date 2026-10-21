import bpy,bmesh,math,json,hashlib,struct,time,datetime
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement');OUT=R/'SourceArt';OUT.mkdir(exist_ok=True)
clock=time.monotonic();started=datetime.datetime.now(datetime.timezone.utc).isoformat()
bpy.ops.wm.open_mainfile(filepath=str(R.parent/'TexturePass/SourceArt/AlderPass_Textured.blend'))
manifest=json.loads((R.parent/'TexturePass/art_manifest.json').read_text())
def geomhash(o):
    h=hashlib.sha256()
    for v in o.data.vertices:h.update(struct.pack('<3d',*v.co))
    for p in o.data.polygons:h.update(struct.pack('<I',len(p.vertices)));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices));h.update(struct.pack('<I',p.material_index))
    return h.hexdigest()
before={o.name:geomhash(o) for o in bpy.data.objects if o.type=='MESH'}
mats={n:bpy.data.materials[n] for n in manifest['palette']}
terrain=bpy.data.objects['SM_Terrain'];tree=BVHTree.FromObject(terrain,bpy.context.evaluated_depsgraph_get())
def ground(x,y):
    hit=tree.ray_cast(Vector((x,y,80)),Vector((0,0,-1)))[0];assert hit is not None
    return hit.z
def ty(x):return -9+.012*(x+3)**2
def tz(x):return .82+.0015*max(0,abs(x)-18)**2
def newmesh(name,verts,faces,materials,slots=None):
    old=bpy.data.objects.get(name)
    if old:bpy.data.objects.remove(old,do_unlink=True)
    me=bpy.data.meshes.new(name+'_Improved');me.from_pydata(verts,[],faces);me.update()
    for m in materials:me.materials.append(mats[m])
    if slots:
        for p,s in zip(me.polygons,slots):p.material_index=s
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);return o
# Trapezoidal ballast bed: sleeper top is tz+.08; ballast is tz-.06.
xs=[-50+i*.25 for i in range(401)];verts=[];faces=[]
for x in xs:
    angle=math.atan(.024*(x+3));n=Vector((-math.sin(angle),math.cos(angle),0));c=Vector((x,ty(x),tz(x)))
    for lateral,z in [(-1.52,-.06),(1.52,-.06),(1.95,-.32),(-1.95,-.32)]:verts.append(tuple(c+n*lateral+Vector((0,0,z))))
for i in range(len(xs)-1):
    a=i*4;b=a+4
    for j in range(4):faces.append((a+j,b+j,b+(j+1)%4,a+(j+1)%4))
faces.extend([(3,2,1,0),(1600,1601,1602,1603)])
newmesh('SM_Ballast',verts,faces,['Ballast'])
# Continuous foot, web and head profile; original centerline and 1.52m gauge.
profile=[(-.085,.08),(.085,.08),(.085,.12),(.027,.12),(.027,.255),(.055,.265),(.055,.32),(-.055,.32),(-.055,.265),(-.027,.255),(-.027,.12),(-.085,.12)]
verts=[];faces=[];slots=[]
for sign in [-1,1]:
    start=len(verts)
    for x in xs:
        angle=math.atan(.024*(x+3));n=Vector((-math.sin(angle),math.cos(angle),0));c=Vector((x,ty(x),tz(x)))+n*(sign*.76)
        for lateral,z in profile:verts.append(tuple(c+n*lateral+Vector((0,0,z))))
    for i in range(len(xs)-1):
        for j in range(len(profile)):
            a=start+i*12+j;b=start+(i+1)*12+j;faces.append((a,b,start+(i+1)*12+(j+1)%12,start+i*12+(j+1)%12));slots.append(0 if j in [4,5,6,7,8] else 1)
    faces.append(tuple(start+j for j in reversed(range(12))));slots.append(1)
    faces.append(tuple(start+400*12+j for j in range(12)));slots.append(1)
newmesh('SM_Rails',verts,[tuple(reversed(f)) for f in faces],['Rail','Metal'],slots)
# Crossing alignment follows the existing curve.
cx=-33.;cy=ty(cx);angle=math.atan(.024*(cx+3));F=Vector((math.cos(angle),math.sin(angle)));N=Vector((-math.sin(angle),math.cos(angle)));C=Vector((cx,cy))
def pt(a,b):return C+F*a+N*b
path=[(-45,-33),(-36,-21),(-31,-10),tuple(pt(0,-6)),tuple(pt(0,-3)),tuple(pt(0,3)),tuple(pt(0,5)),(-30,10),(-23,13),(-16,16),(-7,17),(4,16),(14,19),(20,27),(17,34),(7,37),(-2,32),(-6,25),(-7,17)]
def spline(points):
    out=[];pp=[points[0]]+points+[points[-1]]
    for i in range(1,len(pp)-2):
        p0,p1,p2,p3=[Vector(v) for v in pp[i-1:i+3]]
        for j in range(25):
            t=j/25;out.append(.5*(2*p1+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
    out.append(Vector(points[-1]));return out
lines=[spline(path),[Vector((-30,5)),pt(0,5)]];segments=[];buckets={}
for line in lines:
    for a,b in zip(line,line[1:]):
        idx=len(segments);segments.append((a,b))
        for i in range(math.floor(min(a.x,b.x)-1.7),math.ceil(max(a.x,b.x)+1.7)+1):
            for j in range(math.floor(min(a.y,b.y)-1.7),math.ceil(max(a.y,b.y)+1.7)+1):buckets.setdefault((i,j),[]).append(idx)
def distance(x,y):
    p=Vector((x,y));best=1e9
    for idx in buckets.get((math.floor(x),math.floor(y)),[]):
        a,b=segments[idx];ab=b-a;t=max(0,min(1,(p-a).dot(ab)/max(ab.length_squared,1e-12)));best=min(best,(p-a-ab*t).length)
    return best
def smooth(t):return t*t*(3-2*t)
def pathheight(x,y):
    base=ground(x,y)+.045;delta=Vector((x,y))-C;a=delta.dot(F);b=delta.dot(N)
    w=smooth(max(0,min(1,(6.2-abs(b))/4.0)))*smooth(max(0,min(1,(5.0-abs(a))/2.0)))
    top=tz(x)+.17
    z=max(base,base+(top-base)*w)
    # Flush connection to the original 1:12 platform-ramp toe.
    d=math.hypot(x+30,y-5);pin=1-smooth(min(1,d/1.1))
    return max(base,z*(1-pin)+.425*pin)
step=.20;cache={};lookup={};verts=[];factors=[];faces=[]
def sample(i,j):
    if (i,j) not in cache:cache[i,j]=distance(i*step,j*step)
    return cache[i,j]
def vid(i,j):
    if (i,j) not in lookup:
        x,y=i*step,j*step;d=sample(i,j);lookup[i,j]=len(verts);verts.append([x,y,pathheight(x,y)]);factors.append(1-smooth(max(0,min(1,(d-.88)/.40))))
    return lookup[i,j]
for i in range(-231,113):
    for j in range(-171,193):
        corners=[(i,j),(i+1,j),(i+1,j+1),(i,j+1)]
        if min(sample(*p) for p in corners)>1.28:continue
        a,b,c,d=[vid(*p) for p in corners];faces.extend([(a,b,c),(a,c,d)])
# Enforce clearance at centroids and edge midpoints, including terrain crease crossings.
for iteration in range(4):
    lifts={};bad=0
    for face in faces:
        p=[Vector(verts[k]) for k in face]
        for weights in [(1/3,1/3,1/3),(.5,.5,0),(0,.5,.5),(.5,0,.5)]:
            q=sum((v*w for v,w in zip(p,weights)),Vector());need=ground(q.x,q.y)+.035-q.z
            if need>1e-5:
                bad+=1
                for k in face:lifts[k]=max(lifts.get(k,0),need+.002)
    for k,v in lifts.items():verts[k][2]+=v
    if bad==0:break
foot=newmesh('SM_Footpath',verts,faces,['Gravel'])
colors=foot.data.color_attributes.new(name='PathBlend',type='FLOAT_COLOR',domain='CORNER')
for li,loop in enumerate(foot.data.loops):
    f=factors[loop.vertex_index];colors.data[li].color=(f,f,f,1)
foot.data.color_attributes.active_color=colors
# Timber crossing boards, split at both rails to leave physical flange grooves.
boards=[]
for lo,hi in [(-2.25,-.90),(-.62,.62),(.90,2.25)]:
    count=math.ceil((hi-lo)/.19);width=(hi-lo)/count
    for i in range(count):
        q=pt(0,lo+(i+.5)*width);z=tz(q.x)+.30
        bpy.ops.mesh.primitive_cube_add(size=1,location=(q.x,q.y,z-.06));o=bpy.context.object;o.dimensions=(2.7,width-.012,.12);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.rotation_euler[2]=angle;o.data.materials.append(mats['WoodLight'])
        mod=o.modifiers.new('Soft timber edges','BEVEL');mod.width=.018;mod.segments=2;bpy.ops.object.modifier_apply(modifier=mod.name);boards.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in boards:o.select_set(True)
bpy.context.view_layer.objects.active=boards[0];bpy.ops.object.join();o=bpy.context.object;o.name='SM_PedestrianCrossing';bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
changed=['SM_Footpath','SM_Ballast','SM_Rails','SM_PedestrianCrossing'];after={o.name:geomhash(o) for o in bpy.data.objects if o.type=='MESH'}
assert all(after[k]==v for k,v in before.items() if k not in changed)
known={x['name']:x for x in manifest['meshes']}
for o in bpy.data.objects:
    if o.type!='MESH':continue
    row=known.get(o.name,{'name':o.name});row.update(file=str(OUT/(o.name+'.fbx')),vertices=len(o.data.vertices),polygons=len(o.data.polygons),materials=[m.name for m in o.data.materials])
    if o.name not in known:manifest['meshes'].append(row)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'AlderPass_Geometry.blend'))
(R/'art_manifest.json').write_text(json.dumps(manifest,indent=2))
evidence={'started_at_utc':started,'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-clock,'changed_meshes':changed,'before_geometry_sha256':before,'after_geometry_sha256':after,'unchanged_meshes_verified':len(before)-3,'path_grid_spacing_m':step,'path_top_triangles':len(faces),'path_clearance_iterations':iteration+1,'last_iteration_adjusted_probes':bad,'crossing_center_m':[cx,cy],'crossing_forward':list(F),'crossing_right':list(N),'routes':[[list(p) for p in line] for line in lines],'ballast_design_top_relative_to_track_m':-.06,'sleeper_top_relative_to_track_m':.08,'rail_head_relative_to_track_m':.32}
(R/'geometry_changes.json').write_text(json.dumps(evidence,indent=2));print('SELF_GEOMETRY_COMPLETE',len(faces),time.monotonic()-clock,flush=True)
