from pathlib import Path
root=Path('D:/github/AstraEffort/ForestDemo/Work/high')
exec(compile((root/'finalize_scene.py').read_text(encoding='utf-8-sig'),str(root/'finalize_scene.py'),'exec'))
exec(compile((root/'validate_capture.py').read_text(encoding='utf-8-sig'),str(root/'validate_capture.py'),'exec'))
