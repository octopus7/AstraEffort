"""Local process wrapper; captures actual subprocess exit codes and elapsed time."""
from pathlib import Path
from datetime import datetime, timezone
import json, subprocess, sys, time

ROOT = Path(__file__).resolve().parent
BLENDER = 'C:/Program Files/Blender Foundation/Blender 4.5/blender.exe'
kind = sys.argv[1]
command = [BLENDER, '--background', '--factory-startup', '--threads', '4', '--python-exit-code', '1']
if kind == 'fix_build':
    command += ['--python', str(ROOT / 'build.py'), '--', '--asset', 'fire_engine']
elif kind == 'final_validation':
    command += ['--python', str(ROOT.parent / '_tools' / 'verify_theme.py'), '--', str(ROOT), str(ROOT / 'validation_export.json')]
else:
    raise ValueError(kind)
started = datetime.now(timezone.utc).isoformat()
t0 = time.perf_counter()
with (ROOT / (kind + '.log')).open('w', encoding='utf-8') as out, (ROOT / (kind + '_stderr.log')).open('w', encoding='utf-8') as err:
    result = subprocess.run(command, stdout=out, stderr=err, creationflags=subprocess.CREATE_NO_WINDOW)
record = dict(started_at_utc=started, finished_at_utc=datetime.now(timezone.utc).isoformat(),
              elapsed_seconds=time.perf_counter()-t0, exit_code=result.returncode,
              threads=4, command=command)
(ROOT / (kind + '_process.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record))
raise SystemExit(result.returncode)
