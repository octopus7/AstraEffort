"""Publish only the validated RainyCanal/ultra packages after its private UE closes."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,shutil
P=Path(__file__).resolve().parent
REPO=P.parents[3]
SCRATCH=REPO/'ForestDemo/Saved/Workers/RainyCanal/ultra'
SOURCE=SCRATCH/'Project/Content'
DEST=REPO/'ForestDemo/Content'
def read(name):return json.loads((P/name).read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
v=read('validation.json');assert v['all_passed'] and all(v['checks'].values()) and len(v['checks'])>=23
c=read('Execution/delivery_completion.json');assert c['success'] and c['validated'] and c['stills']==13 and c['movie_frames']==80
t=read('Execution/delivery_timing.json');assert t['exit_code']==0
manifest=read('Screenshots/capture_manifest.json');assert manifest['phase']=='delivery'
assert datetime.fromisoformat(v['utc'])>=datetime.fromisoformat(t['run_started_at_utc'])
shutdown=read('Execution/shutdown_check.json')
assert shutdown['query_succeeded'] and shutdown['matching_process_count']==0
assert datetime.fromisoformat(shutdown['utc'])>=datetime.fromisoformat(t['finished_at_utc'])
assert (datetime.now(timezone.utc)-datetime.fromisoformat(shutdown['utc'])).total_seconds()<600,'Refresh shutdown check'
log=(P/'Execution/delivery.log').read_text(encoding='utf-8-sig',errors='replace')
bad=[line for line in log.splitlines() if re.search(r'LogPython: Error:|Failed to compile Material|Default Material will be used|Fatal error:',line,re.I)]
assert not bad,bad
render=read('render_analysis.json');assert render['all_1920x1080'] and render['all_nonblank'] and len(render['images'])==13
for row in render['images']:assert sha(P/'Screenshots'/(row['name']+'.png'))==row['sha256']
for key,m in render['motion'].items():assert m['delta_seconds']>1 and m['changed_pixels_threshold12']>500,(key,m)
assert render['motion']['water_only']['rain_hidden'] and render['motion']['puddle']['rain_hidden']
videos=read('Motion/video_manifest.json')['videos'];assert len(videos)==2
for row in videos:assert row['decode_verified'] and row['source_frames']==40 and sha(Path(row['file']))==row['sha256']
review=read('QA/final_review.json');assert review['accepted'] and not review['blockers']
for row in review['files']:assert sha(P/row['path'])==row['sha256'],row['path']
allowed_root=Path('RainyCanal/ultra');allowed_map=Path('Maps/RainyCanal_ultra.umap')
files=sorted(p for p in SOURCE.rglob('*') if p.is_file())
for f in files:
    rel=f.relative_to(SOURCE)
    assert (rel.is_relative_to(allowed_root) and f.suffix=='.uasset') or rel==allowed_map,rel
    assert not any('__External' in part or '_BuiltData' in part for part in rel.parts),rel
assert len(list((SOURCE/allowed_root/'Meshes').glob('*.uasset')))==24
assert len(list((SOURCE/allowed_root/'Textures').glob('*.uasset')))==30
assert len(list((SOURCE/allowed_root/'Materials').glob('*.uasset')))==16
assert len(files)==71
assert not (DEST/allowed_root).exists() and not (DEST/allowed_map).exists(),'Never overwrite a prior publication'
# Staging stays inside this assignment. Rename only into its exact empty final scopes.
stage=SCRATCH/'Publication';assert not stage.exists(),'Review an existing publication stage before retrying'
stage.mkdir()
rows=[]
for f in files:
    rel=f.relative_to(SOURCE);out=stage/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,out)
    digest=sha(f);assert sha(out)==digest
    rows.append({'relative_path':rel.as_posix(),'sha256':digest,'bytes':f.stat().st_size})
(DEST/allowed_root).parent.mkdir(parents=True,exist_ok=True)
(stage/allowed_root).rename(DEST/allowed_root)
(DEST/'Maps').mkdir(exist_ok=True)
(stage/allowed_map).rename(DEST/allowed_map)
for row in rows:assert sha(DEST/row['relative_path'])==row['sha256']
out={'utc':datetime.now(timezone.utc).isoformat(),'theme':'RainyCanal','effort':'ultra','source':str(SOURCE),'destination':str(DEST),'map':'/Game/Maps/RainyCanal_ultra','package_count':len(rows),'bytes':sum(r['bytes'] for r in rows),'all_hashes_match':True,'validation_sha256':sha(P/'validation.json'),'fresh_delivery_log_sha256':sha(P/'Execution/delivery.log'),'shutdown_check_sha256':sha(P/'Execution/shutdown_check.json'),'review_sha256':sha(P/'QA/final_review.json'),'files':rows}
(P/'publication_manifest.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k!='files'},indent=2))
