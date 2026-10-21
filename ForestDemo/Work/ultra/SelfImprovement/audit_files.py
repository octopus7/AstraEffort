import json,hashlib,datetime,re
from pathlib import Path
root=Path(r'D:/github/AstraEffort/ForestDemo');out=root/'Work/ultra/SelfImprovement';scratch=root/'Saved/Workers/ultra/SelfImprovement/ForestDemo'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compare(rows,path_key='path',hash_key='sha256'):
 result=[]
 for r in rows:
  p=Path(r[path_key]);h=digest(p) if p.is_file() else None
  if h!=r[hash_key]:result.append({'path':str(p),'expected':r[hash_key],'actual':h})
 return result
report={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
prior=json.loads((out/'baseline_evidence_hashes.json').read_text());report['prior_evidence_files']=len(prior['files']);report['prior_evidence_differences']=compare(prior['files'])
provenance=json.loads((out/'source_provenance.json').read_text());report['source_asset_differences']=compare(provenance['assets'].values(),'source')
native=json.loads((out/'native_port_manifest.json').read_text());report['source_native_differences']=compare(provenance['native_sources'])
report['source_shader_sha256']=digest(Path(provenance['source_project'])/'Shaders/CanopyRim/CanopyRim.usf');report['source_shader_unchanged']=report['source_shader_sha256']==native['shader_sha256']
baseline=json.loads((out/'baseline_content_hashes.json').read_text());report['shared_baseline_content_differences']=compare(baseline['files'])
report['scratch_baseline_content_differences']=[]
for r in baseline['files']:
 p=Path(r['path']);q=scratch/p.relative_to(root)
 if q.is_file() and digest(q)!=r['sha256']:report['scratch_baseline_content_differences'].append(p.relative_to(root).as_posix())
report['scratch_only_map_changed_from_baseline']=report['scratch_baseline_content_differences']==['Content/Maps/ultra.umap']
files=sorted((scratch/'Content/Forest/ultra/AnimeTree').glob('*.uasset'))+[scratch/'Content/Maps/ultra.umap'];bad=[]
report['final_deliverables']=[]
for p in files:
 data=p.read_bytes();paths=set()
 for string in [data.decode('latin-1',errors='ignore'),data.decode('utf-16-le',errors='ignore')]:
  paths.update(re.findall(r'/Game/Environment/[A-Za-z0-9_/.]+|/Script/TunaSweeper[A-Za-z0-9_/.]*',string))
 if paths:bad.append({'file':str(p),'paths':sorted(paths)})
 report['final_deliverables'].append({'relative_path':str(p.relative_to(scratch)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':digest(p)})
report['raw_original_reference_hits']=bad
report['success']=not any(report[k] for k in ['prior_evidence_differences','source_asset_differences','source_native_differences','raw_original_reference_hits']) and report['source_shader_unchanged'] and report['scratch_only_map_changed_from_baseline']
report['initial_after_evidence_differences']=compare(json.loads((out/'initial_after_evidence_hashes.json').read_text())['files'])
report['success'] &= not report['initial_after_evidence_differences']
(out/'file_audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='final_deliverables'},indent=2))
