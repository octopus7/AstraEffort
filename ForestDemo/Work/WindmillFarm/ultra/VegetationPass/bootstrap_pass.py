from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
PASS=Path(__file__).resolve().parent;ROOT=PASS.parent;REPO=ROOT.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=PASS/'Before';before.mkdir(parents=True,exist_ok=False)
pub=json.loads((ROOT/'publication.json').read_text())
scratch=REPO/'ForestDemo/Saved/Workers/WindmillFarm/ultra/VegetationBefore/Content'
for r in pub['files']:
    source=Path(r['destination']);assert sha(source)==r['sha256'],str(source)
    dest=scratch/r['relative_path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
for name in ('RESULT.md','STATUS.json','publication.json','validation.json','visual_review.json','render_analysis.json','timings.json','ue_assemble.py','ue_common.py','ue_capture_pipeline.py','landscape_design.py'):
    shutil.copy2(ROOT/name,before/name)
shutil.copytree(ROOT/'Screenshots',before/'Screenshots',ignore=shutil.ignore_patterns('Draft','Polish'))
status={'theme':'WindmillFarm','effort':'ultra','status':'working','started_at_utc':'2026-10-22T13:57:19+00:00','started_at_kst':'2026-10-22T22:57:19+09:00','timing_note':'First explicit clock reading for this follow-up; initial inspection preceded this timestamp.','finished_at_utc':None,'map':'/Game/Maps/WindmillFarm_ultra','phase':'Original tall meadow and corn source production','blockers':[],'requirements':['Separate populated corn cultivation area','Tall meadow grass clusters reduce empty plains','Both types visibly sway in wind','Preserve four original fields and primary routes']}
(PASS/'STATUS.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
root=json.loads((ROOT/'STATUS.json').read_text());root['status']='working';root['phase']='Vegetation follow-up: tall meadow, separate corn field and anchored wind';root['follow_up']='VegetationPass/STATUS.json'
(ROOT/'STATUS.json').write_text(json.dumps(root,indent=2),encoding='utf-8')
print('Baseline packages/evidence preserved, source hashes matched:',len(pub['files']))
