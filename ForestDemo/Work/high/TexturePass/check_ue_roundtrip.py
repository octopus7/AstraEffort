import bpy, json, math, ast, datetime
from pathlib import Path
R=Path('D:/github/AstraEffort/ForestDemo/Work/high/TexturePass')
audit=json.loads((R/'uv_audit.json').read_text())
# Reuse only the pure triangle-intersection functions, without running authoring.
tree=ast.parse((R/'uv_author.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('signed','intersect_area')],type_ignores=[]),'uv_geometry','exec'))
def inspect(path):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1.0
 from io_scene_fbx import parse_fbx
 tree,version=parse_fbx.parse(str(path))
 settings=next(n for n in tree.elems if n.id==b'GlobalSettings')
 props=next(n for n in settings.elems if n.id==b'Properties70')
 unit_cm=float(next(n for n in props.elems if n.props[0]==b'UnitScaleFactor').props[-1])
 assert abs(unit_cm-1.0)<1e-8,('expected UE centimetre FBX units',unit_cm)
 bpy.ops.import_scene.fbx(filepath=str(path),global_scale=1.0)
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
 area=uvarea=0;triangles=[];bounds=[]
 for obj in meshes:
  me=obj.data;me.calc_loop_triangles();uv=me.uv_layers.active.data
  for tri in me.loop_triangles:
   pts=[obj.matrix_world@me.vertices[i].co for i in tri.vertices]
   area+=(pts[1]-pts[0]).cross(pts[2]-pts[0]).length*.5
   t=[tuple(uv[i].uv) for i in tri.loops];au=abs(signed(t));uvarea+=au
   if au>1e-12:triangles.append(t)
  bounds.extend(tuple(obj.matrix_world@v.co) for v in me.vertices)
 overlaps=0
 bb=[(min(p[0] for p in t),min(p[1] for p in t),max(p[0] for p in t),max(p[1] for p in t)) for t in triangles]
 for i,t in enumerate(triangles):
  for j in range(i):
   if bb[i][0]>=bb[j][2]-1e-8 or bb[j][0]>=bb[i][2]-1e-8 or bb[i][1]>=bb[j][3]-1e-8 or bb[j][1]>=bb[i][3]-1e-8:continue
   if intersect_area(t,triangles[j])>1e-8:overlaps+=1
 return {'mesh_objects':len(meshes),'triangle_count':len(triangles),'fbx_unit_scale_factor_cm':unit_cm,'blender_metres_per_unit':1.0,'import_global_scale':1.0,'actual_surface_area_m2':area,'uv_area':uvarea,'positive_uv_overlap_pairs':overlaps,'dimensions_m':[max(p[k] for p in bounds)-min(p[k] for p in bounds) for k in range(3)]}
binding=json.loads((R/'texture_binding_validation.json').read_text())
report={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Three saved UE mesh variants only; this is not a quantitative roundtrip audit of all 228 variants. All 228 have separate binding/channel/full-precision checks.','method':'Read FBX UnitScaleFactor (assert centimetre units); import into explicit one-metre Blender units at scale 1. Measure exported UE triangle geometry in world metres, UV areas and overlaps. Density denominators use this independently measured UE area multiplied by actual saved-map actor scales, not source audit areas. Source geometry/dimensions provide independent unit-ratio checks.','meshes':{}}
for f in sorted((R/'Source/UEExports').glob('*.fbx')):
 source=inspect(R/'Source/FBX'/f.name);ue=inspect(f)
 base=f.stem.split('_UV')[0];v=audit['meshes'][base]['variants'][f.stem]
 ratio=math.sqrt(ue['actual_surface_area_m2']/source['actual_surface_area_m2'])
 dimension_ratios=[u/s for u,s in zip(ue['dimensions_m'],source['dimensions_m'])]
 assert abs(ratio-1)<.001,(f.name,'area unit ratio',ratio)
 assert all(abs(r-1)<.001 for r in dimension_ratios),(f.name,'dimension ratios',dimension_ratios)
 error=abs(ue['uv_area']/source['uv_area']-1)
 assert error<1e-4,(f.name,error)
 assert ue['positive_uv_overlap_pairs']==0,(f.name,ue)
 assert ue['triangle_count']==source['triangle_count']
 density=627*math.sqrt(ue['uv_area']/(ue['actual_surface_area_m2']*v['scale_bucket']**2))
 assert abs(density-16)<.01,(f.name,density)
 actors=[]
 for instance in binding['instances']:
  if instance['mesh_name']!=f.stem:continue
  scales=[abs(x) for x in instance['world_scale']];assert max(scales)-min(scales)<1e-6
  world_area=ue['actual_surface_area_m2']*scales[0]**2
  measured_density=627*math.sqrt(ue['uv_area']/world_area)
  expected=16*v['scale_bucket']/scales[0]
  assert abs(measured_density/expected-1)<.001
  assert abs(measured_density/16-1)<.0202
  actors.append(dict(instance,actual_world_surface_area_m2=world_area,measured_native_px_per_m=measured_density,expected_px_per_m=expected))
 assert actors,f.stem
 report['meshes'][f.stem]={'source':source,'saved_ue_export':ue,'ue_to_source_linear_unit_ratio':ratio,'ue_to_source_dimension_ratios':dimension_ratios,'unit_geometry_relative_tolerance':.001,'uv_area_relative_error':error,'uv_area_relative_tolerance':.0001,'saved_uv_density_at_bucket_px_per_m':density,'scale_bucket':v['scale_bucket'],'actual_saved_actor_density_checks':actors}
assert len(report['meshes'])==3
report['status']='passed'
(R/'ue_uv_roundtrip_validation.json').write_text(json.dumps(report,indent=2))
print('HIGH_UE_UV_ROUNDTRIP_PASSED')

import numpy as np
manifest=json.loads((R/'Screenshots/capture_manifest.json').read_text())
shots={s['name']:s for s in manifest['shots']}
for k in ('position','rotation_pitch_yaw_roll','projection','horizontal_fov_degrees'):
 assert shots['water_t0'][k]==shots['water_t1'][k],k
imgs=[]
for name in ('water_t0','water_t1'):
 im=bpy.data.images.load(str(R/'Screenshots'/(name+'.png')),check_existing=False)
 assert list(im.size)==[1920,1080]
 pixels=np.empty(1920*1080*4,dtype=np.float32);im.pixels.foreach_get(pixels)
 imgs.append(pixels.reshape(1080,1920,4)[:,:,:3])
delta=np.abs(imgs[1]-imgs[0]);changed=np.any(delta>1/255,axis=2)
result={'same_camera_verified':True,'wall_capture_interval_seconds':shots['water_t1']['elapsed_capture_seconds']-shots['water_t0']['elapsed_capture_seconds'],'editor_world_time_interval_seconds':shots['water_t1']['editor_world_seconds']-shots['water_t0']['editor_world_seconds'],'changed_pixel_fraction_over_1_255':float(changed.mean()),'mean_absolute_channel_difference_0_1':float(delta.mean()),'maximum_channel_difference_0_1':float(delta.max()),'note':'Pixel difference establishes actual temporal render change; visual inspection is recorded separately. This is not proof of a physical fluid solver.'}
assert result['changed_pixel_fraction_over_1_255']>.001,result
import hashlib
result['input_shots']={name:{'captured_at_utc':shots[name]['captured_at_utc'],'sha256':hashlib.sha256((R/'Screenshots'/(name+'.png')).read_bytes()).hexdigest()} for name in ('water_t0','water_t1')}
(R/'water_temporal_validation.json').write_text(json.dumps(result,indent=2))
print('HIGH_WATER_TEMPORAL_PASSED',json.dumps(result))
