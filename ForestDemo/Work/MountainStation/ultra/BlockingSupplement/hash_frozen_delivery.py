from pathlib import Path
import json,hashlib,datetime,sys
W=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra')
F=Path(r'D:/github/AstraEffort/ForestDemo')
P=F/'Saved/Workers/MountainStation/ultra/Project'
manifest=json.loads((W/'BlockingSupplement/Before/publication_manifest.json').read_text(encoding='utf-8-sig'))
files=[]
for entry in manifest['files']:
    live=hashlib.sha256((F/entry['path']).read_bytes()).hexdigest()
    private=hashlib.sha256((P/entry['path']).read_bytes()).hexdigest()
    files.append({'path':entry['path'],'first_delivery_sha256':entry['sha256'],'published_sha256':live,'private_sha256':private,'unchanged':live==private==entry['sha256']})
images=[]
for entry in manifest['screenshots']:
    live=hashlib.sha256((W/'Screenshots'/entry['name']).read_bytes()).hexdigest()
    images.append({'name':entry['name'],'first_delivery_sha256':entry['sha256'],'current_sha256':live,'unchanged':live==entry['sha256']})
record={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files,'screenshots':images,'all_unchanged':all(x['unchanged'] for x in files+images)}
(W/'BlockingSupplement'/sys.argv[1]).write_text(json.dumps(record,indent=2),encoding='utf-8')
assert record['all_unchanged']
print(json.dumps({'files_checked':len(files),'screenshots_checked':len(images),'all_unchanged':record['all_unchanged']}))
