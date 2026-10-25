"""Finite isolated Blender jobs, writing their logs and process timing here only."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, subprocess, sys, time

root = Path(__file__).resolve().parent
mode = sys.argv[1]
exe = 'C:/Program Files/Blender Foundation/Blender 4.5/blender.exe'
command = [exe, '--background', '--factory-startup', '--threads', '4', '--python-exit-code', '1']
if mode == 'build':
    command += ['--python', str(root/'build.py')]
elif mode == 'verify':
    command += ['--python', str(root.parent/'_tools'/'verify_theme.py'), '--', str(root), str(root/'validation_export.json')]
else:
    raise ValueError(mode)
environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
started = datetime.now(timezone.utc).isoformat()
clock = time.perf_counter()
with (root/(mode+'.log')).open('w', encoding='utf-8') as output:
    completed = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, env=environment, check=False)
timing = dict(command=command, started_at_utc=started, finished_at_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.perf_counter()-clock, exit_code=completed.returncode, threads=4)
(root/(mode+'_process.json')).write_text(json.dumps(timing, indent=2), encoding='utf-8')
print(json.dumps(timing, indent=2), flush=True)
raise SystemExit(completed.returncode)
