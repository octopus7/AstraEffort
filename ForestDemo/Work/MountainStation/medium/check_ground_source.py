import bpy,json
from mathutils import Vector
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium'
bpy.ops.wm.open_mainfile(filepath=W+'/AlderPass.blend')
dg=bpy.context.evaluated_depsgraph_get(); results=[]
for x,y in [(0,-30),(20,-30),(-20,-30),(-27,-25)]:
 hit,loc,norm,idx,obj,matrix=bpy.context.scene.ray_cast(dg,Vector((x,y,10)),Vector((0,0,-1)))
 results.append({'x_m':x,'y_m':y,'hit':hit,'object':obj.name if obj else None,'location':list(loc),'normal':list(norm)})
json.dump(results,open(W+'/ground_sample_selection.json','w'),indent=2); print(results)
