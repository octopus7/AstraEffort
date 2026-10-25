import bpy, bmesh, math, json, os, ast, time
from mathutils import Vector
from datetime import datetime, timezone
ROOT=os.path.dirname(os.path.abspath(__file__))
run=time.time();started=datetime.now(timezone.utc).isoformat()
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'mine_elevator.blend'))
asset=bpy.data.collections['ASSET'];M={'rope':bpy.data.materials['Woven steel rope']}
if not bpy.context.scene.get('crown_clearance_corrected',False):
    prefixes=('05 ','03 Main axle carrier beam','03 Carrier orange pin','03 Pedestal lower block','03 Axle bearing block','03 Bearing hold-down')
    for o in asset.objects:
        if any(o.name.startswith(p) for p in prefixes):o.location.z-=.12
    # Reuse only the generic geometry helpers in this asset's own source.
    with open(os.path.join(ROOT,'build.py'),encoding='utf-8-sig') as f:tree=ast.parse(f.read())
    selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('wind','activate','bevel','mesh_obj','tube')]
    exec(compile(ast.Module(body=selected,type_ignores=[]),'own_geometry_helpers','exec'),globals())
    for o in list(asset.objects):
        if o.name.startswith('11 Continuous load rope') or o.name.startswith('11 Winch cable end clamp'):
            bpy.data.objects.remove(o,do_unlink=True)
    R=1.025;r=.184;cx,cz=0,6.56;dx,dz=2.45,2.49
    rel=Vector((0,2.74))-Vector((cx,cz));theta_a=math.atan2(rel.y,rel.x)-math.acos(R/rel.length)
    while theta_a<0:theta_a+=2*math.pi
    delta=Vector((dx-cx,dz-cz));theta_d=math.atan2(delta.y,delta.x)+math.acos((R-r)/delta.length)
    endings=[]
    for i,y in enumerate((-.49,-.01)):
        p=[(0,y,2.74)]
        for k in range(65):
            a=theta_a+(theta_d-theta_a)*k/64;p.append((cx+R*math.cos(a),y,cz+R*math.sin(a)))
        p.append((dx+r*math.cos(theta_d),y,dz+r*math.sin(theta_d)))
        for k in range(1,61):
            a=theta_d-k*(1.5*math.pi)/60;p.append((dx+r*math.cos(a),y,dz+r*math.sin(a)))
        o=tube('11 Continuous load rope %d | cage to sheave to winch'%(i+1),p,.018,'rope',10);activate(o)
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.025,area_weight=0.0,correct_aspect=True,scale_to_bounds=True)
        bpy.ops.object.mode_set(mode='OBJECT');mod=o.modifiers.new('Baked export triangulation','TRIANGULATE');mod.quad_method='BEAUTY';mod.ngon_method='BEAUTY';bpy.ops.object.modifier_apply(modifier=mod.name)
        endings.append(p[-1]);o['part_category']='11';o['uv_layout']='Per-component smart-projected islands; seam-aware, no shared image atlas.'
    # Move the two original style anchor blocks onto the new winding tangency endpoints.
    selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('move_collection','finish','box')]
    M['steel']=bpy.data.materials['Warm galvanized steel'];exec(compile(ast.Module(body=selected,type_ignores=[]),'own_box_helpers','exec'),globals())
    for end in endings:
        o=box('11 Winch cable end clamp',end,(.07,.06,.07),'steel',.014);activate(o)
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
        mod=o.modifiers.new('Baked export triangulation','TRIANGULATE');mod.quad_method='BEAUTY';mod.ngon_method='BEAUTY';bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.context.scene['crown_clearance_corrected']=True
    bpy.context.scene['crown_clearance_metres']=.097
    bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT')
    for o in asset.objects:o.select_set(True)
    bpy.context.view_layer.objects.active=next(iter(asset.objects))
    bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'mine_elevator.glb'),export_format='GLB',use_selection=True,export_apply=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_cameras=False,export_lights=False)
    bpy.ops.export_scene.fbx(filepath=os.path.join(ROOT,'mine_elevator.fbx'),use_selection=True,object_types={'MESH'},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',path_mode='AUTO')
    bpy.ops.object.select_all(action='DESELECT');bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'mine_elevator.blend'))
    with open(os.path.join(ROOT,'clearance_fix_record.json'),'w',encoding='utf-8') as f:json.dump({'started_at_utc':started,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.time()-run,'correction':'Lowered crown sheave and axle carrier assembly 0.12 m, recalculated both tangent rope paths and their winch end clamps. Updated reproducible build source.','nominal_crown_to_liner_clearance_m':.097},f,indent=2)
with open(os.path.join(ROOT,'finalize_captures.py'),encoding='utf-8') as f:exec(compile(f.read(),'finalize_captures.py','exec'))
