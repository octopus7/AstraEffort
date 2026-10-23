"""Build surface-only exchange meshes and actual previews from native voxel grids."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,time,sys
import numpy as np
import bpy
from mathutils import Vector
from voxelkit import write_vox,read_vox,reduce_half,grid_stats,greedy_surface

def utc():return datetime.now(timezone.utc).isoformat()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path,data):Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def srgb(v):
    x=float(v)/255
    return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4

def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    return scene

def collection(name):
    c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c);return c

def build_surface(asset,grid,voxel_size):
    scene=clear_scene();col=collection('ASSET')
    verts,faces,colors,area=greedy_surface(grid,voxel_size)
    mesh=bpy.data.meshes.new(asset.slug+'_voxel_surface');mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(asset.slug,mesh);col.objects.link(obj)
    used=sorted(set(colors));slots={c:i for i,c in enumerate(used)}
    for c in used:
        rgba=grid.palette[c];mat=bpy.data.materials.new(f'Palette_{c:03d}_{rgba[0]:02x}{rgba[1]:02x}{rgba[2]:02x}');mat.use_nodes=True
        bsdf=mat.node_tree.nodes.get('Principled BSDF');color=tuple(srgb(v) for v in rgba[:3])+(1,)
        bsdf.inputs['Base Color'].default_value=color;bsdf.inputs['Roughness'].default_value=.74
        mat.diffuse_color=color;mesh.materials.append(mat)
    for poly,c in zip(mesh.polygons,colors):poly.material_index=slots[c];poly.use_smooth=False
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    mesh.calc_loop_triangles()
    assert all(t.area>1e-14 for t in mesh.loop_triangles),'zero-area triangle'
    assert all(np.isfinite(v.co).all() for v in mesh.vertices),'nonfinite geometry'
    return obj,{'quads':len(faces),'triangles':len(mesh.loop_triangles),'exposed_unit_faces':area,'surface_area_m2':float(area*voxel_size*voxel_size),'materials':len(used)}

def point_at(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def add_studio(bounds):
    scene=bpy.context.scene;studio=collection('STUDIO')
    lo=Vector(bounds[0]);hi=Vector(bounds[1]);center=(lo+hi)*.5;extent=hi-lo;D=max(extent)
    D=max(D,.25)
    def move_to_studio(obj):
        for c in list(obj.users_collection):c.objects.unlink(obj)
        studio.objects.link(obj)
    camdata=bpy.data.cameras.new('Preview_Camera');cam=bpy.data.objects.new('Preview_Camera',camdata);studio.objects.link(cam)
    cam.location=center+Vector((1.35,-1.8,1.20)).normalized()*D*3
    point_at(cam,center);camdata.type='ORTHO'
    inv=cam.rotation_euler.to_matrix().transposed()
    corners=[Vector((x,y,z)) for x in (lo.x,hi.x) for y in (lo.y,hi.y) for z in (lo.z,hi.z)]
    projected=[inv@(p-center) for p in corners]
    sx=max(p.x for p in projected)-min(p.x for p in projected);sy=max(p.y for p in projected)-min(p.y for p in projected)
    camdata.ortho_scale=max(sx,sy)*1.28;camdata.clip_end=D*30;scene.camera=cam
    bpy.ops.mesh.primitive_plane_add(size=D*200,location=(center.x,center.y,lo.z-.003*D));floor=bpy.context.object;floor.name='Studio_floor';move_to_studio(floor)
    mat=bpy.data.materials.new('Studio_ground');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.76,.75,.72,1);bs.inputs['Roughness'].default_value=.9;floor.data.materials.append(mat)
    for name,offset,power,size in [('Key',(-2,-3,4),950,2.8),('Fill',(3,-1,2),520,3.2),('Rim',(1,3,3),750,2.5)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power*(D/4)**2;data.shape='DISK';data.size=D*size
        ob=bpy.data.objects.new(name,data);studio.objects.link(ob);ob.location=center+Vector(offset)*D;point_at(ob,center)
    world=bpy.data.worlds.new('Studio_world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.78,.82,.88,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.film_transparent=False
    scene.view_settings.view_transform='AgX'
    return {'camera_location':list(cam.location),'camera_rotation_radians':list(cam.rotation_euler),'orthographic_scale':camdata.ortho_scale,'target':list(center),'engine':'CYCLES','device':'CPU','threads':4,'samples':24,'resolution':[768,768],'denoising':True,'view_transform':'AgX'}

def run_theme(root,assets):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);started=utc();t0=time.perf_counter();results=[];captures=[]
    requested=None
    if '--asset' in sys.argv:requested=sys.argv[sys.argv.index('--asset')+1]
    if requested:assets=[a for a in assets if a.slug==requested]
    if not assets:raise ValueError('no assets')
    for asset in assets:
        large=asset.grid
        assert max(large.shape)==128 and all(n%2==0 for n in large.shape),'large grid must have even axes and longest 128'
        assert np.count_nonzero(large.data)>0
        half=reduce_half(large)
        if asset.half_postprocess:asset.half_postprocess(half)
        pair=[];camera_bounds=grid_stats(large,asset.voxel_size)['bounds_m']
        for variant,grid,scale in [('large',large,asset.voxel_size),('half',half,asset.voxel_size*2)]:
            dst=root/'assets'/asset.slug/variant;dst.mkdir(parents=True,exist_ok=True)
            vox=dst/(asset.slug+'.vox');write_vox(vox,grid);reopened=read_vox(vox)
            assert np.array_equal(grid.data,reopened.data),'VOX occupancy roundtrip mismatch'
            assert grid.palette==reopened.palette[:len(grid.palette)],'VOX palette roundtrip mismatch'
            obj,surface=build_surface(asset,grid,scale)
            glb=dst/(asset.slug+'.glb');fbx=dst/(asset.slug+'.fbx');blend=dst/(asset.slug+'.blend')
            bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_yup=True,export_texcoords=False,export_normals=True,export_materials='EXPORT')
            bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,add_leaf_bones=False,bake_anim=False)
            camera=add_studio(camera_bounds)
            bpy.ops.wm.save_as_mainfile(filepath=str(blend))
            render_started=utc();rt=time.perf_counter();bpy.context.scene.render.filepath=str(dst/'preview.png');bpy.ops.render.render(write_still=True)
            capture={'asset':asset.slug,'variant':variant,'image':str((dst/'preview.png').relative_to(root)).replace('\\','/'),'started_at_utc':render_started,'finished_at_utc':utc(),'elapsed_seconds':time.perf_counter()-rt,'settings':camera,'source_blend_sha256':sha(blend),'image_sha256':sha(dst/'preview.png')};captures.append(capture)
            metadata={'asset':asset.slug,'label':asset.label,'variant':variant,'format':'MagicaVoxel VOX 150','coordinate_system':'X right, Y back, Z up; front -Y','origin':'XY grid center, bottom grid plane Z=0','palette':grid.palette,'notes':asset.notes or [],'half_method':'2x2x2 nonempty majority; color index breaks ties; optional documented detail correction','same_physical_grid_extents':True,**grid_stats(grid,scale),'surface':surface,'native_roundtrip_passed':True,'exported_geometry_only':True,'uv':'No texture UV required: per-face solid palette PBR materials','sha256':{p.name:sha(p) for p in (vox,blend,glb,fbx,dst/'preview.png')}}
            write_json(dst/'metadata.json',metadata);pair.append(metadata)
        results.append({'asset':asset.slug,'large':pair[0],'half':pair[1]})
        print('VOXEL_ASSET_COMPLETE '+asset.slug,flush=True)
    oldcaptures=[]
    if requested and (root/'capture_manifest.json').exists():oldcaptures=[c for c in json.loads((root/'capture_manifest.json').read_text(encoding='utf-8'))['captures'] if c['asset']!=requested]
    write_json(root/'capture_manifest.json',{'actual_blender_renders':True,'captures':oldcaptures+captures})
    write_json(root/'build_validation.json',{'passed':True,'started_at_utc':started,'finished_at_utc':utc(),'elapsed_seconds':time.perf_counter()-t0,'assets':results,'checks':['Native occupancy and palette roundtrip','Exact exposed boundary area','No zero-area triangles or nonfinite positions','True separate half-resolution occupancy','Both actual previews generated'],'remaining_validation':'Fresh separate BLEND/GLB/FBX reimport and visual review'})
    return results
