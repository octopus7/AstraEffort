import sys,traceback
from pathlib import Path
P=Path('D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra');sys.path.insert(0,str(P))
try:
    import assemble,capture
    assemble.build()
    capture.start('draft')
except Exception:
    (P/'Execution/build4_error.txt').write_text(traceback.format_exc());raise
