"""Set04 original rounded aerial-logistics assets. Run only in private Blender.

No reference assets are imported. The four local concept images inform only the
silhouettes and palette. The finalization steps AUTHOR UVs and record production
measurements; this script does not perform a geometry or export review.
"""
import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
P = math.pi
ASSET = None
M = {}


def stamp():
    return datetime.now(timezone.utc).isoformat()


def material(name, color, metal=0.0, rough=.45, emission=0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Metallic'].default_value = metal
    bs.inputs['Roughness'].default_value = rough
    if emission:
        bs.inputs['Emission Color'].default_value = (*color, 1)
        bs.inputs['Emission Strength'].default_value = emission
    mat.diffuse_color = (*color, 1)
    return mat


def reset():
    global ASSET, M
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for c in list(bpy.data.collections):
        if c.name != 'Collection':
            bpy.data.collections.remove(c)
    c = bpy.data.collections.get('Collection')
    c.name = 'ASSET'
    ASSET = c
    M = {
        'ivory': material('Paint | warm ivory', (.69,.665,.575), .24,.42),
        'slate': material('Paint | muted slate blue', (.115,.205,.265), .35,.38),
        'graphite': material('Mechanisms | graphite', (.055,.068,.075), .55,.4),
        'steel': material('Hardware | brushed steel', (.25,.29,.30), .75,.31),
        'ochre': material('Safety | restrained ochre', (.91,.50,.11), .22,.37),
        'rubber': material('Tires and gaskets | charcoal rubber', (.024,.029,.032), .0,.76),
        'glass': material('Glazing | muted smoked blue', (.065,.15,.19), .45,.21),
        'screen': material('Equipment | inactive blue display', (.035,.085,.105), .25,.29),
        'lamp': material('Lighting | warm diffuser', (1,.70,.32), .10,.28,1.1),
        'white': material('Lighting | white diffuser', (.74,.88,.95), .10,.24,.75),
        'red': material('Lighting | tail red', (.45,.045,.025), .1,.3,.5),
        'concrete': material('Foundation | warm concrete', (.39,.405,.39), .0,.84),
        'deck': material('Service deck | dark gray', (.17,.205,.22), .25,.65),
    }
    scene=bpy.context.scene
    scene.unit_settings.system='METRIC'
    scene.unit_settings.scale_length=1.0
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU'
    scene.cycles.samples=40
    scene.cycles.use_denoising=True
    scene.render.threads_mode='FIXED'
    scene.render.threads=4
    scene.render.resolution_x=960
    scene.render.resolution_y=960
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGBA'
    scene.render.film_transparent=False
    scene.view_settings.view_transform='AgX'
    scene.view_settings.look='AgX - Medium High Contrast'
    bpy.context.preferences.filepaths.save_version=0


def asset_link(obj):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    ASSET.objects.link(obj)


def finish_obj(obj, name, mat, bevel=0, smooth=False):
    obj.name=name
    obj.data.name=name+' | mesh'
    asset_link(obj)
    obj.data.materials.append(M[mat] if isinstance(mat,str) else mat)
    if bevel:
        mod=obj.modifiers.new('Soft functional edges','BEVEL')
        mod.width=bevel
        mod.segments=3
        mod.limit_method='ANGLE'
    for p in obj.data.polygons:
        p.use_smooth=smooth
    if smooth:
        n=obj.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL')
        n.keep_sharp=True
        n.weight=45
    return obj


def box(name,loc,size,mat='ivory',bevel=.06,rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object
    o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if rot: o.rotation_euler=rot
    return finish_obj(o,name,mat,bevel,True)


def cyl(name,loc,radius,depth,mat='graphite',axis='Z',vertices=48,bevel=.02):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc)
    o=bpy.context.object
    if axis=='X': o.rotation_euler[1]=P/2
    if axis=='Y': o.rotation_euler[0]=P/2
    return finish_obj(o,name,mat,bevel,True)


def sphere(name,loc,scale,mat='ivory'):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=1,location=loc)
    o=bpy.context.object
    o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish_obj(o,name,mat,0,True)


def mesh(name,vertices,faces,mat='ivory',bevel=.02,smooth=True):
    data=bpy.data.meshes.new(name+' | mesh')
    data.from_pydata(vertices,[],faces)
    data.update()
    obj=bpy.data.objects.new(name,data)
    ASSET.objects.link(obj)
    return finish_obj(obj,name,mat,bevel,smooth)


def beam(name,a,b,width,mat='graphite',round=True):
    a,b=Vector(a),Vector(b)
    if round:
        o=cyl(name,(a+b)/2,width/2,(b-a).length,mat,bevel=min(.018,width*.08))
    else:
        o=box(name,(a+b)/2,(width,width,(b-a).length),mat,bevel=width*.2)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o


def ring(name,center,outer,inner,z0,z1,mat='ivory',start=0,end=2*P,segments=96,bevel=.02):
    """Closed annular wall or arc with actual open center, rather than a disk."""
    cx,cy=center
    steps=max(3,int(segments*abs(end-start)/(2*P)))
    verts=[]
    for i in range(steps+1):
        t=start+(end-start)*i/steps
        for r,z in ((outer,z0),(outer,z1),(inner,z1),(inner,z0)):
            verts.append((cx+r*math.cos(t),cy+r*math.sin(t),z))
    faces=[]
    for i in range(steps):
        k=i*4
        for j in range(4): faces.append((k+j,k+(j+1)%4,k+4+(j+1)%4,k+4+j))
    faces += [(3,2,1,0),(4*steps,4*steps+1,4*steps+2,4*steps+3)]
    return mesh(name,verts,faces,mat,bevel)


def torus(name,loc,major,minor,mat='steel',rot=None):
    bpy.ops.mesh.primitive_torus_add(major_segments=64,minor_segments=12,location=loc,major_radius=major,minor_radius=minor)
    o=bpy.context.object
    if rot: o.rotation_euler=rot
    return finish_obj(o,name,mat,0,True)


def yz_prism(name,points,width,mat='ivory',bevel=.06,xcenter=0):
    v=[(xcenter+x,y,z) for x in (-width/2,width/2) for y,z in points]
    n=len(points)
    f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    f += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,v,f,mat,bevel)


def front_panel(name,x,y,z,w,h,mat='glass',bevel=.025):
    return box(name,(x,y,z),(w,.055,h),mat,bevel)


def vent_front(name,x,y,z,w,h,bars=5,frame='slate'):
    front_panel(name+' surround',x,y,z,w,h,frame,.04)
    front_panel(name+' recess',x,y-.035,z,w*.86,h*.78,'graphite',.015)
    for i in range(bars):
        zz=z-h*.29+(i/(max(bars-1,1)))*h*.58
        box(name+f' louver {i+1:02}',(x,y-.075,zz),(w*.76,.055,.032),'steel',.01)


def vent_side(name,x,y,z,w,h,bars=5):
    box(name+' frame',(x,y,z),(.065,w,h),'slate',.04)
    side=1 if x>0 else -1
    box(name+' recess',(x+side*.038,y,z),(.035,w*.86,h*.78),'graphite',.015)
    for i in range(bars):
        zz=z-h*.29+(i/(max(bars-1,1)))*h*.58
        box(name+f' louver {i+1:02}',(x+side*.068,y,zz),(.04,w*.76,.035),'steel',.009)


def bolt(name,loc,r=.035,axis='Y'):
    return cyl(name,loc,r,.025,'steel',axis,vertices=12,bevel=.006)


def drone():
    # Scale: compact uncrewed freight carrier with crosswise twin ducts.
    box('Central rounded equipment fuselage',(0,0,2.30),(1.36,2.18,.82),'ivory',.29)
    box('Upper avionics cover',(0,.10,2.73),(1.05,1.70,.15),'ivory',.09)
    box('Transverse load beam',(0,.05,2.27),(4.15,.75,.49),'ivory',.15)
    box('Ventral load saddle',(0,.05,1.80),(1.05,1.35,.22),'graphite',.08)
    box('Nose slate fairing',(0,-.93,2.29),(1.10,.43,.59),'slate',.17)
    front_panel('Navigation sensor ochre bezel',0,-1.168,2.24,.72,.40,'ochre',.11)
    front_panel('Navigation sensor housing',0,-1.208,2.24,.61,.31,'graphite',.08)
    cyl('Navigation primary sensor',(.14,-1.255,2.24),.105,.055,'glass','Y',bevel=.012)
    cyl('Navigation secondary sensor',(-.19,-1.255,2.24),.049,.05,'glass','Y',bevel=.008)
    front_panel('Navigation status strip',0,-1.152,2.55,.38,.065,'white',.025)
    vent_front('Rear fuselage cooling',0,1.11,2.30,.83,.39,5)
    # Top cooling fins and an understated safety panel.
    box('Dorsal cooler well',(0,.22,2.821),(.65,.83,.035),'graphite',.04)
    for i in range(7):
        box(f'Dorsal fin {i+1}',(0,-.10+i*.105,2.85),(.56,.038,.04),'slate',.012)
    box('Dorsal service latch',(0,.79,2.83),(.34,.16,.035),'ochre',.025)
    for side in (-1,1):
        x=side*2.08
        tag='Port' if side<0 else 'Starboard'
        box(tag+' beam collar',(side*.98,.05,2.28),(.21,.83,.58),'graphite',.07)
        ring(tag+' rotor duct shell',(x,.05),1.19,.98,2.12,2.57,'ivory',bevel=.045)
        ring(tag+' upper protection lip',(x,.05),1.21,.97,2.54,2.65,'slate',bevel=.025)
        ring(tag+' lower duct rim',(x,.05),1.16,.995,2.08,2.17,'graphite',bevel=.025)
        ring(tag+' duct ochre band',(x,.05),1.195,1.177,2.43,2.48,'ochre',bevel=.006)
        cyl(tag+' motor spindle',(x,.05,2.37),.23,.31,'graphite',bevel=.045)
        cyl(tag+' motor crown',(x,.05,2.55),.17,.045,'ochre',bevel=.012)
        for i in range(4):
            a=P/4+i*P/2
            # Blunt paddle blades and visible underneath radial bracing.
            o=box(tag+f' blunt rotor blade {i+1}',(x+.58*math.cos(a),.05+.58*math.sin(a),2.43),(.83,.25,.07),'graphite',.065)
            o.rotation_euler[2]=a
            beam(tag+f' radial motor support {i+1}',(x+.16*math.cos(a),.05+.16*math.sin(a),2.20),(x+.98*math.cos(a),.05+.98*math.sin(a),2.16),.075,'steel')
        for j,a in enumerate((-.5,1.5,2.75)):
            px=x+1.196*math.cos(a); py=.05+1.196*math.sin(a)
            o=box(tag+f' duct maintenance inset {j+1}',(px,py,2.28),(.32,.035,.15),'graphite',.035)
            o.rotation_euler[2]=a-P/2
        # Two rigid brackets each side attach the single crate and landing gear.
        for y in (-.60,.66):
            beam(tag+f' cradle diagonal {y}',(side*.55,y,1.85),(side*.89,y,1.48),.13,'graphite',False)
            beam(tag+f' cradle upright {y}',(side*.89,y,1.48),(side*.89,y,.69),.12,'graphite',False)
            cyl(tag+f' cradle upper pivot {y}',(side*.90,y,1.49),.10,.14,'steel','X',bevel=.018)
            beam(tag+f' landing strut {y}',(side*.89,y,.84),(side*1.22,y,.19),.15,'graphite')
        beam(tag+' landing skid',(side*1.23,-1.08,.15),(side*1.23,1.14,.15),.22,'graphite')
        sphere(tag+' skid fore cap',(side*1.23,-1.08,.15),(.11,.11,.11),'rubber')
        sphere(tag+' skid aft cap',(side*1.23,1.14,.15),(.11,.11,.11),'rubber')
    box('Single removable belly cargo crate',(0,.03,1.17),(1.66,1.51,.88),'ivory',.12)
    box('Cargo lid',(0,.03,1.61),(1.69,1.54,.10),'ivory',.06)
    box('Cargo cradle base',(0,.03,.70),(1.88,1.72,.13),'slate',.05)
    for x in (-.57,.57):
        box(f'Cargo front restraint {x}',(x,-.755,1.18),(.085,.08,.99),'graphite',.025)
        box(f'Cargo lid restraint {x}',(x,.03,1.675),(.085,1.58,.045),'graphite',.015)
        box(f'Cargo rear restraint {x}',(x,.815,1.18),(.085,.08,.99),'graphite',.025)
        front_panel(f'Cargo latch {x}',x,-.807,1.44,.12,.18,'ochre',.025)
    front_panel('Cargo front handle frame',0,-.775,1.20,.39,.23,'graphite',.045)
    front_panel('Cargo front handle insert',0,-.825,1.20,.28,.10,'ochre',.025)
    for s in (-1,1):
        box(f'Cargo side recessed handle {s}',(s*.851,.03,1.25),(.045,.34,.20),'graphite',.035)
        box(f'Cargo side grip {s}',(s*.884,.03,1.25),(.05,.24,.07),'ochre',.02)
    return {'design_dimensions_m':[6.58,2.45,2.89],'features':['two open protective rotor ducts with four blunt blades each','central unmanned sensor fuselage','single cargo crate and visible rigid cradle','splayed landing struts with two short skids']}


def wheel(tag,x,y,z,r=.54):
    side=1 if x>0 else -1
    cyl(tag+' tire',(x,y,z),r,.31,'rubber','X',vertices=64,bevel=.075)
    cyl(tag+' rim',(x+side*.17,y,z),r*.68,.045,'steel','X',bevel=.025)
    cyl(tag+' hub',(x+side*.202,y,z),r*.36,.055,'graphite','X',bevel=.018)
    torus(tag+' sidewall ring',(x+side*.163,y,z),r*.83,.011,'graphite',(0,P/2,0))
    for i in range(8):
        a=i*P/4
        bolt(tag+f' rim bolt {i}',(x+side*.235,y+r*.46*math.sin(a),z+r*.46*math.cos(a)),.029,'X')
    for i in range(20):
        a=i*2*P/20
        o=box(tag+f' tread block {i+1:02}',(x,y+(r-.005)*math.sin(a),z+(r-.005)*math.cos(a)),(.29,.11,.045),'rubber',.014)
        o.rotation_euler[0]=-a


def arch_fender(tag,x,y,z):
    # Rounded arch shell in the YZ plane leaving the lower tire exposed.
    verts=[]; steps=24
    for i in range(steps+1):
        a=-.12+(P+.24)*i/steps
        for xx,r in ((x-.15,.66),(x+.15,.66),(x+.15,.81),(x-.15,.81)):
            verts.append((xx,y+r*math.cos(a),z+r*math.sin(a)))
    faces=[]
    for i in range(steps):
        for j in range(4): faces.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
    faces += [(3,2,1,0),(steps*4,steps*4+1,steps*4+2,steps*4+3)]
    return mesh(tag+' rounded wheel-arch fender',verts,faces,'slate',.035)


def tug():
    box('Low structural chassis',(0,0,.65),(1.84,3.88,.40),'graphite',.13)
    box('Ivory continuous waist',(0,0,1.10),(1.98,3.85,.50),'ivory',.17)
    box('Front slate bumper',(0,-1.98,.72),(2.12,.26,.55),'slate',.10)
    box('Rear slate bumper',(0,1.99,.74),(2.12,.25,.52),'slate',.09)
    # Short hood and substantial enclosed cabin with a raked front windshield.
    yz_prism('Sloping rounded short hood',[(-1.95,.99),(-1.95,1.30),(-1.14,1.56),(-.76,1.38),(-.76,.99)],1.98,'ivory',.12)
    yz_prism('Enclosed cabin shell',[(-1.19,1.18),(-.85,2.52),(.53,2.52),(.73,1.18)],1.78,'ivory',.13)
    box('Shallow rounded cab roof',(0,-.12,2.55),(1.94,1.66,.18),'ivory',.12)
    windshield=box('Wide windshield rubber surround',(0,-1.025,1.99),(1.62,.07,1.05),'rubber',.075)
    windshield.rotation_euler[0]=-.245
    windshield=box('Wide smoked front glazing',(0,-1.073,1.99),(1.48,.035,.91),'glass',.065)
    windshield.rotation_euler[0]=-.245
    beam('Windshield central mullion',(0,-1.20,1.53),(0,-.975,2.46),.034,'graphite',False)
    for side in (-1,1):
        x=side*.907
        door=yz_prism(f'Cab door gasket {side}',[(-.94,1.30),(-.71,2.41),(.38,2.41),(.50,1.30)],.025,'rubber',.055,x)
        yz_prism(f'Cab side glazing {side}',[(-.81,1.70),(-.66,2.32),(.26,2.32),(.32,1.70)],.025,'glass',.05,x+side*.023)
        box(f'Cab lower door panel {side}',(x+side*.025,-.19,1.48),(.035,1.03,.29),'slate',.04)
        box(f'Door handle {side}',(x+side*.06,.28,1.66),(.035,.06,.20),'graphite',.018)
        box(f'Cab step lower {side}',(side*1.015,.61,.40),(.35,.63,.13),'slate',.04)
        box(f'Cab step upper {side}',(side*1.015,.61,.66),(.35,.63,.13),'slate',.04)
        box(f'Lower step safety edge {side}',(side*1.20,.61,.43),(.035,.57,.055),'ochre',.012)
        box(f'Upper step safety edge {side}',(side*1.20,.61,.69),(.035,.57,.055),'ochre',.012)
        beam(f'Mirror support lower {side}',(side*.95,-.88,1.58),(side*1.13,-1.0,1.82),.048,'graphite')
        beam(f'Mirror support upright {side}',(side*1.13,-1.0,1.82),(side*1.13,-1.0,2.17),.048,'graphite')
        box(f'Mirror housing {side}',(side*1.14,-1.02,2.12),(.20,.12,.36),'graphite',.065)
        box(f'Mirror face {side}',(side*1.14,-.951,2.12),(.15,.02,.27),'steel',.035)
        for yy,tag in ((-1.25,'front'),(1.28,'rear')):
            wheel(f'{tag} wheel {side}',side*.96,yy,.55)
            arch_fender(f'{tag} {side}',side*.98,yy,.55)
        vent_side(f'Rear power compartment grille {side}',side*1.006,1.30,1.27,.72,.33,4)
        box(f'Rear deck rubber tread {side}',(side*.48,1.29,1.39),(.75,1.05,.035),'rubber',.035)
        # Each front light is framed, with a separate amber indicator.
        front_panel(f'Front lamp surround {side}',side*.69,-2.018,1.18,.42,.25,'graphite',.06)
        front_panel(f'Headlight diffuser {side}',side*.62,-2.058,1.18,.22,.17,'white',.04)
        front_panel(f'Turn indicator {side}',side*.86,-2.058,1.18,.10,.17,'ochre',.025)
        front_panel(f'Bumper driving light socket {side}',side*.72,-2.126,.72,.24,.22,'graphite',.055)
        cyl(f'Bumper driving light {side}',(side*.72,-2.16,.72),.073,.03,'white','Y',bevel=.012)
        front_panel(f'Rear tail light {side}',side*.74,2.13,1.08,.25,.13,'red',.03)
        box(f'Roof marker housing {side}',(side*.72,-.87,2.58),(.26,.13,.15),'graphite',.04)
        front_panel(f'Roof marker lens {side}',side*.72,-.95,2.58,.18,.08,'white',.022)
    vent_front('Front radiator',0,-2.003,1.17,.75,.29,4)
    front_panel('Rear cabin glazing',0,.658,2.02,1.43,.76,'glass',.065)
    box('Rear cabin lower apron',(0,.74,1.51),(1.62,.13,.30),'ivory',.06)
    # Sloped wiper; low engine cover behind the cab.
    beam('Windshield wiper arm',(-.50,-1.25,1.57),(.17,-1.115,2.09),.023,'graphite')
    beam('Windshield wiper blade',(.10,-1.12,1.94),(.29,-1.07,2.25),.035,'graphite')
    box('Rear power cover',(0,1.05,1.50),(1.48,.59,.28),'ivory',.10)
    for i in range(5): box(f'Rear engine top fin {i}',(0,.84+i*.10,1.66),(.77,.034,.025),'graphite',.008)
    cyl('Beacon rubber foot',(0,.05,2.70),.15,.075,'graphite',bevel=.018)
    cyl('Amber warning beacon',(0,.05,2.84),.12,.22,'ochre',vertices=32,bevel=.04)
    # Front recovery clevis and the heavy rear towing mechanism.
    box('Front recovery mount',(0,-2.18,.71),(.39,.19,.37),'graphite',.05)
    for z in (.60,.82): box(f'Front clevis plate {z}',(0,-2.34,z),(.32,.29,.08),'steel',.04)
    cyl('Front clevis vertical pin',(0,-2.40,.71),.055,.35,'graphite',bevel=.012)
    box('Rear towing chassis mount',(0,1.90,1.38),(.70,.43,.20),'graphite',.06)
    for x in (-.27,.27):
        box(f'Rear towing upright {x}',(x,1.97,1.59),(.13,.26,.42),'graphite',.04)
    cyl('Rear coupling cross pin',(0,1.99,1.57),.09,.78,'steel','X',bevel=.02)
    torus('Raised rear towing eye',(0,1.99,1.97),.145,.065,'graphite',(P/2,0,0))
    box('Towing eye stem',(0,1.99,1.74),(.20,.12,.24),'graphite',.055)
    box('Coupler safety lever',(.40,1.99,1.62),(.12,.20,.32),'ochre',.03)
    return {'design_dimensions_m':[2.48,4.50,2.99],'features':['four sturdy wheels with tread blocks','short raked hood and broad enclosed glazed cab','side steps, mirrors and compact beacon','heavy raised rear towing eye and front recovery clevis']}


def dome_surface(name,rings,mat='ivory',start=0,end=2*P,segments=96,thick=.12):
    # Continuous annular roof shell with central cap and thickness.
    verts=[]
    for zoff in (0,-thick):
        for r,z in rings:
            for i in range(segments+1):
                a=start+(end-start)*i/segments
                verts.append((r*math.cos(a),r*math.sin(a),z+zoff))
    n=segments+1; k=len(rings); layer=n*k
    f=[]
    for s in range(2):
        off=s*layer
        for j in range(k-1):
            for i in range(segments):
                q=(off+j*n+i,off+j*n+i+1,off+(j+1)*n+i+1,off+(j+1)*n+i)
                f.append(q if s==0 else tuple(reversed(q)))
    for j in (0,k-1):
        for i in range(segments):
            a=j*n+i;b=j*n+i+1
            f.append((a,b,b+layer,a+layer))
    for i in (0,segments):
        for j in range(k-1):
            a=j*n+i;b=(j+1)*n+i
            f.append((a,b,b+layer,a+layer))
    return mesh(name,verts,f,mat,.025)


def hangar():
    r=4.60; start=-P/6; end=7*P/6
    cyl('Circular facility foundation',(0,0,.12),4.78,.24,'concrete',vertices=128,bevel=.07)
    cyl('Recessed dark service pad',(0,0,.255),4.33,.12,'deck',vertices=128,bevel=.03)
    ring('Inset landing guide',(0,0),3.17,3.09,.318,.333,'ochre',segments=128,bevel=.005)
    ring('Central service pad seam',(0,0),2.23,2.20,.319,.328,'graphite',segments=128,bevel=.003)
    cyl('Central service circle',(0,0,.324),2.18,.014,'deck',vertices=96,bevel=.006)
    for i in range(12):
        a=2*P*i/12
        beam(f'Radial pad joint {i+1}',(3.25*math.cos(a),3.25*math.sin(a),.324),(4.26*math.cos(a),4.26*math.sin(a),.324),.016,'graphite',False)
    ring('Thick circular hangar wall',(0,0),r,4.25,.33,2.53,'ivory',start,end,segments=120,bevel=.055)
    ring('Slate lower wall skirt',(0,0),4.64,4.22,.33,.73,'slate',start,end,segments=120,bevel=.025)
    ring('Circular outer cornice',(0,0),4.69,4.18,2.47,2.66,'slate',start,end,segments=120,bevel=.04)
    # The complete low roof closes above the large open front sector.
    profile=[(.48,3.76),(1.10,3.72),(2.0,3.55),(3.0,3.22),(4.0,2.81),(4.53,2.61)]
    dome_surface('Softly domed continuous roof',profile)
    cyl('Roof central hub lower',(0,0,3.77),.79,.17,'graphite',vertices=64,bevel=.04)
    cyl('Roof central service cap',(0,0,3.88),.71,.13,'slate',vertices=64,bevel=.045)
    ring('Central hub fine rim',(0,0),.55,.52,3.949,3.962,'steel',bevel=.003)
    cyl('Central cap inset',(0,0,3.96),.24,.018,'graphite',bevel=.01)
    # Radial roof ribs are separate shaped strips, with ochre service segments.
    for i in range(8):
        a=i*P/4
        radials=[(.80,3.80),(1.15,3.77),(2.05,3.60),(3.05,3.27),(4.08,2.86),(4.51,2.68)]
        verts=[]
        for rr,zz in radials:
            for dw in (-.095,.095):
                verts.append((rr*math.cos(a)-dw*math.sin(a),rr*math.sin(a)+dw*math.cos(a),zz))
        faces=[(2*j,2*j+1,2*j+3,2*j+2) for j in range(len(radials)-1)]
        o=mesh(f'Roof radial rib {i+1}',verts,faces,'slate',0)
        sol=o.modifiers.new('Rib plate thickness','SOLIDIFY');sol.thickness=.08
        b=o.modifiers.new('Rounded rib edges','BEVEL');b.width=.025;b.segments=3
        if i%2==0:
            rr=3.35
            o=box(f'Roof rib service marker {i+1}',(rr*math.cos(a),rr*math.sin(a),3.17),(.52,.20,.05),'ochre',.015)
            o.rotation_euler[1]=.37;o.rotation_euler[2]=a
    # Broad opening: stout end piers, header and small guide lights.
    for side in (-1,1):
        x=side*3.91;y=-2.28
        box(f'Opening portal pier {side}',(x,y,1.47),(.47,.64,2.45),'ivory',.14)
        box(f'Opening inner protective post {side}',(x-side*.26,y-.13,1.44),(.20,.38,2.20),'graphite',.07)
        front_panel(f'Portal ochre guard {side}',x,y-.35,.82,.25,.79,'ochre',.05)
        front_panel(f'Portal vertical guide lamp {side}',x-side*.25,y-.35,1.85,.055,.47,'lamp',.015)
        bolt(f'Portal foot fastener {side}',(x,y-.37,.43),.04,'Y')
    # Curved front lintel follows the exposed forward perimeter.
    ring('Broad curved opening lintel',(0,0),4.62,4.28,2.44,2.64,'slate',7*P/6,11*P/6,segments=120,bevel=.04)
    for a in (P*1.29,P*1.5,P*1.71):
        x=4.61*math.cos(a);y=4.61*math.sin(a)
        o=box('Opening header lamp '+str(round(a,2)),(x,y,2.48),(.40,.07,.10),'lamp',.025)
        o.rotation_euler[2]=a-P/2
    # Interior stiffeners and service cabinets remain part of the facility.
    for i,a in enumerate([-.1,.45,1.0,1.55,2.1,2.65,3.2]):
        x=4.19*math.cos(a);y=4.19*math.sin(a)
        o=box(f'Interior vertical stiffener {i+1}',(x,y,1.38),(.17,.15,2.10),'slate',.04)
        o.rotation_euler[2]=a
        o=box(f'Interior service light {i+1}',(4.13*math.cos(a),4.13*math.sin(a),.99),(.30,.06,.08),'lamp',.02)
        o.rotation_euler[2]=a-P/2
    # Wall seams are restrained regularly spaced steel strips.
    for i in range(13):
        a=start+.08+(end-start-.16)*i/12
        o=box(f'Outer shell panel joint {i+1}',(4.611*math.cos(a),4.611*math.sin(a),1.56),(.018,.035,1.68),'steel',.005)
        o.rotation_euler[2]=a-P/2
    # Tangential side maintenance door, clearly separate from the open bay.
    a=-.18; rr=4.64
    for name,width,dep,height,z,mat in [('Service doorway surround',.88,.13,1.76,1.26,'slate'),('Service doorway leaf',.70,.15,1.55,1.21,'graphite')]:
        o=box(name,(rr*math.cos(a),rr*math.sin(a),z),(dep,width,height),mat,.09)
        o.rotation_euler[2]=a
    beam('Service door ochre handle',(4.76*math.cos(a),4.76*math.sin(a)-.24,.98),(4.76*math.cos(a),4.76*math.sin(a)-.24,1.35),.045,'ochre')
    for a in (.55,1.55,2.55):
        x=4.64*math.cos(a);y=4.64*math.sin(a)
        o=box(f'External vent frame {a}',(x,y,1.90),(.08,.79,.40),'slate',.045);o.rotation_euler[2]=a
        o=box(f'External vent recess {a}',(x+.052*math.cos(a),y+.052*math.sin(a),1.90),(.04,.65,.28),'graphite',.02);o.rotation_euler[2]=a
        for j in range(4):
            o=box(f'External vent blade {a} {j}',(x+.08*math.cos(a),y+.08*math.sin(a),1.80+j*.065),(.04,.61,.025),'steel',.008);o.rotation_euler[2]=a
    # Short roof exhaust behind the centre; no scenery or detached props.
    x=2.5;y=1.5
    cyl('Roof exhaust plinth',(x,y,3.29),.45,.22,'slate',bevel=.04)
    cyl('Roof exhaust drum',(x,y,3.66),.32,.60,'ivory',bevel=.055)
    cyl('Roof exhaust top collar',(x,y,3.98),.36,.10,'slate',bevel=.025)
    cyl('Roof exhaust top dark opening',(x,y,4.035),.26,.018,'graphite',bevel=.008)
    for j in range(4): ring(f'Exhaust horizontal louver {j}',(x,y),.335,.30,3.45+j*.11,3.49+j*.11,'graphite',bevel=.008)
    ring('Exhaust ochre maintenance band',(x,y),.337,.315,3.89,3.95,'ochre',bevel=.01)
    # Embedded threshold plates belong to the circular hangar foundation.
    for i in range(7):
        a=7*P/6+(2*P/3)*(i+.5)/7
        o=box(f'Front threshold grate {i+1}',(4.12*math.cos(a),4.12*math.sin(a),.332),(.44,.34,.026),'graphite',.025)
        o.rotation_euler[2]=a
        for j in range(4):
            px=4.12*math.cos(a)+(j-1.5)*.08*math.cos(a)
            py=4.12*math.sin(a)+(j-1.5)*.08*math.sin(a)
            o=box(f'Threshold grate bar {i+1}-{j}',(px,py,.35),(.025,.29,.018),'steel',.005);o.rotation_euler[2]=a
    return {'design_dimensions_m':[9.56,9.56,4.05],'features':['low circular thick-walled hangar with broad open front sector','segmented shallow dome with radial ribs','recessed empty service pad and threshold grates','side service door and short roof exhaust']}


def rounded_outline(width,depth,radius,segments=8):
    points=[]
    for cx,cy,start in ((width/2-radius,depth/2-radius,0),(-width/2+radius,depth/2-radius,P/2),(-width/2+radius,-depth/2+radius,P),(width/2-radius,-depth/2+radius,3*P/2)):
        for i in range(segments+1):
            a=start+i*P/2/segments
            points.append((cx+radius*math.cos(a),cy+radius*math.sin(a)))
    return points


def rounded_band(name,width,depth,radius,z0,z1,thick,mat='slate',center=(0,0),bevel=.025):
    outer=rounded_outline(width,depth,radius)
    inner=rounded_outline(width-2*thick,depth-2*thick,max(.04,radius-thick))
    verts=[]
    for z,pts in ((z0,outer),(z1,outer),(z1,inner),(z0,inner)):
        verts.extend([(x+center[0],y+center[1],z) for x,y in pts])
    n=len(outer);faces=[]
    for i in range(n):
        q=(i+1)%n
        for j in range(4):
            jj=(j+1)%4
            faces.append((j*n+i,j*n+q,jj*n+q,jj*n+i))
    return mesh(name,verts,faces,mat,bevel)


def control():
    # Broad low two-storey control room plus an attached one-storey utility annex.
    box('Main raised foundation',(-.6,0,.18),(8.05,5.30,.36),'concrete',.18)
    box('Main lower rounded structure',(-.6,0,1.63),(7.80,5.02,2.73),'ivory',.36)
    rounded_band('Main slate lower skirt',7.88,5.10,.40,.38,.85,.10,'slate',(-.6,0))
    rounded_band('Main ochre course',7.90,5.12,.41,.84,.89,.07,'ochre',(-.6,0),.008)
    rounded_band('Main eave cap',8.02,5.26,.48,2.81,3.04,.16,'slate',(-.6,0),.045)
    # Upper room: opaque glazing is a deliberate stylized material, with separate mullions.
    box('Upper room sill',(-.6,0,3.09),(6.91,4.54,.32),'ivory',.32)
    lower=rounded_outline(6.56,4.18,.50,8)
    upper=rounded_outline(7.03,4.52,.58,8)
    verts=[(x-.6,y,z) for pts,z in ((lower,3.20),(upper,4.55)) for x,y in pts]
    n=len(lower)
    faces=[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh('Wide splayed control-room glazing',verts,faces,'glass',0)
    # 24 wide glazed sectors, with continuous restrained rounded corners.
    for i in range(0,n,2):
        a=Vector((lower[i][0]-.6,lower[i][1],3.18))
        b=Vector((upper[i][0]-.6,upper[i][1],4.58))
        beam(f'Upper room glazing mullion {i//2+1:02}',a,b,.065,'slate',False)
    rounded_band('Upper window lower gasket',6.63,4.25,.52,3.18,3.25,.06,'graphite',(-.6,0),.012)
    rounded_band('Upper window top gasket',7.09,4.58,.60,4.50,4.59,.06,'graphite',(-.6,0),.012)
    box('Shallow broad upper roof',(-.6,0,4.66),(7.64,5.12,.28),'ivory',.32)
    rounded_band('Upper slate fascia',7.67,5.15,.49,4.66,4.86,.17,'slate',(-.6,0),.04)
    rounded_band('Upper ochre fine fascia stripe',7.68,5.16,.50,4.64,4.69,.06,'ochre',(-.6,0),.008)
    box('Roof raised inset deck',(-.6,0,4.82),(6.90,4.32,.09),'deck',.32)
    # Lower floor front glazing, framed on the blank side/rear walls too.
    for i,x in enumerate((-3.05,-1.25,1.98)):
        front_panel(f'Ground-floor front window gasket {i+1}',x,-2.532,1.66,1.33,1.17,'graphite',.10)
        front_panel(f'Ground-floor front window glazing {i+1}',x,-2.57,1.66,1.17,1.01,'glass',.065)
        beam(f'Ground-floor front mullion {i+1}',(x,-2.606,1.17),(x,-2.606,2.14),.036,'slate',False)
        front_panel(f'Front wall lamp backing {i+1}',x,-2.57,2.48,.32,.13,'graphite',.03)
        front_panel(f'Front wall lamp {i+1}',x,-2.615,2.48,.24,.065,'lamp',.018)
    for i,x in enumerate((-3.05,-1.15,.80,2.25)):
        front_panel(f'Rear ground-floor window surround {i}',x,2.535,1.67,1.18,1.04,'slate',.08)
        front_panel(f'Rear ground-floor glazing {i}',x,2.58,1.67,1.04,.90,'glass',.055)
    for j,y in enumerate((-.95,.95)):
        box(f'West ground-floor window surround {j}',(-4.523,y,1.66),(.06,1.40,1.14),'graphite',.08)
        box(f'West ground-floor glazing {j}',(-4.56,y,1.66),(.035,1.25,1.0),'glass',.055)
    # Main entrance aligned with an integral stoop and three broad treads.
    x=.46
    front_panel('Entrance surround',x,-2.59,1.43,1.63,2.16,'slate',.12)
    front_panel('Entrance dark inset',x,-2.65,1.42,1.38,1.96,'graphite',.065)
    for s in (-1,1):
        front_panel(f'Entry door leaf {s}',x+s*.345,-2.69,1.42,.65,1.90,'slate',.035)
        front_panel(f'Entry door glazed panel {s}',x+s*.345,-2.732,1.66,.48,1.15,'glass',.025)
        beam(f'Entry pull handle {s}',(x+s*.11,-2.79,1.27),(x+s*.11,-2.79,1.66),.035,'steel')
    box('Entrance shallow canopy',(x,-2.80,2.58),(2.16,.79,.18),'slate',.085)
    for s in (-1,1):
        front_panel(f'Entrance wall sconce {s}',x+s*.96,-2.60,1.95,.09,.40,'lamp',.02)
    box('Entrance upper stoop',(x,-2.95,.33),(2.26,.85,.47),'concrete',.045)
    for j in range(3):
        # Extend downward toward front, with distinct nosing strips.
        y=-3.40-j*.29;h=.44-j*.14
        box(f'Entry stair tread {j+1}',(x,y,h/2),(2.26,.33,h),'concrete',.025)
        box(f'Entry stair nosing {j+1}',(x,y-.15,h+.008),(2.20,.035,.025),'steel',.007)
    for s in (-1,1):
        xx=x+s*1.10
        beam(f'Entry rail rear upright {s}',(xx,-2.80,.56),(xx,-2.80,1.22),.048,'steel')
        beam(f'Entry rail front upright {s}',(xx,-3.93,.08),(xx,-3.93,.77),.048,'steel')
        beam(f'Entry rail slope {s}',(xx,-2.80,1.22),(xx,-3.93,.77),.06,'ochre')
        beam(f'Entry rail middle {s}',(xx,-2.80,.92),(xx,-3.93,.47),.038,'steel')
    # The one-storey right-side annex is structurally joined to the main block.
    box('Utility annex foundation',(4.44,.30,.14),(2.75,4.57,.28),'concrete',.12)
    box('Attached utility annex',(4.42,.30,1.43),(2.58,4.38,2.56),'ivory',.22)
    box('Annex slate roof cap',(4.42,.30,2.76),(2.74,4.54,.20),'slate',.17)
    rounded_band('Annex slate lower skirt',2.66,4.46,.25,.30,.73,.08,'slate',(4.42,.30),.02)
    front_panel('Annex service door surround',4.60,-1.922,1.39,.94,1.95,'graphite',.08)
    front_panel('Annex service door leaf',4.60,-1.963,1.39,.79,1.81,'slate',.055)
    vent_front('Annex door intake',4.60,-2.008,1.53,.44,.45,6)
    beam('Annex door handle',(4.87,-2.063,1.14),(4.87,-2.063,1.37),.03,'steel')
    front_panel('Annex service entry lamp',4.60,-1.98,2.42,.32,.09,'lamp',.025)
    for xx in (4.03,5.16):
        cyl(f'Annex safety bollard {xx}',(xx,-2.27,.45),.065,.72,'ochre',bevel=.03)
        cyl(f'Annex bollard base {xx}',(xx,-2.27,.105),.105,.08,'graphite',bevel=.015)
    box('Exterior electrical cabinet',(3.45,-1.98,1.08),(.47,.24,.75),'ochre',.055)
    front_panel('Electrical cabinet inset',3.45,-2.12,1.11,.31,.52,'ivory',.025)
    for zz in (.98,1.12,1.26): front_panel(f'Cabinet small vent {zz}',3.45,-2.15,zz,.20,.025,'graphite',.006)
    # Roof air-handling plant with oversized simple louvers, conduit to annex.
    box('Annex HVAC feet',(4.38,.64,2.94),(1.55,1.40,.15),'graphite',.04)
    box('Annex roof HVAC enclosure',(4.38,.64,3.31),(1.40,1.23,.64),'ivory',.08)
    vent_front('HVAC forward intake',4.38,.003,3.31,1.10,.45,6)
    vent_side('HVAC outer intake',5.10,.64,3.31,.90,.44,5)
    for xx in (3.25,3.42):
        beam(f'Utility riser vertical {xx}',(xx,-1.91,.40),(xx,-1.91,3.11),.085,'steel')
        beam(f'Utility riser roof return {xx}',(xx,-1.91,3.11),(xx,-.10,3.11),.085,'steel')
        sphere(f'Utility pipe front elbow {xx}',(xx,-1.91,3.11),(.056,.056,.056),'steel')
        for zz in (.75,1.45,2.20): box(f'Riser wall clamp {xx} {zz}',(xx,-1.93,zz),(.15,.08,.055),'graphite',.01)
    # Low navigation equipment rather than a tall control tower.
    box('Navigation unit service plinth',(.35,.70,4.99),(1.58,1.45,.27),'ivory',.11)
    cyl('Navigation drum base',(.35,.70,5.30),.40,.39,'slate',bevel=.05)
    ring('Navigation drum collar',(.35,.70),.45,.37,5.41,5.48,'graphite',bevel=.015)
    sphere('Blunt navigation radome',(.35,.70,5.84),(.49,.49,.50),'ivory')
    for xx,yy,hh in ((-2.55,.60,1.20),(1.50,1.10,1.59),(-.90,1.43,1.32)):
        cyl(f'Roof antenna pedestal {xx}',(xx,yy,4.94),.095,.20,'slate',bevel=.018)
        cyl(f'Roof antenna mast {xx}',(xx,yy,5.0+hh/2),.021,hh,'steel',vertices=20,bevel=.006)
        box(f'Roof antenna receiver {xx}',(xx,yy,5.35),(.10,.10,.31),'graphite',.025)
    for xx in (-.35,1.05):
        beam(f'Navigation service guard post {xx}',(xx,.08,5.05),(xx,.08,5.49),.034,'steel')
    beam('Navigation service guard top',(-.35,.08,5.49),(1.05,.08,5.49),.04,'steel')
    for i,x in enumerate((-2.8,-1.45,.1,1.6)):
        box(f'Upper room front console silhouette {i}',(x,-1.63,3.42),(.75,.37,.32),'graphite',.045)
        box(f'Upper room monitor silhouette {i}',(x,-1.61,3.72),(.40,.06,.29),'screen',.025)
    return {'design_dimensions_m':[10.43,6.57,6.60],'features':['low broad two-storey rounded control building','wide splayed upper glazing with separate mullions','entry canopy, stairs and handrails','attached utility annex with roof HVAC and service risers','blunt low navigation radome and simple aerials']}


BUILDERS={'twin_rotor_cargo_drone':drone,'airport_cargo_tug':tug,'circular_drone_hangar':hangar,'low_control_building':control}


def author_uvs():
    """Apply authored rounding and create separate packed surface islands per part.

    This is an authoring operator, not a post-production UV validator.
    """
    objects=[o for o in ASSET.objects if o.type=='MESH']
    for i,o in enumerate(objects):
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active=o
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        for mod in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.025,area_weight=.3,correct_aspect=True,scale_to_bounds=True)
        bpy.ops.object.mode_set(mode='OBJECT')
        if o.data.uv_layers.active:
            o.data.uv_layers.active.name='SurfaceUV'
        o['part_role']=o.name
        o['uv_authoring']='per-component Smart Project, 66 degree grouping, 0.025 island margin'
        if i%50==0: print('UV_AUTHORING',i+1,'/',len(objects),flush=True)
    return objects


def studio(objects,slug):
    scene=bpy.context.scene
    coll=bpy.data.collections.new('STUDIO');scene.collection.children.link(coll)
    def link(o):
        for c in list(o.users_collection): c.objects.unlink(o)
        coll.objects.link(o)
    coords=[o.matrix_world@Vector(corner) for o in objects for corner in o.bound_box]
    lo=Vector((min(p.x for p in coords),min(p.y for p in coords),min(p.z for p in coords)))
    hi=Vector((max(p.x for p in coords),max(p.y for p in coords),max(p.z for p in coords)))
    size=hi-lo;center=(hi+lo)/2
    span=max(size.x,size.y,size.z)
    ground=material('STUDIO | matte warm gray',(.37,.39,.40),0,.89)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,lo.z-.015));floor=bpy.context.object
    floor.name='STUDIO | ground';floor.data.materials.append(ground);link(floor)
    world=bpy.data.worlds.new('STUDIO | neutral environment');scene.world=world;world.use_nodes=True
    world.node_tree.nodes['Background'].inputs[0].default_value=(.64,.69,.74,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.32
    def lamp(name,pos,power,width,color):
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=width;data.color=color
        o=bpy.data.objects.new(name,data);coll.objects.link(o);o.location=pos
        o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
    lamp('STUDIO | key',center+Vector((-span*.70,-span*.90,span*1.40)),span*span*65,span*.75,(1.0,.91,.80))
    lamp('STUDIO | fill',center+Vector((span,span*.1,span*.70)),span*span*40,span*.95,(.82,.91,1.0))
    lamp('STUDIO | rim',center+Vector((-.2*span,span,span*1.10)),span*span*55,span*.75,(1,1,1))
    cam_data=bpy.data.cameras.new('STUDIO | orthographic camera');cam=bpy.data.objects.new('STUDIO | orthographic camera',cam_data)
    coll.objects.link(cam);scene.camera=cam;cam_data.type='ORTHO';cam_data.lens=52
    # Orthographic fitting is camera authorship from known scene extents.
    # It is not a rendered-image inspection or automated quality review.
    views={}
    for view,direction in [('hero',Vector((1.15,-1.70,1.05))),('rear',Vector((-1.20,1.65,1.03)))]:
        cam.location=center+direction.normalized()*span*3
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        rot=cam.rotation_euler.to_matrix().transposed()
        cc=[rot@(p-center) for p in coords]
        width=max(p.x for p in cc)-min(p.x for p in cc)
        height=max(p.y for p in cc)-min(p.y for p in cc)
        cam_data.ortho_scale=max(width,height)*1.18
        views[view]={'location':list(cam.location),'rotation_euler':list(cam.rotation_euler),'orthographic_scale':cam_data.ortho_scale,'target':list(center)}
    return cam,views,{'min':list(lo),'max':list(hi),'dimensions':list(size)}


def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser();parser.add_argument('--asset',required=True,choices=list(BUILDERS));opt=parser.parse_args(args)
    slug=opt.asset;out=ROOT/slug;out.mkdir(exist_ok=True);(out/'renders').mkdir(exist_ok=True)
    start=stamp();t0=time.perf_counter()
    reset();design=BUILDERS[slug]()
    objects=author_uvs()
    # Capture measurements only from authored objects, not a reopened export.
    production={'mesh_parts':len(objects),'vertices':sum(len(o.data.vertices) for o in objects),'polygons':sum(len(o.data.polygons) for o in objects),'materials':[{'name':m.name,'base_color':list(m.diffuse_color),'metallic':m.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value,'roughness':m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value} for m in M.values()]}
    cam,views,bounds=studio(objects,slug)
    scene=bpy.context.scene
    def setview(view):
        cfg=views[view];cam.location=cfg['location'];cam.rotation_euler=cfg['rotation_euler'];cam.data.ortho_scale=cfg['orthographic_scale']
    setview('hero')
    # Only ASSET meshes are selected for GLB and FBX. STUDIO remains in native file.
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(slug+'.blend')))
    bpy.ops.export_scene.gltf(filepath=str(out/(slug+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_yup=True)
    bpy.ops.export_scene.fbx(filepath=str(out/(slug+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,path_mode='AUTO')
    render_records=[]
    for view in ('hero','rear'):
        setview(view);scene.render.filepath=str(out/'renders'/(view+'.png'))
        rs=stamp();rt=time.perf_counter();bpy.ops.render.render(write_still=True)
        render_records.append({'view':view,'path':f'{slug}/renders/{view}.png','started_at_utc':rs,'finished_at_utc':stamp(),'elapsed_seconds':round(time.perf_counter()-rt,3),'camera':views[view]})
    meta={'asset':slug,'set':'Set04','theme':'aerial logistics','units':'meters','front_axis':'-Y','up_axis':'+Z','reference':f'../REF/{slug}.png','design':design,'authored_scene_bounds_m':bounds,'production_measurements':production,'uv_authoring':{'method':'individually packed Smart Project surface islands per editable component, after bevel application','angle_degrees':66,'island_margin':.025,'map':'SurfaceUV','independent_uv_review':'deferred_by_user'},'native_collections':['ASSET','STUDIO'],'exports':'ASSET mesh selection only, no studio cameras/lights/floor','render':{'engine':'Cycles CPU','threads':4,'samples':40,'resolution':[960,960],'view_transform':'AgX','look':'Medium High Contrast','background':'neutral warm-gray studio','records':render_records},'review_status':'deferred_by_user','checks_performed':'process completion and expected nonempty output file presence only, by runner','not_performed':['render opening or inspection','fresh native reopen','GLB or FBX reimport','geometry or UV validators','reviewer tasks'],'limitations':['solid palette materials; no texture maps','static meshes; no rig, animation, collision or LOD','glazing is stylized opaque smoked PBR, not a detailed occupied interior','reference back sides interpreted from functional design'],'started_at_utc':start,'finished_at_utc':stamp(),'production_elapsed_seconds':round(time.perf_counter()-t0,3)}
    (out/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('ASSET_PRODUCED_UNREVIEWED',slug,meta['production_elapsed_seconds'],flush=True)


if __name__=='__main__': main()
