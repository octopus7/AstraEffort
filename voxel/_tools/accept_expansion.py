"""Parent-only hash-frozen acceptance after actual primary image inspection."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,argparse
p=argparse.ArgumentParser();p.add_argument('theme');p.add_argument('--confirm-primary-inspected',action='store_true');a=p.parse_args()
assert a.confirm_primary_inspected
root=Path(__file__).resolve().parents[1];sp=root/'EXPANSION_STATE.json';state=json.loads(sp.read_text(encoding='utf-8'));u=state['units'][a.theme];d=root/u['root']
vpath=root/'validation'/('expansion_'+a.theme+'.json');v=json.loads(vpath.read_text(encoding='utf-8'));assert v['passed'] and set(r['asset'] for r in v['records'])==set(u['assets']);assert v['variant_count']==2*len(u['assets'])
status=json.loads((d/'STATUS.json').read_text(encoding='utf-8-sig'));assert status['status']=='ready_for_review';assert (d/'RESULT.md').is_file()
images=[]
for r in v['records']:
    folder=d/'assets'/r['asset']/r['variant']
    for name,h in r['sha256'].items():assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==h,str(folder/name)
    images.append({'path':(folder/'preview.png').relative_to(root).as_posix(),'sha256':r['sha256']['preview.png']})
out={'theme':a.theme,'root':u['root'],'accepted':True,'reviewer':'main','recorded_at_utc':datetime.now(timezone.utc).isoformat(),'all_primary_images_personally_inspected':True,'images':images,'asset_count':v['asset_count'],'variant_count':v['variant_count'],'validation':vpath.relative_to(root).as_posix()}
(root/'validation'/('expansion_'+a.theme+'_visual_review.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
if a.theme not in state['accepted']:state['accepted'].append(a.theme)
state['phase_a_complete']=all(t in state['accepted'] for t,x in state['units'].items() if x['phase']=='additions')
sp.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'accepted':a.theme,'images':len(images),'phase_a_complete':state['phase_a_complete']}))
