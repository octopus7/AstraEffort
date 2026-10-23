"""Final read-back verification and last worker-authored delivery timestamp."""
import sys,json,hashlib,re,ast
from pathlib import Path
from datetime import datetime,timezone,timedelta
sys.dont_write_bytecode=True
import check_preservation
B=Path(r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max');W=B/'TextureImprovement';V=W/'Validation'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o):p.write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
report_path=B/'RESULT.md';report=report_path.read_text(encoding='utf8')
needle='[최종 UV·기하 검사](TextureImprovement/Validation/uv_geometry_validation.json), [제작 원본]'
report=report.replace(needle,'[최종 UV·기하 검사](TextureImprovement/Validation/uv_geometry_validation.json), [독립 FBX·UV 검토](TextureImprovement/Evidence/independent_uv_review.json), [제작 원본]')
for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',report):
 if not link.startswith(('http:','https:','#')):assert (B/link).is_file(),link
for p in (W/'Source').glob('*.py'):ast.parse(p.read_text(encoding='utf8'),filename=str(p))
pub=read(V/'publication_sha256.json');assert len(pub['files'])==46
for r in pub['files']:assert sha(Path(r['private']))==sha(Path(r['published']))==r['published_sha256']
cap=read(W/'Screenshots/capture_manifest.json');assert len(cap['captures'])==8
for r in cap['captures']:assert sha(W/'Screenshots'/r['file'])==r['sha256']
preserved=check_preservation.run()
first=read(B/'FirstDelivery/STATUS.json');root=read(B/'STATUS.json')
for k,v in first.items():
 if k!='status':assert root[k]==v,('first delivery status field changed',k)
status=read(W/'STATUS.json');timing=read(V/'timing_summary.json');oldfinish=status['finished_at_utc'];oldkst=status['finished_at_kst'];oldelapsed=status['elapsed_seconds']
finish=datetime.now(timezone.utc);start=datetime.fromisoformat(status['started_at_utc']);elapsed=(finish-start).total_seconds();kst=finish.astimezone(timezone(timedelta(hours=9))).isoformat()
status.update(finished_at_utc=finish.isoformat(),finished_at_kst=kst,elapsed_seconds=elapsed)
timing.update(finished_at_utc=finish.isoformat(),elapsed_wall_seconds=elapsed)
root['texture_improvement']=status
report=report.replace(oldfinish,finish.isoformat()).replace(oldkst,kst).replace(f'**{oldelapsed:.3f}초**',f'**{elapsed:.3f}초**')
report_path.write_text(report,encoding='utf8');write(W/'STATUS.json',status);write(B/'STATUS.json',root);write(V/'timing_summary.json',timing)
checks={'at_utc':finish.isoformat(),'status':'passed','published_sha256_matches':46,'final_png_hash_matches':8,'first_delivery_archived_work_hash_matches':125,'first_delivery_immutable_active_hash_matches':123,'first_delivery_archived_content_hash_matches':43,'first_delivery_status_fields_preserved':True,'report_local_links_exist':True,'source_python_syntax_valid':True,'worker_files_frozen':True,'final_finish_utc':finish.isoformat(),'elapsed_seconds':elapsed}
write(V/'delivery_checks.json',checks)
manifest=V/'delivery_inventory.json';files=sorted(p for p in W.rglob('*') if p.is_file() and p!=manifest)+[report_path,B/'STATUS.json']
write(manifest,{'frozen_at_utc':finish.isoformat(),'worker':'/root/snowy_onsen_max_fast','status':'ready_for_review','files':[{'relative_to_work':p.relative_to(B).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files],'note':'Worker freezes listed files for parent independent review. Inventory excludes itself; parent may add its own review evidence.'})
print(json.dumps(checks,indent=2),flush=True)
