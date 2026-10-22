import unreal as u,runpy,traceback
from pathlib import Path
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement')
try:
    assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Maps/MountainStation_ultra')
    runpy.run_path(str(R/'capture_views.py'),init_globals={'CAPTURE_PHASE':'after_final'})
except Exception:
    (R/'final_capture_error.txt').write_text(traceback.format_exc());u.SystemLibrary.quit_editor()
