import unreal as u,json,traceback,datetime
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high/TexturePass';BASE='/Game/MountainStation/high';MAP='/Game/Maps/MountainStation_high'
try:
 lib=u.EditorAssetLibrary;level=u.get_editor_subsystem(u.LevelEditorSubsystem);assert level.load_level(MAP)
 palette=json.load(open('D:/github/AstraEffort/ForestDemo/Work/MountainStation/high/Source/source_manifest.json'))['palette']
 changes=[]
 for name,weight in {'Grass':.10,'Hill':.10,'Leaf':.24,'LeafLight':.24,'Flower':.24}.items():
  m=lib.load_asset(BASE+'/Materials/M_'+name);root=u.MaterialEditingLibrary.get_material_property_input_node(m,u.MaterialProperty.MP_BASE_COLOR)
  inputs=u.MaterialEditingLibrary.get_inputs_for_material_expression(m,root);alphas=[x for x in inputs if isinstance(x,u.MaterialExpressionConstant)];assert len(alphas)==1
  previous=alphas[0].r;alphas[0].r=weight;u.MaterialEditingLibrary.recompile_material(m);lib.save_loaded_asset(m);changes.append({'material':m.get_path_name(),'previous_weight':previous,'generated_weight':weight})
 path=BASE+'/Materials/M_PresentationGround';m=lib.load_asset(path)
 if not m:m=u.AssetToolsHelpers.get_asset_tools().create_asset('M_PresentationGround',BASE+'/Materials',u.Material,u.MaterialFactoryNew())
 u.MaterialEditingLibrary.delete_all_material_expressions(m)
 c=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant3Vector,-300,0);c.constant=u.LinearColor(*palette['StoneLight'],1);u.MaterialEditingLibrary.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
 r=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant,-300,150);r.r=.72;u.MaterialEditingLibrary.connect_material_property(r,'',u.MaterialProperty.MP_ROUGHNESS);m.set_editor_property('two_sided',True);u.MaterialEditingLibrary.recompile_material(m);lib.save_loaded_asset(m)
 ground=next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='PresentationGround');old=ground.static_mesh_component.get_material(0).get_path_name();ground.static_mesh_component.set_material(0,m)
 level.save_current_level();lib.save_directory(BASE,only_if_is_dirty=False,recursive=True)
 json.dump({'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'root_cause':'PresentationGround engine plane reused StoneLight, which acquired a generated stone texture at plane UV scale. Split its unchanged constant palette into a dedicated material. Foliage contrast also reduced without changing UVs or textures.','background_previous_material':old,'background_material':m.get_path_name(),'background_color':palette['StoneLight'],'changes':changes},open(W+'/refinement_evidence.json','w'),indent=2)
 u.log('TEXTUREPASS_REFINEMENT_COMPLETE')
except Exception:
 open(W+'/refinement_error.txt','w').write(traceback.format_exc());u.log_error(traceback.format_exc())
finally:u.SystemLibrary.quit_editor()
