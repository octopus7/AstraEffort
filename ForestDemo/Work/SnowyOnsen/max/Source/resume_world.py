import sys,traceback
sys.path.insert(0,r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max/Source')
import build_unreal as b
try:
 meshes={i['name']:b.u.load_asset(b.ASSET+'/Meshes/'+i['name']) for i in b.manifest['meshes']}
 assert all(meshes.values())
 b.make_world(meshes);b.validate();b.capture()
except Exception:
 b.dump('build_error.json',{'at_utc':b.now(),'traceback':traceback.format_exc()});b.u.log_error(traceback.format_exc());b.u.SystemLibrary.quit_editor()
