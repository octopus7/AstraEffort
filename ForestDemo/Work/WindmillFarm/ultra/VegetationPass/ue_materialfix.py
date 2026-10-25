import sys
sys.path.insert(0,'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass')
import assemble_vegetation as av
from ue_common import *
try:
    for slot in ('CornLeaf','CornStalk','CornKernel','CornTassel','MeadowLeaf','MeadowStem','MeadowSeed'):
        av.wind_material(slot,u.load_asset(BASE+'/Textures/T_'+slot+'_BaseColor'))
    save_json('VegetationPass/material_fix.json',{'utc':utc(),'root_cause':'VertexColor expression first output has empty name, not RGB; previous connection returned false. Now assertions enforce all three inputs.','materials':7})
    u.SystemLibrary.quit_editor()
except Exception as e:
    fail(e,'VegetationPass/materialfix');u.SystemLibrary.quit_editor()
