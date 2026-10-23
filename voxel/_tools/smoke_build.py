from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from voxelkit import Grid,Asset,run_theme
g=Grid((128,64,64),[(0,0,0,0),(90,136,114,255),(218,199,163,255),(46,58,65,255)])
g.roundbox((4,4,4),(124,60,48),10,1).box((32,0,16),(96,16,40),0).cylinder((64,32,49),18,20,2,2)
g.cylinder((64,32,51),9,24,2,0).box((8,8,0),(20,20,8),3).box((108,44,0),(120,56,8),3)
run_theme(Path(__file__).resolve().parent/'smoke',[Asset('smoke','Utility test fixture',g)])
