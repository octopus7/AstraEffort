import json,hashlib,datetime
from pathlib import Path
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/TexturePass')
archive=R.parent/'FirstDelivery'
manifest=json.loads((archive/'archive_manifest.json').read_text(encoding='utf-8-sig'))
checked=[]
for row in manifest['files']:
    p=archive/row['relative_path']
    actual=hashlib.sha256(p.read_bytes()).hexdigest()
    checked.append({'path':row['relative_path'],'sha256':actual,'matches':actual.lower()==row['sha256'].lower(),'bytes':p.stat().st_size})
record={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manifest':str(archive/'archive_manifest.json'),'files':checked,'passed':all(x['matches'] for x in checked)}
(R/'first_delivery_immutability.json').write_text(json.dumps(record,indent=2))
assert record['passed']
print(json.dumps({'immutable_archive_files':len(checked),'passed':record['passed']}))
