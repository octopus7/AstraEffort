#!/usr/bin/env python3
"""Inspect the three exported GLBs, textures, ground pivots and preview images."""
from pathlib import Path
from hashlib import sha256
import io,json
import numpy as np
from PIL import Image
from pygltflib import GLTF2
from pygltflib.validator import validate
import trimesh
P=Path(__file__).resolve().parent

def arr(g,i,n,dtype):
 a=g.accessors[i];v=g.bufferViews[a.bufferView]
 return np.frombuffer(g.binary_blob(),dtype=dtype,count=a.count*n,offset=(v.byteOffset or 0)+(a.byteOffset or 0)).reshape(-1,n)

def check(name):
 gltf=GLTF2().load(str(P/name));assert not validate(gltf);scene=trimesh.load(P/name,force='scene',process=False)
 vertices=[];triangles=0;degenerate=0;by_mat={}
 for prim in gltf.meshes[0].primitives:
  mat=gltf.materials[prim.material].name;pos=arr(gltf,prim.attributes.POSITION,3,'<f4');normal=arr(gltf,prim.attributes.NORMAL,3,'<f4');uv=arr(gltf,prim.attributes.TEXCOORD_0,2,'<f4');indices=arr(gltf,prim.indices,1,'<u4').reshape(-1,3)
  assert len(pos)==len(normal)==len(uv) and np.isfinite(pos).all() and np.isfinite(normal).all() and np.isfinite(uv).all() and int(indices.max())<len(pos)
  tris=pos[indices];area=np.linalg.norm(np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]),axis=1)*.5;degenerate+=int((area<1e-10).sum())
  vertices.append(pos);triangles+=len(indices);by_mat[mat]=len(indices)
  if mat=='platform_3':
   assert len(indices)==4 and set(np.sign(normal[:,2]))=={-1.,1.},'Sign faces must face opposite directions'
   assert np.allclose(uv.min(axis=0),[0,0]) and np.allclose(uv.max(axis=0),[1,1])
 assert degenerate==0,(name,degenerate)
 assert triangles==sum(len(m.faces) for m in scene.geometry.values())
 points=np.concatenate(vertices);bounds=np.stack((points.min(axis=0),points.max(axis=0)))
 assert abs(bounds[0,1])<1e-6 and np.allclose(bounds,scene.bounds,atol=1e-5)
 embedded=[]
 for im in gltf.images:
  assert im.bufferView is not None and im.mimeType=='image/png';v=gltf.bufferViews[im.bufferView];raw=gltf.binary_blob()[v.byteOffset:v.byteOffset+v.byteLength];Image.open(io.BytesIO(raw)).verify();embedded.append(im.name)
  if im.name=='platform_3':assert sha256(raw).digest()==sha256((P/'platform_3.png').read_bytes()).digest()
 return {'file':name,'bounds':bounds.tolist(),'dimensions':(bounds[1]-bounds[0]).tolist(),'triangles':triangles,'by_material':by_mat,'zero_area_faces':degenerate,'embedded_textures':embedded,'trimesh_geometries':len(scene.geometry),'pygltflib_validation':'passed'}

if __name__=='__main__':
 results=[check(name) for name in ('platform_sign.glb','cargo_crate.glb','cargo_barrel.glb')]
 images={}
 for imagepath in sorted(P.glob('*.png')):
  with Image.open(imagepath) as im:im.load();images[imagepath.name]=list(im.size)
 output={'assets':results,'pngs_decoded':images};print(json.dumps(output,indent=2));(P/'validation.json').write_text(json.dumps(output,indent=2)+'\n')
