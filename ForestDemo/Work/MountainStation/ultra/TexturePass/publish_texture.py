import json,hashlib,shutil,datetime,struct
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo')
R=ROOT/'Work/MountainStation/ultra/TexturePass'
PRIVATE=ROOT/'Saved/Workers/MountainStation/ultra/Project'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
started=utc()
closed=read(R/'editor_closed_evidence.json');assert closed['own_editor_process_count']==0 and closed['query_succeeded']
assert (datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(closed['checked_at_utc'])).total_seconds()<300
uv=read(R/'uv_validation.json');assert uv['passed'] and len(uv['meshes'])==47
assert read(R/'source_uv_validation.json')['passed']
assert read(R/'Runtime/validation.json')['passed']
assert read(R/'Runtime/native_and_ramp.json')['passed']
assert read(R/'first_delivery_immutability.json')['passed']
assert read(R/'visual_review.json')['all_four_images_inspected']
timing=read(R/'timing_review_04.json');assert timing['exit_code']==0
pkg=read(R/'validation.json');assert not pkg['foreign_game_dependencies'] and pkg['world_partition'] is None
assert pkg['world_path']=='/Game/Maps/MountainStation_ultra.MountainStation_ultra'
capture=read(R/'Screenshots/capture_manifest.json')
first=read(R.parent/'FirstDelivery/Screenshots/capture_manifest.json')
assert len(capture['captures'])==4
shots=[]
for a,b in zip(capture['captures'],first['captures']):
    assert {k:v for k,v in a.items() if k!='captured_at_utc'}=={k:v for k,v in b.items() if k!='captured_at_utc'}
    p=R/'Screenshots'/(a['name']+'.png');data=p.read_bytes()
    assert struct.unpack('>II',data[16:24])==(1920,1080)
    shots.append({'file':str(p),'sha256':digest(p),'dimensions':[1920,1080]})
asset_rel=Path('Content/MountainStation/ultra')
source_files=sorted((PRIVATE/asset_rel).rglob('*'))
source_files=[p for p in source_files if p.is_file()]
assert source_files and all(p.suffix=='.uasset' and 'BuiltData' not in p.name for p in source_files)
files=[]
for p in source_files+[PRIVATE/'Content/Maps/MountainStation_ultra.umap']:
    rel=p.relative_to(PRIVATE)
    assert rel.as_posix().startswith('Content/MountainStation/ultra/') or rel.as_posix()=='Content/Maps/MountainStation_ultra.umap'
    dest=ROOT/rel;dest.parent.mkdir(parents=True,exist_ok=True)
    sha=digest(p);shutil.copy2(p,dest);assert digest(dest)==sha
    files.append({'relative_path':rel.as_posix(),'private_source':str(p),'published_file':str(dest),'bytes':dest.stat().st_size,'sha256':sha})
record={'started_at_utc':started,'finished_at_utc':utc(),'validated_private_editor_closed':True,'files':files,'file_count':len(files),'screenshots':shots,'camera_manifests_equal_except_capture_time':True,'copied_hashes_match':True}
(R/'publication_manifest.json').write_text(json.dumps(record,indent=2))
print(json.dumps({'published_files':len(files),'all_hashes_match':True}))
