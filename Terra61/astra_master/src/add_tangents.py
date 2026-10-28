#!/usr/bin/env python3
"""Add tangent accessors to normal-mapped GLB primitives in place.

Examples:
    python station/src/add_tangents.py /tmp/model.glb
    python station/src/add_tangents.py '/tmp/asset_copies/**/*.glb'

POSITION, NORMAL, TEXCOORD_n and indices may be interleaved, strided, sparse,
or integer-encoded. A normal texture's TEXCOORD_n selection is honored. Tangents
use an area-weighted derivative, Gram-Schmidt orthogonalization, and glTF's
handedness convention. Singular UVs receive a stable perpendicular fallback.
Existing tangents are left untouched. Each changed GLB is atomically replaced.
"""
from __future__ import annotations

import argparse
import base64
import glob
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
from urllib.parse import unquote, urlparse

import numpy as np

DTYPES={5120:np.dtype('i1'),5121:np.dtype('u1'),5122:np.dtype('<i2'),
        5123:np.dtype('<u2'),5125:np.dtype('<u4'),5126:np.dtype('<f4')}
SIZES={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}


def parse_glb(data):
    if len(data)<12: raise ValueError('file is too short for a GLB header')
    magic,version,size=struct.unpack_from('<4sII',data)
    if magic!=b'glTF' or version!=2 or size!=len(data):
        raise ValueError('not a complete glTF 2.0 binary file')
    chunks=[]; offset=12
    while offset<len(data):
        if offset+8>len(data): raise ValueError('truncated chunk header')
        length,kind=struct.unpack_from('<I4s',data,offset); offset+=8
        if length%4 or offset+length>len(data): raise ValueError('invalid or truncated chunk')
        chunks.append((kind,data[offset:offset+length])); offset+=length
    if not chunks or chunks[0][0]!=b'JSON': raise ValueError('first GLB chunk is not JSON')
    if sum(k==b'JSON' for k,_ in chunks)!=1 or sum(k==b'BIN\0' for k,_ in chunks)>1:
        raise ValueError('unexpected duplicate JSON or BIN chunks')
    doc=json.loads(chunks[0][1].rstrip(b' \t\r\n\0'))
    binary=next((payload for kind,payload in chunks if kind==b'BIN\0'),None)
    return doc,binary,chunks


def load_buffers(doc,binary,base):
    buffers=[]
    for index,info in enumerate(doc.get('buffers',[])):
        uri=info.get('uri')
        if uri is None:
            if index!=0 or binary is None: raise ValueError('missing GLB binary buffer')
            data=binary
        elif uri.startswith('data:'):
            metadata,sep,payload=uri.partition(',')
            if not sep: raise ValueError('malformed data URI')
            data=base64.b64decode(payload,validate=True) if metadata.endswith(';base64') else unquote(payload).encode('latin1')
        else:
            parsed=urlparse(uri)
            if parsed.scheme or parsed.netloc: raise ValueError('remote buffer URIs are unsupported')
            data=(base/unquote(parsed.path)).read_bytes()
        if len(data)<info['byteLength']: raise ValueError(f'buffer {index} is truncated')
        buffers.append(data)
    return buffers


def view_array(doc,buffers,view_index,component,components,count,offset=0):
    view=doc['bufferViews'][view_index]; dtype=DTYPES[component]; item=dtype.itemsize
    elem=components*item; stride=view.get('byteStride',elem)
    if stride<elem: raise ValueError('bufferView byteStride is smaller than an element')
    if count<0 or offset<0: raise ValueError('negative accessor count or offset')
    needed=0 if count==0 else (count-1)*stride+elem
    if offset+needed>view['byteLength']: raise ValueError('accessor exceeds its bufferView')
    begin=view.get('byteOffset',0)+offset
    source=buffers[view['buffer']]
    if begin+needed>len(source): raise ValueError('accessor exceeds its buffer')
    if not count: return np.empty((0,components),dtype=dtype)
    return np.ndarray((count,components),dtype=dtype,buffer=source,offset=begin,
                      strides=(stride,item)).copy()


def read_accessor(doc,buffers,index):
    accessor=doc['accessors'][index]
    component=accessor['componentType']; components=SIZES.get(accessor['type'])
    if component not in DTYPES or components is None: raise ValueError('unsupported accessor component or type')
    count=accessor['count']
    if 'bufferView' in accessor:
        data=view_array(doc,buffers,accessor['bufferView'],component,components,count,accessor.get('byteOffset',0))
    else:
        data=np.zeros((count,components),dtype=DTYPES[component])
    sparse=accessor.get('sparse')
    if sparse:
        ind=sparse['indices']; vals=sparse['values']; number=sparse['count']
        if ind['componentType'] not in (5121,5123,5125): raise ValueError('invalid sparse index component')
        indices=view_array(doc,buffers,ind['bufferView'],ind['componentType'],1,number,ind.get('byteOffset',0)).reshape(-1).astype(np.int64)
        if np.any(indices>=count) or len(np.unique(indices))!=len(indices): raise ValueError('invalid sparse indices')
        replacement=view_array(doc,buffers,vals['bufferView'],component,components,number,vals.get('byteOffset',0))
        data[indices]=replacement
    if accessor.get('normalized',False) and component!=5126:
        data=data.astype(np.float64)
        if component==5120: data=np.maximum(data/127.,-1.)
        elif component==5121: data/=255.
        elif component==5122: data=np.maximum(data/32767.,-1.)
        elif component==5123: data/=65535.
        elif component==5125: data/=4294967295.
    return data


def triangle_indices(indices,mode):
    indices=np.asarray(indices,dtype=np.int64).reshape(-1)
    if mode==4:
        if len(indices)%3: raise ValueError('triangle index count is not divisible by three')
        return indices.reshape(-1,3)
    if mode==5:
        if len(indices)<3: return np.empty((0,3),dtype=np.int64)
        result=np.column_stack((indices[:-2],indices[1:-1],indices[2:]))
        result[1::2,:2]=result[1::2,1::-1]
        return result
    if mode==6:
        if len(indices)<3: return np.empty((0,3),dtype=np.int64)
        return np.column_stack((np.full(len(indices)-2,indices[0]),indices[1:-1],indices[2:]))
    raise ValueError(f'normal-mapped primitive has unsupported draw mode {mode}')


def compute_tangents(position,normal,uv,triangles):
    position=np.asarray(position,dtype=np.float64)
    normal=np.asarray(normal,dtype=np.float64)
    uv=np.asarray(uv,dtype=np.float64)
    count=len(position)
    if position.shape!=(count,3) or normal.shape!=(count,3) or uv.shape!=(count,2):
        raise ValueError('POSITION, NORMAL and TEXCOORD counts or dimensions do not match')
    if not (np.isfinite(position).all() and np.isfinite(normal).all() and np.isfinite(uv).all()):
        raise ValueError('nonfinite source attribute')
    lengths=np.linalg.norm(normal,axis=1)
    if np.any(lengths<1e-15): raise ValueError('zero normal cannot define a tangent plane')
    n=normal/lengths[:,None]
    triangles=np.asarray(triangles,dtype=np.int64).reshape(-1,3)
    if len(triangles) and (triangles.min()<0 or triangles.max()>=count): raise ValueError('index out of bounds')
    tangent_sum=np.zeros((count,3),dtype=np.float64); bitangent_sum=np.zeros((count,3),dtype=np.float64)
    if len(triangles):
        p0,p1,p2=position[triangles[:,0]],position[triangles[:,1]],position[triangles[:,2]]
        t0,t1,t2=uv[triangles[:,0]],uv[triangles[:,1]],uv[triangles[:,2]]
        e1=p1-p0; e2=p2-p0; d1=t1-t0; d2=t2-t0
        determinant=d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0]
        area=np.linalg.norm(np.cross(e1,e2),axis=1)
        valid=(np.abs(determinant)>1e-14)&(area>1e-15)&np.isfinite(area)
        if valid.any():
            tri=triangles[valid]; e1=e1[valid]; e2=e2[valid]
            d1=d1[valid]; d2=d2[valid]; inv=1/determinant[valid]
            tangent=(e1*d2[:,1,None]-e2*d1[:,1,None])*inv[:,None]
            bitangent=(e2*d1[:,0,None]-e1*d2[:,0,None])*inv[:,None]
            weight=area[valid,None]
            np.add.at(tangent_sum,tri.reshape(-1),np.repeat(tangent*weight,3,axis=0))
            np.add.at(bitangent_sum,tri.reshape(-1),np.repeat(bitangent*weight,3,axis=0))
    projected=tangent_sum-n*np.sum(n*tangent_sum,axis=1)[:,None]
    magnitude=np.linalg.norm(projected,axis=1)
    fallback=(magnitude<1e-15)|~np.isfinite(magnitude)
    if fallback.any():
        chosen=np.eye(3)[np.argmin(np.abs(n[fallback]),axis=1)]
        projected[fallback]=np.cross(chosen,n[fallback])
        magnitude[fallback]=np.linalg.norm(projected[fallback],axis=1)
    tangent=projected/magnitude[:,None]
    handedness=np.where(np.sum(np.cross(n,tangent)*bitangent_sum,axis=1)<0,-1.,1.)
    result=np.column_stack((tangent,handedness)).astype('<f4')
    if not np.isfinite(result).all(): raise ValueError('failed to construct finite tangents')
    return result


def update_file(path):
    original=path.read_bytes(); doc,binary,chunks=parse_glb(original)
    materials=doc.get('materials',[]); pending=[]
    for mesh in doc.get('meshes',[]):
        for primitive in mesh.get('primitives',[]):
            attributes=primitive.get('attributes',{}); material_index=primitive.get('material')
            if 'TANGENT' in attributes or material_index is None: continue
            if material_index>=len(materials): raise ValueError('material index out of bounds')
            normal_texture=materials[material_index].get('normalTexture')
            if not normal_texture: continue
            texcoord=normal_texture.get('extensions',{}).get('KHR_texture_transform',{}).get('texCoord',normal_texture.get('texCoord',0))
            key=f'TEXCOORD_{texcoord}'
            if not all(k in attributes for k in ('POSITION','NORMAL',key)):
                raise ValueError(f'normal-mapped primitive is missing POSITION, NORMAL, or {key}')
            pending.append((primitive,key))
    if not pending: return 0
    # A GLB binary chunk must bind to buffer 0; all generated station modules
    # are self-contained. Other buffers may still be external or data URIs.
    if binary is None or not doc.get('buffers') or doc['buffers'][0].get('uri') is not None:
        raise ValueError('GLB has no embedded buffer 0 for tangent storage')
    buffers=load_buffers(doc,binary,path.parent)
    additions=[]
    for primitive,key in pending:
        attributes=primitive['attributes']
        position=read_accessor(doc,buffers,attributes['POSITION'])
        normal=read_accessor(doc,buffers,attributes['NORMAL'])
        uv=read_accessor(doc,buffers,attributes[key])
        if 'indices' in primitive:
            index_accessor=doc['accessors'][primitive['indices']]
            if index_accessor['componentType'] not in (5121,5123,5125) or index_accessor['type']!='SCALAR':
                raise ValueError('indices must use an unsigned scalar component type')
            indices=read_accessor(doc,buffers,primitive['indices']).reshape(-1)
        else: indices=np.arange(len(position),dtype=np.int64)
        triangles=triangle_indices(indices,primitive.get('mode',4))
        additions.append((primitive,compute_tangents(position,normal,uv,triangles)))
    blob=bytearray(binary)
    for primitive,tangents in additions:
        while len(blob)%4: blob.append(0)
        start=len(blob); payload=tangents.tobytes(); blob.extend(payload)
        view_index=len(doc.setdefault('bufferViews',[]))
        doc['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(payload),'target':34962})
        accessor_index=len(doc.setdefault('accessors',[]))
        doc['accessors'].append({'bufferView':view_index,'componentType':5126,'count':len(tangents),'type':'VEC4'})
        primitive['attributes']['TANGENT']=accessor_index
    doc['buffers'][0]['byteLength']=len(blob)
    json_data=json.dumps(doc,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')
    json_data+=b' '*((-len(json_data))%4)
    bin_data=bytes(blob)+b'\0'*((-len(blob))%4)
    out_chunks=[]
    for kind,payload in chunks:
        if kind==b'JSON': payload=json_data
        elif kind==b'BIN\0': payload=bin_data
        out_chunks.append(struct.pack('<I4s',len(payload),kind)+payload)
    total=12+sum(map(len,out_chunks))
    output=struct.pack('<4sII',b'glTF',2,total)+b''.join(out_chunks)
    mode=path.stat().st_mode & 0o777
    temp_name=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.'+path.name+'.',suffix='.tmp',delete=False) as tmp:
            temp_name=tmp.name
            os.fchmod(tmp.fileno(),mode)
            tmp.write(output); tmp.flush(); os.fsync(tmp.fileno())
        os.replace(temp_name,path); temp_name=None
    finally:
        if temp_name is not None:
            try: os.unlink(temp_name)
            except FileNotFoundError: pass
    return len(additions)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths',nargs='+',help='GLB file paths or quoted glob patterns')
    args=parser.parse_args(); paths=[]
    for pattern in args.paths:
        matches=glob.glob(pattern,recursive=True)
        if not matches: parser.error(f'no files match {pattern!r}')
        paths.extend(Path(s) for s in matches)
    seen=set(); errors=0
    for path in paths:
        resolved=path.resolve()
        if resolved in seen: continue
        seen.add(resolved)
        if not path.is_file() or path.suffix.lower()!='.glb':
            print(f'{path}: not a GLB file',file=sys.stderr); errors+=1; continue
        try:
            count=update_file(path)
            print(f'{path}: added tangents to {count} primitive(s)' if count else f'{path}: unchanged')
        except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as exc:
            print(f'{path}: {exc}',file=sys.stderr); errors+=1
    return 1 if errors else 0


if __name__=='__main__': sys.exit(main())
