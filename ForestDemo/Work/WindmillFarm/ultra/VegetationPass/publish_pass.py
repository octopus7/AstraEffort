from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,os
from PIL import Image
P=Path(__file__).resolve().parent;ROOT=P.parent;REPO=ROOT.parents[3]
CONTENT=REPO/'ForestDemo/Saved/Workers/WindmillFarm/ultra/Project/Content'
OWN=Path('WindmillFarm/ultra');MAP=Path('Maps/WindmillFarm_ultra.umap')
def read(name):return json.loads((P/name).read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def date(s):return datetime.fromisoformat(s.replace('Z','+00:00'))
def main():
    valid=read('validation.json');run=read('Execution/polish_timing.json');shutdown=read('shutdown_check.json')
    assert valid['all_passed'] and len(valid['checks'])>=23 and all(valid['checks'].values())
    assert run['exit_code']==0 and date(run['run_started_at_utc'])<date(valid['utc'])<date(run['finished_at_utc'])
    latest=max((json.loads(f.read_text(encoding='utf-8-sig')) for f in (P/'Execution').glob('*_timing.json')),key=lambda x:date(x['finished_at_utc']))
    assert latest['exit_code']==0 and shutdown['query_succeeded'] and shutdown['own_unreal_process_count']==0 and date(shutdown['utc'])>=date(latest['finished_at_utc'])
    log=(P/'Execution/polish.log').read_text(errors='replace');assert 'Failed to compile Material' not in log and 'Default Material will be used' not in log and 'LogPython: Error' not in log
    analysis=read('render_analysis.json');review=read('visual_review.json')
    assert analysis['all_1920x1080'] and analysis['all_nonblank'] and len(analysis['images'])==13 and review['accepted']
    for row in analysis['images']:
        path=P/'Screenshots'/(row['name']+'.png');assert Image.open(path).size==(1920,1080)
        assert sha(path)==row['sha256']==review['image_sha256'][row['name']]
    for name in ('corn','meadow'):assert analysis['motion'][name]['changed_pixels_threshold12']>25000
    videos=read('Motion/video_manifest.json')['videos'];assert len(videos)==2
    for video in videos:assert int(video['encoded']['nb_frames'])==32 and sha(Path(video['file']))==video['sha256']
    before={r['relative_path']:r['sha256'] for r in read('Before/publication.json')['files']}
    files=sorted(f for f in CONTENT.rglob('*') if f.is_file())
    assert all(f.relative_to(CONTENT)==MAP or (f.relative_to(CONTENT).is_relative_to(OWN) and f.suffix=='.uasset') for f in files)
    assert all(not any(s in f.as_posix() for s in ('__ExternalActors__','__ExternalObjects__','_BuiltData')) for f in files)
    # Check every existing destination against the frozen baseline before the first mutation.
    plan=[];targetroot=(REPO/'ForestDemo/Content').resolve()
    for source in files:
        relative=source.relative_to(CONTENT);target=(targetroot/relative).resolve();expected=sha(source)
        assert target==targetroot/MAP or target.is_relative_to(targetroot/OWN)
        old=sha(target) if target.exists() else None
        assert old is None or old==before.get(relative.as_posix()) or old==expected,('Unexpected destination modification',target)
        plan.append((source,relative,target,expected,old))
    stage=(REPO/'ForestDemo/Saved/Workers/WindmillFarm/ultra/VegetationPublishStage').resolve()
    rows=[]
    for source,relative,target,expected,old in plan:
        if old!=expected:
            staged=(stage/relative).resolve();assert staged.is_relative_to(stage)
            staged.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,staged);assert sha(staged)==expected
            target.parent.mkdir(parents=True,exist_ok=True);os.replace(staged,target)
        assert sha(target)==expected
        rows.append({'relative_path':relative.as_posix(),'destination':str(target),'source':str(source),'sha256':expected,'bytes':target.stat().st_size,'changed_from_baseline':before.get(relative.as_posix())!=expected,'new':relative.as_posix() not in before})
    result={'utc':datetime.now(timezone.utc).isoformat(),'file_count':len(rows),'new_files':sum(r['new'] for r in rows),'changed_files':sum(r['changed_from_baseline'] for r in rows),'all_hashes_match':True,'private_editor_closed':True,'validation_sha256':sha(P/'validation.json'),'files':rows}
    (P/'publication.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))
if __name__=='__main__':main()
