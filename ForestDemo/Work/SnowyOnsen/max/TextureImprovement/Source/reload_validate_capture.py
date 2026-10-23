"""Fresh saved-map validation and actual captures; version executed by UE03."""
import sys,traceback
sys.dont_write_bytecode=True
sys.path.insert(0,r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max/TextureImprovement/Source')
import build_materials as m
try:m.validate_pass();m.capture_views.capture()
except Exception:
 m.b.dump('build_error.json',{'at_utc':m.b.now(),'traceback':traceback.format_exc()});m.u.log_error(traceback.format_exc());m.u.SystemLibrary.quit_editor()
