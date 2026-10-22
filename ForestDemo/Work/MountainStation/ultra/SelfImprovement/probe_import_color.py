import unreal as u,json,traceback,datetime
from pathlib import Path
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement');A='/Game/MountainStation/ultra/Meshes'
record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
    ss=u.get_editor_subsystem(u.StaticMeshEditorSubsystem);sm=u.load_asset(A+'/SM_Footpath');imp=sm.get_editor_property('asset_import_data')
    record.update(before_option=str(imp.get_editor_property('vertex_color_import_option')),before_colors=ss.has_vertex_colors(sm))
    imp.set_editor_property('vertex_color_import_option',u.VertexColorImportOption.REPLACE);u.EditorAssetLibrary.save_loaded_asset(sm)
    task=u.AssetImportTask();task.filename=str(R/'SourceArt/SM_Footpath.fbx');task.destination_path=A;task.destination_name='SM_Footpath';task.automated=True;task.replace_existing=True;task.save=True
    opt=u.FbxImportUI();opt.import_materials=False;opt.import_textures=False;opt.import_as_skeletal=False;opt.automated_import_should_detect_type=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.static_mesh_import_data.vertex_color_import_option=u.VertexColorImportOption.REPLACE;task.options=opt;task.factory=u.FbxFactory()
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);sm=u.load_asset(A+'/SM_Footpath')
    record.update(after_option=str(sm.get_editor_property('asset_import_data').get_editor_property('vertex_color_import_option')),after_colors=ss.has_vertex_colors(sm))
except Exception:record['error']=traceback.format_exc()
(R/'color_import_probe.json').write_text(json.dumps(record,indent=2));u.SystemLibrary.quit_editor()
