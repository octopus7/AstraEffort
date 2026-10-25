"""Measure isolated four-thread Blender build or fresh independent verification."""
from pathlib import Path
from datetime import datetime, timezone
import os, sys, json, time, subprocess
ROOT = Path(__file__).resolve().parent
mode = sys.argv[1]
argv = ['C:/Program Files/Blender Foundation/Blender 4.5/blender.exe', '--background',
        '--factory-startup', '--threads', '4', '--python-exit-code', '1']
if mode == 'build':
    argv += ['--python', str(ROOT/'build.py')]
elif mode == 'validation':
    argv += ['--python', str(ROOT.parent/'_tools'/'verify_theme.py'), '--', str(ROOT), str(ROOT/'validation_export.json')]
elif mode == 'fix':
    argv += ['--python', str(ROOT/'build.py'), '--', '--asset', sys.argv[2]]
else:
    raise ValueError(mode)
tag = mode if mode != 'fix' else 'fix_' + sys.argv[2]
t0 = time.perf_counter()
start = datetime.now(timezone.utc).isoformat()
environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
with (ROOT/(tag+'.log')).open('w', encoding='utf-8') as out, (ROOT/(tag+'_stderr.log')).open('w', encoding='utf-8') as err:
    process = subprocess.run(argv, stdout=out, stderr=err, env=environment, creationflags=subprocess.CREATE_NO_WINDOW)
record = dict(started_at_utc=start, finished_at_utc=datetime.now(timezone.utc).isoformat(),
              elapsed_seconds=time.perf_counter()-t0, exit_code=process.returncode, threads=4, command=argv)
(ROOT/(tag+'_process.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record))
raise SystemExit(process.returncode)
