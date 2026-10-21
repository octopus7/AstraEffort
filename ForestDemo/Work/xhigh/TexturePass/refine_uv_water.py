import bpy,bmesh,ast,math,json,datetime,collections,os
from mathutils import Vector
ROOT='D:/github/AstraEffort/ForestDemo/Work/xhigh'
OUT=ROOT+'/TexturePass/SourceArt'
tree=ast.parse(open(ROOT+'/TexturePass/unwrap_art.py').read())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'uv_functions','exec'),globals())
bpy.ops.wm.open_mainfile(filepath=OUT+'/QuietCove_TexturePass.blend')
report=json.load(open(OUT+'/uv_report.json'));data=json.load(open(ROOT+'/scene_manifest.json'))
json.dump(report,open(OUT+'/uv_report_initial.json','w'),indent=2)
report['repair_started_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
modified=[]
for name,old in list(report['meshes'].items()):
 water=name in ['SM_Sea','SM_Lake','SM_Surf_0','SM_Surf_1','SM_Surf_2']
 if not water and old['positive_area_overlap_pairs']==0 and old['degenerate_triangles']==0:continue
 obj=bpy.data.objects[name];obj.hide_set(False);obj.hide_viewport=False
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 if name=='SM_Sea':
  vs=[];fs=[];nx=160;ny=56
  # Saved Blender geometry already reflects Y; retain compensated coordinates/winding.
  for j in range(ny+1):
   for i in range(nx+1):vs.append((-50+100*i/nx,50-35*j/ny,0))
  for j in range(ny):
   for i in range(nx):a=j*(nx+1)+i;fs.append((a,a+nx+1,a+nx+2,a+1))
  me=bpy.data.meshes.new('SubdividedSea');me.from_pydata(vs,[],fs);me.update();me.materials.append(bpy.data.materials['WaterSea']);obj.data=me
 elif name=='SM_Lake':
  bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=3,use_grid_fill=True);bm.to_mesh(obj.data);bm.free()
 elif name.startswith('SM_Surf'):
  band=int(name[-1]);vs=[];fs=[]
  for i in range(321):
   x=-49.7+99.4*i/320;coast=-27+3*math.sin(x*.085)+1.8*math.sin(x*.19+.8)
   y=coast+[4.4,1.1,-2.7][band]+.20*math.sin(x*.6+band)
   width=[.45,.28,.20][band]*(.75+.25*math.sin(x*.31+band))
   vs.extend([(x,-y,.025),(x,-y-width,.025)])
  for i in range(320):fs.append((i*2,i*2+1,i*2+3,i*2+2))
  me=bpy.data.meshes.new('SoftFoamRibbon');me.from_pydata(vs,[],fs);me.update();me.materials.append(bpy.data.materials['Foam']);obj.data=me
 else:
  bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.triangulate(bm,faces=list(bm.faces))
  deg=[f for f in bm.faces if f.calc_area()<1e-10]
  if deg:bmesh.ops.delete(bm,geom=deg,context='FACES')
  bm.to_mesh(obj.data);bm.free()
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
 # Near-per-face projection for repaired meshes removes folded cap islands.
 bpy.ops.uv.smart_project(angle_limit=math.radians(66 if water else 1),island_margin=.0064,area_weight=0,correct_aspect=True,scale_to_bounds=False)
 bpy.ops.uv.select_all(action='SELECT');bpy.ops.uv.average_islands_scale(scale_uv=True,shear=False)
 bpy.ops.uv.pack_islands(rotate=True,scale=True,margin_method='FRACTION',margin=.0064)
 bpy.ops.object.mode_set(mode='OBJECT');obj.data.uv_layers.active.name='UniqueSurfaceUV'
 metrics=summarize(obj);metrics['repair']='Water tessellation/foam shape' if water else 'Triangulation, removed zero-area tips, 1 degree surface projection'
 report['meshes'][name]=metrics
 bpy.ops.export_scene.fbx(filepath=OUT+'/'+name+'.fbx',use_selection=True,object_types={'MESH'},add_leaf_bones=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,bake_anim=False,use_mesh_modifiers=True,mesh_smooth_type='FACE',colors_type='LINEAR')
 obj.hide_set(True);modified.append(name);print('REPAIR_COMPLETE',name,json.dumps(metrics),flush=True)
for p in report['placements']:
 m=report['meshes'][p['mesh']];p['material_mesh_factor']=m['mesh_sampling_factor'];p['world_surface_area_m2']=m['surface_area_m2']*p['world_scale'][0]**2;p['uv_area']=m['uv_area']
report['method']='Unique packed UV0 islands; area-normalized island scale. Saved Custom Primitive Data[0] = mesh sampling factor * actual uniform placed world scale. Material samples UV0 * CPD[0]. Generated surface images repeat intentionally; surfaces have separate non-overlapping authoring UVs, not bespoke painted per-instance atlases.'
report['repair_finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['repaired_meshes']=modified
report['passed']=all(m['positive_area_overlap_pairs']==0 and m['uv_bounds'][0]>=-1e-5 and m['uv_bounds'][1]>=-1e-5 and m['uv_bounds'][2]<=1.00001 and m['uv_bounds'][3]<=1.00001 for m in report['meshes'].values())
report['exceptions']=['Curved surfaces retain measured within-island projection stretch; per-mesh area-RMS density is 128 px/m, percentile ranges reported.', 'Uniform scales only; all 889 placed prop scales checked. Future changed actor scales require CPD update.', 'Terrain detail uses world XY at 127.908 px/m horizontally; slope lowers surface density.', 'Water and foam use world-space animated coordinates; no finite albedo texel density. Caustic image uses world projection.', 'NPOT 1254-square original images use no mipmaps; full native texel density is the reported value.']
json.dump(report,open(OUT+'/uv_report.json','w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/QuietCove_TexturePass.blend')
print('REFINE_ALL_COMPLETE',report['passed'],flush=True)
