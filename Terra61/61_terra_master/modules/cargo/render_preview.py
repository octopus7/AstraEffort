#!/usr/bin/env python3
"""Render actual GLB geometry and embedded image maps in a small CPU renderer."""
from pathlib import Path
import io,os,struct,subprocess,tempfile
import numpy as np
from PIL import Image
from pygltflib import GLTF2
P=Path(__file__).resolve().parent

def accessor(g,i,n,dtype):
 a=g.accessors[i];v=g.bufferViews[a.bufferView]
 return np.frombuffer(g.binary_blob(),dtype=dtype,count=a.count*n,offset=(v.byteOffset or 0)+(a.byteOffset or 0)).reshape(-1,n).copy()

def scene(path):
 g=GLTF2().load(str(path));textures=[];records=[]
 for prim in g.meshes[0].primitives:
  mat=g.materials[prim.material];tex=g.textures[mat.pbrMetallicRoughness.baseColorTexture.index];im=g.images[tex.source];v=g.bufferViews[im.bufferView];raw=g.binary_blob()[v.byteOffset:v.byteOffset+v.byteLength]
  img=Image.open(io.BytesIO(raw)).convert('RGBA');flags=(1 if mat.alphaMode=='BLEND' else 0)|(2 if mat.emissiveFactor and max(mat.emissiveFactor)>0 else 0);textures.append((img,flags))
  pos=accessor(g,prim.attributes.POSITION,3,'<f4');uv=accessor(g,prim.attributes.TEXCOORD_0,2,'<f4');idx=accessor(g,prim.indices,1,'<u4').reshape(-1,3)
  for face in np.column_stack((pos,uv))[idx]:records.append(struct.pack('<I15f',prim.material,*face.reshape(-1)))
 return textures,records

def main():
 views=[('platform_sign','platform_sign_preview.png',(3.5,2.5,5.5),(.4,1.55,0),34),
        ('platform_sign','platform_sign_back_preview.png',(-3.5,2.4,-5.5),(.4,1.55,0),35),
        ('cargo_crate','wooden_crate_preview.png',(2.4,1.9,3.2),(0,.55,0),25),
        ('cargo_barrel','wooden_barrel_preview.png',(2.4,1.8,3.1),(0,.53,0),23)]
 with tempfile.TemporaryDirectory(prefix='prop_render_') as t:
  tmp=Path(t);exe=tmp/'render';subprocess.run(['g++','-O3','-std=c++17',str(P/'prop_renderer.cpp'),'-o',str(exe)],check=True)
  for glb,out,eye,target,fov in views:
   textures,records=scene(P/(glb+'.glb'));inp=tmp/'scene.bin'
   with inp.open('wb') as f:
    f.write(struct.pack('<4sIIII',b'SHED',1440,1440,len(textures),len(records)))
    for img,flags in textures:f.write(struct.pack('<III',img.width,img.height,flags));f.write(img.tobytes())
    for r in records:f.write(r)
   ppm=tmp/'render.ppm';subprocess.run([str(exe),str(inp),str(ppm),*[str(a) for a in (*eye,*target,fov,1)]],check=True)
   output=tmp/out
   with Image.open(ppm) as im:im.resize((1280,1280),Image.Resampling.LANCZOS).save(output,optimize=True)
   with Image.open(output) as im:im.load()
   os.replace(output,P/out);print('Saved',out)
if __name__=='__main__':main()
