import sys
sys.path.insert(0,'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass')
sys.path.insert(0,'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra')
from ue_common import *
try:
    import capture_vegetation
    capture_vegetation.start()
except Exception as e:
    fail(e,'VegetationPass/capture');u.SystemLibrary.quit_editor()
