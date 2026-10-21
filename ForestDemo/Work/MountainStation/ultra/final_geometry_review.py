import unreal as u,json,traceback
ROOT=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra';ASSET='/Game/MountainStation/ultra'
try:
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem);levels.load_level('/Game/Maps/MountainStation_ultra')
    for name in ['Fences','Lettering']:
        task=u.AssetImportTask();task.filename=ROOT+'/SourceArt/SM_'+name+'.fbx';task.destination_path=ASSET+'/Meshes';task.destination_name='SM_'+name;task.automated=True;task.replace_existing=True;task.save=True
        op=u.FbxImportUI();op.import_materials=False;op.import_textures=False;op.import_as_skeletal=False;op.automated_import_should_detect_type=False;op.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;op.static_mesh_import_data.combine_meshes=True;op.static_mesh_import_data.auto_generate_collision=False;op.static_mesh_import_data.convert_scene=False;op.static_mesh_import_data.convert_scene_unit=True;op.static_mesh_import_data.generate_lightmap_u_vs=False;task.options=op;task.factory=u.FbxFactory();u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        sm=u.load_asset(ASSET+'/Meshes/SM_'+name)
        for i,s in enumerate(sm.static_materials):sm.set_material(i,u.load_asset(ASSET+'/Materials/M_'+str(s.material_slot_name).split('.')[0]))
        sm.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);u.EditorAssetLibrary.save_loaded_asset(sm)
    levels.save_current_level()
    exec(compile(open(ROOT+'/run_review.py').read(),ROOT+'/run_review.py','exec'),globals())
except Exception:
    with open(ROOT+'/final_geometry_review_error.json','w') as f:json.dump({'traceback':traceback.format_exc()},f,indent=2)
    u.SystemLibrary.quit_editor()
