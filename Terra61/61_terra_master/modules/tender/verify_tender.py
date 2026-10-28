#!/usr/bin/env python3
"""Verify GLB bounds, track fit, coupling face, texture embedding and preview."""
from pathlib import Path
from io import BytesIO
import numpy as np
from PIL import Image
from pygltflib import GLTF2
import trimesh

p=Path(__file__).resolve().parent
file=p/'coal_tender.glb'; s=trimesh.load(file,force='scene',process=False); g=GLTF2().load_binary(str(file))
assert np.allclose(s.bounds[0],[-1.35,0,0],atol=1e-5),s.bounds
assert np.allclose(s.bounds[1,[0,2]],[1.35,6.9],atol=1e-5),s.bounds
assert s.extents[0]<=3 and 6<=s.extents[2]<=7
count=sum(len(m.faces) for m in s.geometry.values());assert count==7488,count
assert len(s.geometry['Coal_Surface_Low_Poly'].faces)==512
for name,mesh in s.geometry.items():
    assert np.isfinite(mesh.vertices).all(),name
    assert (mesh.area_faces>1e-12).all(),name
    assert mesh.visual.uv.shape==(len(mesh.vertices),2),name
    assert np.isfinite(mesh.visual.uv).all(),name
assert len(g.images)==4 and all(i.uri is None and i.bufferView is not None for i in g.images)
assert all(b.uri is None for b in g.buffers)
blob=g.binary_blob()
textures={'AI-derived aged cast iron':'aged_iron.png','AI-derived riveted tender panels':'riveted_side.png','AI-derived coal facets':'coal.png','Procedural worn red oxide paint':'red_oxide.png'}
matched=set()
for mat in g.materials:
    if mat.name not in textures:continue
    tex=g.textures[mat.pbrMetallicRoughness.baseColorTexture.index]
    image=g.images[tex.source];view=g.bufferViews[image.bufferView]
    actual=np.asarray(Image.open(BytesIO(blob[view.byteOffset:view.byteOffset+view.byteLength])).convert('RGB'))
    expected=np.asarray(Image.open(p/'textures'/textures[mat.name]).convert('RGB'))
    assert np.array_equal(actual,expected),mat.name
    matched.add(mat.name);print('embedded texture verified:',mat.name)
assert matched==set(textures)
wheels=s.geometry['Wheel_Treads'].vertices
for z in (1.50,2.55,4.45,5.50):
    v=wheels[(np.abs(wheels[:,1])<1e-6)&(np.abs(wheels[:,2]-z)<1e-5)]
    xs=np.unique(np.round(v[:,0],4))
    assert np.allclose(xs,[-.8165,-.6865,.6865,.8165]),(z,xs)
    assert np.isclose((xs[0]+xs[1])/2,-.7515) and np.isclose((xs[2]+xs[3])/2,.7515)
    print('wheel contact verified at z:',z,'tread centers x=+/-0.7515 m')
c=s.geometry['Chassis_Spokes_Couplings'].vertices
face=c[np.abs(c[:,2])<1e-6]
assert len(face)>0 and np.allclose([face[:,0].min(),face[:,0].max(),face[:,1].min(),face[:,1].max()],[-.12,.12,1.20,1.40],atol=1e-5)
loco_file=p.parent/'locomotive'/'steam_locomotive.glb'
if loco_file.exists():
    loco=trimesh.load(loco_file,force='scene',process=False)
    c2=loco.geometry['Chassis_And_Axles'].vertices
    end=c2[np.abs(c2[:,2]-12.95)<1e-5]
    assert np.allclose([end[:,0].min(),end[:,0].max(),end[:,1].min(),end[:,1].max()],[-.12,.12,1.20,1.40],atol=1e-5)
    print('locomotive rear and tender front coupler faces match at z offset 12.95 m')
for name in ('preview_three_quarter.png','preview_side.png','preview_rear.png'):
    im=Image.open(p/name);assert im.width>=1500 and im.height>=1100
print('PASS: bounds',s.bounds.tolist(),'triangles',count,'meshes',len(s.geometry))
print('PASS: 4 paired axles contact local y=0 and align with both rail heads')
print('PASS: coal surface is 512 triangles and all four textures are embedded')
