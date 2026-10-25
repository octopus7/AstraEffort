import sys,traceback
from pathlib import Path
ROOT=Path('D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra')
sys.path.insert(0,str(ROOT))
try:
    import assemble
    assemble.build()
except Exception:
    (ROOT/'Execution/build_error.txt').write_text(traceback.format_exc())
    raise
