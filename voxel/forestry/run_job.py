"""Run only this theme's Blender build/verification with recorded process timing."""
from pathlib import Path
from datetime import datetime, timezone
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
BLENDER = r'C:/Program Files/Blender Foundation/Blender 4.5/blender.exe'
kind = sys.argv[1]
if kind == 'build':
    args = [BLENDER, '--background', '--factory-startup', '--threads', '4', '--python-exit-code', '1', '--python', str(ROOT / 'build.py')]
elif kind == 'verify':
    args = [BLENDER, '--background', '--factory-startup', '--threads', '4', '--python-exit-code', '1', '--python', str(ROOT.parent / '_tools' / 'verify_theme.py'), '--', str(ROOT), str(ROOT / 'validation_export.json')]
else:
    raise ValueError(kind)
started = datetime.now(timezone.utc)
t0 = time.perf_counter()
with (ROOT / (kind + '.log')).open('w', encoding='utf-8') as log_file:
    result = subprocess.run(args, stdout=log_file, stderr=subprocess.STDOUT, check=False)
finished = datetime.now(timezone.utc)
data = {'kind': kind, 'command': args, 'started_at_utc': started.isoformat(), 'finished_at_utc': finished.isoformat(), 'elapsed_seconds': time.perf_counter()-t0, 'exit_code': result.returncode, 'threads': 4}
(ROOT / (kind + '_process.json')).write_text(json.dumps(data, indent=2), encoding='utf-8')
print(json.dumps(data, indent=2), flush=True)
raise SystemExit(result.returncode)
