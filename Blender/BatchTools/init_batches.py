"""Initialize the authorized nine-set production ledger without overwrites."""
from pathlib import Path
from datetime import datetime,timezone
import json,re
ROOT=Path(__file__).resolve().parents[2]
plan=(ROOT/'Blender/SET_BATCH_PLAN.md').read_text(encoding='utf-8')
sets={}
for line in plan.splitlines():
    if not re.match(r'\| Set\d\d \|',line):continue
    name,theme,items=[x.strip() for x in line.strip('|').split('|')]
    assets=[]
    for entry in items.split(';'):
        slug,label=entry.strip().split(' \u2014 ',1)
        assets.append({'slug':slug,'label':label})
    sets[name]={'theme':theme,'assets':assets,'status':'awaiting_references','reference_count':0,'worker':None,'review_status':'deferred_by_user'}
assert len(sets)==9 and all(len(s['assets'])==4 for s in sets.values())
path=ROOT/'Blender/SET_BATCH_STATE.json'
assert not path.exists(), 'Ledger exists; resume it instead of overwriting'
state={'started_at_utc':datetime.now(timezone.utc).isoformat(),'status':'working','planned_sets':9,'planned_models':36,'current_batch':1,'model':'gpt-6-astra','reasoning_effort':'max','fast_setting':'No separately selectable tool field','review_policy':'Deferred by explicit user instruction; no visual or independent model validation','reference_policy':'Main only, built-in image_gen, one image per model, sequential calls','commit_policy':'Main commits after each completed group of three sets','voxel_completion_commit':'dcbaeb3','batches':[{'number':i+1,'sets':[f'Set{n:02d}' for n in range(3+i*3,6+i*3)],'status':'pending','commit':None} for i in range(3)],'sets':sets}
state['batches'][0]['status']='generating_references'
path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'sets':list(sets),'models':36,'state':str(path)},indent=2))
