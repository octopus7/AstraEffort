"""Independently inspect FBX exported from freshly reloaded saved UE meshes."""
import bpy,ast,math,json,datetime,collections
from mathutils import Vector
ROOT='D:/github/AstraEffort/ForestDemo/Work/xhigh';PHASE=ROOT+'/TexturePass'
tree=ast.parse(open(PHASE+'/unwrap_art.py').read())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'uv_metrics','exec'),globals())
source=json.load(open(PHASE+'/SourceArt/uv_report.json'))
report={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'Fresh UE StaticMeshExporterFBX export, independent Blender re-import, measured surface area/UV area and triangle overlap. No publication before this gate.','meshes':{}}
for name in ['SM_Broadleaf_1','SM_Pine_0','SM_Boulder_0','SM_Dock']:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.import_scene.fbx(filepath='D:/github/AstraEffort/ForestDemo/Saved/Workers/xhigh/TextureRoundtrip/'+name+'.fbx')
 objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(objects)==1,(name,len(objects))
 obj=objects[0];bpy.context.view_layer.objects.active=obj;obj.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 actual=summarize(obj);expected=source['meshes'][name]
 me=obj.data;me.calc_loop_triangles();uvdata=me.uv_layers.active.data;degdetails=[]
 for ti,tr in enumerate(me.loop_triangles):
  ps=[me.vertices[i].co for i in tr.vertices];qs=[uvdata[i].uv for i in tr.loops]
  ga=(ps[1]-ps[0]).cross(ps[2]-ps[0]).length*.5;ua=abs(cross(qs[1]-qs[0],qs[2]-qs[0]))*.5
  if ga<1e-10 or ua<1e-13:degdetails.append({'triangle':ti,'geometry_area_m2':ga,'uv_area':ua,'geometry_degenerate':ga<1e-10,'uv_degenerate':ua<1e-13,'positions_m':[[p.x,p.y,p.z] for p in ps],'uv_coordinates':[[q.x,q.y] for q in qs]})
 actual['degenerate_triangle_details']=degdetails
 actual['source_surface_area_m2']=expected['surface_area_m2'];actual['source_uv_area']=expected['uv_area']
 actual['area_relative_error']=abs(actual['surface_area_m2']/expected['surface_area_m2']-1)
 actual['uv_area_relative_error']=abs(actual['uv_area']/expected['uv_area']-1)
 actual['effective_area_rms_px_per_m_with_saved_material_factor']=actual['base_px_per_m']*expected['mesh_sampling_factor']
 actual['passed']=actual['positive_area_overlap_pairs']==0 and actual['area_relative_error']<.003 and actual['uv_area_relative_error']<.003 and actual['degenerate_triangles']==0
 report['meshes'][name]=actual;print('ROUNDTRIP',name,actual['passed'],flush=True)
report['passed']=all(m['passed'] for m in report['meshes'].values())
json.dump(report,open(PHASE+'/uv_roundtrip_validation.json','w'),indent=2)
