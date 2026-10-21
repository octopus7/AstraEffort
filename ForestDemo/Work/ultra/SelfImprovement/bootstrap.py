import json,hashlib,re,shutil,datetime
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo');WORK=ROOT/'Work/ultra';OUT=WORK/'SelfImprovement'
SOURCE=Path(r'D:/github/extraction_shooter/TunaSweeper');OLD=ROOT/'Saved/Workers/ultra/ForestDemo';NEW=ROOT/'Saved/Workers/ultra/SelfImprovement/ForestDemo'
OUT.mkdir(parents=True,exist_ok=True)
for d in ['Screenshots/Before','Screenshots/After','IntegrationProposal','Execution']: (OUT/d).mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
status={'theme':'Forest','effort':'ultra','phase':'self_improvement','status':'working','started_at_utc':'2026-10-21T15:30:53Z','started_at_kst':'2026-10-22T00:30:53+09:00','finished_at_utc':None,'elapsed_seconds':0,'map':'/Game/Maps/ultra','baseline_commit':'8a686096a17e6560bd8b08241746eef7606fa8e1','repository_baseline':'65f16249f1aacb3dee28b3c3f12b1c70b6207d63','validation':{'phase':'source dependency audit and isolated project preparation'},'blockers':[],'requires_native_integration':True}
if not (OUT/'STATUS.json').exists():(OUT/'STATUS.json').write_text(json.dumps(status,indent=2))
baseline=[]
for p in WORK.rglob('*'):
 if p.is_file() and not p.is_relative_to(OUT):baseline.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
(OUT/'baseline_evidence_hashes.json').write_text(json.dumps({'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':baseline},indent=2))
content=[p for p in (ROOT/'Content/Forest/ultra').rglob('*') if p.is_file()]+[ROOT/'Content/Maps/ultra.umap']
(OUT/'baseline_content_hashes.json').write_text(json.dumps({'files':[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in content]},indent=2))
NEW.mkdir(parents=True,exist_ok=True)
for d in ['Source','Config','Binaries']:shutil.copytree(OLD/d,NEW/d,dirs_exist_ok=True)
shutil.copy2(OLD/'ForestDemo.uproject',NEW/'ForestDemo.uproject')
shutil.copytree(ROOT/'Content/Forest/ultra',NEW/'Content/Forest/ultra',dirs_exist_ok=True)
(NEW/'Content/Maps').mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'Content/Maps/ultra.umap',NEW/'Content/Maps/ultra.umap')
# Preliminary raw serialized FName/path closure. UE AssetRegistry validates it next.
queue=['/Game/Environment/AnimeTree/BP_AnimeFoliageTree'];seen={};missing=[]
while queue:
 package=queue.pop()
 if package in seen:continue
 relative=package[len('/Game/'):]+'.uasset';p=SOURCE/'Content'/relative
 if not p.is_file():missing.append(package);continue
 raw=p.read_bytes();texts=[raw.decode('latin1'),raw.decode('utf-16-le',errors='ignore')]
 deps=sorted(set(x for text in texts for x in re.findall(r'/Game/[A-Za-z0-9_/-]+',text)))
 scripts=sorted(set(x for text in texts for x in re.findall(r'/Script/[A-Za-z0-9_.]+',text)))
 seen[package]={'source':str(p),'sha256':sha(p),'bytes':len(raw),'serialized_game_paths':deps,'serialized_script_paths':scripts}
 for dep in deps:
  if dep!=package and dep not in seen:queue.append(dep)
 dest=NEW/'Content'/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
source_files=[SOURCE/'Source/TunaSweeper/Public/Environment/TunaSweeperAnimeTreeActor.h',SOURCE/'Source/TunaSweeper/Private/Environment/TunaSweeperAnimeTreeActor.cpp']+list((SOURCE/'Source/CanopyRim').rglob('*'))+[SOURCE/'Shaders/CanopyRim/CanopyRim.usf']
manifest={'method':'Preliminary serialized-path closure, must be confirmed by UE AssetRegistry before final asset migration. Original source project is never launched or modified.','source_project':str(SOURCE),'assets':seen,'unresolved_raw_paths':missing,'native_sources':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in source_files if p.is_file()]}
(OUT/'source_provenance.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'baseline_evidence_files':len(baseline),'baseline_content_files':len(content),'source_assets':list(seen),'unresolved_raw_paths':missing,'private_project':str(NEW/'ForestDemo.uproject')},indent=2))
