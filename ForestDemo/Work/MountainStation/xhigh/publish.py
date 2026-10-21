"""Publish only this worker's validated assets after its editor has exited."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json, hashlib, shutil, struct
ROOT=Path('D:/github/AstraEffort/ForestDemo')
WORK=ROOT/'Work/MountainStation/xhigh';SCRATCH=ROOT/'Saved/Workers/MountainStation/xhigh';PROJECT=SCRATCH/'Project'
validation=json.loads((WORK/'Evidence/validation.json').read_text());assert validation['success'],validation['errors']
runtime=json.loads((WORK/'Evidence/runtime_validation.json').read_text());assert runtime['success'],runtime.get('errors')
review=json.loads((WORK/'Evidence/visual_review.json').read_text());assert review['four_scene_images_inspected'] and review['native_hello_visible']
manifest=json.loads((WORK/'Screenshots/capture_manifest.json').read_text());assert len(manifest['captures'])==4
file_verified=datetime.now(timezone.utc).isoformat()
for n in ['overview','top_down','platform','tracks']:
 path=WORK/'Screenshots'/f'{n}.png';raw=path.read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n';assert struct.unpack('>II',raw[16:24])==(1920,1080)
 record=next(c for c in manifest['captures'] if c['name']==n)
 record['bytes_observed_at_export_request']=record['bytes']
 record['bytes']=len(raw);record['sha256']=hashlib.sha256(raw).hexdigest()
 record['file_modified_at_utc']=datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat()
 record['file_verified_at_utc']=file_verified
manifest['file_metadata_note']='Final byte sizes, hashes and modification timestamps verified after UE exit; captured_at_utc records the render export request. Immediate export-request sizes can describe a previous asynchronously replaced PNG.'
(WORK/'Screenshots/capture_manifest.json').write_text(json.dumps(manifest,indent=2))
timings=[]
for path in sorted((SCRATCH/'Timings').glob('*.json')):
 data=json.loads(path.read_text());data['name']=path.stem;timings.append(data)
timings.sort(key=lambda t:t['wait_started_at_utc'])
assert timings[-1]['name']=='capture_delivery' and timings[-1]['exit_code']==0 and timings[-1]['finished_at_utc'],'Final UE process has not completed'
source=PROJECT/'Content/MountainStation/xhigh';dest=ROOT/'Content/MountainStation/xhigh'
assert source.is_dir() and source.resolve().is_relative_to(SCRATCH.resolve())
dest.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(source,dest,dirs_exist_ok=True)
map_src=PROJECT/'Content/Maps/MountainStation_xhigh.umap';map_dst=ROOT/'Content/Maps/MountainStation_xhigh.umap';map_dst.parent.mkdir(exist_ok=True);shutil.copy2(map_src,map_dst)
hashes=[]
for src in sorted(source.rglob('*'))+[map_src]:
 if not src.is_file():continue
 dst=map_dst if src==map_src else dest/src.relative_to(source)
 digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 a,b=digest(src),digest(dst);assert a==b
 hashes.append({'path':str(dst.relative_to(ROOT)).replace('\\','/'),'bytes':dst.stat().st_size,'sha256':a})
(WORK/'Evidence/published_hashes.json').write_text(json.dumps({'verified_at_utc':datetime.now(timezone.utc).isoformat(),'files':hashes},indent=2))
(WORK/'Evidence/process_timings.json').write_text(json.dumps(timings,indent=2))
print(json.dumps({'published_files':len(hashes),'bytes':sum(i['bytes'] for i in hashes),'wait_seconds':sum(t['wait_seconds'] for t in timings),'execution_seconds':sum(t['execution_seconds'] for t in timings)},indent=2))
