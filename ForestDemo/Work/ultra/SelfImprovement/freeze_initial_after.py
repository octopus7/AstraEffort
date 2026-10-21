import hashlib,json,datetime,shutil
from pathlib import Path
out=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement');target=out/'initial_after_evidence_hashes.json'
assert not target.exists(),'Initial After evidence already frozen'
rows=[]
for p in sorted((out/'Screenshots/After').glob('*')):
 if p.is_file():rows.append({'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
target.write_text(json.dumps({'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'Preserve initial source-default palette evidence during supervisor-requested parameter-only color harmonization.','files':rows},indent=2))
archive=out/'InitialValidation';archive.mkdir(exist_ok=True)
for name in ['validation.json','runtime_validation.json','render_analysis.json','visual_review.json','file_audit.json','RESULT.md','completion_summary.json']:
 shutil.copy2(out/name,archive/name)
print('Frozen '+str(len(rows))+' initial After files; initial validation records preserved.')
