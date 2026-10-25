"""Unique UVs, neutral Emission bake, portable PBR materials, GLB export.
Run on the prebake blend with Blender 4.5 --background --threads 4.
"""
import bpy, bmesh, math, json, time, hashlib, struct, zlib, os
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SIZE=4096
START=time.time()
(ROOT/'logs/finalize_process.json').write_text(json.dumps({'pid':os.getpid(),'started_at_utc':datetime.now(timezone.utc).isoformat(),'script':str(Path(__file__).resolve())}),encoding='utf8')
def utc():return datetime.now(timezone.utc).isoformat()
def log(s):print('VENDING '+s,flush=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def write_json(name,data):(ROOT/'validation'/name).write_text(json.dumps(data,indent=2),encoding='utf8')

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/VendingMachine_prebake.blend'))
scene=bpy.context.scene
scene.tool_settings.use_uv_select_sync=True
asset=[o for o in bpy.data.objects if o.type=='MESH' and o.get('asset_part')]
asset.sort(key=lambda o:o.name)
UVSTART=time.time()

def select(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]

def lathe_uv(o):
    me=o.data; uv=me.uv_layers.new(name='UV_Unique')
    n=o['lathe_segments'];profile=json.loads(o['lathe_profile']);ox,oy,oz=json.loads(o['lathe_origin'])
    arc=[0.]
    for k in range(1,len(profile)):
        arc.append(arc[-1]+math.hypot(profile[k][0]-profile[k-1][0],profile[k][1]-profile[k-1][1]))
    side=(len(profile)-1)*n
    for p in me.polygons:
        for li in p.loop_indices:
            vi=me.loops[li].vertex_index;k,j=divmod(vi,n)
            if p.index<side:
                first=p.index%n
                t=(n if first==n-1 and j==0 else j)/n
                uv.data[li].uv=((t-.5)*2*math.pi*profile[k][0],arc[k])
            else:
                v=me.vertices[vi].co;off=.46 if p.index==side else .66
                uv.data[li].uv=(v.x-ox+off,v.y-oy)
    me.uv_layers.active=uv

for idx,o in enumerate(asset):
    select([o])
    # Planar concave n-gons are triangulated before unwrap; lofts retain stable quads.
    bm=bmesh.new();bm.from_mesh(o.data)
    # Blender font conversion emits collinear cap triangles in glyph "4".
    # The diagnostic proves this removes them while preserving a closed mesh.
    bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges))
    if o.name in {'Price_1_4','Price_2_4','Price_3_4'}:
        # Freeze cap topology before UV mode switches can retessellate a quad.
        bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3],quad_method='BEAUTY',ngon_method='BEAUTY')
        bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges))
        bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3],quad_method='BEAUTY',ngon_method='BEAUTY')
    ngons=[f for f in bm.faces if len(f.verts)>4]
    # Lathe cap order is used by the analytical mapper, so preserve caps until after mapping.
    if ngons and not o.get('lathe_segments'):
        bmesh.ops.triangulate(bm,faces=ngons,quad_method='BEAUTY',ngon_method='BEAUTY')
        bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges))
    bm.to_mesh(o.data);bm.free();o.data.update()
    if o.get('lathe_segments'):
        lathe_uv(o)
    else:
        if not o.data.uv_layers:o.data.uv_layers.new(name='UV_Unique')
        o.data.uv_layers.active.name='UV_Unique'
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=0,area_weight=0,correct_aspect=True,scale_to_bounds=False)
        bpy.ops.object.mode_set(mode='OBJECT')
    if idx%40==0:log(f'UV unwrap {idx}/{len(asset)}')

def pack():
    select(asset);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale(scale_uv=False,shear=False)
    bpy.ops.uv.pack_islands('EXEC_DEFAULT',rotate=True,scale=True,merge_overlap=False,margin_method='FRACTION',margin=.002,shape_method='CONVEX')
    bpy.ops.object.mode_set(mode='OBJECT')

log('Packing area-normalized global UV islands')
pack()

def extract_triangles():
    tris=[]; stats=[];counter=0;island_counter=0
    for o in asset:
        me=o.data;me.calc_loop_triangles();uv=me.uv_layers.active.data
        # Island union across exact matching UV edges, independent of mesh membership.
        parents=list(range(len(me.polygons)))
        def find(a):
            while parents[a]!=a:parents[a]=parents[parents[a]];a=parents[a]
            return a
        def union(a,b):
            a=find(a);b=find(b)
            if a!=b:parents[b]=a
        edges={}
        for p in me.polygons:
            ls=list(p.loop_indices)
            for q,li in enumerate(ls):
                lj=ls[(q+1)%len(ls)];v1=me.loops[li].vertex_index;v2=me.loops[lj].vertex_index
                a=tuple(round(float(x),7) for x in uv[li].uv);b=tuple(round(float(x),7) for x in uv[lj].uv)
                key=(v1,v2,a,b) if v1<v2 else (v2,v1,b,a)
                if key in edges:union(p.index,edges[key])
                else:edges[key]=p.index
        ids={}
        for p in me.polygons:
            root=find(p.index)
            if root not in ids:island_counter+=1;ids[root]=island_counter
        area3=area2=0.;zeros3=zeros2=0;density_values=[]
        for t in me.loop_triangles:
            u=np.array([uv[li].uv[:] for li in t.loops],dtype=np.float64)
            verts=[o.matrix_world@me.vertices[vi].co for vi in t.vertices]
            a3=(verts[1]-verts[0]).cross(verts[2]-verts[0]).length*.5
            a2=abs(np.cross(u[1]-u[0],u[2]-u[0]))*.5
            if a3<1e-14:zeros3+=1
            if a2<1e-16:zeros2+=1
            area3+=a3;area2+=a2
            d=SIZE*math.sqrt(a2/a3) if a3>1e-14 else 0.
            density_values.append((d,a3))
            tris.append({'id':counter,'o':o,'poly':t.polygon_index,'uv':u,'a3':a3,'a2':a2,'island':ids[find(t.polygon_index)]})
            counter+=1
        bm=bmesh.new();bm.from_mesh(me)
        nonmanifold=sum(not e.is_manifold for e in bm.edges);boundary=sum(e.is_boundary for e in bm.edges)
        bm.free()
        stats.append({'object':o.name,'vertices':len(me.vertices),'polygons':len(me.polygons),'triangles':len(me.loop_triangles),'islands':len(ids),'surface_area_m2':area3,'uv_area':area2,'effective_density_px_per_m':SIZE*math.sqrt(area2/area3) if area3 else 0,'zero_area_3d_triangles':zeros3,'zero_area_uv_triangles':zeros2,'nonmanifold_edges':nonmanifold,'boundary_edges':boundary})
    return tris,stats,island_counter

def raster(tris,do_layout=True):
    owner=np.full((SIZE,SIZE),-1,np.int32);islands=np.zeros((SIZE,SIZE),np.int32)
    overlap=np.zeros((SIZE,SIZE),bool);bad=set();out_bounds=[];subpixel=0
    for t in tris:
        p=t['uv']*SIZE
        if np.any(t['uv']< -1e-6) or np.any(t['uv']>1+1e-6):out_bounds.append(t['id'])
        lo=np.maximum(np.floor(p.min(axis=0)-.5).astype(int),0);hi=np.minimum(np.ceil(p.max(axis=0)-.5).astype(int),SIZE-1)
        if np.any(hi<lo):subpixel+=1;continue
        x=np.arange(lo[0],hi[0]+1,dtype=np.float64)+.5;y=np.arange(lo[1],hi[1]+1,dtype=np.float64)+.5
        xx,yy=np.meshgrid(x,y)
        den=(p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
        if abs(den)<1e-14:subpixel+=1;continue
        a=((p[1,1]-p[2,1])*(xx-p[2,0])+(p[2,0]-p[1,0])*(yy-p[2,1]))/den
        b=((p[2,1]-p[0,1])*(xx-p[2,0])+(p[0,0]-p[2,0])*(yy-p[2,1]))/den
        c=1-a-b
        inside=(a>1e-7)&(b>1e-7)&(c>1e-7)
        if not inside.any():subpixel+=1;continue
        view=owner[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
        hit=inside&(view>=0)
        if hit.any():
            overlap[lo[1]:hi[1]+1,lo[0]:hi[0]+1]|=hit;bad.add(t['id']);bad.update(int(q) for q in np.unique(view[hit]))
        view[inside]=t['id'];islands[lo[1]:hi[1]+1,lo[0]:hi[0]+1][inside]=t['island']
    result={'resolution':SIZE,'strict_triangle_interior_overlap_pixels':int(overlap.sum()),'overlapping_triangle_ids':sorted(bad),'out_of_bounds_triangle_ids':out_bounds,'triangles_with_no_pixel_center_coverage':subpixel,'occupied_pixels':int((owner>=0).sum()),'occupancy_fraction':float((owner>=0).mean()),'method':'4096x4096 pixel-center triangle rasterization; strict barycentric interior epsilon 1e-7; shared edges excluded; subpixel overlap is not excluded analytically.'}
    if do_layout:
        rng=np.random.default_rng(913);palette=rng.integers(65,225,(int(islands.max())+1,3),dtype=np.uint8);palette[0]=[20,27,32]
        rgb=palette[islands];rgb[overlap]=[255,45,45]
        save_png(ROOT/'validation/UV_Layout_4096.png',np.flipud(rgb))
        # Measured raster moat between different UV islands, with one pixel uncertainty per boundary.
        field=islands.copy();minimum=None
        for step in range(1,13):
            grown=field.copy();collision=False
            for dy,dx in [(0,1),(1,0),(1,1),(1,-1),(-1,0),(0,-1),(-1,-1),(-1,1)]:
                shifted=np.roll(field,(dy,dx),(0,1))
                if dy>0:shifted[:dy]=0
                if dy<0:shifted[dy:]=0
                if dx>0:shifted[:,:dx]=0
                if dx<0:shifted[:,dx:]=0
                hits=(grown>0)&(shifted>0)&(grown!=shifted)
                if hits.any():collision=True
                fill=(grown==0)&(shifted>0);grown[fill]=shifted[fill]
            if collision:minimum=step;break
            field=grown
        result['requested_pack_margin_fraction']=.002
        result['requested_margin_px']=SIZE*.002
        result['island_dilation_first_collision_step']=minimum
        result['raster_padding_note']='Eight-neighbor simultaneous island dilation; first collision step bounds occupied-pixel clearance to about 2*step-2 .. 2*step pixels. This is a raster measurement, not an exact edge-distance guarantee; tiny islands may cover no pixel centers.'
    return result,owner

def save_png(path,rgb):
    arr=np.asarray(rgb,dtype=np.uint8)
    h,w=arr.shape[:2];channels=arr.shape[2]
    def chunk(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
    raw=b''.join(b'\0'+arr[y].tobytes() for y in range(h))
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2 if channels==3 else 6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,6))+chunk(b'IEND',b'')
    Path(path).write_bytes(png)

tris,stats,islands_count=extract_triangles()
log(f'Raster UV validation: {len(tris)} triangles, {islands_count} islands')
check,owner=raster(tris)
if check['strict_triangle_interior_overlap_pixels']:
    issues={}
    for tid in check['overlapping_triangle_ids']:
        t=tris[tid];issues.setdefault(t['o'].name,set()).add(t['poly'])
    write_json('uv_initial_overlap_issues.json',{k:sorted(v) for k,v in issues.items()})
    log('Repairing only UV faces reported by raster: '+str({k:len(v) for k,v in issues.items()}))
    # Each involved polygon gets its own physical planar chart. No geometry changes.
    for name,pids in issues.items():
        o=bpy.data.objects[name];me=o.data;uv=me.uv_layers.active.data
        for counter,pi in enumerate(pids):
            p=me.polygons[pi];normal=p.normal.normalized();axis=Vector((1,0,0))
            if abs(normal.dot(axis))>.9:axis=Vector((0,1,0))
            u=normal.cross(axis).normalized();v=normal.cross(u).normalized()
            base=me.vertices[me.loops[p.loop_start].vertex_index].co
            for li in p.loop_indices:
                q=me.vertices[me.loops[li].vertex_index].co-base
                uv[li].uv=(q.dot(u)+3+counter*4,q.dot(v)+3)
    pack();tris,stats,islands_count=extract_triangles();check,owner=raster(tris)
    check['repair_note']='Overlapping smart-projection faces only were detached into physically scaled planar charts and globally repacked.'
bad_names=sorted({tris[i]['o'].name for i in check['overlapping_triangle_ids']})
check['overlap_objects']=bad_names
check['island_count']=islands_count;check['object_count']=len(asset)
check['density_target_px_per_m']=800
check['density_policy']='All UV islands normalized by physical surface area, then fitted together into one 4096 atlas with 0.002 packing margin. 800 px/m is the nominal target; actual density is bounded by the achieved packing.'
area3=sum(t['a3'] for t in tris);area2=sum(t['a2'] for t in tris)
ds=np.array([SIZE*math.sqrt(t['a2']/t['a3']) if t['a3']>1e-14 else 0 for t in tris]);weights=np.array([t['a3'] for t in tris]);order=np.argsort(ds);cum=np.cumsum(weights[order])/weights.sum()
check['total_surface_area_m2']=area3;check['total_uv_area']=area2
check['effective_global_density_px_per_m']=SIZE*math.sqrt(area2/area3)
check['area_weighted_mean_density_px_per_m']=float(np.sum(ds*weights)/weights.sum())
check['area_weighted_density_p05_p50_p95']=[float(ds[order[min(len(ds)-1,int(np.searchsorted(cum,p)))]] ) for p in [.05,.5,.95]]
check['zero_area_uv_triangles']=sum(x['zero_area_uv_triangles'] for x in stats)
check['zero_area_3d_triangles']=sum(x['zero_area_3d_triangles'] for x in stats)
check['uv_elapsed_seconds']=time.time()-UVSTART
check['passed']=check['strict_triangle_interior_overlap_pixels']==0 and not check['out_of_bounds_triangle_ids'] and check['zero_area_uv_triangles']==0
write_json('uv_validation.json',check);write_json('mesh_validation.json',stats)
if not check['passed']:raise RuntimeError('UV validation failed; see validation/uv_validation.json')
log('UV passed. Density '+str(check['effective_global_density_px_per_m']))

# Neutral albedo bake avoids metallic shading or transparent glass darkening.
BAKESTART=time.time()
atlas=bpy.data.images.new('VendingMachine_BaseColor_4096',width=SIZE,height=SIZE,alpha=True,float_buffer=False)
atlas.generated_color=(.12,.15,.17,1);atlas.colorspace_settings.name='sRGB'
materials={m.name:m for o in asset for m in o.data.materials if m}
saved={}
for name,m in materials.items():
    nt=m.node_tree;p=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL')
    saved[name]={'base':list(p.inputs['Base Color'].default_value),'roughness':float(p.inputs['Roughness'].default_value),'metallic':float(p.inputs['Metallic'].default_value),'alpha':float(p.inputs['Alpha'].default_value),'emission_strength':float(p.inputs['Emission Strength'].default_value),'transmission':float(p.inputs['Transmission Weight'].default_value)}
    emission=nt.nodes.new('ShaderNodeEmission');emission.name='TEMPORARY_NEUTRAL_EMISSION_BAKE'
    if p.inputs['Base Color'].is_linked:nt.links.new(p.inputs['Base Color'].links[0].from_socket,emission.inputs['Color'])
    else:emission.inputs['Color'].default_value=p.inputs['Base Color'].default_value
    emission.inputs['Strength'].default_value=1
    nt.links.new(emission.outputs[0],out.inputs['Surface'])
    target=nt.nodes.new('ShaderNodeTexImage');target.name='BAKE_TARGET';target.image=atlas
    for n in nt.nodes:n.select=False
    target.select=True;nt.nodes.active=target
    # Preserve each original object's Generated coordinates when baking a joined duplicate.
    coord_nodes=[n for n in nt.nodes if n.type=='TEX_COORD']
    if coord_nodes:
        source_attr=nt.nodes.new('ShaderNodeAttribute');source_attr.attribute_name='bake_source_generated'
        source_attr.name='TEMP_PRESERVED_SOURCE_COORDINATES'
        for coord in coord_nodes:
            for link in list(coord.outputs['Generated'].links):
                dest=link.to_socket;nt.links.remove(link);nt.links.new(source_attr.outputs['Vector'],dest)

# Join temporary copies only. The delivery objects and their UV maps stay editable.
# Source-generated 3D coordinates are saved as vertex attributes before joining.
bake_collection=bpy.data.collections.new('TEMP_BAKE_ONLY');scene.collection.children.link(bake_collection)
temporary=[]
for o in asset:
    dup=o.copy();dup.data=o.data.copy();dup.name='TEMP_BAKE_'+o.name;bake_collection.objects.link(dup)
    positions=np.empty((len(dup.data.vertices),3),np.float32);dup.data.vertices.foreach_get('co',positions.ravel())
    mn=positions.min(axis=0);span=positions.max(axis=0)-mn;span[span<1e-12]=1
    values=(positions-mn)/span
    attribute=dup.data.attributes.new('bake_source_generated','FLOAT_VECTOR','POINT');attribute.data.foreach_set('vector',values.ravel())
    temporary.append(dup);o.hide_render=True
select(temporary);bpy.ops.object.join();merged=bpy.context.object;merged.name='TEMP_BAKE_JOINED_PRESERVED_UV'
select([merged]);scene.render.engine='CYCLES';scene.cycles.samples=1
scene.render.bake.margin=8;scene.render.bake.use_clear=True;scene.render.bake.target='IMAGE_TEXTURES'
scene.render.bake.margin_type='EXTEND'
log('Emission base-color atlas bake started')
bpy.ops.object.bake(type='EMIT')
bpy.data.objects.remove(merged,do_unlink=True);bpy.data.collections.remove(bake_collection)
for o in asset:o.hide_render=False
atlas_path=ROOT/'textures/packed/VendingMachine_BaseColor_4096.png'
atlas.filepath_raw=str(atlas_path);atlas.file_format='PNG';atlas.save()
if atlas.packed_file:atlas.unpack(method='REMOVE')
atlas.filepath=str(atlas_path);atlas.reload();atlas.pack()
assert sha(atlas.packed_file.data)==sha(atlas_path.read_bytes()),'Packed PNG bytes differ from fresh atlas file'
log('Atlas saved, reloaded, packed, byte identity verified')

# Rebuild export-safe materials with a single image and scalar PBR factors.
for name,m in materials.items():
    data=saved[name];nt=m.node_tree;nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial');out.location=(620,80)
    p=nt.nodes.new('ShaderNodeBsdfPrincipled');p.location=(320,80);p.name='PORTABLE_PBR'
    p.inputs['Base Color'].default_value=(1,1,1,1)
    p.inputs['Roughness'].default_value=data['roughness'];p.inputs['Metallic'].default_value=data['metallic']
    p.inputs['Alpha'].default_value=data['alpha'];p.inputs['Transmission Weight'].default_value=data['transmission']
    p.inputs['IOR'].default_value=1.45
    tex=nt.nodes.new('ShaderNodeTexImage');tex.name='BAKED_IMAGEGEN_AND_SURFACE_ALBEDO';tex.label='Unique 4096 albedo; generated source enamel / slate';tex.location=(-360,120);tex.image=atlas
    tex.interpolation='Linear';tex.extension='EXTEND'
    uvnode=nt.nodes.new('ShaderNodeUVMap');uvnode.uv_map='UV_Unique';uvnode.location=(-570,120);nt.links.new(uvnode.outputs[0],tex.inputs['Vector'])
    if name=='BODY_VARIANT_WHITE':
        tint=nt.nodes.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.name='BODY_TINT_WHITE_DEFAULT';tint.label='BODY ONLY: white preserves generated ivory';tint.location=(-70,120)
        tint.inputs[0].default_value=1;tint.inputs[2].default_value=(1,1,1,1)
        nt.links.new(tex.outputs['Color'],tint.inputs[1]);nt.links.new(tint.outputs[0],p.inputs['Base Color'])
        m['default_tint']=[1.,1.,1.,1.];m['variant_control']='Shader Editor > BODY_TINT_WHITE_DEFAULT > Color2. Pure white is the supplied ivory finish. Only light-body pieces use this material.'
    else:nt.links.new(tex.outputs['Color'],p.inputs['Base Color'])
    if data['emission_strength']>0:
        nt.links.new(tex.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=data['emission_strength']
    nt.links.new(p.outputs[0],out.inputs['Surface'])
    m.diffuse_color=(1,1,1,data['alpha']);m['baked_atlas']='textures/packed/VendingMachine_BaseColor_4096.png'
    if data['alpha']<1:m.surface_render_method='DITHERED';m.use_transparent_shadow=True

scene.cycles.samples=64;scene.render.resolution_x=1400;scene.render.resolution_y=1540
scene.render.resolution_percentage=100;scene.camera=bpy.data.objects['Camera_Hero']
scene['uv_validation']='validation/uv_validation.json'
scene['atlas_sha256']=sha(atlas_path.read_bytes())
scene['base_color_bake']='Emission, strength 1, 4096, 8px dilation; no lighting, metal, glass darkening baked in.'
scene['body_variant_default']='BODY_TINT_WHITE_DEFAULT multiply Color2=(1,1,1,1). Tint all and only light body.'
# Import placement: foot soles touch Z=0, independently of the studio backdrop.
header=bpy.data.objects.get('Front_Model_Tag')
if header:
    tag_nz=(1.602-1.515)/.135;tag_ny=-math.sqrt(1-tag_nz*tag_nz)
    header.location=(-.118,-.245+.135*tag_ny+.0007*tag_ny,1.602+.0007*tag_nz)
    header.rotation_euler[0]=math.atan2(-tag_ny,tag_nz)
min_z=min((o.matrix_world@Vector(c)).z for o in asset for c in o.bound_box)
for o in asset:o.location.z-=min_z
bpy.data.objects['Studio_Ground'].location.z=0
scene['asset_ground_alignment_m']=-min_z
select(asset)
for im in bpy.data.images:
    if im.source=='FILE' and not im.packed_file:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'VendingMachine.blend'))
log('Exporting self-contained GLB')
bpy.ops.export_scene.gltf(filepath=str(ROOT/'VendingMachine.glb'),export_format='GLB',use_selection=True,export_apply=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_image_format='AUTO',export_extras=True,export_cameras=False,export_lights=False,export_animations=False,export_yup=True)
write_json('bake_export.json',{'timestamp_utc':utc(),'total_finalize_seconds':time.time()-START,'bake_material_export_seconds':time.time()-BAKESTART,'atlas_sha256':sha(atlas_path.read_bytes()),'packed_atlas_sha256':sha(atlas.packed_file.data),'blender_packed_matches_external':True,'material_names':list(materials),'base_color_bake':'Cycles Emission strength 1; 4096 PNG; 8px margin; output reloaded and packed before GLB export','body_white_default':list(materials['BODY_VARIANT_WHITE'].node_tree.nodes['BODY_TINT_WHITE_DEFAULT'].inputs[2].default_value)})
log('FINALIZE_DONE')
