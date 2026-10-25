"""Measure isolated, four-thread Blender processes for this theme only."""
from pathlib import Path
from datetime import datetime, timezone
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
BLENDER = Path('C:/Program Files/Blender Foundation/Blender 4.5/blender.exe')
phase = sys.argv[1]
if phase == 'build':
    script = ROOT / 'build.py'
    args = []
elif phase == 'fix_loader':
    script = ROOT / 'build.py'
    args = ['--', '--asset', 'wheel_loader']
elif phase == 'verify':
    script = ROOT.parent / '_tools' / 'verify_theme.py'
    args = ['--', str(ROOT), str(ROOT / 'validation_export.json')]
else:
    raise ValueError(phase)
command = [str(BLENDER), '--background', '--threads', '4', '--python-exit-code', '1', '--python', str(script), *args]
t0 = time.perf_counter()
started = datetime.now(timezone.utc).isoformat()
with (ROOT / f'{phase}.log').open('w', encoding='utf-8') as log:
    result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT, check=False)
record = {'phase': phase, 'started_at_utc': started, 'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'elapsed_seconds': time.perf_counter() - t0, 'exit_code': result.returncode, 'threads': 4, 'command': command}
(ROOT / f'{phase}_process.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record), flush=True)
raise SystemExit(result.returncode)

