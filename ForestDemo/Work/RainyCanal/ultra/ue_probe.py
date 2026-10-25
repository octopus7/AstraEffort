import unreal,json,traceback
from pathlib import Path
P=Path('D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra')
try:
    result={'project':unreal.Paths.get_project_file_path()}
    for name in ['EditorLevelLibrary','EditorLevelUtils','UnrealEditorSubsystem','LevelEditorSubsystem','EditorActorSubsystem','MaterialEditingLibrary','StaticMeshEditorSubsystem','AutomationLibrary','RenderingLibrary','KismetSystemLibrary']:
        obj=getattr(unreal,name,None)
        if obj:result[name]=[x for x in dir(obj) if any(w in x.lower() for w in ('play','world','collision','level','screenshot','render','vertex','uv_channel','material_usage','connection','trace'))]
    for name in ['request_play_session','request_end_play_map','is_in_play_in_editor','load_level','new_level','save_current_level']:
        m=getattr(unreal.LevelEditorSubsystem,name,None)
        if m:result['level_'+name]=m.__doc__
    for obj,name in [(unreal.EditorLevelLibrary,'editor_play_simulate'),(unreal.RenderingLibrary,'export_render_target'),(unreal.RenderingLibrary,'create_render_target2d'),(unreal.MaterialEditingLibrary,'connect_material_expressions'),(unreal.EditorLevelLibrary,'editor_end_play'),(unreal.SystemLibrary,'line_trace_single'),(unreal.GameplayStatics,'get_player_pawn')]:
        m=getattr(obj,name,None)
        if m:result['doc_'+name]=m.__doc__
    (P/'Execution/probe.json').write_text(json.dumps(result,indent=2))
except Exception:
    (P/'Execution/probe_error.txt').write_text(traceback.format_exc())
    raise
