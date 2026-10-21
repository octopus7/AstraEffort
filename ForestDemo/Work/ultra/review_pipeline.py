import runpy
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra')
runpy.run_path(str(ROOT/'validate_level.py'),init_globals={'KEEP_EDITOR_OPEN':True})
runpy.run_path(str(ROOT/'capture_level.py'),init_globals={'RUN_RUNTIME_VALIDATION':True})
