import bpy,json,sys
from pathlib import Path
W=Path(r'D:/github/AstraEffort/ForestDemo/Work/NightMarket/max')
bpy.ops.wm.open_mainfile(filepath=str(W/'Source'/'NightMarket_Source.blend'))
out=[]
for nm in ['SM_NM_Stall_Buns','SM_NM_Stall_Noodles','SM_NM_Stall_Pastry','SM_NM_Stall_Fruit']:
 me=bpy.data.objects[nm].data;idx=[i for i,m in enumerate(me.materials) if m.name=='GlowCream'];faces=[f for f in me.polygons if f.material_index in idx]
 out.append({'mesh':nm,'font_triangles':len(faces),'front_facing_area_m2':sum(f.area for f in faces if f.normal.y<-.5),'back_facing_area_m2':sum(f.area for f in faces if f.normal.y>.5),'near_front_normal_examples':[list(f.normal) for f in faces[:5]],'font_y_bounds_m':[min(me.vertices[i].co.y for f in faces for i in f.vertices),max(me.vertices[i].co.y for f in faces for i in f.vertices)]})
(W/'Evidence'/('font_geometry_after.json' if '--after' in sys.argv else 'font_geometry_inspection.json')).write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2),flush=True)
