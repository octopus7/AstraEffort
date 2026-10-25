import sys,traceback
from pathlib import Path
P=Path('D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra');sys.path.insert(0,str(P))
try:
    import assemble
    assemble.build()
except Exception:
    (P/'Execution/build3_error.txt').write_text(traceback.format_exc());raise
