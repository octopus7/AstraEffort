import unreal, json
from pathlib import Path
names=['FbxImportUI','FbxStaticMeshImportData','EditorLevelLibrary','StaticMeshEditorSubsystem','AssetRegistryDependencyOptions','SceneCaptureComponent2D','RenderingLibrary','PostProcessSettings','EditorLoadingAndSavingUtils','SystemLibrary','WorldSettings','SkyLightComponent']
out={n:getattr(unreal,n).__doc__ for n in names}
for c,n in [('RenderingLibrary','create_render_target2d'),('RenderingLibrary','export_render_target'),('EditorLevelLibrary','new_level'),('StaticMeshEditorSubsystem','set_collision_complexity'),('SystemLibrary','line_trace_single')]:
 out[c+'.'+n]=str(getattr(getattr(unreal,c),n,None).__doc__)
Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/unreal_api_probe.json').write_text(json.dumps(out,indent=2))
unreal.log('ULTRA_PROBE_OK')
