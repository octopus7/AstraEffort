import sys
sys.path.insert(0,'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra')
from ue_common import *
try:
    import ue_import,ue_assemble
    ue_import.run()
    ue_assemble.run()
    save_json('build_success.json',{'utc':utc(),'map':MAP})
except Exception as e:fail(e,'build');raise
