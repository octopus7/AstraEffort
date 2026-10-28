"""Check the steam locomotive and tender export contracts."""
from pathlib import Path
import io
import json
import math
import os
import unittest

import numpy as np
from PIL import Image
from pygltflib import GLTF2

HERE = Path(os.environ.get('LOCOMOTIVE_OUTPUT', Path(__file__).resolve().parent))
DTYPES = {5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}
COMPONENTS = {'SCALAR':1,'VEC2':2,'VEC3':3}


def accessor(gl, idx):
    a=gl.accessors[idx]; v=gl.bufferViews[a.bufferView]
    return np.frombuffer(gl.binary_blob(),dtype=DTYPES[a.componentType],
                         count=a.count*COMPONENTS[a.type],
                         offset=(v.byteOffset or 0)+(a.byteOffset or 0)).reshape(a.count,-1)


class RollingStockContract(unittest.TestCase):
    def test_expected_exports_exist(self):
        for f in ('manifest.json','locomotive.glb','tender.glb'):
            self.assertTrue((HERE/f).is_file(),f'{f} missing')

    def test_geometry_placement_gauge_and_materials(self):
        manifest=json.loads((HERE/'manifest.json').read_text())
        self.assertEqual(manifest['wheel_contact_z'],0)
        self.assertEqual(manifest['rail_placement_z'],0.22)
        self.assertAlmostEqual(manifest['wheel_center_gauge'],1.435)
        for name,length,budget in [('locomotive',10,6501),('tender',5,1701)]:
            with self.subTest(module=name):
                gl=GLTF2().load(str(HERE/(name+'.glb')))
                root=gl.nodes[gl.scenes[gl.scene].nodes[0]]
                self.assertTrue(np.allclose(root.rotation,[-math.sqrt(.5),0,0,math.sqrt(.5)]))
                all_pos=[]; tris=0
                for mesh in gl.meshes:
                    for prim in mesh.primitives:
                        p=accessor(gl,prim.attributes.POSITION); n=accessor(gl,prim.attributes.NORMAL)
                        uv=accessor(gl,prim.attributes.TEXCOORD_0); idx=accessor(gl,prim.indices).ravel()
                        self.assertEqual(len(p),len(uv)); self.assertEqual(len(p),len(n))
                        self.assertTrue(np.isfinite(p).all() and np.isfinite(n).all() and np.isfinite(uv).all())
                        self.assertLess(idx.max(),len(p)); self.assertEqual(len(idx)%3,0)
                        faces=idx.reshape(-1,3)
                        edge1=p[faces[:,1]]-p[faces[:,0]]; edge2=p[faces[:,2]]-p[faces[:,0]]
                        cross=np.cross(edge1,edge2)
                        self.assertTrue((np.linalg.norm(cross,axis=1)>1e-8).all())
                        self.assertTrue(((cross*n[faces[:,0]]).sum(axis=1)>0).all())
                        d1=uv[faces[:,1]]-uv[faces[:,0]]; d2=uv[faces[:,2]]-uv[faces[:,0]]
                        self.assertTrue((np.abs(d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0])>1e-10).all())
                        material=gl.materials[prim.material]
                        self.assertIsNotNone(material.pbrMetallicRoughness.baseColorTexture)
                        self.assertIsNotNone(material.pbrMetallicRoughness.metallicRoughnessTexture)
                        self.assertIsNotNone(material.normalTexture)
                        all_pos.append(p); tris+=len(idx)//3
                p=np.concatenate(all_pos); bounds=np.stack([p.min(0),p.max(0)])
                self.assertTrue(np.allclose(bounds[:,0],[-1.4,1.4],atol=1e-5))
                self.assertTrue(np.allclose(bounds[:,1],[0,length],atol=1e-5))
                self.assertAlmostEqual(float(bounds[0,2]),0,places=5)
                if name=='locomotive': self.assertAlmostEqual(float(bounds[1,2]),4.5,places=5)
                self.assertEqual(tris,manifest['modules'][name]['triangle_count'])
                self.assertLess(tris,budget)
                for img in gl.images:
                    self.assertIsNone(img.uri); self.assertIsNotNone(img.bufferView)
                    v=gl.bufferViews[img.bufferView]
                    data=gl.binary_blob()[v.byteOffset:v.byteOffset+v.byteLength]
                    with Image.open(io.BytesIO(data)) as pic: pic.verify()
                pairs=3 if name=='locomotive' else 2
                prefix='driving_wheel' if name=='locomotive' else 'tender_wheel'
                for i in range(1,pairs+1):
                    xs=[]
                    for side in ('L','R'):
                        mesh=next(m for m in gl.meshes if m.name==f'{prefix}_{side}_{i}')
                        positions=np.concatenate([accessor(gl,q.attributes.POSITION) for q in mesh.primitives])
                        xs.append((float(positions[:,0].min())+float(positions[:,0].max()))/2)
                        self.assertAlmostEqual(float(positions[:,2].min()),0,places=5)
                    self.assertAlmostEqual(xs[1]-xs[0],1.435,places=5)
                if name=='locomotive':
                    leading=[]
                    for side in ('L','R'):
                        mesh=next(m for m in gl.meshes if m.name==f'leading_wheel_{side}')
                        positions=np.concatenate([accessor(gl,q.attributes.POSITION) for q in mesh.primitives])
                        leading.append((float(positions[:,0].min())+float(positions[:,0].max()))/2)
                        self.assertAlmostEqual(float(positions[:,2].min()),0,places=5)
                    self.assertAlmostEqual(leading[1]-leading[0],1.435,places=5)

    def test_locomotive_wheels_are_unobstructed_and_buffers_project(self):
        gl=GLTF2().load(str(HERE/'locomotive.glb'))
        def mesh_positions(name):
            mesh=next(m for m in gl.meshes if m.name==name)
            return np.concatenate([accessor(gl,p.attributes.POSITION) for p in mesh.primitives])
        chassis=mesh_positions('inner_chassis')
        self.assertTrue(np.allclose([chassis[:,0].min(),chassis[:,0].max()],[-.42,.42],atol=1e-5))
        beam=mesh_positions('front_buffer_beam')
        self.assertTrue(np.allclose([beam[:,1].min(),beam[:,1].max()],[.22,.45],atol=1e-5))
        buffers=mesh_positions('front_buffers')
        self.assertAlmostEqual(float(buffers[:,1].min()),0,places=5)
        self.assertLess(float(buffers[:,1].min()),float(beam[:,1].min()))
        lamp=next(m for m in gl.meshes if m.name=='front_headlamp')
        p=np.concatenate([accessor(gl,q.attributes.POSITION) for q in lamp.primitives])
        self.assertGreater(float(p[:,2].max()),3.7)
        self.assertTrue(any(gl.materials[q.material].name=='lamp_amber' for q in lamp.primitives))
        for name in ('locomotive_frame_and_footplate','inner_chassis','cab_lower_body','chimney'):
            mesh=next(m for m in gl.meshes if m.name==name)
            self.assertTrue(any(gl.materials[p.material].name=='loco_iron' for p in mesh.primitives))


if __name__=='__main__': unittest.main()
