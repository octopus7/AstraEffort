"""Parent-only acceptance record after personally viewing every primary preview."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,hashlib
p=argparse.ArgumentParser();p.add_argument('theme');p.add_argument('--worker',required=True);p.add_argument('--next');p.add_argument('--confirm-primary-inspected',action='store_true');a=p.parse_args()
assert a.confirm_primary_inspected,'Parent must first personally inspect every primary image'
root=Path(__file__).resolve().parents[1];v=json.loads((root/'validation'/f'{a.theme}.json').read_text(encoding='utf-8'));assert v['passed']
images=[]
for r in v['records']:
    d=root/a.theme/'assets'/r['asset']/r['variant']
    for filename,digest in r['sha256'].items():assert hashlib.sha256((d/filename).read_bytes()).hexdigest()==digest,f'changed {d/filename}'
    images.append({'path':str((d/'preview.png').relative_to(root)).replace('\\','/'),'sha256':r['sha256']['preview.png']})
status=json.loads((root/a.theme/'STATUS.json').read_text(encoding='utf-8-sig'));assert status['status']=='ready_for_review'
assert (root/a.theme/'RESULT.md').is_file()
record={'theme':a.theme,'accepted':True,'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'reviewer':'main','all_primary_images_personally_inspected':True,'images':images,'independent_validation':str(Path('validation')/(a.theme+'.json')),'asset_count':v['asset_count'],'variant_count':v['variant_count']}
(root/'validation'/f'{a.theme}_visual_review.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
c=json.loads((root/'coordination.json').read_text(encoding='utf-8'))
if a.theme not in c['accepted']:c['accepted'].append(a.theme)
c['active'][a.worker]=a.next;c['review_notes'][a.theme]=f'Accepted after all {v["variant_count"]} primary renders personally inspected and fresh native/BLEND/GLB/FBX validation passed; hashes frozen.'
(root/'coordination.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'accepted':a.theme,'next':a.next,'images_reviewed':len(images)},ensure_ascii=False))
