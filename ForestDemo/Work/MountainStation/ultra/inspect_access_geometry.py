import bpy,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra'
bpy.ops.wm.open_mainfile(filepath=ROOT+'/SourceArt/AlderPass.blend')
dg=bpy.context.evaluated_depsgraph_get();bvhs={o.name:BVHTree.FromObject(o,dg) for o in bpy.data.objects if o.type=='MESH'}
out=[]
for x in [-29.5,-27.5,-25.5,-23.5,-21.5,-19.5,-17.5,-16]:
    y=max(2,5-(x+30)*3/13);hits=[]
    for name,bvh in bvhs.items():
        hit=bvh.ray_cast(Vector((x,y,25)),Vector((0,0,-1)))
        if hit[0] is not None:hits.append({'mesh':name,'height_m':hit[0].z})
    out.append({'x':x,'y':y,'hits':sorted(hits,key=lambda h:-h['height_m'])})
with open(ROOT+'/source_access_raycasts.json','w') as f:json.dump(out,f,indent=2)
print(out,flush=True)
