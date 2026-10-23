"""Read-only baseline hash checks; writes only this pass's new evidence."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
BASE=Path(r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max');PASS=BASE/'TextureImprovement'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
 archive=BASE/'FirstDelivery';m=read(archive/'archive_manifest.json');rows=[]
 for rec in m['evidence_files']:
  rel=rec['relative_path'];expected=rec['sha256'].lower();p=archive/rel
  assert p.is_file() and p.stat().st_size==rec['bytes'] and sha(p)==expected,str(p)
  active=BASE/rel;check_active=rel not in ['RESULT.md','STATUS.json']
  if check_active:assert active.is_file() and active.stat().st_size==rec['bytes'] and sha(active)==expected,str(active)
  rows.append({'relative_path':rel,'archived_match':True,'active_match':True if check_active else 'authorized active report/status append'})
 content=Path(m['content_snapshot']);cr=[]
 for rec in m['asset_files']:
  p=content/rec['relative_path'];assert p.is_file() and p.stat().st_size==rec['bytes'] and sha(p)==rec['sha256'].lower(),str(p)
  cr.append({'relative_path':rec['relative_path'],'match':True})
 result={'at_utc':datetime.now(timezone.utc).isoformat(),'baseline_commit':m['baseline_commit'],'archive_manifest_sha256':sha(archive/'archive_manifest.json'),'archived_work_files':len(rows),'active_immutable_work_files':len(rows)-2,'archived_content_files':len(cr),'all_match':True,'work_files':rows,'content_files':cr}
 (PASS/'Validation/baseline_preservation.json').write_text(json.dumps(result,indent=2),encoding='utf8')
 print(json.dumps({k:v for k,v in result.items() if k not in ['work_files','content_files']}),flush=True)
 return result
if __name__=='__main__':run()
