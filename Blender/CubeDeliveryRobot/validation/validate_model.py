"""Read-only model/export audit. Writes only validation reports and a reimport render.

Run with Blender 4.5: blender -b --factory-startup --threads 4 --python-exit-code 1
 --python validation/validate_model.py
"""
import bpy, bmesh, json, math, time, hashlib, struct, sys, tempfile, shutil
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
if '--root' in sys.argv:ROOT=Path(sys.argv[sys.argv.index('--root')+1])
V=ROOT/'validation'
t0=time.time()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,data):(V/name).write_text(json.dumps(data,indent=2),encoding='utf8')
def bounds(objs):
    vs=[o.matrix_world@Vector(v) for o in objs for v in o.bound_box]
    lo=[min(v[k] for v in vs) for k in range(3)];hi=[max(v[k] for v in vs) for k in range(3)]
    return {'min':lo,'max':hi,'dimensions':[hi[k]-lo[k] for k in range(3)]}
def geometry_report(objs,topology=False):
    rows=[]
    for o in objs:
        mesh=o.data;mesh.calc_loop_triangles()
        coords=np.array([tuple(v.co) for v in mesh.vertices],dtype=np.float64)
        tri=np.array([tuple(t.vertices) for t in mesh.loop_triangles],dtype=np.int32)
        cross=np.cross(coords[tri[:,1]]-coords[tri[:,0]],coords[tri[:,2]]-coords[tri[:,0]])
        areas=np.linalg.norm(cross,axis=1)*.5
        uv=mesh.uv_layers.active
        uvcoords=np.array([tuple(x.uv) for x in uv.data],dtype=np.float64) if uv else np.empty((0,2))
        if uv:
            loops=np.array([tuple(t.loops) for t in mesh.loop_triangles],dtype=np.int32)
            a=uvcoords[loops[:,1]]-uvcoords[loops[:,0]];b=uvcoords[loops[:,2]]-uvcoords[loops[:,0]]
            uvareas=np.abs(a[:,0]*b[:,1]-a[:,1]*b[:,0])*.5
        else:uvareas=np.zeros(len(tri))
        row={'name':o.name,'vertices':len(coords),'triangles':len(tri),'finite_positions':bool(np.isfinite(coords).all()),'geometric_zero_area_triangles':int((areas<1e-15).sum()),'uv_channels':len(mesh.uv_layers),'uv_zero_area_triangles':int((uvareas<1e-15).sum()),'uv_finite':bool(np.isfinite(uvcoords).all()),'uv_out_of_bounds_values':int(((uvcoords<-1e-6)|(uvcoords>1+1e-6)).sum()),'surface_area_m2':float(areas.sum()),'uv_area':float(uvareas.sum()),'material_slots':[m.name for m in mesh.materials],'origin':list(o.location),'dimensions':list(o.dimensions)}
        if topology:
            bm=bmesh.new();bm.from_mesh(mesh)
            row['boundary_edges']=sum(e.is_boundary for e in bm.edges)
            row['nonmanifold_edges']=sum(not e.is_manifold for e in bm.edges)
            row['wire_vertices']=sum(not v.link_faces for v in bm.verts)
            row['signed_volume_m3']=bm.calc_volume(signed=True);bm.free()
        rows.append(row)
    return rows

initial_hashes={n:sha(ROOT/n) for n in ['CubeDeliveryRobot.blend','CubeDeliveryRobot.glb','CubeDeliveryRobot.fbx','textures/CubeDeliveryRobot_BaseColor_4096.png']}
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'CubeDeliveryRobot.blend'))
scene=bpy.context.scene
native=[o for o in bpy.data.collections['ASSET_CubeDeliveryRobot'].objects if o.type=='MESH']
native_rows=geometry_report(native,True)
native_bounds=bounds(native)
dump('mesh_validation.json',native_rows)
errors=[]
for row in native_rows:
    for key in ['geometric_zero_area_triangles','uv_zero_area_triangles','uv_out_of_bounds_values','boundary_edges','nonmanifold_edges','wire_vertices']:
        if row[key]:errors.append(row['name']+': '+key+'='+str(row[key]))
    if not row['finite_positions'] or not row['uv_finite'] or row['uv_channels']!=1:errors.append(row['name']+': invalid data')
if native_bounds['min'][2]<-1e-5 or native_bounds['min'][2]>.0001:errors.append('Ground contact outside 0.1mm tolerance')
atlas=bpy.data.images.get('CubeDeliveryRobot_BaseColor_4096')
packed_hash=hashlib.sha256(bytes(atlas.packed_file.data)).hexdigest() if atlas and atlas.packed_file else None
if packed_hash!=initial_hashes['textures/CubeDeliveryRobot_BaseColor_4096.png']:errors.append('Packed atlas differs from external PNG')
missing=[im.filepath for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()]
if missing:errors.append('Missing image resources')

# Strict triangle interior raster at the actual atlas resolution. Does not certify subpixel overlaps.
N=4096
counts=np.zeros((N,N),dtype=np.uint16)
owner=np.zeros((N,N),dtype=np.uint8)
subpixel=0
ratios=[];areaweights=[]
for oi,o in enumerate(native):
    mesh=o.data;uv=mesh.uv_layers.active.data
    for tr in mesh.loop_triangles:
        p=np.array([tuple(uv[i].uv) for i in tr.loops],dtype=np.float64)*N
        a,b,c=p
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        world=[o.matrix_world@mesh.vertices[i].co for i in tr.vertices]
        ar=(world[1]-world[0]).cross(world[2]-world[0]).length*.5
        if ar>1e-15:ratios.append(math.sqrt(abs(den)*.5/ar));areaweights.append(ar)
        if abs(den)<1e-12:continue
        x0=max(0,int(math.ceil(p[:,0].min()-.5)));x1=min(N-1,int(math.floor(p[:,0].max()-.5)))
        y0=max(0,int(math.ceil(p[:,1].min()-.5)));y1=min(N-1,int(math.floor(p[:,1].max()-.5)))
        if x1<x0 or y1<y0:subpixel+=1;continue
        xx=np.arange(x0,x1+1,dtype=np.float64)[None,:]+.5;yy=np.arange(y0,y1+1,dtype=np.float64)[:,None]+.5
        q=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
        r=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
        mask=(q>1e-7)&(r>1e-7)&(q+r<1-1e-7)
        if not mask.any():subpixel+=1
        counts[y0:y1+1,x0:x1+1]+=mask
        own=owner[y0:y1+1,x0:x1+1];own[mask]=oi+1
ratios=np.array(ratios);areaweights=np.array(areaweights);order=np.argsort(ratios);cdf=np.cumsum(areaweights[order])/areaweights.sum()
percentiles={str(p):float(ratios[order][min(len(order)-1,np.searchsorted(cdf,p/100))]) for p in [5,50,95]}
uv_report={'resolution':N,'strict_interior_overlap_pixels':int((counts>1).sum()),'occupied_pixels':int((counts>0).sum()),'occupancy_percent':float((counts>0).mean()*100),'triangles_covering_no_pixel_center':subpixel,'surface_area_m2':float(areaweights.sum()),'texel_density_px_m_area_weighted_percentiles':percentiles,'area_weighted_mean_px_m':float(np.average(ratios,weights=areaweights)),'requested_packer_margin_fraction':.0025,'requested_margin_pixels':10.24,'bake_dilation_pixels':8,'limits':'Pixel-center strict interior test; no mathematical exclusion of subpixel overlap; no exact continuous minimum gap or mip-chain bleed certificate.'}
dump('uv_validation.json',uv_report)
if uv_report['strict_interior_overlap_pixels']:errors.append('Unique UV raster overlap')
# Opaque diagnostic PNG colored by functional assembly.
preview=owner[::2,::2];palette=np.zeros((len(native)+1,4),dtype=np.float32);palette[0]=(.045,.055,.065,1)
for i in range(1,len(palette)):
    palette[i]=(.22+.65*((i*.373)%1),.22+.65*((i*.619)%1),.22+.65*((i*.827)%1),1)
im=bpy.data.images.new('UV_layout_diagnostic',width=2048,height=2048,alpha=False);im.pixels.foreach_set(palette[preview].ravel())
im.filepath_raw=str(V/'UV_Layout_2048.png');im.file_format='PNG';im.save();bpy.data.images.remove(im)
del owner,counts,preview

# Parse actual binary glTF, including embedded texture bytes and required attributes.
raw=(ROOT/'CubeDeliveryRobot.glb').read_bytes();magic,version,total=struct.unpack_from('<III',raw,0)
jl,jtype=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+jl]);off=20+jl
bl,btype=struct.unpack_from('<II',raw,off);binary=raw[off+8:off+8+bl]
prims=[p for m in doc['meshes'] for p in m['primitives']]
embedded=[]
for iminfo in doc.get('images',[]):
    if 'bufferView' in iminfo:
        bv=doc['bufferViews'][iminfo['bufferView']];data=binary[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]
        embedded.append(hashlib.sha256(data).hexdigest())
glb_report={'header_valid':magic==0x46546c67 and version==2 and total==len(raw),'mesh_count':len(doc['meshes']),'primitive_count':len(prims),'material_count':len(doc.get('materials',[])),'images_embedded':len(embedded),'image_hashes':embedded,'external_uris':[x['uri'] for x in doc.get('images',[])+doc.get('buffers',[]) if 'uri' in x],'all_primitives_have_uv':all('TEXCOORD_0' in p['attributes'] for p in prims),'all_primitives_have_normals':all('NORMAL' in p['attributes'] for p in prims),'camera_count':len(doc.get('cameras',[])),'light_extension_present':'KHR_lights_punctual' in doc.get('extensions',{}),'node_names':[n.get('name') for n in doc['nodes']]}
dump('glb_validation.json',glb_report)
if not glb_report['header_valid'] or not glb_report['all_primitives_have_uv']:errors.append('Invalid GLB or missing UV')
if glb_report['external_uris'] or glb_report['camera_count'] or glb_report['light_extension_present']:errors.append('GLB includes unwanted dependency or studio')
if embedded!=[initial_hashes['textures/CubeDeliveryRobot_BaseColor_4096.png']]:errors.append('GLB atlas bytes do not match')

# Freshly reimport the exported geometry into the already-reopened studio; never save over source.
for o in native:bpy.data.objects.remove(o,do_unlink=True)
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'CubeDeliveryRobot.glb'))
imported=[o for o in set(bpy.data.objects)-before if o.type=='MESH']
imported_bounds=bounds(imported);imported_rows=geometry_report(imported)
delta=max(abs(imported_bounds[k][i]-native_bounds[k][i]) for k in ['min','max'] for i in range(3))
if len(imported)!=len(native_rows) or delta>1e-5:errors.append('GLB roundtrip count/bounds mismatch')
for row in imported_rows:
    if row['geometric_zero_area_triangles'] or row['uv_zero_area_triangles'] or row['uv_out_of_bounds_values']:errors.append('GLB import invalid triangles/UV: '+row['name'])
scene.render.resolution_x=1400;scene.render.resolution_y=1400;scene.cycles.samples=40
scene.render.filepath=str(ROOT/'renders/glb_reimport_hero.png');bpy.ops.render.render(write_still=True)
a=bpy.data.images.load(str(ROOT/'renders/hero.png'));b=bpy.data.images.load(str(ROOT/'renders/glb_reimport_hero.png'))
ar=np.empty(len(a.pixels),dtype=np.float32);br=np.empty(len(b.pixels),dtype=np.float32);a.pixels.foreach_get(ar);b.pixels.foreach_get(br)
mae=float(np.abs(ar.reshape(-1,4)[:,:3]-br.reshape(-1,4)[:,:3]).mean())
if mae>.015:errors.append('GLB render differs materially: '+str(mae))
dump('glb_reimport_validation.json',{'mesh_count':len(imported),'bounds':imported_bounds,'max_bounds_difference_m':delta,'native_vs_glb_render_rgb_mean_absolute_error':mae,'meshes':imported_rows})

bpy.ops.wm.read_factory_settings(use_empty=True)
from io_scene_fbx import parse_fbx
fbx_root,fbx_version=parse_fbx.parse(str(ROOT/'CubeDeliveryRobot.fbx'))
fbx_images=[]
def walk_fbx(elem):
    if elem.id==b'Content':
        for val in elem.props:
            if isinstance(val,bytes) and val.startswith(b'\x89PNG'):
                fbx_images.append(hashlib.sha256(val).hexdigest())
    for child in elem.elems:walk_fbx(child)
walk_fbx(fbx_root)
if fbx_images!=[initial_hashes['textures/CubeDeliveryRobot_BaseColor_4096.png']]:errors.append('FBX embedded atlas bytes do not match')
with tempfile.TemporaryDirectory(prefix='cube-delivery-verify-') as tempdir:
    temp_fbx=Path(tempdir)/'CubeDeliveryRobot.fbx'
    shutil.copyfile(ROOT/'CubeDeliveryRobot.fbx',temp_fbx)
    bpy.ops.import_scene.fbx(filepath=str(temp_fbx),use_image_search=False)
fbx=[o for o in bpy.context.scene.objects if o.type=='MESH']
fbx_bounds=bounds(fbx);fbx_rows=geometry_report(fbx)
delta=max(abs(fbx_bounds[k][i]-native_bounds[k][i]) for k in ['min','max'] for i in range(3))
if len(fbx)!=len(native_rows) or delta>1e-5:errors.append('FBX roundtrip count/bounds mismatch')
if any(o.type!='MESH' for o in bpy.context.scene.objects):errors.append('FBX includes nonmesh studio data')
for row in fbx_rows:
    if row['geometric_zero_area_triangles'] or row['uv_zero_area_triangles'] or row['uv_out_of_bounds_values']:errors.append('FBX import invalid triangles/UV: '+row['name'])
dump('fbx_reimport_validation.json',{'mesh_count':len(fbx),'bounds':fbx_bounds,'max_bounds_difference_m':delta,'meshes':fbx_rows,'embedded_png_hashes':fbx_images,'note':'Verified by Blender 4.5 reimport; no Unreal Engine import or runtime check was performed.'})
unchanged={n:sha(ROOT/n)==digest for n,digest in initial_hashes.items()}
if not all(unchanged.values()):errors.append('Validation changed a deliverable')
summary={'passed':not errors,'errors':errors,'blender':bpy.app.version_string,'elapsed_seconds':time.time()-t0,'native_mesh_count':len(native_rows),'native_triangles':sum(r['triangles'] for r in native_rows),'bounds_m':native_bounds,'atlas_packed_hash_matches_external':packed_hash==initial_hashes['textures/CubeDeliveryRobot_BaseColor_4096.png'],'missing_resources':missing,'uv':uv_report,'glb_render_mae':mae,'read_only_model_hashes_unchanged':unchanged,'sha256':initial_hashes,'limitations':['Static assembly only: no rig, collision, LODs, physics, gameplay or UE import.','Rear cargo hinge and removable parcel are separate meshes; open view is an explicit preview pose.','UV raster audit has subpixel limitations, noted in uv_validation.json.']}
dump('validation.json',summary)
print('VALIDATION_SUMMARY',json.dumps(summary))
if errors:raise RuntimeError('; '.join(errors))
