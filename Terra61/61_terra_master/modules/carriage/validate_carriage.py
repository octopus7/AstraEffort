#!/usr/bin/env python3
"""Independent checks on the actual exported carriage GLB and images."""
from pathlib import Path
from hashlib import sha256
import io,json
import numpy as np
from PIL import Image
import trimesh
from pygltflib import GLTF2
from pygltflib.validator import validate
P=Path(__file__).resolve().parent

def data(g,i,n,dtype):
 a=g.accessors[i];v=g.bufferViews[a.bufferView]
 return np.frombuffer(g.binary_blob(),dtype=dtype,count=a.count*n,offset=(v.byteOffset or 0)+(a.byteOffset or 0)).reshape(-1,n)

def main():
 p=P/'victorian_carriage.glb';g=GLTF2().load(str(p));assert not validate(g)
 scene=trimesh.load(p,force='scene',process=False)
 vertices=[];faces=0;bad=0;by_material={};wheel_z=None
 for prim in g.meshes[0].primitives:
  mat=g.materials[prim.material].name;pos=data(g,prim.attributes.POSITION,3,'<f4');norm=data(g,prim.attributes.NORMAL,3,'<f4');uv=data(g,prim.attributes.TEXCOORD_0,2,'<f4');inds=data(g,prim.indices,1,'<u4').reshape(-1,3)
  assert len(pos)==len(norm)==len(uv) and np.isfinite(pos).all() and np.isfinite(norm).all() and np.isfinite(uv).all() and int(inds.max())<len(pos)
  tri=pos[inds];area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
  bad+=int((area<1e-9).sum());vertices.append(pos);faces+=len(inds);by_material[mat]=len(inds)
  if mat=='wheel_steel':wheel_z=sorted(set(np.round(pos[np.abs(pos[:,1])<1e-5,2],2).tolist()))
 assert bad==0,(bad,'zero-area faces')
 assert faces==sum(len(m.faces) for m in scene.geometry.values())
 points=np.concatenate(vertices);bounds=np.stack((points.min(axis=0),points.max(axis=0)))
 assert np.allclose(scene.bounds,bounds,atol=1e-5)
 assert bounds[1,0]-bounds[0,0]<=3.0 and abs(bounds[0,1])<1e-5 and bounds[1,1]+.24<=4.5
 assert bounds[0,2]>=-1e-5 and 14<=bounds[1,2]<=16
 assert np.allclose(wheel_z,[2.6,4.2,11,12.6],atol=.01),wheel_z
 for im in g.images:
  assert im.bufferView is not None and im.mimeType=='image/png';v=g.bufferViews[im.bufferView];raw=g.binary_blob()[v.byteOffset:v.byteOffset+v.byteLength]
  Image.open(io.BytesIO(raw)).verify()
  if im.name=='iron_cast_ai':
   assert sha256(raw).digest()==sha256((P/'ai_aged_cast_iron.png').read_bytes()).digest()
   mid=next(i for i,m in enumerate(g.materials) if m.name=='iron_cast_ai')
   assert any(pr.material==mid and pr.attributes.TEXCOORD_0 is not None for pr in g.meshes[0].primitives)
 glass=next(m for m in g.materials if m.name=='window_glass');assert glass.alphaMode=='BLEND' and glass.doubleSided
 im=g.images[g.textures[glass.pbrMetallicRoughness.baseColorTexture.index].source];v=g.bufferViews[im.bufferView]
 image=Image.open(io.BytesIO(g.binary_blob()[v.byteOffset:v.byteOffset+v.byteLength]));assert image.mode=='RGBA' and 0<image.getextrema()[3][0]<255
 pngs={}
 for imagepath in sorted(P.glob('*.png')):
  with Image.open(imagepath) as image:image.load();pngs[imagepath.name]=list(image.size)
 result={'bounds':bounds.tolist(),'dimensions':(bounds[1]-bounds[0]).tolist(),'scene_y_max_at_requested_y_offset':float(bounds[1,1]+.24),'triangle_total':faces,
  'triangles_by_material':by_material,'zero_area_faces':bad,'wheel_contact_z':wheel_z,'trimesh_geometries':len(scene.geometry),
  'pygltflib_validation':'passed','embedded_ai_texture_sha256':sha256((P/'ai_aged_cast_iron.png').read_bytes()).hexdigest(),'pngs_decoded':pngs}
 print(json.dumps(result,indent=2));(P/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
