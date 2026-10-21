import json,hashlib,shutil,datetime
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo')
R=ROOT/'Work/MountainStation/ultra/SelfImprovement';BASE=R.parent
R.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data):(R/name).write_text(json.dumps(data,indent=2),encoding='utf-8')
assert not (R/'STATUS.json').exists(),'Do not reset an existing improvement run'
files=[]
for folder in ['FirstDelivery','TexturePass']:
    for p in sorted((BASE/folder).rglob('*')):
        if p.is_file():files.append({'path':str(p),'relative_path':str(p.relative_to(BASE)),'bytes':p.stat().st_size,'sha256':sha(p)})
write('baseline_immutability.json',{'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline_commit':'3e13e569b0e8725f4a9faaeee8e3d13ddf7b5737','files':files,'file_count':len(files)})
backup=ROOT/'Saved/Workers/MountainStation/ultra/SelfImprovementBaseline'
assert not backup.exists(),'Do not overwrite baseline backup'
manifest=json.loads((BASE/'TexturePass/publication_manifest.json').read_text())
pkgs=[]
for item in manifest['files']:
    p=Path(item['published_file']);assert sha(p)==item['sha256']
    dest=backup/item['relative_path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    assert sha(dest)==item['sha256'];pkgs.append({'backup':str(dest),'published':str(p),'relative_path':item['relative_path'],'sha256':item['sha256'],'bytes':p.stat().st_size})
write('baseline_packages.json',{'baseline_commit':'3e13e569b0e8725f4a9faaeee8e3d13ddf7b5737','backup_root':str(backup),'packages':pkgs})
before=R/'Screenshots/before';before.mkdir(parents=True,exist_ok=True)
for p in (BASE/'TexturePass/Screenshots').iterdir():
    if p.is_file():shutil.copy2(p,before/p.name)
write('STATUS.json',{'theme':'MountainStation','effort':'ultra','pass':'SelfImprovement','status':'working','started_at_utc':'2026-10-21T15:38:54+00:00','started_at_kst':'2026-10-22T00:38:54+09:00','supervisor_token_baseline_at_utc':'2026-10-21T15:37:23.4631689+00:00','baseline_commit':'3e13e569b0e8725f4a9faaeee8e3d13ddf7b5737','finished_at_utc':None,'elapsed_seconds':None,'map':'/Game/Maps/MountainStation_ultra','validation':'Baseline images and 130 package copies preserved; self-review in progress','blockers':[]})
print(json.dumps({'immutable_files':len(files),'baseline_packages':len(pkgs),'baseline_bytes':sum(p['bytes'] for p in pkgs)}))
