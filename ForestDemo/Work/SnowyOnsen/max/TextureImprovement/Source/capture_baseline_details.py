import sys,json,unreal as u
from pathlib import Path
sys.path.insert(0,r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max/TextureImprovement/Source')
import capture_views as c
assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(c.MAP)
c.capture(before=True)
