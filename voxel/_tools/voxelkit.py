"""Native colored voxel authoring and exact boundary extraction. Parent-owned."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import struct, hashlib
import numpy as np

class Grid:
    def __init__(self, shape, palette):
        self.shape=tuple(int(v) for v in shape)
        if len(self.shape)!=3 or min(self.shape)<1 or max(self.shape)>256: raise ValueError('VOX dimensions must be 1..256')
        self.palette=[tuple(int(c) for c in p)+(255,)*(4-len(p)) for p in palette]
        if not 1<=len(self.palette)<=256: raise ValueError('palette has empty index 0 and at most 255 colors')
        self.palette[0]=(0,0,0,0)
        self.data=np.zeros(self.shape,dtype=np.uint8)
        self.x=np.arange(self.shape[0],dtype=np.float32)[:,None,None]+.5
        self.y=np.arange(self.shape[1],dtype=np.float32)[None,:,None]+.5
        self.z=np.arange(self.shape[2],dtype=np.float32)[None,None,:]+.5
    def box(self,lo,hi,color):
        lo=np.maximum(np.floor(lo).astype(int),0); hi=np.minimum(np.ceil(hi).astype(int),self.shape)
        if np.all(hi>lo): self.data[tuple(slice(a,b) for a,b in zip(lo,hi))]=color
        return self
    def roundbox(self,lo,hi,radius,color):
        lo=np.asarray(lo,float);hi=np.asarray(hi,float);c=(lo+hi)/2;h=(hi-lo)/2
        radius=min(float(radius),float(min(h)))
        q=[np.abs(a-c[i])-(h[i]-radius) for i,a in enumerate((self.x,self.y,self.z))]
        outside=sum(np.maximum(a,0)**2 for a in q)
        inside=np.minimum(np.maximum(np.maximum(q[0],q[1]),q[2]),0)
        self.data[np.sqrt(outside)+inside<=radius]=color;return self
    def ellipsoid(self,center,radii,color):
        if min(radii)<=0: raise ValueError('ellipsoid radii must be positive')
        mask=sum(((a-center[i])/radii[i])**2 for i,a in enumerate((self.x,self.y,self.z)))<=1
        self.data[mask]=color;return self
    def cylinder(self,center,radius,length,axis,color):
        return self.cone(center,radius,radius,length,axis,color)
    def cone(self,center,radius_bottom,radius_top,length,axis,color):
        if length<=0:raise ValueError('length must be positive')
        q=[a-center[i] for i,a in enumerate((self.x,self.y,self.z))]
        t=q[axis]/length+.5;r=radius_bottom+(radius_top-radius_bottom)*t
        mask=(t>=0)&(t<=1)&(sum(q[i]**2 for i in range(3) if i!=axis)<=r*r)
        self.data[mask]=color;return self
    def beam(self,a,b,radius,color):
        a=np.asarray(a,float);v=np.asarray(b,float)-a;den=float(v@v)
        if den<1e-12:return self.ellipsoid(a,(radius,)*3,color)
        q=[c-a[i] for i,c in enumerate((self.x,self.y,self.z))]
        t=np.clip(sum(q[i]*v[i] for i in range(3))/den,0,1)
        self.data[sum((q[i]-t*v[i])**2 for i in range(3))<=radius*radius]=color;return self
    def torus(self,center,major_radius,minor_radius,axis,color):
        q=[a-center[i] for i,a in enumerate((self.x,self.y,self.z))]
        ring=np.sqrt(sum(q[i]**2 for i in range(3) if i!=axis))-major_radius
        self.data[ring*ring+q[axis]**2<=minor_radius*minor_radius]=color;return self

@dataclass
class Asset:
    slug:str
    label:str
    grid:Grid
    voxel_size:float=.05
    notes:object=None
    half_postprocess:object=None

def reduce_half(grid):
    if any(n%2 for n in grid.shape):raise ValueError('all large dimensions must be even')
    nx,ny,nz=(n//2 for n in grid.shape)
    blocks=grid.data.reshape(nx,2,ny,2,nz,2).transpose(0,2,4,1,3,5).reshape(nx,ny,nz,8)
    out=Grid((nx,ny,nz),grid.palette);best=np.zeros(out.shape,dtype=np.uint8)
    for i in range(8):
        col=blocks[...,i];count=np.sum(blocks==col[...,None],axis=-1)
        use=(col>0)&((count>best)|((count==best)&(col>out.data)))
        out.data[use]=col[use];best[use]=count[use]
    return out

def _chunk(name,body):return name+struct.pack('<II',len(body),0)+body

def write_vox(path,grid):
    if grid.data.dtype!=np.uint8 or grid.data.shape!=grid.shape:raise ValueError('invalid occupancy array')
    if int(grid.data.max())>=len(grid.palette):raise ValueError('occupied palette index missing')
    coords=np.argwhere(grid.data>0)
    values=np.empty((len(coords),4),dtype=np.uint8)
    values[:,:3]=coords;values[:,3]=grid.data[tuple(coords.T)]
    colors=list(grid.palette[1:])+[(0,0,0,255)]*(256-(len(grid.palette)-1))
    children=_chunk(b'SIZE',struct.pack('<3I',*grid.shape))+_chunk(b'XYZI',struct.pack('<I',len(coords))+values.tobytes())+_chunk(b'RGBA',np.array(colors,dtype=np.uint8).tobytes())
    payload=b'VOX '+struct.pack('<I',150)+b'MAIN'+struct.pack('<II',0,len(children))+children
    Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_bytes(payload)

def read_vox(path):
    raw=Path(path).read_bytes()
    if raw[:4]!=b'VOX ' or len(raw)<20:raise ValueError('not a VOX file')
    if raw[8:12]!=b'MAIN':raise ValueError('missing MAIN')
    n,m=struct.unpack_from('<II',raw,12)
    if n!=0 or 20+m!=len(raw):raise ValueError('invalid root sizes')
    pos=20;shape=None;records=None;rgba=None
    while pos<len(raw):
        name=raw[pos:pos+4];length,child=struct.unpack_from('<II',raw,pos+4);pos+=12
        body=raw[pos:pos+length]
        if len(body)!=length or child:raise ValueError('truncated or unexpected child chunk')
        if name==b'SIZE':shape=struct.unpack('<3I',body)
        elif name==b'XYZI':
            count=struct.unpack_from('<I',body)[0]
            if len(body)!=4+4*count:raise ValueError('bad XYZI length')
            records=np.frombuffer(body[4:],np.uint8).reshape(-1,4).copy()
        elif name==b'RGBA':
            if len(body)!=1024:raise ValueError('bad RGBA length')
            rgba=np.frombuffer(body,np.uint8).reshape(256,4).copy()
        pos+=length
    if shape is None or records is None or rgba is None:raise ValueError('missing required chunks')
    if len(records)==0:raise ValueError('empty asset')
    if np.any(records[:,:3]>=np.array(shape)) or np.any(records[:,3]==0):raise ValueError('invalid coordinate/color')
    if len(np.unique(records[:,:3],axis=0))!=len(records):raise ValueError('duplicate voxel coordinates')
    grid=Grid(shape,[(0,0,0,0)]+[tuple(v) for v in rgba[:255]])
    grid.data[tuple(records[:,:3].T)]=records[:,3]
    return grid

def grid_stats(grid,voxel_size):
    coords=np.argwhere(grid.data>0)
    lo=coords.min(axis=0);hi=coords.max(axis=0)+1
    origin=np.array((grid.shape[0]/2,grid.shape[1]/2,0))
    return {'grid_size':list(grid.shape),'occupied_voxels':int(len(coords)),
        'voxel_size_m':float(voxel_size),'grid_extents_m':[float(n*voxel_size) for n in grid.shape],
        'occupied_bounds_voxels':[lo.tolist(),hi.tolist()],
        'bounds_m':[((lo-origin)*voxel_size).tolist(),((hi-origin)*voxel_size).tolist()],
        'palette_indices':np.unique(grid.data[grid.data>0]).astype(int).tolist(),
        'occupancy_sha256':hashlib.sha256(grid.data.tobytes()).hexdigest()}

def exposed_unit_faces(data):
    count=0
    for axis in range(3):
        a=np.pad(data>0,[(1,1) if i==axis else (0,0) for i in range(3)])
        count+=int(np.count_nonzero(np.diff(a.astype(np.int8),axis=axis)))
    return count

def greedy_surface(grid,voxel_size):
    """Merge only coplanar exposed faces of identical palette index; exact boundary."""
    vertices=[];faces=[];colors=[];area=0
    origin=np.array((grid.shape[0]/2,grid.shape[1]/2,0),float)
    for d in range(3):
        u=(d+1)%3;v=(d+2)%3
        a=np.transpose(grid.data,(d,u,v));z=np.zeros_like(a[:1]);a=np.concatenate((z,a,z),axis=0)
        for k in range(grid.shape[d]+1):
            before=a[k];after=a[k+1]
            for sign in (1,-1):
                mask=np.where((before>0)&(after==0),before,0) if sign==1 else np.where((after>0)&(before==0),after,0)
                if not mask.any():continue
                for i in range(mask.shape[0]):
                    j=0
                    while j<mask.shape[1]:
                        color=int(mask[i,j])
                        if not color:j+=1;continue
                        w=1
                        while j+w<mask.shape[1] and mask[i,j+w]==color:w+=1
                        h=1
                        while i+h<mask.shape[0] and np.all(mask[i+h,j:j+w]==color):h+=1
                        mask[i:i+h,j:j+w]=0
                        points=[]
                        for pu,pv in ((i,j),(i+h,j),(i+h,j+w),(i,j+w)):
                            point=np.zeros(3);point[d]=k;point[u]=pu;point[v]=pv
                            points.append(tuple((point-origin)*voxel_size))
                        start=len(vertices);vertices.extend(points)
                        order=(0,1,2,3) if sign==1 else (3,2,1,0)
                        faces.append(tuple(start+t for t in order));colors.append(color);area+=w*h
                        j+=w
    expected=exposed_unit_faces(grid.data)
    if area!=expected:raise AssertionError(f'boundary area differs {area} vs {expected}')
    return vertices,faces,colors,area

def run_theme(root,assets):
    from blender_pipeline import run_theme as impl
    return impl(Path(root),assets)
