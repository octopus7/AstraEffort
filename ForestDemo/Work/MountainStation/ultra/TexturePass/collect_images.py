from pathlib import Path
import json,hashlib,struct,shutil,datetime
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/TexturePass');O=R/'Images';O.mkdir(exist_ok=True)
S=Path(r'C:/Users/blendue/.codex/generated_images/01a15e6e-1907-7ff1-b13c-5a4a31875490')
names={'wood':'exec-0c828b0e-f45d-4f18-996f-8a33bda08241.png','stone':'exec-139a94c8-267e-4781-8d34-49588598c29d.png','bark':'exec-3578a549-89d3-41ac-a894-4068afddafd0.png','foliage':'exec-26de7ee3-f27f-4c5e-b886-ff173e24cf72.png','metal':'exec-9d46bd76-2efe-4386-913a-da49f64d6912.png'}
calls=json.loads((R/'imagegen_calls.json').read_text())['calls'];records=[]
for c in calls:
    p=S/names[c['name']];q=O/(c['name']+'.png');shutil.copy2(p,q);raw=q.read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n'
    c['original_file']=str(p);c['workspace_file']=str(q);c['sha256']=hashlib.sha256(raw).hexdigest();c['dimensions']=list(struct.unpack('>II',raw[16:24]));c['raw_file_unchanged']=p.read_bytes()==raw
    for key in ['started_at_utc','finished_at_utc']:c[key]=datetime.datetime.strptime(c[key],'%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=datetime.timezone.utc).isoformat()
    c['elapsed_seconds']=(datetime.datetime.fromisoformat(c['finished_at_utc'])-datetime.datetime.fromisoformat(c['started_at_utc'])).total_seconds();records.append(c)
start=min(c['started_at_utc'] for c in records);end=max(c['finished_at_utc'] for c in records);wall=(datetime.datetime.fromisoformat(end)-datetime.datetime.fromisoformat(start)).total_seconds()
result={'calls':records,'summed_call_seconds':sum(c['elapsed_seconds'] for c in records),'union_wall_seconds':wall,'overlapping_call_seconds':sum(c['elapsed_seconds'] for c in records)-wall,'parallel_calls':5,'note':'Five independent built-in imagegen calls overlapped. Sum is not wall time. Original PNGs copied without image editing; monochrome detail is shaded by UE materials.'}
(R/'images_manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='calls'}));print([(c['name'],c['dimensions']) for c in records])
