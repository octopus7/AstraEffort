import unreal as u,json,time,datetime,os
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/TexturePass/UVRevision'; ROOT='/Game/MountainStation/medium/TexturePass/UVRevision'; MAP='/Game/Maps/MountainStation_medium'
L=u.get_editor_subsystem(u.LevelEditorSubsystem);E=u.get_editor_subsystem(u.EditorActorSubsystem);L.load_level(MAP)
tools=u.AssetToolsHelpers.get_asset_tools(); spec=json.load(open(W+'/source_uv_validation.json')); palette=json.load(open('D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/art_manifest.json'))['palette'];palette['bark']=[.36,.23,.14]
def import_asset(file,folder,name,options=None):
 t=u.AssetImportTask();t.filename=file;t.destination_path=folder;t.destination_name=name;t.automated=True;t.replace_existing=True;t.save=True
 if options:t.options=options
 tools.import_asset_tasks([t]);return [u.load_asset(p) for p in t.imported_object_paths]
tex=next(x for x in import_asset(W+'/Source/SurfaceAtlas.png',ROOT+'/Textures','T_SurfaceAtlas') if isinstance(x,u.Texture2D));tex.set_editor_property('srgb',True)
tex.set_editor_property('address_x',u.TextureAddress.TA_CLAMP);tex.set_editor_property('address_y',u.TextureAddress.TA_CLAMP)
materials={}; records=[]
for name,rgb in palette.items():
 path=ROOT+'/Materials/M_'+name
 m=u.load_asset(path) if u.EditorAssetLibrary.does_asset_exist(path) else tools.create_asset('M_'+name,ROOT+'/Materials',u.Material,u.MaterialFactoryNew())
 u.MaterialEditingLibrary.delete_all_material_expressions(m);m.set_editor_property('two_sided',True)
 def node(cls,x,y):return u.MaterialEditingLibrary.create_material_expression(m,cls,x,y)
 def link(a,out,b,inp):
  names=list(u.MaterialEditingLibrary.get_material_expression_input_names(b))
  if inp and inp not in names:inp=names[0]
  assert u.MaterialEditingLibrary.connect_material_expressions(a,out,b,inp),(str(b),names,inp)
 base=node(u.MaterialExpressionConstant3Vector,-700,100);base.set_editor_property('constant',u.LinearColor(*rgb,1))
 swatch=spec['mapping'].get(name)
 weight=.45
 if name in ['grass','edge','gold','white']:weight=.18
 if name in ['woodlight','bark']:weight=.60
 if swatch is not None:
  coord=node(u.MaterialExpressionTextureCoordinate,-1200,-300);coord.set_editor_property('coordinate_index',0)
  repeat=node(u.MaterialExpressionScalarParameter,-1400,-100);repeat.set_editor_property('parameter_name','PackedUVScale');repeat.set_editor_property('default_value',1.0);repeat.set_editor_property('use_custom_primitive_data',True);repeat.set_editor_property('primitive_data_index',0)
  metric=node(u.MaterialExpressionMultiply,-1200,-300);link(coord,'',metric,'A');link(repeat,'',metric,'B')
  frac=node(u.MaterialExpressionFrac,-1000,-300);link(metric,'',frac,'')
  scale=node(u.MaterialExpressionConstant2Vector,-1000,-100);scale.set_editor_property('r',spec['usable_swatch_px'][0]/spec['atlas_size'][0]);scale.set_editor_property('g',spec['usable_swatch_px'][1]/spec['atlas_size'][1])
  mul=node(u.MaterialExpressionMultiply,-800,-300);link(frac,'',mul,'A');link(scale,'',mul,'B')
  off=node(u.MaterialExpressionConstant2Vector,-800,-100);off.set_editor_property('r',((swatch%3)*(spec['atlas_size'][0]/3)+32)/spec['atlas_size'][0]);off.set_editor_property('g',((swatch//3)*(spec['atlas_size'][1]/2)+32)/spec['atlas_size'][1])
  add=node(u.MaterialExpressionAdd,-600,-300);link(mul,'',add,'A');link(off,'',add,'B')
  sample=node(u.MaterialExpressionTextureSample,-400,-300);sample.set_editor_property('texture',tex);link(add,'',sample,'Coordinates')
  lerp=node(u.MaterialExpressionLinearInterpolate,-100,0);lerp.set_editor_property('const_alpha',weight);link(base,'',lerp,'A');link(sample,'RGB',lerp,'B');u.MaterialEditingLibrary.connect_material_property(lerp,'',u.MaterialProperty.MP_BASE_COLOR)
 else:u.MaterialEditingLibrary.connect_material_property(base,'',u.MaterialProperty.MP_BASE_COLOR)
 rough=node(u.MaterialExpressionConstant,-100,250);rough.set_editor_property('r',.55 if name in ['metal','rail','roof'] else .82);u.MaterialEditingLibrary.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
 u.MaterialEditingLibrary.recompile_material(m);materials[name]=m;records.append({'material':path,'source_swatch':swatch,'texture_weight':weight if swatch is not None else 0,'expected_texture':tex.get_path_name() if swatch is not None else None})
opts=u.FbxImportUI();opts.import_mesh=True;opts.import_materials=False;opts.import_textures=False;opts.import_as_skeletal=False
opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.auto_generate_collision=False;opts.static_mesh_import_data.generate_lightmap_u_vs=False
mesh=next(x for x in import_asset(W+'/Source/AlderPass_UV.fbx',ROOT+'/Meshes','SM_AlderPass_UV',opts) if isinstance(x,u.StaticMesh))
slots=[]
for i,slot in enumerate(mesh.get_editor_property('static_materials')):
 name=str(slot.get_editor_property('imported_material_slot_name')); assert name in materials,name;mesh.set_material(i,materials[name]);slots.append({'slot':i,'name':name,'material':materials[name].get_path_name()})
body=mesh.get_editor_property('body_setup');body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);body.set_editor_property('double_sided_geometry',True)
sms=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
for i in range(mesh.get_num_sections(0)):sms.enable_section_collision(mesh,True,0,i)
bs=sms.get_lod_build_settings(mesh,0);bs.set_editor_property('use_full_precision_u_vs',True);bs.set_editor_property('generate_lightmap_u_vs',False);sms.set_lod_build_settings(mesh,0,bs)
for a in E.get_all_level_actors():
 if a.get_actor_label().startswith('Alder Pass |'):
  a.static_mesh_component.set_static_mesh(mesh);a.static_mesh_component.set_default_custom_primitive_data_float(0,1.0);a.static_mesh_component.set_collision_profile_name('BlockAll');a.set_actor_enable_collision(True)
 if a.get_actor_label()=='Quiet blue horizon':
  a.static_mesh_component.set_collision_profile_name('NoCollision');a.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);a.set_actor_enable_collision(False)
tree_mesh=next(x for x in import_asset(W+'/Source/PinePrototype.fbx',ROOT+'/Meshes','SM_PinePrototype',opts) if isinstance(x,u.StaticMesh))
for i,slot in enumerate(tree_mesh.get_editor_property('static_materials')):
 name=str(slot.get_editor_property('imported_material_slot_name'));tree_mesh.set_material(i,materials[name])
body=tree_mesh.get_editor_property('body_setup');body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);body.set_editor_property('double_sided_geometry',True)
for i in range(tree_mesh.get_num_sections(0)):sms.enable_section_collision(tree_mesh,True,0,i)
bs=sms.get_lod_build_settings(tree_mesh,0);bs.set_editor_property('use_full_precision_u_vs',True);bs.set_editor_property('generate_lightmap_u_vs',False);sms.set_lod_build_settings(tree_mesh,0,bs)
for a in E.get_all_level_actors():
 if a.get_actor_label().startswith('Shared Pine |'):E.destroy_actor(a)
instances=json.load(open(W+'/shared_source_validation.json'))['instances']
for i,record in enumerate(instances):
 a=E.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*[v*100 for v in record['location_m']]))
 a.set_actor_label('Shared Pine | '+str(i));a.static_mesh_component.set_static_mesh(tree_mesh);s=record['scale'];a.set_actor_scale3d(u.Vector(s,s,s));a.static_mesh_component.set_default_custom_primitive_data_float(0,s);a.static_mesh_component.set_collision_profile_name('BlockAll');a.set_actor_enable_collision(True)
json.dump({'mesh':tree_mesh.get_path_name(),'instance_count':len(instances),'instances':instances,'density_scaling':'Shared scalar parameter PackedUVScale reads custom primitive data 0 equal to uniform actor scale. UV density stays 128px/m.'},open(W+'/tree_instance_mapping.json','w'),indent=2)
u.EditorAssetLibrary.save_directory(ROOT,only_if_is_dirty=False,recursive=True);L.save_current_level();L.load_level(MAP)
json.dump({'saved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'texture':tex.get_path_name(),'materials':records,'slots':slots,'mesh':mesh.get_path_name(),'source_uv_channel':0,'full_precision_uv':True},open(W+'/material_mapping.json','w'),indent=2)
print('TEXTURE_PASS_APPLIED')




