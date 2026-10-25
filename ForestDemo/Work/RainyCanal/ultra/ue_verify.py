import unreal,sys,traceback,time,json
from pathlib import Path
from datetime import datetime,timezone
P=Path('D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra');sys.path.insert(0,str(P));import validate
LEV=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);ED=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
STATE={'stage':0,'start':time.monotonic()}
def stop():
    unreal.unregister_slate_post_tick_callback(STATE['handle']);unreal.EditorPythonScripting.set_keep_python_script_alive(False);unreal.SystemLibrary.quit_editor()
def tick(dt):
    try:
        if time.monotonic()-STATE['start']<4:return
        if STATE['stage']==0:
            STATE['data']=validate.runtime(ED.get_game_world(),STATE['data']);LEV.editor_request_end_play();STATE['stage']=1;STATE['start']=time.monotonic();return
        STATE['data']['checks']['pie_ended']=not LEV.is_in_play_in_editor();STATE['data']['all_passed']=all(STATE['data']['checks'].values());STATE['data']['utc']=datetime.now(timezone.utc).isoformat();(P/'validation.json').write_text(json.dumps(STATE['data'],indent=2));stop()
    except Exception:
        (P/'Execution/verify_error.txt').write_text(traceback.format_exc());LEV.editor_request_end_play();stop()
try:
    assert LEV.load_level('/Game/Maps/RainyCanal_ultra')
    STATE['data']=validate.saved(ED.get_editor_world());(P/'Execution/static_validation.json').write_text(json.dumps(STATE['data'],indent=2));LEV.editor_request_begin_play();unreal.EditorPythonScripting.set_keep_python_script_alive(True);STATE['handle']=unreal.register_slate_post_tick_callback(tick)
except Exception:
    (P/'Execution/verify_error.txt').write_text(traceback.format_exc());raise
