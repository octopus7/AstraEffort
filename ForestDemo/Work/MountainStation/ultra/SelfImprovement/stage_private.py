from pathlib import Path
import json,shutil,hashlib,sys,datetime
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement');P=Path(r'D:/github/AstraEffort/ForestDemo/Saved/Workers/MountainStation/ultra/Project');C=P.parent/'SelfImprovementCandidate'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if sys.argv[1]=='save_and_restore_baseline':
    assert not C.exists()
    files=sorted((P/'Content/MountainStation/ultra').rglob('*.uasset'))+[P/'Content/Maps/MountainStation_ultra.umap'];rows=[]
    for f in files:
        rel=f.relative_to(P);to=C/rel;to.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,to);assert sha(to)==sha(f);rows.append({'relative_path':rel.as_posix(),'sha256':sha(f)})
    (R/'candidate_packages.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':rows},indent=2))
    for row in json.loads((R/'baseline_packages.json').read_text())['packages']:
        f=Path(row['backup']);assert sha(f)==row['sha256'];shutil.copy2(f,P/row['relative_path'])
    print('Baseline restored in own private project; candidate protected:',len(rows))
elif sys.argv[1]=='restore_candidate':
    rows=json.loads((R/'candidate_packages.json').read_text())['files']
    for row in rows:
        f=C/row['relative_path'];assert sha(f)==row['sha256'];shutil.copy2(f,P/row['relative_path']);assert sha(P/row['relative_path'])==row['sha256']
    print('Candidate restored exactly:',len(rows))
