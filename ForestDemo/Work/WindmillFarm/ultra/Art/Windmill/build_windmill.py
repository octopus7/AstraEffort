"""Independently authored WindmillFarm hero asset. Blender 4.5 background only.
All dimensional coordinates are metres. No external source assets are loaded.
"""
import bpy, math, os, json, random, statistics, datetime, time
from mathutils import Vector, Matrix
from math import sin, cos, pi

ROOT=os.path.dirname(os.path.abspath(__file__))
START=datetime.datetime.now(datetime.timezone.utc)
random.seed(21777)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1.0
scene.render.threads_mode='FIXED'
scene.render.threads=4
MATS={}
COLORS={'Wood':(.205,.115,.064,1),'WoodLight':(.39,.265,.145,1),
       'Stone':(.42,.43,.365,1),'Plaster':(.74,.665,.46,1),
       'Roof':(.29,.145,.092,1),'Iron':(.105,.118,.105,1),
       'Canvas':(.85,.81,.665,1),'Glass':(.20,.31,.32,1)}
for n,c in COLORS.items():
    m=bpy.data.materials.new(n); m.diffuse_color=c; m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=c
    bs.inputs['Roughness'].default_value=.76 if n!='Glass' else .24
    if n=='Iron': bs.inputs['Metallic'].default_value=.65
    MATS[n]=m
PARTS={'tower':[],'rotor':[],'steps':[]}
DETAIL={}

def register(o,name,mat,group='tower',bevel=0,smooth=False):
    o.name=name
    o.data.materials.clear(); o.data.materials.append(MATS[mat])
    if bevel:
        mod=o.modifiers.new('Soft worn edges','BEVEL'); mod.width=bevel; mod.segments=2
        mod.harden_normals=True
        norm=o.modifiers.new('Weighted face normals','WEIGHTED_NORMAL'); norm.keep_sharp=True; norm.weight=35
    if smooth:
        for p in o.data.polygons: p.use_smooth=True
    PARTS[group].append(o)
    return o

def box(name,loc,scale,mat='Wood',group='tower',bevel=.025,rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o=bpy.context.object; o.scale=scale
    if rot: o.rotation_euler=rot
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return register(o,name,mat,group,bevel)

def mesh(name,verts,faces,mat='Wood',group='tower',bevel=.02,smooth=False):
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); scene.collection.objects.link(o)
    return register(o,name,mat,group,bevel,smooth)

def cyl(name,loc,r,depth,mat='Wood',group='tower',verts=32,bevel=.02,rot=None,r2=None):
    if r2 is None: bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc)
    else: bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=r2,depth=depth,location=loc)
    o=bpy.context.object
    if rot: o.rotation_euler=rot
    return register(o,name,mat,group,bevel,True)

def beam(name,a,b,w=.13,d=None,mat='Wood',group='tower',bevel=.02):
    a,b=Vector(a),Vector(b); delta=b-a
    o=box(name,(a+b)/2,(w,d or w,delta.length),mat,group,bevel)
    o.rotation_euler=delta.to_track_quat('Z','Y').to_euler()
    return o

def ring(name,z,r,thick,depth,mat='Wood',group='tower',n=64):
    vs=[]
    for zz in (z-depth/2,z+depth/2):
        for rr in (r-thick/2,r+thick/2):
            vs.extend([(rr*cos(2*pi*j/n),rr*sin(2*pi*j/n),zz) for j in range(n)])
    fs=[]
    for j in range(n):
        k=(j+1)%n
        fs.extend([(j,k,n+k,n+j),(2*n+j,3*n+j,3*n+k,2*n+k),
                   (j,2*n+j,2*n+k,k),(n+j,n+k,3*n+k,3*n+j)])
    return mesh(name,vs,fs,mat,group,.018,True)

def arch(name,width,bottom,spring,depth,loc,mat='Wood',group='tower',bevel=.02,angle=0):
    # Filled arch extrusion in local X/Z, front face points towards -Y.
    rad=width/2; poly=[(-rad,bottom),(rad,bottom),(rad,spring)]
    for i in range(1,17):
        a=i*pi/16; poly.append((rad*cos(a),spring+rad*sin(a)))
    vs=[]
    for y in (-depth/2,depth/2):
        vs.extend([(x,y,z) for x,z in poly])
    # The polygon is CCW in X/Z, whose outward front normal is -Y.
    n=len(poly); fs=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    fs += [(i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n)]
    o=mesh(name,vs,fs,mat,group,bevel)
    o.location=loc; o.rotation_euler.z=angle
    return o

def cut(obj,cutter):
    bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new('Architectural recess','BOOLEAN'); mod.operation='DIFFERENCE'; mod.solver='EXACT'; mod.object=cutter
    # Cut the un-bevelled architectural body; round its finished cuts once later.
    while obj.modifiers.find(mod.name)>0:
        bpy.ops.object.modifier_move_up(modifier=mod.name)
    bpy.ops.object.modifier_apply(modifier=mod.name)

def discard(o):
    for parts in PARTS.values():
        if o in parts: parts.remove(o)
    bpy.data.objects.remove(o,do_unlink=True)

def wedge(name,a0,a1,rin,rout,z0,z1,mat='Stone',group='tower',segments=4,bevel=.025):
    vs=[]
    for z in (z0,z1):
        for r in (rin,rout):
            vs.extend([(r*cos(a0+(a1-a0)*i/segments),r*sin(a0+(a1-a0)*i/segments),z) for i in range(segments+1)])
    n=segments+1; fs=[]
    for i in range(segments):
        fs += [(i,i+1,n+i+1,n+i),(2*n+i,3*n+i,3*n+i+1,2*n+i+1),
               (i,2*n+i,2*n+i+1,i+1),(n+i,n+i+1,3*n+i+1,3*n+i)]
    fs += [(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)]
    return mesh(name,vs,fs,mat,group,bevel)

# Main tower: gently tapered plaster, stone plinth and real shallow entry recess.
core=cyl('Stone mortar core',(0,0,.75),3.28,1.50,'Stone',verts=64,bevel=.04)
shaft=cyl('Tapered plaster shell',(0,0,5.52),3.15,8.14,'Plaster',verts=64,bevel=.06,r2=2.22)
door_cut=arch('Entry cutter',1.88,-.15,2.12,2.0,(0,-3.0,0),'Iron',bevel=0)
cut(core,door_cut); cut(shaft,door_cut)
for course in range(4):
    n=26; h=.365; z0=.02+course*.375
    for j in range(n):
        a0=2*pi*(j+(course%2)*.5)/n+.007
        a1=2*pi*(j+1+(course%2)*.5)/n-.007
        mid=(a0+a1)/2
        # Preserve the doorway gap in the stone courses.
        front=sin(mid)<-.9 and abs(cos(mid))<.33
        if front: continue
        wedge('Hand set plinth stone %02d_%02d'%(course,j),a0,a1,3.19,3.43-course*.035,z0,z0+h,'Stone',bevel=.033)
plinth_ring=ring('Plinth cap timber sill',1.52,3.18,.22,.20,'Wood')
seam_ring=ring('Lower plaster seam trim',1.73,3.13,.10,.075,'WoodLight')
cut(plinth_ring,door_cut); cut(seam_ring,door_cut)
discard(door_cut)

# Arched boarded entrance, segmented voussoirs, strap hinges and latch.
arch('Shadow inside doorway',1.82,.02,2.12,.12,(0,-2.70,0),'Iron',bevel=.015)
arch('Oak arched door',1.64,.08,2.08,.16,(0,-2.82,0),'WoodLight',bevel=.035)
for x in [-.66,-.44,-.22,0,.22,.44,.66]:
    top=2.08+math.sqrt(max(0,.80*.80-x*x))
    box('Door plank recessed seam',(x,-2.916,(.10+top)/2),(.015,.016,top-.10),'Wood',bevel=.004)
for side in (-1,1):
    box('Door stone jamb',(side*1.03,-3.10,1.10),(.29,.45,2.2),'Stone',bevel=.045)
for j in range(13):
    a=(j+.5)*pi/13; r=1.035
    o=box('Door arch voussoir %02d'%j,(r*cos(a),-3.10,2.10+r*sin(a)),(.245,.46,.30),'Stone',bevel=.025)
    o.rotation_euler.y=pi/2-a
for zz in (.58,1.75):
    box('Forged door strap',(0,-2.934,zz),(1.45,.055,.105),'Iron',bevel=.023)
    for xx in (-.64,-.35,.35,.64):
        cyl('Door rivet',(xx,-2.977,zz),.027,.034,'Iron',verts=12,bevel=.008,rot=(pi/2,0,0))
box('Latch handle',(0.56,-3.005,1.13),(.07,.13,.30),'Iron',bevel=.024)
box('Threshold stone',(0,-3.25,.06),(2.3,.64,.12),'Stone',bevel=.045)

# Window recesses and arched timber frames on the upper body.
def window(label,z,az,width=.80,height=1.0):
    rr=3.15-(z-1.45)/8.14*.93
    # az=0 is the south/front direction. Build locally then rotate as a group.
    before=set(PARTS['tower']); radius=width/2; spring=height-radius
    cutter=arch(label+' recess cutter',width+.13,-.04,spring,.72,(0,-rr,z),'Iron',bevel=0)
    cutter.rotation_euler.z=az; cutter.location=Vector((0,-rr,z)); cutter.location=Vector((rr*sin(az),-rr*cos(az),z))
    cut(shaft,cutter); discard(cutter)
    glass=arch(label+' deep glass',width-.10,.02,spring,.09,(0,-rr+.15,z),'Glass',bevel=.018)
    for side in (-1,1):
        box(label+' timber jamb',(side*(radius+.015),-rr-.08,z+spring/2),(.105,.16,spring+.06),'Wood',bevel=.024)
    for j in range(9):
        a=(j+.5)*pi/9; r=radius+.015
        o=box(label+' arched frame',(r*cos(a),-rr-.08,z+spring+r*sin(a)),(.16,.16,.10),'Wood',bevel=.018)
        o.rotation_euler.y=pi/2-a
    box(label+' sill',(0,-rr-.15,z-.035),(width+.28,.39,.14),'WoodLight',bevel=.028)
    box(label+' vertical mullion',(0,-rr-.02,z+height*.47),(.048,.10,height*.91),'WoodLight',bevel=.012)
    box(label+' cross mullion',(0,-rr-.02,z+spring*.68),(width-.07,.10,.047),'WoodLight',bevel=.01)
    # Shutter leaves retain slat detail and a modest asymmetry.
    for side in (-1,1):
        x=side*(radius+.29)
        for k in range(3):
            box(label+' shutter board',(x+(k-1)*.14,-rr-.02,z+height*.43),(.13,.10,height*.82),'WoodLight',bevel=.015)
        for zz in (z+.16,z+height*.69):
            box(label+' shutter strap',(x,-rr-.09,zz),(.43,.065,.065),'Iron',bevel=.012)
    for o in [p for p in PARTS['tower'] if p not in before]:
        # Geometry and location are rotated around tower origin together.
        o.matrix_world=Matrix.Rotation(az,4,'Z') @ o.matrix_world

window('Front lower window',3.52,0,.78,1.10)
window('Front upper window',6.55,0,.84,1.19)
window('West window',6.40,-pi/2,.80,1.15)
window('East window',3.55,pi/2,.77,1.08)
window('Rear loft window',7.35,pi,.70,.96)

# Polygonal gallery: individually fitted floor boards, corbels, rails and balusters.
balcony_z=5.35
ring('Gallery inner bearer',balcony_z-.12,2.73,.24,.24,'Wood',n=48)
ring('Gallery outer bearer',balcony_z-.12,3.50,.23,.27,'Wood',n=64)
for j in range(56):
    a=2*pi*j/56
    wedge('Gallery radial floorboard %02d'%j,a+.006,a+2*pi/56-.006,2.65,3.62,balcony_z,balcony_z+.12,'WoodLight',segments=2,bevel=.015)
for j in range(16):
    a=2*pi*j/16; ca,sa=cos(a),sin(a)
    beam('Gallery support strut',(2.83*ca,2.83*sa,4.30),(3.48*ca,3.48*sa,5.24),.17,mat='Wood',bevel=.025)
    box('Gallery beam end',(3.39*ca,3.39*sa,5.12),(.28,.28,.31),'Wood',bevel=.025)
    post=box('Gallery principal post',(3.48*ca,3.48*sa,5.91),(.15,.15,1.16),'Wood',bevel=.025)
    cyl('Gallery post peg',(3.48*ca,3.48*sa,6.52),.11,.09,'WoodLight',verts=12,bevel=.015)
for j in range(64):
    a=2*pi*(j+.5)/64
    box('Gallery slim baluster',(3.48*cos(a),3.48*sin(a),5.90),(.062,.062,.87),'WoodLight',bevel=.012)
ring('Gallery rounded top rail',6.46,3.48,.18,.15,'Wood',n=64)
ring('Gallery lower rail',5.56,3.48,.10,.10,'Wood',n=64)

# Top wall timber bond, eave fascia, wooden roof structure and individual cap shingles.
ring('Upper tower bond ring',9.30,2.28,.24,.25,'Wood')
ring('Eave board dark',9.53,2.65,.18,.30,'Wood')
ring('Eave board pale accent',9.72,2.65,.10,.075,'WoodLight')
roof=cyl('Cap substructure',(0,0,10.92),2.72,2.56,'Roof',verts=64,bevel=.025,r2=.23)
for j in range(16):
    a=2*pi*j/16
    beam('Exposed eave rafter',(2.15*cos(a),2.15*sin(a),9.35),(2.77*cos(a),2.77*sin(a),9.60),.13,mat='WoodLight',bevel=.018)

# Slightly irregular four-sided shingle tiles, overlapping rows, no bare conical roof.
for row in range(11):
    z0=9.58+row*.231
    z1=min(12.24,z0+.32)
    r0=2.78-(z0-9.58)*.975
    r1=2.78-(z1-9.58)*.975
    n=max(10,int(2*pi*r0/.35))
    for j in range(n):
        a=2*pi*(j+(row%2)*.5)/n
        da=2*pi/n*.49
        zz=random.uniform(-.018,.018)
        outer=[((r0+.05)*cos(a-da),(r0+.05)*sin(a-da),z0+zz),
               ((r0+.05)*cos(a+da),(r0+.05)*sin(a+da),z0+zz),
               ((r1+.05)*cos(a+da*.9),(r1+.05)*sin(a+da*.9),z1+zz),
               ((r1+.05)*cos(a-da*.9),(r1+.05)*sin(a-da*.9),z1+zz)]
        inner=[(x*.99,y*.99,z-.035) for x,y,z in outer]
        mesh('Cap shingle %02d_%03d'%(row,j),outer+inner,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'Roof',bevel=.009)
cyl('Cap ridge iron ferrule',(0,0,12.23),.30,.28,'Iron',verts=20,bevel=.03,r2=.19)
cyl('Cap finial',(0,0,12.48),.11,.30,'WoodLight',verts=16,bevel=.03,r2=.025)

# Axle bearing and wooden headstock remain on the tower; rotor is independent.
box('Axle support headstock',(0,-2.31,9.16),(.97,.58,.91),'Wood',bevel=.09)
for xx in (-.38,.38):
    box('Headstock iron strap',(xx,-2.64,9.16),(.11,.055,.78),'Iron',bevel=.023)
    for zz in (8.89,9.43):
        cyl('Headstock bolt',(xx,-2.69,zz),.047,.05,'Iron',verts=12,bevel=.008,rot=(pi/2,0,0))
cyl('Stationary axle',(0,-3.12,9.20),.18,1.80,'Iron',verts=24,bevel=.025,rot=(pi/2,0,0))

# Four canted timber lattice sweeps with sewn linen panels. Local origin is axle.
# Rotor local plane X/Z, negative Y faces viewers; assembly offset [0,-3.95,9.20].
# The forward offset gives gallery rails and flooring safe static sweep clearance.
for idx in range(4):
    ang=math.radians(18)+idx*pi/2
    def P(s,t,y=0): return (s*cos(ang)+t*sin(ang),y,-s*sin(ang)+t*cos(ang))
    beam('Sweep %d main spar'%idx,P(0,-.35,.04),P(0,5.95,.04),.24,.19,'Wood','rotor',.035)
    # Sails are asymmetric about the spar, like real lattice mill sweeps.
    for s in (-.22,.24,.71,1.15):
        beam('Sweep %d longitudinal lattice'%idx,P(s,1.35,.0),P(s,5.75,.0),.075,.075,'WoodLight','rotor',.015)
    for k in range(13):
        t=1.38+k*.365
        beam('Sweep %d crossbar %02d'%(idx,k),P(-.32,t,-.005),P(1.28,t,-.005),.07,.07,'WoodLight','rotor',.012)
    # Four individually edged linen panels show mild taut bowing, their frame stays exposed.
    for panel in range(4):
        t0=1.72+panel*.94; t1=t0+.85
        s0=.30; s1=1.08; nx=3; nz=4; vs=[]
        for zz in range(nz+1):
            v=zz/nz; tt=t0+(t1-t0)*v
            for xx in range(nx+1):
                u=xx/nx; ss=s0+(s1-s0)*u
                bulge=-.09-.065*sin(pi*u)*sin(pi*v)
                vs.append(P(ss,tt,bulge))
        fs=[]
        for zz in range(nz):
            for xx in range(nx):
                k=zz*(nx+1)+xx; fs.append((k,k+1,k+nx+2,k+nx+1))
        cloth=mesh('Sweep %d linen panel %d'%(idx,panel),vs,fs,'Canvas','rotor',0,True)
        solid=cloth.modifiers.new('Linen thickness','SOLIDIFY'); solid.thickness=.012
        for t in (t0+.018,t1-.018):
            beam('Sweep %d sewn linen hem'%idx,P(s0,t,-.102),P(s1,t,-.102),.022,.024,'Canvas','rotor',.007)
        for s in (s0+.012,s1-.012):
            beam('Sweep %d long linen hem'%idx,P(s,t0,-.102),P(s,t1,-.102),.022,.024,'Canvas','rotor',.007)
        for t in (t0,t1):
            for s in (.32,1.05):
                beam('Sweep %d linen lashing'%idx,P(s,t-.08,-.135),P(s,t+.08,.07),.025,.025,'Wood','rotor',.007)
    for t in (1.37,3.55,5.72):
        # Thin paired iron straps and visible round bolt heads tie the spar to frame.
        beam('Sweep %d spar strap'%idx,P(-.14,t,-.14),P(.15,t,-.14),.11,.025,'Iron','rotor',.009)
        p=P(0,t,-.18)
        cyl('Sweep %d spar bolt'%idx,p,.032,.035,'Iron','rotor',verts=12,bevel=.008,rot=(pi/2,0,0))
    beam('Sweep %d diagonal lattice brace'%idx,P(-.24,1.45,.05),P(1.12,3.45,.05),.052,.055,'Wood','rotor',.01)
    beam('Sweep %d upper diagonal brace'%idx,P(-.24,3.50,.05),P(1.12,5.68,.05),.052,.055,'Wood','rotor',.01)

cyl('Octagonal central oak hub',(0,-.01,0),.52,.43,'Wood','rotor',verts=8,bevel=.06,rot=(pi/2,0,0))
cyl('Wrought iron hub band',(0,-.245,0),.46,.10,'Iron','rotor',verts=32,bevel=.025,rot=(pi/2,0,0))
cyl('Hub axle boss',(0,-.335,0),.19,.18,'Iron','rotor',verts=20,bevel=.03,rot=(pi/2,0,0))
for j in range(8):
    a=j*2*pi/8
    cyl('Hub ring rivet',(cos(a)*.35,-.317,sin(a)*.35),.046,.05,'Iron','rotor',verts=12,bevel=.012,rot=(pi/2,0,0))

# Separate fitted doorstep set with masonry edge lines.
for j in range(3):
    for k in range(4):
        box('Entrance step %d stone %d'%(j,k),((k-1.5)*.56,-3.42-j*.37,.16-j*.045),(.54,.46,.20-j*.03),'Stone','steps',.042)

DETAIL['tower_components']=len(PARTS['tower'])
DETAIL['rotor_components']=len(PARTS['rotor'])
DETAIL['steps_components']=len(PARTS['steps'])

def finalize(group,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in PARTS[group]: o.select_set(True)
    bpy.context.view_layer.objects.active=PARTS[group][0]
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join()
    o=bpy.context.object; o.name=name; o.data.name=name+'_Geometry'
    scene.cursor.location=(0,0,0); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    # Consolidate slots into semantic surfaces without embedding textures.
    used=sorted({p.material_index for p in o.data.polygons})
    byname={}; old=list(o.data.materials); remap={}
    for i in used:
        nm=old[i].name
        if nm not in byname: byname[nm]=len(byname)
        remap[i]=byname[nm]
    indices=[remap[p.material_index] for p in o.data.polygons]
    o.data.materials.clear()
    for nm in byname: o.data.materials.append(MATS[nm])
    for p,mi in zip(o.data.polygons,indices): p.material_index=mi
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    # Boolean recess n-gons are triangulated before UV projection, so each
    # exported triangle receives a nondegenerate mapping on its actual plane.
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY',ngon_method='BEAUTY')
    bpy.ops.object.mode_set(mode='OBJECT')
    if not o.data.uv_layers: o.data.uv_layers.new(name='UV0')
    o.data.uv_layers.active.name='UV0'
    # Unique islands packed independently per material. Textures are per material.
    # The same 0..1 domain is reused by distinct material slots, disclosed below.
    for mi,m in enumerate(o.data.materials):
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
        for p in o.data.polygons: p.select=(p.material_index==mi)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.004,area_weight=1.0,correct_aspect=True,scale_to_bounds=False)
        if m.name=='Plaster':
            # Recess bevels contain narrow triangles that are unsuitable for
            # clustered planar projection. Give each plaster triangle an exact
            # intrinsic 2D island, then use the same unique-island packer.
            bpy.ops.object.mode_set(mode='OBJECT')
            uvs=o.data.uv_layers.active.data
            for p in o.data.polygons:
                if p.material_index!=mi: continue
                vs=[o.data.vertices[o.data.loops[li].vertex_index].co for li in p.loop_indices]
                origin=vs[0]; u=(vs[1]-origin).normalized()
                normal=(vs[1]-origin).cross(vs[2]-origin).normalized(); v=normal.cross(u)
                shift=Vector(((p.index%64)*20.0,(p.index//64)*20.0))
                for li,pt in zip(p.loop_indices,vs):
                    d=pt-origin; uvs[li].uv=Vector((d.dot(u),d.dot(v)))+shift
            bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.uv.average_islands_scale()
        bpy.ops.uv.pack_islands(rotate=True,margin_method='FRACTION',margin=.004)
        bpy.ops.object.mode_set(mode='OBJECT')
    for p in o.data.polygons: p.select=True
    o.data.update()
    return o

objects={}
for group,name in [('tower','SM_MillTower'),('rotor','SM_MillRotor'),('steps','SM_MillSteps')]:
    print('FINALIZE',name,flush=True)
    objects[name]=finalize(group,name)

def polygon_area2(vs):
    return abs(sum(vs[i][0]*vs[(i+1)%len(vs)][1]-vs[(i+1)%len(vs)][0]*vs[i][1] for i in range(len(vs))))*.5

def stats(o):
    me=o.data; me.calc_loop_triangles(); uv=me.uv_layers.active.data
    density=[]; deg=[]; out=0; stats_by_mat={}
    uvtris={i:[] for i in range(len(me.materials))}
    for tri in me.loop_triangles:
        pts=[uv[li].uv[:] for li in tri.loops]
        ua=polygon_area2(pts)
        if tri.area<=1e-12: continue
        if ua<=1e-12: deg.append(tri.polygon_index)
        d=1024*math.sqrt(max(0,ua)/tri.area)
        density.append(d)
        out+=sum(1 for u,v in pts if u < -1e-5 or u > 1.00001 or v < -1e-5 or v > 1.00001)
        mi=me.polygons[tri.polygon_index].material_index
        sm=stats_by_mat.setdefault(me.materials[mi].name,{'area_m2':0,'uv_area':0,'density_samples':[],'triangles':0})
        sm['area_m2']+=tri.area; sm['uv_area']+=ua; sm['density_samples'].append(d); sm['triangles']+=1
        uvtris[mi].append(pts)
    # Conservative occupancy raster at 1024, evaluated at triangle interiors;
    # misses subpixel overlaps. Exact UV triangle intersections are also checked.
    overlap={}
    for mi,tris in uvtris.items():
        # Spatially bucket UV triangles; intersect convex triangles using clipping.
        grid={}; overlaps=0; tested=set(); examples=[]
        def signed(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        def intersection_area(a,b):
            poly=list(a); orient=1 if signed(*b)>=0 else -1
            for i in range(3):
                c,d=b[i],b[(i+1)%3]; res=[]
                if not poly:return 0.0
                p=poly[-1]; sp=orient*signed(c,d,p)
                for q in poly:
                    sq=orient*signed(c,d,q)
                    if (sq>=0)!=(sp>=0):
                        t=sp/(sp-sq); res.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
                    if sq>=0:res.append(q)
                    p=q;sp=sq
                poly=res
            return polygon_area2(poly) if len(poly)>=3 else 0.0
        for ti,t in enumerate(tris):
            x0=max(0,int(min(p[0] for p in t)*48)); x1=min(47,int(max(p[0] for p in t)*48))
            y0=max(0,int(min(p[1] for p in t)*48)); y1=min(47,int(max(p[1] for p in t)*48))
            candidates=set()
            for x in range(x0,x1+1):
                for y in range(y0,y1+1): candidates.update(grid.get((x,y),[]))
            for tj in candidates:
                area=intersection_area(t,tris[tj])
                if area>1e-10:
                    overlaps+=1
                    if len(examples)<4:examples.append({'triangle_a':ti,'triangle_b':tj,'intersection_uv_area':area})
            for x in range(x0,x1+1):
                for y in range(y0,y1+1):grid.setdefault((x,y),[]).append(ti)
        overlap[me.materials[mi].name]={'overlapping_triangle_pairs':overlaps,'examples':examples,'method':'exact convex triangle clipping, area threshold 1e-10, per material; shared borders excluded'}
    for sm in stats_by_mat.values():
        ds=sm.pop('density_samples'); sm['density_px_per_m']={'min':min(ds),'median':statistics.median(ds),'max':max(ds),'area_weighted_equivalent':1024*math.sqrt(sm['uv_area']/sm['area_m2'])}
    return {'name':o.name,'vertices':len(me.vertices),'triangles':len(me.loop_triangles),'surface_area_m2':sum(t.area for t in me.loop_triangles),
        'bounds_local_m':{'min':[min(v.co[i] for v in me.vertices) for i in range(3)],'max':[max(v.co[i] for v in me.vertices) for i in range(3)]},
        'material_slots':[m.name for m in me.materials], 'uv_layer':'UV0','target_texture_resolution':1024,'target_texel_density_px_per_m':128,
        'actual_density_px_per_m':{'min':min(density),'median':statistics.median(density),'max':max(density)},
        'degenerate_uv_triangles':len(deg),'uv_coordinates_outside_01':out,'material_surface_statistics':stats_by_mat,'uv_overlap':overlap,
        'uv_padding_fraction':.004,'uv_padding_nominal_px_at_1024':4.096,
        'uv_note':'Unique Smart Project islands packed in 0..1 independently per material. Plaster recess triangles use intrinsic per-face planar islands after Smart Project to prevent narrow-cut collapses. Cross-material UV domains intentionally reused. No intentional overlap within a material. At 1024 resolution large material surfaces fall below 128px/m; measured exceptions are provided per slot.'}

manifest={'theme':'WindmillFarm','effort':'ultra','started_at_utc':START.isoformat(),'blender_version':bpy.app.version_string,
    'units':'metres','up':'Z','front':'-Y','rotor_spin_axis':'local Y','source_assets':'None. All geometry authored independently by this script.',
    'export_settings':{'global_scale':1,'apply_unit_scale':True,'axis_forward':'-Y','axis_up':'Z','bake_space_transform':False,'use_selection':True,'add_leaf_bones':False,'embed_textures':False},
    'assembly_offsets_m':{'SM_MillTower':[0,0,0],'SM_MillRotor':[0,-3.95,9.20],'SM_MillSteps':[0,0,0]},
    'assembly_rotation_degrees':{'SM_MillTower':[0,0,0],'SM_MillRotor':[0,0,0],'SM_MillSteps':[0,0,0]},
    'source_component_counts':DETAIL,'assets':[],'limitations':['No Unreal import, collision or in-engine render performed by this asset task. Parent handles these checks.','Arch and window openings are shallow facade recesses, not traversable building interiors.','Static mesh only; independent rotor pivot supports parent animation if desired.']}
for name,o in objects.items():
    print('VALIDATE',name,flush=True)
    st=stats(o); manifest['assets'].append(st)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.export_scene.fbx(filepath=os.path.join(ROOT,name+'.fbx'),use_selection=True,object_types={'MESH'},global_scale=1,
        apply_unit_scale=True,axis_forward='-Y',axis_up='Z',bake_space_transform=False,add_leaf_bones=False,embed_textures=False,
        use_mesh_modifiers=True,mesh_smooth_type='FACE',path_mode='AUTO',bake_anim=False)
    print('EXPORTED',name,len(o.data.vertices),'vertices',flush=True)

# Source-art QA render. This is explicitly not UE scene evidence.
objects['SM_MillRotor'].location=(0,-3.95,9.20)
groundmat=bpy.data.materials.new('Preview_only_ground'); groundmat.diffuse_color=(.23,.255,.19,1); groundmat.use_nodes=True
groundmat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.23,.255,.19,1)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.02)); ground=bpy.context.object;ground.name='Preview_only_ground';ground.data.materials.append(groundmat)
world=bpy.data.worlds.new('Preview_world') if not bpy.data.worlds else bpy.data.worlds[0];scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.56,.63,.72,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
bpy.ops.object.light_add(type='AREA',location=(-10,-12,20)); light=bpy.context.object;light.name='Preview_key';light.data.energy=3000;light.data.shape='DISK';light.data.size=12
light.rotation_euler=(Vector((0,0,6))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.light_add(type='SUN',location=(8,6,15));sun=bpy.context.object;sun.name='Preview_sun';sun.rotation_euler=(.45,-.35,-.55);sun.data.energy=1.8;sun.data.angle=.08
bpy.ops.object.camera_add(location=(19,-28,16));cam=bpy.context.object;cam.name='Preview_camera';cam.rotation_euler=(Vector((0,0,7))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=19;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1400;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'Windmill_Source.blend'))
scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(ROOT,'windmill_source_preview.png')
print('RENDER_SOURCE_PREVIEW',flush=True)
bpy.ops.render.render(write_still=True)
manifest['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
manifest['elapsed_seconds']=(datetime.datetime.now(datetime.timezone.utc)-START).total_seconds()
manifest['preview']='windmill_source_preview.png — Blender source-art QA only, not Unreal scene evidence.'
with open(os.path.join(ROOT,'manifest.json'),'w',encoding='utf8') as f:json.dump(manifest,f,indent=2)
print('WINDMILL_BUILD_COMPLETE',json.dumps({'asset_count':len(manifest['assets']),'elapsed_seconds':manifest['elapsed_seconds']}),flush=True)
