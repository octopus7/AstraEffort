"""Isolated Blender 4.5 build. Front = -Y. No external creative dependency.
Run: blender --background --factory-startup --threads 4 --python this_file.py
"""
import bpy, bmesh, math, json, time, os, sys
from mathutils import Vector
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
T0 = time.time()
ASSET = []
COLLECTIONS = {}

def utc(): return datetime.now(timezone.utc).isoformat()
def srgb(v): return v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4
def color(h):
    h=h.lstrip('#'); return tuple(srgb(int(h[i:i+2],16)/255) for i in (0,2,4))+(1,)

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
base=bpy.data.collections.get('Collection'); base.name='VENDING_MACHINE'

def collection(name):
    if name not in COLLECTIONS:
        c=bpy.data.collections.new(name); base.children.link(c); COLLECTIONS[name]=c
    return COLLECTIONS[name]

def own(obj, group):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    collection(group).objects.link(obj); ASSET.append(obj)
    obj['asset_part']=True
    return obj

def mat(name, hexcolor, rough=.45, metallic=0, image=None, emission=0, alpha=1, transmission=0):
    m=bpy.data.materials.new(name); m.use_nodes=True
    m.diffuse_color=color(hexcolor)[:3]+(alpha,)
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=color(hexcolor)
    p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=metallic
    p.inputs['Alpha'].default_value=alpha
    p.inputs['Transmission Weight'].default_value=transmission
    p.inputs['IOR'].default_value=1.45
    m['roughness']=rough; m['metallic']=metallic; m['emission_strength']=emission
    m['alpha']=alpha; m['transmission']=transmission
    if image:
        tex=m.node_tree.nodes.new('ShaderNodeTexImage'); tex.name='GENERATED_SOURCE_ALBEDO'
        tex.image=bpy.data.images.load(str(ROOT/'textures/generated'/image),check_existing=True)
        tex.projection='BOX'; tex.projection_blend=.18
        coord=m.node_tree.nodes.new('ShaderNodeTexCoord')
        scale=m.node_tree.nodes.new('ShaderNodeVectorMath'); scale.operation='SCALE'; scale.inputs[3].default_value=2
        m.node_tree.links.new(coord.outputs['Generated'],scale.inputs[0]); m.node_tree.links.new(scale.outputs[0],tex.inputs['Vector'])
        m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
        m['source_image']=image
    if emission:
        p.inputs['Emission Color'].default_value=color(hexcolor)
        p.inputs['Emission Strength'].default_value=emission
    if alpha<1:
        m.surface_render_method='DITHERED'; m.use_transparent_shadow=True
    return m

BODY=mat('BODY_VARIANT_WHITE', '#ffffff', .39, .08, 'ivory_enamel_original.png')
BODY['variant_instructions']='Dedicated light body. White default tint. Ivory is supplied by image pixels; recolor only this material.'
SLATE=mat('ARMOR_Slate_Powdercoat','#ffffff',.44,.23,'slate_powdercoat_original.png')
DARK=mat('TRIM_Dark_Graphite','#253137',.37,.25)
RUBBER=mat('FEET_Rubber','#263334',.68,0)
CAVITY=mat('DISPLAY_Interior','#263a3f',.52,.12)
SHELF=mat('SHELVES_Slate','#ffffff',.4,.32,'slate_powdercoat_original.png')
METAL=mat('HARDWARE_Burnished_Metal','#707c7c',.3,.72)
AMBER=mat('LAMP_Amber_Emission','#ffba55',.28,.0,emission=3.0)
LAMPFRAME=mat('LAMP_Recess_Frame','#615745',.43,.3)
SCREEN=mat('CONTROL_Black_Screen','#071a24',.2,.08)
CYAN=mat('CONTROL_Cyan_Graphics','#7bdee7',.32,0,emission=.65)
PRINT=mat('GRAPHICS_Warm_White_Separate','#ece9dc',.51,0)
LABEL=mat('BOTTLE_Label_Cream','#e9dfc4',.55,0)
GLASS=mat('GLASS_Display_Lightly_Transparent','#c4e2e5',.10,0,alpha=.032,transmission=0)
GLASS['design_note']='Thin front pane uses low alpha for cross-viewer product visibility, with small transmission. No volumetric beverage shader.'
BOTTLEMATS=[mat('BOTTLE_'+n,h,.31,.04) for n,h in [('Apricot','#d49750'),('SeaBlue','#5a99a7'),('Coral','#c98262'),('Sage','#92a269'),('Golden','#c2a659'),('Berry','#a16c69')]]
CAPMATS=[mat('CAP_'+n,h,.42,.03) for n,h in [('Apricot','#b77b39'),('SeaBlue','#477b89'),('Coral','#ae674e'),('Sage','#75874f'),('Golden','#aa8b3d'),('Berry','#815156')]]

def apply(obj, mod):
    bpy.context.view_layer.objects.active=obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

def finish(obj, material, group, smooth=True):
    obj.data.materials.append(material)
    if smooth:
        for p in obj.data.polygons:p.use_smooth=True
        wn=obj.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL'); wn.keep_sharp=True; wn.weight=50
        apply(obj,wn)
    return own(obj,group)

def box(name,loc,dims,material,bevel=.025,group='01 Cabinet',seg=3,smooth=True):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object; o.name=name; o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        m=o.modifiers.new('Rounded machined edges','BEVEL'); m.width=bevel; m.segments=seg; m.affect='EDGES'
        apply(o,m)
    return finish(o,material,group,smooth)

def cylinder(name,loc,radius,depth,material,vertices=32,bevel=.006,group='07 Hardware',axis='Z'):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc)
    o=bpy.context.object; o.name=name
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    if axis=='X':o.rotation_euler[1]=math.pi/2
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    if bevel:
        m=o.modifiers.new('Soft edge','BEVEL');m.width=bevel;m.segments=3;apply(o,m)
    return finish(o,material,group)

def bool_difference(obj,cutter):
    bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new('True recessed cavity','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    apply(obj,mod)
    if cutter in ASSET:ASSET.remove(cutter)
    bpy.data.objects.remove(cutter,do_unlink=True)

def roundloop(w,h,r,n=8):
    out=[]
    for cx,cz,start in [(w/2-r,-h/2+r,-90),(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180)]:
        for k in range(n):
            a=math.radians(start+90*k/n);out.append((cx+r*math.cos(a),cz+r*math.sin(a)))
    return out

def ring(name,center,outer,inner,depth,material,rout=.07,rin=.05,group='02 Front display'):
    # Four x-z loops form a closed manifold rectangular annulus extruded in Y.
    a=roundloop(*outer,rout);b=roundloop(*inner,rin);n=len(a)
    verts=[]
    for coords,y in [(a,-depth/2),(b,-depth/2),(a,depth/2),(b,depth/2)]:
        verts.extend([(x+center[0],y+center[1],z+center[2]) for x,z in coords])
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j),(j,i,2*n+i,2*n+j),(n+i,n+j,3*n+j,3*n+i)])
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
    return finish(o,material,group)

def prism_profile(name,coords,ydepth,ycenter,material,group='03 Armor',bevel=.025):
    # Extrude a convex x-z profile.
    n=len(coords);vs=[(x,ycenter-ydepth/2,z) for x,z in coords]+[(x,ycenter+ydepth/2,z) for x,z in coords]
    fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    fs.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
    if bevel:
        mod=o.modifiers.new('Armor soft corners','BEVEL');mod.width=bevel;mod.segments=4;apply(o,mod)
    return finish(o,material,group)

def text(name,body,loc,size,material,group='06 Controls and graphics',align='CENTER'):
    cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.align_x=align;cu.align_y='CENTER'
    cu.extrude=.00015;cu.bevel_depth=.00005;cu.bevel_resolution=1;cu.resolution_u=3
    o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(math.pi/2,0,0)
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    bpy.ops.object.convert(target='MESH');o=bpy.context.object
    return finish(o,material,group,False)

def screw(name,loc,axis='Y'):
    o=cylinder(name,loc,.0105,.005,METAL,vertices=12,bevel=.001,axis=axis)
    # The dark slot is independent geometry, not a pre-painted bolt.
    dims={'Y':(.011,.001,.0018),'X':(.001,.011,.0018),'Z':(.011,.0018,.001)}[axis]
    pos=list(loc);pos[{'X':0,'Y':1,'Z':2}[axis]]+= {'X':1,'Y':-1,'Z':1}[axis]*.003
    box(name+'_slot',pos,dims,DARK,.0005,'07 Hardware',seg=1,smooth=False)
    return o

# Main rounded cabinet with actual inset front cavities.
shell=box('Body_MainShell_LightVariant',(0,0,.90),(1.12,.76,1.50),BODY,.135,seg=8)
cut=box('_cut_display',(-.125,-.37,1.015),(.80,.94,1.065),BODY,.068,seg=6)
bool_difference(shell,cut)
cut=box('_cut_delivery',(-.13,-.41,.315),(.55,.50,.165),BODY,.037,seg=5)
bool_difference(shell,cut)
shell['design_note']='Single connected rounded outer case with two real boolean recesses; no image-box cabinet.'

# Window front armor bezel, deep dark inner reveal and visible rear liner.
ring('Display_OuterBezel',(-.125,-.396,1.015),(.815,1.08),(.740,.995),.046,DARK,.078,.055)
ring('Display_InnerReveal',(-.125,-.312,1.015),(.75,1.00),(.704,.954),.168,CAVITY,.055,.039)
box('Display_Interior_Back',(-.125,.080,1.015),(.726,.025,.975),CAVITY,.040,'02 Front display',seg=4)
box('Display_Interior_Left',(-.474,-.095,1.01),(.018,.33,.914),CAVITY,.006,'02 Front display')
box('Display_Interior_Right',(.224,-.095,1.01),(.018,.33,.914),CAVITY,.006,'02 Front display')
box('Display_Interior_Ceiling',(-.125,-.095,1.482),(.67,.34,.025),CAVITY,.008,'02 Front display')

# Three shelves, inset product supports and price rails.
for row,z in enumerate([.522,.824,1.126]):
    box(f'Shelf_{row+1}',(-.125,-.115,z),(.686,.407,.025),SHELF,.012,'04 Products and shelves')
    box(f'Shelf_{row+1}_FrontRail',(-.125,-.323,z+.009),(.69,.028,.041),SLATE,.009,'04 Products and shelves')
    for col,x in enumerate([-.383,-.217,-.051,.115]):
        box(f'Price_{row+1}_{col+1}_Tag',(x,-.339,z+.010),(.057,.002,.020),DARK,.003,'04 Products and shelves',seg=2)
        text(f'Price_{row+1}_{col+1}',f'{row+1}{col+1}',(x,-.341,z+.009),.0105,PRINT,'04 Products and shelves')

def lathe_bottle(name,x,y,z,profile,material):
    # Stable quad strips; seam at rear. UV map assigned analytically later.
    segs=24;vs=[]
    for radius,height in profile:
        for j in range(segs):
            a=2*math.pi*j/segs;vs.append((x+radius*math.sin(a),y+radius*math.cos(a),z+height))
    fs=[]
    for k in range(len(profile)-1):
        for j in range(segs):fs.append((k*segs+j,k*segs+(j+1)%segs,(k+1)*segs+(j+1)%segs,(k+1)*segs+j))
    fs.append(tuple(range(segs-1,-1,-1)));fs.append(tuple((len(profile)-1)*segs+j for j in range(segs)))
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
    o['lathe_segments']=segs;o['lathe_profile']=json.dumps(profile);o['lathe_origin']=json.dumps([x,y,z])
    return finish(o,material,'04 Products and shelves')

profiles=[(.038,0),(.050,.006),(.056,.018),(.057,.035),(.057,.164),(.054,.182),(.041,.198),(.027,.206),(.027,.220)]
palette=[[0,1,2,3],[4,5,1,0],[3,1,4,2]]
for row,z in enumerate([.544,.846,1.148]):
    for col,x in enumerate([-.383,-.217,-.051,.115]):
        idx=palette[row][col]; y=-.245
        bottle=lathe_bottle(f'Bottle_R{row+1}_C{col+1}',x,y,z,profiles,BOTTLEMATS[idx])
        cylinder(f'Bottle_R{row+1}_C{col+1}_Cap',(x,y,z+.226),.030,.022,CAPMATS[idx],24,.005,'04 Products and shelves')
        # Each product has a curved cream label, a small distinct icon and a shoulder line.
        lab=box(f'Bottle_R{row+1}_C{col+1}_Label',(x,y-.057,z+.103),(.060,.006,.066),LABEL,.014,'04 Products and shelves',seg=4)
        if col%2==0:
            # Drop/leaf icon formed with a small lozenge and stem.
            icon=box(f'ProductIcon_{row+1}_{col+1}',(x,y-.061,z+.108),(.018,.002,.031),BOTTLEMATS[idx],.008,'04 Products and shelves',seg=3)
            icon.rotation_euler[1]=.36 if col==0 else -.36
            box(f'IconStem_{row+1}_{col+1}',(x,y-.063,z+.087),(.003,.002,.014),BOTTLEMATS[idx],.001,'04 Products and shelves')
        else:
            cylinder(f'ProductIcon_{row+1}_{col+1}',(x,y-.062,z+.107),.014,.002,BOTTLEMATS[idx],20,.001,'04 Products and shelves',axis='Y')
            box(f'IconStripe_{row+1}_{col+1}',(x,y-.064,z+.088),(.025,.002,.003),BOTTLEMATS[idx],.001,'04 Products and shelves')

# Light bars inside product bay with actual luminous geometry.
box('Interior_Top_LightFrame',(-.125,-.315,1.463),(.626,.030,.024),LAMPFRAME,.009,'05 Lighting')
box('Interior_Top_AmberStrip',(-.125,-.334,1.460),(.589,.008,.010),AMBER,.004,'05 Lighting')
for x in [-.463,.212]:
    box('Interior_Vertical_Light_'+str(x),(x,-.325,1.01),(.013,.022,.854),LAMPFRAME,.006,'05 Lighting')
    box('Interior_Vertical_Glow_'+str(x),(x,-.339,1.01),(.006,.006,.824),AMBER,.0025,'05 Lighting')

# Thin real glazing, separate material; no opaque fake product plane.
pane=box('Glass_FrontPane',(-.125,-.418,1.015),(.729,.003,.984),GLASS,.027,'02 Front display',seg=5)
pane['visibility_note']='Low alpha intentionally keeps the twelve real products legible; preview includes glass.'

# Lower delivery recess and lip, with depth and interior floor.
ring('Delivery_Hatch_Rim',(-.13,-.394,.315),(.574,.190),(.493,.119),.049,DARK,.042,.027,'08 Delivery hatch')
box('Delivery_Hatch_Back',(-.13,-.185,.315),(.497,.012,.123),DARK,.022,'08 Delivery hatch')
box('Delivery_Hatch_Floor',(-.13,-.272,.255),(.493,.185,.013),SLATE,.008,'08 Delivery hatch')
box('Delivery_Hatch_UpperShade',(-.13,-.277,.372),(.497,.18,.013),DARK,.006,'08 Delivery hatch')
box('Delivery_Front_Lip',(-.13,-.406,.251),(.459,.025,.018),METAL,.007,'08 Delivery hatch')
for x in [-.31,.05]:box('Delivery_GripRib_'+str(x),(x,-.323,.270),(.010,.082,.006),DARK,.003,'08 Delivery hatch')

# Front-right narrow control module and rounded light pocket.
box('Controls_Socket',(.413,-.373,.945),(.185,.055,.464),LAMPFRAME,.049,'06 Controls and graphics',seg=5)
box('Controls_Black_Module',(.413,-.411,.945),(.154,.035,.418),DARK,.038,'06 Controls and graphics',seg=5)
box('Controls_Touchscreen',(.413,-.434,1.004),(.113,.008,.212),SCREEN,.024,'06 Controls and graphics',seg=5)
text('Screen_AI','AI',(.413,-.440,1.038),.028,CYAN)
text('Screen_READY','READY',(.413,-.440,.987),.010,CYAN)
for i in range(3):box(f'Screen_Status_{i}',(.395+.018*i,-.441,.956),(.008,.001,.003),CYAN,.001,'06 Controls and graphics',seg=1)
ring('Controls_Amber_Button',(.413,-.437,.836),(.069,.069),(.046,.046),.010,AMBER,.013,.007,'06 Controls and graphics')
box('Controls_Button_Center',(.413,-.438,.836),(.042,.010,.042),DARK,.007,'06 Controls and graphics')
box('Controls_Payment_Slot',(.413,-.438,.777),(.073,.007,.008),SCREEN,.003,'06 Controls and graphics')
text('Screen_NFC',')))',(.413,-.441,.906),.014,PRINT)
box('Front_Right_Light_Recess',(.413,-.369,1.348),(.088,.045,.287),LAMPFRAME,.040,'05 Lighting',seg=5)
box('Front_Right_Amber_Light',(.413,-.395,1.348),(.035,.012,.232),AMBER,.016,'05 Lighting',seg=5)
box('Front_Lower_Access_Plate',(.412,-.356,.659),(.133,.022,.075),BODY,.018,'01 Cabinet',seg=4)
tag_dz=1.602-1.515;tag_r=.135;tag_nz=tag_dz/tag_r;tag_ny=-math.sqrt(1-tag_nz*tag_nz)
tag=text('Front_Model_Tag','AI / 12',(-.118,-.245+tag_r*tag_ny+.0007*tag_ny,1.602+.0007*tag_nz),.025,DARK)
tag.rotation_euler[0]=math.atan2(-tag_ny,tag_nz)

# Soft slate armor wraps the lower corners and side upright bumper columns.
for s in [-1,1]:
    xs=s*.552
    box(f'Side_{s}_UprightArmor',(xs,.233,1.036),(.082,.218,1.039),SLATE,.041,'03 Armor',seg=5)
    box(f'Side_{s}_Ivory_Inset',(s*.568,-.072,1.055),(.028,.356,.933),BODY,.014,'01 Cabinet',seg=4)
    # Lower end-cap cheek in front elevation; distinct wrap with sloped top.
    coords=[(s*x,z) for x,z in [(.355,.151),(.533,.160),(.600,.235),(.600,.540),(.510,.571),(.420,.428)]]
    if s<0:coords.reverse()
    prism_profile(f'Lower_{s}_Armor_Cheek',coords,.714,.006,SLATE,bevel=.035)
    # Front-facing warm light in each lower cheek, within a dark recess.
    box(f'Lower_{s}_LampSocket',(s*.520,-.370,.260),(.071,.037,.112),DARK,.030,'05 Lighting',seg=4)
    box(f'Lower_{s}_AmberLamp',(s*.520,-.392,.260),(.029,.010,.068),AMBER,.013,'05 Lighting',seg=4)
    # Side strip: narrow luminous slot faces outward on X.
    box(f'Side_{s}_LampFrame',(s*.606,.230,1.104),(.025,.084,.588),DARK,.012,'05 Lighting',seg=5)
    box(f'Side_{s}_Lamp_Recess',(s*.623,.230,1.104),(.012,.049,.530),LAMPFRAME,.006,'05 Lighting',seg=4)
    box(f'Side_{s}_AmberStrip',(s*.632,.230,1.104),(.007,.022,.472),AMBER,.003,'05 Lighting',seg=4)
    box(f'Side_{s}_Small_ServiceTab',(s*.609,.230,.751),(.016,.072,.090),DARK,.008,'03 Armor',seg=3)
    # Short curved side seam line and handle.
    box(f'Side_{s}_Handle_Recess',(s*.592,-.150,.536),(.012,.075,.125),DARK,.006,'03 Armor',seg=4)
    box(f'Side_{s}_Handle',(s*.607,-.150,.539),(.021,.014,.079),METAL,.007,'07 Hardware')
    for y,z in [(-.204,.660),(-.204,1.443),(.058,.660),(.058,1.443)]:
        screw(f'Side_{s}_PanelBolt_{y}_{z}',(s*.584,y,z),'X')

# Undertray and four short isolated feet; no support hidden by floor.
box('Underside_Dark_Tray',(0,.015,.161),(1.005,.646,.086),DARK,.040,'03 Armor',seg=5)
for sx in [-1,1]:
    for sy in [-1,1]:
        foot=cylinder(f'Foot_{sx}_{sy}_Rubber',(sx*.443,sy*.275,.056),.108,.070,RUBBER,32,.017,'09 Feet')
        foot.scale.y=.82
        neck=cylinder(f'Foot_{sx}_{sy}_Mount',(sx*.443,sy*.275,.110),.073,.064,SLATE,24,.012,'09 Feet')
        screw(f'Foot_{sx}_{sy}_Fastener',(sx*.443,sy*.275,.146),axis='Z')

# Rear: genuine framed panel, accessible screw heads and discrete ventilation slats.
box('Rear_ServicePanel_Shadow',(0,.375,.974),(.806,.027,1.065),DARK,.062,'10 Rear service',seg=5)
box('Rear_ServicePanel_LightVariant',(0,.397,.974),(.776,.025,1.034),BODY,.058,'10 Rear service',seg=5)
box('Rear_Upper_HandlePocket',(0,.419,1.409),(.237,.018,.046),DARK,.018,'10 Rear service',seg=4)
box('Rear_Upper_Handle',(0,.430,1.415),(.180,.014,.012),METAL,.005,'10 Rear service')
box('Rear_Vent_Recess',(0,.418,.838),(.440,.025,.271),DARK,.038,'10 Rear service',seg=5)
box('Rear_Vent_Perimeter',(0,.435,.838),(.411,.014,.240),SLATE,.028,'10 Rear service',seg=4)
for k in range(5):
    box(f'Rear_VentSlot_{k}',(0,.446,.754+k*.042),(.338,.012,.019),DARK,.008,'10 Rear service',seg=3)
    box(f'Rear_VentSlat_{k}',(0,.450,.768+k*.042),(.329,.014,.013),METAL,.005,'10 Rear service',seg=3)
box('Rear_Lower_KickPlate',(0,.379,.293),(.674,.061,.193),SLATE,.045,'10 Rear service',seg=5)
box('Rear_CablePocket',(0,.421,.281),(.284,.033,.089),DARK,.025,'10 Rear service',seg=4)
for k in range(4):box(f'Rear_CableRib_{k}',(0,.441,.255+k*.016),(.218,.010,.005),SLATE,.002,'10 Rear service')
for x in [-.341,.341]:
    for z in [.507,1.426]:screw(f'RearPanelBolt_{x}_{z}',(x,.416,z),axis='Y')
# Plate printed elements are separate material, not part of the tintable shell.
box('Rear_Serial_Plate',(.215,.421,.606),(.146,.010,.058),METAL,.007,'10 Rear service')
for k in range(5):box(f'Rear_Serial_Line_{k}',(.180+k*.018,.428,.607),(.006,.002,.031),DARK,.001,'10 Rear service',seg=1)

# Top service plate, two small amber markers and protected beacon.
box('Top_Service_Gasket',(0,.015,1.641),(.664,.489,.039),DARK,.072,'11 Top service',seg=5)
box('Top_Service_SlatePlate',(0,.015,1.664),(.629,.461,.041),SLATE,.065,'11 Top service',seg=5)
box('Top_Service_CenterStrip',(0,-.016,1.689),(.325,.375,.009),DARK,.032,'11 Top service',seg=4)
for x in [-.230,.230]:
    screw('Top_Plate_Screw_'+str(x),(x,-.102,1.691),'Z')
    marker=box('Top_AmberMarker_'+str(x),(x*1.74,-.197,1.590),(.042,.049,.020),AMBER,.010,'05 Lighting',seg=3)
    marker.rotation_euler[1]=-.26 if x>0 else .26
cylinder('Beacon_Base',(.320,.175,1.667),.059,.051,DARK,32,.012,'11 Top service')
cylinder('Beacon_MetalCollar',(.320,.175,1.705),.045,.035,METAL,32,.006,'11 Top service')
cylinder('Beacon_AmberLens',(.320,.175,1.749),.033,.067,AMBER,32,.011,'05 Lighting')
cylinder('Beacon_Cap',(.320,.175,1.792),.038,.032,SLATE,32,.010,'11 Top service')
for angle in [-.65,.65,math.pi-.65,math.pi+.65]:
    x=.320+.035*math.cos(angle);y=.175+.035*math.sin(angle)
    cylinder('Beacon_Guard_'+str(angle),(x,y,1.748),.0055,.072,DARK,12,.002,'11 Top service')

# A few restrained fasteners, front shell seams and hinge cues.
for x,z in [(-.476,1.561),(.490,1.556),(-.471,.442),(.310,.438),(-.422,.219),(.310,.220)]:
    screw(f'FrontBodyBolt_{x}_{z}',(x,-.366,z),'Y')
for s in [-1,1]:
    for z in [.669,1.473]:
        box(f'SideHinge_{s}_{z}',(s*.570,.285,z),(.047,.082,.096),DARK,.020,'07 Hardware')
        cylinder(f'SideHingePin_{s}_{z}',(s*.593,.285,z),.013,.083,METAL,16,.004,'07 Hardware',axis='Z')

# Apply transforms and weld coincident vertices before UV work.
for o in ASSET:
    bpy.context.view_layer.objects.active=o
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(o.data);bm.free();o.data.update()

# Source materials use generated coordinates; source UVs are installed during finalization.
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32
scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=1000;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=0;scene.world.color=(.35,.35,.35)
world=scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.68,.74,.78,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.38

stage=bpy.data.collections.new('STUDIO_NOT_EXPORTED');scene.collection.children.link(stage)
def stage_obj(o):
    for c in list(o.users_collection):c.objects.unlink(o)
    stage.objects.link(o);return o
groundmat=mat('STUDIO_Ground','#b8c4c6',.82)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.015));ground=stage_obj(bpy.context.object);ground.name='Studio_Ground';ground.data.materials.append(groundmat)
def area(name,loc,power,size,target=(0,0,.85),col=(1,1,1),shape='DISK',size_y=None):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape=shape;d.size=size;d.color=col
    if size_y and shape=='RECTANGLE':d.size_y=size_y
    o=bpy.data.objects.new(name,d);stage.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
area('Key_Softbox',(-3.5,-4.2,5.2),430,4.0,col=(1,.91,.79))
area('Fill_Softbox',(3.7,-2.5,2.7),230,3.0,col=(.79,.9,1))
area('Rim_Softbox',(1.7,3.0,4.0),490,3.0,col=(.88,.95,1))
area('Interior_Fill',(-.125,-.346,1.43),1.6,.55,target=(-.125,-.10,.85),col=(1,.62,.25),shape='RECTANGLE',size_y=.03)

def camera(name,loc,target,ortho=2.8):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);stage.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=ortho;d.lens=55;return o
cam=camera('Camera_Hero',(2.6,-6.3,3.0),(0,0,.88),2.43);scene.camera=cam
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.render.film_transparent=False
scene['asset_name']='VendingMachine';scene['front_axis']='-Y';scene['generated_texture_source']='source/imagegen_provenance.json'
scene['body_variants']='Only BODY_VARIANT_WHITE is the light-shell material. White factor; ivory texture.'
scene['asset_build_started_utc']=utc()
for im in bpy.data.images:
    if im.source=='FILE':im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/VendingMachine_prebake.blend'))
scene.render.filepath=str(ROOT/'renders/preview_hero.png');bpy.ops.render.render(write_still=True)
data={'timestamp_utc':utc(),'build_seconds':time.time()-T0,'objects':len(ASSET),'vertices':sum(len(o.data.vertices) for o in ASSET),'polygons':sum(len(o.data.polygons) for o in ASSET),'preview':'renders/preview_hero.png'}
(ROOT/'validation/build_preview.json').write_text(json.dumps(data,indent=2),encoding='utf8')
print('VENDING_BUILD_DONE '+json.dumps(data),flush=True)
