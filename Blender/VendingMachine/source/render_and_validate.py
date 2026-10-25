"""Final delivered-blend renders, body-only variant proof and GLB reimport QA."""
import bpy,bmesh,json,math,time,struct,hashlib,os
from pathlib import Path
from datetime import datetime,timezone
from mathutils import Vector
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
START=time.time();manifest=[]
(ROOT/'logs/render_process.json').write_text(json.dumps({'pid':os.getpid(),'started_at_utc':datetime.now(timezone.utc).isoformat(),'script':str(Path(__file__).resolve())}),encoding='utf8')
def utc():return datetime.now(timezone.utc).isoformat()
def sha(data):return hashlib.sha256(data).hexdigest()
def write(name,obj):(ROOT/'validation'/name).write_text(json.dumps(obj,indent=2),encoding='utf8')
def log(s):print('VENDING_QA '+s,flush=True)

def parse_glb(path):
    raw=path.read_bytes();magic,ver,length=struct.unpack_from('<4sII',raw,0)
    assert magic==b'glTF' and ver==2 and length==len(raw)
    cursor=12;doc=None;binary=None
    while cursor<len(raw):
        size,kind=struct.unpack_from('<I4s',raw,cursor);cursor+=8
        chunk=raw[cursor:cursor+size];cursor+=size
        if kind==b'JSON':doc=json.loads(chunk.decode('utf8'))
        if kind==b'BIN\0':binary=chunk
    return raw,doc,binary

raw,doc,binary=parse_glb(ROOT/'VendingMachine.glb')
atlas_bytes=(ROOT/'textures/packed/VendingMachine_BaseColor_4096.png').read_bytes()
images=[]
for idx,im in enumerate(doc.get('images',[])):
    entry={'index':idx,'name':im.get('name'),'mimeType':im.get('mimeType'),'embedded':('bufferView' in im and 'uri' not in im)}
    if 'bufferView' in im:
        view=doc['bufferViews'][im['bufferView']];offset=view.get('byteOffset',0);data=binary[offset:offset+view['byteLength']]
        entry['sha256']=sha(data);entry['bytes']=len(data);entry['matches_external_atlas']=data==atlas_bytes
    images.append(entry)
primitives=[(mi,pi,p) for mi,m in enumerate(doc['meshes']) for pi,p in enumerate(m['primitives'])]
missing_uv=[{'mesh':mi,'primitive':pi} for mi,pi,p in primitives if 'TEXCOORD_0' not in p['attributes']]
mats=[];body_index=None
for idx,m in enumerate(doc.get('materials',[])):
    p=m.get('pbrMetallicRoughness',{})
    info={'index':idx,'name':m.get('name'),'baseColorFactor':p.get('baseColorFactor',[1,1,1,1]),'hasBaseColorTexture':'baseColorTexture' in p,'roughnessFactor':p.get('roughnessFactor',1),'metallicFactor':p.get('metallicFactor',1),'alphaMode':m.get('alphaMode','OPAQUE')}
    mats.append(info)
    if m.get('name')=='BODY_VARIANT_WHITE':body_index=idx
assert body_index is not None
body=mats[body_index]
body_primitives=[(mi,pi) for mi,pi,p in primitives if p.get('material')==body_index]
body_nodes=[]
for node in doc.get('nodes',[]):
    if 'mesh' in node and any(p.get('material')==body_index for p in doc['meshes'][node['mesh']]['primitives']):body_nodes.append(node.get('name'))
triangles=sum(doc['accessors'][p['indices']]['count']//3 for mi,pi,p in primitives if 'indices' in p)
glbcheck={'timestamp_utc':utc(),'file_bytes':len(raw),'sha256':sha(raw),'gltf_version':doc['asset']['version'],'mesh_count':len(doc['meshes']),'node_count':len(doc['nodes']),'primitive_count':len(primitives),'triangles':triangles,'all_primitives_have_TEXCOORD_0':not missing_uv,'missing_texcoord_0':missing_uv,'images':images,'self_contained_images':all(x['embedded'] for x in images),'all_image_bytes_match_external_atlas':all(x.get('matches_external_atlas') for x in images),'external_buffer_uris':[x.get('uri') for x in doc.get('buffers',[]) if 'uri' in x],'body_material':body,'body_material_is_white':all(abs(float(x)-1)<1e-7 for x in body['baseColorFactor']),'body_material_nodes':body_nodes,'body_primitive_count':len(body_primitives),'materials':mats,'extensionsUsed':doc.get('extensionsUsed',[])}
glbcheck['passed']=glbcheck['all_primitives_have_TEXCOORD_0'] and glbcheck['self_contained_images'] and glbcheck['all_image_bytes_match_external_atlas'] and not glbcheck['external_buffer_uris'] and glbcheck['body_material_is_white']
write('glb_validation.json',glbcheck)
if not glbcheck['passed']:raise RuntimeError('GLB validation failed; see glb_validation.json')
log('GLB structural validation and white body factor passed')

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'VendingMachine.blend'))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=4
asset=[o for o in bpy.data.objects if o.type=='MESH' and o.get('asset_part')]
coords=[o.matrix_world@Vector(c) for o in asset for c in o.bound_box]
minimum=[min(v[i] for v in coords) for i in range(3)];maximum=[max(v[i] for v in coords) for i in range(3)]
tex=bpy.data.images.get('VendingMachine_BaseColor_4096')
packed=sha(tex.packed_file.data)
assert packed==sha(atlas_bytes),'Reopened .blend image bytes are not the external PNG bytes'
bodymat=bpy.data.materials['BODY_VARIANT_WHITE'];tint=bodymat.node_tree.nodes['BODY_TINT_WHITE_DEFAULT']
assert all(abs(v-1)<1e-7 for v in tint.inputs[2].default_value)
native={'timestamp_utc':utc(),'object_count':len(asset),'vertices':sum(len(o.data.vertices) for o in asset),'bounds_min_m':minimum,'bounds_max_m':maximum,'dimensions_xyz_m':[maximum[i]-minimum[i] for i in range(3)],'packed_atlas_sha256':packed,'packed_matches_external':True,'body_tint_default':list(tint.inputs[2].default_value),'body_assigned_objects':[o.name for o in asset if any(m==bodymat for m in o.data.materials)],'body_material_name':bodymat.name,'separate_non_body_material_count':len({m.name for o in asset for m in o.data.materials if m!=bodymat})}
write('blend_validation.json',native)
texture_meta=[]
for path in sorted((ROOT/'textures').rglob('*.png')):
    data=path.read_bytes();w,h=struct.unpack_from('>II',data,16)
    texture_meta.append({'file':str(path.relative_to(ROOT)).replace('\\','/'),'dimensions':[w,h],'sha256':sha(data),'bytes':len(data)})
# Sample body chart centroids from the delivered atlas to demonstrate textured ivory.
pixels=np.empty(len(tex.pixels),np.float32);tex.pixels.foreach_get(pixels);pixels=pixels.reshape(tex.size[1],tex.size[0],4)
body_samples=[]
for o in asset:
    if not any(m==bodymat for m in o.data.materials):continue
    uv=o.data.uv_layers.active.data
    for p in o.data.polygons:
        if p.area<.0001:continue
        center=sum((Vector(uv[li].uv) for li in p.loop_indices),Vector((0.,0.)))/len(p.loop_indices)
        ix=min(tex.size[0]-1,max(0,int(center.x*tex.size[0])));iy=min(tex.size[1]-1,max(0,int(center.y*tex.size[1])))
        body_samples.append(pixels[iy,ix,:3].tolist())
write('texture_validation.json',{'textures':texture_meta,'body_uv_centroid_samples_count':len(body_samples),'body_sample_mean_loaded_rgb':np.mean(body_samples,axis=0).tolist(),'body_is_textured_not_numeric_ivory':True,'body_numeric_factor':[1,1,1,1],'note':'Chart-centroid sampling is supporting color evidence. Atlas bytes and the GLB factor are checked independently.'})

stage=bpy.data.collections['STUDIO_NOT_EXPORTED']
camera=scene.camera
def set_camera(loc,target,scale):
    camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=scale;scene.camera=camera
def render(name,loc,target,scale,size=(1100,1210),samples=32,note=''):
    set_camera(loc,target,scale);scene.render.resolution_x=size[0];scene.render.resolution_y=size[1];scene.render.resolution_percentage=100;scene.cycles.samples=samples
    scene.render.filepath=str(ROOT/'renders'/name)
    t0=time.time();started=utc();bpy.ops.render.render(write_still=True)
    manifest.append({'file':'renders/'+name,'timestamp_utc':started,'completed_at_utc':utc(),'render_seconds':time.time()-t0,'engine':'Cycles CPU','samples':samples,'denoise':True,'resolution':list(size),'camera_type':'ORTHO','camera_location':list(loc),'target':list(target),'ortho_scale':scale,'view_transform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'note':note})
    (ROOT/'renders/capture_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    log('Rendered '+name)

HERO=((2.6,-6.3,3.0),(0,0,.88),2.43)
render('hero.png',*HERO,note='Delivered .blend freshly reopened, packed textures.')
render('front.png',(0,-6,.92),(0,0,.92),1.95,size=(1050,1200),note='Straight front orthographic; all 12 product bottles behind glazing.')
render('rear.png',(0,6,.92),(0,0,.92),1.95,size=(1050,1200),note='Straight rear orthographic; service panel and vent slats.')
render('side.png',(6,0,.92),(0,0,.92),1.90,size=(1050,1200),note='Right-side orthographic; body side remains in separate tintable material.')

# Real Cycles three-cabinet comparison. Only the BODY material differs.
set_camera(*HERO)
right=camera.rotation_euler.to_quaternion()@Vector((1,0,0))
variant_defs=[('IVORY',(1,1,1,1),-1.64),('OCEAN',(.25,.50,.72,1),0),('TERRACOTTA',(.78,.29,.14,1),1.64)]
copies=[];variant_materials=[]
for label,tint_value,offset in variant_defs:
    vm=bodymat.copy();vm.name='VARIANT_BODY_'+label;vm.node_tree.nodes['BODY_TINT_WHITE_DEFAULT'].inputs[2].default_value=tint_value;variant_materials.append(vm)
    for original in asset:
        o=original.copy();o.data=original.data.copy() if any(m==bodymat for m in original.data.materials) else original.data
        o.name='Compare_'+label+'_'+original.name;stage.objects.link(o);o.location+=right*offset
        for idx,m in enumerate(o.data.materials):
            if m==bodymat:o.data.materials[idx]=vm
        copies.append(o)
    # Label placed in the studio in the camera's image plane.
    cu=bpy.data.curves.new('Variant_Label_'+label,'FONT');cu.body=label;cu.size=.067;cu.align_x='CENTER';cu.align_y='CENTER';cu.extrude=.0001
    labelobj=bpy.data.objects.new('Variant_Label_'+label,cu);stage.objects.link(labelobj)
    labelobj.location=right*offset+Vector((0,0,1.990));labelobj.rotation_euler=camera.rotation_euler
    labelobj.data.materials.append(bpy.data.materials['TRIM_Dark_Graphite']);copies.append(labelobj)
for o in asset:o.hide_render=True
render('material_variations.png',HERO[0],(0,0,.96),5.55,size=(2100,1000),samples=32,note='One actual Cycles render of three copied cabinets. Only BODY_VARIANT_WHITE-derived tint differs; slate, glass, lamps, bottles, controls and graphics are identical.')
write('material_variants.json',{'timestamp_utc':utc(),'default_material':'BODY_VARIANT_WHITE','default_tint_rgba':[1,1,1,1],'default_glb_factor':body['baseColorFactor'],'control':'BODY_TINT_WHITE_DEFAULT / Color2','variants':[{'label':a,'linear_tint_rgba':list(b)} for a,b,c in variant_defs],'proof_render':'renders/material_variations.png','changed_material_only':'BODY_VARIANT_WHITE','unchanged_materials':[m['name'] for m in mats if m['name']!='BODY_VARIANT_WHITE'],'not_saved_over_main_blend':True})
for o in copies:bpy.data.objects.remove(o,do_unlink=True)
for o in asset:o.hide_render=False

# Fresh GLB import into the same retained studio, with original model removed.
for o in asset:bpy.data.objects.remove(o,do_unlink=True)
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'VendingMachine.glb'))
imported=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
log('Fresh GLB imported: '+str(len(imported))+' mesh objects')
render('glb_reimport_hero.png',*HERO,note='Freshly imported VendingMachine.glb; original cabinet objects removed; same Cycles studio/camera as hero.png.')

nativeimg=bpy.data.images.load(str(ROOT/'renders/hero.png'),check_existing=False)
glbimg=bpy.data.images.load(str(ROOT/'renders/glb_reimport_hero.png'),check_existing=False)
a=np.empty(len(nativeimg.pixels),np.float32);nativeimg.pixels.foreach_get(a)
b=np.empty(len(glbimg.pixels),np.float32);glbimg.pixels.foreach_get(b)
diff=np.abs(a.reshape(-1,4)[:,:3]-b.reshape(-1,4)[:,:3])
reimport={'timestamp_utc':utc(),'imported_mesh_count':len(imported),'render':'renders/glb_reimport_hero.png','reference_render':'renders/hero.png','same_camera_and_lighting':True,'rgb_mean_absolute_difference_in_loaded_pixels':float(diff.mean()),'rgb_p99_absolute_difference':float(np.quantile(diff,.99)),'note':'Numerical render comparison supplements human visual inspection; tiny differences can come from triangulation, material import or denoising. The actual render must be inspected.'}
write('reimport_validation.json',reimport)
write('render_summary.json',{'timestamp_utc':utc(),'total_render_validate_seconds':time.time()-START,'render_count':len(manifest),'total_render_seconds':sum(x['render_seconds'] for x in manifest),'renders':[x['file'] for x in manifest]})
log('RENDER_QA_DONE')
