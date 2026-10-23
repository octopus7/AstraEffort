"""Fresh saved-file and exchange-file checks. Run in an isolated Blender process."""
from pathlib import Path
import sys,json,struct,hashlib,time
from datetime import datetime,timezone
import numpy as np
import bpy

def hash_file(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def parse_native(path):
    raw=path.read_bytes();assert raw[:8]==b'VOX '+struct.pack('<I',150)
    assert raw[8:12]==b'MAIN';rootlen,children=struct.unpack_from('<II',raw,12);assert rootlen==0 and children+20==len(raw)
    pos=20;parts={}
    while pos<len(raw):
        kind=raw[pos:pos+4];n,c=struct.unpack_from('<II',raw,pos+4);assert c==0 and pos+12+n<=len(raw)
        assert kind not in parts;parts[kind]=raw[pos+12:pos+12+n];pos+=12+n
    shape=struct.unpack('<3I',parts[b'SIZE']);assert min(shape)>0 and max(shape)<=256
    block=parts[b'XYZI'];count=struct.unpack_from('<I',block)[0];assert len(block)==4+4*count and count>0
    vox=np.frombuffer(block[4:],np.uint8).reshape(-1,4);assert np.all(vox[:,:3]<shape) and np.all(vox[:,3]>0)
    keys=np.ravel_multi_index(vox[:,:3].T,shape);assert len(np.unique(keys))==count
    palette=np.frombuffer(parts[b'RGBA'],np.uint8).reshape(256,4)
    grid=np.zeros(shape,np.uint8);grid[tuple(vox[:,:3].T)]=vox[:,3]
    return grid,palette,count

def inspect_meshes(objects,meta,grid,strict_studio):
    meshes=[o for o in objects if o.type=='MESH'];assert len(meshes)==1,f'expected 1 voxel mesh, got {len(meshes)}'
    if strict_studio:assert not any(o.type in ('CAMERA','LIGHT') for o in objects),'studio leaked into export'
    verts=[];triangles=0;area=0.;bad=0;wrong_boundary=0;bad_materials=0;offgrid=0
    scale=meta['voxel_size_m'];shape=np.array(grid.shape);origin=np.array((shape[0]/2,shape[1]/2,0))
    for obj in meshes:
        mesh=obj.data;mesh.calc_loop_triangles();world=obj.matrix_world
        xyz=np.array([tuple(world@v.co) for v in mesh.vertices]);assert np.isfinite(xyz).all()
        verts.extend(xyz);offgrid+=int(np.count_nonzero(np.abs(xyz/scale+origin-np.round(xyz/scale+origin))>1e-3))
        for tri in mesh.loop_triangles:
            triangles+=1;p=xyz[list(tri.vertices)];cross=np.cross(p[1]-p[0],p[2]-p[0]);twice=float(np.linalg.norm(cross));area+=twice/2
            if twice<1e-12:bad+=1;continue
            normal=cross/twice;center=p.mean(axis=0)
            inn=np.floor((center-normal*.1*scale)/scale+origin+1e-5).astype(int)
            out=np.floor((center+normal*.1*scale)/scale+origin+1e-5).astype(int)
            inside_valid=np.all(inn>=0)&np.all(inn<shape);outside_valid=np.all(out>=0)&np.all(out<shape)
            if not inside_valid or grid[tuple(inn)]==0 or (outside_valid and grid[tuple(out)]>0):wrong_boundary+=1
            mi=mesh.polygons[tri.polygon_index].material_index
            if mi>=len(mesh.materials) or mesh.materials[mi] is None:bad_materials+=1
            elif inside_valid:
                name=mesh.materials[mi].name
                try:idx=int(name.split('_')[1])
                except Exception:bad_materials+=1;continue
                if idx!=int(grid[tuple(inn)]):bad_materials+=1
    verts=np.array(verts);bounds=[verts.min(axis=0).tolist(),verts.max(axis=0).tolist()]
    assert np.allclose(bounds,meta['bounds_m'],atol=2e-5,rtol=1e-5),'bounds mismatch'
    assert triangles==meta['surface']['triangles'],'triangle count mismatch'
    assert abs(area-meta['surface']['surface_area_m2'])<=max(1e-5,area*2e-5),'surface area mismatch'
    assert bad==0 and wrong_boundary==0 and bad_materials==0 and offgrid==0,f'bad triangles {bad}, boundary {wrong_boundary}, materials {bad_materials}, grid {offgrid}'
    return {'meshes':len(meshes),'triangles':triangles,'bounds_m':bounds,'surface_area_m2':area,'degenerate_triangles':bad,'invalid_boundary_triangles':wrong_boundary,'invalid_material_triangles':bad_materials,'offgrid_coordinates':offgrid}

def main():
    args=sys.argv[sys.argv.index('--')+1:];root=Path(args[0]);dest=Path(args[1]) if len(args)>1 else root/'validation_export.json'
    t0=time.perf_counter();started=datetime.now(timezone.utc).isoformat();records=[];errors=[]
    for meta_path in sorted((root/'assets').glob('*/*/metadata.json')):
        directory=meta_path.parent;meta=json.loads(meta_path.read_text(encoding='utf-8'));slug=meta['asset'];variant=meta['variant'];record={'asset':slug,'variant':variant}
        try:
            grid,palette,count=parse_native(directory/(slug+'.vox'))
            assert list(grid.shape)==meta['grid_size'];assert count==meta['occupied_voxels']
            assert hashlib.sha256(grid.tobytes()).hexdigest()==meta['occupancy_sha256']
            expected=np.array(meta['palette'][1:],np.uint8);assert np.array_equal(palette[:len(expected)],expected)
            for name,digest in meta['sha256'].items():assert hash_file(directory/name)==digest,f'changed file: {name}'
            if variant=='half':
                lg=json.loads((directory.parent/'large'/'metadata.json').read_text(encoding='utf-8'));assert [n*2 for n in grid.shape]==lg['grid_size'];assert abs(meta['voxel_size_m']-lg['voxel_size_m']*2)<1e-10;assert np.allclose(meta['grid_extents_m'],lg['grid_extents_m'])
            imports={}
            for ext in ('blend','glb','fbx'):
                path=directory/(slug+'.'+ext)
                if ext=='blend':
                    bpy.ops.wm.open_mainfile(filepath=str(path));objects=list(bpy.data.collections['ASSET'].all_objects)
                else:
                    bpy.ops.wm.read_factory_settings(use_empty=True)
                    if ext=='glb':bpy.ops.import_scene.gltf(filepath=str(path))
                    else:bpy.ops.import_scene.fbx(filepath=str(path))
                    objects=list(bpy.context.scene.objects)
                imports[ext]=inspect_meshes(objects,meta,grid,ext!='blend')
            record.update(passed=True,occupied_voxels=count,imports=imports,sha256=meta['sha256'])
        except Exception as e:
            errors.append(f'{slug}/{variant}: {type(e).__name__}: {e}');record.update(passed=False,error=str(e))
        records.append(record)
    if not records:errors.append('no delivered variants found')
    names={r['asset'] for r in records}
    for name in names:
        if {r['variant'] for r in records if r['asset']==name}!={'large','half'}:errors.append(name+': missing size variant')
    result={'theme':root.name,'passed':not errors,'started_at_utc':started,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.perf_counter()-t0,'asset_count':len(names),'variant_count':len(records),'errors':errors,'records':records}
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'passed':not errors,'asset_count':len(names),'variant_count':len(records),'errors':errors,'report':str(dest)},ensure_ascii=False),flush=True)
    if errors:raise RuntimeError('validation failed: '+str(errors))

if __name__=='__main__':main()
