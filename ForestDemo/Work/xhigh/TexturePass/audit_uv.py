import bpy,ast,math,json,datetime,collections
from mathutils import Vector
ROOT='D:/github/AstraEffort/ForestDemo/Work/xhigh';OUT=ROOT+'/TexturePass/SourceArt'
tree=ast.parse(open(ROOT+'/TexturePass/unwrap_art.py').read())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'uv_functions','exec'),globals())
bpy.ops.wm.open_mainfile(filepath=OUT+'/QuietCove_TexturePass.blend')
r=json.load(open(OUT+'/uv_report.json'));r['overlap_area_tolerance_uv2']=1e-8;r['overlap_area_tolerance_texel2']=1e-8*1254**2
for name in r['meshes']:
 old=r['meshes'][name];r['meshes'][name]=summarize(bpy.data.objects[name])
 if 'repair' in old:r['meshes'][name]['repair']=old['repair']
 print('AUDIT',name,r['meshes'][name]['positive_area_overlap_pairs'],flush=True)
for p in r['placements']:
 m=r['meshes'][p['mesh']];p['material_mesh_factor']=m['mesh_sampling_factor'];p['world_surface_area_m2']=m['surface_area_m2']*p['world_scale'][0]**2;p['uv_area']=m['uv_area']
r['passed']=all(m['positive_area_overlap_pairs']==0 for m in r['meshes'].values());r['final_audit_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
json.dump(r,open(OUT+'/uv_report.json','w'),indent=2)
for name in ['SM_Broadleaf_1','SM_Pine_0','SM_Boulder_0','SM_Dock']:
 bpy.ops.object.select_all(action='DESELECT');o=bpy.data.objects[name];o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o
 bpy.ops.uv.export_layout(filepath=OUT+'/'+name+'_UV.svg',export_all=True,mode='SVG',size=(1254,1254),opacity=.3)
 o.hide_set(True)
print('AUDIT_COMPLETE',r['passed'],flush=True)
