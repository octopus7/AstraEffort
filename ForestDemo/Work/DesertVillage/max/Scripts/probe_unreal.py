import unreal as u, json, traceback
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/DesertVillage/max')
out={}
try:
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    for clsname in ['LevelEditorSubsystem','AutomationLibrary','UnrealEditorSubsystem','AssetRegistryDependencyOptions','MaterialEditingLibrary','EditorLevelLibrary','World','StaticMesh','CameraComponent','PostProcessSettings','LevelEditorViewportSettings','LevelEditorViewportInstanceSettings']:
        cls=getattr(u,clsname,None)
        out[clsname]={'exists':bool(cls),'members':[m for m in dir(cls) if not m.startswith('_')]} if cls else None
    task=u.AssetImportTask();task.filename=str(ROOT/'SourceArt/FBX/SM_AxisProbe.fbx');task.destination_path='/Game/DesertVillage/max/Probe';task.destination_name='SM_AxisProbe';task.automated=True;task.replace_existing=True;task.save=True
    opt=u.FbxImportUI();opt.import_mesh=True;opt.import_materials=False;opt.import_textures=False;opt.import_as_skeletal=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.automated_import_should_detect_type=False
    opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.generate_lightmap_u_vs=False;opt.static_mesh_import_data.auto_generate_collision=False;opt.static_mesh_import_data.transform_vertex_to_absolute=True;opt.static_mesh_import_data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    task.options=opt;u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);out['imported_paths']=list(task.imported_object_paths)
    mesh=u.load_asset(task.imported_object_paths[0]);b=mesh.get_bounding_box();out['axis_probe']={'min':[b.min.x,b.min.y,b.min.z],'max':[b.max.x,b.max.y,b.max.z]}
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    for name in ['world_partition','world_settings','persistent_level']:
        try:out['world_'+name]=str(world.get_editor_property(name))
        except Exception as e:out['world_'+name]=str(e)
    for name in ['take_high_res_screenshot','set_scalability_quality_level_relative_to_max']:
        out['doc_'+name]=getattr(u.AutomationLibrary,name).__doc__
    for name in ['CameraComponent','LevelEditorViewportInstanceSettings']:
        out['doc_'+name]=getattr(u,name).__doc__
    out['success']=True
except Exception:
    out['error']=traceback.format_exc();u.log_error(out['error'])
finally:
    (ROOT/'Validation/unreal_probe.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    u.SystemLibrary.quit_editor()
