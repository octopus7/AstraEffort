"""Private, deterministic Blender asset build. Run with Blender 4.5 background."""
import bpy, bmesh, math, json, time, os
from mathutils import Vector
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parent
NAME = 'mountain_observatory'
START = '2026-10-23T12:15:41+00:00'
T0 = time.perf_counter()
def utc(): return datetime.now(timezone.utc).isoformat()
def record(path, data): (ROOT/path).write_text(json.dumps(data, indent=2), encoding='utf-8')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
asset = bpy.data.collections.new('ASSET')
studio = bpy.data.collections.new('STUDIO')
bpy.context.scene.collection.children.link(asset)
bpy.context.scene.collection.children.link(studio)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0

def mat(name, color, rough=.5, metal=0, emission=None):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Metallic'].default_value=metal
    if emission:
        bs.inputs['Emission Color'].default_value=(*color,1)
        bs.inputs['Emission Strength'].default_value=emission
    return m
stone=mat('Limestone | warm ivory',(0.63,.595,.515),.72)
stone_light=mat('Limestone | cut edge',(.76,.715,.62),.67)
stone_alt=mat('Limestone | subtle alternate block',(.59,.562,.492),.76)
foundation=mat('Foundation | soft warm gray',(.40,.405,.375),.8)
foundation_alt=mat('Foundation | alternating ashlar',(.43,.433,.40),.8)
mortar=mat('Masonry recessed joint',(.395,.395,.352),.88)
sage=mat('Dome | satin sage enamel',(.205,.31,.285),.44,.32)
sage_light=mat('Roof and dome | sage edge',(.275,.375,.338),.46,.25)
sage_seam=mat('Dome | dark panel joint',(.09,.155,.142),.6,.25)
ivory=mat('Shutter rails | ivory enamel',(.82,.785,.683),.4,.18)
steel=mat('Hardware | graphite iron',(.075,.099,.092),.42,.68)
steel_mid=mat('Hardware | softened brushed steel',(.20,.245,.227),.38,.72)
brass=mat('Hardware | muted amber brass',(.61,.305,.095),.33,.68)
rubber=mat('Gaskets | charcoal rubber',(.032,.043,.038),.73,.03)
interior=mat('Dome interior | dark backing',(.048,.065,.06),.77,.1)
door_mat=mat('Door | deep sage enamel',(.16,.23,.205),.52,.28)
glass=mat('Windows | amber smoked glazing',(.13,.116,.075),.2,.34)
glass_lit=mat('Windows | warm interior reflection',(.47,.287,.105),.27,.15,.12)
lens=mat('Optics | deep blue coated lens',(.022,.065,.083),.1,.6)
lamp=mat('Entry lamp | warm diffuser',(1.0,.57,.16),.33,.05,2.1)
floor_mat=mat('STUDIO | warm pale gray',(.61,.60,.565),.83)

def put(obj, name, material=None, collection=asset):
    obj.name=name
    for c in list(obj.users_collection): c.objects.unlink(obj)
    collection.objects.link(obj)
    if material: obj.data.materials.append(material)
    return obj
def clean(obj):
    bm=bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data); bm.free(); obj.data.update()
def bevel(obj, width=.02, segments=3):
    if width:
        mod=obj.modifiers.new('Physical rounded edges','BEVEL')
        mod.width=width; mod.segments=segments; mod.limit_method='ANGLE'; mod.angle_limit=.35
    mod=obj.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL')
    mod.keep_sharp=True; mod.weight=35
    return obj
def mesh(name, verts, faces, material, edge=0, smooth=False):
    me=bpy.data.meshes.new(name+' mesh'); me.from_pydata(verts, [], faces); me.update()
    o=bpy.data.objects.new(name,me); asset.objects.link(o); me.materials.append(material)
    clean(o)
    for p in me.polygons: p.use_smooth=smooth
    if edge: bevel(o,edge)
    return o
def apply_mods(o):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    for md in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=md.name)
def cube(name, loc, dims, material, edge=.02, rot=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o=put(bpy.context.object,name,material); o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    clean(o); bevel(o,min(edge,min(dims)*.39)); o.rotation_euler[2]=rot
    for p in o.data.polygons: p.use_smooth=True
    return o
def cyl(name, loc, rad, depth, material, direction=(0,0,1), vertices=48, edge=.012):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=rad, depth=depth, location=loc)
    o=put(bpy.context.object,name,material)
    o.rotation_euler=Vector(direction).to_track_quat('Z','Y').to_euler()
    clean(o)
    for p in o.data.polygons: p.use_smooth=True
    if edge: bevel(o,min(edge,depth*.35,rad*.35))
    return o
def tube(name, points, rad, material, res=3):
    cu=bpy.data.curves.new(name+' path','CURVE'); cu.dimensions='3D'; cu.resolution_u=1
    cu.bevel_depth=rad; cu.bevel_resolution=res; cu.use_fill_caps=True
    sp=cu.splines.new('POLY'); sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points): p.co=(*co,1)
    ob=bpy.data.objects.new(name,cu); asset.objects.link(ob); cu.materials.append(material)
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active=ob
    bpy.ops.object.convert(target='MESH'); ob=bpy.context.object; clean(ob)
    for p in ob.data.polygons: p.use_smooth=True
    return ob
def ring(name, center, ro, ri, height, material, n=96, edge=.012, direction=(0,0,1)):
    vs=[]
    for z,r in [(-height/2,ro),(height/2,ro),(-height/2,ri),(height/2,ri)]:
        vs += [(r*math.cos(2*math.pi*i/n),r*math.sin(2*math.pi*i/n),z) for i in range(n)]
    fs=[]
    for i in range(n):
        j=(i+1)%n
        fs.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(n+i,n+j,3*n+j,3*n+i),(i,2*n+i,2*n+j,j)])
    o=mesh(name,vs,fs,material,edge,True); o.location=center
    o.rotation_euler=Vector(direction).to_track_quat('Z','Y').to_euler()
    return o
def annular_sector(name, ro, ri, a0,a1,z0,z1,material,n=12,edge=.012):
    vs=[]
    for z,r in [(z0,ro),(z1,ro),(z0,ri),(z1,ri)]:
        vs.extend([(r*math.sin(a0+(a1-a0)*i/n),-r*math.cos(a0+(a1-a0)*i/n),z) for i in range(n+1)])
    m=n+1; fs=[]
    for i in range(n): fs.extend([(i,i+1,m+i+1,m+i),(2*m+i,3*m+i,3*m+i+1,2*m+i+1),(m+i,m+i+1,3*m+i+1,3*m+i),(i,2*m+i,2*m+i+1,i+1)])
    fs.extend([(0,m,3*m,2*m),(n,2*m+n,3*m+n,m+n)])
    return mesh(name,vs,fs,material,edge,True)
def round_outline(w,h,r,n=8):
    out=[]
    for cx,cy,a in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for i in range(n+1):
            t=math.radians(a+i*90/n); out.append((cx+r*math.cos(t),cy+r*math.sin(t)))
    return out
def prism(name,outline,z0,z1,material,edge=.02,loc=(0,0,0)):
    n=len(outline); vs=[(x,y,z) for z in(z0,z1) for x,y in outline]
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o=mesh(name,vs,fs,material,edge,True); o.location=loc; return o
def round_prism(name,loc,w,d,h,r,material,edge=.02):
    return prism(name,round_outline(w,d,r),-h/2,h/2,material,edge,loc)
def rect_frame(name, center, w,h, border,depth,corner,material,angle=0):
    outer=round_outline(w,h,corner,5); inner=round_outline(w-2*border,h-2*border,max(.018,corner-border),5)
    n=len(outer); vs=[]
    for y,loop in [(-depth/2,outer),(depth/2,outer),(-depth/2,inner),(depth/2,inner)]:
        vs += [(x,y,z) for x,z in loop]
    fs=[]
    for i in range(n):
        j=(i+1)%n
        fs.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
    o=mesh(name,vs,fs,material,.012,True); o.location=center; o.rotation_euler[2]=angle; return o
def boolean_recess(body, name, loc, dims,angle=0,edge=.035):
    cut=cube(name+' temporary cutter',loc,dims,stone,edge,angle); apply_mods(cut)
    bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); bpy.context.view_layer.objects.active=body
    md=body.modifiers.new(name+' actual opening','BOOLEAN'); md.operation='DIFFERENCE'; md.solver='EXACT'; md.object=cut
    while body.modifiers.find(md.name)>0: bpy.ops.object.modifier_move_up(modifier=md.name)
    bpy.ops.object.modifier_apply(modifier=md.name); bpy.data.objects.remove(cut,do_unlink=True)
def polar(r,a,z): return (r*math.sin(a),-r*math.cos(a),z)
def transformed(center,angle,x,y,z):
    return (center[0]+x*math.cos(angle)-y*math.sin(angle),center[1]+x*math.sin(angle)+y*math.cos(angle),center[2]+z)
def window(name, body, angle, radius,z,w=.48,h=1.02):
    boolean_recess(body,name,polar(radius-.06,angle,z),(w,.78,h),angle,.035)
    rect_frame(name+' dressed stone reveal',polar(radius+.018,angle,z),w+.20,h+.20,.105,.15,.09,stone_light,angle)
    rect_frame(name+' inset bronze sash',polar(radius-.135,angle,z),w-.035,h-.035,.044,.055,.045,steel,angle)
    cube(name+' recessed glazing',polar(radius-.175,angle,z),(w-.13,.024,h-.13),glass,.012,angle)
    center=polar(radius-.157,angle,z)
    cube(name+' warm pane reflection',transformed(center,angle,-w*.19,0,.02),(w*.15,.008,h*.73),glass_lit,.003,angle)
    cube(name+' projecting stone sill',polar(radius+.04,angle,z-h/2-.07),(w+.27,.23,.09),stone_light,.025,angle)

# Circular foundation and a coherent, hollow masonry drum.
cyl('Foundation continuous lower footing',(0,0,.06),2.65,.12,foundation,vertices=128,edge=.025)
for i in range(24):
    a=2*math.pi*i/24
    annular_sector('Foundation ashlar %02d'%i,2.63,2.18,a+.003,a+2*math.pi/24-.003,.12,.43,foundation if i%3 else foundation_alt,8,.015)
ring('Circular paved perimeter cap',(0,0,.475),2.66,2.16,.10,stone_light,128,.02)
wall=ring('Rotunda masonry | true hollow wall',(0,0,1.845),2.27,2.025,2.63,stone,144,0)
baseband=ring('Rotunda lower gray plinth',(0,0,.735),2.31,2.02,.42,foundation,144,0)
boolean_recess(wall,'Main entry',(0,-2.17,1.62),(1.025,.88,2.12),0,.12)
boolean_recess(baseband,'Main entry',(0,-2.17,1.62),(1.025,.88,2.12),0,.12)
angles=[-.85,-1.65,-2.45,math.pi,2.40,1.62,.88]
for j,a in enumerate(angles):
    # Annex physically occupies the right side; do not bury windows inside it.
    if a in [1.62,.88]: continue
    window('Rotunda window %02d'%j,wall,a,2.27,1.88,.46,1.00)
bevel(wall,.017); bevel(baseband,.018)
ring('Top dressed limestone cornice',(0,0,3.085),2.38,2.015,.19,stone_light,144,.026)
ring('Cornice lower shadow reveal',(0,0,2.965),2.29,2.02,.042,mortar,128,.007)
cyl('Observatory interior upper floor',(0,0,3.155),2.14,.10,interior,vertices=96,edge=.01)

# Mortar courses, trimmed away from real openings and annex contact area.
def safe_joint(a,z):
    aa=(a+math.pi)%(2*math.pi)-math.pi
    if abs(aa)<.31 and z<2.79: return False
    if .55<aa<2.1 and z<2.78: return False
    for wa in angles[:4]+[angles[4]]:
        diff=abs((aa-wa+math.pi)%(2*math.pi)-math.pi)
        if diff<.18 and 1.24<z<2.52: return False
    return True
for k,z in enumerate([1.02,1.57,2.18,2.72]):
    samples=[(-math.pi+2*math.pi*i/360) for i in range(361)]
    run=[]
    for a in samples:
        if safe_joint(a,z): run.append(polar(2.273,a,z))
        else:
            if len(run)>1: tube('Masonry horizontal joint %d-%d'%(k,len(asset.objects)),run,.004,mortar,1)
            run=[]
    if len(run)>1: tube('Masonry horizontal joint end %d'%k,run,.004,mortar,1)
for row,(lo,hi) in enumerate([(1.03,1.56),(1.58,2.17),(2.19,2.71),(2.73,2.94)]):
    for i in range(18):
        a=2*math.pi*(i+(row%2)*.5)/18
        if safe_joint(a,(lo+hi)/2): tube('Masonry vertical joint %d %02d'%(row,i),[polar(2.274,a,lo),polar(2.274,a,hi)],.004,mortar,1)

# Deep entry frame and recessed leaf.
rect_frame('Entry thick rounded limestone surround',(0,-2.32,1.63),1.52,2.30,.19,.23,.29,stone_light)
rect_frame('Entry inner charcoal gasket',(0,-2.215,1.61),1.105,1.98,.055,.07,.14,rubber)
cube('Entry recessed sage door',(0,-2.15,1.61),(.98,.10,1.86),door_mat,.075)
rect_frame('Door recessed central panel frame',(0,-2.21,1.61),.82,1.68,.027,.018,.09,sage_seam)
cube('Door kick plate',(0,-2.22,.78),(.79,.025,.12),steel_mid,.012)
cube('Door vertical brass pull',(.31,-2.297,1.62),(.045,.045,.52),brass,.018)
for z in [1.40,1.83]: cyl('Door pull standoff %.2f'%z,(.31,-2.25,z),.024,.085,brass,(0,1,0),24,.008)
for z in [1.04,2.12]: cube('Door hinge %.2f'%z,(-.46,-2.22,z),(.035,.04,.16),steel_mid,.01)
cube('Entry lamp bronze housing',(0,-2.46,2.62),(.48,.10,.105),steel,.03)
cube('Entry warm illuminated diffuser',(0,-2.521,2.62),(.37,.015,.042),lamp,.01)

# Three broad, genuinely curved stone steps.
for idx,(r,w,z0,z1) in enumerate([(2.40,2.92,0,.18),(2.18,2.69,.18,.36),(1.96,2.45,.36,.54)]):
    aa=math.asin(w/(2*r)); outline=[(-w/2,-2.04),(w/2,-2.04)]
    outline += [(r*math.sin(a),-1-r*math.cos(a)) for a in [aa-2*aa*i/40 for i in range(41)]]
    prism('Entry curved stair %d'%(idx+1),outline,z0,z1,stone_light,.028)
for side in [-1,1]:
    pts=[(side*1.22,-3.02,1.08),(side*1.14,-2.70,1.27),(side*1.06,-2.35,1.48),(side*1.06,-2.13,1.48)]
    tube('Entry handrail %s'%side,pts,.033,steel_mid,4)
    tube('Entry intermediate rail %s'%side,[(x,y,z-.40) for x,y,z in pts],.018,steel_mid,3)
    for k,(x,y,z) in enumerate(pts[:3]):
        bottom=[.18,.36,.54][k]
        tube('Stair post %s %s'%(side,k),[(x,y,bottom+.012),(x,y,z)],.025,steel_mid,3)
        cyl('Stair post shoe %s %s'%(side,k),(x,y,bottom+.018),.060,.036,steel,vertices=32,edge=.008)

# Compact attached annex: separate rounded architecture, cut recesses, service terrace.
ac=(2.82,.10)
round_prism('Annex foundation footing',(ac[0],ac[1],.06),3.12,3.02,.12,.66,foundation,.025)
round_prism('Annex terrace plinth',(ac[0],ac[1],.275),3.08,2.98,.35,.64,foundation_alt,.025)
round_prism('Annex terrace pale coping',(ac[0],ac[1],.49),3.14,3.04,.10,.67,stone_light,.025)
annex=round_prism('Annex solid rounded masonry',(ac[0],ac[1],1.565),2.54,2.58,2.05,.39,stone,.0)
for j,x in enumerate([2.48,3.30]):
    y=ac[1]-1.29
    boolean_recess(annex,'Annex front recess %d'%j,(x,y+.10,1.68),(.49,.54,1.03),0,.035)
    rect_frame('Annex front stone reveal %d'%j,(x,y-.018,1.68),.67,1.21,.10,.13,.065,stone_light)
    rect_frame('Annex front recessed sash %d'%j,(x,y+.145,1.68),.45,.99,.04,.04,.04,steel)
    cube('Annex front glazing %d'%j,(x,y+.171,1.68),(.37,.018,.90),glass,.005)
    cube('Annex reflected amber vertical %d'%j,(x-.10,y+.157,1.70),(.075,.008,.70),glass_lit,.002)
    cube('Annex window sill %d'%j,(x,y-.04,1.10),(.72,.22,.09),stone_light,.022)
rear_y=ac[1]+1.29
boolean_recess(annex,'Rear service door',(2.75,rear_y-.09,1.38),(.80,.56,1.69),0,.07)
rect_frame('Annex rear doorway stone reveal',(2.75,rear_y+.012,1.38),.98,1.87,.10,.15,.12,stone_light,math.pi)
cube('Annex rear inset service leaf',(2.75,rear_y-.18,1.38),(.73,.075,1.61),door_mat,.04)
cube('Rear service door brass handle',(2.48,rear_y-.109,1.40),(.035,.055,.26),brass,.013)
bevel(annex,.028)
round_prism('Annex roof shadow gasket',(ac[0],ac[1],2.615),2.65,2.69,.065,.43,rubber,.012)
round_prism('Annex rounded sage roof fascia',(ac[0],ac[1],2.755),2.77,2.81,.23,.48,sage_light,.045)
round_prism('Annex shallow raised roof',(ac[0],ac[1],2.89),2.57,2.61,.06,.43,sage,.02)
round_prism('Roof ventilation pedestal',(2.91,.35,2.955),.72,.64,.10,.07,steel_mid,.025)
round_prism('Roof extractor cap',(2.91,.35,3.105),.61,.53,.22,.065,foundation,.022)
for j in range(4): cube('Roof extractor front slot %d'%j,(2.91,.073,3.04+j*.039),(.43,.018,.013),steel,.003)
cube('Roof service access hinge',(3.53,.52,2.94),(.18,.11,.035),steel_mid,.009)
# Annex side vent faces +X: local frame turned 90 degrees.
vent_x=ac[0]+1.27
boolean_recess(annex,'Side ventilation recess',(vent_x-.06,.30,1.72),(.45,1.08,.90),0,.035)
rect_frame('Annex side vent dressed frame',(vent_x+.012,.30,1.72),1.21,1.03,.09,.12,.065,stone_light,math.pi/2)
cube('Annex side vent black recessed cavity',(vent_x-.14,.30,1.72),(.03,1.05,.86),rubber,.01)
for j in range(9):
    o=cube('Annex side ventilation louver %02d'%j,(vent_x-.035,.30,1.35+j*.092),(.16,.98,.044),steel_mid,.012)
    o.rotation_euler[1]=math.radians(-20)
# Small utility hardware and visibly attached pipework.
cube('Rear junction cabinet',(3.72,1.43,1.13),(.43,.19,.66),steel_mid,.04)
rect_frame('Rear junction cabinet inset panel',(3.72,1.538,1.13),.34,.56,.025,.018,.045,door_mat,math.pi)
cyl('Rear cabinet latch',(3.83,1.555,1.13),.025,.024,brass,(0,1,0),24,.006)
tube('Annex exterior utility conduit',[(3.79,1.42,.55),(3.79,1.42,2.35),(3.73,1.42,2.44),(3.55,1.42,2.44)],.025,steel_mid,3)
tube('Annex lower drainpipe',[(1.94,-1.22,2.47),(1.94,-1.22,.83),(2.06,-1.22,.71),(2.44,-1.22,.71),(2.51,-1.22,.63),(2.51,-1.22,.10)],.033,steel_mid,4)
for x,y,z in [(1.94,-1.22,2.20),(1.94,-1.22,1.19),(2.51,-1.22,.31),(3.79,1.42,1.56),(3.79,1.42,2.15)]:
    cube('Pipe fixing saddle %s'%str((x,z)),(x,y+(.025 if y<0 else -.025),z),(.095,.08,.055),steel,.012)
# Terrace rounded corner rail, set within the coping.
rail_xy=[(4.19,-.78),(4.19,.95)]
rail_xy += [(3.80+.39*math.cos(a),.95+.39*math.sin(a)) for a in [math.pi*i/16 for i in range(1,9)]]
rail_xy += [(3.21,1.34)]
for z,rad in [(1.34,.029),(.98,.019)]: tube('Annex terrace horizontal rail %.2f'%z,[(x,y,z) for x,y in rail_xy],rad,steel_mid,3)
for k,(x,y) in enumerate([(4.19,-.78),(4.19,-.15),(4.19,.49),(4.14,1.12),(3.80,1.34),(3.21,1.34)]):
    tube('Annex terrace upright %d'%k,[(x,y,.54),(x,y,1.34)],.024,steel_mid,3)
    cyl('Annex terrace post flange %d'%k,(x,y,.56),.052,.035,steel,vertices=24,edge=.008)
for i in range(14):
    a=2.4+(5.4-2.4)*i/13
    if i<13: tube('Rear rotunda low utility pipe %02d'%i,[polar(2.335,a+(5.4-2.4)/13*j/5,.74) for j in range(6)],.023,steel_mid,3)
    if i%3==0: cube('Rear rotunda pipe bracket %02d'%i,polar(2.32,a,.74),(.095,.07,.085),steel,.012,a)

# Bearing system and dynamic-looking (static) roller hardware.
ring('Dome lower rotation race',(0,0,3.245),2.405,2.05,.13,steel,144,.018)
ring('Dome brass bearing track',(0,0,3.335),2.372,2.06,.045,brass,144,.006)
ring('Dome upper bearing shadow',(0,0,3.397),2.382,2.045,.072,rubber,144,.006)
ring('Dome sage flared equatorial rim',(0,0,3.515),2.445,2.03,.19,sage_light,144,.035)
ring('Dome equator top seal',(0,0,3.612),2.31,2.04,.036,rubber,144,.006)
for i in range(16):
    a=2*math.pi*(i+.5)/16; p=polar(2.39,a,3.34)
    cube('Bearing brass keeper %02d'%i,p,(.105,.055,.11),brass,.013,a)
    cyl('Bearing keeper steel bolt %02d'%i,polar(2.425,a,3.34),.020,.016,steel,(math.sin(a),-math.cos(a),0),16,.004)

# Hemisphere shells with a physically absent front strip. No black overlay.
R=2.285; Z=3.62; GAP=.555
def dome_side(sign):
    nx=27; nt=64; beta0=math.asin(GAP/R); vs=[]
    for i in range(nx):
        b=beta0+(math.pi/2-beta0)*i/nx; x=sign*R*math.sin(b); rho=R*math.cos(b)
        for j in range(nt+1):
            t=math.pi*j/nt; vs.append((x,-rho*math.cos(t),Z+rho*math.sin(t)))
    tip=len(vs); vs.append((sign*R,0,Z)); fs=[]
    for i in range(nx-1):
        for j in range(nt):
            a=i*(nt+1)+j; fs.append((a,a+1,a+1+nt+1,a+nt+1))
    for j in range(nt): fs.append(((nx-1)*(nt+1)+j,(nx-1)*(nt+1)+j+1,tip))
    o=mesh('Dome %s continuous shell'%('east' if sign>0 else 'west'),vs,fs,sage,0,True)
    o.data.materials.append(interior)
    # Guarantee outward normals before shell thickness is applied.
    bm=bmesh.new(); bm.from_mesh(o.data)
    for f in bm.faces:
        c=f.calc_center_median()-Vector((0,0,Z))
        if f.normal.dot(c)<0: f.normal_flip()
    bm.to_mesh(o.data); bm.free()
    md=o.modifiers.new('Real 65 mm shell thickness','SOLIDIFY'); md.thickness=.065; md.offset=-1; md.material_offset=1; md.material_offset_rim=1
    bevel(o,.009,2)
    return o
dome_side(-1); dome_side(1)
vs=[]; fs=[]; nx=12; nt=32
for i in range(nx+1):
    x=-GAP+2*GAP*i/nx; rho=math.sqrt(R*R-x*x)
    for j in range(nt+1):
        t=math.pi/2+math.pi/2*j/nt; vs.append((x,-rho*math.cos(t),Z+rho*math.sin(t)))
for i in range(nx):
    for j in range(nt):
        a=i*(nt+1)+j; fs.append((a,a+1,a+1+nt+1,a+nt+1))
back=mesh('Dome closed rear shutter panel',vs,fs,sage,0,True); back.data.materials.append(interior)
bm=bmesh.new(); bm.from_mesh(back.data)
for f in bm.faces:
    if f.normal.dot(f.calc_center_median()-Vector((0,0,Z)))<0: f.normal_flip()
bm.to_mesh(back.data); bm.free()
md=back.modifiers.new('Rear shutter actual thickness','SOLIDIFY'); md.thickness=.065; md.offset=-1; md.material_offset=1
bevel(back,.01,2)

def curved_rail(name,xc,width,rin,rout,material):
    n=80; vs=[]
    for x,r in [(xc-width/2,rin),(xc+width/2,rin),(xc+width/2,rout),(xc-width/2,rout)]:
        rho=math.sqrt(r*r-x*x)
        for i in range(n+1):
            t=math.pi*i/n; vs.append((x,-rho*math.cos(t),Z+rho*math.sin(t)))
    m=n+1; fs=[]
    for k in range(4):
        kk=(k+1)%4
        for i in range(n): fs.append((k*m+i,k*m+i+1,kk*m+i+1,kk*m+i))
    fs.extend([(0,m,2*m,3*m),(n,3*m+n,2*m+n,m+n)])
    return mesh(name,vs,fs,material,.017,True)
for side in [-1,1]:
    curved_rail('Shutter dark recessed inner track %s'%side,side*.552,.075,R-.025,R+.038,steel)
    curved_rail('Shutter thick ivory curved rail %s'%side,side*.685,.22,R+.025,R+.163,ivory)
    curved_rail('Shutter fine rail edge joint %s'%side,side*.775,.013,R+.165,R+.174,stone_alt)
    for end in [-1,1]:
        yy=end*math.sqrt(R*R-.685**2)
        cube('Shutter drive saddle %s %s'%(side,end),(side*.685,yy,3.694),(.39,.32,.25),sage_light,.045)
        cyl('Shutter drive roller %s %s'%(side,end),(side*.685,yy+end*.055,3.795),.195,.27,steel_mid,(1,0,0),48,.022)
        cyl('Shutter drive amber flange %s %s'%(side,end),(side*.685-side*.10,yy+end*.055,3.795),.197,.025,brass,(1,0,0),48,.006)
        cyl('Shutter drive axle cap %s %s'%(side,end),(side*.685+side*.146,yy+end*.055,3.795),.065,.025,steel,(1,0,0),32,.008)
# Thin, actual geometric panel seams. Surface segments stop at the open slit.
for k,h in enumerate([.66,1.36,1.94]):
    rr=math.sqrt((R+.006)**2-h*h); run=[]
    for j in range(361):
        a=2*math.pi*j/360; x=rr*math.sin(a); y=-rr*math.cos(a)
        if abs(x)>.82 or y>0:
            run.append((x,y,Z+h))
        else:
            if len(run)>1: tube('Dome horizontal seam %d %d'%(k,j),run,.006,sage_seam,2)
            run=[]
    if len(run)>1: tube('Dome horizontal seam end %d'%k,run,.006,sage_seam,2)
for j,a in enumerate([.52,1.00,1.55,2.10,2.64,3.64,4.18,4.73,5.28,5.76]):
    pts=[]
    for i in range(65):
        t=math.pi/2*i/64; x=(R+.006)*math.cos(t)*math.sin(a); y=-(R+.006)*math.cos(t)*math.cos(a)
        if abs(x)>.82: pts.append((x,y,Z+(R+.006)*math.sin(t)))
    if len(pts)>1: tube('Dome meridian seam %02d'%j,pts,.006,sage_seam,2)
# Back panel has a quiet center joint and top retaining strip, while front stays clear.
tube('Rear shutter center seam',[(0,-(R+.008)*math.cos(t),Z+(R+.008)*math.sin(t)) for t in [math.pi/2+(math.pi/2)*i/48 for i in range(49)]],.006,sage_seam,2)
curved_rail('Inner dark curved rear stiffener',0,.055,R-.105,R-.060,interior)
# Only the front half of this center stiffener would obstruct the slit, so replace
# its front-facing geometry by deleting it; the rear panel already carries structure.
ob=bpy.data.objects.get('Inner dark curved rear stiffener'); bpy.data.objects.remove(ob,do_unlink=True)
cube('Open slit lower cross-sill',(0,-2.17,3.66),(1.03,.18,.10),sage_light,.025)
cube('Open slit upper rear lintel',(0,.018,Z+R-.055),(1.05,.13,.09),steel,.025)

# Short optical telescope, two trunnion bearings and a true fork mount.
cyl('Telescope pedestal foot',(0,-.48,3.285),.44,.15,steel_mid,vertices=64,edge=.025)
cyl('Telescope pedestal neck',(0,-.48,3.53),.24,.39,steel,vertices=48,edge=.025)
cyl('Telescope azimuth turntable',(0,-.48,3.745),.44,.10,steel_mid,vertices=64,edge=.025)
cyl('Telescope azimuth brass index ring',(0,-.48,3.805),.405,.025,brass,vertices=64,edge=.005)
pivot=Vector((0,-.55,4.18)); axis=Vector((0,-.66,.751265)).normalized()
for side in [-1,1]:
    tube('Telescope gimbal fork arm %s'%side,[(side*.38,-.48,3.80),(side*.39,-.50,3.92),(side*.39,-.55,4.18)],.071,steel_mid,4)
    cyl('Telescope trunnion outer housing %s'%side,(side*.39,-.55,4.18),.196,.13,steel,(1,0,0),48,.018)
    cyl('Telescope trunnion face %s'%side,(side*.465,-.55,4.18),.145,.045,steel_mid,(1,0,0),48,.012)
    cyl('Telescope amber trunnion hub %s'%side,(side*.492,-.55,4.18),.089,.025,brass,(1,0,0),40,.010)
    for k in range(4):
        a=math.pi/2*k; cyl('Trunnion bolt %s %s'%(side,k),(side*.492,-.55+.116*math.cos(a),4.18+.116*math.sin(a)),.013,.012,steel,(1,0,0),12,.002)
def along(s): return tuple(pivot+axis*s)
ring('Optical telescope ivory primary tube',along(.43),.305,.238,1.18,ivory,64,.018,axis)
cyl('Optical telescope rear housing',along(-.18),.29,.15,steel_mid,axis,64,.025)
cyl('Telescope rear focus drum',along(-.30),.16,.14,steel,axis,48,.015)
cyl('Telescope tube lower brass band',along(-.095),.313,.030,brass,axis,64,.004)
ring('Telescope forward structural collar',along(.94),.337,.253,.115,steel_mid,64,.012,axis)
ring('Telescope open optical rim',along(1.025),.333,.262,.075,ivory,64,.009,axis)
ring('Telescope recessed black optical baffle',along(.99),.262,.230,.10,rubber,64,.006,axis)
cyl('Telescope deeply inset coated lens',along(.947),.229,.015,lens,axis,64,.003)
# Narrow optical highlight ring inside the lip, real geometry rather than a painted patch.
ring('Telescope lens retaining ring',along(.958),.237,.225,.011,steel,64,.002,axis)
cube('Telescope side finder foot',(.27,-.78,4.60),(.13,.14,.12),steel,.018)
finder_origin=Vector((.31,-.80,4.64))
cyl('Telescope compact finder scope',tuple(finder_origin+axis*.16),.056,.41,steel_mid,axis,32,.008)
cyl('Finder recessed objective',tuple(finder_origin+axis*.372),.046,.012,lens,axis,32,.003)

# Bring the whole mounted instrument forward inside the real open slit so both
# barrel and fork are legible from the approved front three-quarter direction.
for o in asset.objects:
    if 'telescope' in o.name.lower() or 'finder' in o.name.lower() or o.name.startswith('Trunnion bolt'):
        o.location.y-=.35

# Geometry bake and real component UV layouts. Exports contain only ASSET.
print('ASSET geometry objects before bake',len(asset.objects),flush=True)
for idx,o in enumerate(list(asset.objects)):
    if o.type!='MESH': continue
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    apply_mods(o); clean(o)
    if not o.data.uv_layers: o.data.uv_layers.new(name='UVMap')
    o.data.uv_layers.active.name='UVMap'
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.018,area_weight=.0,correct_aspect=True,scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    md=o.modifiers.new('Baked deterministic export triangulation','TRIANGULATE'); md.quad_method='BEAUTY'; md.ngon_method='BEAUTY'
    bpy.ops.object.modifier_apply(modifier=md.name)
    o['component_uvs']='Independent smart-projected component islands; 0.018 margin. Solid PBR, no bitmap textures.'
    if idx%60==0: print('Baked / UV',idx,flush=True)

asset['orientation']='Meters; Z up; front -Y; foundation bottom Z=0'
asset['reference']='REF/Set02/mountain_observatory.png; own approved reference only'
asset['construction']='Actual open dome slit and shell thickness; separate closed back panel; inset openings; static telescope and bearing hardware.'

# Asset-only export before the studio is introduced.
bpy.ops.object.select_all(action='DESELECT')
for o in asset.objects: o.select_set(True)
bpy.context.view_layer.objects.active=next(iter(asset.objects))
bpy.ops.export_scene.gltf(filepath=str(ROOT/(NAME+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_yup=True,export_cameras=False,export_lights=False)
bpy.ops.export_scene.fbx(filepath=str(ROOT/(NAME+'.fbx')),use_selection=True,object_types={'MESH'},use_mesh_modifiers=True,mesh_smooth_type='FACE',use_triangles=True,add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y',apply_unit_scale=True,path_mode='AUTO')

# Private studio and two actual Cycles renders.
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-.045))
put(bpy.context.object,'STUDIO floor',floor_mat,studio)
world=bpy.data.worlds.new('Warm gray studio world'); scene.world=world; world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.62,.64,.61,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.32
def area(name,loc,energy,size,color,target=(.5,0,2.7)):
    data=bpy.data.lights.new(name,'AREA'); data.energy=energy; data.shape='DISK'; data.size=size; data.color=color
    o=bpy.data.objects.new(name,data); studio.objects.link(o); o.location=loc; o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('STUDIO broad warm key',(1,-9,11),1850,7.0,(1,.89,.74))
area('STUDIO soft left fill',(-7,-3,7),1200,6.0,(.77,.86,1))
area('STUDIO high rear rim',(5,6,10),2100,6.0,(1,.96,.85))
camdata=bpy.data.cameras.new('STUDIO camera'); cam=bpy.data.objects.new('STUDIO camera',camdata); studio.objects.link(cam); scene.camera=cam
camdata.type='ORTHO'; camdata.ortho_scale=11.35; camdata.lens=50
scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=32
scene.cycles.use_denoising=True; scene.render.threads_mode='FIXED'; scene.render.threads=4
scene.render.resolution_x=1440; scene.render.resolution_y=1080; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'; scene.view_settings.look='AgX - Medium High Contrast'; scene.view_settings.exposure=.05
scene.render.image_settings.color_depth='8'
renders=ROOT/'renders'; renders.mkdir(exist_ok=True)
views=[('hero',(7.5,-17.0,9.5),(.75,-.10,2.82)),('rear',(10.5,15.0,9.2),(.65,0,2.83))]
captures=[]
for label,loc,target in views:
    cam.location=loc; cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(renders/(label+'.png'))
    begin=utc(); rt=time.perf_counter(); bpy.ops.render.render(write_still=True)
    captures.append({'view':label,'path':'renders/'+label+'.png','started_at_utc':begin,'finished_at_utc':utc(),'render_seconds':time.perf_counter()-rt,'camera_location_m':list(loc),'camera_target_m':list(target),'orthographic_scale_m':camdata.ortho_scale})
cam.location=views[0][1]; cam.rotation_euler=(Vector(views[0][2])-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(renders/'hero.png')
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/(NAME+'.blend')))
record('capture_manifest.json',{'asset':NAME,'reference':'D:/github/AstraEffort/REF/Set02/mountain_observatory.png','actual_scene_renders':True,'engine':'Cycles CPU','threads':4,'samples':32,'denoising':True,'resolution':[1440,1080],'color_management':{'view_transform':'AgX','look':'AgX - Medium High Contrast','exposure':.05},'background':'Warm pale gray studio','asset_front':'-Y','up':'Z','units':'meters','captures':captures})
record('build_record.json',{'asset':NAME,'recorded_work_start_utc':START,'build_finished_utc':utc(),'build_process_seconds':time.perf_counter()-T0,'asset_mesh_objects':len(asset.objects),'build_source':'build.py','exports':[NAME+'.blend',NAME+'.glb',NAME+'.fbx']})
print('BUILD_COMPLETE',utc(),flush=True)
