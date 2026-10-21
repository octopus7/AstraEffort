import unreal as u,sys,traceback,json
from pathlib import Path
from datetime import datetime,timezone
W=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh/TexturePass');sys.path.insert(0,str(W))
u.EditorPythonScripting.set_keep_python_script_alive(True)
try:
 assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Maps/MountainStation_xhigh')
 import runtime_validate
 runtime_validate.start()
except Exception:
 (W/'Evidence/runtime_bootstrap_error.json').write_text(json.dumps({'at_utc':datetime.now(timezone.utc).isoformat(),'error':traceback.format_exc()},indent=2));u.SystemLibrary.quit_editor()
