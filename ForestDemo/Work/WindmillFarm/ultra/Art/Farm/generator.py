"""Original WindmillFarm architecture and farm props. Blender 4.5 background."""
import bpy
import bmesh
import math
import json
import random
import time
from pathlib import Path
from datetime import datetime, timezone
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
START = datetime.now(timezone.utc)
RNG = random.Random(71319)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for datablock in list(bpy.data.materials):
    bpy.data.materials.remove(datablock)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1.0

PALETTE = {
    'Wood': (0.255, 0.168, 0.096, 1),
    'WoodLight': (0.435, 0.321, 0.190, 1),
    'Stone': (0.390, 0.403, 0.353, 1),
    'Plaster': (0.708, 0.657, 0.500, 1),
    'Roof': (0.445, 0.196, 0.106, 1),
    'Iron': (0.110, 0.130, 0.122, 1),
    'Canvas': (0.745, 0.727, 0.614, 1),
    'Glass': (0.220, 0.339, 0.330, 1),
    'Hay': (0.644, 0.514, 0.208, 1),
    'Leaf': (0.248, 0.369, 0.129, 1),
    'Soil': (0.240, 0.187, 0.122, 1),
}
MATS = {}
for name, color in PALETTE.items():
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = color
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = .78 if name != 'Iron' else .55
    if name == 'Iron':
        bsdf.inputs['Metallic'].default_value = .65
    MATS[name] = mat

ASSETS = {}
CURRENT = None

def begin(name):
    global CURRENT
    CURRENT = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(CURRENT)
    ASSETS[name] = {'collection': CURRENT, 'parts': []}

def register(obj, label, material):
    obj.name = label
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    CURRENT.objects.link(obj)
    obj.data.materials.clear()
    obj.data.materials.append(MATS[material])
    ASSETS[CURRENT.name]['parts'].append(obj)
    return obj

def bevel(obj, width=.025, segments=2):
    if width > 0:
        mod = obj.modifiers.new('Crafted rounded edges', 'BEVEL')
        mod.width = width
        mod.segments = segments
        mod.limit_method = 'ANGLE'
        mod.angle_limit = .30
        mod.affect = 'EDGES'
        mod.harden_normals = True
    return obj

def cube(label, loc, dims, material='Wood', radius=.025, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if rot is not None:
        obj.rotation_euler = rot
    register(obj, label, material)
    return bevel(obj, min(radius, min(dims)*.32), 2)

def beam(label, a, b, width=.1, depth=None, material='Wood', radius=.025):
    a, b = Vector(a), Vector(b)
    obj = cube(label, (a+b)*.5, (width, depth or width, (b-a).length), material, radius)
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = (b-a).to_track_quat('Z', 'Y')
    return obj

def cyl(label, loc, radius, depth, material='Wood', vertices=16, axis='Z', bevel_width=.018):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    obj = bpy.context.object
    if axis == 'X':
        obj.rotation_euler.y = math.pi*.5
    elif axis == 'Y':
        obj.rotation_euler.x = math.pi*.5
    register(obj, label, material)
    bevel(obj, bevel_width, 2)
    return obj

def torus(label, loc, major, minor, material='Iron', axis='Z', major_segments=24, minor_segments=6):
    bpy.ops.mesh.primitive_torus_add(major_segments=major_segments, minor_segments=minor_segments,
                                  location=loc, major_radius=major, minor_radius=minor)
    obj = bpy.context.object
    if axis == 'X':
        obj.rotation_euler.y = math.pi*.5
    elif axis == 'Y':
        obj.rotation_euler.x = math.pi*.5
    register(obj, label, material)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj

def mesh(label, verts, faces, material='Wood', radius=.01):
    me = bpy.data.meshes.new(label)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(label, me)
    CURRENT.objects.link(ob)
    me.materials.append(MATS[material])
    ASSETS[CURRENT.name]['parts'].append(ob)
    return bevel(ob, radius, 2)

def gable(label, y, depth, half_width, eave, ridge, material='WoodLight'):
    verts = [(-half_width,y-depth*.5,eave),(half_width,y-depth*.5,eave),(0,y-depth*.5,ridge),
             (-half_width,y+depth*.5,eave),(half_width,y+depth*.5,eave),(0,y+depth*.5,ridge)]
    return mesh(label, verts, [(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)], material, .02)

def ring_mesh(label, loc, rad, height, thickness, material='Iron', count=24):
    x,y,z=loc
    verts=[]
    for zz, rr in [(z-height*.5,rad),(z+height*.5,rad),(z-height*.5,rad-thickness),(z+height*.5,rad-thickness)]:
        for i in range(count):
            angle=2*math.pi*i/count
            verts.append((x+rr*math.cos(angle),y+rr*math.sin(angle),zz))
    faces=[]
    for i in range(count):
        j=(i+1)%count
        faces.extend([(i,j,count+j,count+i),(2*count+j,2*count+i,3*count+i,3*count+j),
                      (count+i,count+j,3*count+j,3*count+i),(j,i,2*count+i,2*count+j)])
    return mesh(label,verts,faces,material,.006)

def barrel(label, loc=(0,0,0), scale=1):
    x,y,z=loc
    h=.98*scale
    n=16
    levels=[(0,.31),(.10,.35),(.26,.39),(.51,.41),(.75,.39),(.91,.35),(.98,.31)]
    for i in range(n):
        aa=2*math.pi*i/n+.012
        bb=2*math.pi*(i+1)/n-.012
        verts=[]
        for zz,r in levels:
            for angle in [aa,bb]:
                verts.append((x+scale*r*math.cos(angle),y+scale*r*math.sin(angle),z+zz*scale))
        faces=[]
        for k in range(len(levels)-1):
            faces.append((2*k,2*k+1,2*k+3,2*k+2))
        obj=mesh(label+'_Stave_%02d'%i,verts,faces,'WoodLight' if i%3 else 'Wood',.006*scale)
        mod=obj.modifiers.new('Stave thickness','SOLIDIFY')
        mod.thickness=.035*scale
    for zz,rr in [(.10,.357),(.27,.399),(.73,.399),(.90,.357)]:
        ring_mesh(label+'_IronHoop',(x,y,z+zz*scale),rr*scale,.055*scale,.021*scale,'Iron')
    for zz in [.015,.965]:
        cyl(label+'_Lid',(x,y,z+zz*scale),.303*scale,.035*scale,'WoodLight',24,bevel_width=.008*scale)
        for ix in [-.18,-.06,.06,.18]:
            length=2*math.sqrt(max(.29**2-ix**2,0))*scale
            cube(label+'_LidSeam',(x+ix*scale,y,z+(zz+.019)*scale),(.007*scale,length,.004*scale),'Wood',.001)
    cyl(label+'_Bung',(x+.09*scale,y-.02*scale,z+.995*scale),.04*scale,.018*scale,'Wood',12,bevel_width=.005*scale)

def crate(label, loc=(0,0,0), dims=(.72,.54,.56), filled=False):
    x,y,z=loc
    w,d,h=dims
    for sx in [-1,1]:
        for sy in [-1,1]:
            cube(label+'_Corner',(x+sx*(w/2-.04),y+sy*(d/2-.04),z+h/2),(.075,.075,h),'Wood',.016)
    for row in range(3):
        zz=z+.11+row*(h-.14)/3
        for sy in [-1,1]:
            cube(label+'_SidePlank',(x,y+sy*d/2,zz),(w,.055,(h-.14)/3-.028),'WoodLight',.013)
        for sx in [-1,1]:
            cube(label+'_EndPlank',(x+sx*w/2,y,zz),(.055,d,(h-.14)/3-.028),'WoodLight',.013)
    for i in range(4):
        cube(label+'_Floor',(x-w/2+(i+.5)*w/4,y,z+.045),(w/4-.018,d,.075),'WoodLight',.012)
    if filled:
        for i in range(7):
            px=x+RNG.uniform(-w*.30,w*.30)
            py=y+RNG.uniform(-d*.28,d*.28)
            pz=z+h*.65+RNG.uniform(-.035,.06)
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.10,location=(px,py,pz))
            register(bpy.context.object,label+'_Produce','Hay')

def shovel(label, foot=(0,0,0), tip=(0,0,1.7)):
    a,b=Vector(foot),Vector(tip)
    vec=(b-a).normalized()
    beam(label+'_WoodShaft',a+vec*.28,b,.045,material='WoodLight',radius=.012)
    # Blade at the grounded end, visibly pressed and broad rather than a flat rod.
    ob=cube(label+'_SpadeBlade',a+vec*.16,(.23,.035,.32),'Iron',.045)
    ob.rotation_mode='QUATERNION'
    ob.rotation_quaternion=vec.to_track_quat('Z','Y')
    cyl(label+'_Socket',a+vec*.35,.039,.22,'Iron',12,bevel_width=.008)
    handle=b+vec*.10
    torus(label+'_DGrip',handle,.085,.022,'Wood',axis='Y',major_segments=16,minor_segments=6)

def pitchfork(label, foot=(0,0,0), tip=(0,0,1.8), rake=False):
    a,b=Vector(foot),Vector(tip)
    vec=(b-a).normalized()
    beam(label+'_Shaft',a+vec*.26,b,.047,material='WoodLight',radius=.01)
    center=a+vec*.24
    width=.43 if rake else .29
    beam(label+'_Head',(center.x-width*.5,center.y,center.z),(center.x+width*.5,center.y,center.z),.038,material='Iron',radius=.008)
    count=8 if rake else 4
    for i in range(count):
        xx=center.x-width*.45+i*width*.90/(count-1)
        end=(xx,center.y-.075,center.z-(.12 if rake else .24))
        beam(label+'_Tine',(xx,center.y,center.z),end,.018,material='Iron',radius=.005)

def roof_panel(label, p0, p1, length, rows, cols, material='Roof'):
    # Slope runs p0 (eave) to p1 (ridge); local X follows the pitched roof.
    p0,p1=Vector(p0),Vector(p1)
    slope=p1-p0
    mid=(p0+p1)*.5
    a=math.atan2(slope.z,slope.x)
    # cube local X points uphill under rotation around Y=-a.
    cube(label+'_RoofDeck',mid,(slope.length+.10,length,.15),'Wood',.03,rot=(0,-a,0))
    direction=slope.normalized()
    normal=Vector((-direction.z,0,direction.x))
    if normal.z < 0:
        normal=-normal
    rowstep=slope.length/rows
    colstep=length/cols
    for rr in range(rows):
        for cc in range(cols):
            along=(rr+.5)*rowstep
            off=-length/2+(cc+.5)*colstep
            if rr%2:
                off+=colstep*.055
            loc=p0+direction*along+Vector((0,off,0))+normal*(.105+rr*.001)
            cube(label+'_ClayTile_%02d_%02d'%(rr,cc),loc,
                 (rowstep*1.09,colstep*.96,.072),material,.031,
                 rot=(0,-a,RNG.uniform(-.007,.007)))

# Main barn: front -Y. Intentional stone footing, exposed joinery and substantial doors.
begin('SM_Barn')
for side in [-1,1]:
    for k in range(9):
        cube('Barn_SideFoundation',(side*4.91,-3.20+k*.80,.20),(.33,.77,.40),'Stone',.07)
    cube('Barn_PlasteredLongWall',(side*4.86,0,1.17),(.24,6.86,1.95),'Plaster',.065)
    for k in range(31):
        yy=-3.36+k*.224
        cube('Barn_WeatherboardUpper',(side*4.91,yy,2.68),(.21,.211,1.12),'WoodLight' if k%5 else 'Wood',.018)
    for yy in [-3.38,-1.14,1.14,3.38]:
        cube('Barn_LongWallFramePost',(side*4.99,yy,1.75),(.22,.22,3.48),'Wood',.035)
    for zz in [.42,2.12,3.20]:
        cube('Barn_LongWallRail',(side*5.01,0,zz),(.22,6.97,.20),'Wood',.034)
    for yy in [-2.16,2.16]:
        # Genuine windows inset behind wooden jambs.
        cube('Barn_SideWindowGlass',(side*5.035,yy,1.64),(.025,1.10,.76),'Glass',.01)
        for y2 in [yy-.61,yy+.61]:
            cube('Barn_SideWindowJamb',(side*5.07,y2,1.67),(.14,.09,.93),'Wood',.018)
        for zz in [1.21,2.10]:
            cube('Barn_SideWindowLintel',(side*5.10,yy,zz),(.21,1.33,.10),'WoodLight',.022)
        cube('Barn_SideWindowMullion',(side*5.09,yy,1.66),(.12,.055,.83),'Wood',.012)
        cube('Barn_SideWindowTransom',(side*5.09,yy,1.66),(.12,1.15,.045),'Wood',.01)
    # Front flanking wall bays; central 3.4 metre doors.
    xx=side*3.32
    cube('Barn_FrontPlaster',(xx,-3.45,1.22),(3.14,.22,1.93),'Plaster',.06)
    for k in range(14):
        px=side*(1.88+k*.218)
        cube('Barn_FrontUpperPlank',(px,-3.48,2.69),(.205,.18,1.10),'WoodLight' if k%4 else 'Wood',.019)
    for k in range(4):
        cube('Barn_FrontStone',(side*(2.10+k*.78),-3.48,.21),(.75,.36,.42),'Stone',.065)
    cube('Barn_FrontDoorPost',(side*1.79,-3.64,1.68),(.24,.28,3.35),'Wood',.035)
    # Individual heavy vertical door boards with face battens and diagonals.
    for k in range(7):
        xx=side*(.13+k*.244)
        cube('Barn_DoorPlank',(xx,-3.63,1.46),(.233,.16,2.78),'WoodLight' if k%3 else 'Wood',.018)
    for zz in [.34,1.49,2.64]:
        cube('Barn_DoorCrossBatten',(side*.86,-3.75,zz),(1.65,.095,.15),'Wood',.02)
    beam('Barn_DoorDiagonal',(side*.12,-3.81,.42),(side*1.57,-3.81,2.58),.11,.08,'Wood',.02)
    cube('Barn_DoorHandlePlate',(side*.17,-3.80,1.45),(.12,.035,.24),'Iron',.016)
    torus('Barn_DoorRingHandle',(side*.17,-3.85,1.43),.072,.015,'Iron',axis='Y',major_segments=16)
    for zz in [.34,2.64]:
        for xx in [.18,1.52]:
            cyl('Barn_DoorIronRivet',(side*xx,-3.81,zz),.023,.016,'Iron',8,axis='Y',bevel_width=.003)
cube('Barn_BackPlaster',(0,3.43,1.21),(9.72,.24,1.95),'Plaster',.06)
for k in range(44):
    cube('Barn_BackUpperPlank',(-4.73+k*.22,3.48,2.69),(.211,.19,1.10),'WoodLight' if k%6 else 'Wood',.018)
for yy in [-3.48,3.48]:
    gable('Barn_TriangularGable',yy,.20,4.94,3.20,5.44,'WoodLight')
    cube('Barn_EndEaveBeam',(0,yy,3.22),(10.10,.26,.23),'Wood',.034)
    beam('Barn_LeftGableRafter',(-5.02,yy,3.29),(0,yy,5.54),.19,.24,'Wood',.028)
    beam('Barn_RightGableRafter',(5.02,yy,3.29),(0,yy,5.54),.19,.24,'Wood',.028)
    beam('Barn_GableKingPost',(0,yy-.10,3.28),(0,yy-.10,5.37),.15,.13,'Wood',.022)
    for xx in [-2.5,2.5]:
        beam('Barn_GableDiagonal',(xx,yy-.11,3.31),(0,yy-.11,4.95),.12,.12,'Wood',.02)
cube('Barn_SlidingDoorRail',(0,-3.84,2.98),(7.30,.11,.095),'Iron',.02)
cube('Barn_DoorHeadBoard',(0,-3.57,3.08),(3.42,.23,.28),'WoodLight',.03)
for xx in [-1.42,-.40,.40,1.42]:
    cyl('Barn_DoorRoller',(xx,-3.88,3.01),.076,.045,'Iron',16,axis='Y',bevel_width=.012)
    cube('Barn_DoorRollerHanger',(xx,-3.85,2.80),(.065,.055,.35),'Iron',.014)
for xx in [-1,1]:
    roof_panel('Barn_%sRoof'%('West' if xx<0 else 'East'),(xx*5.35,0,3.22),(0,0,5.62),7.80,8,15)
for k in range(16):
    cyl('Barn_RidgeCap',(0,-3.66+k*.485,5.68),.14,.54,'Roof',12,axis='Y',bevel_width=.025)
for yy in [-3.93,3.93]:
    beam('Barn_Fascia',(-5.40,yy,3.23),(0,yy,5.64),.13,.17,'Wood',.026)
    beam('Barn_Fascia',(5.40,yy,3.23),(0,yy,5.64),.13,.17,'Wood',.026)
# A modest covered work alcove on the left side of the facade.
for xx in [-4.72,-2.42]:
    cube('Barn_AlcovePost',(xx,-4.79,1.25),(.15,.15,2.50),'Wood',.027)
    beam('Barn_AlcoveKneeBrace',(xx,-4.79,1.88),(xx+(.42 if xx<-3 else -.42),-4.79,2.46),.10,material='Wood',radius=.018)
cube('Barn_AlcoveFrontBeam',(-3.57,-4.79,2.48),(2.56,.16,.17),'Wood',.025)
cube('Barn_AlcoveRoof',(-3.57,-4.16,2.67),(2.85,1.63,.15),'Roof',.04,rot=(.13,0,0))
for xx in [-4.15,-3.05]:
    cube('Barn_WorkbenchLeg',(xx,-4.05,.43),(.10,.10,.86),'Wood',.02)
cube('Barn_Workbench',(-3.60,-4.08,.91),(1.57,.62,.12),'WoodLight',.03)
crate('Barn_WorkCrate',(-4.48,-4.12,.02),(.58,.46,.48),True)
cube('Barn_SteppingStone',(.05,-4.02,.08),(3.48,.71,.16),'Stone',.06)

# Tool shed, frontage -Y, asymmetrical lean-to roof.
begin('SM_Shed')
for side in [-1,1]:
    for i in range(4):
        cube('Shed_Foundation',(side*1.92,-1.15+i*.77,.14),(.27,.73,.28),'Stone',.06)
    for i in range(13):
        yy=-1.40+i*.232
        height=2.40+(yy+1.50)*.17
        cube('Shed_SideCladding',(side*1.91,yy,height*.5+.10),(.15,.218,height),'WoodLight' if i%4 else 'Wood',.018)
    for yy in [-1.43,1.43]:
        height=2.40+(yy+1.5)*.17
        cube('Shed_CornerPost',(side*1.99,yy,height*.5),(.20,.20,height),'Wood',.027)
    for zz in [.26,1.33,2.30]:
        cube('Shed_HorizontalRail',(side*2.01,0,zz),(.16,3.02,.16),'Wood',.025)
for i in range(17):
    cube('Shed_BackCladding',(-1.84+i*.23,1.46,1.46),(.219,.16,2.79),'WoodLight' if i%4 else 'Wood',.018)
for xx in [-1.58,1.58]:
    cube('Shed_FrontSidePanel',(xx,-1.47,1.20),(.72,.15,2.38),'WoodLight',.025)
    cube('Shed_DoorJamb',(math.copysign(1.15,xx),-1.57,1.19),(.15,.20,2.37),'Wood',.025)
cube('Shed_DoorLintel',(0,-1.56,2.33),(2.42,.19,.20),'Wood',.025)
# Pair of doors sit open toward the sides; interior shallow shadow and tool wall visible.
cube('Shed_InteriorShadow',(0,.87,1.06),(3.61,.07,1.98),'Wood',.025)
for side in [-1,1]:
    for i in range(5):
        cube('Shed_OpenDoorPlank',(side*(1.25+i*.20),-1.65,1.12),(.19,.11,2.16),'WoodLight',.017)
    for zz in [.31,1.92]:
        cube('Shed_DoorBatten',(side*1.66,-1.73,zz),(1.04,.07,.13),'Wood',.019)
    beam('Shed_DoorBrace',(side*1.24,-1.76,.38),(side*2.08,-1.76,1.85),.10,.06,'Wood',.016)
cube('Shed_Roof', (0,0,2.77),(4.50,3.53,.18),'Roof',.045,rot=(.167,0,0))
for i in range(13):
    xx=-2.10+i*.35
    cube('Shed_RoofBatten',(xx,0,2.89),(.055,3.54,.035),'Wood',.009,rot=(.167,0,0))
for yy,zz in [(-1.77,2.49),(1.77,3.08)]:
    cube('Shed_RoofFascia',(0,yy,zz),(4.56,.12,.20),'Wood',.027)
cube('Shed_ToolRack',(0,.78,1.63),(2.22,.13,.15),'WoodLight',.025)
shovel('Shed_Spade',(-.56,.49,.08),(-.56,.72,1.89))
pitchfork('Shed_Fork',(.08,.51,.07),(.08,.72,1.99))
pitchfork('Shed_Rake',(.70,.52,.10),(.70,.73,1.98),True)
crate('Shed_SupplyCrate',(-.71,-.19,.02),(.75,.55,.55))
barrel('Shed_Barrel',(.85,.02,.02),.78)
cube('Shed_EntryStep',(0,-1.54,.07),(2.30,.76,.14),'Stone',.045)

# Farm cart: four genuinely spoked wheels, open slatted body and cargo.
begin('SM_Cart')
for xx in [-.49,.49]:
    cube('Cart_LongChassis',(xx,0,.69),(.16,2.36,.18),'Wood',.03)
for yy in [-.85,.85]:
    cyl('Cart_IronAxle',(0,yy,.57),.065,1.96,'Iron',12,axis='X',bevel_width=.012)
for i in range(7):
    cube('Cart_FloorPlank',(-.60+i*.20,0,.85),(.188,2.36,.12),'WoodLight' if i%3 else 'Wood',.02)
for side in [-1,1]:
    for yy in [-1.09,0,1.09]:
        cube('Cart_SideUpright',(side*.69,yy,1.23),(.10,.10,.86),'Wood',.022)
    for zz in [1.01,1.23,1.45]:
        cube('Cart_SideBoard',(side*.70,0,zz),(.085,2.42,.16),'WoodLight',.023)
    for yy in [-.85,.85]:
        torus('Cart_WoodWheelRim',(side*.91,yy,.57),.48,.055,'WoodLight',axis='X',major_segments=24,minor_segments=8)
        torus('Cart_IronTyre',(side*.91,yy,.57),.530,.020,'Iron',axis='X',major_segments=24,minor_segments=6)
        cyl('Cart_WheelHub',(side*.91,yy,.57),.115,.24,'Wood',16,axis='X',bevel_width=.025)
        cyl('Cart_HubIronEnd',(side*1.045,yy,.57),.079,.036,'Iron',12,axis='X',bevel_width=.009)
        for i in range(10):
            a=2*math.pi*i/10
            beam('Cart_WheelSpoke',(side*.91,yy+math.cos(a)*.10,.57+math.sin(a)*.10),
                 (side*.91,yy+math.cos(a)*.475,.57+math.sin(a)*.475),.047,.065,'WoodLight',.010)
for yy in [-1.18,1.18]:
    for zz in [1.01,1.23,1.45]:
        cube('Cart_EndBoard',(0,yy,zz),(1.44,.085,.16),'WoodLight',.02)
for side in [-1,1]:
    beam('Cart_PullingShaft',(side*.48,-.96,.72),(side*.38,-2.85,.91),.095,.10,'Wood',.023)
    cyl('Cart_HandGrip',(side*.38,-2.86,.91),.065,.32,'WoodLight',12,axis='Y',bevel_width=.02)
crate('Cart_Crate',(-.22,-.46,.92),(.66,.57,.52),True)
barrel('Cart_Barrel',(.22,.52,.92),.67)
cube('Cart_FoldedCloth',(-.29,.34,1.00),(.49,.55,.15),'Canvas',.055,rot=(0,.05,-.06))

# A straight three metre fence and matching working gate.
begin('SM_FenceSegment')
for xx in [-1.40,1.40]:
    cube('Fence_Post',(xx,0,.62),(.19,.20,1.24),'Wood',.04,rot=(0,.018 if xx<0 else -.028,0))
    cube('Fence_PostCap',(xx,0,1.245),(.225,.23,.095),'WoodLight',.03,rot=(0,.04,0))
    for zz in [.40,.92]:
        cyl('Fence_Peg',(xx,-.139,zz),.023,.06,'WoodLight',10,axis='Y',bevel_width=.006)
for i,zz in enumerate([.40,.92]):
    beam('Fence_SplitRail',(-1.53,-.03,zz-.028),(1.52,-.02,zz+.025),.13,.095,'WoodLight',.028)
    # Small joined wedges imply irregular split-timber construction without decoration.
    cube('Fence_SplitKnot',(-.49+i*.83,-.085,zz+.028),(.23,.032,.066),'Wood',.018,rot=(0,.06,0))

begin('SM_Gate')
for xx in [-1.40,1.40]:
    cube('Gate_FrameStile',(xx,0,.62),(.15,.17,1.20),'Wood',.03)
for zz in [.22,.65,1.13]:
    cube('Gate_HorizontalRail',(0,-.015,zz),(2.84,.13,.14),'WoodLight',.025)
beam('Gate_DiagonalBrace',(-1.32,-.09,.25),(1.33,-.09,1.13),.11,.08,'Wood',.024)
for xx in [-.94,-.47,0,.47,.94]:
    cube('Gate_SlimPicket',(xx,.027,.67),(.075,.09,1.04),'WoodLight',.018)
for zz in [.27,1.08]:
    cube('Gate_HingeStrap',(-1.11,-.11,zz),(.76,.045,.075),'Iron',.013)
    cyl('Gate_HingeKnuckle',(-1.48,-.04,zz),.043,.16,'Iron',12,bevel_width=.01)
cube('Gate_Latch',(1.40,-.14,.92),(.37,.045,.065),'Iron',.01,rot=(0,.08,0))
torus('Gate_LatchRing',(1.29,-.16,.86),.052,.012,'Iron',axis='Y',major_segments=12)

begin('SM_ToolCluster')
crate('Tools_LargeCrate',(-.32,.20,.02),(.81,.61,.57))
crate('Tools_SmallCrate',(-.36,.19,.61),(.61,.48,.42),True)
shovel('Tools_Spade',(.35,-.26,.02),(.18,.27,1.81))
pitchfork('Tools_Pitchfork',(.72,-.08,.03),(.55,.30,1.96))
pitchfork('Tools_Rake',(-.68,-.10,.04),(-.57,.26,1.88),True)
cube('Tools_ShortBench',(.60,.38,.44),(.75,.39,.09),'WoodLight',.025)
for xx in [.32,.87]:
    cube('Tools_BenchLeg',(xx,.38,.22),(.09,.29,.44),'Wood',.02)

begin('SM_Barrel')
barrel('Barrel')

begin('SM_HayBale')
cube('Hay_RoundedBale',(0,0,.38),(1.20,.73,.76),'Hay',.135)
for xx in [-.35,.35]:
    cube('Hay_TwineTop',(xx,0,.772),(.023,.72,.025),'WoodLight',.009)
    cube('Hay_TwineBottom',(xx,0,.019),(.023,.72,.025),'WoodLight',.009)
    for yy in [-.369,.369]:
        cube('Hay_TwineSide',(xx,yy,.39),(.023,.025,.74),'WoodLight',.008)
for i in range(20):
    xx=RNG.uniform(-.52,.52)
    yy=RNG.uniform(-.29,.29)
    zz=.735+RNG.uniform(-.025,.03)
    beam('Hay_StrawOnTop',(xx-.10,yy,zz),(xx+.11,yy+RNG.uniform(-.05,.05),zz),.014,.012,'Hay',.003)

begin('SM_CropClump')
for i in range(9):
    angle=i*2.399
    rad=.22*math.sqrt((i+1)/9)
    xx=math.cos(angle)*rad
    yy=math.sin(angle)*rad
    height=RNG.uniform(.50,.73)
    beam('Crop_Stem',(xx,yy,.015),(xx+.03,yy,height),.018,material='Hay',radius=.005)
    for j in range(4):
        theta=angle+j*1.7
        zz=.12+j*.105
        base=Vector((xx,yy,zz))
        out=Vector((math.cos(theta),math.sin(theta),.38))*.20
        side=Vector((-math.sin(theta),math.cos(theta),0))*.038
        verts=[base,base+out*.65+side,base+out,base+out*.65-side,base+Vector((0,0,.02))]
        leaf=mesh('Crop_PointLeaf',verts,[(0,1,2,3),(4,3,2,1)],'Leaf',.003)
    for j in range(5):
        zz=height-.12+j*.030
        for sign in [-1,1]:
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.033,
                location=(xx+sign*.024,yy,zz))
            ob=bpy.context.object
            ob.scale=(.70,.80,1.4)
            register(ob,'Crop_Grain','Hay')

def area_uv(a,b,c):
    return abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5

def analyze_uv(obj):
    me=obj.data
    uv=me.uv_layers.active.data
    area_world=0.0
    area_uv_total=0.0
    degenerate=0
    outside=0
    weighted=[]
    by_mat={}
    for p in me.polygons:
        li=list(p.loop_indices)
        pa=uv[li[0]].uv
        puv=0.0
        for k in range(1,len(li)-1):
            tri=area_uv(pa,uv[li[k]].uv,uv[li[k+1]].uv)
            if tri<1e-12:
                degenerate+=1
            puv+=tri
        for l in li:
            x,y=uv[l].uv
            if x<-.00001 or y<-.00001 or x>1.00001 or y>1.00001:
                outside+=1
        area_world+=p.area
        area_uv_total+=puv
        if p.area>1e-12:
            weighted.append((1024*math.sqrt(puv/p.area),p.area))
        matname=obj.data.materials[p.material_index].name
        bucket=by_mat.setdefault(matname,{'world_area_m2':0.0,'uv_area':0.0,'faces':0})
        bucket['world_area_m2']+=p.area
        bucket['uv_area']+=puv
        bucket['faces']+=1
    density=1024*math.sqrt(area_uv_total/area_world)
    for name,v in by_mat.items():
        v['equivalent_density_at_1024_px_per_m']=1024*math.sqrt(v['uv_area']/v['world_area_m2'])
    return {
        'uv_layers':[v.name for v in me.uv_layers],
        'method':'Smart-project 66 degrees, scale to equal surface density, pack rotated islands with 0.0015 fractional margin',
        'texel_density_target_px_per_m':128,
        'reference_texture_resolution':1024,
        'world_surface_area_m2':area_world,
        'occupied_uv_triangle_area':area_uv_total,
        'equivalent_density_at_1024_px_per_m':density,
        'estimated_resolution_for_target':int(math.ceil(128/density*1024)),
        'degenerate_uv_triangle_count':degenerate,
        'out_of_01_loop_count':outside,
        'island_padding_uv':.0015,
        'island_padding_px_at_1024':1.536,
        'overlap_check':'Blender pack_islands with unique unmirrored smart-projected islands; numeric triangle-intersection test not yet run',
        'exceptions':(['Large architecture has a unique 0-1 atlas; 1024px cannot reach 128px/m over all surfaces. Use reported minimum texture size or the actual material texture scale.'] if density<110 else []),
        'materials':by_mat,
    }

manifest={
    'theme':'WindmillFarm','effort':'ultra','author':'farm_assets subagent',
    'started_at_utc':START.isoformat(),
    'original_art':True,
    'asset_axis':'Blender metres, Z up, front -Y. FBX -Y forward Z up, scale 1, transforms applied.',
    'material_slots':list(PALETTE),
    'files':[],
    'assets':[],
}

# Convert modifiers to real mesh, join each asset and lay out one unique UV atlas.
for name,info in ASSETS.items():
    print('FINALIZING',name,flush=True)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in info['parts']:
        ob.select_set(True)
    bpy.context.view_layer.objects.active=info['parts'][0]
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join()
    ob=bpy.context.object
    ob.name=name
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    bpy.context.scene.cursor.location=(0,0,0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR',center='MEDIAN')
    # Bevel intersections can leave coincident slivers at cylinder caps or leaf tips.
    # Remove only microscopic construction artifacts before UV projection.
    bm=bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-7)
    bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY')
    tiny=[f for f in bm.faces if f.calc_area()<1e-9]
    microscopic_faces_removed=len(tiny)
    if tiny:
        bmesh.ops.delete(bm,geom=tiny,context='FACES_ONLY')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.0015,area_weight=0,correct_aspect=True,scale_to_bounds=False)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=True,margin=.0015,margin_method='FRACTION',shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.data.uv_layers.active.name='UV0_Unique'
    bounds=[ob.matrix_world@Vector(c) for c in ob.bound_box]
    low=[min(p[k] for p in bounds) for k in range(3)]
    high=[max(p[k] for p in bounds) for k in range(3)]
    stats=analyze_uv(ob)
    # Optional second coordinate channel gives every asset the same measured density.
    # UV0 remains a unique 0-1 atlas; UV1 deliberately uses repeating material space.
    density_scale=128/stats['equivalent_density_at_1024_px_per_m']
    uv0=ob.data.uv_layers.active
    uv1=ob.data.uv_layers.new(name='UV1_Density128')
    for i in range(len(uv0.data)):
        uv1.data[i].uv=uv0.data[i].uv*density_scale
    ob.data.uv_layers.active_index=0
    stats['uv_layers']=[v.name for v in ob.data.uv_layers]
    stats['optional_material_uv_channel']={
        'index':1,'name':'UV1_Density128','scale_from_unique_uv0':density_scale,
        'equivalent_density_at_1024_px_per_m':128,
        'outside_01':'Intentional tiling coordinates for physically consistent repeating surface textures; UV0 alone is the unique nonoverlapping 0-1 atlas.',
        'import_note':'Disable generated lightmap UVs so this authored second channel is retained. Static lights are not used.'}
    asset={'name':name,'fbx':name+'.fbx','bounds_min_m':low,'bounds_max_m':high,
           'dimensions_m':[high[i]-low[i] for i in range(3)],
           'vertices':len(ob.data.vertices),'triangles':len(ob.data.polygons),
           'microscopic_faces_removed':microscopic_faces_removed,
           'materials':[m.name for m in ob.data.materials],
           'uv':stats}
    manifest['assets'].append(asset)
    dest=ROOT/(name+'.fbx')
    bpy.ops.export_scene.fbx(filepath=str(dest),use_selection=True,global_scale=1,
        apply_unit_scale=True,axis_forward='-Y',axis_up='Z',bake_space_transform=False,
        object_types={'MESH'},use_mesh_modifiers=True,mesh_smooth_type='FACE',
        use_custom_props=False,add_leaf_bones=False,path_mode='AUTO',embed_textures=False,
        bake_anim=False)
    manifest['files'].append(dest.name)
    # Persist incremental manifest so failed later export cannot hide successful work.
    (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

# Store source with assets at their native export origin, collections isolated.
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.context.scene.objects:
    ob.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source.blend'))
manifest['finished_at_utc']=datetime.now(timezone.utc).isoformat()
manifest['elapsed_seconds']=(datetime.now(timezone.utc)-START).total_seconds()
manifest['files']+=['source.blend','generator.py','manifest.json']
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('FARM_ASSETS_COMPLETE',manifest['elapsed_seconds'],flush=True)
