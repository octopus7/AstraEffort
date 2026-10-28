#!/usr/bin/env python3
"""Check saved GLB interfaces, embedded texture integrity, and triangle budget."""
from pathlib import Path
from io import BytesIO
import json
import numpy as np
from PIL import Image
from pygltflib import GLTF2
import trimesh

p=Path(__file__).resolve().parent
file=p/'platform_track_bay.glb'
g=GLTF2().load_binary(str(file))
s=trimesh.load(file,force='scene',process=False)
assert np.allclose(s.bounds,[[-10,0,0],[10,.9,6]],atol=1e-6), s.bounds
assert len(s.geometry)==11
count=sum(len(m.faces) for m in s.geometry.values())
assert count==6810
for name,mesh in s.geometry.items():
    assert np.isfinite(mesh.vertices).all(), name
    assert (mesh.area_faces>1e-12).all(), name
    assert np.isfinite(mesh.visual.uv).all(), name
    assert mesh.visual.uv.shape==(len(mesh.vertices),2), name
assert len(g.images)==5
assert all(image.uri is None and image.bufferView is not None for image in g.images)
assert all(buffer.uri is None for buffer in g.buffers)
blob=g.binary_blob()
checks={'Worn limestone paving':'paving.png','Dark broken stone ballast':'ballast.png','Weathered ashlar masonry':'ashlar.png','Limestone coping blocks':'coping.png','Weathered hardwood sleepers':'wood.png'}
for mat in g.materials:
    if mat.name not in checks: continue
    texture_index=mat.pbrMetallicRoughness.baseColorTexture.index
    img=g.images[g.textures[texture_index].source]; view=g.bufferViews[img.bufferView]
    embedded=np.asarray(Image.open(BytesIO(blob[view.byteOffset:view.byteOffset+view.byteLength])).convert('RGB'))
    expected=np.asarray(Image.open(p/'textures'/checks[mat.name]).convert('RGB'))
    assert np.array_equal(embedded,expected),mat.name
    print('embedded texture verified:',mat.name,embedded.shape)
for name in ('paving','ballast'):
    pixels=np.asarray(Image.open(p/'textures'/f'{name}.png').convert('RGB'))
    assert np.array_equal(pixels[0],pixels[-1]),name+' z-seam'
    print('texture repeat verified:',name,'first and last rows identical')
rail=s.geometry['Tracks_Steel_Rails']
xyz=rail.vertices
r=xyz[np.isclose(xyz[:,1],.210,atol=1e-6)]
xvals=np.unique(np.round(r[:,0],4))
expected=np.array([-4.7855,-4.7175,-3.2825,-3.2145,3.2145,3.2825,4.7175,4.7855])
assert np.allclose(xvals,expected,atol=1e-4),(xvals,expected)
assert np.isclose(xvals[2]-xvals[1],1.435,atol=1e-4)
assert np.isclose(xvals[6]-xvals[5],1.435,atol=1e-4)
assert np.allclose(rail.bounds[:,2],[0,6])
wood=s.geometry['Tracks_Hardwood_Sleepers']
v=wood.vertices.reshape((-1,24,3))
centers=(v[:,:,2].min(axis=1)+v[:,:,2].max(axis=1))/2
assert np.allclose(centers[:10],np.arange(.3,6,.6),atol=1e-5)
assert np.allclose(centers[10:],np.arange(.3,6,.6),atol=1e-5)
for name in ('Ballast_Stones_Charcoal','Ballast_Stones_Pale','Ballast_Stones_Warm'):
    xyz=s.geometry[name].vertices
    assert ((xyz[:,0]>=-6)&(xyz[:,0]<=-2)|(xyz[:,0]>=2)&(xyz[:,0]<=6)).all()
    assert ((xyz[:,2]>=0)&(xyz[:,2]<=6)).all()
for preview in ('preview_overview.png','preview_track_detail.png'):
    im=Image.open(p/preview); assert im.width>=1500 and im.height>=1000
print('PASS: bounds',s.bounds.tolist(),'triangles',count,'nodes',len(s.geometry))
print('PASS: standard gauge 1.435 m for both tracks; rails z=0..6 m')
print('PASS: sleepers repeat every 0.6 m, including between bays')
