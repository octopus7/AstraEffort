from pathlib import Path
import json,re,hashlib
ROOT=Path(r'D:/github/AstraEffort');W=ROOT/'ForestDemo/Work/DesertVillage/max'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=(W/'RESULT.md').read_text(encoding='utf-8');links=re.findall(r'\]\(([^)]+)\)',report)
missing=[x for x in links if not (W/x).is_file()];assert not missing,missing
delivery=read(W/'Validation/delivery_manifest.json')
for f in delivery['files']:assert sha(ROOT/f['path'])==f['sha256'],f['path']
v=read(W/'Validation/final_verification.json');assert sha(W/'RESULT.md')==v['result_sha256'];assert sha(W/'STATUS.json')==v['status_sha256']
assert read(W/'STATUS.json')['status']=='ready_for_review'
for p in ['saved_map_validation.json','uv_density_validation.json','fbx_geometry_validation.json','capture_validation.json']:assert read(W/'Validation'/p)['passed'],p
print(json.dumps({'report_local_links':len(links),'missing_links':missing,'published_files_rehashed':len(delivery['files']),'result_sha256':v['result_sha256'],'all_checks':True},indent=2))
