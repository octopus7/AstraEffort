import sys
sys.path.insert(0,'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra')
from ue_common import *
try:
    import ue_assemble
    ue_assemble.run()
    save_json('build_success.json',{'utc':utc(),'map':MAP,'assembly_rhi':'D3D12SM5'})
except Exception as e:fail(e,'assembly_gpu');raise
