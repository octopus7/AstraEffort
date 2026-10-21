import runpy,json,unreal as u
from pathlib import Path
p=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement')
runpy.run_path(str(p/'validate_level.py'),init_globals={'KEEP_EDITOR_OPEN':True})
runpy.run_path(str(p/'validate_final_palette.py'))
if json.loads((p/'validation.json').read_text())['success']:runpy.run_path(str(p/'capture_final.py'))
else:u.SystemLibrary.quit_editor()
