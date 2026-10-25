import sys
sys.path.insert(0,'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra')
from ue_common import *
try:
    import ue_capture_pipeline
    ue_capture_pipeline.start('Screenshots',True)
except Exception as e:fail(e,'final_init');raise
