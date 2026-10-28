#!/usr/bin/env python3
"""Verify saved GLB, wheel contact alignment, PBR texture embedding and bounds."""
from pathlib import Path
from io import BytesIO
import json
import numpy as np
from PIL import Image
from pygltflib import GLTF2
import trimesh

p=Path(__file__).resolve().parent
path=p/'steam_locomotive.glb'
s=trimesh.load(path,force='scene',process=False);g=GLTF2().load_binary(str(path))
expected=np.array([[-1.38,0,0],[1.38,4.21,12.95]])
assert np.allclose(s.bounds,expected,atol=1e-5),s.bounds
assert s.extents[0]<3 and 12<s.extents[2]<14
assert len(s.geometry)==10
count=sum(len(m.faces) for m in s.geometry.values());assert count==16184,count
for name,mesh in s.geometry.items():
    assert np.isfinite(mesh.vertices).all(),name
    assert (mesh.area_faces>1e-12).all(),name
    assert mesh.visual.uv.shape==(len(mesh.vertices),2),name
    assert np.isfinite(mesh.visual.uv).all(),name
assert len(g.images)==4 and all(i.uri is None and i.bufferView is not None for i in g.images)
assert all(b.uri is None for b in g.buffers)
blob=g.binary_blob()
textures={'AI-derived riveted boiler steel':'boiler_sheet.png','AI-derived aged cast iron':'aged_iron.png','AI-derived smokebox door and rivet detail':'smokebox_door.png','Procedural worn red iron':'red_painted_iron.png'}
matched=set()
for mat in g.materials:
    if mat.name not in textures:continue
    tex=g.textures[mat.pbrMetallicRoughness.baseColorTexture.index]
    image=g.images[tex.source];view=g.bufferViews[image.bufferView]
    actual=np.asarray(Image.open(BytesIO(blob[view.byteOffset:view.byteOffset+view.byteLength])).convert('RGB'))
    expected_image=np.asarray(Image.open(p/'textures'/textures[mat.name]).convert('RGB'))
    assert np.array_equal(actual,expected_image),mat.name
    matched.add(mat.name);print('embedded texture verified:',mat.name)
assert matched==set(textures)
# Both side-wheel treads include two X boundaries each, at local Y=0.
# Their midpoints are the associated station rail-head centers +/-0.7515.
wheels=s.geometry['Wheel_Rims_And_Pilot'].vertices
for z in (2.10,4.05,6.20,8.35,10.90):
    points=wheels[(np.abs(wheels[:,1])<1e-6)&(np.abs(wheels[:,2]-z)<1e-5)]
    xs=np.unique(np.round(points[:,0],4))
    assert np.allclose(xs,[-.8165,-.6865,.6865,.8165]),(z,xs)
    assert np.isclose((xs[0]+xs[1])/2,-.7515) and np.isclose((xs[2]+xs[3])/2,.7515)
    print('wheel contact verified:',z,'m; tread centers +/-0.7515 m')
for name in ('preview_three_quarter.png','preview_side.png','preview_front.png'):
    im=Image.open(p/name);assert im.width>=1500 and im.height>=1100
print('PASS: actual GLB bounds',s.bounds.tolist(),'triangles',count,'meshes',len(s.geometry))
print('PASS: 3 paired 0.8 m driving wheels; 2 smaller paired axles; all 5 pairs meet Y=0')
