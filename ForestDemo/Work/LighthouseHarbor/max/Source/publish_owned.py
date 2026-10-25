"""Copy only validated owned deliverables after the queued private editor has closed."""
from pathlib import Path
import hashlib,json,shutil
from datetime import datetime,timezone
REPO=Path('D:/github/AstraEffort').resolve();ROOT=REPO/'ForestDemo/Work/LighthouseHarbor/max'
PRIVATE=REPO/'ForestDemo/Saved/Workers/LighthouseHarbor/max/HarborPrivate/Content'
TARGET=REPO/'ForestDemo/Content';ASSETREL=Path('LighthouseHarbor/max');MAPREL=Path('Maps/LighthouseHarbor_max.umap')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['source_validation','fbx_roundtrip','saved_map_validation','capture_pixels']:
    assert read(ROOT/'Validation'/(name+'.json'))['pass'],name
manifest=read(ROOT/'Screenshots/capture_manifest.json');assert len(manifest['captures'])==6
timingfiles=list((ROOT/'Timings').glob('capture_*.json'));assert timingfiles
latest=max((read(p) for p in timingfiles),key=lambda d:d['finished_at_utc'])
assert latest['exit_code'] in [0,-1073741819],'Unexpected final private editor termination status'
latest_log=Path(latest['log']).read_text(encoding='utf-8',errors='replace')
assert 'LogExit: Exiting.' in latest_log and 'Log file closed' in latest_log,'Final editor shutdown was not observed'
assert all('HARBOR_CAPTURE '+n in latest_log for n in ['overview','top_down','lighthouse','harbor','motion_t0','motion_t1'])
assert 'Failed to compile Material' not in latest_log and 'Traceback (most recent call last)' not in latest_log
assert datetime.fromisoformat(latest['finished_at_utc'])>=datetime.fromisoformat(manifest['completed_at_utc'])
files=sorted((PRIVATE/ASSETREL).rglob('*.uasset'))+[PRIVATE/MAPREL]
assert len(files)>=100 and all(p.exists() for p in files)
assert not any('BuiltData' in p.name or '__External' in str(p) for p in files)
records=[]
for source in files:
    rel=source.relative_to(PRIVATE);dest=TARGET/rel
    allowed=(dest.is_relative_to(TARGET/ASSETREL) or dest==TARGET/MAPREL)
    assert allowed and source.resolve().is_relative_to(PRIVATE.resolve()),str(dest)
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
    a,b=sha(source),sha(dest);assert a==b
    records.append({'path':str(rel).replace('\\','/'),'bytes':source.stat().st_size,'sha256':a,'private_published_equal':True})
result={'pass':True,'published_at_utc':datetime.now(timezone.utc).isoformat(),'private_editor_finished_at_utc':latest['finished_at_utc'],
        'final_editor_exit_code':latest['exit_code'],'artifact_validation_passed':True,
        'process_status_note':'Output/capture validation and editor log closure checked independently. 0xC0000005, if present, is retained as a post-shutdown process-status anomaly, never reported as clean exit.',
        'published_files':len(records),'total_bytes':sum(x['bytes'] for x in records),'files':records,
        'map_sha256':next(x['sha256'] for x in records if x['path']==MAPREL.as_posix())}
(ROOT/'Validation/published_hashes.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('OWNED_PUBLISH_PASS',len(records),'files;',result['map_sha256'])
