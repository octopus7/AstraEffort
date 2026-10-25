import runpy,traceback
ns=runpy.run_path(r'D:/github/AstraEffort/ForestDemo/Work/DesertVillage/max/Scripts/build_unreal.py',run_name='desert_helpers');globals().update(ns)
try:
    if not levels.load_level(MAP):raise RuntimeError('Final saved map reload failed')
    result=validate();result['fresh_read_only_final_session']=True;record('saved_map_validation.json',result)
except Exception:
    record('final_verify_error.json',{'at_utc':utc(),'error':traceback.format_exc()});u.log_error(traceback.format_exc())
finally:u.SystemLibrary.quit_editor()
