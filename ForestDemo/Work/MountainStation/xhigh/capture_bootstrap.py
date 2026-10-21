import unreal, traceback
from pathlib import Path
work=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh')
try:
 unreal.EditorPythonScripting.set_keep_python_script_alive(True)
 exec(compile((work/'refine_look.py').read_text(),str(work/'refine_look.py'),'exec'),globals())
 exec(compile((work/'capture_scene.py').read_text(),str(work/'capture_scene.py'),'exec'),globals())
except Exception:
 (work/'Evidence/capture_bootstrap_error.txt').write_text(traceback.format_exc())
 unreal.log_error(traceback.format_exc())
 unreal.SystemLibrary.quit_editor()
