import unreal as u, json, runpy, traceback, datetime, time
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra'); OUT=ROOT/'TexturePass'
ns=runpy.run_path(str(ROOT/'build_level.py'),init_globals={'SKIP_BUILD':True})
eas=ns['eas']; actors=ns['actors']; levels=ns['levels']; meshed=ns['meshed']; assettools=ns['assettools']; ml=ns['ml']; prop=ns['prop']; expr=ns['expr'];scalar=ns['scalar']; vector=ns['vector']; connect=ns['connect']; output=ns['output'];ASSET=ns['ASSET'];DATA=ns['DATA']
UV=json.loads((OUT/'uv_report.json').read_text()); assert UV['success']
report={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'textures':{},'materials':{},'mesh_count':0,'actors':[]}
def clean(name):
 mat=eas.load_asset(ASSET+'/Materials/M_'+name)
 for _ in range(24):
  if ml.get_num_material_expressions(mat)==0:break
  ml.delete_all_material_expressions(mat)
 assert ml.get_num_material_expressions(mat)==0
 prop(mat,'two_sided',True);prop(mat,'blend_mode',u.BlendMode.BLEND_OPAQUE)
 return mat
def mul(mat,a,b=None,value=1):
 n=expr(mat,u.MaterialExpressionMultiply);connect(a,'',n,'A')
 if b:connect(b,'',n,'B')
 else:prop(n,'const_b',value)
 return n
def custom(mat,code,kind='float3',inputs=None):
 n=expr(mat,u.MaterialExpressionCustom);prop(n,'code',code)
 prop(n,'output_type',u.CustomMaterialOutputType.CMOT_FLOAT3 if kind=='float3' else u.CustomMaterialOutputType.CMOT_FLOAT1)
 custom_inputs=[]
 for k in inputs:
  ci=u.CustomInput();prop(ci,'input_name',k);custom_inputs.append(ci)
 prop(n,'inputs',custom_inputs)
 for key,val in inputs.items():connect(val,'',n,key)
 return n
def finish(mat):ml.recompile_material(mat);eas.save_loaded_asset(mat)
def texture_material(name,color,texture):
 mat=clean(name);sample=expr(mat,u.MaterialExpressionTextureSample);prop(sample,'texture',texture)
 tint=custom(mat,'float l=dot(C,float3(0.2126,0.7152,0.0722));return Tint*(0.68+1.65*l);',inputs={'C':sample,'Tint':vector(mat,color)})
 output(tint,'',mat,u.MaterialProperty.MP_BASE_COLOR);output(mul(mat,tint,value=.09),'',mat,u.MaterialProperty.MP_EMISSIVE_COLOR)
 output(scalar(mat,.82),'',mat,u.MaterialProperty.MP_ROUGHNESS);finish(mat)
 report['materials'][name]={'texture':texture.get_path_name(),'UV_channel':0,'UV_scale':1,'base_color':'Generated albedo luminance modulates retained palette color; full-resolution source, no coordinate tiling or mirroring.'}
 return mat
def animated_material(name):
 mat=clean(name);p=expr(mat,u.MaterialExpressionWorldPosition);t=expr(mat,u.MaterialExpressionTime)
 inputs={'P':p,'T':t}
 if name in ['Sea','Lake']:
  prop(mat,'blend_mode',u.BlendMode.BLEND_TRANSLUCENT)
  prop(mat,'translucency_lighting_mode',u.TranslucencyLightingMode.TLM_SURFACE)
  if name=='Sea':
   code='float coast=3200-220*sin(P.x*.00075)-150*cos(P.x*.0013+.5);float d=P.y-coast;float wave=sin(d*.033-T*1.8+sin(P.x*.004)*.7);float foam=pow(saturate(wave),18)*saturate(1-abs(d-400)/650);return lerp(float3(.12,.35,.36),float3(.95,.98,.94),foam*.88);'
   normal='return normalize(float3(.12*cos(P.x*.009+P.y*.005-T*1.3),.15*cos(P.y*.012-T*1.8+sin(P.x*.006)),1));'
   wpo='return float3(0,0,3.2*sin(P.y*.013-T*1.8+sin(P.x*.004)) + 1.4*sin(P.x*.011+P.y*.008-T*.9));'
  else:
   code='float w=.5+.5*sin(P.x*.012+P.y*.008-T*.65);return lerp(float3(.12,.32,.27),float3(.20,.42,.34),w*.4);'
   normal='return normalize(float3(.055*cos(P.x*.012+P.y*.005-T*.65),.06*cos(P.y*.013-T*.8),1));'
   wpo='return float3(0,0,.8*sin(P.x*.008+P.y*.009-T*.7));'
  color=custom(mat,code,inputs=inputs);output(color,'',mat,u.MaterialProperty.MP_BASE_COLOR)
  output(mul(mat,color,value=.18),'',mat,u.MaterialProperty.MP_EMISSIVE_COLOR)
  output(custom(mat,normal,inputs=inputs),'',mat,u.MaterialProperty.MP_NORMAL)
  output(custom(mat,wpo,inputs=inputs),'',mat,u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
  output(scalar(mat,.62 if name=='Sea' else .50),'',mat,u.MaterialProperty.MP_OPACITY)
  output(scalar(mat,.38),'',mat,u.MaterialProperty.MP_ROUGHNESS);output(scalar(mat,.22),'',mat,u.MaterialProperty.MP_SPECULAR)
 elif name=='Foam':
  prop(mat,'blend_mode',u.BlendMode.BLEND_MASKED);prop(mat,'opacity_mask_clip_value',.34)
  output(vector(mat,(.95,.99,.94,1)),'',mat,u.MaterialProperty.MP_BASE_COLOR)
  output(vector(mat,(.15,.16,.15,1)),'',mat,u.MaterialProperty.MP_EMISSIVE_COLOR)
  output(scalar(mat,.82),'',mat,u.MaterialProperty.MP_ROUGHNESS)
  output(custom(mat,'return .58+.42*sin(P.x*.035+sin(P.y*.018)-T*1.5);','float1',inputs),'',mat,u.MaterialProperty.MP_OPACITY_MASK)
  output(custom(mat,'return float3(0,22*sin(T*.9+P.x*.006),5+2*sin(P.y*.013-T*1.8));',inputs=inputs),'',mat,u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
 elif name=='Terrain':
  vertex=expr(mat,u.MaterialExpressionVertexColor);output(vertex,'',mat,u.MaterialProperty.MP_BASE_COLOR)
  caustic=custom(mat,'float ocean=saturate((-34-P.z)/80);float2 q=(P.xy-float2(-1500,-800))/float2(1200,950);float lake=saturate((1-dot(q,q))*5)*saturate((100-P.z)/35);float mask=max(ocean,lake);float v=abs(sin(P.x*.025+sin(P.y*.018+T*.55))+sin(P.y*.023-T*.65));float c=pow(saturate(1-v*.8),9)*mask;return Base*.035+c*float3(.30,.43,.29);',inputs={'P':p,'T':t,'Base':vertex})
  output(caustic,'',mat,u.MaterialProperty.MP_EMISSIVE_COLOR);output(scalar(mat,.86),'',mat,u.MaterialProperty.MP_ROUGHNESS)
 finish(mat);report['materials'][name]={'time_node':True,'world_position':True,'artistic_approximation':True,'expressions':ml.get_num_material_expressions(mat)}
 return mat
try:
 assert levels.load_level('/Game/Maps/ultra')
 tasks=[]
 for name in ['Bark','Canopy','Stone','Wood']:
  task=u.AssetImportTask();prop(task,'filename',str(OUT/'Generated'/(name+'.png')));prop(task,'destination_path',ASSET+'/Textures');prop(task,'destination_name','T_'+name);prop(task,'automated',True);prop(task,'replace_existing',True);prop(task,'save',True);tasks.append(task)
 assettools.import_asset_tasks(tasks)
 textures={}
 for name in ['Bark','Canopy','Stone','Wood']:
  tex=eas.load_asset(ASSET+'/Textures/T_'+name);assert tex
  prop(tex,'srgb',True);prop(tex,'mip_gen_settings',u.TextureMipGenSettings.TMGS_NO_MIPMAPS);prop(tex,'never_stream',True)
  eas.save_loaded_asset(tex);textures[name]=tex;report['textures'][name]={'asset':tex.get_path_name(),'source':str(OUT/'Generated'/(name+'.png')),'size':[tex.blueprint_get_size_x(),tex.blueprint_get_size_y()],'mips':'NoMipmaps; original NPOT dimensions retained'}
 mapping={}
 for name,c in DATA['palette'].items():
  surface='Bark' if name in ['Bark','BarkLight'] else 'Canopy' if name.startswith(('Leaf','Pine')) or name in ['Grass','Fern','Stem'] else 'Stone' if name.startswith('Rock') else 'Wood' if name in ['Wood','Endgrain','ReedHead'] else None
  if surface:mapping[name]=texture_material(name,c,textures[surface])
 for name in ['Sea','Lake','Foam','Terrain']:mapping[name]=animated_material(name)
 for name in DATA['palette']:
  if name not in mapping:mapping[name]=eas.load_asset(ASSET+'/Materials/M_'+name)
 # Import in bounded batches and persist so a failed run can resume safely.
 records=UV['meshes']
 for offset in range(0,len(records),50):
  batch=[]
  for record in records[offset:offset+50]:
   name=record['variant'];path=ASSET+'/Meshes/UV/'+name
   if eas.does_asset_exist(path):continue
   task=u.AssetImportTask();prop(task,'filename',str(OUT/'SourceArt'/(name+'.fbx')));prop(task,'destination_path',ASSET+'/Meshes/UV');prop(task,'destination_name',name);prop(task,'automated',True);prop(task,'replace_existing',True);prop(task,'save',False)
   options=u.FbxImportUI();prop(options,'import_mesh',True);prop(options,'import_as_skeletal',False);prop(options,'import_materials',False);prop(options,'import_textures',False);prop(options,'import_animations',False);prop(options,'automated_import_should_detect_type',False);prop(options,'mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH)
   md=options.static_mesh_import_data;prop(md,'combine_meshes',True);prop(md,'auto_generate_collision',False);prop(md,'generate_lightmap_u_vs',False);prop(md,'normal_import_method',u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
   prop(task,'options',options);prop(task,'factory',u.FbxFactory());batch.append(task)
  if batch:assettools.import_asset_tasks(batch)
  for record in records[offset:offset+50]:
   mesh=eas.load_asset(ASSET+'/Meshes/UV/'+record['variant']);assert mesh
   for i,m in enumerate(record['materials']):mesh.set_material(i,mapping[m])
   settings=meshed.get_lod_build_settings(mesh,0);prop(settings,'use_full_precision_u_vs',True);meshed.set_lod_build_settings(mesh,0,settings)
   body=mesh.get_editor_property('body_setup')
   if record['source'].startswith(('SM_Broadleaf','SM_Pine')) or record['collision']=='complex':prop(body,'collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
   elif record['collision']=='simple':meshed.remove_collisions(mesh);meshed.add_simple_collisions(mesh,u.ScriptingCollisionShapeType.NDOP26)
   eas.save_loaded_asset(mesh);report['mesh_count']+=1
  u.log('ULTRA_TEXTURE_IMPORT '+str(offset+len(records[offset:offset+50])))
 by_index={r['placement_index']:r for r in records}
 for actor in actors.get_all_level_actors():
  if not isinstance(actor,u.StaticMeshActor):continue
  old=actor.static_mesh_component.static_mesh
  try:index=int(actor.get_actor_label().split()[-1])
  except ValueError:continue
  if index not in by_index:continue
  record=by_index[index];loc=actor.get_actor_location();rot=actor.get_actor_rotation();scale=actor.get_actor_scale3d()
  if '_UV_' not in old.get_name():assert max(abs(a-b) for a,b in zip([scale.x,scale.y,scale.z],record['baked_world_scale']))<1e-4
  actor.static_mesh_component.set_static_mesh(eas.load_asset(ASSET+'/Meshes/UV/'+record['variant']));actor.set_actor_scale3d(u.Vector(1,1,1))
  report['actors'].append({'label':actor.get_actor_label(),'mesh':record['variant'],'position_cm':[loc.x,loc.y,loc.z],'rotation':[rot.pitch,rot.yaw,rot.roll],'actor_scale':[1,1,1]})
 assert len(report['actors'])==len(records)
 assert levels.save_current_level();eas.save_directory(ASSET,only_if_is_dirty=True,recursive=True)
 report['success']=True;report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 (OUT/'build_result.json').write_text(json.dumps(report,indent=2));u.log('ULTRA_TEXTURE_BUILD_SUCCESS')
except Exception:
 report['success']=False;report['error']=traceback.format_exc();(OUT/'build_result.json').write_text(json.dumps(report,indent=2));raise
finally:u.SystemLibrary.quit_editor()
