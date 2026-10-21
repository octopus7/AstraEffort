"""Publish only 10 validated owned tree assets and ultra.umap after supervisor integration."""
import json,hashlib,shutil,datetime,re
from pathlib import Path
root=Path(r'D:/github/AstraEffort/ForestDemo');out=root/'Work/ultra/SelfImprovement';scratch=root/'Saved/Workers/ultra/SelfImprovement/ForestDemo'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for filename in ['validation.json','runtime_validation.json','render_analysis.json','native_code_review.json','file_audit.json','final_palette_validation.json','final_render_analysis.json']:
 assert json.loads((out/filename).read_text(encoding='utf-8-sig'))['success'],filename+' not passed'
timing=json.loads((out/'Execution/ue-final-palette.json').read_text(encoding='utf-8-sig'));assert timing['exit_code']==0
proposal=json.loads((out/'IntegrationProposal/manifest.json').read_text())
integration=[]
for item in proposal['files']:
 p=root/item['path'];assert p.is_file(), 'Supervisor integration missing: '+str(p)
 assert digest(p)==item['sha256'],'Integrated plugin differs: '+str(p)
 integration.append({'path':item['path'],'sha256':digest(p)})
renderer_values=[];section=''
for line in (root/'Config/DefaultEngine.ini').read_text(encoding='utf-8-sig').splitlines():
 line=line.strip()
 if line.startswith('['):section=line
 elif section=='[/Script/Engine.RendererSettings]' and line.lower().startswith('r.customdepth='):renderer_values.append(line.split('=',1)[1].strip())
assert renderer_values and renderer_values[-1]=='3','Shared stencil mode not enabled'
dll=root/'Plugins/ForestUltraTrees/Binaries/Win64/UnrealEditor-ForestUltraTrees.dll';assert dll.is_file(),'Shared plugin build missing'
descriptor=json.loads((root/'ForestDemo.uproject').read_text());assert not any(p.get('Name')=='ForestUltraTrees' and not p.get('Enabled',True) for p in descriptor.get('Plugins',[]))
baseline=json.loads((out/'baseline_content_hashes.json').read_text())
for item in baseline['files']:
 p=Path(item['path']);assert p.is_file() and digest(p)==item['sha256'],'Shared owned baseline changed before publish: '+str(p)
audit=json.loads((out/'file_audit.json').read_text());rows=[]
assert len(audit['final_deliverables'])==11
for item in audit['final_deliverables']:
 rel=item['relative_path'];assert rel=='Content/Maps/ultra.umap' or rel.startswith('Content/Forest/ultra/AnimeTree/')
 src=scratch/rel;dst=root/rel;assert src.is_file() and digest(src)==item['sha256']
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert digest(dst)==item['sha256']
 rows.append(dict(item,destination=str(dst)))
report={'published_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'success':True,'files':rows,'supervisor_plugin_files_verified':integration,'shared_plugin_dll':str(dll),'shared_plugin_dll_sha256':digest(dll),'shared_stencil_mode':3,'private_editor_closed_before_publish':True,'private_editor_completion_evidence':'Execution/ue-final-palette.json','worker_shared_code_edits':False,'git_operations':False}
(out/'publication.json').write_text(json.dumps(report,indent=2));print(json.dumps({'success':True,'published_files':len(rows)}))
