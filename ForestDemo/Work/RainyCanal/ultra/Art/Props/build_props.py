"""Original RainyCanal/ultra prop geometry. Blender 4.5 background authoring.
No external artwork, assets or project libraries are read.
"""
import bpy, math, json, os, sys, datetime, time
from mathutils import Vector

ROOT = r'D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Art/Props'
SCRATCH = r'D:/github/AstraEffort/ForestDemo/Saved/Workers/RainyCanal/ultra/Props'
os.makedirs(ROOT + '/FBX', exist_ok=True)
os.makedirs(ROOT + '/Preview', exist_ok=True)
START = datetime.datetime.now(datetime.timezone.utc)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in list(bpy.data.materials): bpy.data.materials.remove(block)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
COLORS = {'Stone':(.39,.43,.41,1),'Timber':(.24,.135,.073,1),
          'Metal':(.055,.075,.075,1),'WindowGlass':(.95,.54,.19,1),
          'RoofClay':(.40,.20,.13,1),'Leaf':(.12,.26,.13,1)}
MATS={}
for name,color in COLORS.items():
    mat=bpy.data.materials.new(name); mat.diffuse_color=color; mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=color
    bsdf.inputs['Roughness'].default_value=.42 if name=='Metal' else .68
    if name=='Metal': bsdf.inputs['Metallic'].default_value=.8
    if name=='WindowGlass':
        bsdf.inputs['Emission Color'].default_value=color
        bsdf.inputs['Emission Strength'].default_value=.8
    MATS[name]=mat
parts=[]
assets=[]

def addpart(obj, material, bevel=0):
    obj.data.materials.clear(); obj.data.materials.append(MATS[material])
    bpy.context.view_layer.objects.active=obj
    obj.select_set(True)
    if bevel:
        mod=obj.modifiers.new('Soft handmade edges','BEVEL')
        mod.width=bevel; mod.segments=1 if material=='Stone' else 2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    parts.append(obj)
    obj.select_set(False)
    return obj

def cube(name,loc,dim,mat,bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    obj=bpy.context.object; obj.name=name; obj.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return addpart(obj,mat,min(bevel,min(dim)*.23))

def cylinder(name,loc,radius,depth,mat,vertices=16,bevel=.015):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc)
    obj=bpy.context.object; obj.name=name
    return addpart(obj,mat,bevel)

def mesh(name,vs,fs,mat,bevel=0):
    data=bpy.data.meshes.new(name); data.from_pydata(vs,[],fs); data.update()
    obj=bpy.data.objects.new(name,data); scene.collection.objects.link(obj)
    return addpart(obj,mat,bevel)

def beam(name,a,b,width,depth,mat,bevel=.012):
    a,b=Vector(a),Vector(b); d=b-a
    obj=cube(name,(a+b)*.5,(width,depth,d.length),mat,bevel)
    obj.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    return obj

def cylbeam(name,a,b,r,mat,vertices=12):
    a,b=Vector(a),Vector(b); d=b-a
    obj=cylinder(name,(a+b)*.5,r,d.length,mat,vertices,min(r*.25,.012))
    obj.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    return obj

def prism_between(name,x0,x1,y0,y1,b0,b1,t0,t1,mat,bevel=0):
    return mesh(name,[(x0,y0,b0),(x1,y0,b1),(x1,y1,b1),(x0,y1,b0),
                      (x0,y0,t0),(x1,y0,t1),(x1,y1,t1),(x0,y1,t0)],
                     [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,bevel)

def top(x): return 1.1*(1-(x/8)**2)
def underside(x): return -.95+1.58*math.sqrt(max(0,1-(x/6)**2)) if abs(x)<6 else -.95

def finish(name,notes):
    global parts
    bpy.ops.object.select_all(action='DESELECT')
    for obj in parts: obj.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]
    bpy.ops.object.join(); obj=bpy.context.object; obj.name=name
    scene.cursor.location=(0,0,0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    if name=='SM_Bench':
        floor=min(v.co.z for v in obj.data.vertices)
        for vertex in obj.data.vertices: vertex.co.z-=floor
    # Consistent outside normals and remove zero-area accidental geometry.
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    # UV0: unique packed islands. 0.004 normalized margin is >2 pixels @1024.
    if not obj.data.uv_layers: obj.data.uv_layers.new(name='UVMap')
    obj.data.uv_layers[0].name='UVMap'
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.004,area_weight=.1,correct_aspect=True,scale_to_bounds=False)
    bpy.ops.uv.pack_islands(rotate=True,scale=True,margin_method='ADD',margin=.004)
    bpy.ops.object.mode_set(mode='OBJECT')
    for loopuv in obj.data.uv_layers[0].data:
        loopuv.uv=loopuv.uv*.994+Vector((.003,.003))
    # UV1 is a physical orthonormal projection per planar source polygon.
    # Eight scene meters = one 1024px tile = exactly 128px/m.
    uv=obj.data.uv_layers.new(name='Physical128')
    for poly in obj.data.polygons:
        n=poly.normal.normalized()
        ref=Vector((1,0,0)) if abs(n.x)<.91 else Vector((0,1,0))
        u=(ref-n*ref.dot(n)).normalized(); v=n.cross(u).normalized()
        for li in poly.loop_indices:
            p=obj.data.vertices[obj.data.loops[li].vertex_index].co
            uv.data[li].uv=(p.dot(u)/8,p.dot(v)/8)
    obj.data.uv_layers.active_index=0
    # Triangulate only AFTER UV authoring so flat surfaces retain coherent grain.
    triang=obj.modifiers.new('Export triangles','TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier=triang.name)
    obj.data.calc_loop_triangles()
    bounds=[[min(v.co[k] for v in obj.data.vertices),max(v.co[k] for v in obj.data.vertices)] for k in range(3)]
    notes.update(name=name,filename='FBX/'+name+'.fbx',bounds_m=bounds,
                 dimensions_m=[r[1]-r[0] for r in bounds],triangles=len(obj.data.loop_triangles),
                 materials=[m.name for m in obj.data.materials],uv_channels=[x.name for x in obj.data.uv_layers])
    bpy.ops.export_scene.fbx(filepath=ROOT+'/FBX/'+name+'.fbx',use_selection=True,
        object_types={'MESH'},axis_forward='-Y',axis_up='Z',global_scale=1,
        apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
        use_space_transform=True,bake_space_transform=False,mesh_smooth_type='FACE',
        use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,path_mode='AUTO')
    assets.append((obj,notes)); parts=[]
    obj.select_set(False)
    print('DELIVERED',name,json.dumps(notes),flush=True)
    return obj

# 1. Stone bridge: deck is a ribbon above a shaped structural arch, never a water-blocking box.
vs=[]; fs=[]; steps=40
for i in range(steps+1):
    x=-8+16*i/steps
    vs.extend([(x,-1.67,underside(x)),(x,1.67,underside(x)),(x,-1.67,top(x)),(x,1.67,top(x))])
for i in range(steps):
    j=i*4; k=j+4
    fs.extend([(j,k,k+1,j+1),(j+2,j+3,k+3,k+2),(j,j+2,k+2,k),(j+1,k+1,k+3,j+3)])
fs.extend([(0,1,3,2),(steps*4,steps*4+2,steps*4+3,steps*4+1)])
mesh('Continuous smooth arched walking deck',vs,fs,'Stone')
for side in [-1,1]:
    for i in range(32):
        x0=-8+i*.5+.008; x1=-8+(i+1)*.5-.008
        ya,yb=sorted((side*1.67,side*1.96))
        prism_between('Individual arch voussoir',x0,x1,ya,yb,underside(x0),underside(x1),top(x0),top(x1),'Stone',.012)
    for row in range(2):
        count=22; length=14.8/count
        for i in range(count):
            x0=-7.4+i*length+.01; x1=-7.4+(i+1)*length-.01
            ya,yb=sorted((side*1.65,side*1.98))
            prism_between('Rounded parapet masonry',x0,x1,ya,yb,top(x0)+row*.39,top(x1)+row*.39,
                          top(x0)+(row+1)*.39-.015,top(x1)+(row+1)*.39-.015,'Stone',.025)
    for i in range(22):
        x0=-7.4+i*14.8/22+.012; x1=-7.4+(i+1)*14.8/22-.012
        ya,yb=sorted((side*1.61,side*2.02))
        prism_between('Rounded coping',x0,x1,ya,yb,top(x0)+.78,top(x1)+.78,top(x0)+1,top(x1)+1,'Stone',.035)
finish('SM_StoneBridge',{'orientation':'X crosses canal; clear walk Y=3.22m; Z deck endpoints=0',
    'walkway_clear_width_m':3.22,'walk_surface_endpoints_m':[[-8,0,0],[8,0,0]],
    'walk_surface_center_m':[0,0,1.1],'underside_center_z_m':.63,'parapet_height_m':1,
    'waterway':'Open beneath arch. At canal water z=-1.2m, center vertical clearance=1.83m. Abutments outside |x|=6.',
    'collision_recommendation':'Use complex as simple for curved walking deck and parapets; no autogenerated convex full-span hull.'})

# 2. Timber footbridge, with planks, long girders, posts and handrails.
for i in range(48):
    cube('Deck plank',(-8+(i+.5)*16/48,0,-.075),(16/48-.012,3.3,.15),'Timber',.014)
for y in [-1.22,1.22]: cube('Long structural girder',(0,y,-.3),(16,.21,.31),'Timber',.025)
for y in [-1.64,1.64]:
    for x in [-7.85+i*15.7/8 for i in range(9)]:
        cube('Rail post',(x,y,.46),(.14,.14,1.08),'Timber',.024)
        cube('Post cap',(x,y,1.025),(.19,.19,.07),'Timber',.018)
    for z in [.43,.94]: cube('Hand rail',(0,y,z),(16,.12,.13),'Timber',.025)
finish('SM_TimberBridge',{'orientation':'X spans canal, clear walk Y=3.0m, deck top Z=0',
    'walk_surface_endpoints_m':[[-8,0,0],[8,0,0]],'walkway_clear_width_m':3.0,
    'collision_recommendation':'Complex as simple; supports are below the deck.'})

# 3. Canal lamp, warm panelled lantern and rounded antique cast-metal base.
cylinder('Foot',(0,0,.045),.24,.09,'Metal',20,.02)
cylinder('Base plinth',(0,0,.135),.175,.12,'Metal',16,.022)
cylinder('Base stem',(0,0,.4),.11,.43,'Metal',16,.018)
cylinder('Base collar',(0,0,.66),.14,.095,'Metal',16,.02)
cylinder('Lamp pole',(0,0,1.73),.065,2.1,'Metal',16,.012)
for z in [1.0,2.48,2.75]: cylinder('Decorative collar',(0,0,z),.092,.07,'Metal',16,.012)
cube('Lantern bottom',(0,0,2.84),(.48,.48,.09),'Metal',.035)
cube('Lantern top frame',(0,0,3.49),(.45,.45,.075),'Metal',.022)
for x in [-.195,.195]:
    for y in [-.195,.195]: cube('Lantern corner',(x,y,3.17),(.045,.045,.61),'Metal',.012)
for sign in [-1,1]:
    cube('Warm side panel X',(sign*.202,0,3.17),(.012,.345,.54),'WindowGlass',.003)
    cube('Warm side panel Y',(0,sign*.202,3.17),(.345,.012,.54),'WindowGlass',.003)
mesh('Pitched lantern hat',[(-.29,-.29,3.52),(.29,-.29,3.52),(.29,.29,3.52),(-.29,.29,3.52),(0,0,3.72)],
    [(0,3,2,1),(0,1,4),(1,2,4),(2,3,4),(3,0,4)],'Metal',.018)
cylinder('Finial',(0,0,3.745),.042,.11,'Metal',12,.012)
finish('SM_CanalLamp',{'orientation':'Origin foot Z=0; four glass panels centered Z=3.17m',
    'emission_material':'WindowGlass','light_location_local_m':[0,0,3.17],
    'collision_recommendation':'Simple convex is acceptable for this narrow prop; lamp fixture is visual.'})

# 4. Bench. Facing -Y, slats across X.
for y in [-.22,-.075,.075,.22]: cube('Seat slat',(0,y,.46),(1.7,.125,.075),'Timber',.022)
for x in [-.68,.68]:
    for y in [-.19,.19]: beam('Iron foot',(x,y,0),(x,y*.76,.45),.07,.07,'Metal',.015)
    beam('Seat bracket',(x,-.28,.405),(x,.30,.405),.06,.075,'Metal')
    beam('Back support',(x,.18,.39),(x,.29,.99),.055,.065,'Metal')
    beam('Arm support',(x,-.17,.44),(x,-.17,.67),.045,.045,'Metal')
    beam('Arm rest',(x,-.22,.68),(x,.25,.72),.06,.08,'Timber',.018)
for z in [.70,.87]: cube('Back slat',(0,.27+(z-.7)*.12,z),(1.7,.075,.13),'Timber',.022)
finish('SM_Bench',{'orientation':'Length X; sitting direction -Y; origin ground 0','seat_height_m':.4975})

# 5. Rounded clay planting trough with original leaf clusters.
cube('Clay planter',(0,0,.245),(1.15,.55,.49),'RoofClay',.07)
for y in [-.25,.25]: cube('Planter lip',(0,y,.515),(1.2,.10,.07),'RoofClay',.026)
for x in [-.55,.55]: cube('Planter end lip',(x,0,.515),(.10,.50,.07),'RoofClay',.026)
cube('Planting surface',(0,0,.50),(1.0,.40,.025),'Timber',.012)
for i in range(15):
    angle=i*2.399963
    origin=Vector((.36*math.sin(i*1.8),.10*math.cos(i*2.1),.52))
    tip=origin+Vector((.22*math.cos(angle),.20*math.sin(angle),.30+.18*((i%4)/3)))
    mid=(origin+tip)*.5+Vector((0,0,.08))
    side=Vector((-math.sin(angle),math.cos(angle),0))*(.06+.02*(i%3))
    leafverts=[tuple(origin),tuple(mid+side),tuple(tip),tuple(mid-side),tuple(mid+Vector((0,0,.04)))]
    mesh('Folded green leaf',leafverts,[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,3,2),(0,2,1)],'Leaf')
finish('SM_Planter',{'orientation':'Container length X; origin ground 0','container_dimensions_m':[1.2,.6,.55],
    'exception':'Planted leaves extend above the 0.55m container height.'})

# 6. Mooring bollard with base bolts.
cylinder('Bollard base',(0,0,.055),.22,.11,'Metal',16,.022)
cylinder('Bollard post',(0,0,.33),.105,.45,'Metal',16,.018)
cylinder('Bollard cap',(0,0,.575),.16,.15,'Metal',16,.03)
cylbeam('Cross mooring bar',(-.25,0,.47),(.25,0,.47),.055,'Metal')
for a in range(4):
    ang=a*math.pi/2+math.pi/4
    cylinder('Base bolt',(.155*math.cos(ang),.155*math.sin(ang),.12),.024,.025,'Metal',6,.004)
finish('SM_MooringBollard',{'orientation':'Origin ground 0; bar across X','height_m':.65})

# 7. Open clinker-like dinghy. The shell is hollow, with gunwales and three seats.
stations=[(-2,.035),(-1.5,.52),(-.9,.73),(0,.8),(.9,.73),(1.5,.52),(2,.035)]
for sign in [-1,1]:
    for i in range(len(stations)-1):
        x0,w0=stations[i]; x1,w1=stations[i+1]
        # Bilge is thinner at bow/stern, deepest amidships.
        b0=-.35+.25*(abs(x0)/2)**2; b1=-.35+.25*(abs(x1)/2)**2
        s0=.25+.10*(abs(x0)/2)**2; s1=.25+.10*(abs(x1)/2)**2
        for strip in range(3):
            a=strip/3; b=(strip+1)/3
            ya0=sign*w0*(.15+.85*a); ya1=sign*w1*(.15+.85*a)
            yb0=sign*w0*(.15+.85*b); yb1=sign*w1*(.15+.85*b)
            za0=b0+(s0-b0)*a; za1=b1+(s1-b1)*a
            zb0=b0+(s0-b0)*b; zb1=b1+(s1-b1)*b
            vv=[(x0,ya0,za0),(x1,ya1,za1),(x1,yb1,zb1),(x0,yb0,zb0),
                (x0,ya0-sign*.035,za0+.035),(x1,ya1-sign*.035,za1+.035),
                (x1,yb1-sign*.035,zb1+.035),(x0,yb0-sign*.035,zb0+.035)]
            mesh('Solid thin hull strake',vv,[(0,1,2),(0,2,3),(4,7,6),(4,6,5),
                 (0,4,5,1),(3,2,6,7),(0,3,7,4),(1,5,6,2)],'Timber')
        beam('Rounded gunwale',(x0,sign*w0,s0+.035),(x1,sign*w1,s1+.035),.075,.07,'Timber',.018)
for i in range(len(stations)-1):
    x0,w0=stations[i]; x1,w1=stations[i+1]
    b0=-.35+.25*(abs(x0)/2)**2; b1=-.35+.25*(abs(x1)/2)**2
    prism_between('Keel floor',x0,x1,-min(w0,w1)*.18,min(w0,w1)*.18,b0,b1,b0+.055,b1+.055,'Timber')
for x,width in [(-.95,1.36),(0,1.5),(.95,1.36)]:
    cube('Rowing seat',(x,0,.165),(.28,width,.075),'Timber',.02)
for x in [-1.4,-.65,.65,1.4]:
    w=.54 if abs(x)>1 else .75
    beam('Rib left',(x,-w,.17),(x,-.17,-.24),.045,.05,'Timber',.008)
    beam('Rib right',(x,w,.17),(x,.17,-.24),.045,.05,'Timber',.008)
finish('SM_Boat',{'orientation':'Bow/stern along X; origin Z=0 is waterline; open hull, no water plane',
    'hull_bottom_z_m':-.35,'nominal_dimensions_m':[4,1.6],
    'collision_recommendation':'Visual waterside prop; complex collision if boarding is needed.'})

# 8. Quiet metal canal-edge rail, exact nominal 3m segment.
for x in [-1.41,1.41]:
    cylinder('Railing post',(x,0,.49),.04,.98,'Metal',12,.01)
    cylinder('Post base',(x,0,.035),.09,.07,'Metal',12,.012)
    cylinder('Post cap',(x,0,.98),.055,.04,'Metal',12,.008)
for z in [.34,.93]: cylbeam('Railing bar',(-1.5,0,z),(1.5,0,z),.03,'Metal')
for i in range(7):
    x=-1.1+i*2.2/6
    cylbeam('Vertical rail',(x,0,.34),(x,0,.93),.018,'Metal',8)
finish('SM_RailingSegment',{'orientation':'Length X; origin ground 0; nominal spacing 3m',
    'placement_spacing_m':3,'post_centers_x_m':[-1.41,1.41]})

manifest={'theme':'RainyCanal','effort':'ultra','original_geometry':True,
    'started_at_utc':START.isoformat(),'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'units':'meters','fbx_axis_forward':'-Y','fbx_axis_up':'Z','ue_import_scale':1,
    'material_slots_contract':list(MATS),'uv0':'UVMap: unique packed islands; pack ADD margin .004, then 0.994 scale and 0.003 border offset; actual pixel separation measured in validation.json',
    'uv1':'Physical128: physical projection, 8m/tile, 128px/m at1024; intentional repeating/overlapping UVs outside unit square',
    'assets':[n for o,n in assets]}
with open(ROOT+'/manifest.json','w',encoding='utf8') as f: json.dump(manifest,f,indent=2)

# A source preview assembly uses copies. Export meshes themselves remain at origin.
sourcecoll=bpy.data.collections.new('Original export meshes at local origin'); scene.collection.children.link(sourcecoll)
for obj,notes in assets:
    for c in list(obj.users_collection): c.objects.unlink(obj)
    sourcecoll.objects.link(obj); obj.hide_render=True; obj.hide_set(True)
previewcoll=bpy.data.collections.new('Preview layout only'); scene.collection.children.link(previewcoll)
layout={'SM_StoneBridge':(0,4,0),'SM_TimberBridge':(0,-2.2,0),'SM_CanalLamp':(-6,-7,0),
        'SM_Bench':(-3.5,-7,0),'SM_Planter':(-.7,-7,0),'SM_MooringBollard':(1.1,-7,0),
        'SM_Boat':(4,-7,.36),'SM_RailingSegment':(0,-10,0)}
for obj,notes in assets:
    dup=bpy.data.objects.new('PREVIEW_'+obj.name,obj.data); previewcoll.objects.link(dup)
    dup.location=layout[obj.name]
    dup.hide_render=False; dup.hide_set(False)
world=scene.world or bpy.data.worlds.new('World'); scene.world=world
world.use_nodes=True; world.node_tree.nodes['Background'].inputs[0].default_value=(.30,.34,.38,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.5
bpy.ops.object.light_add(type='AREA',location=(1,-4,17)); light=bpy.context.object
light.name='Preview softbox'; light.data.energy=2200; light.data.shape='DISK'; light.data.size=12
bpy.ops.object.camera_add(location=(19,-27,21)); cam=bpy.context.object
cam.rotation_euler=(Vector((0,-2,0))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO'; cam.data.ortho_scale=27; scene.camera=cam
scene.render.engine='CYCLES'; scene.cycles.samples=24; scene.cycles.use_denoising=True
scene.render.resolution_x=1600; scene.render.resolution_y=1100; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
scene.render.filepath=ROOT+'/Preview/source_preview.png'
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/source.blend')
bpy.ops.render.render(write_still=True)
print('BUILD_COMPLETE',flush=True)
