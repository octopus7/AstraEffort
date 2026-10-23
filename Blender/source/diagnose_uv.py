import bpy,numpy as np,json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
N=4096;grid=np.full((N,N),-1,dtype=np.int32);pairs=collections.Counter();infos=[];bad=collections.Counter();faces=set();zerofaces=[]
for o in [o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('SSTO_')]:
    me=o.data;me.calc_loop_triangles();uv=me.uv_layers.active
    for t in me.loop_triangles:
        idx=len(infos);p=me.polygons[t.polygon_index]
        info=(o.name,p.material_index,t.polygon_index)
        infos.append(info);pts=np.array([uv.data[j].uv[:] for j in t.loops])*N
        lo=np.maximum(0,np.ceil(pts.min(axis=0)-.5).astype(int));hi=np.minimum(N-1,np.floor(pts.max(axis=0)-.5).astype(int))
        if np.any(hi<lo):continue
        a,b,c=pts;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-9:
            zerofaces.append(info);continue
        x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
        q=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den;r=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
        mask=(q>1e-5)&(r>1e-5)&(q+r<1-1e-5)
        block=grid[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
        for prev,num in zip(*np.unique(block[mask&(block>=0)],return_counts=True)):
            old=infos[prev];pairs[(old[0],info[0])]+=int(num)
            faces.add(old);faces.add(info)
            if old[0]==info[0]:bad[(o.name,old[1],info[1])]+=int(num)
        block[mask]=idx
report={'overlap_faces':sorted(faces),'zero_faces':zerofaces,'overlap_object_pairs':[(str(k),v) for k,v in pairs.most_common(20)],'within_object_material_pairs':[(str(k),v) for k,v in bad.most_common(20)],'layers':{o.name:[(uv.name,uv.active_render) for uv in o.data.uv_layers] for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('SSTO_')}}
print(json.dumps(report,indent=2));(ROOT/'validation'/'uv_diagnosis.json').write_text(json.dumps(report,indent=2))
