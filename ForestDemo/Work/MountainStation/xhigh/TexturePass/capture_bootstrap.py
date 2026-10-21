import unreal as u,traceback,json,sys
from pathlib import Path
from datetime import datetime,timezone
W=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh/TexturePass');sys.path.insert(0,str(W))
u.EditorPythonScripting.set_keep_python_script_alive(True)
try:
 exec((W/'validate_saved_textures.py').read_text(),{'__name__':'__main__'})
 exec((W/'capture_scene.py').read_text(),globals())
except Exception:
 (W/'Evidence/bootstrap_error.json').write_text(json.dumps({'at_utc':datetime.now(timezone.utc).isoformat(),'error':traceback.format_exc()},indent=2));u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
