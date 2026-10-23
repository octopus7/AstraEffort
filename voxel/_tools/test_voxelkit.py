"""Format and boundary invariants, independent of authored model choices."""
import tempfile
from pathlib import Path
import numpy as np
from voxelkit import Grid,write_vox,read_vox,reduce_half,greedy_surface

def main():
    p=[(0,0,0,0),(197,76,31,255),(11,112,169,255)]
    g=Grid((4,4,4),p);g.box((0,0,0),(2,1,1),1);g.data[3,3,3]=2
    with tempfile.TemporaryDirectory() as d:
        path=Path(d)/'test.vox';write_vox(path,g);r=read_vox(path)
        assert np.array_equal(g.data,r.data)
        assert r.palette[:3]==p
        # Duplicate coordinates must be rejected rather than silently overwrite.
        raw=bytearray(path.read_bytes());start=raw.index(b'XYZI')+16;raw[start+4:start+8]=raw[start:start+4];path.write_bytes(raw)
        try:read_vox(path)
        except ValueError as e:assert 'duplicate' in str(e)
        else:raise AssertionError('duplicate accepted')
    h=reduce_half(g);assert h.shape==(2,2,2);assert h.data[0,0,0]==1 and h.data[1,1,1]==2
    solid=Grid((4,4,4),p).box((1,1,1),(3,3,3),1)
    verts,faces,colors,area=greedy_surface(solid,1)
    assert len(faces)==6 and area==24 and set(colors)=={1}
    center=np.array((0,0,2))
    for face in faces:
        v=np.array([verts[i] for i in face]);normal=np.cross(v[1]-v[0],v[2]-v[0]);assert np.dot(normal,v.mean(axis=0)-center)>0
    solid.data[1,:,:]=np.where(solid.data[1,:,:]>0,2,0)
    _,faces,colors,area=greedy_surface(solid,1);assert area==24 and set(colors)=={1,2}
    print('PASS: VOX occupancy/palette roundtrip; duplicate rejection; half details; exact external area; outward normals; color boundary')

if __name__=='__main__':main()
