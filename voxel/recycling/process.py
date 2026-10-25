"""Run this theme's isolated Blender tasks with actual process timing."""
from pathlib import Path
from datetime import datetime, timezone
import json
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
phase = sys.argv[1]
command = ['C:/Program Files/Blender Foundation/Blender 4.5/blender.exe', '--background', '--threads', '4', '--python-exit-code', '1']
if phase == 'build':
    command += ['--python', str(root / 'build.py')]
elif phase == 'verify':
    command += ['--python', str(root.parent / '_tools' / 'verify_theme.py'), '--', str(root), str(root / 'validation_export.json')]
else:
    raise ValueError('Unknown process phase')
t0 = time.perf_counter()
started = datetime.now(timezone.utc).isoformat()
with (root / f'{phase}.log').open('w', encoding='utf-8') as log:
    completed = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT, check=False)
result = {'phase': phase, 'started_at_utc': started, 'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'elapsed_seconds': time.perf_counter() - t0, 'exit_code': completed.returncode, 'command': command, 'threads': 4}
(root / f'{phase}_process.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result), flush=True)
raise SystemExit(completed.returncode)

