import sys
sys.path.insert(0,'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass')
import assemble_vegetation
from ue_common import *
try:
    assemble_vegetation.run()
    u.SystemLibrary.quit_editor()
except Exception as e:
    fail(e,'VegetationPass/build')
    u.SystemLibrary.quit_editor()
