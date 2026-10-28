"""Contract checks for the cart, crate and barrel GLBs."""
from pathlib import Path
import io
import json
import math
import unittest
import numpy as np
from PIL import Image
from pygltflib import GLTF2

HERE=Path(__file__).resolve().parent
EXPECT={'luggage_cart':([[-.6,0,0],[.6,2,1.5]],1700),
        'crate':([[-.4,0,0],[.4,.8,.8]],100),
        'barrel':([[-.325,0,0],[.325,.65,.9]],250)}
TYPES={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}
SIZES={'SCALAR':1,'VEC2':2,'VEC3':3}


def accessor(gl, idx):
    a=gl.accessors[idx]; v=gl.bufferViews[a.bufferView]
    return np.frombuffer(gl.binary_blob(),dtype=TYPES[a.componentType],count=a.count*SIZES[a.type],
                         offset=(v.byteOffset or 0)+(a.byteOffset or 0)).reshape(a.count,-1)


class FreightPropContract(unittest.TestCase):
    def test_exports_exist(self):
        for f in ['manifest.json']+[n+'.glb' for n in EXPECT]:
            self.assertTrue((HERE/f).is_file(),f'{f} is missing')

    def test_dimensions_geometry_and_materials(self):
        manifest=json.loads((HERE/'manifest.json').read_text())
        for name,(bounds,budget) in EXPECT.items():
            with self.subTest(name=name):
                gl=GLTF2().load(str(HERE/(name+'.glb')))
                root=gl.nodes[gl.scenes[gl.scene].nodes[0]]
                self.assertTrue(np.allclose(root.rotation,[-math.sqrt(.5),0,0,math.sqrt(.5)]))
                all_pos=[]; tris=0
                for mesh in gl.meshes:
                    for prim in mesh.primitives:
                        p=accessor(gl,prim.attributes.POSITION); n=accessor(gl,prim.attributes.NORMAL)
                        uv=accessor(gl,prim.attributes.TEXCOORD_0); idx=accessor(gl,prim.indices).reshape(-1)
                        self.assertEqual(len(p),len(uv)); self.assertEqual(len(p),len(n))
                        self.assertTrue(np.isfinite(p).all() and np.isfinite(n).all() and np.isfinite(uv).all())
                        self.assertLess(idx.max(),len(p)); self.assertEqual(len(idx)%3,0)
                        f=idx.reshape(-1,3); e1=p[f[:,1]]-p[f[:,0]]; e2=p[f[:,2]]-p[f[:,0]]
                        cross=np.cross(e1,e2)
                        self.assertTrue((np.linalg.norm(cross,axis=1)>1e-9).all())
                        self.assertTrue(((cross*n[f[:,0]]).sum(axis=1)>0).all())
                        d1=uv[f[:,1]]-uv[f[:,0]]; d2=uv[f[:,2]]-uv[f[:,0]]
                        self.assertTrue((np.abs(d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0])>1e-10).all())
                        material=gl.materials[prim.material]
                        self.assertIsNotNone(material.pbrMetallicRoughness.baseColorTexture)
                        self.assertIsNotNone(material.pbrMetallicRoughness.metallicRoughnessTexture)
                        self.assertIsNotNone(material.normalTexture)
                        all_pos.append(p); tris+=len(idx)//3
                p=np.concatenate(all_pos); actual=np.stack([p.min(0),p.max(0)])
                self.assertTrue(np.allclose(actual,bounds,atol=1e-5),str(actual))
                self.assertLess(tris,budget); self.assertEqual(tris,manifest['modules'][name]['triangle_count'])
                for image in gl.images:
                    self.assertIsNone(image.uri); self.assertIsNotNone(image.bufferView)
                    v=gl.bufferViews[image.bufferView]
                    with Image.open(io.BytesIO(gl.binary_blob()[v.byteOffset:v.byteOffset+v.byteLength])) as im:
                        im.verify()
                if name=='luggage_cart':
                    names={m.name for m in gl.meshes}
                    self.assertTrue({'trunk_blue','trunk_brown','trunk_tan'}.issubset(names))
                    self.assertEqual(sum(n.startswith('cart_wheel_') for n in names),4)
                    for mesh in (m for m in gl.meshes if m.name.startswith('cart_wheel_')):
                        points=np.concatenate([accessor(gl,q.attributes.POSITION) for q in mesh.primitives])
                        self.assertAlmostEqual(float(points[:,2].min()),0,places=5)
                    image_names={im.name for im in gl.images}
                    self.assertTrue({'case_blue_basecolor.png','case_brown_basecolor.png','case_tan_basecolor.png'}.issubset(image_names))
                    self.assertTrue({'case_blue_top_basecolor.png','case_brown_top_basecolor.png','case_tan_top_basecolor.png'}.issubset(image_names))

if __name__=='__main__': unittest.main()
