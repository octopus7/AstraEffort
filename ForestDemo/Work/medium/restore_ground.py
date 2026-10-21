import unreal as u,traceback,os
ROOT='D:/github/AstraEffort/ForestDemo/Work/medium'
try:
 u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
 t=u.AssetImportTask();t.filename=ROOT+'/Source/Ground.fbx';t.destination_path='/Game/Forest/medium/Meshes';t.destination_name='GroundSmooth';t.automated=True;t.save=True;t.replace_existing=True
 opt=u.FbxImportUI();opt.import_mesh=True;opt.import_materials=False;opt.import_textures=False;opt.import_as_skeletal=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.automated_import_should_detect_type=False;opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.vertex_color_import_option=u.VertexColorImportOption.REPLACE;t.options=opt
 u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);m=u.load_asset('/Game/Forest/medium/Meshes/GroundSmooth');assert m
 for i,slot in enumerate(m.static_materials):m.set_material(i,u.load_asset('/Game/Forest/medium/Materials/M_'+str(slot.material_slot_name).split('.')[0]))
 m.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);u.EditorAssetLibrary.save_loaded_asset(m)
 level=u.get_editor_subsystem(u.LevelEditorSubsystem);level.load_level('/Game/Maps/medium')
 ground=next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='Ground');ground.static_mesh_component.set_static_mesh(m);level.save_current_level()
 if u.EditorAssetLibrary.does_asset_exist('/Game/Forest/medium/Meshes/Ground'):u.EditorAssetLibrary.delete_asset('/Game/Forest/medium/Meshes/Ground')
 if u.EditorAssetLibrary.does_asset_exist('/Game/Forest/medium/Meshes/GroundPainted'):u.EditorAssetLibrary.delete_asset('/Game/Forest/medium/Meshes/GroundPainted')
 if u.EditorAssetLibrary.does_asset_exist('/Game/Forest/medium/Materials/M_Ground'):u.EditorAssetLibrary.delete_asset('/Game/Forest/medium/Materials/M_Ground')
 for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
  if isinstance(a,u.DirectionalLight):a.light_component.set_editor_property('forward_shading_priority',1 if a.get_actor_label()=='Warm afternoon sun' else 0)
 level.save_current_level()
 exec(open(ROOT+'/finish_scene.py').read(),globals())
except Exception:
 open(ROOT+'/capture_error.txt','w').write(traceback.format_exc());u.SystemLibrary.quit_editor()
