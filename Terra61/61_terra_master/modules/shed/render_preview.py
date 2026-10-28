#!/usr/bin/env python3
"""Render the actual delivered GLB via a small CPU z-buffer; no Blender needed."""
from pathlib import Path
import io, os, struct, subprocess, tempfile
import numpy as np
from PIL import Image
from pygltflib import GLTF2
OUT=Path(__file__).resolve().parent

def load_access(gltf, idx, shape, typ):
    acc=gltf.accessors[idx];view=gltf.bufferViews[acc.bufferView];offset=(view.byteOffset or 0)+(acc.byteOffset or 0)
    raw=gltf.binary_blob();return np.frombuffer(raw,dtype=typ,count=acc.count*shape,offset=offset).reshape((-1,shape)).copy()

def load_glb(path,material_offset=0):
    gltf=GLTF2().load(str(path))
    triangles=[];textures=[]
    for prim in gltf.meshes[0].primitives:
        mat=gltf.materials[prim.material];tex=gltf.textures[mat.pbrMetallicRoughness.baseColorTexture.index];img=gltf.images[tex.source];view=gltf.bufferViews[img.bufferView];raw=gltf.binary_blob()[view.byteOffset:view.byteOffset+view.byteLength]
        rgba=Image.open(io.BytesIO(raw)).convert('RGBA');flags=(1 if mat.alphaMode=='BLEND' else 0)|(2 if mat.emissiveFactor and max(mat.emissiveFactor)>0 else 0)
        textures.append((rgba,flags))
        pos=load_access(gltf,prim.attributes.POSITION,3,'<f4');uv=load_access(gltf,prim.attributes.TEXCOORD_0,2,'<f4');idx=load_access(gltf,prim.indices,1,'<u4').reshape(-1,3)
        triangles.append((np.column_stack((pos,uv))[idx],prim.material+material_offset))
    return triangles,textures

def main():
    triangles,textures=load_glb(OUT/'train_shed_bay.glb')
    end_triangles,end_textures=load_glb(OUT/'train_shed_end_frame.glb',len(textures))
    textures.extend(end_textures)
    with tempfile.TemporaryDirectory(prefix='shed_render_') as tmp:
        tmp=Path(tmp);exe=tmp/'render';subprocess.run(['g++','-O3','-std=c++17',str(OUT/'shed_renderer.cpp'),'-o',str(exe)],check=True)
        views=[('shed_single_preview.png',1,(27,16,-26),(0,6.6,3),30),
               ('shed_repeat_preview.png',3,(31,15,-31),(0,6.1,8.8),31),
               ('shed_interior_preview.png',3,(0,3.5,-14),(0,7.5,9),56)]
        for filename,repeat,eye,target,fov in views:
            rec=[]
            for n in range(repeat):
                for data,mat in triangles:
                    data=data.copy();data[:,:,2]+=n*6
                    for one in data:
                        rec.append(struct.pack('<I15f',mat,*one.reshape(-1)))
            if repeat>1:
                for data,mat in end_triangles:
                    data=data.copy();data[:,:,2]+=repeat*6-.28
                    for one in data: rec.append(struct.pack('<I15f',mat,*one.reshape(-1)))
            inp=tmp/'scene.bin'
            with inp.open('wb') as f:
                f.write(struct.pack('<4sIIII',b'SHED',1920,1440,len(textures),len(rec)))
                for img,flags in textures:
                    f.write(struct.pack('<III',img.width,img.height,flags));f.write(img.tobytes())
                for item in rec:f.write(item)
            ppm=tmp/'render.ppm'; args=[str(exe),str(inp),str(ppm)]+[str(v) for v in (*eye,*target,fov,repeat)]
            subprocess.run(args,check=True)
            # Finish encoding and verify off to the side before publishing the
            # file, so concurrent project snapshots cannot capture a partial PNG.
            finished=tmp/filename
            with Image.open(ppm) as im: im.resize((1600,1200),Image.Resampling.LANCZOS).save(finished,optimize=True)
            with Image.open(finished) as im: im.load()
            os.replace(finished,OUT/filename)
            print('Saved',filename)
if __name__=='__main__':main()
