import json,hashlib,datetime
from pathlib import Path
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement');P=Path(r'D:/github/AstraEffort/ForestDemo/Saved/Workers/MountainStation/ultra/Project')
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def inventory():
    files=sorted((P/'Content/MountainStation/ultra').rglob('*.uasset'))+[P/'Content/Maps/MountainStation_ultra.umap']
    assert not list((P/'Content').rglob('*BuiltData*'))
    for folder in ['__ExternalActors__','__ExternalObjects__']:assert not [f for f in (P/'Content'/folder).rglob('*') if f.is_file()]
    return [{'relative_path':p.relative_to(P).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in files]
def snapshot():
    data={'run':'SelfImprovement-final','snapshot_at_utc':stamp(),'project':str(P),'files':inventory(),'validated':False}
    (R/'validated_packages.json').write_text(json.dumps(data,indent=2));return data
def confirm():
    data=json.loads((R/'validated_packages.json').read_text());assert inventory()==data['files'],'Private packages changed after validation snapshot';return data
def baseline_check():
    base=json.loads((R/'baseline_immutability.json').read_text());actual=[]
    for folder in ['FirstDelivery','TexturePass']:
        for p in sorted((R.parent/folder).rglob('*')):
            if p.is_file():actual.append({'path':str(p),'relative_path':str(p.relative_to(R.parent)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    assert actual==base['files'],'Baseline content inventory changed'
    result={'checked_at_utc':stamp(),'file_count':len(actual),'passed':True};(R/'baseline_immutability_verified.json').write_text(json.dumps(result,indent=2));return result
def validate_allocations():
    count=0
    for name,layout in json.loads((R/'uv_layouts.json').read_text()).items():
        charts=layout['charts'];seen=[];end_y=0
        for row in layout['rows']:
            assert row['y']>=end_y;end_x=0
            for index in row['charts']:
                c=charts[index];assert c[0]==index and c[1]>=end_x and c[2]==row['y'] and c[4]<=row['height'];assert c[1]+c[3]<=layout['side_px'] and c[2]+c[4]<=layout['side_px'];end_x=c[1]+c[3];seen.append(index)
            end_y=row['y']+row['height']
        assert sorted(seen)==list(range(len(charts)));count+=len(charts)
    (R/'allocation_validation.json').write_text(json.dumps({'checked_at_utc':stamp(),'chart_rectangles_checked':count,'passed':True},indent=2))
