"""Publish only after UE has exited and all recorded checks have been inspected."""
from pathlib import Path
import json,hashlib,struct,shutil,datetime
WORK=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra')
PROJECT=Path(r'D:/github/AstraEffort/ForestDemo/Saved/Workers/MountainStation/ultra/Project')
FINAL=Path(r'D:/github/AstraEffort/ForestDemo')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
v=json.loads((WORK/'validation.json').read_text(encoding='utf-8-sig'))
r=json.loads((WORK/'runtime_validation.json').read_text(encoding='utf-8-sig'))
inspection=json.loads((WORK/'visual_inspection.json').read_text(encoding='utf-8-sig'))
assert v['map_reloaded'] and not v['foreign_game_dependencies'] and 'invalidated' not in v
assert all(not p['initial_overlap'] for p in v['collision_samples'])
assert r['normal_shutdown'] and r['pie_world_count']>=1 and all(w['passed'] for w in r['worlds'])
assert r['map_sha256_before']==r['map_sha256_after']==digest(PROJECT/'Content/Maps/MountainStation_ultra.umap')
assert inspection['inspected_by_author'] is True
images=[]
for name in ['overview','top_down','platform','tracks']:
    p=WORK/'Screenshots'/f'{name}.png';raw=p.read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n'
    assert struct.unpack('>II',raw[16:24])==(1920,1080)
    assert digest(p)==inspection['sha256'][name]
    images.append({'name':p.name,'bytes':len(raw),'sha256':digest(p)})
content=PROJECT/'Content'
assert not any(content.rglob('*BuiltData*'))
assert not any(content.rglob('__ExternalActors__')) and not any(content.rglob('__ExternalObjects__'))
assert [p.name for p in (content/'Maps').iterdir()]==['MountainStation_ultra.umap']
source=content/'MountainStation'/'ultra';dest=FINAL/'Content'/'MountainStation'/'ultra'
items=[]
for p in sorted(source.rglob('*')):
    if not p.is_file():continue
    assert p.suffix=='.uasset'
    q=dest/p.relative_to(source);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    assert digest(p)==digest(q)
    items.append({'path':str(q.relative_to(FINAL)).replace('\\','/'),'bytes':q.stat().st_size,'sha256':digest(q)})
p=content/'Maps'/'MountainStation_ultra.umap';q=FINAL/'Content'/'Maps'/p.name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);assert digest(p)==digest(q)
items.append({'path':str(q.relative_to(FINAL)).replace('\\','/'),'bytes':q.stat().st_size,'sha256':digest(q)})
record={'published_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'map':'/Game/Maps/MountainStation_ultra','asset_files':len(items)-1,'total_bytes':sum(x['bytes'] for x in items),'external_packages':False,'built_data':False,'files':items,'screenshots':images}
(WORK/'publication_manifest.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k not in ['files','screenshots']}))
