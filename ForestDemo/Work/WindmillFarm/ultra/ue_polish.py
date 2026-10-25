import sys
sys.path.insert(0,'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra')
from ue_common import *
try:
    import ue_assemble,ue_capture_pipeline
    ue_assemble.run()
    ue_capture_pipeline.start('Screenshots/Polish',False)
except Exception as e:fail(e,'polish');raise
