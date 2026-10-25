"""Save a built-in generation into the authorized set and update the ledger."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,shutil
p=argparse.ArgumentParser();p.add_argument('set');p.add_argument('slug');p.add_argument('source');p.add_argument('started');p.add_argument('finished');a=p.parse_args()
ROOT=Path(__file__).resolve().parents[2]
state_path=ROOT/'Blender/SET_BATCH_STATE.json';state=json.loads(state_path.read_text(encoding='utf-8'))
unit=state['sets'][a.set];assert a.slug in {x['slug'] for x in unit['assets']}
folder=ROOT/'REF'/a.set;destination=folder/(a.slug+'.png');assert not destination.exists(),str(destination)
source=Path(a.source);assert source.is_file()
shutil.copy2(source,destination)
parse=lambda value:datetime.strptime(value,'%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=timezone.utc)
started,finished=parse(a.started),parse(a.finished)
record={'asset':a.slug,'method':'built-in image_gen; main only; sequential','started_at_utc':started.isoformat(),'finished_at_utc':finished.isoformat(),'elapsed_seconds':(finished-started).total_seconds(),'source':str(source),'image':destination.name,'prompt':a.slug+'.prompt.txt','sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'review_status':'deferred_by_user'}
manifest_path=folder/'generation_manifest.json'
manifest=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {'set':a.set,'method':'four sequential main-only built-in image generations','records':[]}
assert a.slug not in {x['asset'] for x in manifest['records']}
manifest['records'].append(record)
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
local=ROOT/'Blender'/a.set/'REF';local.mkdir(parents=True,exist_ok=True)
for name in (destination.name,a.slug+'.prompt.txt','generation_manifest.json','.gitattributes'):
    origin=folder/name
    if origin.is_file():
        target=local/name
        if target.exists() and name!='generation_manifest.json':
            assert target.read_bytes()==origin.read_bytes(),f'Conflicting local reference: {target}'
        else:shutil.copy2(origin,target)
unit['reference_count']=len(manifest['records']);unit['status']='references_ready' if len(manifest['records'])==4 else 'generating_references'
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'saved':str(destination),'set_copy':str(local/destination.name),'reference_count':unit['reference_count'],'elapsed_seconds':record['elapsed_seconds']},indent=2))
