import unreal as u,json,time,traceback
from pathlib import Path
from datetime import datetime,timezone
W=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh/TexturePass');R='/Game/MountainStation/xhigh';start=time.time()
report={'started_at_utc':datetime.now(timezone.utc).isoformat(),'texture_bindings':{},'imports':[]}
try:
 u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
 assets=u.AssetToolsHelpers.get_asset_tools();textures={}
 for name in ['Wood','Mineral','PaintedMetal','Foliage']:
  task=u.AssetImportTask();task.filename=str(W/'Textures'/(name+'.png'));task.destination_path=R+'/Textures';task.destination_name='T_'+name;task.automated=True;task.replace_existing=True;task.save=True;assets.import_asset_tasks([task])
  tex=u.load_asset(R+'/Textures/T_'+name);assert tex
  tex.set_editor_property('srgb',False);tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_MASKS)
  tex.set_editor_property('mip_gen_settings',u.TextureMipGenSettings.TMGS_NO_MIPMAPS);tex.set_editor_property('never_stream',True)
  tex.set_editor_property('address_x',u.TextureAddress.TA_WRAP);tex.set_editor_property('address_y',u.TextureAddress.TA_WRAP)
  u.EditorAssetLibrary.save_loaded_asset(tex);textures[name]=tex
 families={'Wood':['Timber','Wood','Cargo'],'Mineral':['Rock','RockLight','Ballast','Trail','Paving','EdgeStone','Plaster','Earth'],'PaintedMetal':['Roof','RoofSeam','Metal','Rail','Red'],'Foliage':['Pine','PineLight','Bush','Grass','GrassLight']}
 palette=json.loads((W.parent/'SourceArt/palette.json').read_text());lib=u.MaterialEditingLibrary
 for family,names in families.items():
  for name in names:
   mat=u.load_asset(R+'/Materials/M_'+name);lib.delete_all_material_expressions(mat)
   def node(cls,x,y):return lib.create_material_expression(mat,cls,x,y)
   def link(a,out,b,inp):assert lib.connect_material_expressions(a,out,b,inp)
   def scalar(value,x,y):n=node(u.MaterialExpressionConstant,x,y);n.r=value;return n
   uv=node(u.MaterialExpressionTextureCoordinate,-800,-100);uv.coordinate_index=0;uv.u_tiling=1;uv.v_tiling=1
   sample=node(u.MaterialExpressionTextureSample,-600,-100);sample.texture=textures[family];sample.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_MASKS;link(uv,'',sample,'UVs')
   amp={'Wood':.8,'Mineral':.55,'PaintedMetal':.35,'Foliage':.4}[family]
   mul=node(u.MaterialExpressionMultiply,-380,-100);link(sample,'R',mul,'A');link(scalar(amp,-600,180),'',mul,'B')
   add=node(u.MaterialExpressionAdd,-170,-100);link(mul,'',add,'A');link(scalar(1-.5*amp,-380,190),'',add,'B')
   tint=node(u.MaterialExpressionConstant3Vector,-170,150);tint.constant=u.LinearColor(*palette[name],1)
   color=node(u.MaterialExpressionMultiply,60,-100);link(add,'',color,'A');link(tint,'',color,'B');assert lib.connect_material_property(color,'',u.MaterialProperty.MP_BASE_COLOR)
   rm=node(u.MaterialExpressionMultiply,-380,370);link(sample,'R',rm,'A');link(scalar(.16,-600,490),'',rm,'B')
   ra=node(u.MaterialExpressionAdd,-100,370);link(rm,'',ra,'A');link(scalar((.35 if name in ['Rail','Metal'] else .78)-.08,-380,520),'',ra,'B');assert lib.connect_material_property(ra,'',u.MaterialProperty.MP_ROUGHNESS)
   mat.set_editor_property('two_sided',True);lib.recompile_material(mat);u.EditorAssetLibrary.save_loaded_asset(mat)
   report['texture_bindings'][name]={'texture':textures[family].get_path_name(),'family':family,'uv_channel':0,'uv_multiplier':1,'base_color':'palette * (1 - amplitude/2 + texture.R * amplitude)','amplitude':amp,'roughness':'baseline - 0.08 + texture.R * 0.16'}
 report['solid_exceptions']={'Glass':'Existing solid blue glass','Cream':'Lettering, clock face, safety line and small light surfaces preserve readability','Amber':'Small warm hardware/detail','Dark':'Closed tunnel end','Flowers':'Small colored blossoms','Backdrop':'Engine-sphere unlit backdrop'}
 editor=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
 for fbx in sorted((W/'SourceArt').glob('*.fbx')):
  task=u.AssetImportTask();task.filename=str(fbx);task.destination_path=R+'/Meshes';task.destination_name='SM_'+fbx.stem;task.automated=True;task.replace_existing=True;task.save=True
  opt=u.FbxImportUI();opt.import_mesh=True;opt.import_materials=False;opt.import_textures=False;opt.import_as_skeletal=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.automated_import_should_detect_type=False
  data=opt.static_mesh_import_data;data.combine_meshes=True;data.auto_generate_collision=False;data.generate_lightmap_u_vs=False;data.convert_scene=True;data.convert_scene_unit=True;data.import_uniform_scale=1;task.options=opt;assets.import_asset_tasks([task])
  mesh=u.load_asset(R+'/Meshes/SM_'+fbx.stem);assert mesh
  for i,slot in enumerate(mesh.static_materials):mesh.set_material(i,u.load_asset(R+'/Materials/M_'+str(slot.material_slot_name).split('.')[0]))
  body=mesh.get_editor_property('body_setup');body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);body.set_editor_property('double_sided_geometry',True)
  settings=editor.get_lod_build_settings(mesh,0);settings.set_editor_property('use_full_precision_u_vs',True);settings.set_editor_property('generate_lightmap_u_vs',False);editor.set_lod_build_settings(mesh,0,settings)
  u.EditorAssetLibrary.save_loaded_asset(mesh);report['imports'].append(mesh.get_path_name());print('TEXTURE_IMPORT',fbx.stem)
 u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Maps/MountainStation_xhigh')
 for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
  if a.get_actor_label()=='Sun_Afternoon':a.light_component.set_editor_property('forward_shading_priority',1)
  if a.get_actor_label()=='Sky_BroadFill':a.light_component.set_editor_property('forward_shading_priority',0)
 u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level();u.EditorAssetLibrary.save_directory(R)
 docs={}
 for cls,methods in {'GeometryScript_AssetUtils':['copy_mesh_from_static_mesh_v2'],'GeometryScript_MeshQueries':['get_triangle_positions','get_triangle_u_vs','get_all_triangle_i_ds','get_mesh_volume_area'],'GeometryScript_ListUtilityFunctions':['convert_index_list_to_array'],'GeometryScript_Materials':['get_all_triangle_material_i_ds'],'MaterialEditingLibrary':['get_used_textures','get_inputs_for_material_expression','get_material_property_input_node'],'Texture2D':['blueprint_get_size_x','blueprint_get_size_y']}.items():
  obj=getattr(u,cls,None);docs[cls]={'exists':obj is not None,'matching_names':[s for s in dir(obj) if any(x in s for x in ['triangle','uv','index_list','used_texture','property_input'])] if obj else []}
  for method in methods:docs[cls][method]=str(getattr(obj,method,None).__doc__)
 (W/'Evidence/ue_api_probe.json').write_text(json.dumps(docs,indent=2))
 report['success']=True;report['finished_at_utc']=datetime.now(timezone.utc).isoformat();report['elapsed_seconds']=time.time()-start
except Exception:
 report['success']=False;report['exception']=traceback.format_exc();u.log_error(report['exception'])
(W/'Evidence/build_textures.json').write_text(json.dumps(report,indent=2));print('TEXTURE_BUILD',report['success']);u.SystemLibrary.quit_editor()
