import bpy, math, random
from pathlib import Path
from mathutils import Vector
from math import sin, cos, pi
random.seed(29)
out = Path(__file__).parent
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
def material(name, rgb, noise=3):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*rgb,1)
    m.use_nodes=True
    nodes=m.node_tree.nodes
    links=m.node_tree.links
    bs=nodes.get('Principled BSDF')
    bs.inputs['Roughness'].default_value=.86
    n=nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value=noise
    n.inputs['Detail'].default_value=3
    tc=nodes.new('ShaderNodeTexCoord')
    links.new(tc.outputs['Object'],n.inputs[0])
    ramp=nodes.new('ShaderNodeValToRGB')
    for el,f in zip(ramp.color_ramp.elements,[.56,1.32]):
        el.color=(*(min(1,x*f) for x in rgb),1)
    links.new(n.outputs['Fac'],ramp.inputs[0])
    links.new(ramp.outputs[0],bs.inputs['Base Color'])
    bump=nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value=.16
    bump.inputs['Distance'].default_value=.055
    links.new(n.outputs['Fac'],bump.inputs['Height'])
    links.new(bump.outputs[0],bs.inputs['Normal'])
    return m
oak=material('Oiled oak',(.34,.155,.053))
dark=material('Weathered timber',(.165,.073,.033))
plaster=material('Limewash',(.88,.67,.39))
glass=material('Blue window glass',(.073,.22,.235))
slate=[material('Lichen slate %d'%i,(.12+.018*i,.157+.014*i,.055+.004*i)) for i in range(5)]
stone=[material('Sandstone %d'%i,(.34+.043*i,.277+.032*i,.19+.027*i)) for i in range(5)]
leaf=material('Garden leaves',(.114,.25,.044))
grass=material('Meadow',(.27,.345,.101),1.9)
flower=material('Ivory petals',(.98,.86,.54))
gold=material('Marigold',(.93,.43,.045))
clay=material('Terracotta',(.47,.18,.075))
iron=material('Forged iron',(.065,.055,.038))
lamp=material('Amber lantern',(.98,.58,.16))
lamp.node_tree.nodes.get('Principled BSDF').inputs['Emission Color'].default_value=(1,.48,.11,1)
lamp.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=1.3
def mesh(name,verts,faces,mat,edge=0):
    data=bpy.data.meshes.new(name)
    data.from_pydata(verts,[],faces)
    data.materials.append(mat)
    obj=bpy.data.objects.new(name,data)
    scene.collection.objects.link(obj)
    if edge:
        mod=obj.modifiers.new('Soft corners','BEVEL')
        mod.width=edge
        mod.segments=2
        mod=obj.modifiers.new('Face normals','WEIGHTED_NORMAL')
    return obj
def box(name,pos,size,mat,edge=.025):
    a,b,c=[v/2 for v in size]
    verts=[(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]
    ob=mesh(name,verts,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,edge)
    ob.location=pos
    return ob
def beam(name,a,b,w,d,mat):
    v=Vector(b)-Vector(a)
    ob=box(name,(Vector(a)+Vector(b))/2,(w,d,v.length),mat)
    ob.rotation_euler=v.to_track_quat('Z','Y').to_euler()
def ring(name,x,y,z,rx,ry,h,mat,n=9,top=1,jitter=0):
    outline=[(cos(2*pi*i/n)*rx*(1+random.uniform(-jitter,jitter)),sin(2*pi*i/n)*ry*(1+random.uniform(-jitter,jitter))) for i in range(n)]
    verts=[(x+a*f,y+b*f,z+dz) for f,dz in [(1,0),(top,h)] for a,b in outline]
    return mesh(name,verts,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat,.018)
def ell(name,p,s,m):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=p)
    o=bpy.context.object;o.name=name;o.scale=s;o.data.materials.append(m)
def garden(x,y,z,r):
    for i in range(12):
        dx=random.uniform(-r,r);dy=random.uniform(-r,r)
        h=random.uniform(.1,.22)
        ell('Leaf cluster',(x+dx,y+dy,z+h*.5),(.12,.10,h),leaf)
        if i%2==0:
            for j in range(5):
                a=j*2*pi/5
                ell('Petal',(x+dx+.045*cos(a),y+dy+.045*sin(a),z+h*1.6),(.053,.048,.033),flower)
            ell('Pollen',(x+dx,y+dy,z+h*1.6+.018),(.034,.034,.024),gold)
# Structural shell and masonry plinth
box('Limewashed walls',(0,0,1.51),(5.5,4.2,2.98),plaster,.075)
for side in [-1,1]:
    for row in range(2):
        for i in range(9):
            box('Foundation fieldstone',(-2.47+i*.617,side*2.105,.18+row*.29),(.60,.17,.30),random.choice(stone),.065)
        for i in range(7):
            box('Foundation return',(side*2.755,-1.83+i*.61,.18+row*.29),(.17,.60,.30),random.choice(stone),.065)
    for yy in [-2.08,2.08]:
        box('Corner post',(side*2.73,yy,1.8),(.15,.16,2.4),dark)
# Roof generator uses local ridge and slope coordinates, including raised courses of staggered shingles.
def roof(name,center,length,half,base,rise,cross=False):
    def point(u,v,z):
        x,y=center
        return (x-v,y+u,z) if cross else (x+u,y+v,z)
    def height(v):return base+rise*(1-abs(v)/half)
    for end in [-1,1]:
        u=end*length/2
        tri=[point(u,-half,base),point(u,half,base),point(u,0,base+rise)]
        mesh(name+' gable',tri,[(0,1,2)],plaster)
        for s in [-1,1]:
            beam(name+' bargeboard',point(u,s*half,base),point(u,0,base+rise),.145,.145,oak)
        beam(name+' tie',point(u,-half,base),point(u,half,base),.13,.14,dark)
    rows=max(3,round(half/.32))
    cols=max(3,round(length/.51))
    w=length/cols
    for s in [-1,1]:
        beam(name+' eaves',point(-length/2,s*half,base),point(length/2,s*half,base),.15,.17,dark)
        for row in range(rows):
            v0=half*(1-row/rows)
            v1=max(0,v0-half/rows-.048)
            offset=.5 if row%2 else 0
            for col in range(cols+1):
                a=max(-length/2,-length/2+(col-offset)*w)+.004
                b=min(length/2,-length/2+(col+1-offset)*w)-.004
                if b-a<.08:continue
                lip=random.uniform(0,.038)
                tip=v0+lip
                corners=[(a+.04,tip),(b-.05,tip+.008),(b,tip-.045),(b,v1),(a,v1),(a,tip-.04)]
                vv=[point(u,s*v,height(v)+z+(.04 if v>v1+.06 else 0)) for z in [.002,.084] for u,v in corners]
                faces=[tuple(range(5,-1,-1)),tuple(range(6,12))]+[(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)]
                if s<0:faces=[tuple(reversed(f)) for f in faces]
                mesh(name+' shingle',vv,faces,random.choice(slate),.018)
    for i in range(cols):
        a=point(-length/2+(i+.5)*w,0,base+rise+.10)
        box(name+' ridge cap',a,(.24,w-.008,.17) if cross else (w-.008,.24,.17),slate[4],.063)
roof('Main roof',(0,0),6.13,2.50,2.92,2.12)
roof('Porch',(-1.30,-2.33),2.32,1.07,2.39,.98,True)
roof('Dormer',(.87,-1.4),1.18,.69,3.73,.75,True)
box('Dormer face',(.87,-1.95,3.48),(1.26,.14,.56),plaster)
def window(x,y,z,width,height,side=False):
    def piece(name,u,d,v,w,t,h,m):
        return box(name,(x-d,y+u,z+v) if side else (x+u,y+d,z+v),(t,w,h) if side else (w,t,h),m,.016)
    piece('Glazing',0,0,0,width,.075,height,glass)
    for v in [-height/2,0,height/2]:
        piece('Window rail',0,-.063,v,width+.14,.105,.062,oak)
    for u in [-width/2,0,width/2]:
        piece('Window stile',u,-.072,0,.072,.105,height+.10,oak)
    piece('Stone sill',0,-.09,-height/2-.07,width+.26,.27,.11,stone[3])
window(.87,-2.045,3.59,.72,.56)
window(.97,-2.15,1.69,1.2,1.04)
window(2.79,.22,1.72,1.13,1.0,True)
for x in [.08,1.86]:
    for k in [-1,0,1]: box('Shutter board',(x+k*.13,-2.18,1.68),(.126,.1,1.12),oak)
    for z in [1.3,2.06]:box('Shutter cleat',(x,-2.245,z),(.42,.08,.09),dark)
box('Flower box',(.99,-2.39,1.03),(1.24,.38,.25),dark)
for x in [.59,1.04,1.43]:garden(x,-2.41,1.16,.16)
for x in [-2.18,-.43]:
    box('Porch pillar',(x,-3.32,1.44),(.19,.21,2.03),oak)
    box('Pillar footing',(x,-3.32,.50),(.31,.32,.29),stone[3],.045)
    beam('Pillar knee',(x,-3.32,1.99),(x+(.32 if x<-1 else -.32),-3.32,2.37),.13,.14,oak)
for i in range(6):box('Door plank',(-1.79+i*.19,-2.146,1.35),(.184,.10,1.98),oak)
for x in [-1.94,-.74]:box('Door jamb',(x,-2.19,1.37),(.14,.18,2.10),dark)
box('Door lintel',(-1.34,-2.19,2.39),(1.35,.18,.17),dark)
for z in [.78,1.91]:box('Strap hinge',(-1.69,-2.22,z),(.39,.06,.066),iron)
ell('Door latch',(-.92,-2.26,1.40),(.06,.07,.06),iron)
for i in range(3):box('Porch step',(-1.3,-2.8-i*.37,.23-i*.065),(2.02-i*.10,1.45,.45-i*.13),stone[3],.062)
beam('Lantern stem',(-2.13,-3.31,2.28),(-2.13,-3.31,1.97),.036,.036,iron)
ring('Lantern cap',-2.13,-3.31,1.92,.17,.17,.12,iron,4,.3)
ring('Lantern glass',-2.13,-3.31,1.64,.10,.10,.28,lamp,4,1.5)
ring('Lantern base',-2.13,-3.31,1.61,.12,.12,.055,iron,4)
# Chimney stones and open terracotta flue.
cx,cy=2.04,.39
box('Chimney mortar',(cx,cy,4.8),(.70,.70,2.10),stone[0])
for j in range(8):
    for s in [-1,1]:
        for k in [-1,1]:
            box('Chimney ashlar',(cx+k*.199,cy+s*.314,3.95+j*.255),(.388,.18,.247),random.choice(stone),.038)
        box('Chimney side',(cx+s*.315,cy,3.95+j*.255),(.17,.47,.247),random.choice(stone),.035)
for s in [-1,1]:
    box('Flue rim',(cx,cy+s*.31,5.97),(.79,.17,.21),clay,.033)
    box('Flue rim',(cx+s*.31,cy,5.97),(.17,.47,.21),clay,.033)
box('Flue interior',(cx,cy,5.85),(.52,.52,.03),iron)
ring('Meadow bank',0,-.53,-.13,4.67,4.66,.19,grass,24,.99,.04)
for i in range(3):
    ring('Walk stone',-1.31+.09*sin(i),-4.13-i*.40,.067,.35,.19,.083,stone[i],8,.94,.11)
for x,y in [(-2.62,-2.74),(2.61,-2.42),(3.04,1.27),(-2.95,.4)]:
    garden(x,y,.09,.25)
ring('Clay pot',-2.52,-2.87,.08,.24,.24,.43,clay,12,1.28)
garden(-2.52,-2.87,.49,.22)
# Neutral studio staging and game-angle preview.
box('Studio floor',(0,0,-.24),(200,200,.18),material('Warm paper',(.74,.69,.57)),0)
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
target=Vector((0,-.44,2.0))
e=math.radians(60);a=math.radians(25)
bpy.ops.object.camera_add(location=target+18*Vector((cos(e)*sin(a),-cos(e)*cos(a),sin(e))))
cam=bpy.context.object;cam.name='Preview | 60 degree pitch';aim(cam,target);cam.data.type='ORTHO';cam.data.ortho_scale=12.1;scene.camera=cam
def light(pos,power,size,color):
    bpy.ops.object.light_add(type='AREA',location=pos)
    o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=color;aim(o,(0,0,2))
light((-5,-6,11),1600,6,(1,.87,.69))
light((6,-2,8),950,7,(.84,.90,1))
light((1,5,9),1250,5,(1,.93,.72))
world=bpy.data.worlds.new('Soft daylight');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.70,.76,.84,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.42
scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
scene.render.resolution_x=1100;scene.render.resolution_y=960;scene.render.resolution_percentage=100
scene.render.filepath='//Preview.png'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.color_type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'MossCottage.blend'))
bpy.ops.render.render(write_still=True)
