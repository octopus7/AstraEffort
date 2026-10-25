"""Rabbit three-wheel autonomous bike. Isolated Blender 4.5 asset build."""
import bpy,bmesh,math,json,time
from pathlib import Path
from mathutils import Vector
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1];START=time.time();TAU=math.tau
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.24,.29,.35,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
ASSET=bpy.data.collections.new('RABBIT_BIKE');scene.collection.children.link(ASSET)
STUDIO=bpy.data.collections.new('STUDIO_NOT_EXPORTED');scene.collection.children.link(STUDIO)
parts=[]
def log(s):print('RABBIT: '+s,flush=True)
def mat(name,color,metal=0,rough=.5,tex=None,emit=None):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;bs=n.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
    if tex:
        im=n.new('ShaderNodeTexImage');im.name='Generated_Source';im.image=bpy.data.images.load(str(ROOT/'textures'/tex),check_existing=True)
        uv=n.new('ShaderNodeTexCoord');sc=n.new('ShaderNodeVectorMath');sc.operation='SCALE';sc.inputs[3].default_value=8 if tex=='generated_rubber.png' else 4
        m.node_tree.links.new(uv.outputs['UV'],sc.inputs[0]);m.node_tree.links.new(sc.outputs['Vector'],im.inputs['Vector'])
        if tex=='generated_rubber.png':
            mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[0].default_value=.12;mix.inputs[1].default_value=(*color,1)
            m.node_tree.links.new(im.outputs['Color'],mix.inputs[2]);m.node_tree.links.new(mix.outputs['Color'],bs.inputs['Base Color'])
        else:m.node_tree.links.new(im.outputs['Color'],bs.inputs['Base Color'])
    if emit:bs.inputs['Emission Color'].default_value=(*emit,1);bs.inputs['Emission Strength'].default_value=2.5
    return m
ivory=mat('01_Ivory_Ceramic',(.8,.73,.6),.13,.4,'generated_ivory.png')
orange=mat('02_Tangerine_Enamel',(.8,.25,.04),.3,.36,'generated_orange.png')
rubber=mat('03_Tire_Rubber',(.025,.027,.03),.02,.76,'generated_rubber.png')
graphite=mat('04_Graphite_Alloy',(.06,.075,.085),.45,.43)
steel=mat('05_Brushed_Titanium',(.34,.38,.4),.82,.28)
seat=mat('06_Saddle_Cushion',(.055,.061,.065),.03,.66,'generated_rubber.png')
black=mat('07_Gaskets',(.012,.017,.022),.12,.48)
glass=mat('08_Sensor_Glass',(.016,.035,.045),.4,.15)
light=mat('09_Amber_Headlight',(1,.34,.035),.05,.2,emit=(1,.27,.018))
corelight=mat('10_Light_Core',(1,.7,.32),.05,.2,emit=(1,.56,.22))
red=mat('11_Red_Tail_Light',(.65,.012,.006),.05,.22,emit=(1,.02,.005))
blue=mat('12_Sensor_Status',(.01,.25,.4),.05,.2,emit=(.02,.42,.65))
MATS=[ivory,orange,rubber,graphite,steel,seat,black,glass,light,corelight,red,blue]

def link(o,col=ASSET):
    for c in list(o.users_collection):c.objects.unlink(o)
    col.objects.link(o)
def finish(o,name,m,group='Body',bevel=0,smooth=True):
    o.name=name;link(o);o.data.materials.append(m);o['assembly']=group
    if smooth:
        for p in o.data.polygons:p.use_smooth=True
    if bevel:
        mod=o.modifiers.new('Soft manufactured edge','BEVEL');mod.width=bevel;mod.segments=3;mod.limit_method='ANGLE'
        mod=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');mod.keep_sharp=True
    parts.append(o);return o
def mesh(name,verts,faces,m,group='Body',bevel=0,smooth=True):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);ASSET.objects.link(o)
    return finish(o,name,m,group,bevel,smooth)
def box(name,loc,size,m,group='Body',bevel=.015,rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if rot:o.rotation_euler=rot
    return finish(o,name,m,group,bevel)
def cyl(name,a,b,r,m,group='Mechanics',r2=None,seg=24,bevel=.003):
    a,b=Vector(a),Vector(b);d=b-a
    bpy.ops.mesh.primitive_cone_add(vertices=seg,radius1=r,radius2=r if r2 is None else r2,depth=d.length,location=(a+b)/2)
    o=bpy.context.object;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return finish(o,name,m,group,bevel)
def torus(name,loc,r,minor,m,group='Mechanics',axis=(1,0,0),seg=48):
    bpy.ops.mesh.primitive_torus_add(major_segments=seg,minor_segments=8,major_radius=r,minor_radius=minor,location=loc)
    o=bpy.context.object;o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler();return finish(o,name,m,group)
def sphere(name,loc,scale,m,group='Mechanics'):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=loc);o=bpy.context.object;o.scale=scale;return finish(o,name,m,group)
def side_panel(name,poly,x,thick,m,group='Body',bevel=.015):
    n=len(poly);verts=[(xx,y,z) for xx in (x-thick/2,x+thick/2) for y,z in poly]
    faces=[tuple(reversed(range(n))),tuple(n+j for j in range(n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
    return mesh(name,verts,faces,m,group,bevel)
def loft(name,sections,m,group='Body',seg=40):
    verts=[]
    for y,w,zc,h in sections:
        for j in range(seg):
            a=TAU*j/seg;verts.append((w*math.cos(a),y,zc+h*math.sin(a)))
    faces=[(i*seg+j,i*seg+(j+1)%seg,(i+1)*seg+(j+1)%seg,(i+1)*seg+j) for i in range(len(sections)-1) for j in range(seg)]
    faces.extend([tuple(reversed(range(seg))),tuple((len(sections)-1)*seg+j for j in range(seg))])
    o=mesh(name,verts,faces,m,group)
    # A cylindrical chart with physical cross-section arc length stays injective
    # even on the very thin inset shells; planar projection folds these edges.
    uv=o.data.uv_layers.new(name='UV_Unique');arcs=[]
    for y,w,zc,h in sections:
        arc=[0]
        for j in range(seg):
            a=TAU*j/seg;b=TAU*(j+1)/seg
            arc.append(arc[-1]+math.hypot(w*(math.cos(b)-math.cos(a)),h*(math.sin(b)-math.sin(a))))
        arcs.append(arc)
    for p in o.data.polygons:
        if p.index<(len(sections)-1)*seg:
            i,j=divmod(p.index,seg)
            coords=[(sections[i][0],arcs[i][j]),(sections[i][0],arcs[i][j+1]),(sections[i+1][0],arcs[i+1][j+1]),(sections[i+1][0],arcs[i+1][j])]
        else:
            off=10 if p.index==(len(sections)-1)*seg else 20
            coords=[(o.data.vertices[v].co.x+off,o.data.vertices[v].co.z+off) for v in p.vertices]
        for li,co in zip(p.loop_indices,coords):uv.data[li].uv=co
    o['analytical_uv']=name!='Central_graphite_frame'
    sub=o.modifiers.new('Continuous sculpted shell','SUBSURF');sub.levels=2;sub.render_levels=2
    return o

def tire(name,c,r,w):
    # Cross-section loop: the two seams are unique, never mirrored or stacked.
    prof=[(-.36,.66),(-.49,.74),(-.50,.87),(-.43,.96),(-.30,1.0),(-.15,1.0),(0,1.0),(.15,1.0),(.30,1.0),(.43,.96),(.50,.87),(.49,.74),(.36,.66)]
    seg=288;verts=[]
    for pi,(xx,rr) in enumerate(prof):
        for j in range(seg):
            a=TAU*j/seg;rad=r*rr
            if rr>=.96:
                # Staggered physical chevron channels, no painted fake tread.
                phase=(j/seg*24+abs(xx)*.92)%1
                if phase<.16:rad-=r*.020
                if abs(xx)<.02:rad-=r*.008
            verts.append((c[0]+xx*w,c[1]+rad*math.sin(a),c[2]+rad*math.cos(a)))
    faces=[]
    for i in range(len(prof)):
        for j in range(seg):faces.append((i*seg+j,i*seg+(j+1)%seg,((i+1)%len(prof))*seg+(j+1)%seg,((i+1)%len(prof))*seg+j))
    o=mesh(name,verts,faces,rubber,name)
    uv=o.data.uv_layers.new(name='UV_Unique');arcs=[0]
    for i in range(len(prof)):
        x0,r0=prof[i];x1,r1=prof[(i+1)%len(prof)];arcs.append(arcs[-1]+math.hypot((x1-x0)*w,(r1-r0)*r))
    for p in o.data.polygons:
        i=p.index//seg;j=p.index%seg
        coords=[(j/seg*TAU*r,arcs[i]),((j+1)/seg*TAU*r,arcs[i]),((j+1)/seg*TAU*r,arcs[i+1]),(j/seg*TAU*r,arcs[i+1])]
        for li,v in zip(p.loop_indices,coords):uv.data[li].uv=v
    o['analytical_uv']=True
    return o

def wheel(label,center,r,w):
    x,y,z=center;group='Wheel_'+label
    tire('Tire_'+label,center,r,w)
    cyl('Axle_'+label,(x-w*.61,y,z),(x+w*.61,y,z),r*.20,steel,group,seg=32)
    for sign in (-1,1):
        xs=x+sign*w*.50
        cyl('Rim_backing',(xs-sign*.012,y,z),(xs+sign*.006,y,z),r*.725,graphite,group,seg=64,bevel=.004)
        torus('Orange_rim_lip',(xs+sign*.007,y,z),r*.715,r*.037,orange,group,seg=64)
        # Three-piece aero cover with shallow radial separation.
        for sector in range(3):
            a0=sector*TAU/3+.035;a1=(sector+1)*TAU/3-.035
            ring=[]
            for rad in (r*.17,r*.645):
                for k in range(17):
                    a=a0+(a1-a0)*k/16;ring.append((xs+sign*(.018 if rad<r*.3 else .011),y+rad*math.sin(a),z+rad*math.cos(a)))
            fs=[(k,k+1,17+k+1,17+k) for k in range(16)]
            o=mesh('Ivory_aero_cover',ring,fs,ivory,group)
            so=o.modifiers.new('Aero cover thickness','SOLIDIFY');so.thickness=.008
            be=o.modifiers.new('Soft cover rim','BEVEL');be.width=.004;be.segments=2;be.limit_method='ANGLE'
        cyl('Hub_orange_ring',(xs,y,z),(xs+sign*.030,y,z),r*.18,orange,group,seg=32)
        cyl('Hub_center',(xs+sign*.029,y,z),(xs+sign*.036,y,z),r*.115,graphite,group,seg=24)
        for j in range(5):
            a=j*TAU/5;yy=y+r*.24*math.sin(a);zz=z+r*.24*math.cos(a)
            cyl('Hub_bolt',(xs+sign*.015,yy,zz),(xs+sign*.020,yy,zz),.006,steel,group,seg=8,bevel=.001)
        torus('Sidewall_bead',(xs-sign*.014,y,z),r*.83,.0025,black,group,seg=64)

log('Build three wheels, differential track and visible suspension')
wheel('Front_L',(-.639,-.72,.325),.325,.25)
wheel('Front_R',(.639,-.72,.325),.325,.25)
wheel('Rear',(0,.94,.425),.425,.34)

for sign in (-1,1):
    group='Suspension_'+('L' if sign<0 else 'R')
    # Two wishbones, steering knuckle, diagonal damper and a separate tie rod.
    for z in (.28,.46):
        for y in (-.91,-.40):
            cyl('Wishbone_arm',(sign*.22,y,z+.02),(sign*.55,-.72,z),.035,graphite,group)
            cyl('Wishbone_inner_pivot',(sign*.20,y-.045,z+.02),(sign*.20,y+.045,z+.02),.048,steel,group,seg=20)
            a=Vector((sign*.22,y,z+.02));b=Vector((sign*.55,-.72,z));dv=b-a
            cyl('Amber_arm_collar',a+dv*.68,a+dv*.84,.040,orange,group,seg=24)
        torus('Pivot_recess_ring',(sign*.20,-.958,z+.02),.037,.007,graphite,group,axis=(0,1,0),seg=24)
        cyl('Pivot_hex_bolt',(sign*.20,-.962,z+.02),(sign*.20,-.970,z+.02),.017,steel,group,seg=6,bevel=.001)
        cyl('Outer_ball_joint',(sign*.53,-.72,z),(sign*.59,-.72,z),.048,steel,group,seg=24)
    cyl('Steering_upright',(sign*.555,-.72,.23),(sign*.555,-.72,.51),.047,graphite,group)
    top=Vector((sign*.31,-.49,.75));bottom=Vector((sign*.57,-.72,.32));dv=top-bottom
    cyl('Damper_polished_rod',bottom,top,.025,steel,group)
    cyl('Orange_shock_body',bottom+dv*.40,top-dv*.09,.049,orange,group)
    for t in (.35,.42,.82,.90):
        p=bottom+dv*t;torus('Shock_collar',p,.046,.007,graphite if t in (.35,.90) else steel,group,axis=dv)
    for p in (top,bottom):
        cyl('Damper_eye',p-Vector((.035,0,0)),p+Vector((.035,0,0)),.047,graphite,group,seg=24)
    cyl('Steering_link',(sign*.19,-.92,.39),(sign*.57,-.80,.40),.018,steel,group)
    sphere('Spherical_knuckle',(sign*.56,-.72,.325),(.07,.063,.07),graphite,group)
    cyl('Visible_axle',(sign*.53,-.72,.325),(sign*.69,-.72,.325),.055,orange,group,seg=24)
    # Double-sided swingarm supports the rear wheel.
    side_panel('Rear_swingarm',[(.18,.49),(.27,.59),(.94,.50),(1.00,.40),(.89,.34),(.24,.40)],sign*.23,.095,graphite,'Rear_Swingarm',.026)
    side_panel('Swingarm_recess',[(.34,.48),(.43,.51),(.83,.45),(.86,.40),(.42,.42)],sign*.283,.012,steel,'Rear_Swingarm',.009)
    cyl('Swingarm_front_pivot',(sign*.18,.25,.49),(sign*.31,.25,.49),.075,steel,'Rear_Swingarm',seg=32)
    cyl('Swingarm_hub_bearing',(sign*.17,.94,.425),(sign*.30,.94,.425),.085,graphite,'Rear_Swingarm',seg=32)
    cyl('Swingarm_hub_cap',(sign*.29,.94,.425),(sign*.315,.94,.425),.057,orange,'Rear_Swingarm',seg=32)

log('Sculpt the rabbit cowl, side body, saddle and tall decorative ears')
loft('Central_graphite_frame',[(-.90,.17,.49,.09),(-.72,.24,.48,.14),(-.36,.27,.49,.16),(.12,.26,.49,.16),(.52,.26,.54,.17),(.76,.18,.64,.13)],graphite,'Frame')
loft('Rounded_front_cowl',[(-1.028,.105,.714,.038),(-1.015,.18,.73,.07),(-.91,.265,.77,.12),(-.72,.32,.82,.165),(-.48,.35,.85,.19),(-.25,.31,.86,.18),(-.08,.25,.80,.14),(.02,.15,.73,.07)],ivory,'Front_Cowl')
# A smaller panel sits naturally on the sloping hood, with a graphite seam behind it.
loft('Cowl_inset_gasket',[(-.94,.085,.828,.008),(-.83,.19,.906,.010),(-.61,.237,.988,.010),(-.40,.22,1.039,.010),(-.26,.16,1.032,.008)],graphite,'Front_Cowl',seg=24)
loft('Cowl_inset_ivory',[(-.93,.080,.833,.009),(-.82,.185,.912,.010),(-.60,.232,.994,.010),(-.40,.215,1.045,.010),(-.27,.155,1.038,.008)],ivory,'Front_Cowl',seg=24)

def facepatch(name,poly,m,offset=0,group='Face',thick=.012):
    n=len(poly);verts=[]
    for dy in (0,thick):
        for x,z in poly:verts.append((x,-1.073+1.90*x*x+offset+dy,z))
    faces=[tuple(reversed(range(n))),tuple(n+j for j in range(n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
    return mesh(name,verts,faces,m,group,.006)
facepatch('Dark_eye_mask',[(-.283,.791),(-.275,.695),(-.17,.658),(.17,.658),(.275,.695),(.283,.791)],black)
for sign in (-1,1):
    pts=[(.080,.741),(.258,.778),(.246,.728),(.087,.704)]
    facepatch('Amber_eye',[(sign*x,z) for x,z in pts],light,-.009,thick=.006)
    pts=[(.100,.738),(.245,.768),(.236,.742),(.102,.715)]
    facepatch('Headlight_inner_strip',[(sign*x,z) for x,z in pts],corelight,-.017,thick=.004)
# A quad strip replaces the concave curved n-gon, so the lower lip cannot
# self-intersect when triangulated or projected into UVs.
verts=[];nx=32
for layer in (0,.012):
    for row in (0,1):
        for j in range(nx+1):
            x=-.258+.516*j/nx;z=.627+.048*(abs(x)/.258)**2+row*.025
            verts.append((x,-1.063+1.90*x*x+layer,z))
stride=nx+1;faces=[]
for j in range(nx):
    faces += [(j,j+1,stride+j+1,stride+j),(2*stride+j,3*stride+j,3*stride+j+1,2*stride+j+1),(j,2*stride+j,2*stride+j+1,j+1),(stride+j,stride+j+1,3*stride+j+1,3*stride+j)]
faces += [(0,stride,3*stride,2*stride),(nx,2*stride+nx,3*stride+nx,stride+nx)]
mesh('Lower_ivory_face_lip',verts,faces,ivory,'Face',.003)
loft('Chin_bumper',[(-1.025,.11,.60,.035),(-.98,.20,.59,.06),(-.84,.23,.58,.065),(-.77,.21,.57,.04)],graphite,'Face',seg=24)
for x in (-.039,.039):
    cyl('Forward_sensor_lens',(x,-1.086,.703),(x,-1.094,.703),.014,glass,'Face',seg=20,bevel=.002)
box('Forehead_sensor_mount',(0,-.37,1.047),(.145,.17,.028),graphite,'Sensors',.018,rot=(.10,0,0))
box('Forehead_sensor_window',(0,-.413,1.067),(.075,.060,.009),glass,'Sensors',.012)

for sign in (-1,1):
    side_panel('Main_side_panel',[(-.29,.72),(-.14,.94),(.16,.99),(.49,.91),(.69,.76),(.56,.48),(.10,.405),(-.20,.49)],sign*.285,.080,ivory,'Body_Panels',.045)
    side_panel('Side_service_gasket',[(-.05,.56),(.02,.78),(.29,.81),(.36,.60),(.28,.48),(.06,.46)],sign*.330,.011,graphite,'Body_Details',.018)
    side_panel('Side_service_cover',[(-.035,.562),(.03,.768),(.279,.788),(.342,.60),(.27,.493),(.064,.477)],sign*.339,.012,ivory,'Body_Details',.016)
    box('Side_service_latch',(sign*.351,.15,.64),(.018,.048,.12),graphite,'Body_Details',.008)
    box('Side_latch_inlay',(sign*.363,.15,.64),(.008,.016,.07),steel,'Body_Details',.004)
    side_panel('Amber_battery_marker',[(.36,.53),(.43,.55),(.45,.73),(.39,.77)],sign*.337,.013,orange,'Body_Details',.006)
    side_panel('Upper_side_intake',[(-.13,.89),(-.12,.96),(-.035,.98),(.02,.91)],sign*.319,.016,black,'Body_Details',.008)
    for j in range(3):
        box('Intake_louver',(sign*.333,-.077+j*.022,.93),(.014,.008,.043),steel,'Body_Details',.003,rot=(.15,0,0))
    for y,z in ((-.18,.53),(.07,.44),(.51,.53),(.48,.84),(-.08,.91)):
        cyl('Panel_fastener',(sign*.327,y,z),(sign*.339,y,z),.008,steel,'Body_Details',seg=8,bevel=.001)

box('Saddle_recess',(0,.225,.865),(.47,.71,.105),black,'Saddle',.06)
for x in (-.095,.095):
    for y in (.06,.25):box('Segmented_seat_cushion',(x,y,.920),(.18,.18,.075),seat,'Saddle',.035)
box('Seat_front_bolster',(0,-.075,.926),(.39,.085,.090),seat,'Saddle',.035)
box('Seat_backrest',(0,.47,.993),(.40,.14,.19),seat,'Saddle',.043,rot=(math.radians(12),0,0))
box('Backrest_center_pad',(0,.392,1.012),(.29,.034,.13),graphite,'Saddle',.020,rot=(math.radians(12),0,0))
loft('Rear_upper_shell',[(.47,.25,.86,.12),(.63,.27,.89,.12),(.85,.25,.92,.10),(1.07,.21,.93,.06),(1.24,.13,.91,.025)],ivory,'Rear_Cowl',seg=32)
loft('Tail_orange_spine',[(.59,.15,1.008,.015),(.77,.17,1.022,.018),(.97,.14,1.010,.018),(1.15,.095,.966,.014)],orange,'Rear_Cowl',seg=24)

def ear(name,sign,scale=1,offset=0,m=ivory,thick=.04):
    poly=[(-.055,0),(-.085,.13),(-.058,.35),(.015,.55),(.065,.53),(.080,.37),(.056,.13),(.040,.018)]
    controls=[Vector(p) for p in poly];poly=[]
    for i in range(len(controls)):
        p0,p1,p2,p3=[controls[k%len(controls)] for k in (i-1,i,i+1,i+2)]
        for j in range(4):
            t=j/4;v=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)
            poly.append(tuple(v))
    verts=[]
    for layer in (0,thick):
        for u,v in poly:
            u*=scale;v=(v-.26)*scale+.26
            verts.append((sign*(.225+.17*v/.55+u),-.36+.21*v/.55+offset+layer,1.005+v))
    n=len(poly);faces=[tuple(reversed(range(n))),tuple(n+j for j in range(n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
    return mesh(name,verts,faces,m,'Ears',.012)
for sign in (-1,1):
    ear('Rabbit_ear_shell',sign)
    ear('Ear_dark_inner_border',sign,.82,-.008,graphite,.012)
    ear('Ear_orange_inset',sign,.65,-.018,orange,.008)
    cyl('Ear_mount_hinge',(sign*.20,-.35,1.025),(sign*.27,-.35,1.025),.047,graphite,'Ears',seg=24)

log('Rear duct modules, lamps, panel fittings and cooling')
def duct(name,x,z):
    # Section revolved around +Y, with a recessed open bore and closed wall thickness.
    prof=[(.98,.061),(1.11,.088),(1.18,.086),(1.19,.074),(1.14,.067),(1.01,.045),(.98,.061)]
    seg=40;verts=[(x+r*math.cos(TAU*j/seg),y,z+r*math.sin(TAU*j/seg)) for y,r in prof for j in range(seg)]
    faces=[(i*seg+j,i*seg+(j+1)%seg,(i+1)*seg+(j+1)%seg,(i+1)*seg+j) for i in range(len(prof)-1) for j in range(seg)]
    mesh(name,verts,faces,graphite,'Rear_Modules')
    torus('Duct_metal_lip',(x,1.17,z),.078,.009,steel,'Rear_Modules',axis=(0,1,0),seg=40)
    cyl('Duct_recess',(x,1.005,z),(x,1.016,z),.046,black,'Rear_Modules',seg=32,bevel=0)
for sign in (-1,1):
    box('Rear_duct_housing',(sign*.285,1.00,.697),(.15,.21,.33),ivory,'Rear_Modules',.055)
    duct('Upper_rear_duct',sign*.29,.805);duct('Lower_rear_duct',sign*.29,.585)
    side_panel('Rear_module_side_insert',[(.91,.64),(.91,.78),(1.02,.79),(1.08,.70),(1.02,.61)],sign*.365,.01,graphite,'Rear_Modules',.018)
    for z in (.65,.76):cyl('Rear_module_bolt',(sign*.371,.98,z),(sign*.379,.98,z),.008,steel,'Rear_Modules',seg=8,bevel=.001)
box('Tail_lamp_recess',(0,1.215,.925),(.31,.06,.085),black,'Rear_Lights',.025)
box('Tail_red_strip',(0,1.249,.929),(.235,.014,.032),red,'Rear_Lights',.012)
box('Tail_small_diagnostic',(0,1.25,.886),(.06,.011,.012),blue,'Rear_Lights',.004)
for sign in (-1,1):
    box('Front_amber_reflector',(sign*.307,-.52,.896),(.018,.074,.024),orange,'Body_Details',.007)
    for y in (-.81,-.58):
        sphere('Cowl_recessed_screw',(sign*.245,y,.87 if y<-.7 else .98),(.006,.006,.004),steel,'Body_Details')

log('Apply rounded edges and retain component vertex groups')
bpy.context.scene.tool_settings.use_uv_select_sync=True
for o in parts:
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.0000001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    vg=o.vertex_groups.new(name=o.name);vg.add(list(range(len(o.data.vertices))),1,'REPLACE')
    if not o.get('analytical_uv',False):
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(65),island_margin=0,area_weight=0,correct_aspect=True,scale_to_bounds=False)
        bpy.ops.object.mode_set(mode='OBJECT')
    o.data.uv_layers.active.name='UV_Unique'
groups=defaultdict(list)
for o in parts:groups[o['assembly']].append(o)
meshes=[]
for group,obs in groups.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    if len(obs)>1:bpy.ops.object.join()
    o=bpy.context.object;o.name='RB_'+group;meshes.append(o);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)

log('Unique UVs: analytical tires/lofts, projected individual components, global area normalization')
bpy.context.scene.tool_settings.use_uv_select_sync=True
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.average_islands_scale()
log('Pack '+str(bpy.ops.uv.pack_islands('EXEC_DEFAULT',rotate=True,scale=True,merge_overlap=False,margin_method='FRACTION',margin=.002,shape_method='CONVEX')))
bpy.ops.object.mode_set(mode='OBJECT')
for o in meshes:o.data.uv_layers.active.name='UV_Unique'

log('Bake three image-generated surfaces into one unlit 4K atlas')
atlas=bpy.data.images.new('RabbitBike_BaseColor_4096',width=4096,height=4096,alpha=False);atlas.generated_color=(.04,.045,.05,1)
for m in MATS:
    n=m.node_tree.nodes
    for node in n:node.select=False
    dest=n.new('ShaderNodeTexImage');dest.name='Final_Unique_Atlas';dest.image=atlas;dest.select=True;n.active=dest
    bs=n.get('Principled BSDF');em=n.new('ShaderNodeEmission');em.name='Temporary_Bake'
    if bs.inputs['Base Color'].is_linked:m.node_tree.links.new(bs.inputs['Base Color'].links[0].from_socket,em.inputs['Color'])
    else:em.inputs['Color'].default_value=bs.inputs['Base Color'].default_value
    m.node_tree.links.new(em.outputs[0],n.get('Material Output').inputs['Surface'])
scene.cycles.samples=1;bpy.ops.object.bake(type='EMIT',use_clear=True,margin=8)
atlas.filepath_raw=str(ROOT/'textures'/'RabbitBike_BaseColor_4096.png');atlas.file_format='PNG';atlas.save()
for m in MATS:
    n=m.node_tree.nodes;bs=n.get('Principled BSDF');m.node_tree.links.new(n['Final_Unique_Atlas'].outputs['Color'],bs.inputs['Base Color'])
    m.node_tree.links.new(bs.outputs['BSDF'],n.get('Material Output').inputs['Surface']);n.remove(n['Temporary_Bake'])
log('Export GLB with embedded texture')
bpy.ops.export_scene.gltf(filepath=str(ROOT/'RabbitBike.glb'),export_format='GLB',use_selection=True,export_apply=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_animations=False,export_cameras=False,export_lights=False,export_extras=True)

def area(name,loc,power,size,color,target=(0,0,.65)):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);STUDIO.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
floor=mat('Studio_floor',(.14,.18,.22),.08,.48)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.012));o=bpy.context.object;o.name='Studio_Floor';link(o,STUDIO);o.data.materials.append(floor)
area('Large_warm_key',(-3,-4,5),440,4,(1,.89,.76))
area('Cool_rim',(3,3,4),550,3,(.70,.83,1))
area('Front_fill',(4,-2,2),250,3,(.9,.95,1))
area('Overhead_softbox',(-1,1,6),300,3,(1,.97,.9))
d=bpy.data.cameras.new('Presentation_Camera');cam=bpy.data.objects.new('Presentation_Camera',d);STUDIO.objects.link(cam);scene.camera=cam;d.type='ORTHO';d.ortho_scale=3.45
cam.location=(3.3,-4.7,2.65);cam.rotation_euler=(Vector((0,.06,.73))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.cycles.samples=48;scene.render.resolution_x=1500;scene.render.resolution_y=1300;scene.render.resolution_percentage=100
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
for im in bpy.data.images:
    if im.source=='FILE' or im==atlas:
        try:im.pack()
        except:pass
for screen in bpy.data.screens:
    for ar in screen.areas:
        if ar.type=='VIEW_3D':ar.spaces.active.region_3d.view_perspective='CAMERA';ar.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'RabbitBike.blend'))
coords=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
manifest={'blender':bpy.app.version_string,'source_reference':'REF/rabbit_bike.png','asset_objects':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),'dimensions_m':[max(v[i] for v in coords)-min(v[i] for v in coords) for i in range(3)],'wheel_layout':'Two front wheels, one larger centered rear wheel','uv':'Unique global 0-1; analytical tread charts; averaged area scale; no mirrored/stacked charts','pack_margin_uv':.002,'pack_margin_pixels_setting':8.192,'bake_margin_pixels':8,'albedo':'textures/RabbitBike_BaseColor_4096.png','original_image_count':3,'source_uv_repetition_before_unique_bake':4,'scope':'Static exterior, deployed wheels, decorative ears, no animation rig','elapsed_build_seconds':time.time()-START}
manifest['source_uv_repetition_before_unique_bake']={'ivory':4,'orange':4,'rubber_and_saddle':8}
manifest['rubber_generated_color_mix']=.12
manifest['uv']='Unique global 0-1; analytical tires and thin shell lofts; projected central frame/individual components; area-normalized charts'
(ROOT/'validation'/'build_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
log('Render hero');scene.render.filepath=str(ROOT/'renders'/'hero.png');bpy.ops.render.render(write_still=True)
log('BUILD_DONE')
