"""Read actual GLB accessors and node transforms; no native Blender scene trust."""
import json,struct,hashlib
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
raw=(ROOT/'VendingMachine.glb').read_bytes();cursor=12;doc=None;binary=None
while cursor<len(raw):
    size,kind=struct.unpack_from('<I4s',raw,cursor);cursor+=8;chunk=raw[cursor:cursor+size];cursor+=size
    if kind==b'JSON':doc=json.loads(chunk.decode())
    if kind==b'BIN\0':binary=chunk
TYPES={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}
COUNTS={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def accessor(index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];dt=np.dtype(TYPES[a['componentType']]);width=COUNTS[a['type']]
    offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',dt.itemsize*width)
    return np.ndarray((a['count'],width),dtype=dt,buffer=binary,offset=offset,strides=(stride,dt.itemsize)).astype(np.float64)
def matrix(node):
    if 'matrix' in node:return np.array(node['matrix'],dtype=np.float64).reshape(4,4,order='F')
    x,y,z,w=node.get('rotation',[0,0,0,1])
    r=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]],dtype=np.float64)
    m=np.eye(4);m[:3,:3]=r@np.diag(node.get('scale',[1,1,1]));m[:3,3]=node.get('translation',[0,0,0]);return m
parents={}
for i,node in enumerate(doc['nodes']):
    for c in node.get('children',[]):parents[c]=i
cache={}
def world(i):
    if i not in cache:cache[i]=(world(parents[i]) if i in parents else np.eye(4))@matrix(doc['nodes'][i])
    return cache[i]
mins=[];maxs=[];stats=[];zero_uv=zero_3d=out_bounds=0
for ni,node in enumerate(doc['nodes']):
    if 'mesh' not in node:continue
    transform=world(ni)
    for pi,p in enumerate(doc['meshes'][node['mesh']]['primitives']):
        vertices=accessor(p['attributes']['POSITION']);uv=accessor(p['attributes']['TEXCOORD_0']);ids=accessor(p['indices']).ravel().astype(np.int64).reshape(-1,3)
        wp=vertices@transform[:3,:3].T+transform[:3,3]
        mins.append(wp.min(axis=0));maxs.append(wp.max(axis=0))
        q=uv[ids];a2=np.abs((q[:,1,0]-q[:,0,0])*(q[:,2,1]-q[:,0,1])-(q[:,1,1]-q[:,0,1])*(q[:,2,0]-q[:,0,0]))*.5
        v=wp[ids];a3=np.linalg.norm(np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]),axis=1)*.5
        z2=int((a2<1e-16).sum());z3=int((a3<1e-14).sum());outside=int(np.any((uv< -1e-6)|(uv>1+1e-6),axis=1).sum())
        zero_uv+=z2;zero_3d+=z3;out_bounds+=outside
        stats.append({'node':node.get('name'),'primitive':pi,'triangles':len(ids),'zero_area_uv_triangles':z2,'zero_area_geometry_triangles':z3,'uv_vertices_outside_unit_square':outside})
lo=np.min(mins,axis=0);hi=np.max(maxs,axis=0);dims=hi-lo
native=json.loads((ROOT/'validation/blend_validation.json').read_text())
native_dims=native['dimensions_xyz_m'];expected=np.array([native_dims[0],native_dims[2],native_dims[1]])
result={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'source':'Direct GLB accessor and hierarchical node-transform parse','glb_sha256':hashlib.sha256(raw).hexdigest(),'axis_convention':'glTF Y up; Blender X,Z,Y dimensions correspond to GLB X,Y,Z','bounds_min_m':lo.tolist(),'bounds_max_m':hi.tolist(),'dimensions_xyz_m':dims.tolist(),'feet_at_y_zero':bool(abs(lo[1])<1e-7),'dimensions_match_native_axis_permutation':bool(np.allclose(dims,expected,atol=1e-5)),'zero_area_uv_triangles':zero_uv,'zero_area_geometry_triangles':zero_3d,'uv_vertices_outside_unit_square':out_bounds,'primitives':stats}
result['passed']=result['feet_at_y_zero'] and result['dimensions_match_native_axis_permutation'] and zero_uv==0 and zero_3d==0 and out_bounds==0
(ROOT/'validation/glb_geometry_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='primitives'}),flush=True)
if not result['passed']:raise RuntimeError('Actual GLB geometry validation failed')
