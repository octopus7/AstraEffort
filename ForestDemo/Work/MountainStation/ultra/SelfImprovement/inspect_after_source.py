import bpy,json,math,datetime
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement')
bpy.ops.wm.open_mainfile(filepath=str(R/'SourceArt/AlderPass_Textured.blend'))
dg=bpy.context.evaluated_depsgraph_get()
trees={n:BVHTree.FromObject(bpy.data.objects[n],dg) for n in ['SM_Terrain','SM_Footpath','SM_Ballast','SM_Sleepers','SM_Rails','SM_RailFasteners']}
def height(name,x,y):
    p,n,i,d=trees[name].ray_cast(Vector((x,y,80)),Vector((0,0,-1)))
    return p.z if p else None
path=bpy.data.objects['SM_Footpath'];path.data.calc_loop_triangles();probes=[]
for t in path.data.loop_triangles:
    if t.normal.z<.1:continue
    p=sum((path.data.vertices[i].co for i in t.vertices),Vector())/3
    h=height('SM_Terrain',p.x,p.y)
    probes.append({'triangle':t.index,'xyz':list(p),'terrain_z':h,'clearance_m':p.z-h})
probes.sort(key=lambda x:x['clearance_m'])
track=[]
for i in range(8,140,8):
    x=-49.5+i*.68;y=-9+.012*(x+3)**2
    track.append({'xy':[x,y],'terrain':height('SM_Terrain',x,y),'ballast':height('SM_Ballast',x,y),'sleeper':height('SM_Sleepers',x,y)})
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'path_top_triangle_probes':len(probes),'path_below_terrain_count':sum(p['clearance_m']<0 for p in probes),'path_worst_samples':probes[:20],'track_top_heights':track}
(R/'source_after_diagnostics.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result),flush=True)
