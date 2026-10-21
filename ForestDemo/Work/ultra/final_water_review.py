import unreal as u, runpy, json, datetime
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra')
try:
 ns=runpy.run_path(str(ROOT/'build_level.py'),init_globals={'SKIP_BUILD':True})
 for name in ['Lake','Sea']:ns['create_mat'](name,ns['DATA']['palette'][name])
 ns['levels'].load_level('/Game/Maps/ultra');ns['levels'].save_current_level()
 (ROOT/'scene_ready_time.json').write_text(json.dumps({'scene_saved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'changes':'Calm water material rebuilt without unsupported ripple graph; final validated lighting, transforms and collision unchanged.'},indent=2))
 u.log('ULTRA_FINAL_WATER_SAVED')
 runpy.run_path(str(ROOT/'review_pipeline.py'))
except Exception:
 import traceback
 (ROOT/'final_review_error.txt').write_text(traceback.format_exc())
 u.SystemLibrary.quit_editor()
 raise
