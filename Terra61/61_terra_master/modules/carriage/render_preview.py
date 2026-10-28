#!/usr/bin/env python3
"""Render actual carriage GLB geometry and embedded textures in a CPU preview."""
from pathlib import Path
import io,os,struct,subprocess,tempfile
import numpy as np
from PIL import Image
from pygltflib import GLTF2
P=Path(__file__).resolve().parent

def accessor(gltf,index,n,dtype):
 a=gltf.accessors[index];v=gltf.bufferViews[a.bufferView]
 return np.frombuffer(gltf.binary_blob(),dtype=dtype,count=a.count*n,offset=(v.byteOffset or 0)+(a.byteOffset or 0)).reshape(-1,n).copy()

def main():
 g=GLTF2().load(str(P/'victorian_carriage.glb'));triangles=[];textures=[]
 for p in g.meshes[0].primitives:
  m=g.materials[p.material];tex=g.textures[m.pbrMetallicRoughness.baseColorTexture.index];im=g.images[tex.source];v=g.bufferViews[im.bufferView];raw=g.binary_blob()[v.byteOffset:v.byteOffset+v.byteLength]
  img=Image.open(io.BytesIO(raw)).convert('RGBA');flags=(1 if m.alphaMode=='BLEND' else 0)|(2 if m.emissiveFactor and max(m.emissiveFactor)>0 else 0);textures.append((img,flags))
  pos=accessor(g,p.attributes.POSITION,3,'<f4');uv=accessor(g,p.attributes.TEXCOORD_0,2,'<f4');idx=accessor(g,p.indices,1,'<u4').reshape(-1,3)
  triangles.append((np.column_stack((pos,uv))[idx],p.material))
 with tempfile.TemporaryDirectory(prefix='carriage_render_') as t:
  tmp=Path(t);exe=tmp/'render';subprocess.run(['g++','-O3','-std=c++17',str(P/'carriage_renderer.cpp'),'-o',str(exe)],check=True)
  rec=[]
  for data,mat in triangles:
   for face in data:rec.append(struct.pack('<I15f',mat,*face.reshape(-1)))
  inp=tmp/'scene.bin'
  with inp.open('wb') as f:
   f.write(struct.pack('<4sIIII',b'SHED',1920,1440,len(textures),len(rec)))
   for img,flags in textures:f.write(struct.pack('<III',img.width,img.height,flags));f.write(img.tobytes())
   for x in rec:f.write(x)
  views=[('carriage_hero_preview.png',(20,8,-12),(0,2.2,7.6),26),
         ('carriage_side_preview.png',(27,4.6,7.6),(0,2.05,7.6),27),
         ('carriage_end_preview.png',(8,4.5,-9),(0,2,5.8),31)]
  for name,eye,target,fov in views:
   ppm=tmp/'preview.ppm';subprocess.run([str(exe),str(inp),str(ppm),*[str(a) for a in (*eye,*target,fov,1)]],check=True)
   output=tmp/name
   with Image.open(ppm) as im: im.resize((1600,1200),Image.Resampling.LANCZOS).save(output,optimize=True)
   with Image.open(output) as im:im.load()
   os.replace(output,P/name);print('Saved',name)
if __name__=='__main__':main()
