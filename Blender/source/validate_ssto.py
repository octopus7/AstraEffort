"""Read-only checks of final .blend / GLB, plus independent re-import render."""
import bpy, bmesh, numpy as np, json, math, struct, hashlib, datetime, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('SSTO_')]
N=4096
coverage=np.zeros((N,N),dtype=np.uint8)
owners=np.zeros((N,N),dtype=np.uint8)
stats=[];tri_stats=[];zero_uv=0;outside=0;overlap_pixels=0;manifold={}
for oi,o in enumerate(meshes):
    me=o.data;me.calc_loop_triangles();uv=me.uv_layers.active
    bm=bmesh.new();bm.from_mesh(me)
    manifold[o.name]={'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges)};bm.free()
    uvs=np.array([p.uv[:] for p in uv.data],dtype=np.float64)
    outside+=int(np.sum(np.any((uvs < -1e-7)|(uvs>1+1e-7),axis=1)))
    wa=ua=0
    for tri in me.loop_triangles:
        a,b,c=uvs[list(tri.loops)]
        area=abs(np.cross(b-a,c-a))*.5
        warea=tri.area
        wa+=warea;ua+=area
        if area<1e-14:
            zero_uv+=1;continue
        if warea>1e-12:tri_stats.append((math.sqrt(area/warea)*N,warea))
        pts=np.array([a,b,c])*N
        xmin=max(0,int(np.ceil(pts[:,0].min()-.5)));xmax=min(N-1,int(np.floor(pts[:,0].max()-.5)))
        ymin=max(0,int(np.ceil(pts[:,1].min()-.5)));ymax=min(N-1,int(np.floor(pts[:,1].max()-.5)))
        if xmax<xmin or ymax<ymin:continue
        xs,ys=np.meshgrid(np.arange(xmin,xmax+1)+.5,np.arange(ymin,ymax+1)+.5)
        p0,p1,p2=pts
        den=(p1[1]-p2[1])*(p0[0]-p2[0])+(p2[0]-p1[0])*(p0[1]-p2[1])
        q1=((p1[1]-p2[1])*(xs-p2[0])+(p2[0]-p1[0])*(ys-p2[1]))/den
        q2=((p2[1]-p0[1])*(xs-p2[0])+(p0[0]-p2[0])*(ys-p2[1]))/den
        mask=(q1>1e-6)&(q2>1e-6)&(q1+q2<1-1e-6)
        block=coverage[ymin:ymax+1,xmin:xmax+1]
        overlap_pixels+=int(np.sum(mask&(block>0)))
        block[mask]+=1;owners[ymin:ymax+1,xmin:xmax+1][mask]=oi+1
    stats.append({'mesh':o.name,'surface_m2':wa,'uv_area':ua,'effective_texels_per_meter':math.sqrt(ua/wa)*N,'triangles':len(me.loop_triangles)})

ordered=sorted(tri_stats);tw=sum(w for _,w in ordered)
def quantile(p):
    s=0
    for v,w in ordered:
        s+=w
        if s>=tw*p:return v
    return ordered[-1][0]

# A UV inspection image, computed from mesh UVs (not scene evidence or an asset texture).
palette=np.array([[.035,.045,.06,1],[.90,.79,.58,1],[.25,.49,.65,1],[.82,.37,.15,1],[.38,.68,.53,1],[.58,.46,.76,1],[.7,.65,.32,1],[.34,.64,.73,1],[.7,.39,.45,1],[.4,.53,.33,1],[.65,.50,.34,1],[.5,.58,.67,1]],dtype=np.float32)
vis=palette[owners]
im=bpy.data.images.new('UV_Layout_Verification',width=N,height=N,alpha=True)
im.pixels.foreach_set(vis.reshape(-1));im.filepath_raw=str(ROOT/'validation'/'UV_layout_4096.png');im.file_format='PNG';im.save()

raw=(ROOT/'SSTO.glb').read_bytes();magic,version,length=struct.unpack_from('<4sII',raw)
pos=12;gltf=None
while pos<len(raw):
    n,kind=struct.unpack_from('<I4s',raw,pos);pos+=8
    if kind==b'JSON':gltf=json.loads(raw[pos:pos+n].decode('utf-8'))
    pos+=n
assert gltf
images=gltf.get('images',[])
primitives=[p for m in gltf['meshes'] for p in m['primitives']]
report={
    'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'source_mesh_count':len(meshes),'uv_out_of_bounds_corners':outside,'zero_area_uv_triangles':zero_uv,
    'uv_overlap_pixels_at_4096':overlap_pixels,'uv_covered_pixels':int(np.sum(coverage>0)),
    'uv_coverage_percent':float(np.mean(coverage>0)*100),
    'uv_overlap_method':'4096 x 4096 interior pixel rasterization, barycentric epsilon 1e-6. Subpixel intersections are not ruled out by this test.',
    'density_world_area_weighted_px_per_m':{str(p):quantile(p) for p in (.01,.05,.5,.95,.99)},
    'mesh_density':stats,'topology':manifold,
    'glb':{'magic':magic.decode(),'version':version,'declared_bytes':length,'actual_bytes':len(raw),
           'mesh_count':len(gltf['meshes']),'primitive_count':len(primitives),'material_count':len(gltf['materials']),
           'all_primitives_have_uv':all('TEXCOORD_0' in p['attributes'] for p in primitives),
           'image_count':len(images),'all_images_embedded':all('bufferView' in im and 'uri' not in im for im in images),
           'has_exported_cameras':bool(gltf.get('cameras')),'has_exported_lights':bool(gltf.get('extensions',{}).get('KHR_lights_punctual')),
           'sha256':hashlib.sha256(raw).hexdigest()},
}
(ROOT/'validation'/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('SSTO_VALIDATION',json.dumps(report),flush=True)
assert outside==0, 'UV bounds check failed'
assert overlap_pixels==0, 'UV overlap raster check failed'
assert zero_uv==0, 'Collapsed UV triangles remain'
assert length==len(raw) and magic==b'glTF' and version==2, 'Invalid GLB header'
assert images and report['glb']['all_images_embedded'], 'Textures must be embedded'
assert report['glb']['all_primitives_have_uv'], 'Every exported primitive needs UVs'

# Re-import the actual GLB into a fresh scene while retaining the source studio only.
for o in list(meshes):bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'SSTO.glb'))
imported=[o for o in bpy.context.selected_objects if o.type=='MESH']
coords=[o.matrix_world@v.co for o in imported for v in o.data.vertices]
dimensions=[max(v[i] for v in coords)-min(v[i] for v in coords) for i in range(3)]
report['reimport']={'mesh_count':len(imported),'dimensions_m':dimensions,'material_slots':sum(len(o.material_slots) for o in imported),'all_have_uv':all(bool(o.data.uv_layers) for o in imported)}
assert len(imported)==len(meshes), 'Re-import changed assembly count'
assert abs(dimensions[2]-24.0)<.001, 'Re-import changed reference scale'
assert report['reimport']['all_have_uv'], 'Re-import lost UVs'
report['required_checks_passed']=True
(ROOT/'validation'/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
if '--no-render' in sys.argv:
    print('REIMPORT_CHECK_DONE',flush=True)
    raise SystemExit(0)
scene=bpy.context.scene
scene.cycles.samples=32;scene.render.resolution_x=1100;scene.render.resolution_y=1300;scene.render.resolution_percentage=100
cam=scene.camera
def render(name,pos,target,scale,floor=True):
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    bpy.data.objects['Studio_floor_NOT_EXPORTED'].hide_render=not floor
    scene.render.filepath=str(ROOT/'renders'/name);bpy.ops.render.render(write_still=True)

render('glb_reimport_front.png',(0,-52,15),(0,0,12),27)
render('rear.png',(-30,45,26),(0,0,11.7),29.3)
render('engines.png',(14,-20,-12),(0,0,4.0),17,False)
(ROOT/'validation'/'capture_manifest.json').write_text(json.dumps({'engine':'Cycles','source':'Independently re-imported SSTO.glb','samples':32,'resolution':[1100,1300],'views':['glb_reimport_front.png','rear.png','engines.png'],'captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2),encoding='utf-8')
print('VALIDATION_DONE',flush=True)
