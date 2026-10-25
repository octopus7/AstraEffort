"""Six-neighbor occupancy components, using scanline interval unions."""
from pathlib import Path
import sys,json
sys.dont_write_bytecode=True
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[1]/'_tools'))
from voxelkit import read_vox

def components(grid):
    parent=[];weight=[];runs=[];lines={}
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    def join(a,b):
        a=root(a);b=root(b)
        if a==b:return
        if weight[a]<weight[b]:a,b=b,a
        parent[b]=a;weight[a]+=weight[b]
    for z in range(grid.shape[2]):
        for y in range(grid.shape[1]):
            line=grid.data[:,y,z]>0
            change=np.diff(np.pad(line.astype(np.int8),(1,1)))
            starts=np.flatnonzero(change==1);ends=np.flatnonzero(change==-1)
            current=[]
            for a,b in zip(starts,ends):
                idx=len(parent);parent.append(idx);weight.append(int(b-a))
                runs.append((int(a),int(b),y,z));current.append((int(a),int(b),idx))
            lines[(y,z)]=current
            for key in ((y-1,z),(y,z-1)):
                other=lines.get(key,[]);i=j=0
                while i<len(current) and j<len(other):
                    a,b,idx=current[i];c,d,jdx=other[j]
                    if a<d and c<b:join(idx,jdx)
                    if b<d:i+=1
                    else:j+=1
    result={}
    for i,(a,b,y,z) in enumerate(runs):
        r=root(i)
        if r not in result:result[r]={'occupied_voxels':0,'bounds_voxels':[[a,y,z],[b,y+1,z+1]]}
        item=result[r];item['occupied_voxels']+=b-a
        item['bounds_voxels'][0]=np.minimum(item['bounds_voxels'][0],[a,y,z]).tolist()
        item['bounds_voxels'][1]=np.maximum(item['bounds_voxels'][1],[b,y+1,z+1]).tolist()
    return sorted(result.values(),key=lambda x:-x['occupied_voxels'])

if __name__=='__main__':
    records=[]
    for path in sorted((ROOT/'assets').rglob('*.vox')):
        parts=components(read_vox(path))
        records.append({'file':path.relative_to(ROOT).as_posix(),'component_count':len(parts),'components':parts})
    result={'all_connected':all(r['component_count']==1 for r in records),'variants':records}
    print(json.dumps(result,indent=2))
    output=ROOT/'logs'/('support_check_'+('initial' if not (ROOT/'logs'/'support_check_initial.json').exists() else 'latest')+'.json')
    output.write_text(json.dumps(result,indent=2),encoding='utf-8')
