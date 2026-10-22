"""Publish only the exact privately validated owned packages, after UE exit."""
import datetime,hashlib,json,runpy,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[3];P=ROOT/'Saved/Workers/MountainStation/ultra/Project'
def read(n):return json.loads((R/n).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
package=runpy.run_path(str(R/'package_state.py'));record=package['confirm']();assert record['validated'];package['baseline_check']()
for name in ['uv_validation.json','improvement_geometry_validation.json','allocation_validation.json','Runtime/native_and_ramp.json','Runtime/changed_routes.json','visual_review.json']:
    assert read(name)['passed'],name
runtime=read('Runtime/validation.json');assert runtime['passed']
validation=read('validation.json');assert validation['world_partition'] is None and not validation['foreign_game_dependencies'] and validation['force_no_precomputed_lighting']
capture=read('Screenshots/after_final/capture_manifest.json');assert capture['passed'] and capture['packages_unchanged_after_capture']
assert capture['validated_package_manifest_sha256']==sha(R/'validated_packages.json')
before=read('Screenshots/before_fixed/capture_manifest.json')
assert before['passed']
for key in ['resolution','exposure','actual_cvars','capture_source']:assert before[key]==capture[key],key
assert len(capture['captures'])==len(before['captures'])==6
for b,a in zip(before['captures'],capture['captures']):
    for key in ['name','location','rotation','projection','horizontal_fov','ortho_width_cm','actual_projection','actual_fov','actual_ortho_width']:
        assert b.get(key)==a.get(key),(a['name'],key)
    assert sha(R/'Screenshots/after_final'/(a['name']+'.png'))==a['sha256']
    assert sha(R/'Screenshots/before_fixed'/(b['name']+'.png'))==b['sha256']
# Query only command lines of UE processes; no other worker assets are read.
command="Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'UnrealEditor*' } | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
out=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,check=True).stdout.strip()
processes=json.loads(out) if out else [];processes=processes if isinstance(processes,list) else [processes]
assert not any(str(P).replace('\\','/').lower() in (x.get('CommandLine') or '').replace('\\','/').lower() for x in processes),'Private UE still running'
allowed='Content/MountainStation/ultra/'
for row in record['files']:
    rel=row['relative_path'];assert rel.startswith(allowed) or rel=='Content/Maps/MountainStation_ultra.umap'
    src=P/rel;dst=ROOT/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert sha(dst)==row['sha256']
expected={x['relative_path'] for x in record['files']}
actual={x.relative_to(ROOT).as_posix() for x in (ROOT/'Content/MountainStation/ultra').rglob('*.uasset')}|{'Content/Maps/MountainStation_ultra.umap'}
assert actual==expected,'Unexpected published owned packages'
package['confirm']();package['baseline_check']()
result={'published_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'private_editor_closed':True,'package_count':len(record['files']),'validated_manifest_sha256':sha(R/'validated_packages.json'),'capture_manifest_sha256':sha(R/'Screenshots/after_final/capture_manifest.json'),'same_camera_settings_verified':True,'files':record['files']}
(R/'publication_manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'published_packages':len(record['files']),'passed':True}))
