#!/usr/bin/env python3
"""Verify actual GLB data, embedded texture use, repeat bounds and clearance."""
from pathlib import Path
from hashlib import sha256
import io, json
import numpy as np
from PIL import Image
import trimesh
from pygltflib import GLTF2
from pygltflib.validator import validate

P=Path(__file__).resolve().parent

def data(gltf, index, cols, dtype):
    acc=gltf.accessors[index];view=gltf.bufferViews[acc.bufferView]
    return np.frombuffer(gltf.binary_blob(),dtype=dtype,count=acc.count*cols,offset=(view.byteOffset or 0)+(acc.byteOffset or 0)).reshape(-1,cols)

def run(name):
    p=P/name; gltf=GLTF2().load(str(p)); assert not validate(gltf)
    scene=trimesh.load(p,force='scene',process=False)
    points=[]; face_count=0; degenerate=0; min_track_y=[float('inf')]*3
    tracks=[(-5.8,-2.2),(-1.5,1.5),(2.2,5.8)]
    for primitive in gltf.meshes[0].primitives:
        pos=data(gltf,primitive.attributes.POSITION,3,'<f4');nor=data(gltf,primitive.attributes.NORMAL,3,'<f4');uv=data(gltf,primitive.attributes.TEXCOORD_0,2,'<f4');ind=data(gltf,primitive.indices,1,'<u4').reshape(-1,3)
        assert len(pos)==len(nor)==len(uv) and np.isfinite(pos).all() and np.isfinite(nor).all() and np.isfinite(uv).all()
        assert len(ind) and int(ind.max())<len(pos)
        tris=pos[ind];cross=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]);areas=np.linalg.norm(cross,axis=1)*.5
        degenerate+=int((areas<1e-9).sum());face_count+=len(ind);points.append(pos)
        low=tris.min(axis=1); high=tris.max(axis=1)
        for i,(left,right) in enumerate(tracks):
            xhits=(high[:,0]>=left)&(low[:,0]<=right)
            if xhits.any(): min_track_y[i]=min(min_track_y[i],float(low[xhits,1].min()))
    pts=np.concatenate(points); bounds=np.stack((pts.min(axis=0),pts.max(axis=0)))
    assert degenerate==0, f'{name}: {degenerate} degenerate faces'
    assert all(y>4.5 for y in min_track_y),min_track_y
    assert sum(len(m.faces) for m in scene.geometry.values())==face_count
    assert np.allclose(scene.bounds,bounds,atol=1e-5)
    assert np.allclose(bounds[:,0],[-9.99,9.99],atol=.005)
    assert abs(bounds[0,1])<1e-5
    assert len(gltf.images)==len(gltf.materials)
    for im in gltf.images:
        assert im.bufferView is not None and im.mimeType=='image/png'
        view=gltf.bufferViews[im.bufferView];blob=gltf.binary_blob()[view.byteOffset:view.byteOffset+view.byteLength]
        Image.open(io.BytesIO(blob)).verify()
        if im.name=='iron_cast_ai':
            assert sha256(blob).digest()==sha256((P/'ai_aged_cast_iron.png').read_bytes()).digest()
            material_idx=next(i for i,m in enumerate(gltf.materials) if m.name=='iron_cast_ai')
            assert any(pr.material==material_idx and pr.attributes.TEXCOORD_0 is not None for pr in gltf.meshes[0].primitives)
    if 'bay' in name:
        assert np.allclose(bounds[:,2],[0,6],atol=1e-5)
        glass=next(m for m in gltf.materials if m.name=='roof_glass')
        assert glass.alphaMode=='BLEND' and glass.doubleSided
        im=gltf.images[gltf.textures[glass.pbrMetallicRoughness.baseColorTexture.index].source];view=gltf.bufferViews[im.bufferView]
        image=Image.open(io.BytesIO(gltf.binary_blob()[view.byteOffset:view.byteOffset+view.byteLength]))
        assert image.mode=='RGBA' and 0<image.getextrema()[3][0]<image.getextrema()[3][1]<255
    return {'file':name,'triangles':face_count,'min_track_corridor_geometry_y':min_track_y,'bounds':bounds.tolist(),'degenerate_faces':degenerate,'trimesh_geometries':len(scene.geometry),'pygltflib_validation':'passed'}

if __name__=='__main__':
    result=[run('train_shed_bay.glb'),run('train_shed_end_frame.glb')]
    print(json.dumps(result,indent=2))
    (P/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
