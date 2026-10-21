import unreal as u,json,os,traceback,datetime,time
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high/TexturePass';BASE='/Game/MountainStation/high';MAP='/Game/Maps/MountainStation_high'
start=time.time();lib=u.EditorAssetLibrary;at=u.AssetToolsHelpers.get_asset_tools();ms=u.get_editor_subsystem(u.StaticMeshEditorSubsystem);level=u.get_editor_subsystem(u.LevelEditorSubsystem)
try:
 u.EditorPythonScripting.set_keep_python_script_alive(True);level.load_level(MAP)
 world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();u.SystemLibrary.execute_console_command(world,'Interchange.FeatureFlags.Import.FBX 0')
 manifest=json.load(open(W+'/imagegen_manifest.json'));source=json.load(open(W+'/source_uv_validation.json'));tasks=[]
 for row in source['meshes']:
  task=u.AssetImportTask();task.filename=W+'/FBX/'+row['name']+'.fbx';task.destination_path=BASE+'/Meshes';task.destination_name=row['name'];task.automated=True;task.replace_existing=True;task.save=True
  opt=u.FbxImportUI();opt.import_mesh=True;opt.import_materials=False;opt.import_textures=False;opt.import_as_skeletal=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
  sd=opt.static_mesh_import_data;sd.combine_meshes=True;sd.auto_generate_collision=False;sd.generate_lightmap_u_vs=False
  task.options=opt;tasks.append(task)
 at.import_asset_tasks(tasks)
 tex={};texrecords=[]
 for row in manifest['calls']:
  t=u.AssetImportTask();t.filename=row['workspace_path'];t.destination_path=BASE+'/Textures';t.destination_name='T_'+row['id'];t.automated=True;t.replace_existing=True;t.save=True;at.import_asset_tasks([t])
  texture=lib.load_asset(BASE+'/Textures/T_'+row['id']);texture.set_editor_property('srgb',True);texture.set_editor_property('mip_gen_settings',u.TextureMipGenSettings.TMGS_NO_MIPMAPS);texture.set_editor_property('address_x',u.TextureAddress.TA_WRAP);texture.set_editor_property('address_y',u.TextureAddress.TA_WRAP);lib.save_loaded_asset(texture);tex[row['id']]=texture
  texrecords.append({'id':row['id'],'path':texture.get_path_name(),'size':[texture.blueprint_get_size_x(),texture.blueprint_get_size_y()],'original_sha256':row['sha256'],'mips':'NoMipmaps; preserve exact non-power-of-two original output and source density'})
 palette=json.load(open('D:/github/AstraEffort/ForestDemo/Work/MountainStation/high/Source/source_manifest.json'))['palette'];palette['Leather']=palette['Ochre']
 links=[]
 for textureid,names in manifest['mapping'].items():
  row=next(x for x in manifest['calls'] if x['id']==textureid)
  for name in names:
   path=BASE+'/Materials/M_'+name;m=lib.load_asset(path)
   if not m:m=at.create_asset('M_'+name,BASE+'/Materials',u.Material,u.MaterialFactoryNew())
   u.MaterialEditingLibrary.delete_all_material_expressions(m)
   expr=lambda cls,x,y:u.MaterialEditingLibrary.create_material_expression(m,cls,x,y)
   sample=expr(u.MaterialExpressionTextureSample,-650,0);sample.texture=tex[textureid]
   tc=expr(u.MaterialExpressionTextureCoordinate,-900,0);tc.coordinate_index=0;tc.u_tiling=1.;tc.v_tiling=1.;u.MaterialEditingLibrary.connect_material_expressions(tc,'',sample,'Coordinates')
   scale=expr(u.MaterialExpressionConstant3Vector,-650,200);scale.constant=u.LinearColor(*[palette[name][i]/max(.01,row['mean_linear_rgb'][i]) for i in range(3)],1)
   mult=expr(u.MaterialExpressionMultiply,-350,0);u.MaterialEditingLibrary.connect_material_expressions(sample,'RGB',mult,'A');u.MaterialEditingLibrary.connect_material_expressions(scale,'',mult,'B')
   base=expr(u.MaterialExpressionConstant3Vector,-350,200);base.constant=u.LinearColor(*palette[name],1)
   mix=expr(u.MaterialExpressionLinearInterpolate,-50,0);alpha=expr(u.MaterialExpressionConstant,-200,400);alpha.r=.72;u.MaterialEditingLibrary.connect_material_expressions(alpha,'',mix,'Alpha');u.MaterialEditingLibrary.connect_material_expressions(base,'',mix,'A');u.MaterialEditingLibrary.connect_material_expressions(mult,'',mix,'B');u.MaterialEditingLibrary.connect_material_property(mix,'',u.MaterialProperty.MP_BASE_COLOR)
   rough=expr(u.MaterialExpressionConstant,-50,200);rough.r=.3 if name=='Rail' else .72;u.MaterialEditingLibrary.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
   if name=='Rail':
    metal=expr(u.MaterialExpressionConstant,-50,300);metal.r=.65;u.MaterialEditingLibrary.connect_material_property(metal,'',u.MaterialProperty.MP_METALLIC)
   m.set_editor_property('two_sided',True);u.MaterialEditingLibrary.recompile_material(m);lib.save_loaded_asset(m)
   links.append({'material':path,'texture':tex[textureid].get_path_name(),'uv_channel':0,'uv_multiplier':[1,1],'generated_weight':.72,'normalization':'per-channel generated-image mean to preserve original palette'})
 for row in source['meshes']:
  mesh=lib.load_asset(BASE+'/Meshes/'+row['name'])
  for i,slot in enumerate(mesh.get_editor_property('static_materials')):
   name=str(slot.material_slot_name).split('.')[0];mat=lib.load_asset(BASE+'/Materials/M_'+name)
   if mat:mesh.set_material(i,mat)
  settings=ms.get_lod_build_settings(mesh,0);settings.use_full_precision_u_vs=True;settings.generate_lightmap_u_vs=False;ms.set_lod_build_settings(mesh,0,settings)
  mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);lib.save_loaded_asset(mesh)
 level.save_current_level();lib.save_directory(BASE,only_if_is_dirty=False,recursive=True)
 json.dump({'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':time.time()-start,'textures':texrecords,'material_links':links,'mesh_count':len(source['meshes'])},open(W+'/import_evidence.json','w'),indent=2)
 u.log('TEXTUREPASS_IMPORT_COMPLETE')
except Exception:
 open(W+'/import_error.txt','w').write(traceback.format_exc());u.log_error(traceback.format_exc())
finally:u.SystemLibrary.quit_editor()
