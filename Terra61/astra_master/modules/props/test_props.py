"""Reusable furnishing export checks."""
from pathlib import Path
from io import BytesIO
import json, math
import numpy as np
from PIL import Image
from pygltflib import GLTF2
import trimesh

HERE=Path(__file__).resolve().parent


def data_for(gltf,accessor_id):
    accessor=gltf.accessors[accessor_id]; view=gltf.bufferViews[accessor.bufferView]
    dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[accessor.componentType]
    width={'SCALAR':1,'VEC2':2,'VEC3':3}[accessor.type]
    offset=(view.byteOffset or 0)+(accessor.byteOffset or 0)
    return np.frombuffer(gltf.binary_blob(),dtype=dtype,count=accessor.count*width,offset=offset).reshape(accessor.count,width)


def test_props():
    manifest=json.loads((HERE/'manifest.json').read_text())
    for name,limit in [('station_gaslamp',1200),('station_bench',1000),('station_clock_sign',1400)]:
        path=HERE/f'{name}.glb'
        assert path.exists(),f'missing {path}'
        gltf=GLTF2().load_binary(str(path))
        root=gltf.nodes[gltf.scenes[gltf.scene].nodes[0]]
        assert np.allclose(root.rotation,[-math.sqrt(.5),0,0,math.sqrt(.5)])
        assert all(im.bufferView is not None and im.uri is None for im in gltf.images)
        for im in gltf.images:
            v=gltf.bufferViews[im.bufferView]
            with Image.open(BytesIO(gltf.binary_blob()[(v.byteOffset or 0):(v.byteOffset or 0)+v.byteLength])) as image:
                image.verify()
        for mat in gltf.materials:
            assert mat.pbrMetallicRoughness.baseColorTexture is not None
            if mat.name not in ('lantern','sign3'):
                assert mat.normalTexture is not None and mat.pbrMetallicRoughness.metallicRoughnessTexture is not None
        for mesh in gltf.meshes:
            for p in mesh.primitives:
                assert p.attributes.TEXCOORD_0 is not None and p.attributes.NORMAL is not None
                positions=data_for(gltf,p.attributes.POSITION)
                normals=data_for(gltf,p.attributes.NORMAL)
                uvs=data_for(gltf,p.attributes.TEXCOORD_0)
                indices=data_for(gltf,p.indices).ravel()
                assert len(positions)==len(normals)==len(uvs)
                assert np.isfinite(positions).all() and np.isfinite(normals).all() and np.isfinite(uvs).all()
                assert np.allclose(np.linalg.norm(normals,axis=1),1,atol=1e-4)
                assert len(indices)%3==0 and indices.max()<len(positions)
                triangles=positions[indices].reshape(-1,3,3)
                assert np.all(np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)>1e-8)
        scene=trimesh.load(str(path),force='scene')
        count=sum(len(geom.faces) for geom in scene.geometry.values())
        assert count==manifest['modules'][name]['triangles'] and count<=limit
        for mesh in scene.geometry.values():
            assert np.isfinite(mesh.vertices).all() and np.isfinite(mesh.visual.uv).all()
            assert len(mesh.faces)>0
        lo,hi=np.array(manifest['modules'][name]['bounds_author_z_up'])
        assert np.allclose(scene.bounds,[[lo[0],lo[2],-hi[1]],[hi[0],hi[2],-lo[1]]],atol=1e-4)
        if name=='station_gaslamp':
            assert any(m.name=='lantern' and m.emissiveTexture is not None and any(m.emissiveFactor)
                       for m in gltf.materials)
            assert abs(hi[2]-4.0)<.2
        elif name=='station_bench':
            assert abs((hi[0]-lo[0])-2.1)<.1 and abs(hi[2]-1.0)<.15
        else:
            assert {'clock','sign3'}.issubset({m.name for m in gltf.materials})
            assert 3.0 < hi[2] < 4.2 and lo[2] == 0

if __name__=='__main__':
    test_props()
    print('Furnishing GLBs: geometry, UV, embedded textures, orientation, sizes and lamp emission passed.')
