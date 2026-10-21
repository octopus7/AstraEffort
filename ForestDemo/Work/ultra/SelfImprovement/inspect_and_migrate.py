import runpy,json,unreal as u
from pathlib import Path
p=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement')
runpy.run_path(str(p/'inspect_tree.py'),init_globals={'KEEP_EDITOR_OPEN':True})
if json.loads((p/'source_tree_inspection.json').read_text())['success']:
 runpy.run_path(str(p/'migrate_replace.py'))
else:u.SystemLibrary.quit_editor()
