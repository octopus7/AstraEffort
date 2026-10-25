"""Set03 original rounded geometry authoring. Run only in private Blender CLI.

The source creates authored geometry, UV layouts, exports and two studio images.
No validation/reimport or render review is performed by this script.
"""
import bpy
import math
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parent
TAU = math.tau
KST = timezone(timedelta(hours=9))
ASSET = None
MATS = {}


def stamp():
    return datetime.now(timezone.utc).isoformat()


def material(name, color, metallic=0.0, roughness=0.5, emission=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Metallic'].default_value = metallic
    bs.inputs['Roughness'].default_value = roughness
    if emission:
        bs.inputs['Emission Color'].default_value = (*color, 1)
        bs.inputs['Emission Strength'].default_value = emission
    return m


def reset(slug):
    global ASSET, MATS
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    ASSET = bpy.data.collections.new('ASSET')
    bpy.context.scene.collection.children.link(ASSET)
    ASSET['asset_slug'] = slug
    MATS = {
        'ivory': material('Paint | Warm Ivory', (0.74, .70, .59), .18, .36),
        'sage': material('Paint | Muted Sage', (.28, .39, .29), .22, .40),
        'sage_light': material('Paint | Light Sage Trim', (.40, .51, .38), .20, .37),
        'graphite': material('Mechanism | Graphite Metal', (.09, .105, .10), .65, .35),
        'rubber': material('Rubber | Soft Charcoal', (.027, .033, .031), .0, .68),
        'steel': material('Metal | Brushed Steel', (.40, .43, .40), .75, .28),
        'orange': material('Safety | Operational Orange', (.95, .31, .035), .15, .31),
        'glass': material('Glass | Muted Blue Grey', (.13, .23, .25), .38, .16),
        'lens': material('Optics | Deep Blue Lens', (.025, .075, .095), .55, .09),
        'lamp': material('Lamp | Warm Diffuser', (1, .80, .40), .10, .22, 2),
        'red': material('Lamp | Red Tail Lens', (.54, .045, .027), .12, .23),
        'concrete': material('Masonry | Warm Cast Concrete', (.46, .46, .42), .0, .80),
        'interior': material('Interior | Pale Warm Wall', (.56, .56, .49), .0, .72),
        'bristle': material('Brush | Sage Bristles', (.23, .30, .17), .0, .77),
    }
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 1
    bpy.context.preferences.filepaths.save_version = 0


def link_asset(obj, mat):
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    ASSET.objects.link(obj)
    obj.data.materials.append(MATS[mat])
    obj['role'] = 'editable_asset_component'
    return obj


def bevel(obj, amount=.04, segments=3):
    if amount:
        mod = obj.modifiers.new('Soft manufactured edges', 'BEVEL')
        mod.width = amount
        mod.segments = segments
    n = obj.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
    n.keep_sharp = True
    return obj


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def box_uv(obj):
    """Six separate, padded planar islands sized to the authored box faces."""
    mesh = obj.data
    uv = mesh.uv_layers.active or mesh.uv_layers.new(name='UVMap')
    maxdim = max(obj.dimensions)
    for face in mesh.polygons:
        n = face.normal
        axis = max(range(3), key=lambda i: abs(n[i]))
        u, v = [i for i in range(3) if i != axis]
        slot = axis * 2 + (1 if n[axis] < 0 else 0)
        cellx, celly = slot % 3, slot // 3
        for li in face.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv = ((cellx + .5 + .88*co[u]/maxdim)/3,
                              (celly + .5 + .88*co[v]/maxdim)/2)
    obj['uv_authoring'] = 'Six padded planar face islands in local metric proportions'


def box(name, loc, dims, mat='ivory', edge=.04, rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    box_uv(o)
    if rotation:
        o.rotation_euler = rotation
    link_asset(o, mat)
    bevel(o, min(edge, min(dims)*.38))
    return o


def cyl(name, loc, radius, depth, mat='graphite', axis=(0,0,1), edge=.015, vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                       end_fill_type='NGON', calc_uvs=True, location=loc)
    o = bpy.context.object
    o.name = name
    o.rotation_euler = Vector(axis).to_track_quat('Z','Y').to_euler()
    link_asset(o, mat)
    smooth(o)
    bevel(o, min(edge, depth*.2, radius*.3))
    o['uv_authoring'] = 'Primitive cylindrical side strip and independent cap islands'
    return o


def rod(name, a, b, radius, mat='graphite', edge=.01, vertices=16):
    av,bv=Vector(a),Vector(b)
    return cyl(name,(av+bv)*.5,radius,(bv-av).length,mat,bv-av,edge,vertices)


def sphere(name, loc, scale, mat='sage', segments=32, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1,calc_uvs=True,location=loc)
    o=bpy.context.object
    o.name=name
    o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    link_asset(o,mat)
    smooth(o)
    o['uv_authoring']='Latitude/longitude sphere unwrap'
    return o


def torus(name, loc, major, minor, mat='graphite', axis=(0,0,1), segments=40):
    bpy.ops.mesh.primitive_torus_add(major_segments=segments,minor_segments=10,
                                   major_radius=major,minor_radius=minor,location=loc,generate_uvs=True)
    o=bpy.context.object
    o.name=name
    o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
    link_asset(o,mat)
    smooth(o)
    o['uv_authoring']='Toroidal longitudinal/radial wrap'
    return o


def mesh_obj(name, verts, faces, mat, uvs=None, edge=.0, sm=False):
    mesh=bpy.data.meshes.new(name+' Mesh')
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    o=bpy.data.objects.new(name,mesh)
    ASSET.objects.link(o)
    mesh.materials.append(MATS[mat])
    layer=mesh.uv_layers.new(name='UVMap')
    if uvs:
        for poly, coords in zip(mesh.polygons,uvs):
            for li,co in zip(poly.loop_indices,coords):
                layer.data[li].uv=co
    else:
        # Per-face planar atlas for a few architectural/custom panel polygons.
        cells=math.ceil(math.sqrt(len(faces)))
        for pi,p in enumerate(mesh.polygons):
            axis=max(range(3),key=lambda k:abs(p.normal[k]))
            a,b=[k for k in range(3) if k!=axis]
            pts=[mesh.vertices[mesh.loops[li].vertex_index].co for li in p.loop_indices]
            lo=[min(c[a] for c in pts),min(c[b] for c in pts)]
            hi=[max(c[a] for c in pts),max(c[b] for c in pts)]
            denom=max(hi[0]-lo[0],hi[1]-lo[1],.001)
            for li,co in zip(p.loop_indices,pts):
                layer.data[li].uv=((pi%cells+.06+.88*(co[a]-lo[0])/denom)/cells,
                                   (pi//cells+.06+.88*(co[b]-lo[1])/denom)/cells)
    o['role']='editable_asset_component'
    o['uv_authoring']='Authored parameterized surface islands' if uvs else 'Per-face padded planar atlas'
    if sm:smooth(o)
    if edge:bevel(o,edge)
    return o


def panel(name, corners, thickness, mat='glass', edge=.02):
    """Extrude a convex face along its surface normal; explicit editable mesh."""
    pts=[Vector(p) for p in corners]
    n=(pts[1]-pts[0]).cross(pts[2]-pts[0]).normalized()
    verts=[tuple(p+n*thickness*.5) for p in pts]+[tuple(p-n*thickness*.5) for p in pts]
    count=len(pts)
    faces=[tuple(range(count)),tuple(range(2*count-1,count-1,-1))]
    faces += [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    return mesh_obj(name,verts,faces,mat,edge=edge)


def tube(name, points, radius, mat='graphite', sides=16, caps=True):
    """Circular sweep with arc-length side-strip UVs and isolated end caps."""
    pts=[Vector(p) for p in points]
    distances=[0.]
    for a,b in zip(pts,pts[1:]):distances.append(distances[-1]+(b-a).length)
    verts=[]
    for i,p in enumerate(pts):
        tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
        reference=Vector((0,0,1)) if abs(tangent.z)<.9 else Vector((0,1,0))
        u=tangent.cross(reference).normalized()
        v=tangent.cross(u).normalized()
        for k in range(sides):
            a=TAU*k/sides
            verts.append(tuple(p+radius*(math.cos(a)*u+math.sin(a)*v)))
    faces=[];uvs=[]
    for j in range(len(pts)-1):
        for k in range(sides):
            kp=(k+1)%sides
            faces.append((j*sides+k,j*sides+kp,(j+1)*sides+kp,(j+1)*sides+k))
            u0=.04+.70*distances[j]/distances[-1];u1=.04+.70*distances[j+1]/distances[-1]
            v0=.05+.55*k/sides;v1=.05+.55*(k+1)/sides
            uvs.append(((u0,v0),(u0,v1),(u1,v1),(u1,v0)))
    if caps:
        for j,reverse,cx in [(0,True,.20),(len(pts)-1,False,.60)]:
            seq=list(range(sides))
            if reverse:seq.reverse()
            faces.append(tuple(j*sides+k for k in seq))
            uvs.append(tuple((cx+.12*math.cos(TAU*k/sides),.80+.12*math.sin(TAU*k/sides)) for k in seq))
    return mesh_obj(name,verts,faces,mat,uvs,sm=True)


def curved_points(points, steps=6):
    p=[Vector(v) for v in points]
    out=[]
    for i in range(len(p)-1):
        a,b,c,d=p[max(0,i-1)],p[i],p[i+1],p[min(len(p)-1,i+2)]
        for j in range(steps):
            t=j/steps
            q=.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
            out.append(tuple(q))
    out.append(tuple(p[-1]))
    return out


def hose(name, points, radius=.045, mat='graphite'):
    return tube(name,curved_points(points),radius,mat)


def flange(name, loc, outer=.23, inner=.14, depth=.09, mat='steel', axis=(0,1,0), bolts=6):
    q=Vector(axis).normalized().to_track_quat('Z','Y')
    origin=Vector(loc)
    rings=[(outer,-depth/2),(outer,depth/2),(inner,depth/2),(inner,-depth/2)]
    verts=[];faces=[];uvs=[];N=32
    for r,z in rings:
        for i in range(N):
            verts.append(tuple(origin+q@Vector((r*math.cos(TAU*i/N),r*math.sin(TAU*i/N),z))))
    for j in range(4):
        for k in range(N):
            faces.append((j*N+k,j*N+(k+1)%N,((j+1)%4)*N+(k+1)%N,((j+1)%4)*N+k))
            u0=.05+.90*k/N;u1=.05+.90*(k+1)/N;v0=.03+j*.24;v1=v0+.20
            uvs.append(((u0,v0),(u1,v0),(u1,v1),(u0,v1)))
    o=mesh_obj(name,verts,faces,mat,uvs,edge=.008,sm=True)
    for i in range(bolts):
        a=TAU*i/bolts
        center=origin+q@Vector(((outer+inner)*.5*math.cos(a),(outer+inner)*.5*math.sin(a),depth*.65))
        cyl(name+' bolt %02d'%i,center,.018,depth*.45,'steel',axis,.004,6)
    return o


def wheel(name, x, y, z, radius=.46, width=.27, tread=20):
    cyl(name+' tire',(x,y,z),radius,width,'rubber',(1,0,0),.055)
    sign=1 if x>0 else -1
    face=x+sign*width*.50
    cyl(name+' rim',(face,y,z),radius*.69,.035,'sage',(1,0,0),.015)
    torus(name+' rim lip',(face+sign*.022,y,z),radius*.60,.025,'steel',(1,0,0))
    cyl(name+' central hub',(face+sign*.04,y,z),radius*.31,.08,'graphite',(1,0,0),.015)
    for k in range(6):
        a=TAU*k/6
        cyl(name+' lug %02d'%k,(face+sign*.046,y+radius*.45*math.cos(a),z+radius*.45*math.sin(a)),radius*.045,.04,'steel',(1,0,0),.003,6)
    for k in range(tread):
        a=TAU*k/tread
        box(name+' tread %02d'%k,(x,y+(radius-.008)*math.cos(a),z+(radius-.008)*math.sin(a)),
            (width*.83,radius*.18,.045),'rubber',.012,(a-math.pi/2,0,0))


def arch_fender(name,x,y,z,inner,outer,width):
    N=24;verts=[]
    for xx,r in [(x-width/2,inner),(x-width/2,outer),(x+width/2,outer),(x+width/2,inner)]:
        for i in range(N+1):
            a=.08+(math.pi-.16)*i/N
            verts.append((xx,y+r*math.cos(a),z+r*math.sin(a)))
    faces=[];uvs=[]
    for j in range(4):
        for i in range(N):
            faces.append((j*(N+1)+i,j*(N+1)+i+1,((j+1)%4)*(N+1)+i+1,((j+1)%4)*(N+1)+i))
            u0=.04+.92*i/N;u1=.04+.92*(i+1)/N;v0=.03+j*.24
            uvs.append(((u0,v0),(u1,v0),(u1,v0+.20),(u0,v0+.20)))
    for end in (0,N):
        faces.append(tuple(j*(N+1)+end for j in range(4)))
        uvs.append(((.1,.1),(.2,.1),(.2,.2),(.1,.2)))
    return mesh_obj(name,verts,faces,'sage',uvs,edge=.015,sm=True)


def roof_shell(name,cx,cy,base,width,length,rise,mat='sage',thick=.13):
    N=40;verts=[];faces=[];uvs=[]
    # Cross section is a restrained shallow barrel, with real roof thickness.
    for zz,yy in [(0,-length/2),(0,length/2),(-thick,length/2),(-thick,-length/2)]:
        for i in range(N+1):
            t=i/N
            verts.append((cx-width*.5+width*t,cy+yy,base+rise*math.sin(math.pi*t)+zz))
    for j in range(4):
        for i in range(N):
            faces.append((j*(N+1)+i,j*(N+1)+i+1,((j+1)%4)*(N+1)+i+1,((j+1)%4)*(N+1)+i))
            u0=.03+.94*i/N;u1=.03+.94*(i+1)/N;v0=.025+j*.24
            uvs.append(((u0,v0),(u1,v0),(u1,v0+.20),(u0,v0+.20)))
    for end in (0,N):
        faces.append(tuple(j*(N+1)+end for j in range(4)))
        uvs.append(((.02,.02),(.05,.02),(.05,.05),(.02,.05)))
    return mesh_obj(name,verts,faces,mat,uvs,edge=.02,sm=True)


def louver(name, center, width, height, face='front'):
    x,y,z=center
    if face=='front':
        box(name+' recess',(x,y,z),(width,.045,height),'graphite',.025)
        for i in range(6):box(name+' slat %02d'%i,(x,y-.025,z-height*.4+i*height*.16),(width*.89,.09,.045),'steel',.012,(.20,0,0))
    else:
        box(name+' recess',(x,y,z),(.045,width,height),'graphite',.025)
        for i in range(6):box(name+' slat %02d'%i,(x+.025,y,z-height*.4+i*height*.16),(.09,width*.89,.045),'steel',.012,(0,.20,0))


def wall_lamp(name,loc,scale=1):
    x,y,z=loc
    box(name+' casing',loc,(.18*scale,.15*scale,.40*scale),'graphite',.055*scale)
    box(name+' diffuser',(x,y-.085*scale,z),(.12*scale,.025*scale,.28*scale),'lamp',.04*scale)
    for dz in (-.1,.1):box(name+' protective bar',(x,y-.11*scale,z+dz*scale),(.16*scale,.025*scale,.025*scale),'graphite',.007*scale)


def street_sweeper():
    # Compact four-wheel municipal vehicle, broad short cab and enclosed hopper.
    box('Chassis structural tray',(0,.0,.61),(1.45,2.95,.28),'graphite',.10)
    box('Lower rear service sill',(0,.80,.91),(1.68,1.68,.48),'sage',.15)
    # Cab is a trapezoidal closed shell; exterior window inserts are separate meshes.
    cross=[(-1.68,.75),(-1.65,1.10),(-1.39,2.34),(-1.19,2.49),(-.18,2.45),(-.10,.75)]
    verts=[(x,y,z) for x in (-.81,.81) for y,z in cross]
    faces=[tuple(range(5,-1,-1)),tuple(range(6,12))]+[(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)]
    mesh_obj('Cab ivory rounded shell',verts,faces,'ivory',edge=.085)
    def fy(z):return -1.65+(z-1.10)*.26/1.24
    windshield=[(-.70,fy(1.19)-.037,1.19),(.70,fy(1.19)-.037,1.19),(.70,fy(2.28)-.037,2.28),(-.70,fy(2.28)-.037,2.28)]
    panel('Windshield rubber surround',windshield,.045,'rubber',.065)
    glass=[(-.65,fy(1.25)-.066,1.25),(.65,fy(1.25)-.066,1.25),(.64,fy(2.22)-.066,2.22),(-.64,fy(2.22)-.066,2.22)]
    panel('Broad panoramic windshield',glass,.018,'glass',.06)
    for s in (-1,1):
        x=s*.835
        corners=[(x,-1.48,1.05),(x,-1.25,2.27),(x,-.30,2.27),(x,-.23,.94)]
        panel(('Left' if s<0 else 'Right')+' door gasket',corners,.035,'rubber',.05)
        corners=[(x+s*.024,-1.38,1.14),(x+s*.024,-1.20,2.21),(x+s*.024,-.37,2.21),(x+s*.024,-.32,1.05)]
        panel(('Left' if s<0 else 'Right')+' door glazing',corners,.022,'glass',.045)
        box('Door lower panel '+str(s),(x+s*.02,-.63,.99),(.08,.55,.29),'sage',.045)
        box('Door grab handle '+str(s),(x+s*.075,-.35,1.43),(.065,.08,.22),'graphite',.025)
        hose('Mirror support '+str(s),[(x,-1.16,2.07),(s*1.05,-1.25,2.09),(s*1.11,-1.40,1.94)],.035)
        box('Side mirror case '+str(s),(s*1.12,-1.42,1.81),(.13,.14,.37),'graphite',.055)
        box('Side mirror reflective surface '+str(s),(s*1.12,-1.50,1.81),(.105,.018,.30),'steel',.03)
        box('Mirror amber indicator '+str(s),(s*1.19,-1.43,1.73),(.018,.08,.10),'orange',.014)
        box('Front lamp gasket '+str(s),(s*.62,-1.64,1.0),(.29,.12,.21),'graphite',.06)
        cyl('Front circular headlamp '+str(s),(s*.62,-1.715,1.02),.085,.04,'lamp',(0,-1,0),.012)
        box('Front amber marker '+str(s),(s*.78,-1.67,1.05),(.065,.055,.12),'orange',.022)
    box('Sage front bumper',(0,-1.69,.80),(1.66,.20,.19),'sage',.075)
    for s in (-1,1):box('Roof worklamp '+str(s),(s*.64,-1.34,2.39),(.22,.18,.13),'graphite',.045);box('Roof worklamp lens '+str(s),(s*.64,-1.44,2.39),(.16,.025,.075),'lamp',.02)
    cyl('Beacon pedestal',(0,-.66,2.49),.16,.07,'graphite')
    cyl('Amber rotating beacon',(0,-.66,2.64),.12,.24,'orange',edge=.04)
    cyl('Beacon top cap',(0,-.66,2.77),.12,.04,'orange')
    rod('Wiper lower arm',(-.05,-1.72,1.19),(-.37,-1.62,1.67),.018)
    rod('Wiper blade',(-.40,-1.61,1.58),(-.27,-1.51,2.06),.022)
    # Soft superelliptical collection body keeps a visible cylindrical hopper silhouette.
    N=48;verts=[];faces=[];uvs=[]
    for y in (.02,1.64):
        for k in range(N):
            a=TAU*k/N
            xx=.78*math.copysign(abs(math.cos(a))**.72,math.cos(a))
            zz=1.72+.67*math.copysign(abs(math.sin(a))**.78,math.sin(a))
            verts.append((xx,y,zz))
    for k in range(N):
        kp=(k+1)%N;faces.append((k,kp,kp+N,k+N));uvs.append(((.04+.92*k/N,.04),(.04+.92*(k+1)/N,.04),(.04+.92*(k+1)/N,.58),(.04+.92*k/N,.58)))
    for j,cy in [(0,.76),(1,.76)]:
        seq=list(range(N)) if j else list(reversed(range(N)))
        faces.append(tuple(k+j*N for k in seq))
        uvs.append(tuple((.25+j*.5+.18*math.cos(TAU*k/N),cy+.18*math.sin(TAU*k/N)) for k in seq))
    mesh_obj('Enclosed cylindrical collection hopper',verts,faces,'ivory',uvs,edge=.06,sm=True)
    for s in (-1,1):
        box('Hopper sage lower panel '+str(s),(s*.775,.84,1.32),(.07,1.34,.49),'sage',.10)
        box('Hopper service hatch '+str(s),(s*.82,.37,1.75),(.06,.52,.66),'ivory',.065)
        box('Hopper recessed latch '+str(s),(s*.86,.24,1.75),(.035,.10,.18),'graphite',.02)
        box('Rear orange marker '+str(s),(s*.62,1.72,1.25),(.14,.055,.16),'orange',.025)
        box('Rear red tail lamp '+str(s),(s*.62,1.72,1.06),(.16,.055,.11),'red',.025)
        wheel('Wheel '+str(s)+' front',s*.85,-.65,.49)
        wheel('Wheel '+str(s)+' rear',s*.85,1.05,.49)
        for y in (-.65,1.05):arch_fender('Rounded wheel arch '+str((s,y)),s*.86,y,.49,.48,.59,.32)
        box('Access step '+str(s),(s*.94,-.09,.64),(.30,.35,.10),'graphite',.04)
    box('Rear dump door',(0,1.70,1.75),(1.35,.10,1.01),'sage',.18)
    box('Rear door inset',(0,1.765,1.77),(1.13,.035,.77),'ivory',.13)
    for x in (-.5,.5):
        box('Rear latch '+str(x),(x,1.80,1.48),(.13,.10,.28),'graphite',.025)
        rod('Dump hydraulic strut '+str(x),(x,1.45,2.25),(x,.64,2.47),.05)
    box('Rear bumper',(0,1.83,.69),(1.64,.20,.17),'graphite',.06)
    cyl('Hopper fill cap',(0,.85,2.42),.18,.08,'graphite')
    hose('External ribbed suction hose',[(.88,-.02,.66),(.88,-.02,1.4),(.87,-.04,2.10),(.70,.15,2.48),(.45,.60,2.47)],.105)
    for z in [1.0+i*.07 for i in range(16)]:torus('Hose corrugation %.2f'%z,(.88,-.02,z),.104,.014,'rubber')
    for x in (-.88,.88):
        y=-1.97
        rod('Brush outrigger '+str(x),(x*.56,-1.32,.55),(x,y,.48),.075)
        cyl('Brush hydraulic motor '+str(x),(x,y,.54),.13,.19,'graphite')
        box('Brush orange safety cap '+str(x),(x,y,.66),(.22,.18,.06),'orange',.03)
        cyl('Brush drive plate '+str(x),(x,y,.39),.34,.07,'graphite',edge=.025)
        for k in range(36):
            a=TAU*k/36
            a2=a+.06
            rod('Sweeping bristle '+str((x,k)),(x+.28*math.cos(a),y+.28*math.sin(a),.36),
                (x+.47*math.cos(a2),y+.47*math.sin(a2),.055),.017,'bristle' if k%3 else 'rubber',.003,6)
    box('Suction shoe body',(0,-1.85,.29),(.78,.35,.30),'graphite',.065)
    box('Suction mouth dark aperture',(0,-2.045,.22),(.66,.02,.12),'rubber',.025)
    box('Suction shoe lower lip',(0,-2.06,.15),(.79,.06,.045),'steel',.014)
    return {'description':'Compact four-wheel sweeper with broad sloping glazing, enclosed hopper, twin powered side brushes and central suction shoe.',
            'intended_dimensions_m':{'width':2.75,'depth':4.30,'height':2.80}}


def pipe_inspection_robot():
    centers=[(0,-1.14,0),(0,0,0),(.14,1.12,.15)]
    for i,(cx,cy,angle) in enumerate(centers):
        before=set(ASSET.objects)
        box('Module %d ivory capsule'%i,(0,0,.65),(.76,.78,.57),'ivory',.20)
        box('Module %d sage top access hatch'%i,(0,.02,.934),(.48,.48,.04),'sage',.07)
        box('Module %d orange service latch'%i,(0,-.16,.964),(.14,.07,.025),'orange',.012)
        for s in (-1,1):
            box('Module %d side inset %d'%(i,s),(s*.379,.02,.66),(.035,.47,.32),'sage',.07)
            for y in (-.25,.25):cyl('Module %d panel screw %d %.2f'%(i,s,y),(s*.405,y,.73),.024,.018,'steel',(1,0,0),.004,8)
            rod('Module %d wheel suspension %d'%(i,s),(s*.22,.05,.43),(s*.46,.09,.28),.065)
            wheel('Module %d wheel %d'%(i,s),s*.48,.08,.25,.25,.18,16)
        box('Module %d undercarriage'%i,(0,.06,.37),(.62,.50,.15),'graphite',.055)
        if i==0:
            box('Camera forward mounting plate',(0,-.406,.65),(.68,.06,.48),'graphite',.13)
            cyl('Camera lens housing',(0,-.49,.65),.19,.17,'graphite',(0,-1,0),.022)
            torus('Camera protective lens bezel',(0,-.588,.65),.165,.022,'steel',(0,1,0))
            cyl('Optical camera glass',(0,-.595,.65),.143,.025,'lens',(0,1,0),.015)
            torus('Optical inner lens reflection',(0,-.611,.65),.082,.008,'glass',(0,1,0))
            for s in (-1,1):
                for dz in (-.115,.115):
                    cyl('Inspection lamp bezel '+str((s,dz)),(s*.265,-.455,.65+dz),.064,.065,'steel',(0,1,0),.008)
                    cyl('Inspection lamp diffuser '+str((s,dz)),(s*.265,-.493,.65+dz),.047,.018,'lamp',(0,1,0),.008)
        elif i==1:
            box('Center module ventilation',(0,.035,.96),(.34,.30,.025),'graphite',.025)
            for k in range(5):box('Center cooling fin %d'%k,(-.13+k*.065,.035,.98),(.025,.26,.02),'steel',.004)
        else:
            box('Reel support crossbar',(0,.15,1.01),(.77,.18,.10),'graphite',.035)
            for x in (-.30,.30):
                box('Reel upright '+str(x),(x,.17,1.22),(.08,.15,.47),'graphite',.035)
                cyl('Reel flange '+str(x),(x,.17,1.32),.32,.06,'graphite',(1,0,0),.022)
                cyl('Reel axle cap '+str(x),(x*1.15,.17,1.32),.075,.07,'steel',(1,0,0),.01)
            cyl('Cable reel drum',(0,.17,1.32),.21,.56,'graphite',(1,0,0),.025)
            for k in range(9):torus('Orange wound tether %02d'%k,(-.235+k*.058,.17,1.32),.24,.027,'orange',(1,0,0))
            rod('Reel carry handle',(-.34,.17,1.65),(.34,.17,1.65),.035)
            hose('Tether tail',[(.02,.42,1.34),(.02,.68,1.26),(.10,.84,1.04),(.22,.95,.86)],.028,'orange')
            cyl('Rear tether connector',(.22,.98,.85),.068,.17,'graphite',(0,1,0),.015)
            torus('Tether connector orange seal',(.22,1.075,.85),.054,.015,'orange',(0,1,0))
        transform=Matrix.Translation((cx,cy,0))@Matrix.Rotation(angle,4,'Z')
        for o in set(ASSET.objects)-before:o.matrix_world=transform@o.matrix_world
    for i,(cx,cy) in enumerate([(0,-.57),(.07,.57)]):
        rod('Universal joint longitudinal shaft %d'%i,(cx,cy-.18,.64),(cx,cy+.18,.64),.115)
        cyl('Universal joint cross pivot %d'%i,(cx,cy,.64),.17,.40,'graphite',(1,0,0),.025)
        for s in (-1,1):
            cyl('Universal pivot cap '+str((i,s)),(cx+s*.21,cy,.64),.13,.055,'steel',(1,0,0),.015)
            torus('Universal orange seal '+str((i,s)),(cx+s*.245,cy,.64),.106,.015,'orange',(1,0,0))
            box('Universal fork '+str((i,s)),(cx+s*.145,cy,.64),(.07,.44,.14),'graphite',.035)
        hose('Joint protected cable %d'%i,[(cx-.14,cy-.23,.83),(cx-.16,cy,.90),(cx-.14,cy+.23,.83)],.028)
    return {'description':'Three compact capsule inspection modules, six rubber wheels, two exposed universal joints, forward camera with four work lamps and rear orange tether reel.',
            'intended_dimensions_m':{'width':1.35,'depth':3.85,'height':1.70}}


def road_maintenance_depot():
    box('Shallow building foundation',(0,0,.12),(7.75,5.25,.24),'concrete',.16)
    box('Garage service floor',(-.82,-.08,.26),(5.50,4.85,.09),'interior',.03)
    box('Left structural wall',(-3.52,.12,1.73),(.28,4.75,2.98),'ivory',.06)
    box('Rear structural wall',(0,2.37,1.73),(7.20,.26,2.98),'ivory',.06)
    box('Right structural wall',(3.52,.12,1.73),(.28,4.75,2.98),'ivory',.06)
    for x in (-3.43,1.35):
        box('Bay rounded structural pier '+str(x),(x,-2.28,1.72),(.40,.44,3.05),'ivory',.075)
        box('Bay pier concrete foot '+str(x),(x,-2.28,.57),(.47,.50,.62),'concrete',.045)
    box('Main front lintel',(-1.05,-2.27,3.00),(5.16,.44,.45),'ivory',.07)
    for x in (-3.17,1.10):box('Roller door vertical guide '+str(x),(x,-2.31,1.64),(.14,.20,2.62),'graphite',.035)
    box('Roller door top guide',(-1.035,-2.31,2.93),(4.43,.20,.18),'graphite',.04)
    cyl('Raised shutter orange roller',(-1.035,-2.28,2.80),.13,4.20,'orange',(1,0,0),.02)
    for i in range(3):box('Raised shutter horizontal slat %d'%i,(-1.035,-2.41,2.75+i*.06),(4.17,.035,.045),'orange',.009)
    roof_shell('Soft barrel roof',0,.08,3.22,7.64,5.02,.70,'sage',.15)
    for y in (-2.43,-1.60,-.70,.30,1.3,2.58):
        pts=[]
        for i in range(41):
            t=i/40;pts.append((-3.82+7.64*t,y,3.25+.70*math.sin(math.pi*t)))
        tube('Roof curved standing seam %.2f'%y,pts,.028,'sage_light',10)
    # Four separate curved glass panels follow the barrel across the front roof band.
    for i in range(4):
        x0=-2.55+i*.88;x1=x0+.77;y0=-2.03;y1=-1.23
        z0=3.25+.70*math.sin(math.pi*(x0+3.82)/7.64)
        z1=3.25+.70*math.sin(math.pi*(x1+3.82)/7.64)
        panel('Roof skylight %d'%i,[(x0,y0,z0),(x1,y0,z1),(x1,y1,z1),(x0,y1,z0)],.055,'glass',.025)
    # Roof ventilation: two turbine-like mushroom vents and rear louver stack.
    for x in (-2.25,1.65):
        z=3.24+.70*math.sin(math.pi*(x+3.82)/7.64)
        box('Turbine plinth '+str(x),(x,.80,z+.075),(.48,.48,.16),'sage',.04)
        cyl('Turbine dark core '+str(x),(x,.80,z+.30),.23,.37,'graphite',edge=.055)
        sphere('Turbine cap '+str(x),(x,.80,z+.42),(.28,.28,.12),'sage')
        for k in range(12):
            a=TAU*k/12
            hose('Turbine vane '+str((x,k)),[(x+.21*math.cos(a),.80+.21*math.sin(a),z+.14),(x+.28*math.cos(a+.15),.80+.28*math.sin(a+.15),z+.30),(x+.22*math.cos(a+.28),.80+.22*math.sin(a+.28),z+.47)],.014,'steel')
    box('Rear roof ventilation curb',(2.25,1.65,3.68),(1.10,.85,.20),'sage',.04)
    box('Rear roof exhaust housing',(2.25,1.65,3.97),(1.05,.80,.50),'graphite',.06)
    for k in range(4):box('Roof exhaust louver %d'%k,(2.25,1.22,3.80+k*.105),(.96,.10,.045),'steel',.012)
    # Front and side office glazing with dedicated own entrance.
    box('Office back partition',(2.40,.48,1.65),(1.82,.16,2.8),'interior',.04)
    box('Office left partition',(1.62,-.92,1.65),(.15,2.94,2.8),'ivory',.035)
    box('Office front lower wall',(2.63,-2.34,.75),(1.76,.26,1.0),'ivory',.055)
    box('Office front window gasket',(2.31,-2.49,1.82),(1.05,.09,1.28),'sage',.055)
    box('Office front glazed pane',(2.31,-2.55,1.82),(.89,.035,1.10),'glass',.035)
    box('Office front mullion',(2.31,-2.58,1.82),(.045,.025,1.12),'ivory',.008)
    box('Office door frame',(3.15,-2.50,1.40),(.69,.14,2.30),'sage',.045)
    box('Office door leaf',(3.15,-2.60,1.37),(.55,.065,2.14),'sage',.035)
    box('Office door glass',(3.15,-2.64,1.80),(.39,.025,.99),'glass',.03)
    rod('Office door vertical pull',(3.34,-2.72,1.18),(3.34,-2.72,1.55),.022,'steel')
    box('Office front window sill',(2.30,-2.59,1.16),(1.25,.20,.10),'sage',.035)
    box('Office shallow canopy',(2.60,-2.42,2.95),(2.23,.79,.20),'sage',.11)
    box('Office step',(3.17,-2.75,.16),(.95,.40,.18),'concrete',.055)
    for y in (-1.40,-.35):
        box('Office side window frame '+str(y),(3.68,y,1.94),(.08,.89,1.25),'sage',.04)
        box('Office side glass '+str(y),(3.73,y,1.94),(.025,.74,1.09),'glass',.025)
        box('Office side sill '+str(y),(3.77,y,1.28),(.19,1.0,.10),'sage',.025)
    # Shallow genuinely recessed tool alcove at the bay/office junction.
    box('Tool alcove backing',(1.60,-2.19,.95),(.55,.12,1.23),'graphite',.025)
    for x in (1.28,1.91):box('Tool alcove jamb '+str(x),(x,-2.37,.95),(.10,.38,1.35),'ivory',.025)
    box('Tool alcove lintel',(1.60,-2.37,1.64),(.73,.38,.10),'ivory',.025)
    for z in (.37,.83,1.27):
        box('Alcove shelf '+str(z),(1.60,-2.38,z),(.58,.31,.06),'steel',.01)
        box('Alcove utility case '+str(z),(1.60,-2.40,z+.15),(.35,.23,.24),'orange' if z<.9 else 'sage',.04)
        box('Alcove case handle '+str(z),(1.60,-2.53,z+.23),(.15,.035,.045),'graphite',.014)
    # Interior equipment remains separately editable and visible through open bay.
    box('Rear workbench top',(-.70,1.91,1.01),(3.85,.62,.13),'steel',.04)
    for x in (-2.15,.55):
        box('Workbench cabinet '+str(x),(x,1.94,.65),(.78,.53,.68),'graphite',.04)
        for z in (.45,.62,.79):
            box('Workbench drawer '+str((x,z)),(x,1.655,z),(.69,.035,.13),'sage',.018)
            box('Workbench drawer pull '+str((x,z)),(x,1.625,z+.02),(.32,.04,.024),'steel',.008)
    box('Tool board',(-.65,2.20,1.69),(2.84,.08,.91),'graphite',.04)
    for i in range(8):
        x=-1.80+i*.33
        rod('Hanging wrench shank %d'%i,(x,2.135,1.48),(x,2.135,1.91),.025,'steel')
        torus('Hanging wrench head %d'%i,(x,2.13,1.94),.052,.018,'steel',(0,1,0),24)
    for x in (-2.85,-2.22):
        box('Left storage upright '+str(x),(x,.45,1.27),(.06,.10,1.93),'graphite',.015)
    for z in (.40,.90,1.40,1.90):
        box('Left storage shelf '+str(z),(-2.54,.44,z),(.74,.66,.065),'steel',.015)
        box('Left shelf storage case '+str(z),(-2.54,.44,z+.17),(.54,.46,.27),'orange' if z<1 else 'sage',.045)
    box('Service trench dark inset',(-.90,-.35,.317),(2.54,2.50,.025),'graphite',.04)
    for x in (-2.22,.42):box('Service trench safety edge '+str(x),(x,-.35,.334),(.045,2.59,.02),'orange',.008)
    for k in range(18):box('Service trench grating %02d'%k,(-.90,-1.54+k*.14,.342),(2.47,.035,.03),'steel',.008)
    for x in (-3.12,1.09):
        cyl('Bay safety bollard '+str(x),(x,-2.63,.72),.105,.91,'orange',edge=.035)
        cyl('Bay bollard dark band '+str(x),(x,-2.63,.78),.11,.22,'graphite',edge=.01)
    for x in (-2.60,-1.05,.52):
        box('Bay overhead lamp housing '+str(x),(x,-2.53,3.10),(.65,.16,.15),'graphite',.045)
        box('Bay overhead lamp diffuser '+str(x),(x,-2.625,3.10),(.54,.03,.075),'lamp',.025)
    for x in (-2.1,.1):
        box('Interior ceiling luminaire '+str(x),(x,.65,3.04),(1.00,.18,.08),'graphite',.025)
        box('Interior ceiling diffuser '+str(x),(x,.65,2.99),(.88,.13,.025),'lamp',.01)
    wall_lamp('Office entrance light',(3.12,-2.84,2.62),.65)
    louver('Rear wall ventilation',(1.50,2.53,2.34),1.18,.65)
    box('Rear service door',(-2.38,2.53,1.25),(.94,.10,1.96),'sage',.045)
    box('Rear door glazing',(-2.38,2.60,1.75),(.63,.03,.63),'glass',.035)
    for s in (-1,1):
        x=s*3.30
        hose('Rainwater downpipe '+str(s),[(x,2.48,3.3),(x,2.60,2.90),(x,2.60,.44),(x+s*.18,2.60,.30)],.055,'graphite')
    return {'description':'Rounded barrel-roof maintenance depot with genuinely open service bay, raised shutter, interior benches and grating, glazed side office with separate door, recessed tool alcove and roof ventilation.',
            'intended_dimensions_m':{'width':7.8,'depth':5.6,'height':4.3}}


def compact_pump_station():
    box('Station shallow concrete foundation',(0,.10,.14),(5.50,4.00,.28),'concrete',.19)
    box('Utility building rear wall',(0,1.72,1.75),(4.85,.24,3.00),'ivory',.09)
    box('Utility enclosed side wall',(2.27,.43,1.75),(.30,2.74,3.0),'ivory',.09)
    for x in (-2.20,2.20):
        box('Canopy front rounded column '+str(x),(x,-1.48,1.72),(.33,.38,2.95),'ivory',.065)
        box('Canopy column sage base '+str(x),(x,-1.48,.75),(.37,.42,.83),'sage',.05)
        box('Canopy column foot '+str(x),(x,-1.48,.38),(.48,.52,.20),'concrete',.04)
    box('Left rear canopy pier',(-2.20,1.50,1.73),(.33,.38,2.95),'ivory',.055)
    roof_shell('Pump station shallow curved roof',0,.12,3.25,5.18,3.93,.42,'sage',.17)
    for y in (-1.82,-.90,.02,.94,2.06):
        pts=[(-2.59+5.18*i/36,y,3.28+.42*math.sin(math.pi*i/36)) for i in range(37)]
        tube('Canopy roof raised seam %.2f'%y,pts,.026,'sage_light',10)
    for y in (-1.40,.10,1.48):box('Canopy underside beam '+str(y),(0,y,3.13),(4.55,.14,.18),'graphite',.035)
    box('Canopy ceiling light casing',(0,-.72,3.07),(1.60,.24,.10),'graphite',.04)
    box('Canopy ceiling diffuser',(0,-.72,3.005),(1.43,.17,.04),'lamp',.025)
    # Rear utility door, panel and exhaust stack give the facility a useful rear.
    box('Rear utility door',(1.12,1.89,1.31),(1.04,.10,2.03),'sage',.06)
    box('Rear utility door window',(1.12,1.96,1.82),(.73,.025,.62),'glass',.045)
    box('Rear utility pull',(1.47,1.98,1.22),(.055,.06,.30),'steel',.018)
    louver('Utility side ventilation',(2.44,.63,2.42),.80,.58,'side')
    louver('Utility rear ventilation',(-.95,1.88,2.26),1.10,.63)
    box('Exhaust stack plinth',(1.50,1.11,3.65),(.52,.52,.30),'ivory',.06)
    cyl('Exhaust stack core',(1.50,1.11,3.95),.20,.38,'graphite',edge=.025)
    for z in (3.83,3.94,4.05):cyl('Exhaust stack rain baffle '+str(z),(1.50,1.11,z),.28,.055,'steel',edge=.018)
    sphere('Exhaust mushroom cap',(1.50,1.11,4.16),(.35,.35,.18),'sage')
    # Paired understandable volutes and rear electric motors.
    for i,x in enumerate((-.95,.82)):
        box('Pump %d concrete plinth'%i,(x,.05,.39),(1.45,2.12,.22),'concrete',.07)
        box('Pump %d steel skid'%i,(x,.08,.54),(1.20,1.84,.12),'sage',.04)
        for sx in (-.32,.32):
            box('Pump %d cast mounting foot %.2f'%(i,sx),(x+sx,-.13,.67),(.21,.56,.20),'sage',.045)
            for y in (-.30,.05):cyl('Pump anchor '+str((i,sx,y)),(x+sx,y,.79),.035,.07,'steel',edge=.006,vertices=6)
        sphere('Pump %d rounded volute housing'%i,(x,-.27,1.11),(.53,.30,.55),'sage',40,20)
        cyl('Pump %d front volute plate'%i,(x,-.53,1.11),.43,.075,'sage_light',(0,1,0),.025,40)
        flange('Pump %d front volute flange'%i,(x,-.59,1.11),.44,.27,.07,'sage',(0,-1,0),8)
        cyl('Pump %d central inlet neck'%i,(x,-.72,1.11),.23,.29,'graphite',(0,1,0),.025)
        flange('Pump %d suction coupling'%i,(x,-.87,1.11),.30,.20,.10,'sage',(0,-1,0),6)
        # Front suction bend travels to a dedicated foundation penetration.
        hose('Pump %d curved suction inlet'%i,[(x,-.85,1.11),(x,-1.24,1.11),(x,-1.46,.94),(x,-1.48,.52)],.20)
        flange('Pump %d inlet floor socket'%i,(x,-1.48,.53),.29,.19,.10,'steel',(0,0,1),6)
        box('Pump %d inlet floor footing'%i,(x,-1.48,.36),(.65,.65,.15),'concrete',.04)
        cyl('Pump %d motor coupling'%i,(x,.16,1.08),.21,.40,'steel',(0,1,0),.018)
        cyl('Pump %d electric motor body'%i,(x,.70,1.08),.32,.82,'graphite',(0,1,0),.055,40)
        cyl('Pump %d motor end cover'%i,(x,1.13,1.08),.34,.12,'graphite',(0,1,0),.05,40)
        for k in range(9):
            y=.34+k*.085
            cyl('Pump %d cooling fin %02d'%(i,k),(x,y,1.08),.36,.035,'graphite',(0,1,0),.007)
        box('Pump %d motor terminal box'%i,(x,.63,1.44),(.40,.34,.17),'graphite',.045)
        box('Pump %d orange motor service tab'%i,(x,.45,1.47),(.22,.045,.10),'orange',.02)
        for sx in (-.24,.24):box('Pump %d motor foot %.2f'%(i,sx),(x+sx,.73,.66),(.18,.72,.15),'sage',.035)
        # Tangential discharge at the top of the volute joins the overhead manifold.
        rod('Pump %d vertical discharge'%i,(x+.12,-.19,1.48),(x+.12,-.19,2.20),.145)
        flange('Pump %d discharge flange'%i,(x+.12,-.19,1.74),.22,.135,.10,'sage',(0,0,1),6)
        flange('Pump %d upper discharge collar'%i,(x+.12,-.19,2.17),.22,.135,.10,'sage',(0,0,1),6)
        hose('Pump %d motor electrical conduit'%i,[(x,.80,1.49),(x,1.33,1.50),(x,1.43,.73),(1.66,1.43,.73)],.025)
    hose('Main thick curved manifold',[(-2.82,-.19,1.25),(-2.40,-.19,1.25),(-2.10,-.19,1.57),(-2.05,-.19,2.13),(-1.70,-.19,2.24),(1.55,-.19,2.24),(1.95,-.19,2.10),(2.10,-.19,1.56),(2.42,-.19,1.25),(2.82,-.19,1.25)],.165)
    for x in (-1.65,-.30,1.46):flange('Manifold service flange '+str(x),(x,-.19,2.24),.24,.155,.10,'sage',(1,0,0),6)
    for s in (-1,1):
        flange('Station external outlet flange '+str(s),(s*2.83,-.19,1.25),.285,.165,.105,'steel',(s,0,0),8)
        cyl('Outlet inner dark recess '+str(s),(s*2.77,-.19,1.25),.159,.02,'rubber',(1,0,0),.0)
        box('External pipe support '+str(s),(s*2.48,-.19,.83),(.18,.34,.64),'sage',.025)
        box('External pipe support foot '+str(s),(s*2.48,-.19,.43),(.39,.47,.10),'steel',.025)
    # Orange handwheel on a graphite gate valve in the visible header.
    cyl('Valve body',(.37,-.19,2.24),.23,.27,'graphite',(1,0,0),.04)
    rod('Valve stem',(.37,-.19,2.24),(.37,-.61,2.24),.065,'steel')
    torus('Operational orange valve handwheel',(.37,-.68,2.24),.245,.030,'orange',(0,1,0))
    cyl('Valve handwheel hub',(.37,-.68,2.24),.068,.09,'orange',(0,1,0),.015)
    for k in range(4):
        a=TAU*k/4
        rod('Valve handwheel spoke %d'%k,(.37,-.68,2.24),(.37+.22*math.cos(a),-.68,2.24+.22*math.sin(a)),.022,'orange')
    # Compact control cabinet on right front column, with readable operational controls.
    box('Control cabinet enclosure',(2.09,-1.49,1.62),(.74,.32,1.48),'ivory',.075)
    box('Control cabinet front panel',(2.09,-1.68,1.62),(.63,.065,1.34),'steel',.035)
    box('Control cabinet display bezel',(2.09,-1.725,2.03),(.39,.035,.28),'graphite',.025)
    box('Control cabinet display glass',(2.09,-1.747,2.03),(.31,.014,.20),'glass',.012)
    for i,(x,z,mat) in enumerate([(1.94,1.73,'orange'),(2.23,1.73,'graphite'),(1.94,1.51,'sage'),(2.23,1.51,'sage')]):
        cyl('Control button bezel %d'%i,(x,-1.73,z),.069,.035,'graphite',(0,1,0),.008)
        cyl('Control button cap %d'%i,(x,-1.758,z),.049,.028,mat,(0,1,0),.01)
    box('Control cabinet orange access hatch',(2.09,-1.737,1.17),(.40,.035,.36),'orange',.035)
    box('Control cabinet service lock',(2.22,-1.765,1.19),(.035,.025,.075),'graphite',.009)
    for i in range(3):
        x=1.93+i*.14
        hose('Control cabinet routed conduit %d'%i,[(x,-1.52,.88),(x,-1.52,.59),(x+.02,-1.26,.47),(2.20,-.75,.47),(2.20,.28,.62)],.035)
    wall_lamp('Canopy right column lamp',(2.20,-1.71,2.66),.80)
    wall_lamp('Canopy left column lamp',(-2.20,-1.71,2.65),.80)
    return {'description':'Small curved-roof utility station with open canopy, paired rounded volute pumps, rear finned electric motors, curved common manifold with two side outlets, orange gate valve handwheel and compact control cabinet.',
            'intended_dimensions_m':{'width':5.80,'depth':4.05,'height':4.35}}


BUILDERS={'street_sweeper':street_sweeper,'pipe_inspection_robot':pipe_inspection_robot,
          'road_maintenance_depot':road_maintenance_depot,'compact_pump_station':compact_pump_station}


def authoring_bounds():
    bpy.context.view_layer.update()
    corners=[]
    for obj in ASSET.objects:
        if obj.type=='MESH':
            corners += [obj.matrix_world@Vector(p) for p in obj.bound_box]
    lo=Vector([min(p[i] for p in corners) for i in range(3)])
    hi=Vector([max(p[i] for p in corners) for i in range(3)])
    return lo,hi


def studio(lo,hi):
    scene=bpy.context.scene
    col=bpy.data.collections.new('STUDIO')
    scene.collection.children.link(col)
    def move(o):
        for c in list(o.users_collection):c.objects.unlink(o)
        col.objects.link(o)
    span=max(hi-lo);center=(hi+lo)*.5
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,lo.z-.025))
    floor=bpy.context.object;floor.name='STUDIO | Neutral seamless floor';move(floor)
    floor.data.materials.append(material('Studio | Warm Grey',(.63,.64,.61),0,.82))
    for name,offset,power,size in [('Key',(1.6,-2.1,2.7),1200,1.6),('Fill',(-2.0,-.7,1.4),800,1.8),('Rim',(.6,2.0,2.2),1100,1.4)]:
        data=bpy.data.lights.new('STUDIO | '+name,'AREA');data.energy=power*(span/3)**2;data.shape='DISK';data.size=span*size
        ob=bpy.data.objects.new('STUDIO | '+name,data);col.objects.link(ob)
        ob.location=center+Vector(offset)*span
        ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler()
    data=bpy.data.cameras.new('STUDIO | Orthographic camera')
    cam=bpy.data.objects.new('STUDIO | Orthographic camera',data);col.objects.link(cam)
    cam.data.type='ORTHO';cam.data.lens=50;cam.data.clip_end=1000
    scene.camera=cam
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU';scene.cycles.samples=40;scene.cycles.use_denoising=True
    scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.render.resolution_x=960;scene.render.resolution_y=960;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
    scene.render.film_transparent=False
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.73,.76,.78,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.40
    scene.view_settings.view_transform='AgX'
    return cam,center,span


def camera_view(cam,center,span,lo,hi,rear=False):
    direction=Vector((-1.6,2.35,1.55) if rear else (1.6,-2.35,1.55))
    cam.location=center+direction*span
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update()
    inv=cam.matrix_world.inverted()
    corners=[inv@Vector((x,y,z)) for x in (lo.x,hi.x) for y in (lo.y,hi.y) for z in (lo.z,hi.z)]
    xs=[c.x for c in corners];ys=[c.y for c in corners]
    cam.data.ortho_scale=max(max(xs)-min(xs),max(ys)-min(ys))*1.20
    return {'projection':'orthographic','location_m':list(cam.location),'target_m':list(center),
            'rotation_euler_radians':list(cam.rotation_euler),'orthographic_scale_m':cam.data.ortho_scale}


def produce(slug):
    start=stamp();t0=time.perf_counter();out=ROOT/slug;out.mkdir(exist_ok=True);(out/'renders').mkdir(exist_ok=True)
    reset(slug)
    design=BUILDERS[slug]()
    bpy.context.view_layer.update()
    lo,hi=authoring_bounds()
    objs=[o for o in ASSET.objects if o.type=='MESH']
    authored={'mesh_objects':len(objs),'base_mesh_vertices':sum(len(o.data.vertices) for o in objs),
              'base_mesh_polygons':sum(len(o.data.polygons) for o in objs),
              'authored_bounds_m':{'minimum':list(lo),'maximum':list(hi),'dimensions':list(hi-lo)},
              'measurement_note':'Direct production measurements from the authored scene, not independent validation.'}
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    export_times={}
    t=time.perf_counter()
    bpy.ops.export_scene.gltf(filepath=str(out/(slug+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
    export_times['glb_seconds']=time.perf_counter()-t
    t=time.perf_counter()
    bpy.ops.export_scene.fbx(filepath=str(out/(slug+'.fbx')),use_selection=True,object_types={'MESH'},
                             use_mesh_modifiers=True,axis_forward='-Z',axis_up='Y',add_leaf_bones=False,
                             bake_anim=False,apply_unit_scale=True,global_scale=1.0,path_mode='AUTO')
    export_times['fbx_seconds']=time.perf_counter()-t
    cam,center,span=studio(lo,hi)
    views={}
    views['hero']=camera_view(cam,center,span,lo,hi)
    bpy.context.scene.render.filepath=str(out/'renders'/'hero.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(slug+'.blend')))
    for view in ('hero','rear'):
        if view=='rear':views[view]=camera_view(cam,center,span,lo,hi,True)
        bpy.context.scene.render.filepath=str(out/'renders'/(view+'.png'))
        render_start=stamp();rt=time.perf_counter()
        bpy.ops.render.render(write_still=True)
        views[view].update({'render_started_at_utc':render_start,'render_finished_at_utc':stamp(),'render_seconds':time.perf_counter()-rt})
    metadata={'set':'Set03','slug':slug,'theme':'Urban maintenance','status':'produced_unreviewed','review_status':'deferred_by_user',
              'reference':'REF/Set03/'+slug+'.png','created_with':'Blender 4.5.12, independent background process',
              'units':'meters','front_direction':'-Y','up_axis':'+Z','asset_collection':'ASSET','studio_collection':'STUDIO',
              'geometry_only_exports':True,'editable_named_components':True,'uv_method':'Per-component primitive unwraps and explicit parameterized/planar islands; no UV validator run.',
              'materials':[m.name for m in MATS.values()], 'design':design,'production_measurements':authored,
              'render_settings':{'engine':'Cycles','device':'CPU','threads':4,'samples':40,'denoising':True,'resolution':[960,960],'color_transform':'AgX','views':views},
              'started_at_utc':start,'finished_at_utc':stamp(),'production_seconds':time.perf_counter()-t0,'export_timings':export_times,
              'deferred_checks':['visual inspection','fresh BLEND reopen','GLB/FBX reimport','geometry validation','UV validation','independent review'],
              'limitations':['Static asset with solid-color PBR materials. No rig, animation, collision or LODs.','Reference proportions and small engineering details are artistically simplified.','Renders generated for future review and not inspected.']}
    (out/'metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print('SET03_PRODUCED '+slug+' '+json.dumps({'seconds':metadata['production_seconds'],'mesh_objects':len(objs)}),flush=True)


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if len(args)!=1 or args[0] not in BUILDERS:
        raise SystemExit('Usage: blender --background --factory-startup --threads 4 --python-exit-code 1 --python build.py -- SLUG')
    produce(args[0])
