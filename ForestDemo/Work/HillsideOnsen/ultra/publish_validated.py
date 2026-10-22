"""Publish only this task's verified saved packages after its private UE exits."""
from pathlib import Path
import hashlib,json,shutil,subprocess
from datetime import datetime,timezone
BASE=Path('D:/github/AstraEffort/ForestDemo')
W=BASE/'Work/HillsideOnsen/ultra'
P=BASE/'Saved/Workers/HillsideOnsen/ultra/Project'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
validation=read(W/'Validation/engine_validation.json')
runtime=read(W/'Validation/runtime_walks.json')
capture=read(W/'Screenshots/capture_manifest.json')
visual=read(W/'Validation/visual_review.json')
packages=read(W/'Validation/validated_packages.json')
after=read(W/'Validation/after_capture_packages.json')
assert validation['passed'],validation.get('failures')
assert runtime['status']=='passed',runtime.get('blockers')
assert read(W/'Validation/effect_graphs.json')['passed']
assert capture['packages_unchanged'] and after['unchanged']
assert capture['packages_sha256']==packages['digest']
assert after['files']==packages['files']
assert visual['passed'] and visual['capture_manifest_sha256']==sha(W/'Screenshots/capture_manifest.json')
for required in ['overview','top_down','hot_spring','village_path','hot_spring_timed_04s','hot_spring_timed_08s']:
    entry=next(x for x in capture['views'] if x['name']==required)
    assert sha(W/'Screenshots'/entry['file'])==entry['sha256']
# Read process metadata only; never terminate another worker or any process.
query="Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'UnrealEditor*' -and $_.CommandLine -like '*Saved*Workers*HillsideOnsen*ultra*Project*ForestDemo.uproject*' } | Select-Object ProcessId,Name | ConvertTo-Json -Compress"
active=subprocess.run(['powershell','-NoProfile','-Command',query],capture_output=True,text=True,check=True).stdout.strip()
assert not active,'Private UE still active: '+active
allowed='Content/HillsideOnsen/ultra/'
for e in packages['files']:
    rel=e['path'];assert rel.startswith(allowed) or rel=='Content/Maps/HillsideOnsen_ultra.umap'
    src=P/rel;assert sha(src)==e['sha256'] and src.stat().st_size==e['bytes']
existing=list((BASE/allowed).rglob('*.uasset')) if (BASE/allowed).exists() else []
expected={e['path'] for e in packages['files']}
assert all(p.relative_to(BASE).as_posix() in expected for p in existing),'Unexpected stale owned package; inspect before publication'
for e in packages['files']:
    dest=BASE/e['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(P/e['path'],dest)
for e in packages['files']:assert sha(BASE/e['path'])==e['sha256']
report={'utc':datetime.now(timezone.utc).isoformat(),'passed':True,'private_editor_closed':True,'package_count':len(packages['files']),'capture_manifest_sha256':sha(W/'Screenshots/capture_manifest.json'),'source_manifest_sha256':sha(W/'scene_manifest.json'),'engine_validation_sha256':sha(W/'Validation/engine_validation.json'),'runtime_validation_sha256':sha(W/'Validation/runtime_walks.json'),'files':packages['files']}
(W/'publication_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'published_packages':len(packages['files']),'all_hashes_match':True,'map':'/Game/Maps/HillsideOnsen_ultra'}))
