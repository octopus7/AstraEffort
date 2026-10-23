"""Reference-led SSTO asset. Run in a separate Blender 4.5 background process."""
import bpy, bmesh, math, json, time, os
from pathlib import Path
from mathutils import Vector
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
START = time.time()
TAU = math.tau
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.threads_mode = 'FIXED'
scene.render.threads = 4
scene.view_settings.view_transform = 'AgX'
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.world.color = (0.16, 0.19, 0.23)
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.20,0.25,0.32,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.45
ASSET = bpy.data.collections.new('SSTO_ASSET')
scene.collection.children.link(ASSET)
STUDIO = bpy.data.collections.new('STUDIO_NOT_EXPORTED')
scene.collection.children.link(STUDIO)
objects = []

def log(s):
    print('SSTO: '+s, flush=True)

def material(name, color, metallic=0.0, rough=0.5, texture=None, emission=None):
    mat=bpy.data.materials.new(name); mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Metallic'].default_value=metallic
    bs.inputs['Roughness'].default_value=rough
    if texture:
        tex=mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex.name='Generated_Source_Albedo'; tex.label='Original image_gen surface'
        tex.image=bpy.data.images.load(str(ROOT/'textures'/texture),check_existing=True)
        uv=mat.node_tree.nodes.new('ShaderNodeTexCoord')
        scale=mat.node_tree.nodes.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=5.0
        mat.node_tree.links.new(uv.outputs['UV'],scale.inputs[0]);mat.node_tree.links.new(scale.outputs['Vector'],tex.inputs['Vector'])
        mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    if emission:
        bs.inputs['Emission Color'].default_value=(*emission,1)
        bs.inputs['Emission Strength'].default_value=2.0
    return mat

ivory=material('01_Ivory_Ceramic',(.8,.77,.68),.15,.43,'generated_ivory_ceramic.png')
blue=material('02_Slate_Enamel',(.14,.23,.31),.32,.37,'generated_slate_armor.png')
dark=material('03_Thermal_Graphite',(.032,.043,.052),.42,.51)
metal=material('04_Titanium',(.25,.29,.31),.82,.31)
gold=material('05_Heat_Titanium',(.24,.16,.075),.72,.38)
orange=material('06_Safety_Amber',(.95,.41,.055),.15,.36)
glass=material('07_Cockpit_Glass',(.025,.06,.095),.35,.22)
glass.node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.3
rubber=material('08_Footpad_Carbon',(.025,.027,.029),.05,.70)
lightblue=material('09_Position_Light',(.025,.32,.45),.1,.22,emission=(.025,.48,.65))
MATS=[ivory,blue,dark,metal,gold,orange,glass,rubber,lightblue]

def relink(o, collection=ASSET):
    for col in list(o.users_collection): col.objects.unlink(o)
    collection.objects.link(o)

def finish(o,name,mat,group='Hull',bevel=0,smooth=True):
    o.name=name; relink(o); o.data.materials.append(mat)
    o['assembly']=group
    if smooth:
        for p in o.data.polygons: p.use_smooth=True
    if bevel:
        mod=o.modifiers.new('Manufactured soft edges','BEVEL');mod.width=bevel;mod.segments=3
        mod.limit_method='ANGLE'
        mod=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');mod.keep_sharp=True
    objects.append(o)
    return o

def mesh(name,verts,faces,mat,group='Hull',bevel=0,smooth=True):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new(name,me);ASSET.objects.link(o)
    return finish(o,name,mat,group,bevel,smooth)

def uv_sphere(name,location,scale,mat,group='Details',segments=16,rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=location)
    o=bpy.context.object;o.scale=scale
    return finish(o,name,mat,group)

def cylinder(name,a,b,r,mat,group='Details',vertices=24,r2=None,bevel=0.025):
    a,b=Vector(a),Vector(b);v=b-a
    bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=r,radius2=r if r2 is None else r2,depth=v.length,location=(a+b)/2)
    o=bpy.context.object;o.rotation_euler=v.to_track_quat('Z','Y').to_euler()
    return finish(o,name,mat,group,bevel)

def torus(name,center,major,minor,mat,group='Details',axis=(0,0,1)):
    bpy.ops.mesh.primitive_torus_add(major_segments=48,minor_segments=8,location=center,major_radius=major,minor_radius=minor)
    o=bpy.context.object;o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
    return finish(o,name,mat,group)

PROFILE=[(2.95,2.45),(3.2,2.95),(3.8,3.63),(5.0,4.03),(7.3,4.23),(10.0,4.25),(12.8,4.05),(15.5,3.61),(17.8,3.04),(19.8,2.30),(21.5,1.54),(22.7,.94),(23.55,.53),(23.92,.27),(24.0,.015)]
def radius(z):
    for i in range(len(PROFILE)-1):
        z0,r0=PROFILE[i];z1,r1=PROFILE[i+1]
        if z0<=z<=z1:
            m0=(r1-PROFILE[max(i-1,0)][1])/(z1-PROFILE[max(i-1,0)][0])
            m1=(PROFILE[min(i+2,len(PROFILE)-1)][1]-r0)/(PROFILE[min(i+2,len(PROFILE)-1)][0]-z0)
            t=(z-z0)/(z1-z0)
            return (2*t**3-3*t*t+1)*r0+(t**3-2*t*t+t)*(z1-z0)*m0+(-2*t**3+3*t*t)*r1+(t**3-t*t)*(z1-z0)*m1
    return PROFILE[0][1] if z<PROFILE[0][0] else PROFILE[-1][1]

def hullpt(theta,z,offset=0):
    r=radius(z)+offset
    return (r*math.cos(theta),r*.91*math.sin(theta),z)

def lathe(name,profile,mat,group='Hull',center=(0,0),seg=64,yscale=1,cap=True):
    verts=[(center[0]+r*math.cos(TAU*j/seg),center[1]+r*yscale*math.sin(TAU*j/seg),z) for z,r in profile for j in range(seg)]
    faces=[]
    for i in range(len(profile)-1):
        for j in range(seg):faces.append((i*seg+j,i*seg+(j+1)%seg,(i+1)*seg+(j+1)%seg,(i+1)*seg+j))
    if cap: faces.extend([tuple(reversed(range(seg))),tuple((len(profile)-1)*seg+j for j in range(seg))])
    return mesh(name,verts,faces,mat,group)

log('Build continuous hull and conformal panel shell')
lathe('Pressure_hull',[(2.95+i*(21.05/100),max(.006,radius(2.95+i*(21.05/100))-.028)) for i in range(101)],dark,yscale=.91)

def panel(name,a0,a1,z0,z1,mat,group='Hull',offset=.02,nx=6,nz=10):
    verts=[hullpt(a0+(a1-a0)*j/nx,z0+(z1-z0)*i/nz,offset) for i in range(nz+1) for j in range(nx+1)]
    faces=[(i*(nx+1)+j,i*(nx+1)+j+1,(i+1)*(nx+1)+j+1,(i+1)*(nx+1)+j) for i in range(nz) for j in range(nx)]
    o=mesh(name,verts,faces,mat,group)
    so=o.modifiers.new('Plate thickness','SOLIDIFY');so.thickness=.035
    be=o.modifiers.new('Panel edge radius','BEVEL');be.width=.018;be.segments=2;be.limit_method='ANGLE'
    return o

bands=[(3.55,7.45),(7.49,12.0),(12.04,16.45),(16.49,21.4)]
for b,(lo,hi) in enumerate(bands):
    for s in range(12):
        a0=TAU*s/12-TAU/24+.0035;a1=a0+TAU/12-.007
        mat=blue if (b==0 and s in (2,3,4)) or (b==3 and s in (2,3,4)) else ivory
        panel('Hull_plate_%02d_%02d'%(b,s),a0,a1,lo,hi,mat)
for s in range(8):
    panel('Nose_cap_%02d'%s,TAU*s/8+.004,TAU*(s+1)/8-.004,21.44,23.88,blue,offset=.025,nx=8,nz=12)
lathe('Nose_tip',[(23.8,radius(23.8)+.026),(23.92,.295),(23.98,.15),(24,.025)],blue,yscale=.91)

def patch(name,angle,zc,aw,zh,offset,mat,group='Details',power=4.0):
    seg=48;steps=5;verts=[hullpt(angle,zc,offset)]
    for k in range(1,steps+1):
        for j in range(seg):
            t=TAU*j/seg
            u=math.copysign(abs(math.cos(t))**(2/power),math.cos(t))
            v=math.copysign(abs(math.sin(t))**(2/power),math.sin(t))
            verts.append(hullpt(angle+u*aw*k/steps,zc+v*zh*k/steps,offset))
    faces=[(0,1+j,1+(j+1)%seg) for j in range(seg)]
    for k in range(steps-1):
        lo=1+k*seg;up=lo+seg
        for j in range(seg):faces.append((lo+j,up+j,up+(j+1)%seg,lo+(j+1)%seg))
    o=mesh(name,verts,faces,mat,group)
    so=o.modifiers.new('Inlaid plate thickness','SOLIDIFY');so.thickness=.025
    return o

front=-math.pi/2
patch('Cockpit_outer_frame',front,19.95,.57,1.9,.095,ivory,'Cockpit')
patch('Cockpit_recess_gasket',front,19.95,.524,1.74,.13,dark,'Cockpit')
patch('Cockpit_panoramic_glazing',front,19.98,.486,1.63,.16,glass,'Cockpit',4.8)
for a in (-.56,0,.56):
    patch('Upper_navigation_window_frame',front+a,22.38,.115,.22,.085,dark,'Cockpit',3)
    patch('Upper_navigation_window',front+a,22.38,.078,.15,.115,glass,'Cockpit',3)
for a in (-2.25,-.9):
    patch('Cockpit_lock',a,21.32,.022,.07,.09,gold,'Cockpit',3)

patch('Crew_hatch_seal',front,12.72,.221,3.36,.075,dark)
patch('Crew_hatch_cover',front,12.72,.211,3.31,.102,ivory)
patch('Crew_hatch_instrument_mount',front,14.86,.12,.98,.14,blue)
patch('Crew_hatch_instrument_glass',front,15.09,.077,.60,.17,glass)
patch('Crew_hatch_recess_latch',front,14.30,.042,.12,.19,gold)
patch('Lower_service_hatch_seal',front,8.03,.132,.86,.075,dark)
patch('Lower_service_hatch',front,8.03,.115,.78,.105,ivory)
patch('Lower_service_hatch_grip',front,7.95,.046,.52,.13,metal)
patch('Rear_access_backing',math.pi/2,14.62,.23,2.2,.09,dark)
patch('Rear_access_panel',math.pi/2,14.62,.214,2.15,.125,blue)
patch('Rear_access_handle',math.pi/2,14.8,.035,1.25,.16,metal)
patch('Front_lower_blue_fairing',front,4.85,.37,1.3,.11,blue)
for angle in (-.48, -2.66):
    panel('Amber_shoulder_stripe',angle-.025,angle+.025,14.7,18.05,orange,offset=.055,nx=2,nz=14)
    panel('Amber_shoulder_return',angle-.025,angle+.20,14.68,14.88,orange,offset=.06,nx=6,nz=2)
for side in (0,math.pi):
    patch('Side_lock_backing',side,12.6,.12,1.0,.08,dark)
    patch('Side_lock_plate',side,12.6,.094,.9,.105,blue)
    patch('Side_lock_handle',side,12.6,.028,.54,.14,metal)
    patch('Thermal_vent_backing',side,6.1,.23,.5,.085,dark)
    for j in range(6):
        panel('Vent_slat',side-.18+j*.064,side-.153+j*.064,5.78,6.45,metal,offset=.115,nx=1,nz=2)

log('Add fasteners, landing outriggers and hollow engines')
for z in (4.05,7.15,12.32,16.15,21.15):
    for s in range(12):
        a=TAU*s/12+.17
        if abs((a-front+math.pi)%TAU-math.pi)<.5 and z>18:continue
        p=Vector(hullpt(a,z,.095));n=Vector((math.cos(a),math.sin(a),.10)).normalized()
        cylinder('Flush_panel_fastener',p,p+n*.028,.055,metal,vertices=8,bevel=.008)
for a in (-.46,-2.68):
    for z in (8.8,10.1,11.4):
        patch('Hatch_hinge',a,z,.034,.20,.095,metal)

def finmesh(name,poly,angle,width,mat,group,bevel=.12):
    direction=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-math.sin(angle),math.cos(angle),0))
    verts=[tuple(direction*r+side*t+Vector((0,0,z))) for t in (-width/2,width/2) for r,z in poly]
    n=len(poly);faces=[tuple(reversed(range(n))),tuple(n+j for j in range(n))]
    faces +=[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
    return mesh(name,verts,faces,mat,group,bevel)

for idx,ang in enumerate((math.radians(210),math.radians(330),math.radians(90))):
    group=('Landing_Port','Landing_Starboard','Landing_Aft')[idx]
    d=Vector((math.cos(ang),math.sin(ang),0));side=Vector((-math.sin(ang),math.cos(ang),0))
    finmesh('Swept_landing_fairing',[(3.35,3.55),(3.52,10.7),(4.04,9.0),(5.55,5.65),(6.05,2.0),(5.72,1.55),(4.96,1.72),(4.22,3.18)],ang,.78,ivory,group,.21)
    finmesh('Slate_outer_landing_shield',[(4.35,5.96),(4.92,6.62),(5.55,5.55),(6.05,2.05),(5.69,1.69),(5.04,1.87),(4.62,3.57)],ang,.83,blue,group,.17)
    finmesh('Amber_landing_shoulder',[(4.18,6.43),(4.57,7.40),(4.90,6.70),(4.40,5.82)],ang,.82,orange,group,.10)
    foot=d*5.6
    cylinder('Footpad',(*foot[:2],.10),(*foot[:2],.31),.67,rubber,group,48,r2=.61,bevel=.08)
    cylinder('Footpad_upper_plate',(*foot[:2],.31),(*foot[:2],.43),.51,metal,group,40,bevel=.04)
    torus('Footpad_rim',(*foot[:2],.23),.60,.045,dark,group)
    cylinder('Landing_piston',tuple(d*5.6+Vector((0,0,.4))),tuple(d*5.48+Vector((0,0,1.86))),.16,metal,group,24)
    cylinder('Landing_piston_sleeve',tuple(d*5.56+Vector((0,0,.75))),tuple(d*5.49+Vector((0,0,1.57))),.25,dark,group,24)
    cylinder('Articulated_brace',tuple(d*4.45+Vector((0,0,3.6))),tuple(d*5.54+Vector((0,0,1.05))),.115,metal,group,20)
    for z,rad in ((1.32,5.53),(3.5,4.49)):
        point=d*rad+Vector((0,0,z));cylinder('Landing_hinge',point-side*.55,point+side*.55,.22,gold,group,24)
    for r,z in ((5.73,2.18),(5.25,4.23),(4.82,5.72)):
        for sign in (-1,1):
            p=d*r+side*(sign*.43)+Vector((0,0,z));cylinder('Fin_fastener',p,p+side*sign*.024,.07,metal,group,8,bevel=.008)
    p=d*5.64+Vector((0,0,2.78))
    uv_sphere('Landing_position_light',p,(.10,.10,.13),lightblue,group)

# Small rear flight-control fins stay visibly separate from the landing fairings.
for ang in (math.radians(38),math.radians(142)):
    finmesh('Rear_control_fin',[(3.15,11.4),(3.58,14.45),(5.12,10.35),(5.32,7.55),(4.94,7.37),(3.75,8.55)],ang,.22,blue,'Control_Fins',.14)
    finmesh('Rear_control_fin_inset',[(3.7,10.8),(3.91,12.5),(4.86,10.0),(4.99,7.9),(4.7,7.85),(4.05,8.9)],ang,.25,ivory,'Control_Fins',.08)

lathe('Engine_deck',[(2.85,2.55),(3.12,3.12),(3.42,3.2),(3.6,3.09)],metal,'Engine_Deck',seg=80,yscale=.91)
torus('Engine_deck_thermal_ring',(0,0,3.11),2.95,.12,dark,'Engine_Deck')
for i,(x,y) in enumerate(((0,-1.52),(-1.56,1.02),(1.56,1.02))):
    group='Engine_%02d'%(i+1)
    # Closed thickness cross section: outer wall, lip, inner wall, throat.
    prof=[(3.25,.56),(2.98,.65),(2.72,.57),(2.48,.62),(2.14,.75),(1.62,.99),(1.25,1.12),(1.15,1.11),(1.15,1.00),(1.30,1.01),(1.68,.87),(2.14,.64),(2.48,.50),(2.73,.44),(3.25,.46),(3.25,.56)]
    lathe('Hollow_regenerative_bell',prof,dark,group,center=(x,y),seg=64,cap=False)
    for z,r in ((1.24,1.095),(1.48,1.02),(2.19,.72),(2.56,.61),(2.86,.60)):
        torus('Nozzle_reinforcement_ring',(x,y,z),r,.045,metal if z<2 else gold,group)
    lathe('Engine_mount_armor',[(2.82,.68),(3.12,.84),(3.48,.86),(3.70,.73)],blue,group,center=(x,y),seg=48)
    for j in range(12):
        a=TAU*j/12
        p1=(x+.68*math.cos(a),y+.68*math.sin(a),2.45)
        p2=(x+.99*math.cos(a),y+.99*math.sin(a),1.48)
        cylinder('Regenerative_cooling_channel',p1,p2,.024,metal,group,8,bevel=0)
    cylinder('Dark_combustion_throat',(x,y,2.74),(x,y,2.83),.43,rubber,group,32,bevel=0)
    torus('Throat_thermal_lip',(x,y,2.69),.43,.05,gold,group)

for j in range(12):
    a=TAU*j/12
    cylinder('Deck_lock',(2.87*math.cos(a),2.61*math.sin(a),2.98),(2.87*math.cos(a),2.61*math.sin(a),3.15),.09,gold,'Engine_Deck',8)

log('Apply modifiers and preserve named assembly groups')
for o in objects:
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for mod in list(o.modifiers):
        try:bpy.ops.object.modifier_apply(modifier=mod.name)
        except RuntimeError:pass
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    vg=o.vertex_groups.new(name=o.name);vg.add(list(range(len(o.data.vertices))),1,'REPLACE')

groups=defaultdict(list)
for o in objects:groups[o['assembly']].append(o)
meshes=[]
for name,obs in groups.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join()
    o=bpy.context.object;o.name='SSTO_'+name;meshes.append(o)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)

# Ground-plane origin and exactly 24 m overall reference height.
for o in meshes:
    for v in o.data.vertices:v.co.z=(v.co.z-.10)*(24.0/23.9)

log('Unwrap all unique surfaces and normalize texel density')
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
bpy.context.scene.tool_settings.use_uv_select_sync=True
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(72),island_margin=0,area_weight=0,correct_aspect=True,scale_to_bounds=False)
bpy.ops.object.mode_set(mode='OBJECT')
# Eight analytical gores prevent the tapered hidden pressure hull from folding at the pole.
core=next(o for o in meshes if o.name=='SSTO_Hull')
gid=core.vertex_groups['Pressure_hull'].index
coreverts={v.index for v in core.data.vertices if any(g.group==gid for g in v.groups)}
uv=core.data.uv_layers.active
for p in core.data.polygons:
    if not all(v in coreverts for v in p.vertices):continue
    if len(p.vertices)>4:
        for li in p.loop_indices:
            v=core.data.vertices[core.data.loops[li].vertex_index].co
            uv.data[li].uv=(v.x+500,v.y+500+(50 if v.z>12 else 0))
        continue
    angles=[math.atan2(core.data.vertices[v].co.y/.91,core.data.vertices[v].co.x)%TAU for v in p.vertices]
    if max(angles)-min(angles)>math.pi:angles=[a+TAU if a<math.pi else a for a in angles]
    sector=int((sum(angles)/len(angles))/(TAU/8));mid=(sector+.5)*TAU/8
    for li,a in zip(p.loop_indices,angles):
        v=core.data.vertices[core.data.loops[li].vertex_index].co
        r=math.hypot(v.x,v.y/.91);uv.data[li].uv=(sector*40+r*(a-mid),v.z)
# Project microscopic bevel faces individually when normal grouping collapses their UV area.
repaired=0
for o in meshes:
    me=o.data;me.calc_loop_triangles();uv=me.uv_layers.active;bad=set()
    for t in me.loop_triangles:
        a,b,c=[uv.data[j].uv for j in t.loops]
        if abs((b-a).cross(c-a))<2e-14:bad.add(t.polygon_index)
    for pi in bad:
        p=me.polygons[pi];origin=me.vertices[p.vertices[0]].co
        edge=max((me.vertices[v].co-origin for v in p.vertices),key=lambda v:v.length).normalized()
        ortho=p.normal.cross(edge).normalized()
        extent=max((me.vertices[v].co-origin).length for v in p.vertices)
        for li in p.loop_indices:
            v=(me.vertices[me.loops[li].vertex_index].co-origin)/max(extent,1e-10)
            uv.data[li].uv=(10+repaired*2+v.dot(edge),10+v.dot(ortho))
        repaired+=1
log('Planar repair of %d microscopic bevel faces'%repaired)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.average_islands_scale()
log('Pack result '+str(bpy.ops.uv.pack_islands('EXEC_DEFAULT',rotate=True,scale=True,merge_overlap=False,margin_method='FRACTION',margin=.003,shape_method='CONVEX')))
bpy.ops.object.mode_set(mode='OBJECT')
for o in meshes:o.data.uv_layers.active.name='UV_Unique'

log('Bake generated albedo sources into the unique 4096 atlas')
atlas=bpy.data.images.new('SSTO_BaseColor_4096',width=4096,height=4096,alpha=False)
atlas.generated_color=(.1,.12,.14,1)
for mat in MATS:
    nodes=mat.node_tree.nodes
    for n in nodes:n.select=False
    node=nodes.new('ShaderNodeTexImage');node.name='Final_Unique_Atlas';node.image=atlas;node.select=True;nodes.active=node
    # Emit only the input albedo while baking; metallic/glass responses must not darken the map.
    bs=nodes.get('Principled BSDF');em=nodes.new('ShaderNodeEmission');em.name='Temporary_Albedo_Bake'
    if bs.inputs['Base Color'].is_linked:mat.node_tree.links.new(bs.inputs['Base Color'].links[0].from_socket,em.inputs['Color'])
    else:em.inputs['Color'].default_value=bs.inputs['Base Color'].default_value
    mat.node_tree.links.new(em.outputs[0],nodes.get('Material Output').inputs['Surface'])
scene.cycles.samples=1
scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True
scene.render.bake.margin=12
bpy.ops.object.bake(type='EMIT',use_clear=True,margin=12)
atlas.filepath_raw=str(ROOT/'textures'/'SSTO_BaseColor_4096.png');atlas.file_format='PNG';atlas.save()
for mat in MATS:
    nodes=mat.node_tree.nodes;bs=nodes.get('Principled BSDF')
    mat.node_tree.links.new(nodes['Final_Unique_Atlas'].outputs['Color'],bs.inputs['Base Color'])
    mat.node_tree.links.new(bs.outputs['BSDF'],nodes.get('Material Output').inputs['Surface'])
    nodes.remove(nodes['Temporary_Albedo_Bake'])

# Export only the asset before constructing the photographic stage.
log('Export self-contained GLB')
bpy.ops.export_scene.gltf(filepath=str(ROOT/'SSTO.glb'),export_format='GLB',use_selection=True,export_apply=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_animations=False,export_cameras=False,export_lights=False,export_extras=True)

def area_light(name,location,power,size,color,target=(0,0,12)):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    o=bpy.data.objects.new(name,data);STUDIO.objects.link(o);o.location=location;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    return o

floor=material('Studio_floor',(.14,.18,.23),.12,.48)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.015));stage=bpy.context.object;stage.name='Studio_floor_NOT_EXPORTED';relink(stage,STUDIO);stage.data.materials.append(floor)
area_light('Large_warm_key',(-17,-23,32),17000,15,(1.0,.88,.73))
area_light('Cool_edge',(14,12,27),23000,12,(.64,.79,1.0))
area_light('Soft_front_fill',(18,-12,15),10000,13,(.79,.88,1.0))
area_light('Nose_softbox',(-4,4,38),13000,11,(1.0,.95,.85))
camdata=bpy.data.cameras.new('Presentation_Camera');cam=bpy.data.objects.new('Presentation_Camera',camdata);STUDIO.objects.link(cam);scene.camera=cam
camdata.type='ORTHO';camdata.ortho_scale=30

def set_camera(position,target,scale):
    cam.location=position;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();camdata.ortho_scale=scale

scene.cycles.samples=40
scene.render.resolution_x=1300;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
set_camera((31,-46,29),(0,0,11.7),29.3)
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
for img in bpy.data.images:
    if img.source=='FILE' or img==atlas:
        try:img.pack()
        except:pass
for screen in bpy.data.screens:
    for ar in screen.areas:
        if ar.type=='VIEW_3D':
            ar.spaces.active.region_3d.view_perspective='CAMERA'
            ar.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'SSTO.blend'))
build={
    'blender':bpy.app.version_string,'reference':'REF/b425f2b5-a83a-4f47-bdbe-de826e5a13da.png',
    'asset_objects':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),'polygons':sum(len(o.data.polygons) for o in meshes),
    'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),
    'dimensions_m':[round(max((o.matrix_world@v.co)[i] for o in meshes for v in o.data.vertices)-min((o.matrix_world@v.co)[i] for o in meshes for v in o.data.vertices),4) for i in range(3)],
    'uv':'One global 0-1 atlas; no mirrors; smart projection, average island scale, global pack.',
    'requested_pack_margin_uv':.003,'requested_pack_margin_px_at_4096':12.288,'bake_dilation_px':12,
    'textures':['textures/SSTO_BaseColor_4096.png'],'build_elapsed_seconds':time.time()-START,
    'scope':'Exterior, deployed landing gear, no animation or interior cutaway',
    'normal_map':'None; relief and panel edges are geometry. Generated images supply albedo.',
}
(ROOT/'validation'/'build_manifest.json').write_text(json.dumps(build,indent=2),encoding='utf-8')
log('RENDER hero')
scene.render.filepath=str(ROOT/'renders'/'hero.png');bpy.ops.render.render(write_still=True)
log('BUILD_DONE')
