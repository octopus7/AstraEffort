"""Original RainyCanal architecture. Run only in private Blender background process."""
import bpy, math, json, os, sys, time, statistics, hashlib
from mathutils import Vector
from datetime import datetime, timezone

OUT = r'D:\github\AstraEffort\ForestDemo\Work\RainyCanal\ultra\Art\Architecture'
SCRATCH = r'D:\github\AstraEffort\ForestDemo\Saved\Workers\RainyCanal\ultra\Architecture'
START = datetime.now(timezone.utc).isoformat()
T0 = time.monotonic()
os.makedirs(OUT, exist_ok=True)
os.makedirs(SCRATCH, exist_ok=True)
SLOTS = ['Stone','PlasterCream','PlasterSage','PlasterRose','Timber','RoofSlate','RoofClay','Metal','WindowGlass']
COLORS = [(0.32,0.35,0.34,1),(0.72,0.66,0.49,1),(0.36,0.49,0.43,1),(0.60,0.38,0.32,1),
          (0.20,0.13,0.087,1),(0.18,0.25,0.29,1),(0.43,0.21,0.13,1),(0.12,0.17,0.18,1),(0.90,0.59,0.23,1)]
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for mat in list(bpy.data.materials):
    bpy.data.materials.remove(mat)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1.0
MATS = {}
for name, color in zip(SLOTS,COLORS):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = color
    bs.inputs['Roughness'].default_value = 0.60 if name != 'Metal' else 0.28
    if name == 'WindowGlass':
        bs.inputs['Emission Color'].default_value = color
        bs.inputs['Emission Strength'].default_value = 0.32
        bs.inputs['Roughness'].default_value = 0.26
    MATS[name] = mat

parts=[]
def finish(o,name,mat,bevel=0):
    o.name=name
    o.data.materials.append(MATS[mat])
    if bevel>0:
        mod=o.modifiers.new('Soft crafted edges','BEVEL')
        # Keep thin caps below the half-thickness collapse limit after world-coordinate float conversion.
        mod.width=min(bevel,min(o.dimensions)*.24); mod.segments=2
        bpy.context.view_layer.objects.active=o
        bpy.ops.object.modifier_apply(modifier=mod.name)
    for poly in o.data.polygons:
        poly.use_smooth=False
    parts.append(o)
    return o

def box(name,loc,dims,mat,bevel=.025,rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object
    o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if rot is not None: o.rotation_euler=rot
    return finish(o,name,mat,bevel)

def beam(name,a,b,width,depth,mat='Timber',bevel=.018):
    a,b=Vector(a),Vector(b)
    o=box(name,(a+b)/2,(width,depth,(b-a).length),mat,bevel)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o

def cyl(name,a,b,r,mat='Metal',verts=10):
    a,b=Vector(a),Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=(b-a).length,location=(a+b)/2)
    o=bpy.context.object
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return finish(o,name,mat,.008)

def prism(name,coords,faces,mat,bevel=.02):
    me=bpy.data.meshes.new(name)
    me.from_pydata(coords,[],faces);me.update()
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
    bpy.context.view_layer.objects.active=o
    return finish(o,name,mat,bevel)

def window_front(cx,y,cz,w,h,label='Window',cross=True,side=False):
    # Front surfaces point outward at -Y; side variant is created by rotate about local center.
    added=len(parts)
    box(label+'_back',(cx,y,cz),(w+.20,.13,h+.20),'Timber',.022)
    box(label+'_glass',(cx,y-.085,cz),(w,.045,h),'WindowGlass',.016)
    for x in [cx-w/2,cx+w/2]:box(label+'_jamb',(x,y-.13,cz),(.075,.09,h+.08),'Timber',.012)
    for z in [cz-h/2,cz+h/2]:box(label+'_rail',(cx,y-.13,z),(w+.08,.10,.075),'Timber',.012)
    box(label+'_mullion',(cx,y-.14,cz),(.050,.09,h),'Timber',.01)
    if cross:box(label+'_transom',(cx,y-.15,cz),(w,.09,.048),'Timber',.01)
    box(label+'_sill',(cx,y-.14,cz-h/2-.11),(w+.34,.36,.12),'Stone',.025)
    return parts[added:]

def sidewindow(side,x,cy,cz,w,h,label):
    created=window_front(0,0,cz,w,h,label)
    # Canonical front -Y transforms to +X or -X.
    ang=math.pi/2 if side>0 else -math.pi/2
    for o in created:
        p=o.location.copy()
        o.location=(x + math.cos(ang)*p.x-math.sin(ang)*p.y,
                    cy + math.sin(ang)*p.x+math.cos(ang)*p.y,p.z)
        o.rotation_euler.z+=ang

def door(cx,y,h=2.0,w=1.0):
    box('Door recess',(cx,y,.25+h/2),(w+.25,.15,h+.15),'Timber',.025)
    box('Door plank panel',(cx,y-.10,.25+h/2),(w,.07,h),'Timber',.022)
    for i in range(1,5):
        box('Door thin vertical seam',(cx-w/2+i*w/5,y-.145,.25+h/2),(.012,.014,h-.12),'Metal',.003)
    box('Door upper glazing',(cx,y-.16,.25+h*.75),(w*.55,.035,h*.24),'WindowGlass',.015)
    box('Door glazing bar',(cx,y-.19,.25+h*.75),(.042,.045,h*.25),'Timber',.008)
    cyl('Door knob',(cx+w*.32,y-.19,1.13),(cx+w*.32,y-.24,1.13),.045,'Metal',10)
    box('Stone door stoop',(cx,y-.39,.12),(w+ .65,.84,.24),'Stone',.035)
    box('Grounded lower step',(cx,y-.94,.06),(w+.80,.36,.12),'Stone',.025)

def wall_gable(w,d,wall_h,peak,plaster):
    box('Continuous grounded foundation',(0,0,.27),(w,d,.54),'Stone',.065)
    box('Plaster body',(0,0,(wall_h+.48)/2),(w-.10,d-.10,wall_h-.48),plaster,.055)
    # Closed triangular prism gable volume, avoiding accidental open faces.
    z=wall_h-.03; top=peak-.14
    vs=[(-w/2+.05,-d/2+.05,z),(w/2-.05,-d/2+.05,z),(0,-d/2+.05,top),
        (-w/2+.05,d/2-.05,z),(w/2-.05,d/2-.05,z),(0,d/2-.05,top)]
    prism('Full plaster gable',vs,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],plaster,.018)
    for x in [-w/2+.03,w/2-.03]:
        for y in [-d/2+.015,d/2-.015]:
            box('Timber corner post',(x,y,(wall_h+.48)/2),(.16,.16,wall_h-.48),'Timber',.024)
    for z in [.62,wall_h-.06]:
        for y in [-d/2-.005,d/2+.005]:box('Front timber band',(0,y,z),(w,.14,.15),'Timber',.022)
        for x in [-w/2-.005,w/2+.005]:box('Side timber band',(x,0,z),(.14,d,.15),'Timber',.022)

def roof(w,d,wall_h,peak,mat):
    half=w/2+.46; depth=d+ .86
    roof_base=wall_h-.06; rise=peak-roof_base
    for side in [-1,1]:
        angle=side*math.atan2(rise,half)
        slope=math.sqrt(half*half+rise*rise)
        # local X spans ridge -> eave; rotating around Y raises at center
        box('Broad pitched roof',(side*half/2,0,(peak+roof_base)/2),(slope,depth,.16),mat,.033,rot=(0,angle,0))
        for row in range(1,9):
            f=row/9
            x=side*half*f;z=peak-rise*f+.095
            box('Restrained roof course',(x,0,z),(.044,depth-.05,.035),mat,.009,rot=(0,angle,0))
        for y in [-depth/2,depth/2]:
            beam('Gable verge',(0,y,peak+.025),(side*half,y,roof_base+.025),.15,.16,'Timber',.024)
        # gutter trough uses a narrow dark horizontal channel, terminating in downpipe.
        gx=side*(half+.02)
        box('Roof rain gutter',(gx,0,roof_base-.07),(.20,depth+.02,.16),'Metal',.035)
        box('Gutter inner dark channel',(gx,0,roof_base+.015),(.12,depth-.05,.025),'Metal',.008)
        pipe_y=d/2-.34
        cyl('Gutter outlet',(gx,pipe_y,roof_base-.05),(gx,pipe_y,roof_base-.38),.075)
        cyl('Downpipe shoulder',(gx,pipe_y,roof_base-.38),(side*(w/2+.13),pipe_y,roof_base-.62),.070)
        cyl('Vertical rainwater pipe',(side*(w/2+.13),pipe_y,roof_base-.62),(side*(w/2+.13),pipe_y,.22),.067)
        cyl('Drain outlet elbow',(side*(w/2+.13),pipe_y,.22),(side*(w/2+.32),pipe_y,.16),.067)
        for z in [1.1,wall_h-1.0]:
            box('Downpipe wall bracket',(side*(w/2+.08),pipe_y,z),(.24,.08,.08),'Metal',.015)
    cyl('Roof rounded ridge cap',(0,-depth/2-.04,peak+.04),(0,depth/2+.04,peak+.04),.115,mat,12)
    # Small rectangular chimney with broad rain cap.
    chimney_x=w*.22;chimney_y=d*.20
    chimney_base=peak-rise*(abs(chimney_x)/half)-.16
    box('Stone chimney',(chimney_x,chimney_y,chimney_base+.64),(.58,.64,1.28),'Stone',.04)
    box('Chimney cap',(chimney_x,chimney_y,chimney_base+1.29),(.76,.80,.14),'Stone',.035)
    box('Chimney soot throat',(chimney_x,chimney_y,chimney_base+1.37),(.47,.51,.025),'Metal',.02)

def detail_timbers(w,d,wall_h,levels):
    for z in levels:
        for y in [-d/2-.025,d/2+.025]:box('Floor timber rail',(0,y,z),(w+.04,.14,.15),'Timber',.022)
        for x in [-w/2-.025,w/2+.025]:box('Floor side rail',(x,0,z),(.14,d+.04,.15),'Timber',.022)
    for side in [-1,1]:
        x=side*(w/2+.035)
        # Two shallow sidewall braces, kept clear of the window openings.
        beam('Wall knee brace',(x,-d/2+.35,wall_h-.24),(x,-d/2+1.15,wall_h-.98),.11,.11,'Timber',.015)
        beam('Wall knee brace',(x,d/2-.35,wall_h-.24),(x,d/2-1.15,wall_h-.98),.11,.11,'Timber',.015)

def make_building(name,w,d,wall_h,peak,color,roofmat,kind):
    global parts
    parts=[]
    wall_gable(w,d,wall_h,peak,color)
    roof(w,d,wall_h,peak,roofmat)
    detail_timbers(w,d,wall_h,[2.65] if kind!='B' else [2.62,4.89])
    if kind=='A':
        door(0,-d/2-.06,1.97,1.02)
        for x in [-2.16,2.16]:window_front(x,-d/2-.075,1.71,1.16,1.27)
        for x in [-1.52,1.52]:window_front(x,-d/2-.075,3.83,1.05,1.29)
        window_front(0,-d/2-.075,5.55,.72,.85,'Attic window',False)
        # Slender door rain hood, not an oversized stylized ornament.
        box('Door rain hood',(0,-d/2-.39,2.48),(1.70,.85,.10),'RoofSlate',.025,rot=(.10,0,0))
        for x in [-.65,.65]:beam('Canopy timber bracket',(x,-d/2-.11,2.02),(x,-d/2-.66,2.39),.09,.09)
        for side in [-1,1]:
            for y in [-1.2,1.35]:
                sidewindow(side,side*(w/2-.02),y,1.77,1.0,1.28,'Side window')
                sidewindow(side,side*(w/2-.02),y,3.83,.96,1.22,'Upper side window')
    elif kind=='B':
        door(-1.15,-d/2-.06,2.04,.98)
        window_front(1.45,-d/2-.075,1.73,1.22,1.30)
        for z in [3.72,5.82]:
            for x in [-1.35,1.35]:window_front(x,-d/2-.075,z,.95,1.23)
        window_front(0,-d/2-.075,7.10,.63,.73,'High attic window',False)
        for side in [-1,1]:
            for z in [1.75,3.74,5.82]:
                for y in [-1.35,1.35]:sidewindow(side,side*(w/2-.02),y,z,.88,1.20,'Tall house side window')
        box('Narrow door hood',(-1.15,-d/2-.32,2.60),(1.46,.72,.10),'RoofClay',.025,rot=(.12,0,0))
    else:
        door(.0,-d/2-.06,2.09,1.02)
        for x in [-2.38,2.38]:window_front(x,-d/2-.09,1.58,2.05,1.54,'Shop display window',False)
        for x in [-2.60,0,2.60]:window_front(x,-d/2-.075,3.50,1.05,1.04,'Shop upper window')
        # Solid canvas-like timber rain canopy with exact approved slot material.
        box('Shop continuous rain canopy',(0,-d/2-.55,2.66),(w-.35,1.18,.13),'RoofSlate',.04,rot=(.10,0,0))
        box('Shop canopy edge',(0,-d/2-1.10,2.60),(w-.30,.12,.21),'Timber',.025)
        for x in [-3.30,3.30]:
            beam('Shop canopy wall brace',(x,-d/2-.11,2.05),(x,-d/2-.95,2.58),.12,.12)
        for side in [-1,1]:
            sidewindow(side,side*(w/2-.02),-1.0,1.64,1.20,1.36,'Shop side lower')
            sidewindow(side,side*(w/2-.02),1.40,3.50,.95,1.04,'Shop side upper')
        window_front(0,-d/2-.075,5.16,.66,.72,'Shop attic',False)
    # Rear doors/windows ensure village blocks also read in overview shots.
    for x in [-w*.23,w*.23]:
        created=window_front(x,-d/2-.075,1.72,.92,1.18,'Rear window')
        for o in created:
            o.location.x=-o.location.x;o.location.y=-o.location.y;o.rotation_euler.z+=math.pi
    for p_ob in parts:
        p_ob.data.calc_loop_triangles()
        bad=sum(1 for t in p_ob.data.loop_triangles if (p_ob.data.vertices[t.vertices[1]].co-p_ob.data.vertices[t.vertices[0]].co).cross(p_ob.data.vertices[t.vertices[2]].co-p_ob.data.vertices[t.vertices[0]].co).length < 1e-12)
        if bad: print('SOURCE_DEGENERATE',p_ob.name,bad,tuple(p_ob.dimensions),flush=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]
    bpy.ops.object.join()
    ob=bpy.context.object;ob.name=name
    bpy.context.scene.cursor.location=(0,0,0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    oldslots=[m.name for m in ob.data.materials]
    indices=[SLOTS.index(oldslots[p.material_index]) for p in ob.data.polygons]
    ob.data.materials.clear()
    for n in SLOTS:ob.data.materials.append(MATS[n])
    for p,i in zip(ob.data.polygons,indices):p.material_index=i
    tri=ob.modifiers.new('Explicit export triangulation','TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier=tri.name)
    for uv in list(ob.data.uv_layers):ob.data.uv_layers.remove(uv)
    uv0=ob.data.uv_layers.new(name='UV0_Unique')
    uv1=ob.data.uv_layers.new(name='UV1_Density128')
    n=math.ceil(math.sqrt(len(ob.data.polygons)))
    pad=2.25/1024; room=1/n-2*pad
    assert room>0, 'Triangle atlas needs lower triangle count'
    for idx,p in enumerate(ob.data.polygons):
        vv=[ob.data.vertices[v].co for v in p.vertices]
        e1=vv[1]-vv[0]; e2=vv[2]-vv[0]
        length=e1.length
        assert length>1e-9, (name,idx,p.material_index,[tuple(v) for v in vv])
        tx=e1/length; nx=e1.cross(e2).normalized();ty=nx.cross(tx)
        flat=[(0.,0.),(length,0.),(e2.dot(tx),e2.dot(ty))]
        lo=[min(q[j] for q in flat) for j in [0,1]]
        span=max(max(q[j] for q in flat)-lo[j] for j in [0,1])
        for li,uv in zip(p.loop_indices,flat):
            uv0.data[li].uv=((idx%n)/n+pad+(uv[0]-lo[0])*room/span,
                             (idx//n)/n+pad+(uv[1]-lo[1])*room/span)
        # Planar world mapping uses an orthonormal face basis: isometric at 128px/m.
        normal=p.normal.normalized()
        helper=Vector((0,0,1)) if abs(normal.z)<.9 else Vector((0,1,0))
        tangent=helper.cross(normal).normalized();bitangent=normal.cross(tangent).normalized()
        for li,v in zip(p.loop_indices,vv):uv1.data[li].uv=(v.dot(tangent)*.125,v.dot(bitangent)*.125)
    ob.data.uv_layers.active_index=0
    return ob,n

specs=[('SM_CanalHouseA',7.,6.,4.76,6.95,'PlasterCream','RoofSlate','A'),
       ('SM_CanalHouseB',6.,6.,6.65,8.43,'PlasterSage','RoofClay','B'),
       ('SM_CanalShop',8.,6.,4.24,6.43,'PlasterRose','RoofSlate','Shop')]
assets=[];obs=[]
for sp in specs:
    ob,grid=make_building(*sp)
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    filepath=os.path.join(OUT,ob.name+'.fbx')
    bpy.ops.export_scene.fbx(filepath=filepath,use_selection=True,object_types={'MESH'},
        apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',global_scale=1.0,
        axis_forward='-Y',axis_up='Z',add_leaf_bones=False,bake_anim=False,
        use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=True)
    bounds=[[min(v.co[k] for v in ob.data.vertices),max(v.co[k] for v in ob.data.vertices)] for k in range(3)]
    assets.append({'name':ob.name,'file':filepath,'body_footprint_m':[sp[1],sp[2]],'bounds_m':bounds,
        'dimensions_m':[b[1]-b[0] for b in bounds], 'triangles':len(ob.data.polygons),
        'vertices':len(ob.data.vertices),'atlas_grid':grid,'main_plaster':sp[5],'roof':sp[6],
        'front_local_direction':[0,-1,0],'origin':'body base center, z=0','scale':[1,1,1],
        'maximum_stoop_top_m':.24,'lowest_geometry_z_m':bounds[2][0]})
    obs.append(ob)

# Source preview is Blender authoring evidence only, not UE scene evidence.
for ob,x in zip(obs,[-10,0,10]):ob.location.x=x
floor=box('Preview ground',(0,0,-.12),(40,25,.22),'Stone',.06)
floor.hide_set(False)
bpy.ops.object.camera_add(location=(23,-37,24))
camera=bpy.context.object;camera.name='Source preview camera'
direction=Vector((0,0,3.3))-camera.location
camera.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=37
bpy.context.scene.camera=camera
def light(name,location,power,size,color):
    bpy.ops.object.light_add(type='AREA',location=location)
    o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=color
    o.rotation_euler=(Vector((0,0,3))-o.location).to_track_quat('-Z','Y').to_euler()
light('Soft overcast key',(0,-13,23),3800,18,(.80,.87,1.0))
light('Warm fill',(-15,-8,10),1400,12,(1.0,.83,.65))
light('Rim',(4,13,19),3000,15,(.78,.86,1.0))
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=32
scene.render.resolution_x=1800;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world.color=(.20,.23,.28)
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG'
scene.render.filepath=os.path.join(OUT,'source_preview.png')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'source.blend'))
bpy.ops.render.render(write_still=True)

def qa_mesh(ob,asset):
    me=ob.data;me.calc_loop_triangles()
    n=asset['atlas_grid'];pad=2.25/1024
    occupied=set();bad_cells=0;degenerate_geo=0;degenerate_uv=0;densities=[];min_border=1.
    for p in me.polygons:
        if len(p.vertices)!=3:raise AssertionError('FBX face is not triangulated')
        xyz=[me.vertices[i].co for i in p.vertices]
        geoarea=(xyz[1]-xyz[0]).cross(xyz[2]-xyz[0]).length*.5
        uvs=[me.uv_layers[0].data[li].uv.copy() for li in p.loop_indices]
        cu=sum(u.x for u in uvs)/3;cv=sum(u.y for u in uvs)/3
        cell=(math.floor(cu*n),math.floor(cv*n))
        if cell in occupied:bad_cells+=1
        occupied.add(cell)
        for u in uvs:
            distances=[u.x-cell[0]/n,(cell[0]+1)/n-u.x,u.y-cell[1]/n,(cell[1]+1)/n-u.y]
            min_border=min(min_border,*distances)
            if min(distances)<-1e-6:bad_cells+=1
        uvarea=abs((uvs[1].x-uvs[0].x)*(uvs[2].y-uvs[0].y)-(uvs[1].y-uvs[0].y)*(uvs[2].x-uvs[0].x))*.5
        if geoarea<1e-12:degenerate_geo+=1
        if uvarea<1e-14:degenerate_uv+=1
        uvv=[me.uv_layers[1].data[li].uv.copy() for li in p.loop_indices]
        uv1area=abs((uvv[1].x-uvv[0].x)*(uvv[2].y-uvv[0].y)-(uvv[1].y-uvv[0].y)*(uvv[2].x-uvv[0].x))*.5
        if geoarea>1e-12:densities.append(1024*math.sqrt(uv1area/geoarea))
    bounds=[[min(v.co[k] for v in me.vertices),max(v.co[k] for v in me.vertices)] for k in range(3)]
    delta=max(abs(a-b) for old,new in zip(asset['bounds_m'],bounds) for a,b in zip(old,new))
    slotnames=[m.name for m in me.materials]
    q={'imported_triangles':len(me.polygons),'imported_vertices':len(me.vertices),
       'uv_channels':[u.name for u in me.uv_layers],'material_slots':slotnames,
       'bounds_m':bounds,'max_bounds_delta_m':delta,'geometry_degenerate_triangles':degenerate_geo,
       'uv0_degenerate_triangles':degenerate_uv,'uv0_duplicate_or_outside_cells':bad_cells,
       'uv0_min_cell_border_px_1024':min_border*1024,
       'uv0_min_island_gap_lower_bound_px_1024':min_border*2048,
       'uv1_density_px_per_m_min':min(densities),'uv1_density_px_per_m_max':max(densities),
       'uv1_density_px_per_m_mean':statistics.mean(densities),
       'uv1_overlap':'Intentional overlapping repeated planar surface mapping; not a lightmap.',
       'fbx_reimported_at_utc':datetime.now(timezone.utc).isoformat()}
    q['passed']=(len(me.polygons)<30000 and degenerate_geo==0 and degenerate_uv==0 and bad_cells==0
        and min_border*1024>=2.20 and delta<.0001 and slotnames==SLOTS and len(me.uv_layers)==2
        and min(densities)>127.8 and max(densities)<128.2)
    return q

# Real exporter readback in a clean scene, no original objects/materials retained.
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
for a in assets:
    bpy.ops.import_scene.fbx(filepath=a['file'],use_custom_normals=True)
    imported=[o for o in bpy.context.selected_objects if o.type=='MESH']
    assert len(imported)==1, 'Export must contain exactly one joined mesh'
    a['fbx_readback']=qa_mesh(imported[0],a)
    a['sha256']=hashlib.sha256(open(a['file'],'rb').read()).hexdigest()
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
manifest={'theme':'RainyCanal','effort':'ultra','authoring_scope':'Architecture',
    'started_at_utc':START,'finished_at_utc':datetime.now(timezone.utc).isoformat(),
    'elapsed_build_render_readback_seconds':time.monotonic()-T0,
    'assets':assets,'material_slots_order':SLOTS,
    'fbx_export':{'axis_forward':'-Y','axis_up':'Z','apply_unit_scale':True,'units':'metres','leaf_bones':False},
    'uv0':{'purpose':'unique per-triangle atlas','padding_to_cell_border_px_at_1024':2.25,'minimum_island_gap_px_at_1024':4.5,'overlap':'none; proven distinct grid cells'},
    'uv1':{'purpose':'surface material texture coordinates','target_texel_density_px_per_m':128,'texture_size_px':1024,'mapping':'orthonormal planar per face, repeating beyond 0..1','exceptions':'Intentional UV1 overlaps/repeats; UV0 density varies with per-triangle fit and is not used for surface density.'},
    'source_preview':'source_preview.png; Blender source preview only, not UE capture',
    'materials':'Preview colors only; parent replaces exact named slots with owned UE materials/textures.',
    'all_fbx_readback_checks_passed':all(a['fbx_readback']['passed'] for a in assets)}
with open(os.path.join(OUT,'manifest.json'),'w',encoding='utf-8') as f:json.dump(manifest,f,indent=2)
print(json.dumps({'ARCHITECTURE_BUILD_COMPLETE':manifest['all_fbx_readback_checks_passed'],'manifest':os.path.join(OUT,'manifest.json'),'assets':[{ 'name':a['name'],'triangles':a['triangles'],'qa':a['fbx_readback']} for a in assets]},indent=2))
if not manifest['all_fbx_readback_checks_passed']:raise RuntimeError('FBX readback checks failed; inspect manifest')
