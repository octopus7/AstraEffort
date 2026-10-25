import bpy, json, math, datetime
from pathlib import Path
from mathutils import Vector
W=Path(r'D:/github/AstraEffort/ForestDemo/Work/NightMarket/max')
bpy.ops.wm.open_mainfile(filepath=str(W/'Source'/'NightMarket_Source.blend'))
data=json.loads((W/'Source'/'source_manifest.json').read_text(encoding='utf-8'));changes=[]
angles={'Stall_Soup':-12,'Stall_Greens':10,'Stall_Pastry':-8,'Stall_Dumplings':8}
for key,semantic in data['semantic_groups'].items():
 obj=bpy.data.objects.get('SM_NM_'+key)
 if not obj:continue
 rules=[]
 if semantic['type']=='food_cart':
  x,y=semantic['position_m'];a=math.radians(angles.get(key,0));n=Vector((math.sin(a),-math.cos(a),0));p=Vector((x,y,3.55))+n*2.01
  rules.append(('GlowCream',n,p))
 elif semantic['type']=='shopfront':
  x,y,w,d=semantic['footprint_m'];rules.append(('GlowCream',Vector((0,-1,0)),Vector((x,y-d/2-.64,4.53))))
  rules.append(('GlowMint',Vector((1,0,0)),Vector((x+w/2+.33,y-d/2+.3,6.5))))
 elif semantic['type']=='entrance':
  rules=[('GlowCream',Vector((0,-1,0)),Vector((0,-43.24,6.62))),('GlowMint',Vector((0,-1,0)),Vector((0,-43.25,5.90)))]
 if not rules:continue
 me=obj.data;flipped=0;tested=0
 for material,n,p in rules:
  ids={i for i,m in enumerate(me.materials) if m.name==material}
  for face in me.polygons:
   if face.material_index not in ids:continue
   depth=(face.center-p).dot(n);alignment=face.normal.dot(n)
   # Only the 36mm thick authored text envelope; window planes are separated.
   if abs(depth)>.0205 or abs(alignment)<.3 or abs(depth)<.00001:continue
   tested+=1
   if depth*alignment<0:face.flip();flipped+=1
 me.update();changes.append({'mesh':obj.name,'inspected_cap_and_bevel_faces':tested,'flipped_inward_open_glyph_faces':flipped})
bpy.ops.wm.save_as_mainfile(filepath=str(W/'Source'/'NightMarket_Source.blend'))
(W/'Evidence'/'font_winding_correction.json').write_text(json.dumps({'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cause':'Global consistent-normal operation had ambiguously oriented disconnected open font caps. Explicit front/back text-envelope tests determine intended winding. Closed component audit is kept separate.','changed':changes,'flipped_total':sum(c['flipped_inward_open_glyph_faces'] for c in changes)},indent=2),encoding='utf-8')
print('FONT_CAP_CORRECTION',sum(c['flipped_inward_open_glyph_faces'] for c in changes),flush=True)
exec((W/'Source'/'verify_source_uv.py').read_text(encoding='utf-8'),{'__name__':'__main__'})
